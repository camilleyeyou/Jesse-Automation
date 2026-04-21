"""
WeeklyReviewAgent — Accountability Loop (Phase 3.3)

Runs every Friday at 6:30 PM (after Portfolio QC at 6:00 PM).
Compares the editorial calendar plan to what actually got posted,
generates an adherence report, and stores it as strategy_insights
so the WeeklyStrategistAgent can adjust next week's plan.

Uses GPT-4o for nuanced comparison analysis.
"""

import json
import logging
from datetime import date, timedelta, datetime
from typing import Dict, Any, List

from .base_agent import BaseAgent

try:
    from ..infrastructure.memory import get_memory
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    get_memory = None

logger = logging.getLogger(__name__)


class WeeklyReviewAgent(BaseAgent):
    """
    Compares this week's editorial calendar plan to actual published posts
    and generates an accountability report with adherence scoring.
    """

    def __init__(self, ai_client, config, db_path="data/automation/queue.db"):
        super().__init__(ai_client=ai_client, config=config, name="WeeklyReview")
        self.memory = get_memory(db_path) if MEMORY_AVAILABLE else None

    async def execute(self, **kwargs) -> Dict[str, Any]:
        logger.info("=" * 60)
        logger.info("📋 WEEKLY REVIEW — Comparing plan vs reality")
        logger.info("=" * 60)

        if not self.memory:
            return {"success": False, "error": "Memory not available"}

        # ── 1. Get this week's Mon-Fri date range ──
        today = date.today()
        # Walk back to Monday of this week
        monday = today - timedelta(days=today.weekday())
        friday = monday + timedelta(days=4)
        week_dates = [(monday + timedelta(days=i)) for i in range(5)]

        start_date = monday.isoformat()
        end_date = friday.isoformat()

        # ── 2. Get editorial calendar entries for this week ──
        calendar_entries = self.memory.get_calendar_week(start_date, end_date)
        logger.info(f"📅 Found {len(calendar_entries)} calendar entries for {start_date} to {end_date}")

        # ── 3. Get actual published posts this week ──
        posts = self.memory.get_recent_posts(days=7, limit=50)
        # Filter to posts created this week (Mon-Fri range)
        weekly_posts = []
        for p in posts:
            created = p.get("created_at", "")[:10]
            if start_date <= created <= end_date:
                weekly_posts.append(p)

        published_posts = [p for p in weekly_posts if p.get("posted_to_linkedin")]
        logger.info(f"📝 Found {len(published_posts)} published posts this week")

        # ── 4. Build the comparison data ──
        comparison = self._build_comparison(week_dates, calendar_entries, published_posts)

        if not calendar_entries and not published_posts:
            logger.info("No calendar entries and no posts this week — skipping review")
            return {
                "success": True,
                "skipped": True,
                "reason": "no_data",
                "message": "No calendar entries or published posts this week",
            }

        # ── 5. Call GPT-4o to analyze ──
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(comparison, start_date, end_date)

        result = await self.ai_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            model="gpt-5.1",
            response_format="json",
            temperature=0.3,
        )

        content = result.get("content", {})
        if isinstance(content, str):
            try:
                content = json.loads(content)
            except json.JSONDecodeError:
                logger.error("Failed to parse weekly review response")
                return {"success": False, "error": "parse_error"}

        # ── 6. Extract scores ──
        adherence_score = content.get("adherence_score", 0)
        deviations = content.get("deviations", [])
        recommendations = content.get("recommendations", [])
        narrative_coherence = content.get("narrative_coherence", "")
        summary = content.get("summary", "")

        # ── 7. Store as strategy_insight with type "weekly_review" ──
        self.memory.add_strategy_insight(
            insight_type="weekly_review",
            observation=json.dumps({
                "adherence_score": adherence_score,
                "deviations": deviations,
                "recommendations": recommendations,
                "narrative_coherence": narrative_coherence,
                "summary": summary,
                "calendar_entries": len(calendar_entries),
                "published_posts": len(published_posts),
                "week": start_date,
                "date": datetime.utcnow().isoformat(),
            }),
            confidence=0.8,
            evidence_count=max(len(calendar_entries), len(published_posts)),
        )

        # ── 8. If adherence below 50%, store a planning_alert ──
        if adherence_score < 50:
            alert_text = (
                f"Weekly adherence score critically low ({adherence_score}/100) "
                f"for week of {start_date}. "
                f"Deviations: {'; '.join(d[:80] for d in deviations[:3]) if deviations else 'unknown'}. "
                f"The strategist should create a more realistic plan next week."
            )
            self.memory.add_strategy_insight(
                insight_type="planning_alert",
                observation=alert_text,
                confidence=0.7,
                evidence_count=max(len(calendar_entries), len(published_posts)),
            )
            logger.warning(f"⚠️ Low adherence ({adherence_score}/100) — planning_alert stored")

        result_summary = {
            "success": True,
            "adherence_score": adherence_score,
            "deviations_count": len(deviations),
            "calendar_entries": len(calendar_entries),
            "published_posts": len(published_posts),
            "narrative_coherence": narrative_coherence[:200] if isinstance(narrative_coherence, str) else str(narrative_coherence),
            "summary": summary[:200],
        }

        logger.info(
            f"📋 Review complete: adherence={adherence_score}/100, "
            f"deviations={len(deviations)}, planned={len(calendar_entries)}, posted={len(published_posts)}"
        )
        return result_summary

    # ═══════════════════════════════════════════════════════════════════════════
    # COMPARISON BUILDER
    # ═══════════════════════════════════════════════════════════════════════════

    def _build_comparison(
        self,
        week_dates: List[date],
        calendar_entries: List[Dict],
        published_posts: List[Dict],
    ) -> List[Dict]:
        """
        For each day Mon-Fri, build a comparison record showing
        what was planned vs what was actually posted.
        """
        # Index calendar entries by date (take last entry per date if duplicates)
        cal_by_date = {}
        for entry in calendar_entries:
            d = entry.get("scheduled_for", "")[:10]
            cal_by_date[d] = entry

        # Index posts by date
        posts_by_date = {}
        for post in published_posts:
            d = post.get("created_at", "")[:10]
            if d not in posts_by_date:
                posts_by_date[d] = []
            posts_by_date[d].append(post)

        comparison = []
        for wd in week_dates:
            ds = wd.isoformat()
            day_name = wd.strftime("%A")

            planned = cal_by_date.get(ds)
            actual_list = posts_by_date.get(ds, [])

            record = {
                "date": ds,
                "day": day_name,
                "planned": None,
                "actual": None,
                "post_published": len(actual_list) > 0,
            }

            if planned:
                record["planned"] = {
                    "theme": planned.get("theme", ""),
                    "format": planned.get("format", ""),
                    "angle_seed": planned.get("angle_seed", ""),
                }

            if actual_list:
                # Take the first published post for that day
                a = actual_list[0]
                record["actual"] = {
                    "theme": a.get("pillar", "") or a.get("theme", ""),
                    "format": a.get("format", ""),
                    "content_preview": (a.get("content", "") or "")[:200],
                    "hook": a.get("hook", ""),
                }

            comparison.append(record)

        return comparison

    # ═══════════════════════════════════════════════════════════════════════════
    # PROMPTS
    # ═══════════════════════════════════════════════════════════════════════════

    def _build_system_prompt(self) -> str:
        return """You are an editorial accountability analyst for Jesse A. Eisenbalm,
a premium lip balm brand with an absurdist, self-aware LinkedIn presence.

Your job is to compare the week's editorial PLAN (from the calendar) to what
actually got PUBLISHED, and produce an honest accountability report.

SCORING GUIDELINES for adherence_score (0-100):
- 90-100: Nearly perfect execution — all days posted, themes/formats match
- 70-89:  Good execution — most days posted, minor deviations
- 50-69:  Partial execution — some days missed or significant theme drift
- 30-49:  Poor execution — major gaps between plan and reality
- 0-29:   Plan largely ignored or no posts published

For theme matching: exact match = full credit, related theme = partial credit, unrelated = no credit.
For format matching: exact match = full credit, similar format = partial credit.
For angle_seed: do a rough semantic check — did the actual post content address the planned angle?
If there was no plan (no calendar entries), score based on whether the week's posts form a coherent set.

OUTPUT FORMAT (strict JSON):
{
  "adherence_score": 75,
  "deviations": [
    "Tuesday: planned ai_economy/hot_take but posted ai_slop/narrative",
    "Thursday: no post published (planned rituals/observation)"
  ],
  "recommendations": [
    "Schedule buffer time for Thursday posts — this is the second week with a Thursday gap",
    "Consider simplifying angle seeds — the more specific ones tend to get ignored"
  ],
  "narrative_coherence": "The week's posts told a loosely connected story about AI overwhelm, though Thursday's gap broke the rhythm. Monday and Wednesday were strong bookends.",
  "summary": "3 of 5 planned posts published. Theme adherence was moderate — 2 exact matches, 1 partial. The strategist should plan lighter on Thursdays."
}"""

    def _build_user_prompt(self, comparison: List[Dict], start_date: str, end_date: str) -> str:
        lines = [f"WEEKLY REVIEW: {start_date} to {end_date}\n"]

        for day in comparison:
            lines.append(f"--- {day['day']} ({day['date']}) ---")

            if day["planned"]:
                p = day["planned"]
                lines.append(f"  PLANNED: theme={p['theme']}, format={p['format']}, angle_seed=\"{p['angle_seed']}\"")
            else:
                lines.append("  PLANNED: (no calendar entry)")

            if day["actual"]:
                a = day["actual"]
                lines.append(f"  ACTUAL:  theme={a['theme']}, format={a['format']}")
                lines.append(f"           content: \"{a['content_preview']}\"")
            else:
                lines.append("  ACTUAL:  (no post published)")

            lines.append("")

        lines.append("Analyze the plan-vs-reality comparison above.")
        lines.append("Score adherence, list deviations, provide recommendations, and assess narrative coherence.")

        return "\n".join(lines)
