"""
Trend Service V2 - GUARANTEED UNIQUE TRENDS
Each call to get_trend_for_post() returns a DIFFERENT trend
"""

import os
import logging
import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


@dataclass
class TrendingNews:
    """A trending news item"""
    headline: str
    summary: str
    source: str
    url: str
    category: str
    age: str
    jesse_angle: str = ""


class TrendService:
    """
    Fetches trending news - GUARANTEES unique trends per batch
    
    Key change: Instead of returning all trends and hoping AI picks different ones,
    we now track which trends have been used and return only unused ones.
    """
    
    def __init__(self):
        self.brave_api_key = os.getenv("BRAVE_API_KEY")
        self.logger = logging.getLogger("TrendService")
        
        # Cache for fetched trends
        self.cached_trends: List[TrendingNews] = []
        self.cache_time: Optional[datetime] = None
        self.cache_duration = timedelta(minutes=30)  # Shorter cache for fresher content
        
        # Track used trends within current batch
        self.batch_used_indices: Set[int] = set()
        self.current_batch_id: Optional[str] = None
        
        if self.brave_api_key:
            self.logger.info("✅ Brave Search API configured")
        else:
            self.logger.warning("⚠️ No BRAVE_API_KEY - using fallback trends")
    
    def start_new_batch(self, batch_id: str):
        """Call this at the start of each batch to reset used trends"""
        self.current_batch_id = batch_id
        self.batch_used_indices = set()
        self.logger.info(f"Started new batch {batch_id} - trend tracking reset")
    
    async def get_next_unused_trend(self) -> Optional[TrendingNews]:
        """Get the next trend that hasn't been used in this batch"""
        
        # Refresh cache if needed
        if not self.cached_trends or self._cache_expired():
            await self._refresh_trends()
        
        # Find first unused trend
        for idx, trend in enumerate(self.cached_trends):
            if idx not in self.batch_used_indices:
                self.batch_used_indices.add(idx)
                self.logger.info(f"Assigned trend {idx}: {trend.headline[:50]}...")
                return trend
        
        # All trends used - fetch fresh ones
        self.logger.warning("All cached trends used - fetching fresh batch")
        await self._refresh_trends(force=True)
        
        # Try again with fresh trends
        for idx, trend in enumerate(self.cached_trends):
            if idx not in self.batch_used_indices:
                self.batch_used_indices.add(idx)
                return trend
        
        # Still nothing - return None (will generate original content)
        self.logger.warning("No unused trends available")
        return None
    
    def _cache_expired(self) -> bool:
        """Check if cache needs refresh"""
        if not self.cache_time:
            return True
        return datetime.now() > self.cache_time + self.cache_duration
    
    async def _refresh_trends(self, force: bool = False):
        """Fetch fresh trends from multiple diverse sources"""
        
        self.logger.info("Refreshing trends cache...")
        all_trends = []
        
        if self.brave_api_key and HTTPX_AVAILABLE:
            # DIVERSE search queries - different topics to ensure variety
            search_queries = [
                # Tech & Business
                ("tech layoffs 2026", "tech_industry"),
                ("startup funding round", "startup_news"),
                ("CEO resignation fired", "corporate_drama"),
                
                # AI specifically  
                ("artificial intelligence OpenAI Google", "ai_news"),
                ("ChatGPT AI announcement", "ai_news"),
                
                # Entertainment & Pop Culture
                ("celebrity news hollywood", "entertainment"),
                ("Netflix streaming show", "entertainment"),
                ("viral TikTok trend", "viral_social"),
                ("new movie release box office", "entertainment"),
                ("new music album release", "entertainment"),
                ("pop culture news", "entertainment"),
                
                # Sports
                ("NFL coach fired hired", "sports"),
                ("NBA trade deadline", "sports"),
                
                # Business & Finance
                ("stock market earnings", "finance"),
                ("company bankruptcy", "finance"),
                
                # Workplace
                ("return to office remote work", "workplace"),
                ("LinkedIn viral post cringe", "workplace_viral"),
            ]
            
            # Shuffle to get different results each time
            random.shuffle(search_queries)
            
            # Only query 6 random categories to stay under rate limits
            selected_queries = search_queries[:6]
            
            for query, category in selected_queries:
                trends = await self._search_brave(query, category)
                all_trends.extend(trends)
                # Small delay to avoid rate limits
                await asyncio.sleep(0.2)
        
        # Add fallback trends if needed
        if len(all_trends) < 10:
            fallbacks = self._get_fallback_trends()
            all_trends.extend(fallbacks)
        
        # Deduplicate by headline similarity
        unique_trends = self._deduplicate_trends(all_trends)
        
        # Add Jesse angles
        for trend in unique_trends:
            if not trend.jesse_angle:
                trend.jesse_angle = self._generate_jesse_angle(trend)
        
        # Shuffle to randomize order
        random.shuffle(unique_trends)
        
        self.cached_trends = unique_trends
        self.cache_time = datetime.now()
        
        # Reset used indices when cache refreshes
        if force:
            self.batch_used_indices = set()
        
        self.logger.info(f"Cached {len(self.cached_trends)} unique trends")
    
    async def _search_brave(self, query: str, category: str) -> List[TrendingNews]:
        """Search Brave News API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.search.brave.com/res/v1/news/search",
                    params={
                        "q": query,
                        "count": 3,  # Fewer per query, more queries
                        "freshness": "pd",
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
                    for result in results:
                        trends.append(TrendingNews(
                            headline=result.get("title", ""),
                            summary=result.get("description", ""),
                            source=result.get("meta_url", {}).get("hostname", "unknown"),
                            url=result.get("url", ""),
                            category=category,
                            age=result.get("age", "today")
                        ))
                    return trends
                    
                elif response.status_code == 429:
                    self.logger.warning(f"Rate limited for '{query}'")
                    return []
                else:
                    self.logger.warning(f"Brave API returned {response.status_code}")
                    return []
                    
        except Exception as e:
            self.logger.error(f"Brave search failed: {e}")
            return []
    
    def _deduplicate_trends(self, trends: List[TrendingNews]) -> List[TrendingNews]:
        """Remove duplicate/similar trends"""
        unique = []
        seen_keywords = set()
        
        for trend in trends:
            # Extract key words from headline
            words = set(trend.headline.lower().split())
            # Remove common words
            words -= {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'to', 'for', 'of', 
                     'and', 'in', 'on', 'at', 'as', 'by', 'with', 'from', 'new', 'says',
                     'after', 'how', 'why', 'what', 'when', 'will', 'has', 'have', 'been'}
            
            # Check if we've seen similar keywords
            significant_words = {w for w in words if len(w) > 4}
            
            if significant_words:
                overlap = significant_words & seen_keywords
                # If more than 50% overlap, skip as duplicate
                if len(overlap) > len(significant_words) * 0.5:
                    continue
                
                seen_keywords.update(significant_words)
            
            unique.append(trend)
        
        return unique
    
    def _get_fallback_trends(self) -> List[TrendingNews]:
        """Diverse fallback trends when API fails"""
        
        fallbacks = [
            TrendingNews(
                headline="Major tech company announces surprise layoffs affecting thousands",
                summary="Another round of 'efficiency measures' hits the industry",
                source="tech_news", url="", category="tech_industry", age="today"
            ),
            TrendingNews(
                headline="Startup raises $50M Series B, immediately pivots to AI",
                summary="Adding 'AI-powered' to everything continues",
                source="startup_news", url="", category="startup_news", age="today"
            ),
            TrendingNews(
                headline="LinkedIn influencer's 4am routine post goes viral for wrong reasons",
                summary="The hustle culture discourse continues",
                source="social", url="", category="workplace_viral", age="today"
            ),
            TrendingNews(
                headline="CEO sends 2000-word memo about company culture before layoffs",
                summary="'We're a family' hits different when HR is involved",
                source="business", url="", category="corporate_drama", age="today"
            ),
            TrendingNews(
                headline="New AI model claims to be 'more human than humans'",
                summary="Still can't apply lip balm though",
                source="ai_news", url="", category="ai_news", age="today"
            ),
            TrendingNews(
                headline="NFL team fires coach after disappointing season",
                summary="Sports leadership changes continue",
                source="sports", url="", category="sports", age="today"
            ),
            TrendingNews(
                headline="Streaming service raises prices again, loses subscribers",
                summary="The streaming wars claim another victim",
                source="entertainment", url="", category="entertainment", age="today"
            ),
            TrendingNews(
                headline="Return to office mandate sparks employee backlash",
                summary="Executives confused why workers prefer working from home",
                source="workplace", url="", category="workplace", age="today"
            ),
            TrendingNews(
                headline="Crypto exchange faces regulatory scrutiny",
                summary="Web3 winter continues",
                source="finance", url="", category="finance", age="today"
            ),
            TrendingNews(
                headline="Celebrity announces surprise project on social media",
                summary="Breaking the internet, one post at a time",
                source="entertainment", url="", category="entertainment", age="today"
            ),
        ]
        
        random.shuffle(fallbacks)
        return fallbacks
    
    def _generate_jesse_angle(self, trend: TrendingNews) -> str:
        """Generate a Jesse-style angle for the trend"""
        
        angles = {
            "tech_industry": [
                "Layoffs hit. Your severance doesn't include lip balm. Ours does.",
                "Tech jobs come and go. Dry lips are forever. Unless.",
                "Another reorg. Your org chart changes. Your lip care shouldn't.",
            ],
            "startup_news": [
                "Runway is short. So is this lip balm. But it works.",
                "Series B closed. Series B-alm open. $8.99.",
                "Pivot complete. Now pivot to lip care.",
            ],
            "workplace_viral": [
                "That post is cringe. Your dry lips are also cringe. Fix one of them.",
                "LinkedIn thinks you should hustle at 4am. We think you should moisturize.",
                "Viral for the wrong reasons. Unlike moisturized lips.",
            ],
            "corporate_drama": [
                "Corporate says we're family. Families don't do layoffs. $8.99.",
                "The memo was long. Your patience is short. So is lip balm application.",
                "Culture fit? How about moisture fit.",
            ],
            "ai_news": [
                "AI can do a lot. It can't feel chapped lips. You can.",
                "Robots don't need lip balm. You do. Advantage: you.",
                "AI wrote your email. It can't write you moisturized lips.",
            ],
            "sports": [
                "Coaching changes happen. Lip moisture doesn't have to.",
                "Big game energy. Small tube salvation.",
                "Sports are stressful. Your lips don't have to be.",
            ],
            "entertainment": [
                "Content is streaming. Your lips are cracking. Priorities.",
                "Binge-watching? Binge-moisturizing.",
                "Entertainment comes and goes. Dry lips are always there. Unfortunately.",
            ],
            "finance": [
                "Markets are volatile. Lip balm is $8.99. Consistent.",
                "Your portfolio is uncertain. Your lip moisture doesn't have to be.",
                "Stock down. Lips dry. Control what you can.",
            ],
            "workplace": [
                "RTO mandate? Return to lip care.",
                "Office or home. Your lips are dry either way.",
                "Hybrid work. Consistent lip care.",
            ],
        }
        
        category_angles = angles.get(trend.category, angles.get("tech_industry"))
        return random.choice(category_angles)
    
    def format_single_trend(self, trend: TrendingNews) -> str:
        """Format a single trend for the content generator"""
        
        return f"""═══════════════════════════════════════════════════════════════════════════════
🎯 YOUR ASSIGNED TREND - REACT TO THIS SPECIFIC NEWS
═══════════════════════════════════════════════════════════════════════════════

📰 HEADLINE: {trend.headline}

Category: {trend.category}
Source: {trend.source}

{f"Details: {trend.summary}" if trend.summary else ""}

💡 Jesse angle: {trend.jesse_angle}

═══════════════════════════════════════════════════════════════════════════════
REQUIREMENTS:
- React to THIS headline specifically
- Use the actual names/numbers from the headline
- Don't be generic - be specific to this news
- Each post in the batch gets a DIFFERENT trend
═══════════════════════════════════════════════════════════════════════════════"""


# Legacy compatibility
async def get_trending_news(self, force_refresh: bool = False) -> List[TrendingNews]:
    """Legacy method - returns all cached trends"""
    if force_refresh or not self.cached_trends or self._cache_expired():
        await self._refresh_trends()
    return self.cached_trends


# Singleton
_trend_service: Optional[TrendService] = None

def get_trend_service() -> TrendService:
    global _trend_service
    if _trend_service is None:
        _trend_service = TrendService()
    return _trend_service