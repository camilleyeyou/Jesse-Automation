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
    
    # Diverse search queries organized by category
    SEARCH_CATEGORIES = {
        "tech": [
            "tech layoffs 2026",
            "AI company news today",
            "startup funding news",
            "tech CEO controversy",
            "Silicon Valley news today",
            "cryptocurrency news today",
            "cybersecurity breach news",
        ],
        "business": [
            "corporate layoffs today",
            "CEO news today",
            "company scandal news",
            "business merger acquisition",
            "stock market news today",
            "retail store closings",
            "corporate earnings report",
        ],
        "viral": [
            "viral social media today",
            "trending Twitter X today",
            "viral TikTok news",
            "celebrity controversy today",
            "internet outrage today",
            "LinkedIn viral post",
        ],
        "politics": [
            "political news today USA",
            "government policy news",
            "election news today",
            "political controversy",
        ],
        "culture": [
            "workplace culture news",
            "remote work news today",
            "Gen Z workplace news",
            "corporate culture controversy",
            "office return mandate news",
        ],
        "economy": [
            "inflation news today",
            "housing market news",
            "job market news today",
            "recession fears news",
            "consumer spending news",
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
        """Return a diverse fallback trend when API fails"""
        
        # Extended diverse fallback pool
        fallbacks = [
            # Tech
            TrendingNews(
                headline="Tech giant announces surprise workforce reduction amid AI pivot",
                summary="Company cites need to 'reallocate resources' toward artificial intelligence",
                source="tech_news", category="tech",
            ),
            TrendingNews(
                headline="Startup founder's viral LinkedIn post about 'hustle culture' sparks debate",
                summary="Post claiming '4am wake-ups changed my life' draws mixed reactions",
                source="social", category="viral",
            ),
            TrendingNews(
                headline="Major company reverses remote work policy, mandates office return",
                summary="Employees express frustration over sudden policy change",
                source="business", category="culture",
            ),
            # Business
            TrendingNews(
                headline="CEO's 'we're a family' email precedes mass layoffs",
                summary="Workers share screenshots of contradictory corporate messaging",
                source="business", category="business",
            ),
            TrendingNews(
                headline="Company stock plummets after controversial executive decision",
                summary="Shareholders demand accountability from leadership",
                source="finance", category="business",
            ),
            # Culture
            TrendingNews(
                headline="Gen Z workers push back against 'productivity theater' in offices",
                summary="Younger employees question value of mandatory in-person attendance",
                source="culture", category="culture",
            ),
            TrendingNews(
                headline="LinkedIn 'thought leader' faces backlash for tone-deaf career advice",
                summary="Post suggesting workers 'just be grateful' goes viral for wrong reasons",
                source="social", category="viral",
            ),
            # Economy
            TrendingNews(
                headline="Housing market shows signs of strain as prices continue rising",
                summary="First-time buyers increasingly priced out of market",
                source="economy", category="economy",
            ),
            TrendingNews(
                headline="Inflation concerns persist as everyday costs squeeze consumers",
                summary="Families adjust budgets amid rising prices",
                source="economy", category="economy",
            ),
            # Viral/Social
            TrendingNews(
                headline="Corporate jargon reaches new heights with latest buzzword trend",
                summary="'Synergize your bandwidth' and other phrases workers love to hate",
                source="viral", category="viral",
            ),
            TrendingNews(
                headline="Employee's honest Glassdoor review goes viral",
                summary="Candid assessment of workplace culture resonates with thousands",
                source="social", category="viral",
            ),
            TrendingNews(
                headline="Company's AI chatbot gives hilariously wrong customer advice",
                summary="Screenshots of bot confusion spread across social media",
                source="tech", category="tech",
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