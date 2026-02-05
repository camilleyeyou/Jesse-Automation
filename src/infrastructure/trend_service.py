"""
Trend Service - BRAVE SEARCH + GOOGLE TRENDS POWERED
- Uses Brave Search API to get REAL news articles with context
- Uses pytrends as supplementary source for trending topics
- Enriches bare Google Trends topics with Brave Search context
- Persists used topics in database to prevent repetition
- Falls back to curated trending topics when APIs fail
"""

import os
import re
import json
import sqlite3
import logging
import random
import hashlib
from typing import Optional, Set, List, Dict
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import pytrends
try:
    from pytrends.request import TrendReq
    PYTRENDS_AVAILABLE = True
except ImportError:
    PYTRENDS_AVAILABLE = False
    logger.warning("pytrends not installed. Run: pip install pytrends")

# httpx for Brave Search API
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


@dataclass
class TrendingNews:
    """A trending news item with rich context"""
    headline: str
    summary: str = ""
    source: str = "google_trends"
    url: str = ""
    category: str = "trending"
    fingerprint: str = ""
    description: str = ""
    related_articles: list = field(default_factory=list)
    jesse_angle: str = ""
    news_freshness: str = "today"


class TrendService:
    """
    Multi-source trend fetcher with rich news context.

    Priority chain:
    1. Brave Search API — real news articles with titles, descriptions, URLs
    2. Google Trends — trending topic names, enriched with Brave context
    3. Curated fallback list — evergreen topics
    """

    # Days to prevent topic reuse
    TOPIC_COOLDOWN_DAYS = 7

    # Brave Search category queries — balanced mix of positive, neutral, and critical
    CATEGORY_QUERIES = {
        "ai_innovation": "AI breakthrough innovation announcement today",
        "ai_news": "AI news update today",
        "workplace_culture": "workplace culture trend this week",
        "tech_news": "tech industry news today",
        "pop_culture": "trending pop culture news today",
        "startup_success": "startup launch success funding news today",
        "creative_tech": "creative technology art design trending today",
        "wellness_trend": "wellness trend self-care popular today",
        "business_milestone": "company milestone achievement announcement today",
        "viral_moment": "viral moment feel good story trending today",
    }

    def __init__(self, db_path: str = "data/automation/queue.db"):
        self.logger = logging.getLogger("TrendService")
        self.db_path = Path(db_path)

        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_database()

        # Track topics used in current batch
        self.batch_used_headlines: Set[str] = set()

        # Initialize Brave Search
        self.brave_api_key = os.getenv("BRAVE_API_KEY")
        if self.brave_api_key and HTTPX_AVAILABLE:
            self.logger.info("✅ Brave Search API configured — real news context enabled")
        else:
            if not self.brave_api_key:
                self.logger.info("⚠️ No BRAVE_API_KEY — Brave Search unavailable")
            if not HTTPX_AVAILABLE:
                self.logger.info("⚠️ httpx not installed — Brave Search unavailable")

        # Initialize pytrends connection
        self.pytrends = None
        if PYTRENDS_AVAILABLE:
            try:
                self.pytrends = TrendReq(
                    hl='en-US',
                    tz=360,
                    timeout=(10, 25),
                    retries=2,
                    backoff_factor=0.5
                )
                self.logger.info("✅ Google Trends (pytrends) initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize pytrends: {e}")
                self.pytrends = None
        else:
            self.logger.warning("⚠️ pytrends not available")

    def _init_database(self):
        """Initialize SQLite database for topic tracking"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS used_topics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        headline TEXT NOT NULL,
                        fingerprint TEXT UNIQUE,
                        category TEXT,
                        source TEXT,
                        url TEXT,
                        used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        post_id TEXT
                    )
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_fingerprint ON used_topics(fingerprint)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_used_at ON used_topics(used_at)
                """)
                conn.commit()
                self.logger.info(f"📊 Topic tracking database initialized at {self.db_path}")
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")

    def _generate_fingerprint(self, headline: str, summary: str = "") -> str:
        """Generate a fingerprint to identify similar topics"""
        text = f"{headline} {summary}".lower()

        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                     'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                     'would', 'could', 'should', 'may', 'might', 'must', 'shall',
                     'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
                     'as', 'into', 'through', 'during', 'before', 'after', 'above',
                     'below', 'between', 'under', 'again', 'further', 'then', 'once',
                     'and', 'but', 'or', 'nor', 'so', 'yet', 'both', 'either',
                     'neither', 'not', 'only', 'own', 'same', 'than', 'too', 'very',
                     'just', 'about', 'also', 'now', 'new', 'says', 'said', 'news',
                     'today', 'report', 'reports', 'latest', 'breaking', 'trending'}

        words = re.findall(r'[a-z0-9]+', text)
        key_words = [w for w in words if w not in stopwords and len(w) > 2]
        key_words = sorted(set(key_words))[:8]

        fingerprint_text = ' '.join(key_words)
        return hashlib.md5(fingerprint_text.encode()).hexdigest()[:16]

    def _is_topic_used(self, fingerprint: str) -> bool:
        """Check if a topic fingerprint was used in the cooldown period"""
        if fingerprint in self.batch_used_headlines:
            return True

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

    def mark_topic_used_permanent(self, trend: TrendingNews, post_id: str = None):
        """Public method to mark a topic as used (called after successful post)"""
        self._record_used_topic(trend, post_id)

    async def get_one_fresh_trend(self, post_id: str = None) -> Optional[TrendingNews]:
        """
        Fetch ONE fresh trending topic with rich context.

        Priority chain:
        1. Brave Search API (real news with titles, descriptions, URLs)
        2. Google Trends (topic names, enriched with Brave context)
        3. Curated fallback list
        """

        # Try Brave Search first (richest context)
        if self.brave_api_key and HTTPX_AVAILABLE:
            trend = await self._get_brave_news_trend(post_id)
            if trend:
                return trend

        # Try Google Trends (less context, but real trending data)
        if self.pytrends:
            trend = await self._get_google_trend(post_id)
            if trend:
                # Enrich bare topic with Brave context
                if self.brave_api_key and HTTPX_AVAILABLE:
                    trend = await self._enrich_with_brave(trend)
                return trend

        # Fallback to curated trending topics
        return await self._get_fallback_trend(post_id)

    async def _get_brave_news_trend(self, post_id: str = None) -> Optional[TrendingNews]:
        """Fetch trending news from Brave Search API with rich context"""

        # Shuffle categories for variety
        categories = list(self.CATEGORY_QUERIES.items())
        random.shuffle(categories)

        for category_name, query in categories:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        "https://api.search.brave.com/res/v1/news/search",
                        params={"q": query, "count": 5, "freshness": "pd"},
                        headers={
                            "X-Subscription-Token": self.brave_api_key,
                            "Accept": "application/json"
                        },
                        timeout=10.0
                    )

                    if response.status_code != 200:
                        self.logger.warning(f"Brave search failed for {category_name}: {response.status_code}")
                        continue

                    data = response.json()
                    results = data.get("results", [])

                    if not results:
                        continue

                    for result in results:
                        title = result.get("title", "")
                        description = result.get("description", "")
                        url = result.get("url", "")

                        if not title:
                            continue

                        trend = TrendingNews(
                            headline=title,
                            summary=description[:200] if description else f"Trending: {title}",
                            description=description,
                            source="brave_search",
                            url=url,
                            category=category_name,
                            news_freshness="today",
                            related_articles=[
                                {
                                    "title": r.get("title", ""),
                                    "snippet": r.get("description", "")[:100],
                                    "url": r.get("url", "")
                                }
                                for r in results[1:4]
                            ]
                        )
                        trend.fingerprint = self._generate_fingerprint(trend.headline, trend.summary)

                        if not self._is_topic_used(trend.fingerprint):
                            self._record_used_topic(trend, post_id)
                            self.logger.info(f"✅ Selected Brave news [{category_name}]: {title[:70]}...")
                            return trend

            except Exception as e:
                self.logger.error(f"Brave search error for {category_name}: {e}")
                continue

        self.logger.warning("No fresh Brave news found across all categories")
        return None

    async def _enrich_with_brave(self, trend: TrendingNews) -> TrendingNews:
        """Enrich a bare Google Trends topic with real news context from Brave"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.search.brave.com/res/v1/news/search",
                    params={
                        "q": f"{trend.headline} news today",
                        "count": 3,
                        "freshness": "pw"
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

                    if results:
                        top = results[0]
                        trend.summary = top.get("description", trend.summary)[:200]
                        trend.description = top.get("description", "")
                        trend.url = top.get("url", trend.url)
                        trend.source = "google_trends+brave"
                        trend.news_freshness = "today"
                        trend.related_articles = [
                            {
                                "title": r.get("title", ""),
                                "snippet": r.get("description", "")[:100],
                                "url": r.get("url", "")
                            }
                            for r in results[1:4]
                        ]
                        self.logger.info(f"✅ Enriched Google Trend '{trend.headline}' with Brave context")
        except Exception as e:
            self.logger.warning(f"Brave enrichment failed for '{trend.headline}': {e}")

        return trend

    async def _get_google_trend(self, post_id: str = None) -> Optional[TrendingNews]:
        """Get a trending topic from Google Trends"""
        try:
            self.logger.info("🔍 Fetching Google Trends daily searches...")

            trending_df = self.pytrends.trending_searches(pn='united_states')

            if trending_df is None or trending_df.empty:
                self.logger.warning("No trending searches returned")
                return None

            trending_topics = trending_df[0].tolist()

            self.logger.info(f"📈 Found {len(trending_topics)} trending topics from Google Trends")

            random.shuffle(trending_topics)

            for topic in trending_topics:
                trend = TrendingNews(
                    headline=topic,
                    summary=f"Currently trending on Google: {topic}",
                    source="google_trends",
                    category="trending",
                    url=f"https://trends.google.com/trends/explore?q={topic.replace(' ', '%20')}&geo=US"
                )
                trend.fingerprint = self._generate_fingerprint(trend.headline, trend.summary)

                if not self._is_topic_used(trend.fingerprint):
                    self._record_used_topic(trend, post_id)
                    self.logger.info(f"✅ Selected Google Trend: {topic}")
                    return trend
                else:
                    self.logger.debug(f"⏭️ Skipping used topic: {topic}")

            self.logger.warning("All Google Trends topics have been used recently")
            return None

        except Exception as e:
            self.logger.error(f"Google Trends error: {e}")
            return None

    async def _get_realtime_trends(self, post_id: str = None) -> Optional[TrendingNews]:
        """Get realtime trending searches (backup method)"""
        try:
            self.logger.info("🔍 Fetching realtime Google Trends...")

            realtime_df = self.pytrends.realtime_trending_searches(pn='US')

            if realtime_df is None or realtime_df.empty:
                return None

            for _, row in realtime_df.iterrows():
                title = row.get('title', '')
                if not title:
                    continue

                trend = TrendingNews(
                    headline=title,
                    summary=str(row.get('entityNames', '')),
                    source="google_trends_realtime",
                    category="trending"
                )
                trend.fingerprint = self._generate_fingerprint(trend.headline, trend.summary)

                if not self._is_topic_used(trend.fingerprint):
                    self._record_used_topic(trend, post_id)
                    self.logger.info(f"✅ Selected realtime trend: {title}")
                    return trend

            return None

        except Exception as e:
            self.logger.error(f"Realtime trends error: {e}")
            return None

    async def _get_fallback_trend(self, post_id: str = None) -> TrendingNews:
        """Return a curated fallback trend when all APIs fail"""

        fallbacks = [
            TrendingNews(
                headline="Taylor Swift",
                summary="Taylor Swift continues to dominate headlines with tour and music news",
                source="fallback", category="celebrity",
            ),
            TrendingNews(
                headline="Beyoncé",
                summary="Beyoncé remains in the spotlight with new projects and appearances",
                source="fallback", category="celebrity",
            ),
            TrendingNews(
                headline="Travis Kelce",
                summary="NFL star Travis Kelce trending for football and personal life",
                source="fallback", category="sports",
            ),
            TrendingNews(
                headline="Drake",
                summary="Drake making headlines in music industry",
                source="fallback", category="music",
            ),
            TrendingNews(
                headline="Kendrick Lamar",
                summary="Kendrick Lamar trending for music releases and cultural impact",
                source="fallback", category="music",
            ),
            TrendingNews(
                headline="NFL Playoffs",
                summary="NFL playoff drama captivates fans nationwide",
                source="fallback", category="sports",
            ),
            TrendingNews(
                headline="NBA Trade Rumors",
                summary="NBA teams making moves as trade deadline approaches",
                source="fallback", category="sports",
            ),
            TrendingNews(
                headline="LeBron James",
                summary="LeBron James continues to make basketball history",
                source="fallback", category="sports",
            ),
            TrendingNews(
                headline="Netflix",
                summary="Netflix releases new hit show that everyone is watching",
                source="fallback", category="entertainment",
            ),
            TrendingNews(
                headline="Oscar Nominations",
                summary="Hollywood buzzing about award season predictions",
                source="fallback", category="entertainment",
            ),
            TrendingNews(
                headline="Timothée Chalamet",
                summary="Timothée Chalamet trending for new film project",
                source="fallback", category="celebrity",
            ),
            TrendingNews(
                headline="Zendaya",
                summary="Zendaya making headlines for fashion and film",
                source="fallback", category="celebrity",
            ),
            TrendingNews(
                headline="iPhone",
                summary="Apple iPhone news continues to trend among consumers",
                source="fallback", category="tech",
            ),
            TrendingNews(
                headline="Elon Musk",
                summary="Elon Musk creates controversy with latest statements",
                source="fallback", category="tech",
            ),
            TrendingNews(
                headline="ChatGPT",
                summary="AI chatbot continues to spark debates about technology",
                source="fallback", category="tech",
            ),
            TrendingNews(
                headline="TikTok Trend",
                summary="New viral TikTok challenge takes over social media",
                source="fallback", category="viral",
            ),
            TrendingNews(
                headline="Super Bowl",
                summary="Super Bowl anticipation builds as teams compete",
                source="fallback", category="sports",
            ),
            TrendingNews(
                headline="Coachella",
                summary="Music festival announcements generate excitement",
                source="fallback", category="entertainment",
            ),
            TrendingNews(
                headline="The Bachelor",
                summary="Reality TV drama unfolds on latest season",
                source="fallback", category="entertainment",
            ),
            TrendingNews(
                headline="Real Housewives",
                summary="Reality TV franchise drama trending on social media",
                source="fallback", category="entertainment",
            ),
        ]

        for fb in fallbacks:
            fb.fingerprint = self._generate_fingerprint(fb.headline, fb.summary)

        random.shuffle(fallbacks)

        for fb in fallbacks:
            if not self._is_topic_used(fb.fingerprint):
                self._record_used_topic(fb, post_id)
                self.logger.info(f"📌 Using fallback topic: {fb.headline}")
                return fb

        self.logger.warning("⚠️ All fallback topics used — selecting random")
        chosen = random.choice(fallbacks)
        return chosen

    def reset_batch_tracking(self):
        """Reset batch-level tracking (call at start of new batch)"""
        self.batch_used_headlines.clear()
        self.logger.info("🔄 Reset batch tracking")

    def reset_for_new_batch(self):
        """Alias for reset_batch_tracking (used by orchestrator)"""
        self.reset_batch_tracking()

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

    def cleanup_old_topics(self, days: int = 30):
        """Remove topics older than specified days"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cutoff_date = datetime.now() - timedelta(days=days)
                cursor.execute("""
                    DELETE FROM used_topics WHERE used_at < ?
                """, (cutoff_date.isoformat(),))
                deleted = cursor.rowcount
                conn.commit()
                self.logger.info(f"🧹 Cleaned up {deleted} old topics")
        except Exception as e:
            self.logger.error(f"Error cleaning up topics: {e}")

    def get_stats(self) -> Dict:
        """Get service statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) FROM used_topics")
                total = cursor.fetchone()[0]

                cutoff = datetime.now() - timedelta(days=self.TOPIC_COOLDOWN_DAYS)
                cursor.execute("SELECT COUNT(*) FROM used_topics WHERE used_at > ?",
                             (cutoff.isoformat(),))
                in_cooldown = cursor.fetchone()[0]

                cursor.execute("""
                    SELECT category, COUNT(*) FROM used_topics
                    WHERE used_at > ? GROUP BY category
                """, (cutoff.isoformat(),))
                by_category = dict(cursor.fetchall())

                return {
                    "total_topics_used": total,
                    "in_cooldown_period": in_cooldown,
                    "cooldown_days": self.TOPIC_COOLDOWN_DAYS,
                    "by_category": by_category,
                    "pytrends_available": self.pytrends is not None,
                    "brave_search_available": self.brave_api_key is not None,
                    "source": "brave_search" if self.brave_api_key else ("google_trends" if self.pytrends else "fallback")
                }
        except Exception as e:
            self.logger.error(f"Error getting stats: {e}")
            return {"error": str(e)}


def get_trend_service(db_path: str = "data/automation/queue.db") -> TrendService:
    """Factory function to create a TrendService instance"""
    return TrendService(db_path=db_path)


# Convenience function for quick trend fetch
async def get_trending_topic() -> Optional[TrendingNews]:
    """Quick function to get a single trending topic"""
    service = TrendService()
    return await service.get_one_fresh_trend()
