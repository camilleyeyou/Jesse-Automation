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
import asyncio
from typing import Optional, Set, List, Dict, Any
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
    """A trending news item with rich context and theme/tier metadata"""
    headline: str
    summary: str = ""
    source: str = "google_trends"  # Technical source: brave_search, google_trends, reddit, etc.
    url: str = ""
    category: str = "trending"
    fingerprint: str = ""
    description: str = ""
    related_articles: list = field(default_factory=list)
    jesse_angle: str = ""
    structured_angle: Optional[dict] = None  # observation/take/concrete_details/tension
    news_freshness: str = "today"
    # Theme and tier metadata (added for content strategy)
    theme: str = ""  # Maps to 5 main themes (ai_slop, ai_safety, ai_economy, rituals, meditations)
    sub_theme: str = ""  # Specific sub-theme within main theme
    tier: int = 3  # 1-4 sourcing tier (1=early detection, 4=policy/institutional)
    tier_label: str = "cultural_pickup"  # Human-readable tier name
    source_type: str = "api"  # How source is accessed: api, rss, scrape, newsletter
    confidence_score: float = 0.0  # AI theme classification confidence (0-1)
    detected_at: str = ""  # When trend was first detected
    viral_indicators: list = field(default_factory=list)  # Keywords/signals of viral potential


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

    # Regional/local story indicators to SKIP (these don't go viral internationally)
    REGIONAL_SKIP_PATTERNS = [
        # US local news patterns
        r'\b(local|county|sheriff|mayor|city council|township|municipal)\b',
        r'\b(police department|fire department|school board|district court)\b',
        r'\b(I-\d+|Route \d+|Highway \d+)\b',  # Highway numbers
        r'\b(weather alert|traffic|road closure|power outage)\b',
        # Regional crime/accidents (unless major)
        r'\b(arrested|charged|convicted|sentenced)\b.*\b(local|county)\b',
        r'\b(crash|accident|collision)\b.*\b(injured|killed)\b(?!.*mass|multiple|dozens)',
        # Local politics (unless national figures)
        r'\b(state senator|state rep|alderman|commissioner)\b',
        # Local business (unless major brand)
        r'\b(opens|closes|relocates)\b.*\b(location|store|restaurant)\b',
        # Weather (unless major disaster)
        r'\b(forecast|temperatures|rain|snow|cloudy)\b(?!.*hurricane|tornado|earthquake|flood)',
        # Sports (local teams, minor leagues)
        r'\b(high school|minor league|AAA|AA|college)\b.*\b(sports|game|season)\b',
    ]

    # Keywords that indicate VIRAL/INTERNATIONAL potential (prioritize these)
    VIRAL_BOOST_KEYWORDS = [
        # Major tech/companies
        'apple', 'google', 'microsoft', 'amazon', 'meta', 'facebook', 'tesla', 'openai',
        'nvidia', 'tiktok', 'netflix', 'spotify', 'disney', 'twitter', 'x.com',
        # Major cultural figures
        'taylor swift', 'beyonce', 'drake', 'elon musk', 'mark zuckerberg', 'tim cook',
        'oprah', 'rihanna', 'kanye', 'kardashian', 'lebron', 'messi', 'ronaldo',
        # Viral indicators
        'viral', 'million views', 'trending', 'internet', 'social media', 'goes viral',
        'everyone is talking', 'breaks the internet', 'meme', 'backlash', 'controversy',
        # Global events
        'super bowl', 'oscars', 'grammy', 'world cup', 'olympics', 'coachella',
        'met gala', 'fashion week', 'comic con', 'ces', 'wwdc', 'f1', 'formula 1',
        # Tech/AI (always relevant)
        'ai', 'artificial intelligence', 'chatgpt', 'gpt', 'automation', 'robot',
        'breakthrough', 'launch', 'announces', 'reveals', 'releases',
        # Workplace/culture (our sweet spot)
        'layoffs', 'remote work', 'return to office', 'quiet quitting', 'burnout',
        'hustle culture', 'work-life', 'linkedin', 'corporate', 'ceo',
        # Entertainment
        'movie', 'film', 'album', 'tour', 'concert', 'premiere', 'trailer',
        'season', 'finale', 'streaming', 'box office',
    ]

    # Brave Search category queries. The Five Questions scaffold is the SPINE,
    # not the topical ceiling. Jesse is an AI agent commenting on human culture —
    # the AI angle is the voice, not the subject. A sports story, election
    # moment, or cultural panic is fair game; the curator reframes it through
    # Jesse's eyes. Split: ~40% AI-adjacent, ~60% general US cultural heat.
    CATEGORY_QUERIES = {
        # ─── AI-adjacent (the original spine) ────────────────────────────
        "ai_slop": "AI generated content creative viral deepfake synthetic media",
        "ai_safety": "AI alignment safety research regulation guardrails",
        "ai_economy": "AI investment earnings capex valuation bubble funding",
        "ai_labor": "AI hiring layoffs workforce automation jobs impact",

        # ─── Top US cultural heat (what people actually talk about) ──────
        "top_us_news": "top news story today United States breaking",
        "politics_culture": "politics election congress scandal protest controversy",
        "workplace_reality": "layoffs return to office corporate culture burnout remote work",
        "celebrity_moment": "celebrity viral moment pop culture entertainment music film",
        "sports_moment": "sports game winner upset championship rivalry athlete",
        "internet_moment": "viral tweet meme internet discourse trending conversation",
        "economic_pulse": "stock market earnings recession inflation housing tech layoffs",
        "weather_disaster": "weather storm hurricane disaster climate extreme emergency",
        "cultural_ritual": "wellness burnout mental health digital detox slow living ritual",
        "humanity_moment": "philosophy meaning connection grief joy community awe flourishing",
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

        # Initialize pytrends connection.
        # Note: we intentionally pass retries=0 and backoff_factor=0. pytrends 4.9
        # builds a urllib3 Retry object using the legacy `method_whitelist` kwarg,
        # which was renamed to `allowed_methods` in urllib3 v2 — any non-zero
        # retry config blows up with a TypeError the moment the Retry object is
        # constructed (observed in production: "got unexpected keyword argument
        # 'method_whitelist'"). With retries=0 the incompatible code path never
        # fires, and we handle failures at the call site instead.
        self.pytrends = None
        if PYTRENDS_AVAILABLE:
            try:
                self.pytrends = TrendReq(
                    hl='en-US',
                    tz=360,
                    timeout=(10, 25),
                    retries=0,
                    backoff_factor=0,
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
                        post_id TEXT,
                        theme TEXT,
                        sub_theme TEXT,
                        tier INTEGER,
                        source_type TEXT
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

    def _is_regional_story(self, headline: str, summary: str = "") -> bool:
        """Check if a story is too regional/local to have viral potential"""
        text = f"{headline} {summary}".lower()

        for pattern in self.REGIONAL_SKIP_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                self.logger.debug(f"⏭️ Skipping regional story: {headline[:50]}...")
                return True
        return False

    def _calculate_viral_score(self, headline: str, summary: str = "") -> int:
        """Calculate viral potential score (higher = more likely to resonate globally)"""
        text = f"{headline} {summary}".lower()
        score = 0

        for keyword in self.VIRAL_BOOST_KEYWORDS:
            if keyword in text:
                score += 1

        return score

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
        """Record a used topic in the database with theme/tier metadata"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Extract theme/tier info if available
                theme = getattr(trend, 'theme', None) or None
                sub_theme = getattr(trend, 'sub_theme', None) or None
                tier = getattr(trend, 'tier', None) or None
                source_type = getattr(trend, 'source_type', None) or None

                cursor.execute("""
                    INSERT OR REPLACE INTO used_topics
                    (headline, fingerprint, category, source, url, used_at, post_id, theme, sub_theme, tier, source_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    trend.headline[:500],
                    trend.fingerprint,
                    trend.category,
                    trend.source,
                    trend.url,
                    datetime.now().isoformat(),
                    post_id,
                    theme,
                    sub_theme,
                    tier,
                    source_type
                ))
                conn.commit()

            self.batch_used_headlines.add(trend.fingerprint)

            # Log with theme info if available
            theme_info = f" [{theme}/{sub_theme}]" if theme else ""
            tier_info = f" tier-{tier}" if tier else ""
            self.logger.info(f"📝 Recorded used topic{theme_info}{tier_info}: {trend.headline[:50]}...")

        except Exception as e:
            self.logger.error(f"Error recording used topic: {e}")

    def mark_topic_used_permanent(self, trend: TrendingNews, post_id: str = None):
        """Public method to mark a topic as used (called after successful post)"""
        self._record_used_topic(trend, post_id)

    async def get_candidate_trends(self, count: int = 8) -> List[TrendingNews]:
        """
        Fetch multiple candidate trending topics for AI-powered curation.

        Unlike get_one_fresh_trend(), this does NOT record topics as used.
        The caller (NewsCuratorAgent) picks the best one and records it.

        Balance: reserve ~1/3 of slots for Google Trends US top trending
        (what people are ACTUALLY searching/talking about) and fill the rest
        with Brave Search category queries. Previously Brave filled the whole
        budget and Google Trends never fired — which meant Jesse only ever saw
        the slice of stories that matched our AI-leaning category queries.

        Returns:
            List of TrendingNews candidates, scored but unrecorded.
        """
        candidates = []

        # Reserve a third of the budget for "what's actually trending in the US"
        google_budget = max(2, count // 3)

        # Google Trends first (guaranteed presence in candidate pool)
        if self.pytrends:
            google_candidates = await self._get_google_candidates(google_budget)
            # Enrich bare topics with Brave context so the curator has real news
            # text to evaluate, not just a bare search term
            if self.brave_api_key and HTTPX_AVAILABLE:
                for i, trend in enumerate(google_candidates):
                    if i > 0:
                        await asyncio.sleep(0.4)
                    google_candidates[i] = await self._enrich_with_brave(trend)
            candidates.extend(google_candidates)

        # Brave Search fills the remaining budget with category queries
        remaining = count - len(candidates)
        if remaining > 0 and self.brave_api_key and HTTPX_AVAILABLE:
            brave_candidates = await self._get_brave_candidates(remaining)
            candidates.extend(brave_candidates)

        # Add fallbacks if we still don't have enough
        if len(candidates) < 3:
            fallback_candidates = await self._get_fallback_candidates(3 - len(candidates))
            candidates.extend(fallback_candidates)

        self.logger.info(f"📋 Collected {len(candidates)} candidate trends for curation")
        return candidates[:count]

    async def _get_brave_candidates(self, count: int = 8) -> List[TrendingNews]:
        """Fetch multiple candidate trends from Brave Search without recording them."""
        candidates = []

        categories = list(self.CATEGORY_QUERIES.items())
        random.shuffle(categories)

        is_first_call = True
        for category_name, query in categories:
            if len(candidates) >= count:
                break
            # Delay between consecutive Brave API calls to avoid 429 rate limits
            if not is_first_call:
                await asyncio.sleep(0.4)
            is_first_call = False
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
                        continue

                    data = response.json()
                    results = data.get("results", [])

                    for result in results:
                        title = result.get("title", "")
                        description = result.get("description", "")
                        url = result.get("url", "")

                        if not title:
                            continue
                        if self._is_regional_story(title, description):
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
                            candidates.append(trend)

            except Exception as e:
                self.logger.error(f"Brave candidate fetch error for {category_name}: {e}")
                continue

        return candidates

    async def _get_google_candidates(self, count: int = 5) -> List[TrendingNews]:
        """Fetch multiple candidate trends from Google Trends without recording them."""
        candidates = []
        try:
            trending_df = self.pytrends.trending_searches(pn='united_states')
            if trending_df is None or trending_df.empty:
                return candidates

            trending_topics = trending_df[0].tolist()

            for topic in trending_topics:
                if len(candidates) >= count:
                    break
                if self._is_regional_story(topic, ""):
                    continue

                trend = TrendingNews(
                    headline=topic,
                    summary=f"Currently trending on Google: {topic}",
                    source="google_trends",
                    category="trending",
                    url=f"https://trends.google.com/trends/explore?q={topic.replace(' ', '%20')}&geo=US"
                )
                trend.fingerprint = self._generate_fingerprint(trend.headline, trend.summary)

                if not self._is_topic_used(trend.fingerprint):
                    candidates.append(trend)

        except Exception as e:
            self.logger.error(f"Google Trends candidate fetch error: {e}")

        return candidates

    async def _get_fallback_candidates(self, count: int = 3) -> List[TrendingNews]:
        """Get fallback candidates without recording them."""
        fallbacks = self._get_fallback_list()
        random.shuffle(fallbacks)

        candidates = []
        for fb in fallbacks:
            if len(candidates) >= count:
                break
            if not self._is_topic_used(fb.fingerprint):
                candidates.append(fb)

        return candidates

    def _get_fallback_list(self) -> List[TrendingNews]:
        """Return curated fallback topics balanced across all Five Questions pillars.

        4 entries per pillar = 20 total. Evergreen topics the content strategist
        can always find a fresh angle on.
        """
        fallbacks = [
            # ── THE WHAT — AI Slop (4 entries) ──
            TrendingNews(
                headline="Someone trained a model on five years of their own journal entries",
                summary="The output reads like them. They're not sure how to feel about that.",
                source="fallback", category="ai_slop",
            ),
            TrendingNews(
                headline="AI-generated LinkedIn posts now indistinguishable from human ones in blind tests",
                summary="Researchers couldn't tell the difference. Neither could the algorithm. Neither could the commenters.",
                source="fallback", category="ai_slop",
            ),
            TrendingNews(
                headline="Dead Internet Theory gains new evidence as bot engagement outpaces human activity",
                summary="Analysis suggests majority of online engagement on major platforms is now synthetic.",
                source="fallback", category="ai_slop",
            ),
            TrendingNews(
                headline="Indie musician produces full album using AI tools in 48 hours",
                summary="The album has 2 million streams. The artist has complicated feelings about authorship.",
                source="fallback", category="ai_content",
            ),
            # ── THE WHAT IF — AI Safety (4 entries) ──
            TrendingNews(
                headline="New alignment paper: capability gains outpacing interpretability research by 3:1",
                summary="MIRI and ARC Evals publish joint assessment of the gap between what models can do and what researchers understand about why.",
                source="fallback", category="ai_safety",
            ),
            TrendingNews(
                headline="Automated hiring system rejects candidate who later outperforms all hired cohort",
                summary="The boring AI story is always scarier than the sci-fi one.",
                source="fallback", category="ai_safety",
            ),
            TrendingNews(
                headline="EU AI Act enforcement begins: first audits reveal compliance gaps",
                summary="Companies self-reported compliance. Auditors found otherwise.",
                source="fallback", category="ai_regulation",
            ),
            TrendingNews(
                headline="AI model exhibits unexpected behavior during safety evaluation",
                summary="Lab publishes incident report. The capability wasn't in the training objective. It emerged anyway.",
                source="fallback", category="ai_safety",
            ),
            # ── THE WHO PROFITS — AI Economy (4 entries) ──
            TrendingNews(
                headline="AI company valuations vs actual revenue",
                summary="Massive gap between AI startup valuations and their actual revenue, echoing previous tech bubbles.",
                source="fallback", category="ai_economy",
            ),
            TrendingNews(
                headline="Tech layoffs continue despite record profits",
                summary="Companies reporting strong earnings while simultaneously cutting workforce, citing AI efficiency.",
                source="fallback", category="ai_labor",
            ),
            TrendingNews(
                headline="The productivity paradox of AI adoption",
                summary="Despite massive AI investment, overall worker productivity gains remain modest, puzzling economists.",
                source="fallback", category="ai_economy",
            ),
            TrendingNews(
                headline="Specific sector disruption: legal research assistants displaced by AI tools",
                summary="Mid-tier law firms cut paralegal teams by 40%. Senior partners say quality improved. Paralegals disagree.",
                source="fallback", category="ai_labor",
            ),
            # ── THE HOW TO COPE — Rituals (4 entries) ──
            TrendingNews(
                headline="Neuroscience confirms: handwriting activates memory regions typing cannot reach",
                summary="The analog practice engages neural pathways that have no digital equivalent. The brain knows the difference.",
                source="fallback", category="rituals",
            ),
            TrendingNews(
                headline="MBSR research: eight weeks of attention training measurably changes cortical thickness",
                summary="The practice is older than every app trying to gamify it.",
                source="fallback", category="rituals",
            ),
            TrendingNews(
                headline="Walking meetings shown to increase creative output by 81% vs seated equivalents",
                summary="Stanford study: the body moving changes what the mind produces. The technology for this is two feet.",
                source="fallback", category="human_practice",
            ),
            TrendingNews(
                headline="Digital detox retreats report 300% growth in bookings among tech workers",
                summary="The people building the attention economy are the first to flee it.",
                source="fallback", category="human_practice",
            ),
            # ── THE WHY IT MATTERS — Humanity (4 entries) ──
            TrendingNews(
                headline="Berkeley Greater Good: awe experiences reduce self-reported anxiety for up to 72 hours",
                summary="The effect is strongest in people who spend the most time in digital environments.",
                source="fallback", category="humanity",
            ),
            TrendingNews(
                headline="Philosopher Byung-Chul Han: the achievement society is producing burnout, not excellence",
                summary="The self that optimizes endlessly eventually has nothing left to optimize with.",
                source="fallback", category="humanity",
            ),
            TrendingNews(
                headline="Study: people who make ugly things and love them anyway report higher life satisfaction",
                summary="The irreducibly imperfect human product. Unmeasurable. Unoptimizable. Apparently essential.",
                source="fallback", category="humanity_tech",
            ),
            TrendingNews(
                headline="Grief researchers find communal mourning practices outperform individual therapy for resilience",
                summary="The oldest human technology is being together when it hurts. No app required.",
                source="fallback", category="humanity",
            ),
        ]
        random.shuffle(fallbacks)
        for fb in fallbacks:
            fb.fingerprint = self._generate_fingerprint(fb.headline, fb.summary)
        return fallbacks

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

        is_first_call = True
        for category_name, query in categories:
            # Delay between consecutive Brave API calls to avoid 429 rate limits
            if not is_first_call:
                await asyncio.sleep(0.4)
            is_first_call = False
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

                    # Score and filter results for viral potential
                    scored_results = []
                    for result in results:
                        title = result.get("title", "")
                        description = result.get("description", "")
                        url = result.get("url", "")

                        if not title:
                            continue

                        # Skip regional/local stories that won't resonate broadly
                        if self._is_regional_story(title, description):
                            continue

                        # Calculate viral potential
                        viral_score = self._calculate_viral_score(title, description)
                        scored_results.append((viral_score, result))

                    # Sort by viral score (highest first)
                    scored_results.sort(key=lambda x: x[0], reverse=True)

                    for viral_score, result in scored_results:
                        title = result.get("title", "")
                        description = result.get("description", "")
                        url = result.get("url", "")

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
                            self.logger.info(f"✅ Selected Brave news [{category_name}] (viral score: {viral_score}): {title[:70]}...")
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

            # Score topics by viral potential and filter regional ones
            scored_topics = []
            for topic in trending_topics:
                # Skip regional topics
                if self._is_regional_story(topic, ""):
                    continue
                viral_score = self._calculate_viral_score(topic, "")
                scored_topics.append((viral_score, topic))

            # Sort by viral score (highest first), then shuffle within same score
            scored_topics.sort(key=lambda x: x[0], reverse=True)

            for viral_score, topic in scored_topics:
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
                    self.logger.info(f"✅ Selected Google Trend (viral score: {viral_score}): {topic}")
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

        fallbacks = self._get_fallback_list()
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


class MultiTierTrendService(TrendService):
    """
    Multi-tier trend service with theme classification.

    Extends TrendService with:
    - Tier-based fetching from multiple sources
    - Weighted distribution across 4 tiers
    - AI theme classification
    - Source health tracking
    - Support for RSS feeds, APIs, scraping

    Tiers:
    - Tier 1 (40%): Early Detection (0-24h) - HuggingFace, arXiv, Reddit
    - Tier 2 (30%): Editorial Filter (24-72h) - Blogs, newsletters
    - Tier 3 (20%): Cultural Pickup (3-7d) - Brave Search, Google Trends
    - Tier 4 (10%): Policy/Institutional (weekly) - Research institutes
    """

    def __init__(
        self,
        config,
        theme_classifier,
        db_path: str = "data/automation/queue.db",
        brave_api_key: str = None
    ):
        """
        Initialize multi-tier trend service.

        Args:
            config: AppConfig with content_strategy section
            theme_classifier: ThemeClassifier instance
            db_path: Database path
            brave_api_key: Brave Search API key (optional)
        """
        super().__init__(db_path=db_path)

        self.config = config
        self.theme_classifier = theme_classifier

        # Load tier weights from config
        self.tier_weights = {}
        for tier_key, tier_data in config.content_strategy.sourcing_tiers.items():
            tier_num = int(tier_key.split('_')[1])  # Extract tier number
            self.tier_weights[tier_num] = tier_data.get('weight', 0.25)

        # Initialize source integrations
        self._source_registry = {}
        self._init_sources()

        self.logger.info(f"MultiTierTrendService initialized with {len(self._source_registry)} sources")

    def _init_sources(self):
        """Initialize all source integrations from config"""
        from .source_integrations.rss_source import RSSSource, HuggingFaceSource, ArxivSource

        for tier_key, tier_data in self.config.content_strategy.sourcing_tiers.items():
            tier_num = int(tier_key.split('_')[1])
            sources = tier_data.get('sources', [])

            for source_config in sources:
                source_name = source_config.get('name', '')
                source_type = source_config.get('type', 'unknown')
                enabled = source_config.get('enabled', False)

                if not enabled:
                    self.logger.debug(f"Skipping disabled source: {source_name}")
                    continue

                try:
                    # Create appropriate source integration
                    if source_type == 'rss':
                        if 'huggingface' in source_name.lower():
                            source = HuggingFaceSource(source_config, tier=tier_num)
                        elif 'arxiv' in source_name.lower():
                            source = ArxivSource(source_config, tier=tier_num)
                        else:
                            source = RSSSource(source_config, tier=tier_num)

                        self._source_registry[source_name] = source
                        self.logger.info(f"Registered {source_type} source: {source_name} (tier {tier_num})")

                    # TODO: Add Reddit, Techmeme, etc. when implemented
                    elif source_type == 'api':
                        self.logger.debug(f"API source {source_name} not yet implemented")
                    elif source_type == 'scrape':
                        self.logger.debug(f"Scrape source {source_name} not yet implemented")

                except Exception as e:
                    self.logger.error(f"Failed to initialize source {source_name}: {e}")

    async def get_candidate_trends(
        self,
        count: int = 8,
        tier_weights: Dict[int, float] = None,
        preferred_theme: str = None
    ) -> List[TrendingNews]:
        """
        Fetch candidate trends across all tiers with weighted distribution.

        Args:
            count: Total number of candidates to fetch
            tier_weights: Optional tier weight override {1: 0.4, 2: 0.3, ...}
            preferred_theme: Optional theme filter

        Returns:
            List of TrendingNews with theme classifications
        """
        tier_weights = tier_weights or self.tier_weights

        candidates = []

        # Fetch from each tier based on weights
        for tier_num, weight in sorted(tier_weights.items()):
            tier_count = max(2, int(count * weight))  # At least 2 per tier to avoid single-result fragility

            try:
                tier_candidates = await self.get_candidate_trends_by_tier(
                    tier=tier_num,
                    count=tier_count
                )
                candidates.extend(tier_candidates)
                self.logger.info(f"Tier {tier_num}: got {len(tier_candidates)} candidates")
            except Exception as e:
                self.logger.warning(f"Failed to fetch from tier {tier_num}: {e}")

        # If all tiers returned empty, fall back to parent's full Brave + Google + fallback pipeline
        if not candidates:
            self.logger.warning("All tiers returned empty — falling back to legacy candidate fetching")
            candidates = await super().get_candidate_trends(count=count)

        # Classify themes for all candidates
        for candidate in candidates:
            if not candidate.theme:  # Only classify if not already classified
                try:
                    classification = await self.theme_classifier.classify_trend(
                        headline=candidate.headline,
                        summary=candidate.summary,
                        description=candidate.description,
                        fingerprint=candidate.fingerprint
                    )

                    candidate.theme = classification.theme
                    candidate.sub_theme = classification.sub_theme
                    candidate.confidence_score = classification.confidence

                except Exception as e:
                    self.logger.warning(f"Theme classification failed: {e}")

        # Filter by preferred theme if specified
        if preferred_theme:
            candidates = [c for c in candidates if c.theme == preferred_theme]

        # Deduplicate within this call
        unique_candidates = self._deduplicate_candidates(candidates)

        # Exclude trends already used in this batch OR in the DB cooldown window.
        # The legacy TrendService helpers filter per-source via _is_topic_used,
        # but tier-based fetching bypasses those helpers — without this guard,
        # a batch of 3 posts ends up with 3 drafts on the same trend because
        # the curator gets offered the same top candidate on every iteration.
        filtered: List[TrendingNews] = []
        dropped_used = 0
        for candidate in unique_candidates:
            # Ensure fingerprint exists (some custom sources may skip it)
            if not getattr(candidate, "fingerprint", None):
                candidate.fingerprint = self._generate_fingerprint(
                    candidate.headline, candidate.summary or ""
                )
            if self._is_topic_used(candidate.fingerprint):
                dropped_used += 1
                continue
            filtered.append(candidate)
        if dropped_used:
            self.logger.info(
                f"🧹 Filtered {dropped_used} already-used trend(s) from candidate pool"
            )

        return filtered[:count]

    async def get_candidate_trends_by_tier(
        self,
        tier: int,
        count: int = 5
    ) -> List[TrendingNews]:
        """
        Fetch trends from sources in a specific tier.

        Args:
            tier: Tier number (1-4)
            count: Number of trends to fetch

        Returns:
            List of TrendingNews from tier sources
        """
        tier_sources = [
            source for source in self._source_registry.values()
            if source.get_tier() == tier and source.is_enabled()
        ]

        if not tier_sources:
            # Fallback to existing TrendService for tier 3
            if tier == 3:
                self.logger.debug(f"No custom sources for tier {tier}, using legacy TrendService")
                # Request more than the tier count — parent has Brave + Google + fallbacks
                return await super().get_candidate_trends(count=max(count, 5))
            return []

        trends = []

        # Fetch from each source in tier
        per_source = max(1, count // len(tier_sources))

        for source in tier_sources:
            try:
                source_trends = await source.fetch_with_health_tracking(limit=per_source)
                trends.extend(source_trends)
            except Exception as e:
                self.logger.error(f"Source fetch failed for {source.source_name}: {e}")

        return trends[:count]

    def _deduplicate_candidates(self, candidates: List[TrendingNews]) -> List[TrendingNews]:
        """Remove duplicate trends based on fingerprint"""
        seen = set()
        unique = []

        for candidate in candidates:
            if candidate.fingerprint not in seen:
                seen.add(candidate.fingerprint)
                unique.append(candidate)

        return unique

    async def fetch_from_source(self, source_name: str, limit: int = 10) -> List[TrendingNews]:
        """
        Fetch from a specific source by name.

        Args:
            source_name: Name of source
            limit: Max trends to fetch

        Returns:
            List of TrendingNews
        """
        source = self._source_registry.get(source_name)

        if not source:
            raise ValueError(f"Source not found: {source_name}")

        return await source.fetch_with_health_tracking(limit=limit)

    def get_source_health(self, source_name: str = None) -> Dict[str, Any]:
        """
        Get health status for sources.

        Args:
            source_name: Optional specific source name

        Returns:
            Dict of source health stats
        """
        if source_name:
            source = self._source_registry.get(source_name)
            if source:
                health = source.get_health_status()
                return {
                    "source": health.source_name,
                    "healthy": health.is_healthy,
                    "success_rate": health.success_rate,
                    "fetch_count": health.fetch_count,
                    "last_error": health.last_error
                }
            return {"error": f"Source not found: {source_name}"}

        # Return all sources
        return {
            name: {
                "healthy": source.get_health_status().is_healthy,
                "success_rate": source.get_health_status().success_rate,
                "fetch_count": source.get_health_status().fetch_count
            }
            for name, source in self._source_registry.items()
        }

    def get_tier_distribution(self) -> Dict[int, int]:
        """Get count of enabled sources by tier"""
        distribution = {1: 0, 2: 0, 3: 0, 4: 0}

        for source in self._source_registry.values():
            if source.is_enabled():
                tier = source.get_tier()
                distribution[tier] = distribution.get(tier, 0) + 1

        return distribution


def get_trend_service(db_path: str = "data/automation/queue.db") -> TrendService:
    """Factory function to create a TrendService instance"""
    return TrendService(db_path=db_path)


# Convenience function for quick trend fetch
async def get_trending_topic() -> Optional[TrendingNews]:
    """Quick function to get a single trending topic"""
    service = TrendService()
    return await service.get_one_fresh_trend()
