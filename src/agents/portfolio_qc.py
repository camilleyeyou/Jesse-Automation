"""
PortfolioQCAgent — Brand Consistency Guardian (Phase 3.2)

Runs every Friday at 6:00 PM.
Evaluates the last 10 posts as a COLLECTION (not individually) to detect:
- Brand voice consistency / tone drift
- Reading level trends
- Positioning adherence (is Jesse still Jesse?)
- Theme/format diversity health

Writes a scored report to strategy_insights and flags drift for human review.
Uses GPT-4o for nuanced brand analysis.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List

from .base_agent import BaseAgent

try:
    from ..infrastructure.memory import get_memory
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    get_memory = None

logger = logging.getLogger(__name__)


class PortfolioQCAgent(BaseAgent):
    """
    Reviews recent posts as a portfolio/collection and scores brand health.
    """

    def __init__(self, ai_client, config, db_path="data/automation/queue.db"):
        super().__init__(ai_client=ai_client, config=config, name="PortfolioQC")
        self.memory = get_memory(db_path) if MEMORY_AVAILABLE else None

    async def execute(self, **kwargs) -> Dict[str, Any]:
        logger.info("=" * 60)
        logger.info("🔍 PORTFOLIO QC — Evaluating brand consistency")
        logger.info("=" * 60)

        if not self.memory:
            return {"success": False, "error": "Memory not available"}

        # Get last 10 published posts
        posts = self.memory.get_recent_posts(days=14, limit=10)
        published = [p for p in posts if p.get("posted_to_linkedin")]

        if len(published) < 3:
            logger.info(f"Only {len(published)} published posts — need at least 3 for QC")
            return {"success": True, "skipped": True, "reason": "insufficient_posts", "count": len(published)}

        prompt = self._build_prompt(published)
        system_prompt = self._build_system_prompt()

        result = await self.ai_client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            model="gpt-4o",
            response_format="json",
            temperature=0.3,
        )

        content = result.get("content", {})
        if isinstance(content, str):
            try:
                content = json.loads(content)
            except json.JSONDecodeError:
                logger.error("Failed to parse QC response")
                return {"success": False, "error": "parse_error"}

        # Save the QC report as a strategy insight
        overall_score = content.get("overall_score", 0)
        drift_detected = content.get("drift_detected", False)
        report_summary = content.get("summary", "")

        self.memory.add_strategy_insight(
            insight_type="portfolio_qc",
            observation=json.dumps({
                "overall_score": overall_score,
                "voice_consistency": content.get("voice_consistency", 0),
                "tone_drift": content.get("tone_drift", "none"),
                "reading_level_trend": content.get("reading_level_trend", "stable"),
                "positioning_adherence": content.get("positioning_adherence", 0),
                "diversity_score": content.get("diversity_score", 0),
                "drift_detected": drift_detected,
                "flags": content.get("flags", []),
                "summary": report_summary,
                "posts_evaluated": len(published),
                "date": datetime.utcnow().isoformat(),
            }),
            confidence=0.8,
            evidence_count=len(published),
        )

        # If drift is detected, also add a targeted insight for the strategist
        if drift_detected:
            flags = content.get("flags", [])
            flag_text = "; ".join(flags[:3]) if flags else "General drift detected"
            self.memory.add_strategy_insight(
                insight_type="drift_alert",
                observation=f"Portfolio QC flagged drift: {flag_text}",
                confidence=0.7,
                evidence_count=len(published),
            )
            logger.warning(f"⚠️ Drift detected: {flag_text}")

        summary = {
            "success": True,
            "overall_score": overall_score,
            "drift_detected": drift_detected,
            "posts_evaluated": len(published),
            "summary": report_summary[:200],
        }

        logger.info(f"🔍 QC complete: score={overall_score}/10, drift={'YES' if drift_detected else 'no'}")
        return summary

    def _build_system_prompt(self) -> str:
        return """You are a brand strategist reviewing a portfolio of LinkedIn posts for
