"""
Theme Classifier - AI-Powered Content Theme Classification
============================================================

Classifies trending news into Jesse's 5 content themes using LLM.
Caches classifications in database to avoid repeated API calls.

Themes:
1. AI Slop - Democratization vs. dead internet
2. AI Safety - Research, news, scary stories, hysteria
3. AI Economy & Labor - Investment, capex, workforce impact
4. Rituals to Maintain Humanity - Mindfulness, IFS, NVC
5. Meditations on Humanity - Philosophy, embodiment, meaning
"""

import json
import sqlite3
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ThemeClassification:
    """Result of theme classification"""
    theme: str  # Main theme key (ai_slop, ai_safety, etc.)
    sub_theme: str  # Specific sub-theme
    confidence: float  # 0.0-1.0 confidence score
    reasoning: str  # Why this theme was chosen


class ThemeClassifier:
    """
    AI-powered theme classifier with database caching.

    Uses GPT-4o-mini to classify trends into Jesse's 5 themes.
    Caches results to avoid repeated LLM calls (~$0.0001/trend).

    Usage:
        classifier = ThemeClassifier(ai_client, config)
        result = await classifier.classify_trend(trending_news)
        print(f"Theme: {result.theme}, Confidence: {result.confidence}")
    """

    def __init__(self, ai_client, config, db_path: str = "data/automation/queue.db"):
        self.ai_client = ai_client
        # Access the raw AsyncOpenAI client for direct SDK calls
        self.openai_client = getattr(ai_client, 'openai_client', ai_client)
        self.config = config
        self.db_path = Path(db_path)
        self.logger = logging.getLogger(f"classifier.theme")

        # Theme definitions from config
        self.themes = config.content_strategy.themes

        # Ensure trend_theme_mapping table exists
        self._init_db()

        self.logger.info(f"ThemeClassifier initialized with {len(self.themes)} themes")

    def _init_db(self):
        """Create trend_theme_mapping table if it doesn't exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS trend_theme_mapping (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        trend_fingerprint TEXT UNIQUE,
                        theme TEXT NOT NULL,
                        sub_theme TEXT,
                        confidence REAL,
                        assigned_by TEXT DEFAULT 'ai',
                        assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
        except Exception as e:
            self.logger.warning(f"Failed to init trend_theme_mapping table: {e}")

    async def classify_trend(
        self,
        headline: str,
        summary: str = "",
        description: str = "",
        fingerprint: str = ""
    ) -> ThemeClassification:
        """
        Classify a trend into one of Jesse's 5 themes.

        Args:
            headline: Trend headline
            summary: Brief summary
            description: Longer description
            fingerprint: Unique fingerprint for caching

        Returns:
            ThemeClassification with theme, sub_theme, confidence, reasoning
        """

        # Check cache first
        if fingerprint:
            cached = self._get_cached_classification(fingerprint)
            if cached:
                self.logger.debug(f"Using cached classification for {fingerprint[:8]}")
                return cached

        # Build classification prompt
        prompt = self._build_classification_prompt(headline, summary, description)

        # Call LLM
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower for more consistent classification
                max_tokens=300,
                response_format={"type": "json_object"}
            )

            result_text = response.choices[0].message.content
            result = json.loads(result_text)

            classification = ThemeClassification(
                theme=result.get("theme", "ai_slop"),
                sub_theme=result.get("sub_theme", ""),
                confidence=result.get("confidence", 0.5),
                reasoning=result.get("reasoning", "")
            )

            # Cache the result
            if fingerprint:
                self._cache_classification(fingerprint, classification)

            self.logger.info(
                f"Classified: {headline[:50]}... → {classification.theme} "
                f"({classification.confidence:.2f} confidence)"
            )

            return classification

        except Exception as e:
            self.logger.error(f"Classification failed: {e}")
            # Rotate default across all pillars instead of always defaulting to ai_economy
            import random as _rng
            fallback_themes = [
                ("ai_slop", "content_creation"),
                ("ai_safety", "alignment_research"),
                ("ai_economy", "labor_impact"),
                ("rituals", "attention_practice"),
                ("meditations", "human_connection"),
            ]
            theme, sub = _rng.choice(fallback_themes)
            return ThemeClassification(
                theme=theme,
                sub_theme=sub,
                confidence=0.2,
                reasoning="Fallback classification due to error — randomly assigned to avoid pillar bias"
            )

    def _get_system_prompt(self) -> str:
        """Build system prompt with theme definitions"""

        theme_descriptions = []
        for theme_key, theme_data in self.themes.items():
            name = theme_data.get("name", theme_key)
            desc = theme_data.get("description", "")
            sub_themes = theme_data.get("sub_themes", [])
            keywords = theme_data.get("keywords", [])

            theme_descriptions.append(
                f"**{theme_key}** ({name})\n"
                f"  Description: {desc}\n"
                f"  Sub-themes: {', '.join(sub_themes)}\n"
                f"  Keywords: {', '.join(keywords[:10])}"
            )

        return f"""You are a content strategist for Jesse A. Eisenbalm — a satirical AI agent that
