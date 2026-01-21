"""
Trend Service - FINAL FIX
Fetches diverse trends from multiple categories to ensure variety.

The key: Use DIFFERENT search queries to get DIFFERENT results.
"""

import os
import logging
import asyncio
import random
from datetime import datetime, timedelta
from typing import List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    logger.warning("httpx not available")


@dataclass
class TrendingNews:
    """A trending news item"""
    headline: str
    summary: str = ""
    source: str = ""
    url: str = ""
    category: str = ""
    age: str = "today"
    jesse_angle: str = ""


class TrendService:
    """
    Fetches trending news from Brave Search API.
    
    KEY: Each search query returns DIFFERENT results.
    So we use DIFFERENT queries to get DIVERSE trends.
    """
    
    def __init__(self):
        self.brave_api_key = os.getenv("BRAVE_API_KEY")
        self.logger = logging.getLogger("TrendService")
        
        # Cache
        self.cached_trends: List[TrendingNews] = []
        self.cache_time: Optional[datetime] = None
        self.cache_duration = timedelta(minutes=30)
        
        if self.brave_api_key:
            self.logger.info("✅ Brave Search API configured for trend fetching")
        else:
            self.logger.warning("⚠️ No BRAVE_API_KEY - will use fallback trends")
    
    async def get_trending_news(self, force_refresh: bool = False) -> List[TrendingNews]:
        """
        Fetch diverse trending news.
        
        Returns a list of trends from DIFFERENT categories to ensure
        that when we assign trend[0], trend[1], trend[2] to posts,
        they're actually different topics.
        """
        
        # Check cache (unless force refresh)
        if not force_refresh and self.cached_trends and self.cache_time:
            if datetime.now() < self.cache_time + self.cache_duration:
                self.logger.info(f"Using cached trends ({len(self.cached_trends)} items)")
                # Shuffle cached trends to get variety on repeated calls
                shuffled = self.cached_trends.copy()
                random.shuffle(shuffled)
                return shuffled
        
        self.logger.info("Fetching fresh trends from multiple categories...")
        
        all_trends = []
        
        if self.brave_api_key and HTTPX_AVAILABLE:
            # DIFFERENT search queries = DIFFERENT results
            # This is the key to getting diverse trends
            search_configs = [
                # Tech & Business (but different angles)
                {"query": "tech company layoffs 2026", "category": "tech_layoffs"},
                {"query": "startup funding Series A B", "category": "startup_funding"},
                {"query": "CEO fired resigned steps down", "category": "ceo_news"},
                
                # AI (the hot topic)
                {"query": "OpenAI ChatGPT Google AI announcement", "category": "ai_news"},
                
                # Workplace & Corporate
                {"query": "return to office remote work mandate", "category": "workplace"},
                {"query": "LinkedIn viral post cringe hustle", "category": "linkedin_cringe"},
                
                # Entertainment & Pop Culture (broader appeal)
                {"query": "Netflix show movie streaming", "category": "entertainment"},
                {"query": "celebrity news viral moment", "category": "celebrity"},
                
                # Sports (mass appeal in US)
                {"query": "NFL coach fired hired trade", "category": "nfl"},
                {"query": "NBA trade deadline news", "category": "nba"},
                
                # Finance & Economy
                {"query": "stock market earnings report", "category": "finance"},
                {"query": "inflation economy recession", "category": "economy"},
            ]
            
            # Shuffle and pick 6 different categories
            random.shuffle(search_configs)
            selected_configs = search_configs[:6]
            
            for config in selected_configs:
                try:
                    trends = await self._search_brave(config["query"], config["category"])
                    if trends:
                        # Only take the TOP result from each category
                        # This ensures diversity - one result per category
                        all_trends.append(trends[0])
                        self.logger.info(f"  ✓ {config['category']}: {trends[0].headline[:50]}...")
                except Exception as e:
                    self.logger.warning(f"  ✗ {config['category']}: {e}")
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.15)
        
        # Add fallback trends if we don't have enough
        if len(all_trends) < 5:
            self.logger.info("Adding fallback trends for variety")
            fallbacks = self._get_fallback_trends()
            # Only add fallbacks we don't already have (by category)
            existing_categories = {t.category for t in all_trends}
            for fb in fallbacks:
                if fb.category not in existing_categories:
                    all_trends.append(fb)
                    existing_categories.add(fb.category)
                if len(all_trends) >= 10:
                    break
        
        # Add Jesse angles
        for trend in all_trends:
            if not trend.jesse_angle:
                trend.jesse_angle = self._get_jesse_angle(trend.category)
        
        # Update cache
        self.cached_trends = all_trends
        self.cache_time = datetime.now()
        
        self.logger.info(f"📰 Prepared {len(all_trends)} diverse trends")
        return all_trends
    
    async def _search_brave(self, query: str, category: str) -> List[TrendingNews]:
        """Search Brave News API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.search.brave.com/res/v1/news/search",
                    params={
                        "q": query,
                        "count": 3,
                        "freshness": "pd",  # Past day
                        "country": "us",
                        "search_lang": "en"
                    },
                    headers={
                        "X-Subscription-Token": self.brave_api_key,
                        "Accept": "application/json"
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    
                    trends = []
                    for r in results:
                        trends.append(TrendingNews(
                            headline=r.get("title", ""),
                            summary=r.get("description", ""),
                            source=r.get("meta_url", {}).get("hostname", "news"),
                            url=r.get("url", ""),
                            category=category,
                            age=r.get("age", "today")
                        ))
                    return trends
                    
                elif response.status_code == 429:
                    self.logger.warning(f"Brave API rate limited (429) for '{query}'")
                    return []
                else:
                    self.logger.warning(f"Brave API {response.status_code} for '{query}'")
                    return []
                    
        except Exception as e:
            self.logger.error(f"Brave search failed for '{query}': {e}")
            return []
    
    def _get_fallback_trends(self) -> List[TrendingNews]:
        """Diverse fallback trends when API fails"""
        fallbacks = [
            TrendingNews(
                headline="Major tech company announces another round of layoffs",
                summary="Thousands affected in latest efficiency measures",
                source="tech_news", category="tech_layoffs",
                jesse_angle="Your severance package doesn't include lip balm."
            ),
            TrendingNews(
                headline="Startup raises $50M Series B, immediately pivots to AI",
                summary="Adding AI to everything continues to be a winning strategy with VCs",
                source="startup_news", category="startup_funding",
                jesse_angle="Runway is temporary. Lip moisture is eternal. Well, until it dries."
            ),
            TrendingNews(
                headline="LinkedIn influencer's 4am morning routine goes viral for wrong reasons",
                summary="Hustle culture meets reality check in the comments",
                source="social", category="linkedin_cringe",
                jesse_angle="I wake up at 4am because anxiety, not hustle. At least my lips aren't dry."
            ),
            TrendingNews(
                headline="Company mandates return to office, employees push back",
                summary="Remote work debate continues across corporate America",
                source="workplace", category="workplace",
                jesse_angle="Office or home, your lips are dry either way."
            ),
            TrendingNews(
                headline="New AI model claims human-level performance on benchmark",
                summary="The AI arms race continues with another major announcement",
                source="ai_news", category="ai_news",
                jesse_angle="AI can write your emails. It can't moisturize your lips."
            ),
            TrendingNews(
                headline="NFL team makes surprising coaching change",
                summary="Fans react to unexpected front office decision",
                source="sports", category="nfl",
                jesse_angle="Coaches come and go. Chapped lips are forever. Unless."
            ),
            TrendingNews(
                headline="Netflix announces price increase, subscribers react",
                summary="Streaming costs continue to rise",
                source="entertainment", category="entertainment",
                jesse_angle="Subscription fatigue is real. Lip balm is $8.99. Once."
            ),
            TrendingNews(
                headline="CEO sends company-wide email about 'difficult decisions'",
                summary="Corporate speak precedes another round of cuts",
                source="business", category="ceo_news",
                jesse_angle="The memo was 2000 words. Nobody read it. Everyone got fired anyway."
            ),
        ]
        random.shuffle(fallbacks)
        return fallbacks
    
    def _get_jesse_angle(self, category: str) -> str:
        """Get a Jesse-style angle for a category"""
        angles = {
            "tech_layoffs": "Your severance doesn't include lip balm. Jesse A. Eisenbalm does.",
            "startup_funding": "Runway burns fast. Lip balm doesn't. $8.99.",
            "ceo_news": "Leadership changes. Dry lips don't. Well, they do. That's the problem.",
            "ai_news": "AI can't feel chapped lips. You can. Advantage: unclear.",
            "workplace": "Office or home, your lips are dry either way.",
            "linkedin_cringe": "Hustle culture won't moisturize your lips.",
            "entertainment": "Content is streaming. Your lips are cracking. Priorities.",
            "celebrity": "Fame is fleeting. Chapped lips feel eternal.",
            "nfl": "Coaching carousel spins. Your lip care shouldn't.",
            "nba": "Trade deadline stress. Lip care is $8.99.",
            "finance": "Markets are volatile. Lip balm is $8.99. Consistent.",
            "economy": "Inflation is real. Lip balm is still $8.99.",
        }
        return angles.get(category, "Life is chaos. Lip balm is $8.99.")


# Singleton
_trend_service: Optional[TrendService] = None

def get_trend_service() -> TrendService:
    global _trend_service
    if _trend_service is None:
        _trend_service = TrendService()
    return _trend_service