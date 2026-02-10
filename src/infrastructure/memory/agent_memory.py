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
                    metadata TEXT
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

            # Create indexes for common queries
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_content_created ON content_memory(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_content_approved ON content_memory(was_approved)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_content_pillar ON content_memory(pillar)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_validator_name ON validator_memory(validator_name)")

            conn.commit()

        logger.debug("Memory tables initialized")

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
        metadata: Dict = None
    ):
        """Store a generated post in memory"""

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
                     topic, trending_topic, was_approved, average_score, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    post_id, batch_id, content, hook, ending, pillar, format, voice,
                    topic, trending_topic, was_approved, average_score,
                    json.dumps(metadata) if metadata else None
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
        else:
            # It's a dict
            name = validation_score.get('agent_name', validation_score.get('validator_name', 'Unknown'))
            score = validation_score.get('score', 0)
            approved = validation_score.get('approved', False)
            feedback = validation_score.get('feedback', '')
            strengths = validation_score.get('strengths', [])
            weaknesses = validation_score.get('weaknesses', [])

        cursor.execute("""
            INSERT INTO validator_memory
            (post_id, validator_name, score, approved, feedback, strengths, weaknesses, pillar, format)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            post_id, name, score, approved, feedback,
            json.dumps(strengths) if strengths else None,
            json.dumps(weaknesses) if weaknesses else None,
            pillar, format
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

        return {
            "total_posts_remembered": total_posts,
            "approved_posts": approved_posts,
            "approval_rate": approved_posts / total_posts if total_posts > 0 else 0,
            "total_validator_feedback": total_feedback,
            "total_insights": total_insights,
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
