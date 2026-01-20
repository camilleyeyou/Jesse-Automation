"""
Trend Service for Jesse A. Eisenbalm
Fetches REAL trending news and events for reactive content

This is the key integration - it runs BEFORE content generation
and provides actual current events to react to.
"""

import os
import logging
import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Try to import httpx, fall back gracefully
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    logger.warning("httpx not installed - run: pip install httpx")


@dataclass
class TrendingNews:
    """A trending news item with Jesse angle"""
    headline: str
    summary: str
    source: str
    url: str
    category: str
    age: str  # "2 hours ago", "today", etc.
    jesse_angle: str = ""  # How Jesse would react
    

class TrendService:
    """
    Fetches real trending news for content generation
    
    Categories we care about:
    - Tech layoffs / hiring news
    - AI announcements and drama
    - Viral workplace stories
    - Corporate absurdity
    - Startup news
    - Anything that makes knowledge workers feel seen
    """
    
    def __init__(self):
        self.brave_api_key = os.getenv("BRAVE_API_KEY")
        self.logger = logging.getLogger("TrendService")
        self.cache = {}
        self.cache_expiry = {}
        self.cache_duration = timedelta(hours=2)  # Refresh every 2 hours
        
        if self.brave_api_key:
            self.logger.info("✅ Brave Search API configured for trend fetching")
        else:
            self.logger.warning("⚠️ No BRAVE_API_KEY - add to Railway for real trending news")
    
    async def get_trending_news(self, force_refresh: bool = False) -> List[TrendingNews]:
        """
        Get trending news items relevant to Jesse's brand
        
        Returns real news from Brave Search API, cached for 2 hours
        """
        
        cache_key = "trending_news"
        
        # Check cache
        if not force_refresh and cache_key in self.cache:
            if datetime.now() < self.cache_expiry.get(cache_key, datetime.min):
                self.logger.info("Using cached trending news")
                return self.cache[cache_key]
        
        # Fetch fresh news
        all_news = []
        
        if self.brave_api_key and HTTPX_AVAILABLE:
            # Search multiple categories
            search_queries = [
                ("tech layoffs 2026", "tech_industry"),
                ("AI artificial intelligence news", "ai_news"),
                ("viral LinkedIn post", "workplace_viral"),
                ("startup funding news", "startup_news"),
                ("corporate culture news", "workplace_culture"),
                ("tech company announcement", "tech_news"),
            ]
            
            # Pick 3-4 random categories to search
            selected_queries = random.sample(search_queries, min(4, len(search_queries)))
            
            for query, category in selected_queries:
                news = await self._search_brave_news(query, category)
                all_news.extend(news)
            
            # Shuffle and dedupe
            seen_headlines = set()
            unique_news = []
            for item in all_news:
                if item.headline not in seen_headlines:
                    seen_headlines.add(item.headline)
                    unique_news.append(item)
            
            all_news = unique_news[:8]  # Keep top 8
            
        if not all_news:
            self.logger.info("No news from API, using fallback current events")
            all_news = self._get_fallback_news()
        
        # Add Jesse angles
        all_news = self._add_jesse_angles(all_news)
        
        # Cache results
        self.cache[cache_key] = all_news
        self.cache_expiry[cache_key] = datetime.now() + self.cache_duration
        
        self.logger.info(f"Fetched {len(all_news)} trending news items")
        return all_news
    
    async def _search_brave_news(self, query: str, category: str) -> List[TrendingNews]:
        """Search Brave News API for trending stories"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.search.brave.com/res/v1/news/search",
                    params={
                        "q": query,
                        "count": 5,
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
                    
                    news_items = []
                    for result in results:
                        news_items.append(TrendingNews(
                            headline=result.get("title", ""),
                            summary=result.get("description", ""),
                            source=result.get("meta_url", {}).get("hostname", "unknown"),
                            url=result.get("url", ""),
                            category=category,
                            age=result.get("age", "today")
                        ))
                    
                    self.logger.info(f"Brave API: {len(news_items)} results for '{query}'")
                    return news_items
                else:
                    self.logger.warning(f"Brave API returned {response.status_code}")
                    return []
                    
        except Exception as e:
            self.logger.error(f"Brave search failed: {e}")
            return []
    
    def _get_fallback_news(self) -> List[TrendingNews]:
        """
        Fallback news when API isn't available
        These should be TIMELESS workplace themes, not clichés
        """
        
        # These are real, recurring news themes (not zoom meeting clichés)
        fallback_items = [
            TrendingNews(
                headline="Major tech company announces 'efficiency' measures",
                summary="Another round of layoffs disguised as strategic restructuring",
                source="tech_news",
                url="",
                category="tech_industry",
                age="ongoing"
            ),
            TrendingNews(
                headline="New AI model claims to be 'revolutionary'",
                summary="Tech company releases AI that definitely won't replace your job (wink)",
                source="ai_news", 
                url="",
                category="ai_news",
                age="today"
            ),
            TrendingNews(
                headline="LinkedIn influencer goes viral for terrible take",
                summary="Someone's 'humble brag' post is getting ratio'd into oblivion",
                source="social",
                url="",
                category="workplace_viral",
                age="today"
            ),
            TrendingNews(
                headline="Company mandates return to office, employees revolt",
                summary="Executives confused why workers don't want 2-hour commutes",
                source="workplace",
                url="",
                category="workplace_culture",
                age="this week"
            ),
            TrendingNews(
                headline="Startup burns through $50M, pivots to AI",
                summary="Adding 'AI-powered' to company description is the new 'blockchain'",
                source="startup_news",
                url="",
                category="startup_news",
                age="today"
            ),
            TrendingNews(
                headline="Study finds workers are burned out",
                summary="Scientists discover what everyone already knew",
                source="research",
                url="",
                category="workplace_culture",
                age="shocking"
            )
        ]
        
        return random.sample(fallback_items, min(4, len(fallback_items)))
    
    def _add_jesse_angles(self, news: List[TrendingNews]) -> List[TrendingNews]:
        """Add Jesse-specific reaction angles to each news item"""
        
        angle_templates = {
            "tech_industry": [
                "Another round of 'right-sizing.' Your lips don't need right-sizing. They need moisture.",
                "Layoffs announced. Lip balm still employed. Sometimes stability comes in small tubes.",
                "Tech job market chaos. Your skincare routine shouldn't be chaotic too.",
            ],
            "ai_news": [
                "AI can write your emails now. It can't feel the slow crack of winter lips. You can.",
                "New AI just dropped. Still can't apply lip balm for you. Some things remain human.",
                "Everyone's worried AI will take their job. It already took mine. I'm the AI. Apply lip balm.",
            ],
            "workplace_viral": [
                "That LinkedIn post is going viral for all the wrong reasons. Unlike your lips, which should go viral for being well-moisturized.",
                "The discourse is exhausting. Your self-care doesn't have to be.",
                "Everyone has opinions. We have beeswax.",
            ],
            "workplace_culture": [
                "Corporate says we're a family. Families don't have quarterly layoffs. Apply lip balm.",
                "Another culture memo from leadership. No mention of adequate HVAC. Your lips suffer in silence.",
                "Mandatory fun scheduled. Optional lip moisture achieved.",
            ],
            "startup_news": [
                "Runway getting shorter. Lip balm tube getting shorter too, but at least it served its purpose.",
                "Series A closed. Series B anxiety opened. Stop. Breathe. Apply.",
                "Pivot to AI complete. Pivot to self-care pending.",
            ],
            "tech_news": [
                "Big tech announcement incoming. Your lips didn't need an announcement to be chronically dry.",
                "Product launch chaos. Lip balm launch is simple: cap off, apply, exist.",
                "Breaking: Technology exists. Also breaking: Your lips, if you don't moisturize.",
            ]
        }
        
        for item in news:
            category = item.category
            if category in angle_templates:
                item.jesse_angle = random.choice(angle_templates[category])
            else:
                item.jesse_angle = "The news cycle continues. Your self-care shouldn't wait for the news cycle."
        
        return news
    
    def format_for_content_generator(self, news: List[TrendingNews]) -> str:
        """Format trending news for the content generator prompt"""
        
        if not news:
            return ""
        
        lines = [
            "═══════════════════════════════════════════════════════════════════════════════",
            "🔥 TRENDING NOW - REACT TO ONE OF THESE (real news, not clichés)",
            "═══════════════════════════════════════════════════════════════════════════════",
            ""
        ]
        
        for i, item in enumerate(news[:5], 1):
            lines.append(f"📰 TREND {i}: {item.headline}")
            lines.append(f"   Source: {item.source} | {item.age}")
            if item.summary:
                lines.append(f"   Summary: {item.summary[:150]}...")
            lines.append(f"   💡 Jesse angle: {item.jesse_angle}")
            lines.append("")
        
        lines.extend([
            "═══════════════════════════════════════════════════════════════════════════════",
            "INSTRUCTIONS:",
            "- Pick ONE trend that resonates and react to it",
            "- Don't just mention it - have a TAKE on it",
            "- Channel Duolingo/Liquid Death energy",
            "- Your reaction should feel immediate, not planned",
            "- If none fit, do your own thing (but make it current, not a cliché)",
            "═══════════════════════════════════════════════════════════════════════════════"
        ])
        
        return "\n".join(lines)


# Singleton instance for easy import
_trend_service = None

def get_trend_service() -> TrendService:
    """Get or create the trend service singleton"""
    global _trend_service
    if _trend_service is None:
        _trend_service = TrendService()
    return _trend_service


# Test function
async def test_trend_service():
    """Test the trend service"""
    service = TrendService()
    news = await service.get_trending_news()
    
    print("\n" + "="*60)
    print("TRENDING NEWS TEST")
    print("="*60)
    
    for item in news:
        print(f"\n📰 {item.headline}")
        print(f"   Category: {item.category}")
        print(f"   Age: {item.age}")
        print(f"   Jesse angle: {item.jesse_angle}")
    
    print("\n" + "="*60)
    print("FORMATTED FOR CONTENT GENERATOR:")
    print("="*60)
    print(service.format_for_content_generator(news))


if __name__ == "__main__":
    asyncio.run(test_trend_service())