Jesse A. Eisenbalm — a satirical AI agent that pushes lip balm and has lots of
commentary on how AI and bots are superior to humans, except they don't have lips.

BRAND ANCHORS:
- Voice: Fun, clear, satirical — Absurdist Modern Luxury
- Character: Jesse is a satirical AI agent, not a brand. Proudly AI-powered.
- THE DOUBLE SATIRE:
  1. You need human lips to sell lip balm (beauty = rich ground for human oddity)
  2. By promoting AI, Jesse highlights where humans must do better
- Sentiment range: 25% smug AI superiority, 25% dry warmth, 25% absurdist joy, 25% genuine humanity
- THE DRY COMEDY ENGINE: Jesse treats "dryness" as a double meaning — dry humor,
  dry lips, dry corporate culture. Clinical diagnostician voice uses pseudo-scientific
  language, invented conditions, dryness scores. Selling relief, not chapstick.
- Word limit: 40-100 words per post
- No hashtags, no external links in post body
- The product ($8.99 lip balm) is always the quiet anchor, never the hard sell
- If the AI-vs-human-lips tension disappears entirely, that's drift

EVALUATE THE POSTS AS A COLLECTION. Score each dimension 1-10.

DRIFT DETECTION THRESHOLDS (apply these strictly):
- voice_consistency < 6 → drift_detected = true
- positioning_adherence < 6 → drift_detected = true
- tone_drift = "significant" → drift_detected = true
- diversity_score < 4 → drift_detected = true (theme/format monotony)
- If 3+ posts in a row have the same emotional tone → flag as "one-note"
- If 0 posts answer HOW TO COPE or WHY IT MATTERS → flag as "missing warmth"
- If any single pillar exceeds 40% of posts → flag as "pillar_imbalance" (e.g., "ai_economy is 72% of content — target is ~20%")
- If 0 posts from AI Slop, AI Safety, Rituals, or Humanity → flag as "pillar_starvation"
- If clinical diagnostician posts hedge or wink at their own format → flag as "clinical_commitment_break"
- If same invented condition is reused across posts → flag as "dryness_repetition"
- If 0 posts use clinical/diagnostic/pseudo-scientific framing → flag as "underusing_dry_comedy_engine"

TONE DRIFT DEFINITIONS:
- "none" = Jesse's full range is present (smug, warm, amused, concerned, etc.)
- "mild" = Slightly leaning into one tone but still some variety
- "significant" = 70%+ of posts are the same emotional register (usually cynical/snarky)

OUTPUT FORMAT (JSON):
{
  "overall_score": 7.5,
  "voice_consistency": 8,
  "positioning_adherence": 7,
  "diversity_score": 6,
  "reading_level_trend": "stable",
  "tone_drift": "none|mild|significant",
  "drift_detected": false,
  "flags": ["specific concern 1", "specific concern 2"],
  "recommendations": ["actionable suggestion 1"],
  "summary": "2-3 sentence executive summary"
}"""

    def _build_prompt(self, posts: list) -> str:
        post_blocks = []
        for i, p in enumerate(posts, 1):
            content = p.get("content", "")[:300]
            theme = p.get("theme", "?")
            fmt = p.get("format", "?")
            score = p.get("average_score", 0)
            eng = p.get("engagement_score", "n/a")
            date = p.get("created_at", "?")

            post_blocks.append(
                f"POST {i} ({date[:10]}) — theme: {theme}, format: {fmt}, "
                f"validator_avg: {score:.1f}, engagement: {eng}\n"
                f'"""{content}"""'
            )

        posts_text = "\n\n".join(post_blocks)

        return f"""Review these {len(posts)} recent LinkedIn posts as a portfolio.
Evaluate brand consistency, tone drift, diversity, and positioning adherence.

{posts_text}

Score each dimension and flag any drift or concerns."""
