"""
StrategyRefinementAgent — The Learning Loop (Phase 3.1)

Runs every Sunday at 6:30 AM (after performance ingestion, before strategist).
Reads the past week's post performance vs historical averages and generates
2-3 new strategy_insights entries. Also updates confidence scores on existing
insights when new evidence supports or contradicts them.

Uses GPT-4o for analytical quality.
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


class StrategyRefinementAgent(BaseAgent):
    """
    Analyses post performance and distils reusable editorial insights.

    Each week it:
    1. Reads this week's engagement data + historical averages
    2. Asks GPT-4o to identify patterns and generate insights
    3. Writes new strategy_insights rows (or updates existing ones)
    """

    def __init__(self, ai_client, config, db_path="data/automation/queue.db"):
        super().__init__(ai_client=ai_client, config=config, name="StrategyRefinement")
        self.memory = get_memory(db_path) if MEMORY_AVAILABLE else None

    async def execute(self, **kwargs) -> Dict[str, Any]:
        logger.info("=" * 60)
        logger.info("📈 STRATEGY REFINEMENT — Analysing performance patterns")
        logger.info("=" * 60)

        if not self.memory:
            return {"success": False, "error": "Memory not available"}

        # Gather data
        recent = self.memory.get_recent_performance(days=7)
        historical = self.memory.get_recent_performance(days=60)
        existing_insights = self.memory.get_strategy_insights(top=20)

        if not recent and not historical:
            logger.info("No performance data yet — skipping refinement")
            return {"success": True, "new_insights": 0, "updated_insights": 0, "reason": "no_data"}

        # Build the analysis prompt
        prompt = self._build_prompt(recent, historical, existing_insights)
        system_prompt = self._build_system_prompt()

        result = await self.ai_client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            model="gpt-4o",
            response_format="json",
            temperature=0.4,
        )

        content = result.get("content", {})
        if isinstance(content, str):
            try:
                content = json.loads(content)
            except json.JSONDecodeError:
                logger.error("Failed to parse refinement response")
                return {"success": False, "error": "parse_error"}

        # Write new insights
        new_insights = content.get("new_insights", [])
        updated_insights = content.get("updated_insights", [])

        new_count = 0
        for ins in new_insights[:3]:  # Cap at 3 per week
            try:
                self.memory.add_strategy_insight(
                    insight_type=ins.get("type", "general"),
                    observation=ins.get("observation", ""),
                    confidence=float(ins.get("confidence", 0.3)),
                    evidence_count=int(ins.get("evidence_count", 1)),
                )
                new_count += 1
                logger.info(f"  📝 New insight: {ins.get('observation', '')[:80]}...")
            except Exception as e:
                logger.warning(f"  Failed to save insight: {e}")

        # Update existing insights with new evidence
        updated_count = 0
        for upd in updated_insights:
            try:
                insight_id = int(upd.get("id", 0))
                if insight_id > 0:
                    self.memory.update_strategy_insight(
                        insight_id=insight_id,
                        confidence=float(upd.get("new_confidence", 0.5)),
                        evidence_count=int(upd.get("new_evidence_count", 1)),
                    )
                    updated_count += 1
                    logger.info(f"  🔄 Updated insight #{insight_id}: confidence → {upd.get('new_confidence')}")
            except Exception as e:
                logger.warning(f"  Failed to update insight: {e}")

        summary = {
            "success": True,
            "new_insights": new_count,
            "updated_insights": updated_count,
            "recent_posts_analysed": len(recent),
            "historical_posts_analysed": len(historical),
        }
        logger.info(f"📈 Refinement complete: {new_count} new, {updated_count} updated")
        return summary

    def _build_system_prompt(self) -> str:
        return """You are a data-driven editorial analyst for a LinkedIn content account.

Your job is to look at this week's post performance alongside historical averages
and identify actionable patterns. You output structured JSON.

