"""
Trend Service for Jesse A. Eisenbalm
Fetches REAL trending news and events for reactive content

This is the key integration - it runs BEFORE content generation
and provides actual current events to react to.

UPDATED:
- More diverse search categories (not just tech)
- Better US focus with viral/cultural trends
- Improved caching and deduplication
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
    
    Categories we care about (EXPANDED beyond just tech):
    - Tech layoffs / hiring news
    - AI announcements and drama  
    - Viral workplace stories
    - Corporate absurdity
    - Startup news
    - Pop culture / viral moments
    - Sports highlights
    - Entertainment news
    - Economic / market news
    - Anything that makes people feel seen
    """
    
    def __init__(self):
        self.brave_api_key = os.getenv("BRAVE_API_KEY")
        self.logger = logging.getLogger("TrendService")
        self.cache = {}
        self.cache_expiry = {}
        self.cache_duration = timedelta(hours=1)  # Refresh every 1 hour for fresher content
        
        # Track used headlines to avoid repetition across batches
        self.used_headlines = set()
        self.used_headlines_max = 50  # Keep track of last 50 used headlines
        
        if self.brave_api_key:
            self.logger.info("✅ Brave Search API configured for trend fetching")
        else:
            self.logger.warning("⚠️ No BRAVE_API_KEY - add to Railway for real trending news")
    
    async def get_trending_news(self, force_refresh: bool = False) -> List[TrendingNews]:
        """
        Get trending news items relevant to Jesse's brand
        
        Returns real news from Brave Search API, cached for 1 hour
        """
        
        cache_key = "trending_news"
        
        # Check cache
        if not force_refresh and cache_key in self.cache:
            if datetime.now() < self.cache_expiry.get(cache_key, datetime.min):
                self.logger.info("Using cached trending news")
                # Filter out already-used headlines from cache
                cached = self.cache[cache_key]
                fresh = [n for n in cached if n.headline not in self.used_headlines]
                if len(fresh) >= 3:  # Need at least 3 fresh trends
                    return fresh
                # Otherwise, refresh
        
        # Fetch fresh news
        all_news = []
        
        if self.brave_api_key and HTTPX_AVAILABLE:
            # EXPANDED: More diverse search categories for US audience
            search_queries = [
                # Tech & Work (original)
                ("tech layoffs 2026", "tech_industry"),
                ("AI artificial intelligence news", "ai_news"),
                ("viral LinkedIn post", "workplace_viral"),
                ("startup funding news", "startup_news"),
                ("corporate culture news", "workplace_culture"),
                ("tech company announcement", "tech_news"),
                ("return to office RTO", "workplace_culture"),
                
                # Pop Culture & Entertainment (NEW)
                ("viral tweet today", "viral_social"),
                ("celebrity news today", "entertainment"),
                ("trending meme today", "viral_social"),
                ("Netflix show trending", "entertainment"),
                ("movie box office news", "entertainment"),
                
                # Sports (NEW)
                ("NFL news today", "sports"),
                ("NBA news today", "sports"),
                ("sports viral moment", "sports"),
                
                # Economy & Finance (NEW)
                ("stock market news today", "finance"),
                ("economy news today", "finance"),
                ("housing market news", "finance"),
                
                # General Viral (NEW)
                ("viral video today", "viral_social"),
                ("trending news USA today", "general_news"),
                ("weird news today", "weird_news"),
            ]
            
            # Pick 5-6 random categories to search (more diversity)
            selected_queries = random.sample(search_queries, min(6, len(search_queries)))
            
            for query, category in selected_queries:
                news = await self._search_brave_news(query, category)
                all_news.extend(news)
            
            # Shuffle and dedupe
            seen_headlines = set()
            unique_news = []
            for item in all_news:
                # Skip if we've used this headline recently
                if item.headline in self.used_headlines:
                    continue
                if item.headline not in seen_headlines:
                    seen_headlines.add(item.headline)
                    unique_news.append(item)
            
            all_news = unique_news[:10]  # Keep top 10 for more variety
            
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
    
    def mark_headline_used(self, headline: str):
        """Mark a headline as used to avoid repetition"""
        self.used_headlines.add(headline)
        # Trim if too many
        if len(self.used_headlines) > self.used_headlines_max:
            # Remove oldest (convert to list, slice, back to set)
            self.used_headlines = set(list(self.used_headlines)[-self.used_headlines_max:])
    
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
                elif response.status_code == 429:
                    self.logger.warning(f"Brave API rate limited (429) for '{query}'")
                    return []
                else:
                    self.logger.warning(f"Brave API returned {response.status_code}")
                    return []
                    
        except Exception as e:
            self.logger.error(f"Brave search failed: {e}")
            return []
    
    def _get_fallback_news(self) -> List[TrendingNews]:
        """
        Fallback news when API isn't available
        These should be TIMELESS workplace/cultural themes, not clichés
        """
        
        # These are real, recurring news themes (expanded beyond just tech)
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
            ),
            # NEW: Non-tech fallbacks
            TrendingNews(
                headline="Celebrity says something controversial on social media",
                summary="The internet has opinions",
                source="entertainment",
                url="",
                category="entertainment",
                age="today"
            ),
            TrendingNews(
                headline="Sports team makes surprising playoff run",
                summary="Fans go wild, bandwagon fills up fast",
                source="sports",
                url="",
                category="sports",
                age="today"
            ),
            TrendingNews(
                headline="New streaming show everyone's talking about",
                summary="Did you watch it yet? Everyone's asking",
                source="entertainment",
                url="",
                category="entertainment",
                age="this week"
            ),
            TrendingNews(
                headline="Stock market does something unexpected",
                summary="Experts pretend they saw it coming",
                source="finance",
                url="",
                category="finance",
                age="today"
            ),
        ]
        
        # Return a random selection
        return random.sample(fallback_items, min(6, len(fallback_items)))
    
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
                "Everyone's worried AI will take their job. Meanwhile, your lips are quietly suffering.",
            ],
            "workplace_viral": [
                "That post is going viral for all the wrong reasons. Unlike your lips, which should go viral for being moisturized.",
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
            ],
            # NEW: Angles for expanded categories
            "viral_social": [
                "The internet found a new main character today. Tomorrow it'll be someone else. Your lip care shouldn't be that chaotic.",
                "Everyone's watching that viral video. Nobody's watching their lip health. We see you.",
                "Social media moves fast. Self-care can move slow. That's allowed.",
            ],
            "entertainment": [
                "Everyone's talking about that show. Nobody's talking about lip care. That's our job.",
                "Hot take: the best character development is your lips going from cracked to hydrated.",
                "Celebrity drama comes and goes. Dry lip season is eternal.",
            ],
            "sports": [
                "Big game energy. Small tube salvation. Sometimes the real wins are moisturized.",
                "Sports fans feel everything. Your lips shouldn't have to feel everything too.",
                "Victory lap? More like 'remember to reapply' lap.",
            ],
            "finance": [
                "Markets are volatile. Lip care shouldn't be. $12 for stability.",
                "Portfolio down? Lips hydrated? One of those things you can control.",
                "Financial advice: invest in your lips. Returns are immediate.",
            ],
            "general_news": [
                "The news cycle continues. Your self-care shouldn't wait for the news cycle.",
                "Breaking news: you deserve a moment of calm. Also breaking: your lips without moisture.",
                "Headlines come and go. Your lips are still there, still dry, still waiting.",
            ],
            "weird_news": [
                "The world is strange. Lip balm is simple. Sometimes simple wins.",
                "Weird things happen every day. Moisturizing your lips doesn't have to be one of them.",
                "In a world of chaos, be the person who remembered to bring lip balm.",
            ],
        }
        
        for item in news:
            category = item.category
            if category in angle_templates:
                item.jesse_angle = random.choice(angle_templates[category])
            else:
                # Default angle for unknown categories
                item.jesse_angle = "The world keeps spinning. Your lips keep drying. Jesse A. Eisenbalm keeps moisturizing."
        
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
        
        for i, item in enumerate(news[:6], 1):  # Show up to 6 trends
            category_emoji = {
                "tech_industry": "💼",
                "ai_news": "🤖",
                "workplace_viral": "📱",
                "startup_news": "🚀",
                "workplace_culture": "🏢",
                "tech_news": "💻",
                "viral_social": "🔥",
                "entertainment": "🎬",
                "sports": "⚽",
                "finance": "📈",
                "general_news": "📰",
                "weird_news": "🤯",
            }.get(item.category, "📰")
            
            lines.append(f"{category_emoji} TREND {i}: {item.headline}")
            lines.append(f"   Category: {item.category} | Source: {item.source} | {item.age}")
            if item.summary:
                lines.append(f"   Summary: {item.summary[:150]}...")
            lines.append(f"   💡 Jesse angle: {item.jesse_angle}")
            lines.append("")
        
        lines.extend([
            "═══════════════════════════════════════════════════════════════════════════════",
            "INSTRUCTIONS:",
            "- Pick ONE trend that resonates and react to it",
            "- Each post in a batch should use a DIFFERENT trend",
            "- Don't just mention it - have a TAKE on it",
            "- Channel Duolingo/Liquid Death energy",
            "- Your reaction should feel immediate, not planned",
            "- If none fit, do your own thing (but make it current, not a cliché)",
            "- IMPORTANT: Hook must be attention-grabbing and scroll-stopping",
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