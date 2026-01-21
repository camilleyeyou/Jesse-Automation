"""
Trend Service - SIMPLIFIED
- Fetches TOP trending news (not niche queries)
- ONE fresh trend per request
- NO caching (each post gets fresh data)
- Tracks used headlines in memory only during batch
"""

import os
import logging
import random
from typing import Optional, Set
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
    summary: str = ""
    source: str = ""
    url: str = ""
    category: str = ""


class TrendService:
    """
    Simple trend fetcher.
    
    Key principles:
    - Fetch what's ACTUALLY trending (top news, not niche searches)
    - One fresh API call per post
    - Track used headlines to avoid duplicates within batch
    - No persistent caching
    """
    
    def __init__(self):
        self.brave_api_key = os.getenv("BRAVE_API_KEY")
        self.logger = logging.getLogger("TrendService")
        
        # Only track used headlines during current batch (in memory)
        self.used_headlines: Set[str] = set()
        
        if self.brave_api_key:
            self.logger.info("✅ Brave Search API configured")
        else:
            self.logger.warning("⚠️ No BRAVE_API_KEY")
    
    def reset_for_new_batch(self):
        """Call at start of each batch to clear used headlines"""
        self.used_headlines = set()
        self.logger.info("Reset used headlines for new batch")
    
    async def get_one_fresh_trend(self) -> Optional[TrendingNews]:
        """
        Fetch ONE fresh trending topic that hasn't been used.
        
        Strategy: Search for TOP trending news, filter out used ones.
        """
        
        if not self.brave_api_key or not HTTPX_AVAILABLE:
            return self._get_fallback_trend()
        
        # Search queries that get ACTUAL top trending news
        # These are broad queries that return what's actually trending
        search_queries = [
            "breaking news today",
            "trending news USA",
            "top headlines today",
            "viral news today",
            "biggest story today",
        ]
        
        random.shuffle(search_queries)
        
        for query in search_queries:
            try:
                trends = await self._search_brave(query)
                
                # Find first trend we haven't used
                for trend in trends:
                    headline_key = trend.headline.lower()[:50]  # Normalize for comparison
                    
                    if headline_key not in self.used_headlines:
                        self.used_headlines.add(headline_key)
                        self.logger.info(f"✅ Fresh trend: {trend.headline[:60]}...")
                        return trend
                
            except Exception as e:
                self.logger.warning(f"Search failed for '{query}': {e}")
                continue
        
        # If all API trends are used, return a fallback
        self.logger.warning("All API trends used, using fallback")
        return self._get_fallback_trend()
    
    async def _search_brave(self, query: str) -> list:
        """Search Brave News API for trending news"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.search.brave.com/res/v1/news/search",
                    params={
                        "q": query,
                        "count": 10,  # Get more results to filter
                        "freshness": "pd",  # Past day only
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
                            category="trending"
                        ))
                    return trends
                    
                elif response.status_code == 429:
                    self.logger.warning("Brave API rate limited")
                    return []
                else:
                    return []
                    
        except Exception as e:
            self.logger.error(f"Brave search error: {e}")
            return []
    
    def _get_fallback_trend(self) -> TrendingNews:
        """Return a fallback trend when API fails"""
        
        fallbacks = [
            TrendingNews(
                headline="Tech industry continues layoff wave as companies focus on AI",
                summary="Major tech companies announce workforce reductions",
                source="tech_news", category="tech"
            ),
            TrendingNews(
                headline="CEO faces backlash after controversial company memo",
                summary="Corporate leadership under scrutiny",
                source="business", category="business"
            ),
            TrendingNews(
                headline="Social media reacts to latest viral moment",
                summary="Internet discourse continues",
                source="social", category="viral"
            ),
        ]
        
        # Find one we haven't used
        for fb in fallbacks:
            key = fb.headline.lower()[:50]
            if key not in self.used_headlines:
                self.used_headlines.add(key)
                return fb
        
        # All used, return random anyway
        return random.choice(fallbacks)


# Singleton
_trend_service: Optional[TrendService] = None

def get_trend_service() -> TrendService:
    global _trend_service
    if _trend_service is None:
        _trend_service = TrendService()
    return _trend_service