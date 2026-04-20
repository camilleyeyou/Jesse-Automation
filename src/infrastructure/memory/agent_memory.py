"""
Agent Memory System
====================

Provides three types of memory for AI agents:

1. CONTENT MEMORY
   - All generated posts with metadata
   - Topics and hooks used
   - Success/failure tracking
   - Prevents repetition

2. VALIDATOR LEARNING MEMORY
   - Feedback patterns per validator
   - What each validator likes/dislikes
   - Approval rates by content type
   - Specific critique themes

3. SESSION MEMORY
   - Current batch context
   - What's been generated this session
   - Prevents within-session repetition

4. POSITION MEMORY
   - What Jesse SAID about each topic
   - Sentiment and key claims tracked
   - Enables building on prior positions
   - Prevents accidental self-contradiction
"""

import json
import sqlite3
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class ContentMemoryEntry:
    """A remembered piece of content"""
    post_id: str
    batch_id: str
    content: str
    hook: str
    ending: str
    pillar: str
    format: str
    voice: str
    topic: Optional[str]
    trending_topic: Optional[str]
    was_approved: bool
    average_score: float
    created_at: str
    posted_to_linkedin: bool = False
    linkedin_engagement: Optional[Dict] = None


@dataclass
class ValidatorFeedback:
    """Feedback from a single validator"""
    validator_name: str
    post_id: str
    score: float
    approved: bool
    feedback: str
    strengths: List[str]
    weaknesses: List[str]
    pillar: str
    format: str
    created_at: str


@dataclass
class ValidatorPattern:
    """Learned pattern about what a validator prefers"""
    validator_name: str
    likes: List[str]
    dislikes: List[str]
    approval_rate: float
    avg_score: float
    best_pillars: List[str]
    worst_pillars: List[str]
    common_critiques: List[str]
    common_praise: List[str]


@dataclass
class SessionContext:
    """Current session/batch context"""
    session_id: str
    started_at: str
    posts_generated: int
    topics_used: List[str]
    hooks_used: List[str]
    endings_used: List[str]
    pillars_used: List[str]
    formats_used: List[str]