RULES:
- Generate 1-3 NEW insights per week (quality over quantity)
- Each insight must be specific and falsifiable (not generic advice)
- Confidence starts low (0.2-0.5) and grows with evidence
- If existing insights are supported or contradicted by new data, flag them for update
- If new evidence CONTRADICTS a high-confidence insight, lower its confidence — don't ignore the conflict
- Insight types: format_learning, theme_performance, timing, voice, engagement_pattern

QUALITY GATE — Every insight MUST include:
1. A specific comparison (X vs Y, not just "X performs well")
2. At least one number (engagement score, percentage, count)
3. A time range ("over N weeks" or "in the last N posts")

REJECT THESE GENERIC PLATITUDES (do NOT generate insights like these):
❌ "Shorter posts perform better" — too vague, no comparison
❌ "Engaging content gets more engagement" — tautology
❌ "Posts about trending topics do well" — obvious, not actionable
❌ "Variety is important" — not falsifiable
❌ "The audience responds to authenticity" — unmeasurable

GOOD INSIGHT EXAMPLES:
✅ "First-person absurdist posts average 3.2x engagement vs third-person narrative (observed across 8 posts over 6 weeks)"
✅ "AI Safety content gets 40% more comments than AI Slop; AI Slop gets 2x more shares (based on 12 posts)"
✅ "Posts with a named source in the hook average 28 reactions vs 14 for posts with generic hooks (last 10 posts)"
✅ "Tuesday 9am posts outperform Thursday 4pm by 40% on impressions (12-week rolling average)"

OUTPUT FORMAT (JSON):
{
  "new_insights": [
    {
      "type": "format_learning",
      "observation": "Specific, measurable observation with data",
      "confidence": 0.3,
      "evidence_count": 1
    }
  ],
  "updated_insights": [
    {
      "id": 5,
      "reason": "Why this insight's confidence changed",
      "new_confidence": 0.6,
      "new_evidence_count": 8
    }
  ],
  "analysis_notes": "Brief reasoning summary"
}"""

    def _build_prompt(self, recent: list, historical: list, existing_insights: list) -> str:
        # Format recent performance
        recent_lines = []
        for p in recent[:15]:
            recent_lines.append(
                f"  - theme={p.get('theme','?')} format={p.get('format','?')} "
                f"engagement={p.get('engagement_score',0)} "
                f"reactions={p.get('reactions',0)} comments={p.get('comments',0)} "
                f"shares={p.get('shares',0)} impressions={p.get('impressions',0)} "
                f"validator_avg={p.get('average_score',0):.1f} "
                f"date={p.get('created_at','?')}"
            )
        recent_block = "\n".join(recent_lines) if recent_lines else "  (no data this week)"

        # Compute historical averages
        if historical:
            avg_eng = sum(p.get("engagement_score", 0) or 0 for p in historical) / len(historical)
            avg_react = sum(p.get("reactions", 0) or 0 for p in historical) / len(historical)
            avg_comm = sum(p.get("comments", 0) or 0 for p in historical) / len(historical)
            hist_block = (
                f"  Posts: {len(historical)}, Avg engagement: {avg_eng:.1f}, "
                f"Avg reactions: {avg_react:.1f}, Avg comments: {avg_comm:.1f}"
            )
        else:
            hist_block = "  (no historical data yet)"

        # Format existing insights
        insight_lines = []
        for ins in existing_insights[:15]:
            insight_lines.append(
                f"  - [id={ins.get('id')}] type={ins.get('insight_type')} "
                f"confidence={ins.get('confidence',0):.2f} "
                f"evidence={ins.get('evidence_count',0)} "
                f"observation=\"{ins.get('observation','')[:100]}\""
            )
        insights_block = "\n".join(insight_lines) if insight_lines else "  (none yet)"

        return f"""Analyse performance data and generate editorial insights.

THIS WEEK'S POSTS:
{recent_block}

HISTORICAL AVERAGES (60 days):
{hist_block}

EXISTING INSIGHTS:
{insights_block}

Based on this data, identify 1-3 new patterns and flag any existing insights
that should have their confidence updated. Be specific and data-driven."""
