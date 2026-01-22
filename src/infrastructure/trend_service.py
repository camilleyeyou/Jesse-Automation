"""
Trend Service - ENHANCED with Database Tracking
- Fetches diverse trending news across multiple categories
- Persists used topics in database to prevent repetition
- Tracks topics for configurable days (default: 7 days)
- Uses category rotation to ensure variety
- Extracts topic "fingerprints" to catch similar stories
"""

import os
import re
import json
import sqlite3
import logging
import random
import hashlib
from typing import Optional, Set, List, Dict
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path

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
    fingerprint: str = ""  # For similarity detection


class TrendService:
    """
    Enhanced trend fetcher with persistent topic tracking.
    
    Key improvements:
    - Database persistence of used topics (no repeats for X days)
    - Multiple diverse news categories with rotation
    - Fingerprint-based similarity detection
    - Fallback topic pool that's also tracked
    """
    
    # Diverse search queries organized by category - MAINSTREAM CULTURE FOCUS
    SEARCH_CATEGORIES = {
        "pop_culture": [
            "celebrity news today",
            "trending celebrity drama",
            "famous people controversy today",
            "Hollywood news today",
            "music artist news today",
            "reality TV drama today",
            "influencer drama news",
            "celebrity breakup news",
            "award show news",
        ],
        "entertainment": [
            "viral movie news today",
            "Netflix trending news",
            "streaming wars news",
            "TV show controversy",
            "box office news today",
            "music industry news",
            "concert tour news",
            "album release news today",
        ],
        "sports": [
            "NFL news today",
            "NBA news today",
            "sports drama today",
            "athlete controversy",
            "Super Bowl news",
            "Olympics news",
            "sports trade news",
            "coach fired news",
        ],
        "viral_social": [
            "viral TikTok today",
            "trending meme today",
            "Twitter X drama today",
            "social media outrage today",
            "viral video today",
            "internet celebrity news",
            "influencer scandal",
            "cancel culture news",
        ],
        "lifestyle": [
            "dating app news",
            "relationship trend news",
            "wellness trend controversy",
            "food trend news today",
            "travel chaos news",
            "fashion controversy today",
            "beauty industry news",
        ],
        "tech_mainstream": [
            "iPhone news today",
            "social media update news",
            "AI controversy mainstream",
            "Elon Musk news today",
            "Mark Zuckerberg news",
            "Apple news today",
            "Google controversy",
            "Amazon news today",
        ],
        "politics_culture": [
            "political drama today",
            "politician controversy",
            "White House news today",
            "Congress news today",
            "political scandal",
            "government shutdown news",
        ],
        "economy_personal": [
            "grocery prices news",
            "rent prices news today",
            "gas prices news",
            "layoffs news today",
            "job market news",
            "cost of living news",
            "minimum wage news",
        ]
    }
    
    # Days to prevent topic reuse
    TOPIC_COOLDOWN_DAYS = 7
    
    def __init__(self, db_path: str = "data/automation/queue.db"):
        self.brave_api_key = os.getenv("BRAVE_API_KEY")
        self.logger = logging.getLogger("TrendService")
        self.db_path = Path(db_path)
        
        # In-memory cache for current batch (supplements database)
        self.batch_used_headlines: Set[str] = set()
        
        # Track which categories we've used recently to rotate
        self.category_usage: Dict[str, int] = {cat: 0 for cat in self.SEARCH_CATEGORIES}
        
        # Initialize database table
        self._init_database()
        
        if self.brave_api_key:
            self.logger.info("✅ Brave Search API configured for trend fetching")
        else:
            self.logger.warning("⚠️ No BRAVE_API_KEY - will use fallbacks")
    
    def _init_database(self):
        """Initialize the used_topics table in the existing database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS used_topics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        headline TEXT NOT NULL,
                        fingerprint TEXT NOT NULL,
                        category TEXT,
                        source TEXT,
                        url TEXT,
                        used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        post_id TEXT,
                        UNIQUE(fingerprint)
                    )
                """)
                
                # Create index for faster lookups
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_used_topics_fingerprint 
                    ON used_topics(fingerprint)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_used_topics_used_at 
                    ON used_topics(used_at)
                """)
                
                conn.commit()
                self.logger.info("✅ Used topics database table initialized")
        except Exception as e:
            self.logger.error(f"Failed to init database: {e}")
    
    def reset_for_new_batch(self):
        """Reset batch-level tracking (database tracking persists)"""
        self.batch_used_headlines = set()
        self.logger.info("Reset batch-level headline tracking")
    
    def _generate_fingerprint(self, headline: str, summary: str = "") -> str:
        """
        Generate a fingerprint for similarity detection.
        Extracts key entities and concepts to catch similar stories.
        """
        text = f"{headline} {summary}".lower()
        
        # Remove common words
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 
                     'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                     'would', 'could', 'should', 'may', 'might', 'must', 'shall',
                     'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
                     'as', 'into', 'through', 'during', 'before', 'after', 'above',
                     'below', 'between', 'under', 'again', 'further', 'then', 'once',
                     'and', 'but', 'or', 'nor', 'so', 'yet', 'both', 'either',
                     'neither', 'not', 'only', 'own', 'same', 'than', 'too', 'very',
                     'just', 'about', 'also', 'now', 'new', 'says', 'said', 'news',
                     'today', 'report', 'reports', 'latest', 'breaking'}
        
        # Extract words (alphanumeric only)
        words = re.findall(r'[a-z0-9]+', text)
        
        # Filter stopwords and very short words
        key_words = [w for w in words if w not in stopwords and len(w) > 2]
        
        # Sort and take top 8 most significant words
        key_words = sorted(set(key_words))[:8]
        
        # Create hash from sorted key words
        fingerprint_text = ' '.join(key_words)
        return hashlib.md5(fingerprint_text.encode()).hexdigest()[:16]
    
    def _is_topic_used(self, fingerprint: str) -> bool:
        """Check if a topic fingerprint was used in the cooldown period"""
        # Check batch cache first
        if fingerprint in self.batch_used_headlines:
            return True
        
        # Check database
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cutoff_date = datetime.now() - timedelta(days=self.TOPIC_COOLDOWN_DAYS)
                
                cursor.execute("""
                    SELECT COUNT(*) FROM used_topics 
                    WHERE fingerprint = ? AND used_at > ?
                """, (fingerprint, cutoff_date.isoformat()))
                
                count = cursor.fetchone()[0]
                return count > 0
        except Exception as e:
            self.logger.error(f"Error checking used topic: {e}")
            return False
    
    def _record_used_topic(self, trend: TrendingNews, post_id: str = None):
        """Record a used topic in the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO used_topics 
                    (headline, fingerprint, category, source, url, used_at, post_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    trend.headline[:500],
                    trend.fingerprint,
                    trend.category,
                    trend.source,
                    trend.url,
                    datetime.now().isoformat(),
                    post_id
                ))
                conn.commit()
                
            self.batch_used_headlines.add(trend.fingerprint)
            self.logger.info(f"📝 Recorded used topic: {trend.headline[:50]}...")
            
        except Exception as e:
            self.logger.error(f"Error recording used topic: {e}")
    
    def _get_least_used_category(self) -> str:
        """Get the category that's been used least recently"""
        # Sort by usage count
        sorted_cats = sorted(self.category_usage.items(), key=lambda x: x[1])
        return sorted_cats[0][0]
    
    async def get_one_fresh_trend(self, post_id: str = None) -> Optional[TrendingNews]:
        """
        Fetch ONE fresh trending topic that hasn't been used recently.
        
        Strategy:
        1. Rotate through news categories for variety
        2. Search each category until we find an unused topic
        3. Check against database for recent usage
        4. Fall back to diverse fallback pool if needed
        """
        
        if not self.brave_api_key or not HTTPX_AVAILABLE:
            return await self._get_fallback_trend(post_id)
        
        # Get categories in order of least-used first
        sorted_categories = sorted(
            self.category_usage.items(), 
            key=lambda x: (x[1], random.random())  # Sort by usage, random tiebreaker
        )
        
        for category, _ in sorted_categories:
            queries = self.SEARCH_CATEGORIES[category].copy()
            random.shuffle(queries)
            
            for query in queries[:3]:  # Try up to 3 queries per category
                try:
                    trends = await self._search_brave(query, category)
                    
                    for trend in trends:
                        if not self._is_topic_used(trend.fingerprint):
                            # Found a fresh topic!
                            self._record_used_topic(trend, post_id)
                            self.category_usage[category] += 1
                            self.logger.info(f"✅ Fresh trend from '{category}': {trend.headline[:60]}...")
                            return trend
                    
                except Exception as e:
                    self.logger.warning(f"Search failed for '{query}': {e}")
                    continue
        
        # All API trends exhausted, use fallback
        self.logger.warning("All API trends used, trying fallback pool")
        return await self._get_fallback_trend(post_id)
    
    async def _search_brave(self, query: str, category: str = "general") -> List[TrendingNews]:
        """Search Brave News API for trending news"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.search.brave.com/res/v1/news/search",
                    params={
                        "q": query,
                        "count": 15,  # Get more results to filter
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
                        headline = r.get("title", "")
                        summary = r.get("description", "")
                        
                        trend = TrendingNews(
                            headline=headline,
                            summary=summary,
                            source=r.get("meta_url", {}).get("hostname", "news"),
                            url=r.get("url", ""),
                            category=category,
                            fingerprint=self._generate_fingerprint(headline, summary)
                        )
                        trends.append(trend)
                    
                    return trends
                    
                elif response.status_code == 429:
                    self.logger.warning(f"Brave API rate limited (429) for '{query}'")
                    return []
                else:
                    self.logger.warning(f"Brave API returned {response.status_code} for '{query}'")
                    return []
                    
        except Exception as e:
            self.logger.error(f"Brave search error: {e}")
            return []
    
    async def _get_fallback_trend(self, post_id: str = None) -> TrendingNews:
        """Return a diverse fallback trend when API fails - MAINSTREAM POP CULTURE FOCUS"""
        
        # Extended diverse fallback pool - POP CULTURE & MAINSTREAM
        fallbacks = [
            # Celebrity/Entertainment
            TrendingNews(
                headline="Taylor Swift announces surprise album drop during concert",
                summary="Swifties crash Ticketmaster for the 47th time this year",
                source="entertainment", category="pop_culture",
            ),
            TrendingNews(
                headline="Beyoncé spotted at Lakers game looking unbothered",
                summary="Internet loses collective mind over courtside footage",
                source="celebrity", category="pop_culture",
            ),
            TrendingNews(
                headline="Timothée Chalamet photographed looking pensive in New York",
                summary="Fans debate whether he's sad or just French",
                source="celebrity", category="pop_culture",
            ),
            TrendingNews(
                headline="Zendaya and Tom Holland seen holding hands again",
                summary="Couple continues to exist, internet continues to care",
                source="celebrity", category="pop_culture",
            ),
            TrendingNews(
                headline="Drake and Kendrick beef enters new chapter",
                summary="Music industry braces for more diss tracks",
                source="music", category="entertainment",
            ),
            # Sports
            TrendingNews(
                headline="LeBron James posts cryptic Instagram story",
                summary="NBA fans analyze every pixel for hidden meaning",
                source="sports", category="sports",
            ),
            TrendingNews(
                headline="Travis Kelce celebrates touchdown with suspicious dance move",
                summary="Taylor Swift seen laughing in private box",
                source="sports", category="sports",
            ),
            TrendingNews(
                headline="NFL referee makes controversial call in playoff game",
                summary="Twitter explodes with conspiracy theories",
                source="sports", category="sports",
            ),
            # Viral/Social Media
            TrendingNews(
                headline="New TikTok trend has everyone doing the same dance",
                summary="Your aunt will learn it in approximately 3 weeks",
                source="social", category="viral_social",
            ),
            TrendingNews(
                headline="Influencer's 'day in my life' video sparks heated debate",
                summary="People question whether anyone actually lives like this",
                source="social", category="viral_social",
            ),
            TrendingNews(
                headline="Celebrity's unfiltered selfie breaks Instagram record",
                summary="Fans praise authenticity of $500 skincare routine",
                source="social", category="viral_social",
            ),
            TrendingNews(
                headline="Dating app releases data on what profiles get most likes",
                summary="Results surprise absolutely no one",
                source="lifestyle", category="lifestyle",
            ),
            # TV/Streaming
            TrendingNews(
                headline="Netflix show finale leaves fans divided",
                summary="Ending described as 'perfect' and 'a war crime' simultaneously",
                source="entertainment", category="entertainment",
            ),
            TrendingNews(
                headline="Reality TV star says something controversial on reunion episode",
                summary="Producers definitely didn't plan this at all",
                source="entertainment", category="entertainment",
            ),
            # Tech but mainstream
            TrendingNews(
                headline="Elon Musk tweets something provocative again",
                summary="Stock price reacts, humanity sighs collectively",
                source="tech", category="tech_mainstream",
            ),
            TrendingNews(
                headline="Apple announces new iPhone with feature that already existed",
                summary="Pre-orders sell out in minutes anyway",
                source="tech", category="tech_mainstream",
            ),
            # Politics but pop culture adjacent
            TrendingNews(
                headline="Politician's outfit at event becomes main topic of discussion",
                summary="Policy takes backseat to fashion critique",
                source="politics", category="politics_culture",
            ),
            TrendingNews(
                headline="First Lady seen reading specific book, internet investigates",
                summary="Book sales increase 4000% overnight",
                source="politics", category="politics_culture",
            ),
            # Lifestyle/Trends
            TrendingNews(
                headline="New wellness trend promises to change your life completely",
                summary="Involves waking up early and drinking something green",
                source="lifestyle", category="lifestyle",
            ),
            TrendingNews(
                headline="Avocado toast prices reach new heights in major cities",
                summary="Millennials blamed for economy again somehow",
                source="lifestyle", category="economy_personal",
            ),
        ]
        
        # Generate fingerprints for fallbacks
        for fb in fallbacks:
            fb.fingerprint = self._generate_fingerprint(fb.headline, fb.summary)
        
        # Shuffle and find unused
        random.shuffle(fallbacks)
        
        for fb in fallbacks:
            if not self._is_topic_used(fb.fingerprint):
                self._record_used_topic(fb, post_id)
                return fb
        
        # All fallbacks used in cooldown period - return random with warning
        self.logger.warning("⚠️ All fallback topics used recently - selecting random")
        chosen = random.choice(fallbacks)
        return chosen
    
    def get_recent_topics(self, limit: int = 20) -> List[Dict]:
        """Get recently used topics for debugging/display"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT headline, category, source, used_at 
                    FROM used_topics 
                    ORDER BY used_at DESC 
                    LIMIT ?
                """, (limit,))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Error getting recent topics: {e}")
            return []
    
    def mark_topic_used_permanent(self, headline: str, category: str = ""):
        """
        Mark a topic as permanently used (after successful post).
        Alias for _record_used_topic that can be called externally.
        """
        trend = TrendingNews(
            headline=headline,
            category=category,
            fingerprint=self._generate_fingerprint(headline)
        )
        self._record_used_topic(trend, post_id="published")
        self.logger.info(f"✅ Topic permanently marked as used: {headline[:50]}...")
    
    def cleanup_old_topics(self, days: int = 30):
        """Remove topics older than specified days"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cutoff = datetime.now() - timedelta(days=days)
                cursor.execute(
                    "DELETE FROM used_topics WHERE used_at < ?", 
                    (cutoff.isoformat(),)
                )
                deleted = cursor.rowcount
                conn.commit()
                self.logger.info(f"🧹 Cleaned up {deleted} old topics")
                return deleted
        except Exception as e:
            self.logger.error(f"Error cleaning up topics: {e}")
            return 0


# Singleton
_trend_service: Optional[TrendService] = None

def get_trend_service(db_path: str = "data/automation/queue.db") -> TrendService:
    global _trend_service
    if _trend_service is None:
        _trend_service = TrendService(db_path)
    return _trend_service