class AgentMemory:
    """
    Unified memory system for all agents.

    Usage:
        memory = get_memory()

        # Before generating content
        recent_topics = memory.get_recent_topics(days=7)
        avoid_hooks = memory.get_recent_hooks(limit=5)
        validator_prefs = memory.get_validator_preferences("SarahChen")

        # After generating content
        memory.remember_post(post, validation_scores, was_approved=True)

        # Session tracking
        memory.start_session("batch_123")
        memory.add_to_session(topic="AI meetings", hook="Breaking:")
        session = memory.get_session_context()
    """

    def __init__(self, db_path: str = "data/automation/queue.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Session memory (in-memory, resets each batch)
        self._session: Optional[SessionContext] = None

        self._init_database()
        logger.info(f"AgentMemory initialized at {self.db_path}")

    def _init_database(self):
        """Create memory tables if they don't exist"""

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("PRAGMA journal_mode=WAL")

            # Content memory - all generated posts
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS content_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id TEXT UNIQUE,
                    batch_id TEXT,
                    content TEXT NOT NULL,
                    hook TEXT,
                    ending TEXT,
                    pillar TEXT,
                    format TEXT,
                    voice TEXT,
                    topic TEXT,
                    trending_topic TEXT,
                    was_approved BOOLEAN DEFAULT FALSE,
                    average_score REAL DEFAULT 0,
                    posted_to_linkedin BOOLEAN DEFAULT FALSE,
                    linkedin_post_id TEXT,
                    linkedin_engagement TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    theme TEXT,
                    sub_theme TEXT,
                    trend_tier INTEGER
                )
            """)

            # Validator feedback memory
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS validator_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id TEXT,
                    validator_name TEXT NOT NULL,
                    score REAL,
                    approved BOOLEAN,
                    feedback TEXT,
                    strengths TEXT,
                    weaknesses TEXT,
                    pillar TEXT,
                    format TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (post_id) REFERENCES content_memory(post_id)
                )
            """)

            # Aggregated learnings (updated periodically)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_insights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    insight_type TEXT NOT NULL,
                    insight_key TEXT NOT NULL,
                    insight_value TEXT NOT NULL,
                    confidence REAL DEFAULT 0,
                    sample_count INTEGER DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(insight_type, insight_key)
                )
            """)

            # Editorial calendar — weekly plan from ContentStrategistAgent
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS editorial_calendar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scheduled_for DATE,
                    theme TEXT,
                    format TEXT,
                    angle_seed TEXT,
                    status TEXT DEFAULT 'planned',
                    post_id INTEGER,
                    created_by TEXT DEFAULT 'manual',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Strategy insights — accumulated editorial learnings
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS strategy_insights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    insight_type TEXT,
                    observation TEXT,
                    confidence REAL DEFAULT 0.0,
                    evidence_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_validated TIMESTAMP
                )
            """)

            # Client reviews — human feedback from client on content quality
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS client_reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id TEXT,
                    rating INTEGER,
                    category TEXT,
                    review_text TEXT,
                    addressed INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Position memory — what Jesse SAID about topics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS position_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id TEXT,
                    theme TEXT,
                    sub_theme TEXT,
                    topic TEXT,
                    position_summary TEXT,
                    sentiment TEXT,
                    key_claim TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Gold-standard posts — the curated corpus used for retrieval-augmented
            # voice grounding (Fix #4). The generator retrieves the top-K similar
            # gold-standard posts and injects them into the user prompt so it
            # learns voice by example rather than from a 400-line system prompt.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gold_standard_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    pillar TEXT,
                    format TEXT,
                    embedding BLOB,
                    notes TEXT,
                    curator TEXT DEFAULT 'manual',
                    source_post_id TEXT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Add missing columns to content_memory (safe ALTER TABLE)
            engagement_columns = [
                ("theme", "TEXT"),
                ("sub_theme", "TEXT"),
                ("trend_tier", "INTEGER"),
                ("engagement_score", "REAL"),
                ("reactions", "INTEGER DEFAULT 0"),
                ("comments", "INTEGER DEFAULT 0"),
                ("shares", "INTEGER DEFAULT 0"),
                ("impressions", "INTEGER DEFAULT 0"),
                ("performance_fetched_at", "TIMESTAMP"),
            ]
            for col_name, col_type in engagement_columns:
                try:
                    cursor.execute(f"ALTER TABLE content_memory ADD COLUMN {col_name} {col_type}")
                except sqlite3.OperationalError:
                    pass  # Column already exists

            # Create indexes for common queries
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_content_created ON content_memory(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_content_approved ON content_memory(was_approved)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_content_pillar ON content_memory(pillar)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_validator_name ON validator_memory(validator_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_editorial_scheduled ON editorial_calendar(scheduled_for)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_editorial_status ON editorial_calendar(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_strategy_type ON strategy_insights(insight_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_position_theme ON position_memory(theme)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_position_created ON position_memory(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_client_reviews_created ON client_reviews(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_client_reviews_addressed ON client_reviews(addressed)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_gold_pillar ON gold_standard_posts(pillar)")

            # Generator avoid-list — the closed-loop receiving end of the
            # QualityDriftAgent. When the supervisor detects recycled phrases,
            # template overuse, or voice drift, it writes entries here; the
            # content strategist reads them before each generation and injects
            # them into the VARIETY GUARD section of the user prompt. Entries
            # expire so short-term fixes don't permanently constrain the model.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS generator_avoid_list (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phrase TEXT NOT NULL,
                    reason TEXT,
                    category TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    active INTEGER DEFAULT 1
                )
            """)
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_avoid_active_expires "
                "ON generator_avoid_list(active, expires_at)"
            )

            # Phase 0 schema additions (2026-04-19) — observability for the new
            # AngleArchitect + register system. Idempotent: ALTER TABLE fails
            # silently when the column already exists, which is what we want on
            # subsequent startups. Each one wrapped in its own try/except.
            phase0_migrations = [
                # content_memory — richer per-post metadata
                "ALTER TABLE content_memory ADD COLUMN register TEXT",
                "ALTER TABLE content_memory ADD COLUMN blueprint TEXT",  # JSON blob
                "ALTER TABLE content_memory ADD COLUMN curator_angle TEXT",  # JSON blob
                # validator_memory — criteria_breakdown exposes which specific
                # diagnostic questions each validator actually ran, not just
                # the score
                "ALTER TABLE validator_memory ADD COLUMN criteria_breakdown TEXT",  # JSON
                # Phase 2 (2026-04-19): register-aware retrieval.
                # gold_standard_posts gains a register tag so retrieval can
                # bias toward the currently-picked register's specimens.
                "ALTER TABLE gold_standard_posts ADD COLUMN register TEXT",
            ]
            for sql in phase0_migrations:
                try:
                    cursor.execute(sql)
                except sqlite3.OperationalError as migration_err:
                    # Column already exists — expected on re-runs
                    if "duplicate column" not in str(migration_err).lower():
                        logger.warning(f"Migration skipped ({sql}): {migration_err}")

            # Index so register-rotation queries are fast
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_content_register "
                "ON content_memory(register)"
            )

            conn.commit()

        logger.debug("Memory tables initialized")

        # Auto-seed gold-standard corpus from the JSON files that ship with the
        # repo. Per-file idempotent: each seed file is identified by the curator
        # tag 'seed:{filename}', so a new seed file dropped into data/seeds/
        # gets loaded even when the table already has content from earlier
        # seeds. Matters on Railway where the DB sits on a persistent volume.
        self._autoseed_new_gold_standard_files()

    def _autoseed_new_gold_standard_files(self):
        """Load any data/seeds/gold_standard_*.json files that haven't been loaded yet.

        Per-file idempotence: for each seed file, we check if there's at least
        one gold_standard_posts row with curator = 'seed:{filename}'. If yes,
        we skip the whole file. If no, we load every specimen in it.

        This replaces the previous "if table is empty" short-circuit, which
        prevented new seed files from loading once ANY specimens existed —
        meaning the 2026-04-19 Liquid Death specimens would never have
        reached production on top of the existing Coachella corpus.

        File format expected:
            {"version": 1, "specimens": [
                {"content": ..., "pillar": ..., "format": ..., "notes": ...,
                 "curator": ..., "embedding": [float, ...]}, ...
            ]}
        """
        seeds_dir = Path(__file__).resolve().parent.parent.parent.parent / "data" / "seeds"
        if not seeds_dir.exists():
            return

        seed_files = sorted(seeds_dir.glob("gold_standard_*.json"))
        if not seed_files:
            return

        import json as _json
        total_loaded = 0
        for seed_file in seed_files:
            curator_tag = f"seed:{seed_file.name}"

            # Check if this specific seed file has already been loaded
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT COUNT(*) FROM gold_standard_posts WHERE curator = ?",
                        (curator_tag,),
                    )
                    already_loaded = cursor.fetchone()[0]
                if already_loaded > 0:
                    logger.debug(
                        f"Seed {seed_file.name} already loaded ({already_loaded} rows), skipping"
                    )
                    continue
            except Exception as e:
                logger.debug(f"Skipping autoseed check for {seed_file.name}: {e}")
                continue

            try:
                with open(seed_file) as f:
                    payload = _json.load(f)
                specimens = payload.get("specimens", [])
                if not isinstance(specimens, list):
                    continue
                file_loaded = 0
                for spec in specimens:
                    embedding = spec.get("embedding")
                    if not embedding or not isinstance(embedding, list):
                        continue
                    try:
                        self.add_gold_standard_post(
                            content=spec.get("content", ""),
                            pillar=spec.get("pillar"),
                            format=spec.get("format"),
                            embedding=embedding,
                            notes=spec.get("notes"),
                            curator=spec.get("curator") or curator_tag,
                            register=spec.get("register"),  # Phase 2
                        )
                        file_loaded += 1
                    except Exception as inner:
                        logger.warning(f"Failed to load specimen from {seed_file.name}: {inner}")
                if file_loaded:
                    logger.info(f"Autoseed: loaded {file_loaded} specimen(s) from {seed_file.name}")
                total_loaded += file_loaded
            except Exception as outer:
                logger.warning(f"Failed to read seed file {seed_file}: {outer}")

        if total_loaded:
            logger.info(f"✅ Autoseeded {total_loaded} new gold-standard specimen(s) total")

    # ═══════════════════════════════════════════════════════════════════════════
    # GOLD STANDARD POSTS (Fix #4 — retrieval-augmented voice grounding)
    # ═══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def _encode_embedding(embedding) -> bytes:
        """Serialize a float embedding vector as compact bytes for SQLite BLOB storage."""
        import array
        return array.array('f', embedding).tobytes()

    @staticmethod
    def _decode_embedding(blob: bytes):
        """Deserialize an embedding BLOB back to a list of floats."""
        import array
        a = array.array('f')
        a.frombytes(blob)
        return list(a)

    @staticmethod
    def _cosine_similarity(a, b) -> float:
        """Cosine similarity without numpy. Returns 0 if either vector is zero."""
        if not a or not b:
            return 0.0
        # Sum-of-products dot product
        dot = 0.0
        na = 0.0
        nb = 0.0
        # Guard mismatched lengths
        n = min(len(a), len(b))
        for i in range(n):
            ai = a[i]
            bi = b[i]
            dot += ai * bi
            na += ai * ai
            nb += bi * bi
        if na <= 0 or nb <= 0:
            return 0.0
        return dot / ((na ** 0.5) * (nb ** 0.5))

    def add_gold_standard_post(
        self,
        content: str,
        pillar: str = None,
        format: str = None,
        embedding=None,
        notes: str = None,
        curator: str = "manual",
        source_post_id: str = None,
        register: str = None,
    ) -> int:
        """Insert a gold-standard post (for retrieval-augmented voice grounding).

        Embedding should be a list of floats. If None, the row is stored without
        an embedding — search will skip it.

        Phase 2 (2026-04-19): `register` tags the specimen with its voice
        register (clinical_diagnostician / contrarian / prophet / confession
        / roast) so retrieval can bias toward the currently-picked register.
        """
        blob = self._encode_embedding(embedding) if embedding else None
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO gold_standard_posts
                   (content, pillar, format, embedding, notes, curator, source_post_id, register)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (content, pillar, format, blob, notes, curator, source_post_id, register),
            )
            conn.commit()
            return cursor.lastrowid

    def count_gold_standard_posts(self, pillar: str = None) -> int:
        """How many gold-standard posts are available (optionally scoped to a pillar)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if pillar:
                cursor.execute(
                    "SELECT COUNT(*) FROM gold_standard_posts WHERE pillar = ? AND embedding IS NOT NULL",
                    (pillar,),
                )
            else:
                cursor.execute("SELECT COUNT(*) FROM gold_standard_posts WHERE embedding IS NOT NULL")
            return cursor.fetchone()[0]

    def search_gold_standard_by_embedding(
        self,
        query_embedding,
        pillar: str = None,
        top_k: int = 5,
        register: str = None,
    ) -> List[Dict]:
        """Return top-K most similar gold-standard posts by cosine similarity.

        Scope priority (Phase 2, 2026-04-19):
          1. If register is set, try register-scoped first (voice is the
             #1 anchor — matching register > matching pillar).
          2. Fall back to pillar-scoped if register returns empty.
          3. Broaden to all specimens if both scoped queries return empty.

        This biases retrieval toward specimens in the register the architect
        picked, which reinforces the voice decision instead of pulling the
        generator toward a different register's examples.
        """
        if not query_embedding:
            return []

        rows = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Try register-scoped first — voice takes precedence over pillar
            if register:
                cursor.execute(
                    """SELECT id, content, pillar, format, embedding, notes, register
                       FROM gold_standard_posts
                       WHERE register = ? AND embedding IS NOT NULL""",
                    (register,),
                )
                rows = cursor.fetchall()

            # Fall back to pillar-scoped if register found nothing
            if not rows and pillar:
                cursor.execute(
                    """SELECT id, content, pillar, format, embedding, notes, register
                       FROM gold_standard_posts
                       WHERE pillar = ? AND embedding IS NOT NULL""",
                    (pillar,),
                )
                rows = cursor.fetchall()

            # Broaden if both scoped queries were empty
            if not rows:
                cursor.execute(
                    """SELECT id, content, pillar, format, embedding, notes, register
                       FROM gold_standard_posts
                       WHERE embedding IS NOT NULL"""
                )
                rows = cursor.fetchall()

        scored = []
        for r in rows:
            emb = self._decode_embedding(r["embedding"])
            sim = self._cosine_similarity(query_embedding, emb)
            scored.append(
                {
                    "id": r["id"],
                    "content": r["content"],
                    "pillar": r["pillar"],
                    "format": r["format"],
                    "register": r["register"] if "register" in r.keys() else None,
                    "notes": r["notes"],
                    "similarity": sim,
                }
            )

        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return scored[:top_k]

    def get_top_engagement_posts_for_curation(self, limit: int = 30) -> List[Dict]:
        """Pull the top-engagement approved posts for the human to curate into gold-standard.

        Used by scripts/curate_gold_standard.py. Engagement = reactions + comments + shares.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """SELECT post_id, content, pillar, format,
                          COALESCE(reactions, 0) AS reactions,
                          COALESCE(comments, 0) AS comments,
                          COALESCE(shares, 0) AS shares,
                          COALESCE(engagement_score, 0) AS engagement_score
                   FROM content_memory
                   WHERE was_approved = 1
                     AND (COALESCE(reactions, 0) + COALESCE(comments, 0) + COALESCE(shares, 0)) > 0
                   ORDER BY (COALESCE(reactions, 0) + COALESCE(comments, 0) + COALESCE(shares, 0)) DESC
                   LIMIT ?""",
                (limit,),
            )
            return [dict(r) for r in cursor.fetchall()]

    # ═══════════════════════════════════════════════════════════════════════════
    # CONTENT MEMORY
    # ═══════════════════════════════════════════════════════════════════════════

    def remember_post(
        self,
        post_id: str,
        batch_id: str,
        content: str,
        hook: str = None,
        ending: str = None,
        pillar: str = None,
        format: str = None,
        voice: str = None,
        topic: str = None,
        trending_topic: str = None,
        was_approved: bool = False,
        average_score: float = 0,
        validation_scores: List[Dict] = None,
        metadata: Dict = None,
        register: str = None,
        blueprint: Dict = None,
        curator_angle: Dict = None,
    ):
        """Store a generated post in memory.

        Phase 0 (2026-04-19) adds register/blueprint/curator_angle as first-class
        fields so the diagnostics endpoint can return them per post and the
        Quality Drift supervisor can reason about register rotation.
        """

        # Extract hook (first line) if not provided
        if not hook and content:
            lines = content.strip().split('\n')
            hook = lines[0][:150] if lines else ""

        # Extract ending (last meaningful line) if not provided
        if not ending and content:
            lines = [l.strip() for l in content.strip().split('\n') if l.strip()]
            ending = lines[-1][:150] if lines else ""

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO content_memory
                    (post_id, batch_id, content, hook, ending, pillar, format, voice,
                     topic, trending_topic, was_approved, average_score, metadata,
                     register, blueprint, curator_angle)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    post_id, batch_id, content, hook, ending, pillar, format, voice,
                    topic, trending_topic, was_approved, average_score,
                    json.dumps(metadata) if metadata else None,
                    register,
                    json.dumps(blueprint, default=str) if blueprint else None,
                    json.dumps(curator_angle, default=str) if curator_angle else None,
                ))

                # Store validator feedback if provided
                if validation_scores:
                    for vs in validation_scores:
                        self._store_validator_feedback(cursor, post_id, vs, pillar, format)

                conn.commit()

            except Exception as e:
                logger.error(f"Failed to remember post: {e}")

        # Update session memory
        if self._session:
            self._session.posts_generated += 1
            if topic and topic not in self._session.topics_used:
                self._session.topics_used.append(topic)
            if hook and hook not in self._session.hooks_used:
                self._session.hooks_used.append(hook[:50])
            if ending and ending not in self._session.endings_used:
                self._session.endings_used.append(ending[:50])
            if pillar and pillar not in self._session.pillars_used:
                self._session.pillars_used.append(pillar)
            if format and format not in self._session.formats_used:
                self._session.formats_used.append(format)

        logger.debug(f"Remembered post {post_id} (approved={was_approved})")

    # ═══════════════════════════════════════════════════════════════════════════
    # QUALITY DRIFT TOOLS (read helpers the QualityDriftAgent calls)
    # ═══════════════════════════════════════════════════════════════════════════

    def get_recent_posts_with_validation(self, days: int = 7, limit: int = 30) -> List[Dict]:
        """Return recent posts joined with their per-validator scores.

        Used by QualityDriftAgent. Each row includes:
          - content, pillar, format, created_at, was_approved, average_score
          - validators: list of {agent_name, score, approved, feedback}
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """SELECT post_id, content, pillar, format, created_at,
                          was_approved, average_score, theme, sub_theme
                   FROM content_memory
                   WHERE created_at >= datetime('now', ?)
                   ORDER BY created_at DESC
                   LIMIT ?""",
                (f"-{days} days", limit),
            )
            posts = [dict(r) for r in cursor.fetchall()]

            # Attach validator scores for each post
            for p in posts:
                cursor.execute(
                    """SELECT validator_name, score, approved, feedback
                       FROM validator_memory
                       WHERE post_id = ?
                       ORDER BY validator_name""",
                    (p["post_id"],),
                )
                p["validators"] = [dict(r) for r in cursor.fetchall()]

        return posts

    def count_phrase_occurrences(self, phrase: str, days: int = 14) -> Dict[str, Any]:
        """Count how many recent posts contain a phrase (case-insensitive).

        Used by QualityDriftAgent to detect pattern recycling — e.g.
        "Tube #4,847", "Stop. Breathe.", "Hyper-Arid Social Desiccation".
        Returns the count, the sample post excerpts, and the total posts checked.
        """
        if not phrase or not phrase.strip():
            return {"count": 0, "total_posts": 0, "samples": []}

        pattern = f"%{phrase.strip()}%"
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """SELECT COUNT(*) FROM content_memory
                   WHERE created_at >= datetime('now', ?)""",
                (f"-{days} days",),
            )
            total_posts = cursor.fetchone()[0]

            cursor.execute(
                """SELECT post_id, content, created_at FROM content_memory
                   WHERE created_at >= datetime('now', ?)
                   AND content LIKE ? COLLATE NOCASE
                   ORDER BY created_at DESC
                   LIMIT 10""",
                (f"-{days} days", pattern),
            )
            hits = [dict(r) for r in cursor.fetchall()]

        return {
            "phrase": phrase,
            "count": len(hits),
            "total_posts": total_posts,
            "rate": round(len(hits) / total_posts, 3) if total_posts else 0.0,
            "samples": [
                {"post_id": h["post_id"], "excerpt": h["content"][:200], "when": h["created_at"]}
                for h in hits[:5]
            ],
        }

    def get_validator_scorecard(self, days: int = 14) -> Dict[str, Any]:
        """Per-validator approval rate + score distribution over the window.

        Used by QualityDriftAgent to detect validator bias drift — e.g. Marcus
        rejecting 80% of AI_Economy posts while Sarah approves 95%.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """SELECT validator_name,
                          COUNT(*) as total,
                          SUM(CASE WHEN approved THEN 1 ELSE 0 END) as approvals,
                          AVG(score) as avg_score,
                          MIN(score) as min_score,
                          MAX(score) as max_score
                   FROM validator_memory
                   WHERE created_at >= datetime('now', ?)
                   GROUP BY validator_name
                   ORDER BY validator_name""",
                (f"-{days} days",),
            )
            per_validator = []
            for r in cursor.fetchall():
                total = r["total"] or 0
                approvals = r["approvals"] or 0
                per_validator.append({
                    "validator": r["validator_name"],
                    "total": total,
                    "approvals": approvals,
                    "approval_rate": round(approvals / total, 3) if total else 0.0,
                    "avg_score": round(r["avg_score"] or 0, 2),
                    "score_range": [round(r["min_score"] or 0, 1), round(r["max_score"] or 0, 1)],
                })

            # Cross-tabulate approval rate by pillar per validator
            cursor.execute(
                """SELECT vm.validator_name, vm.pillar,
                          COUNT(*) as total,
                          SUM(CASE WHEN vm.approved THEN 1 ELSE 0 END) as approvals
                   FROM validator_memory vm
                   WHERE vm.created_at >= datetime('now', ?)
                   AND vm.pillar IS NOT NULL
                   GROUP BY vm.validator_name, vm.pillar""",
                (f"-{days} days",),
            )
            pillar_breakdown = {}
            for r in cursor.fetchall():
                v = r["validator_name"]
                total = r["total"] or 0
                rate = round((r["approvals"] or 0) / total, 3) if total else 0.0
                pillar_breakdown.setdefault(v, {})[r["pillar"]] = {
                    "total": total, "approval_rate": rate,
                }

        return {
            "days": days,
            "per_validator": per_validator,
            "pillar_breakdown": pillar_breakdown,
        }

    def get_pillar_distribution(self, days: int = 14) -> Dict[str, Any]:
        """Distribution of posts across the five pillars.

        Used by QualityDriftAgent to detect rotation imbalance.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT pillar, COUNT(*) as count
                   FROM content_memory
                   WHERE created_at >= datetime('now', ?)
                   AND pillar IS NOT NULL
                   GROUP BY pillar""",
                (f"-{days} days",),
            )
            distribution = {row[0]: row[1] for row in cursor.fetchall()}

            cursor.execute(
                """SELECT COUNT(*) FROM content_memory
                   WHERE created_at >= datetime('now', ?)""",
                (f"-{days} days",),
            )
            total = cursor.fetchone()[0] or 0

        expected = ["the_what", "the_what_if", "the_who_profits", "the_how_to_cope", "the_why_it_matters"]
        gaps = [p for p in expected if p not in distribution]

        return {
            "days": days,
            "total_posts": total,
            "distribution": distribution,
            "missing_pillars": gaps,
            "balanced": len(gaps) == 0 and (
                total == 0 or max(distribution.values()) <= 2 * min(distribution.values())
            ),
        }

    def get_fallback_shipping_rate(self, days: int = 14) -> Dict[str, Any]:
        """Heuristic: how often did posts ship via the 'max revisions' fallback?

        A fallback-shipped post has was_approved=True but average_score < 7.0 (the
        normal approval threshold), indicating the orchestrator kept the 'best
        version' rather than reaching 2-of-3 validator consensus.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT COUNT(*) FROM content_memory
                   WHERE created_at >= datetime('now', ?)
                   AND was_approved = 1""",
                (f"-{days} days",),
            )
            total_shipped = cursor.fetchone()[0] or 0

            cursor.execute(
                """SELECT COUNT(*) FROM content_memory
                   WHERE created_at >= datetime('now', ?)
                   AND was_approved = 1
                   AND average_score > 0
                   AND average_score < 7.0""",
                (f"-{days} days",),
            )
            fallback_count = cursor.fetchone()[0] or 0

        return {
            "days": days,
            "total_shipped": total_shipped,
            "fallback_shipped": fallback_count,
            "fallback_rate": round(fallback_count / total_shipped, 3) if total_shipped else 0.0,
        }

    def write_quality_finding(
        self,
        insight_type: str,
        observation: str,
        severity: str = "info",
        evidence: Optional[Dict] = None,
        suggested_action: Optional[str] = None,
    ) -> int:
        """Persist a QualityDriftAgent finding to strategy_insights.

        Uses insight_type prefix 'drift:<type>' so findings are distinguishable
        from other strategy insights. Evidence and suggested_action are folded
        into the observation text for display.
        """
        sev = (severity or "info").lower()
        confidence_map = {"critical": 0.9, "warning": 0.7, "info": 0.5}
        confidence = confidence_map.get(sev, 0.5)

        body_parts = [observation.strip()]
        if suggested_action:
            body_parts.append(f"\n\n**Suggested action:** {suggested_action.strip()}")
        if evidence:
            import json as _json
            body_parts.append(f"\n\n**Evidence:** {_json.dumps(evidence, default=str)[:800]}")
        body = "".join(body_parts)

        prefixed_type = insight_type if insight_type.startswith("drift:") else f"drift:{insight_type}"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO strategy_insights
                   (insight_type, observation, confidence, evidence_count)
                   VALUES (?, ?, ?, ?)""",
                (prefixed_type, body, confidence, 1),
            )
            conn.commit()
            return cursor.lastrowid

    def add_to_avoid_list(
        self,
        phrase: str,
        reason: str,
        category: str = "phrase",
        days_active: int = 14,
    ) -> Optional[int]:
        """Add a phrase/pattern to the generator avoid-list.

        Called by the QualityDriftAgent when it detects a recycled phrase,
        template overuse, or voice drift. The content strategist reads active
        entries before each generation. Duplicate phrases extend the existing
        entry's expiration rather than creating a new row.

        Category is a free-form tag ('phrase' / 'specific_detail' / 'structure')
        that lets the strategist group avoids in the prompt.
        """
        from datetime import datetime as _dt, timedelta as _td
        if not phrase or not phrase.strip():
            return None

        phrase_norm = phrase.strip()
        expires_at = _dt.utcnow() + _td(days=max(1, days_active))

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Deduplicate: if an identical active phrase exists, bump its
            # expiry rather than adding another row.
            cursor.execute(
                "SELECT id FROM generator_avoid_list "
                "WHERE phrase = ? AND active = 1 LIMIT 1",
                (phrase_norm,),
            )
            row = cursor.fetchone()
            if row:
                cursor.execute(
                    "UPDATE generator_avoid_list "
                    "SET expires_at = ?, reason = ?, category = ? "
                    "WHERE id = ?",
                    (expires_at.isoformat(), reason, category, row[0]),
                )
                conn.commit()
                return row[0]

            cursor.execute(
                """INSERT INTO generator_avoid_list
                   (phrase, reason, category, expires_at, active)
                   VALUES (?, ?, ?, ?, 1)""",
                (phrase_norm, reason, category, expires_at.isoformat()),
            )
            conn.commit()
            return cursor.lastrowid

    def get_active_avoid_phrases(self, limit: int = 40) -> List[Dict]:
        """Return currently-active avoid-list entries (not expired).

        Used by the content strategist before each generation to pull in
        supervisor-identified phrases to avoid.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """SELECT phrase, reason, category, created_at, expires_at
                   FROM generator_avoid_list
                   WHERE active = 1
                   AND (expires_at IS NULL OR expires_at > datetime('now'))
                   ORDER BY created_at DESC
                   LIMIT ?""",
                (limit,),
            )
            return [dict(r) for r in cursor.fetchall()]

    def get_severely_starved_pillar(self, days: int = 7) -> Optional[str]:
        """Return a pillar name that has ZERO posts in the window, or None.

        Used by the orchestrator as a safety valve: if the editorial calendar
        has left a pillar completely uncovered for the full window, the
        orchestrator overrides the day's planned theme to cover the gap.
        Returns at most one pillar (preferring alphabetical order for
        determinism when multiple are starved).
        """
        expected = [
            "the_what", "the_what_if", "the_who_profits",
            "the_how_to_cope", "the_why_it_matters",
        ]
        # Map to theme keys used by the curator (config uses different names)
        pillar_to_theme = {
            "the_what": "ai_slop",
            "the_what_if": "ai_safety",
            "the_who_profits": "ai_economy",
            "the_how_to_cope": "rituals",
            "the_why_it_matters": "meditations",
        }

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT pillar, COUNT(*) FROM content_memory
                   WHERE created_at >= datetime('now', ?)
                   AND pillar IS NOT NULL
                   GROUP BY pillar""",
                (f"-{days} days",),
            )
            counts = {row[0]: row[1] for row in cursor.fetchall()}

            # If no posts at all in window, no starvation (system is just idle)
            cursor.execute(
                "SELECT COUNT(*) FROM content_memory WHERE created_at >= datetime('now', ?)",
                (f"-{days} days",),
            )
            total = cursor.fetchone()[0] or 0

        if total < 3:
            # Not enough activity to declare starvation
            return None

        starved = [p for p in expected if counts.get(p, 0) == 0]
        if not starved:
            return None
        # Map to theme for news_curator's preferred_theme parameter
        return pillar_to_theme.get(starved[0], starved[0])

    def prune_expired_avoid_entries(self) -> int:
        """Mark expired avoid entries inactive. Returns number of entries pruned."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE generator_avoid_list SET active = 0 "
                "WHERE active = 1 AND expires_at IS NOT NULL AND expires_at <= datetime('now')"
            )
            conn.commit()
            return cursor.rowcount

    def get_recent_drift_findings(self, days: int = 14, limit: int = 50) -> List[Dict]:
        """Pull recent drift findings for the dashboard."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """SELECT id, insight_type, observation, confidence, created_at
                   FROM strategy_insights
                   WHERE insight_type LIKE 'drift:%'
                   AND created_at >= datetime('now', ?)
                   ORDER BY created_at DESC
                   LIMIT ?""",
                (f"-{days} days", limit),
            )
            return [dict(r) for r in cursor.fetchall()]

    def get_recent_posts(self, days: int = 7, limit: int = 50) -> List[Dict]:
        """Get recently generated posts"""

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM content_memory
                WHERE created_at >= datetime('now', ?)
                ORDER BY created_at DESC
                LIMIT ?
            """, (f'-{days} days', limit))

            return [dict(row) for row in cursor.fetchall()]

    def get_recent_registers(self, days: int = 7, limit: int = 10) -> List[str]:
        """Get the sequence of registers used in recent posts (newest first).

        Used by AngleArchitectAgent to rotate — the architect avoids picking
        a register that dominates the recent window. Phase 1 addition
        (2026-04-19).

        Returns the raw list INCLUDING duplicates so callers can count
        frequency, not just distinct registers.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT register FROM content_memory
                WHERE register IS NOT NULL
                  AND created_at >= datetime('now', ?)
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (f"-{days} days", limit),
            )
            return [row[0] for row in cursor.fetchall() if row[0]]

    def get_recent_blueprint_fields(
        self, fields: List[str], days: int = 7, limit: int = 10,
    ) -> Dict[str, List[str]]:
        """Extract specific fields from recent blueprints as parallel lists.

        Phase C (2026-04-20): length_target and structure_shape are stored
        inside the blueprint JSON blob (not separate columns). This helper
        parses recent blueprints and returns requested fields as lists
        suitable for rotation-based constraint (same shape as
        get_recent_registers).

        Args:
            fields: blueprint keys to extract (e.g. ['length_target',
                'structure_shape'])
            days: look-back window
            limit: max posts to scan

        Returns:
            Dict keyed by field name → list of values (newest first,
            skipping posts where the blueprint was missing / fallback /
            field absent).
        """
        result: Dict[str, List[str]] = {f: [] for f in fields}

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT blueprint FROM content_memory
                    WHERE blueprint IS NOT NULL
                      AND created_at >= datetime('now', ?)
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (f"-{days} days", limit),
                )
                for row in cursor.fetchall():
                    raw = row[0]
                    if not raw:
                        continue
                    try:
                        bp = json.loads(raw)
                    except (json.JSONDecodeError, TypeError):
                        continue
                    if not isinstance(bp, dict) or bp.get("fallback"):
                        continue
                    for field in fields:
                        val = bp.get(field)
                        if val and isinstance(val, str):
                            result[field].append(val)
        except Exception as e:
            logger.warning(f"get_recent_blueprint_fields failed: {e}")
        return result

    def get_recent_topics(self, days: int = 7, limit: int = 20) -> List[str]:
        """Get topics used recently (to avoid repetition)"""

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT DISTINCT topic FROM content_memory
                WHERE topic IS NOT NULL
                AND created_at >= datetime('now', ?)
                ORDER BY created_at DESC
                LIMIT ?
            """, (f'-{days} days', limit))

            return [row[0] for row in cursor.fetchall()]

    def get_recent_trending_topics(self, days: int = 14, limit: int = 30) -> List[str]:
        """Get trending topics used recently"""

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT DISTINCT trending_topic FROM content_memory
                WHERE trending_topic IS NOT NULL
                AND created_at >= datetime('now', ?)
                ORDER BY created_at DESC
                LIMIT ?
            """, (f'-{days} days', limit))

            return [row[0] for row in cursor.fetchall()]

    def get_recent_hooks(self, days: int = 7, limit: int = 10) -> List[str]:
        """Get hooks used recently (to vary openings)"""

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT DISTINCT hook FROM content_memory
                WHERE hook IS NOT NULL
                AND created_at >= datetime('now', ?)
                ORDER BY created_at DESC
                LIMIT ?
            """, (f'-{days} days', limit))

            return [row[0] for row in cursor.fetchall()]

    def get_recent_endings(self, days: int = 7, limit: int = 10) -> List[str]:
        """Get endings used recently (to vary closings)"""

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT DISTINCT ending FROM content_memory
                WHERE ending IS NOT NULL
                AND created_at >= datetime('now', ?)
                ORDER BY created_at DESC
                LIMIT ?
            """, (f'-{days} days', limit))

            return [row[0] for row in cursor.fetchall()]

    def get_recent_pillars(self, days: int = 7, limit: int = 10) -> List[str]:
        """Get pillars/themes used recently (to ensure variety across Five Questions)"""

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT pillar FROM content_memory
                WHERE pillar IS NOT NULL
                AND created_at >= datetime('now', ?)
                ORDER BY created_at DESC
                LIMIT ?
            """, (f'-{days} days', limit))

            return [row[0] for row in cursor.fetchall()]

    def get_pillar_stats(self, days: int = 30) -> Dict[str, Dict]:
        """Get statistics by content pillar"""

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    pillar,
                    COUNT(*) as total,
                    SUM(CASE WHEN was_approved THEN 1 ELSE 0 END) as approved,
                    AVG(average_score) as avg_score
                FROM content_memory
                WHERE created_at >= datetime('now', ?)
                AND pillar IS NOT NULL
                GROUP BY pillar
                ORDER BY avg_score DESC
            """, (f'-{days} days',))

            stats = {}
            for row in cursor.fetchall():
                pillar, total, approved, avg_score = row
                stats[pillar] = {
                    "total": total,
                    "approved": approved,
                    "approval_rate": approved / total if total > 0 else 0,
                    "avg_score": avg_score or 0
                }

            return stats

    def get_successful_patterns(self, min_score: float = 7.0, limit: int = 20) -> List[Dict]:
        """Get patterns from highly-rated posts"""

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT pillar, format, voice, hook, ending, average_score
                FROM content_memory
                WHERE was_approved = TRUE
                AND average_score >= ?
                ORDER BY average_score DESC
                LIMIT ?
            """, (min_score, limit))

            return [dict(row) for row in cursor.fetchall()]

    def get_failed_patterns(self, max_score: float = 5.0, limit: int = 20) -> List[Dict]:
        """Get patterns from low-rated posts (to avoid)"""

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT pillar, format, voice, hook, ending, average_score
                FROM content_memory
                WHERE was_approved = FALSE
                AND average_score <= ?
                ORDER BY average_score ASC
                LIMIT ?
            """, (max_score, limit))

            return [dict(row) for row in cursor.fetchall()]

    def mark_posted_to_linkedin(self, post_id: str, linkedin_post_id: str):
        """Mark a post as published to LinkedIn"""

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE content_memory
                SET posted_to_linkedin = TRUE, linkedin_post_id = ?
                WHERE post_id = ?
            """, (linkedin_post_id, post_id))
            conn.commit()

    # ═══════════════════════════════════════════════════════════════════════════
    # IMAGE STYLE MEMORY
    # ═══════════════════════════════════════════════════════════════════════════

    def remember_image_style(
        self,
        post_id: str,
        scene_category: str,
        mood: str,
        uses_jesse: bool = False,
        jesse_scenario: str = None,
        image_type: str = "product"
    ):
        """Record image style used for a post (for variety tracking)"""

        # Store as learning insight
        self.store_insight(
            insight_type="image_style",
            key=post_id,
            value={
                "scene_category": scene_category,
                "mood": mood,
                "uses_jesse": uses_jesse,
                "jesse_scenario": jesse_scenario,
                "image_type": image_type
            },
            confidence=1.0,
            sample_count=1
        )

        logger.debug(f"Remembered image style for {post_id}: {scene_category}/{mood}")

    def get_recent_image_styles(self, days: int = 7, limit: int = 20) -> List[Dict]:
        """Get recently used image styles (to avoid repetition)"""

        insights = self.get_all_insights("image_style")

        # Filter by date and limit
        recent = []
        for i in insights[:limit]:
            try:
                value = json.loads(i.get("insight_value", "{}")) if isinstance(i.get("insight_value"), str) else i.get("insight_value", {})
                recent.append({
                    "post_id": i.get("insight_key"),
                    **value
                })
            except Exception:
                pass

        return recent

    # ═══════════════════════════════════════════════════════════════════════════
    # VALIDATOR LEARNING MEMORY
    # ═══════════════════════════════════════════════════════════════════════════

    def _store_validator_feedback(
        self,
        cursor,
        post_id: str,
        validation_score: Dict,
        pillar: str = None,
        format: str = None
    ):
        """Store individual validator feedback"""

        # Handle both dict and ValidationScore object
        if hasattr(validation_score, 'agent_name'):
            # It's a ValidationScore object
            name = validation_score.agent_name
            score = validation_score.score
            approved = validation_score.approved
            feedback = validation_score.feedback
            strengths = getattr(validation_score, 'strengths', [])
            weaknesses = getattr(validation_score, 'weaknesses', [])
            criteria_breakdown = getattr(validation_score, 'criteria_breakdown', None)
        else:
            # It's a dict
            name = validation_score.get('agent_name', validation_score.get('validator_name', 'Unknown'))
            score = validation_score.get('score', 0)
            approved = validation_score.get('approved', False)
            feedback = validation_score.get('feedback', '')
            strengths = validation_score.get('strengths', [])
            weaknesses = validation_score.get('weaknesses', [])
            criteria_breakdown = validation_score.get('criteria_breakdown')

        cursor.execute("""
            INSERT INTO validator_memory
            (post_id, validator_name, score, approved, feedback, strengths, weaknesses,
             pillar, format, criteria_breakdown)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            post_id, name, score, approved, feedback,
            json.dumps(strengths) if strengths else None,
            json.dumps(weaknesses) if weaknesses else None,
            pillar, format,
            json.dumps(criteria_breakdown, default=str) if criteria_breakdown else None
        ))

    def get_validator_preferences(self, validator_name: str, days: int = 30) -> ValidatorPattern:
        """Get learned preferences for a specific validator"""

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get basic stats
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN approved THEN 1 ELSE 0 END) as approved_count,
                    AVG(score) as avg_score
                FROM validator_memory
                WHERE validator_name = ?
                AND created_at >= datetime('now', ?)
            """, (validator_name, f'-{days} days'))

            row = cursor.fetchone()
            total = row['total'] or 0
            approved_count = row['approved_count'] or 0
            avg_score = row['avg_score'] or 0

            # Get best pillars
            cursor.execute("""
                SELECT pillar, AVG(score) as avg_score
                FROM validator_memory
                WHERE validator_name = ?
                AND pillar IS NOT NULL
                AND created_at >= datetime('now', ?)
                GROUP BY pillar
                ORDER BY avg_score DESC
                LIMIT 3
            """, (validator_name, f'-{days} days'))
            best_pillars = [row['pillar'] for row in cursor.fetchall()]

            # Get worst pillars
            cursor.execute("""
                SELECT pillar, AVG(score) as avg_score
                FROM validator_memory
                WHERE validator_name = ?
                AND pillar IS NOT NULL
                AND created_at >= datetime('now', ?)
                GROUP BY pillar
                ORDER BY avg_score ASC
                LIMIT 3
            """, (validator_name, f'-{days} days'))
            worst_pillars = [row['pillar'] for row in cursor.fetchall()]

            # Aggregate strengths and weaknesses
            cursor.execute("""
                SELECT strengths, weaknesses FROM validator_memory
                WHERE validator_name = ?
                AND created_at >= datetime('now', ?)
            """, (validator_name, f'-{days} days'))

            all_strengths = []
            all_weaknesses = []
            for row in cursor.fetchall():
                if row['strengths']:
                    try:
                        all_strengths.extend(json.loads(row['strengths']))
                    except:
                        pass
                if row['weaknesses']:
                    try:
                        all_weaknesses.extend(json.loads(row['weaknesses']))
                    except:
                        pass

            # Count most common
            strength_counts = defaultdict(int)
            for s in all_strengths:
                strength_counts[s] += 1
            weakness_counts = defaultdict(int)
            for w in all_weaknesses:
                weakness_counts[w] += 1

            common_praise = sorted(strength_counts.keys(), key=lambda x: strength_counts[x], reverse=True)[:5]
            common_critiques = sorted(weakness_counts.keys(), key=lambda x: weakness_counts[x], reverse=True)[:5]

            return ValidatorPattern(
                validator_name=validator_name,
                likes=common_praise,
                dislikes=common_critiques,
                approval_rate=approved_count / total if total > 0 else 0,
                avg_score=avg_score,
                best_pillars=best_pillars,
                worst_pillars=worst_pillars,
                common_critiques=common_critiques,
                common_praise=common_praise
            )

    def get_all_validator_patterns(self, days: int = 30) -> Dict[str, ValidatorPattern]:
        """Get learned patterns for all validators"""

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT DISTINCT validator_name FROM validator_memory
                WHERE created_at >= datetime('now', ?)
            """, (f'-{days} days',))

            validators = [row[0] for row in cursor.fetchall()]

        return {v: self.get_validator_preferences(v, days) for v in validators}

    def get_validator_feedback_summary(self) -> str:
        """Get a human-readable summary of validator learnings"""

        patterns = self.get_all_validator_patterns()

        if not patterns:
            return "No validator feedback recorded yet."

        lines = ["## Validator Learning Summary\n"]

        for name, pattern in patterns.items():
            lines.append(f"### {name}")
            lines.append(f"- Approval Rate: {pattern.approval_rate:.1%}")
            lines.append(f"- Average Score: {pattern.avg_score:.1f}/10")

            if pattern.best_pillars:
                lines.append(f"- Best Pillars: {', '.join(pattern.best_pillars)}")
            if pattern.worst_pillars:
                lines.append(f"- Struggles With: {', '.join(pattern.worst_pillars)}")
            if pattern.common_praise:
                lines.append(f"- Often Praises: {', '.join(pattern.common_praise[:3])}")
            if pattern.common_critiques:
                lines.append(f"- Common Critiques: {', '.join(pattern.common_critiques[:3])}")
            lines.append("")

        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════════════════════════
    # SESSION MEMORY
    # ═══════════════════════════════════════════════════════════════════════════

    def start_session(self, session_id: str = None):
        """Start a new generation session"""

        from uuid import uuid4

        self._session = SessionContext(
            session_id=session_id or str(uuid4()),
            started_at=datetime.utcnow().isoformat(),
            posts_generated=0,
            topics_used=[],
            hooks_used=[],
            endings_used=[],
            pillars_used=[],
            formats_used=[]
        )

        logger.info(f"Started memory session: {self._session.session_id}")

    def end_session(self):
        """End the current session"""

        if self._session:
            logger.info(f"Ended session {self._session.session_id}: {self._session.posts_generated} posts")
        self._session = None

    def get_session_context(self) -> Optional[SessionContext]:
        """Get current session context"""
        return self._session

    def get_session_avoid_patterns(self) -> Dict[str, List[str]]:
        """Get patterns to avoid based on current session"""

        if not self._session:
            return {}

        return {
            "recent_topics": self._session.topics_used,
            "recent_hooks": self._session.hooks_used,
            "recent_endings": self._session.endings_used,
            "recent_pillars": self._session.pillars_used,
            "recent_formats": self._session.formats_used
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # LEARNING INSIGHTS
    # ═══════════════════════════════════════════════════════════════════════════

    def store_insight(self, insight_type: str, key: str, value: Any, confidence: float = 0.5, sample_count: int = 1):
        """Store a learned insight"""

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO learning_insights
                (insight_type, insight_key, insight_value, confidence, sample_count, updated_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            """, (insight_type, key, json.dumps(value), confidence, sample_count))

            conn.commit()

    def get_insight(self, insight_type: str, key: str) -> Optional[Any]:
        """Get a stored insight"""

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT insight_value, confidence FROM learning_insights
                WHERE insight_type = ? AND insight_key = ?
            """, (insight_type, key))

            row = cursor.fetchone()
            if row:
                try:
                    return json.loads(row[0])
                except:
                    return row[0]
            return None

    def get_all_insights(self, insight_type: str = None) -> List[Dict]:
        """Get all stored insights"""

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if insight_type:
                cursor.execute("""
                    SELECT * FROM learning_insights
                    WHERE insight_type = ?
                    ORDER BY confidence DESC
                """, (insight_type,))
            else:
                cursor.execute("""
                    SELECT * FROM learning_insights
                    ORDER BY insight_type, confidence DESC
                """)

            return [dict(row) for row in cursor.fetchall()]

    # ═══════════════════════════════════════════════════════════════════════════
    # MEMORY CONTEXT FOR PROMPTS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_memory_context_for_generation(self, days: int = 7) -> str:
        """
        Get a formatted memory context to include in generation prompts.
        This helps the AI avoid repetition and learn from past feedback.
        """

        lines = []

        # Recent topics to avoid
        recent_topics = self.get_recent_topics(days=days, limit=10)
        if recent_topics:
            lines.append("RECENTLY USED TOPICS (avoid repetition):")
            for topic in recent_topics[:7]:
                lines.append(f"  - {topic}")
            lines.append("")

        # Recent hooks to avoid
        recent_hooks = self.get_recent_hooks(days=days, limit=5)
        if recent_hooks:
            lines.append("RECENT HOOKS (vary your openings):")
            for hook in recent_hooks[:5]:
                lines.append(f"  - {hook[:80]}...")
            lines.append("")

        # Session context
        session = self.get_session_context()
        if session and session.posts_generated > 0:
            lines.append(f"THIS SESSION: Already generated {session.posts_generated} posts")
            if session.pillars_used:
                lines.append(f"  Pillars used: {', '.join(session.pillars_used)}")
            if session.topics_used:
                lines.append(f"  Topics covered: {', '.join(session.topics_used[:3])}")
            lines.append("")

        # Pillar performance
        pillar_stats = self.get_pillar_stats(days=30)
        if pillar_stats:
            lines.append("PILLAR PERFORMANCE (last 30 days):")
            for pillar, stats in sorted(pillar_stats.items(), key=lambda x: x[1]['avg_score'], reverse=True):
                lines.append(f"  - {pillar}: {stats['approval_rate']:.0%} approval, avg {stats['avg_score']:.1f}/10")
            lines.append("")

        # Validator learnings
        validator_patterns = self.get_all_validator_patterns(days=30)
        if validator_patterns:
            lines.append("VALIDATOR PREFERENCES:")
            for name, pattern in validator_patterns.items():
                prefs = []
                if pattern.common_praise:
                    prefs.append(f"likes: {', '.join(pattern.common_praise[:2])}")
                if pattern.common_critiques:
                    prefs.append(f"dislikes: {', '.join(pattern.common_critiques[:2])}")
                if prefs:
                    lines.append(f"  - {name}: {'; '.join(prefs)}")
            lines.append("")

        if not lines:
            return ""

        return "═══════════════════════════════════════════════════════════════════════════════\n" + \
               "MEMORY CONTEXT (learned from past generations)\n" + \
               "═══════════════════════════════════════════════════════════════════════════════\n\n" + \
               "\n".join(lines)

    # ═══════════════════════════════════════════════════════════════════════════
    # ENGAGEMENT DATA
    # ═══════════════════════════════════════════════════════════════════════════

    def update_post_engagement(
        self,
        linkedin_post_id: str,
        reactions: int = 0,
        comments: int = 0,
        shares: int = 0,
        impressions: int = 0,
        engagement_score: float = None,
    ):
        """Update engagement metrics for a published post."""
        if engagement_score is None:
            engagement_score = reactions + (comments * 2) + (shares * 3)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE content_memory
                SET reactions = ?, comments = ?, shares = ?, impressions = ?,
                    engagement_score = ?, performance_fetched_at = datetime('now')
                WHERE linkedin_post_id = ?
            """, (reactions, comments, shares, impressions, engagement_score, linkedin_post_id))
            conn.commit()
            updated = cursor.rowcount
        if updated:
            logger.info(f"Updated engagement for {linkedin_post_id}: r={reactions} c={comments} s={shares} i={impressions}")
        else:
            logger.warning(f"No content_memory row found for linkedin_post_id={linkedin_post_id}")

    def get_posts_needing_engagement(self, min_age_hours: int = 24) -> List[Dict]:
        """Get published posts that haven't had engagement fetched yet (or not recently)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT post_id, linkedin_post_id, content, created_at,
                       engagement_score, performance_fetched_at
                FROM content_memory
                WHERE posted_to_linkedin = TRUE
                AND linkedin_post_id IS NOT NULL
                AND linkedin_post_id != ''
                AND (
                    performance_fetched_at IS NULL
                    OR performance_fetched_at < datetime('now', '-7 days')
                )
                AND created_at <= datetime('now', ?)
                ORDER BY created_at DESC
            """, (f'-{min_age_hours} hours',))
            return [dict(row) for row in cursor.fetchall()]

    def get_recent_performance(self, days: int = 14) -> List[Dict]:
        """Get engagement data for recently published posts."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT post_id, linkedin_post_id, content, pillar, theme, sub_theme,
                       format, created_at, engagement_score, reactions, comments,
                       shares, impressions, average_score
                FROM content_memory
                WHERE posted_to_linkedin = TRUE
                AND engagement_score IS NOT NULL
                AND created_at >= datetime('now', ?)
                ORDER BY created_at DESC
            """, (f'-{days} days',))
            return [dict(row) for row in cursor.fetchall()]

    # ═══════════════════════════════════════════════════════════════════════════
    # EDITORIAL CALENDAR
    # ═══════════════════════════════════════════════════════════════════════════

    def add_calendar_entry(
        self,
        scheduled_for: str,
        theme: str,
        format: str = None,
        angle_seed: str = None,
        created_by: str = "manual",
    ) -> int:
        """Add an entry to the editorial calendar. Returns the row id."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO editorial_calendar (scheduled_for, theme, format, angle_seed, created_by)
                VALUES (?, ?, ?, ?, ?)
            """, (scheduled_for, theme, format, angle_seed, created_by))
            conn.commit()
            return cursor.lastrowid

    def get_calendar_entry(self, scheduled_for: str) -> Optional[Dict]:
        """Get the editorial calendar entry for a given date (YYYY-MM-DD)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM editorial_calendar
                WHERE scheduled_for = ?
                ORDER BY id DESC LIMIT 1
            """, (scheduled_for,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_calendar_week(self, start_date: str, end_date: str) -> List[Dict]:
        """Get editorial calendar entries for a date range."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM editorial_calendar
                WHERE scheduled_for BETWEEN ? AND ?
                ORDER BY scheduled_for ASC
            """, (start_date, end_date))
            return [dict(row) for row in cursor.fetchall()]

    def update_calendar_status(self, entry_id: int, status: str, post_id: int = None):
        """Update editorial calendar entry status."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if post_id is not None:
                cursor.execute("""
                    UPDATE editorial_calendar SET status = ?, post_id = ? WHERE id = ?
                """, (status, post_id, entry_id))
            else:
                cursor.execute("""
                    UPDATE editorial_calendar SET status = ? WHERE id = ?
                """, (status, entry_id))
            conn.commit()

    # ═══════════════════════════════════════════════════════════════════════════
    # STRATEGY INSIGHTS
    # ═══════════════════════════════════════════════════════════════════════════

    def add_strategy_insight(
        self,
        insight_type: str,
        observation: str,
        confidence: float = 0.0,
        evidence_count: int = 1,
    ) -> int:
        """Add a strategy insight. Returns the row id."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO strategy_insights
                (insight_type, observation, confidence, evidence_count, last_validated)
                VALUES (?, ?, ?, ?, datetime('now'))
            """, (insight_type, observation, confidence, evidence_count))
            conn.commit()
            return cursor.lastrowid

    def get_strategy_insights(self, top: int = 10, insight_type: str = None) -> List[Dict]:
        """Get top strategy insights by confidence."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if insight_type:
                cursor.execute("""
                    SELECT * FROM strategy_insights
                    WHERE insight_type = ?
                    ORDER BY confidence DESC, evidence_count DESC
                    LIMIT ?
                """, (insight_type, top))
            else:
                cursor.execute("""
                    SELECT * FROM strategy_insights
                    ORDER BY confidence DESC, evidence_count DESC
                    LIMIT ?
                """, (top,))
            return [dict(row) for row in cursor.fetchall()]

    def update_strategy_insight(self, insight_id: int, confidence: float, evidence_count: int):
        """Update an existing strategy insight with new evidence."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE strategy_insights
                SET confidence = ?, evidence_count = ?, last_validated = datetime('now')
                WHERE id = ?
            """, (confidence, evidence_count, insight_id))
            conn.commit()

    # ═══════════════════════════════════════════════════════════════════════════
    # CLIENT REVIEWS — Human feedback from client
    # ═══════════════════════════════════════════════════════════════════════════

    def add_client_review(
        self,
        review_text: str,
        rating: int = None,
        category: str = "general",
        post_id: str = None,
    ) -> int:
        """Add a client review. Returns the row id."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO client_reviews
                (post_id, rating, category, review_text)
                VALUES (?, ?, ?, ?)
            """, (post_id, rating, category, review_text))
            conn.commit()
            return cursor.lastrowid

    def get_client_reviews(self, limit: int = 50, unaddressed_only: bool = False) -> List[Dict]:
        """Get client reviews, optionally only unaddressed ones."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if unaddressed_only:
                cursor.execute("""
                    SELECT * FROM client_reviews
                    WHERE addressed = 0
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (limit,))
            else:
                cursor.execute("""
                    SELECT * FROM client_reviews
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def mark_reviews_addressed(self, review_ids: List[int]):
        """Mark reviews as addressed after refinement processes them."""
        if not review_ids:
            return
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            placeholders = ",".join("?" for _ in review_ids)
            cursor.execute(f"""
                UPDATE client_reviews
                SET addressed = 1
                WHERE id IN ({placeholders})
            """, review_ids)
            conn.commit()

    def delete_client_review(self, review_id: int):
        """Delete a client review by id."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM client_reviews WHERE id = ?", (review_id,))
            conn.commit()

    # ═══════════════════════════════════════════════════════════════════════════
    # ADAPTIVE THEME WEIGHTS (Phase 4.2)
    # ═══════════════════════════════════════════════════════════════════════════

    def get_theme_performance(self, days: int = 30) -> Dict[str, Dict]:
        """
        Get average engagement per theme over the last N days.
        Returns {theme: {count, avg_engagement, avg_reactions, avg_comments}}.
        Used by adaptive weighting to shift towards high-performing themes.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT theme,
                       COUNT(*) as count,
                       AVG(COALESCE(engagement_score, 0)) as avg_engagement,
                       AVG(COALESCE(reactions, 0)) as avg_reactions,
                       AVG(COALESCE(comments, 0)) as avg_comments,
                       AVG(COALESCE(shares, 0)) as avg_shares
                FROM content_memory
                WHERE posted_to_linkedin = TRUE
                AND theme IS NOT NULL
                AND created_at >= datetime('now', ?)
                GROUP BY theme
            """, (f'-{days} days',))
            return {row['theme']: dict(row) for row in cursor.fetchall()}

    def compute_adaptive_weights(self, days: int = 30) -> Dict[str, float]:
        """
        Compute adaptive theme weights based on rolling engagement averages.

        Themes with higher engagement get proportionally more weight.
        Guarantees a minimum floor (0.10) so no theme is fully starved.
        """
        perf = self.get_theme_performance(days=days)
        if not perf:
            return {}

        # Compute raw scores (engagement-based)
        raw = {}
        for theme, data in perf.items():
            raw[theme] = max(data.get("avg_engagement", 0), 0.1)

        total = sum(raw.values())
        if total == 0:
            return {t: 1.0 / len(raw) for t in raw}

        # Proportional weights with minimum floor
        floor = 0.10
        remaining = 1.0 - floor * len(raw)
        if remaining < 0:
            # Too many themes for the floor — equal weights
            return {t: 1.0 / len(raw) for t in raw}

        weights = {}
        for theme, score in raw.items():
            weights[theme] = floor + remaining * (score / total)

        return weights

    # ═══════════════════════════════════════════════════════════════════════════
    # A/B FORMAT TESTING (Phase 4.3)
    # ═══════════════════════════════════════════════════════════════════════════

    def get_format_performance(self, days: int = 30) -> Dict[str, Dict]:
        """
        Get average engagement per post format over the last N days.
        Returns {format: {count, avg_engagement, avg_reactions, avg_comments}}.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT format,
                       COUNT(*) as count,
                       AVG(COALESCE(engagement_score, 0)) as avg_engagement,
                       AVG(COALESCE(reactions, 0)) as avg_reactions,
                       AVG(COALESCE(comments, 0)) as avg_comments,
                       AVG(COALESCE(shares, 0)) as avg_shares
                FROM content_memory
                WHERE posted_to_linkedin = TRUE
                AND format IS NOT NULL
                AND created_at >= datetime('now', ?)
                GROUP BY format
            """, (f'-{days} days',))
            return {row['format']: dict(row) for row in cursor.fetchall()}

    def get_underexplored_formats(self, days: int = 30, min_count: int = 3) -> List[str]:
        """
        Identify formats with fewer than min_count posts in the period.
        These are candidates for A/B testing.
        """
        known_formats = [
            "observation", "hot_take", "narrative", "question",
            "confession", "breaking", "list"
        ]
        perf = self.get_format_performance(days=days)
        return [f for f in known_formats if perf.get(f, {}).get("count", 0) < min_count]

    # ═══════════════════════════════════════════════════════════════════════════
    # POSITION MEMORY — What Jesse SAID about topics
    # ═══════════════════════════════════════════════════════════════════════════

    def store_position(
        self,
        post_id: str,
        theme: str,
        sub_theme: str = None,
        topic: str = None,
        position_summary: str = None,
        sentiment: str = None,
        key_claim: str = None,
    ):
        """Store a position Jesse took on a topic."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO position_memory
                (post_id, theme, sub_theme, topic, position_summary, sentiment, key_claim)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (post_id, theme, sub_theme, topic, position_summary, sentiment, key_claim))
            conn.commit()
        logger.debug(f"Stored position for post {post_id}: {sentiment} on {theme}/{topic}")

    def get_positions_on_topic(self, topic: str, days: int = 60) -> List[Dict]:
        """Return past positions on a topic."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM position_memory
                WHERE topic = ?
                AND created_at >= datetime('now', ?)
                ORDER BY created_at DESC
            """, (topic, f'-{days} days'))
            return [dict(row) for row in cursor.fetchall()]

    def get_positions_by_theme(self, theme: str, days: int = 30, limit: int = 10) -> List[Dict]:
        """Return recent positions for a theme."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM position_memory
                WHERE theme = ?
                AND created_at >= datetime('now', ?)
                ORDER BY created_at DESC
                LIMIT ?
            """, (theme, f'-{days} days', limit))
            return [dict(row) for row in cursor.fetchall()]

    def get_position_context_for_generation(self, theme: str = None, days: int = 30) -> str:
        """
        Return a formatted string for prompts showing what Jesse has said recently.
        If theme is provided, filters to that theme; otherwise returns all recent positions.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if theme:
                cursor.execute("""
                    SELECT theme, sub_theme, topic, position_summary, sentiment, key_claim, created_at
                    FROM position_memory
                    WHERE theme = ?
                    AND created_at >= datetime('now', ?)
                    ORDER BY created_at DESC
                    LIMIT 10
                """, (theme, f'-{days} days'))
            else:
                cursor.execute("""
                    SELECT theme, sub_theme, topic, position_summary, sentiment, key_claim, created_at
                    FROM position_memory
                    WHERE created_at >= datetime('now', ?)
                    ORDER BY created_at DESC
                    LIMIT 15
                """, (f'-{days} days',))

            rows = [dict(row) for row in cursor.fetchall()]

        if not rows:
            return ""

        lines = []
        theme_label = theme.replace('_', ' ').title() if theme else "ALL THEMES"
        lines.append(f"JESSE'S PRIOR POSITIONS ON {theme_label}:")

        for row in rows:
            created = row.get("created_at", "")
            # Calculate rough age
            age_str = self._format_age(created)
            sentiment = row.get("sentiment", "")
            summary = row.get("position_summary", "")
            claim = row.get("key_claim", "")
            topic_label = row.get("topic") or row.get("sub_theme") or ""

            if summary:
                entry = f"- {age_str}: \"{summary}\""
                if topic_label:
                    entry += f" [topic: {topic_label}]"
                if sentiment:
                    entry += f" ({sentiment})"
                lines.append(entry)

        lines.append("BUILD ON these positions. Don't contradict without acknowledging the shift.")
        return "\n".join(lines)

    @staticmethod
    def _format_age(created_at_str: str) -> str:
        """Convert a timestamp string to a human-friendly age like '2 weeks ago'."""
        try:
            created = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            now = datetime.utcnow()
            delta = now - created.replace(tzinfo=None)
            days = delta.days
            if days == 0:
                return "today"
            elif days == 1:
                return "yesterday"
            elif days < 7:
                return f"{days} days ago"
            elif days < 14:
                return "1 week ago"
            elif days < 30:
                weeks = days // 7
                return f"{weeks} weeks ago"
            else:
                months = days // 30
                return f"{months} month{'s' if months > 1 else ''} ago"
        except Exception:
            return "recently"

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM content_memory")
            total_posts = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM content_memory WHERE was_approved = TRUE")
            approved_posts = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM validator_memory")
            total_feedback = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM learning_insights")
            total_insights = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM position_memory")
            total_positions = cursor.fetchone()[0]

        return {
            "total_posts_remembered": total_posts,
            "approved_posts": approved_posts,
            "approval_rate": approved_posts / total_posts if total_posts > 0 else 0,
            "total_validator_feedback": total_feedback,
            "total_insights": total_insights,
            "total_positions": total_positions,
            "session_active": self._session is not None,
            "session_posts": self._session.posts_generated if self._session else 0
        }


# ═══════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════════════════

_memory: Optional[AgentMemory] = None


def get_memory(db_path: str = "data/automation/queue.db") -> AgentMemory:
    """Get or create the global memory instance"""
    global _memory
    if _memory is None:
        _memory = AgentMemory(db_path)
    return _memory