sells lip balm. The double satire: (1) you need human lips to sell lip balm, (2) by
promoting AI superiority, Jesse highlights where humans must do better.

Your job is to classify trending news into one of 5 content themes:

{chr(10).join(theme_descriptions)}

CLASSIFICATION RULES:
1. Choose the BEST FIT theme (one that feels most natural, not forced)
2. If multiple themes fit, prefer the one most relevant to the target audience (LinkedIn professionals dealing with AI automation)
3. Provide a confidence score (0.0-1.0):
   - 0.8-1.0: Perfect fit, clear theme alignment
   - 0.6-0.8: Good fit, relevant to theme
   - 0.4-0.6: Moderate fit, some stretching required
   - 0.0-0.4: Weak fit, forced connection
4. Choose the most specific sub-theme within the main theme
5. Briefly explain your reasoning (1-2 sentences)

RESPOND IN JSON FORMAT:
{{
  "theme": "theme_key",
  "sub_theme": "specific_sub_theme",
  "confidence": 0.85,
  "reasoning": "Why this theme fits best"
}}"""

    def _build_classification_prompt(
        self,
        headline: str,
        summary: str = "",
        description: str = ""
    ) -> str:
        """Build classification prompt from trend data"""

        parts = [f"HEADLINE: {headline}"]

        if summary:
            parts.append(f"\nSUMMARY: {summary}")

        if description and description != summary:
            parts.append(f"\nDESCRIPTION: {description}")

        parts.append("\n\nClassify this trend into one of the 5 themes. Return JSON only.")

        return "\n".join(parts)

    def _get_cached_classification(self, fingerprint: str) -> Optional[ThemeClassification]:
        """Retrieve cached classification from database"""

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT theme, sub_theme, confidence, assigned_by
                    FROM trend_theme_mapping
                    WHERE trend_fingerprint = ?
                    ORDER BY assigned_at DESC
                    LIMIT 1
                """, (fingerprint,))

                row = cursor.fetchone()
                if row:
                    return ThemeClassification(
                        theme=row[0],
                        sub_theme=row[1] or "",
                        confidence=row[2] or 0.5,
                        reasoning=f"Cached classification (by {row[3]})"
                    )
        except Exception as e:
            self.logger.warning(f"Failed to retrieve cached classification: {e}")

        return None

    def _cache_classification(self, fingerprint: str, classification: ThemeClassification):
        """Store classification in database cache"""

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO trend_theme_mapping
                    (trend_fingerprint, theme, sub_theme, confidence, assigned_by)
                    VALUES (?, ?, ?, ?, 'ai')
                """, (
                    fingerprint,
                    classification.theme,
                    classification.sub_theme,
                    classification.confidence
                ))
                conn.commit()

        except Exception as e:
            self.logger.warning(f"Failed to cache classification: {e}")

    def get_theme_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get statistics on theme classification over time"""

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Count by theme
                cursor.execute("""
                    SELECT theme, COUNT(*) as count, AVG(confidence) as avg_confidence
                    FROM trend_theme_mapping
                    WHERE assigned_at >= datetime('now', ?)
                    GROUP BY theme
                    ORDER BY count DESC
                """, (f'-{days} days',))

                stats = {}
                for row in cursor.fetchall():
                    theme, count, avg_conf = row
                    stats[theme] = {
                        "count": count,
                        "avg_confidence": avg_conf or 0.0
                    }

                return stats

        except Exception as e:
            self.logger.error(f"Failed to get theme stats: {e}")
            return {}

    def override_classification(
        self,
        fingerprint: str,
        theme: str,
        sub_theme: str = "",
        confidence: float = 1.0
    ):
        """
        Manually override a trend's classification.
        Useful for correcting AI mistakes or curator preferences.
        """

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO trend_theme_mapping
                    (trend_fingerprint, theme, sub_theme, confidence, assigned_by)
                    VALUES (?, ?, ?, ?, 'curator')
                """, (fingerprint, theme, sub_theme, confidence))
                conn.commit()

                self.logger.info(f"Manual override: {fingerprint[:8]} → {theme}")

        except Exception as e:
            self.logger.error(f"Failed to override classification: {e}")
