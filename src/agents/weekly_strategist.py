"""
WeeklyStrategistAgent — The Strategic Brain (Phase 2)

ReAct-style agent that runs every Sunday at 7:00 AM (after performance
ingestion at 6:00 AM).  It reads engagement data, theme coverage, strategy
insights, and trending signals, then writes a Mon-Fri editorial calendar.

Uses GPT-4o (not mini) for planning quality.

Tool functions available to the agent:
  - get_recent_performance  — engagement data from content_memory
  - get_theme_distribution  — recent theme coverage
  - get_strategy_insights   — accumulated editorial learnings
  - get_trending_signals    — wraps MultiTierTrendService
  - write_weekly_brief      — commits plan to editorial_calendar
"""

import json
import logging
from datetime import date, timedelta
from typing import Dict, Any, List, Optional

from .base_agent import BaseAgent

try:
    from ..infrastructure.memory import get_memory
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    get_memory = None

try:
    from ..infrastructure.trend_service import get_trend_service
    TREND_AVAILABLE = True
except ImportError:
    TREND_AVAILABLE = False

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# TOOL DEFINITIONS (OpenAI function-calling schema)
# ═══════════════════════════════════════════════════════════════════════════

STRATEGIST_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_recent_performance",
            "description": "Get engagement metrics (reactions, comments, shares, impressions) for posts published in the last N days.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back (default 14)",
                        "default": 14,
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_theme_distribution",
            "description": "Get the distribution of content themes used in the last N days. Shows how many posts per theme.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back (default 7)",
                        "default": 7,
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_strategy_insights",
            "description": "Get accumulated editorial learnings (strategy insights) ranked by confidence. These are patterns the system has learned over time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "top": {
                        "type": "integer",
                        "description": "Number of top insights to return (default 10)",
                        "default": 10,
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_trending_signals",
            "description": "Get current trending topics across all sourcing tiers. Returns headlines, themes, and freshness.",
            "parameters": {
                "type": "object",
                "properties": {
                    "count": {
                        "type": "integer",
                        "description": "Number of trending signals to fetch (default 10)",
                        "default": 10,
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_adaptive_weights",
            "description": "Get recommended theme weights based on rolling engagement performance. Themes with higher engagement get more weight. Also lists underexplored formats for A/B testing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days for rolling average (default 30)",
                        "default": 30,
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_weekly_brief",
            "description": "Commit the weekly editorial plan to the editorial_calendar. Call this once you have decided the plan for Mon-Fri.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content_slots": {
                        "type": "array",
                        "description": "Array of 5 content slot objects, one per weekday (Mon-Fri).",
                        "items": {
                            "type": "object",
                            "properties": {
                                "day": {"type": "string", "description": "Day of week: monday, tuesday, etc."},
                                "theme": {"type": "string", "description": "Content theme key: ai_slop, ai_safety, ai_economy, rituals, meditations"},
                                "format": {"type": "string", "description": "Post format: observation, hot_take, narrative, question, confession, breaking, list"},
                                "angle_seed": {"type": "string", "description": "1-2 sentence seed describing the specific angle or hook for the day's post"},
                            },
                            "required": ["day", "theme", "angle_seed"],
                        },
                    },
                    "avoid_guidance": {
                        "type": "string",
                        "description": "Themes, formats, or angles to avoid this week (based on recent overuse or poor performance).",
                    },
                    "double_down_guidance": {
                        "type": "string",
                        "description": "Themes, formats, or angles to lean into this week (based on strong recent performance).",
                    },
                },
                "required": ["content_slots"],
            },
        },
    },
]


class WeeklyStrategistAgent(BaseAgent):
    """
    ReAct agent that plans the weekly editorial calendar.

    Flow:
    1. System prompt frames the task
    2. Agent calls tools to gather data
    3. Agent reasons about what it learned
    4. Agent calls write_weekly_brief to commit the plan
    """

    MAX_ITERATIONS = 8  # Safety limit on ReAct loop

    def __init__(self, ai_client, config, trend_service=None, db_path="data/automation/queue.db"):
        super().__init__(ai_client=ai_client, config=config, name="WeeklyStrategist")
        self.trend_service = trend_service
        self.db_path = db_path
        self.memory = get_memory(db_path) if MEMORY_AVAILABLE else None

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Run the weekly strategy planning loop.

        Returns the editorial brief that was written, or error info.
        """
        logger.info("=" * 60)
        logger.info("🧠 WEEKLY STRATEGIST — Planning editorial calendar")
        logger.info("=" * 60)

        # Calculate the upcoming Mon-Fri dates
        today = date.today()
        # Find next Monday (or today if it's Monday)
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0 and today.weekday() != 0:
            days_until_monday = 7
        next_monday = today + timedelta(days=days_until_monday)
        week_dates = [(next_monday + timedelta(days=i)) for i in range(5)]
        week_str = f"{week_dates[0].isoformat()} to {week_dates[-1].isoformat()}"

        system_prompt = self._build_system_prompt(week_str)
        user_prompt = self._build_user_prompt(week_dates)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        brief_result = None

        for iteration in range(self.MAX_ITERATIONS):
            logger.info(f"🔄 ReAct iteration {iteration + 1}/{self.MAX_ITERATIONS}")

            response = await self.ai_client.generate_with_tools(
                messages=messages,
                tools=STRATEGIST_TOOLS,
                model="gpt-4o",
                temperature=0.7,
            )

            assistant_message = response.get("message", {})
            messages.append(assistant_message)

            tool_calls = assistant_message.get("tool_calls")

            if not tool_calls:
                # Agent is done reasoning — no more tool calls
                logger.info("Agent finished reasoning (no tool calls)")
                break

            # Execute each tool call
            for tool_call in tool_calls:
                fn_name = tool_call["function"]["name"]
                try:
                    fn_args = json.loads(tool_call["function"]["arguments"] or "{}")
                except json.JSONDecodeError:
                    logger.warning(f"  ⚠️ Malformed arguments for {fn_name}, using defaults")
                    fn_args = {}

                logger.info(f"  🔧 Tool: {fn_name}({fn_args})")

                try:
                    result = await self._execute_tool(fn_name, fn_args, week_dates)
                except Exception as e:
                    logger.error(f"  ❌ Tool {fn_name} failed: {e}")
                    result = {"error": f"Tool execution failed: {e}"}

                if fn_name == "write_weekly_brief":
                    brief_result = result

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(result, default=str),
                })

        if brief_result and brief_result.get("success"):
            logger.info(f"✅ Weekly brief written: {len(brief_result.get('entries', []))} calendar entries")
            return brief_result
        else:
            logger.warning("⚠️ Agent did not write a weekly brief")
            # Extract the last assistant text as the reasoning
            last_text = ""
            for msg in reversed(messages):
                if msg.get("role") == "assistant" and msg.get("content"):
                    last_text = msg["content"]
                    break
            return {
                "success": False,
                "error": "Agent did not call write_weekly_brief",
                "reasoning": last_text[:500],
            }

    # ═══════════════════════════════════════════════════════════════════════════
    # TOOL EXECUTION
    # ═══════════════════════════════════════════════════════════════════════════

    async def _execute_tool(self, fn_name: str, fn_args: Dict, week_dates: list) -> Dict:
        """Route a tool call to its handler."""

        if fn_name == "get_recent_performance":
            return self._tool_recent_performance(fn_args.get("days", 14))

        elif fn_name == "get_theme_distribution":
            return self._tool_theme_distribution(fn_args.get("days", 7))

        elif fn_name == "get_strategy_insights":
            return self._tool_strategy_insights(fn_args.get("top", 10))

        elif fn_name == "get_trending_signals":
            return await self._tool_trending_signals(fn_args.get("count", 10))

        elif fn_name == "get_adaptive_weights":
            return self._tool_adaptive_weights(fn_args.get("days", 30))

        elif fn_name == "write_weekly_brief":
            return self._tool_write_weekly_brief(fn_args, week_dates)

        else:
            return {"error": f"Unknown tool: {fn_name}"}

    def _tool_recent_performance(self, days: int) -> Dict:
        if not self.memory:
            return {"error": "Memory not available", "posts": []}

        posts = self.memory.get_recent_performance(days=days)

        if not posts:
            return {"posts": [], "summary": "No engagement data available yet."}

        # Compute summary stats
        total = len(posts)
        avg_engagement = sum(p.get("engagement_score", 0) or 0 for p in posts) / total
        avg_reactions = sum(p.get("reactions", 0) or 0 for p in posts) / total
        avg_comments = sum(p.get("comments", 0) or 0 for p in posts) / total

        return {
            "posts": posts,
            "summary": {
                "total_posts": total,
                "avg_engagement_score": round(avg_engagement, 1),
                "avg_reactions": round(avg_reactions, 1),
                "avg_comments": round(avg_comments, 1),
            },
        }

    def _tool_theme_distribution(self, days: int) -> Dict:
        if not self.memory:
            return {"error": "Memory not available"}

        posts = self.memory.get_recent_posts(days=days, limit=100)

        theme_counts = {}
        for p in posts:
            theme = p.get("theme") or "unclassified"
            theme_counts[theme] = theme_counts.get(theme, 0) + 1

        return {
            "distribution": theme_counts,
            "total_posts": len(posts),
            "days": days,
        }

    def _tool_strategy_insights(self, top: int) -> Dict:
        if not self.memory:
            return {"error": "Memory not available", "insights": []}

        insights = self.memory.get_strategy_insights(top=top)
        return {"insights": insights}

    def _tool_adaptive_weights(self, days: int) -> Dict:
        if not self.memory:
            return {"error": "Memory not available"}

        weights = self.memory.compute_adaptive_weights(days=days)
        theme_perf = self.memory.get_theme_performance(days=days)
        format_perf = self.memory.get_format_performance(days=days)
        underexplored = self.memory.get_underexplored_formats(days=days)

        return {
            "adaptive_weights": {k: round(v, 3) for k, v in weights.items()},
            "theme_performance": {
                k: {"count": v.get("count", 0), "avg_engagement": round(v.get("avg_engagement", 0), 1)}
                for k, v in theme_perf.items()
            },
            "format_performance": {
                k: {"count": v.get("count", 0), "avg_engagement": round(v.get("avg_engagement", 0), 1)}
                for k, v in format_perf.items()
            },
            "underexplored_formats": underexplored,
            "note": "Underexplored formats have fewer than 3 posts — consider testing them this week.",
        }

    async def _tool_trending_signals(self, count: int) -> Dict:
        if not self.trend_service:
            return {"error": "Trend service not available", "signals": []}

        try:
            self.trend_service.reset_for_new_batch()
            trends = await self.trend_service.get_candidate_trends(count=count)

            signals = []
            for t in trends:
                signals.append({
                    "headline": t.headline,
                    "category": t.category,
                    "theme": getattr(t, "theme", None),
                    "sub_theme": getattr(t, "sub_theme", None),
                    "tier": getattr(t, "tier", None),
                    "summary": t.summary[:200] if t.summary else None,
                })
            return {"signals": signals, "count": len(signals)}

        except Exception as e:
            logger.error(f"Trending signals fetch failed: {e}")
            return {"error": str(e), "signals": []}

    def _tool_write_weekly_brief(self, args: Dict, week_dates: list) -> Dict:
        if not self.memory:
            return {"success": False, "error": "Memory not available"}

        content_slots = args.get("content_slots", [])
        avoid_guidance = args.get("avoid_guidance", "")
        double_down_guidance = args.get("double_down_guidance", "")

        if not content_slots:
            return {"success": False, "error": "No content_slots provided"}

        # Map day names to dates
        day_map = {
            "monday": 0, "tuesday": 1, "wednesday": 2,
            "thursday": 3, "friday": 4,
        }

        entries = []
        for slot in content_slots:
            day_name = slot.get("day", "").lower()
            day_idx = day_map.get(day_name)

            if day_idx is not None and day_idx < len(week_dates):
                scheduled_for = week_dates[day_idx].isoformat()
            else:
                # Best effort: use slots in order
                idx = len(entries)
                if idx < len(week_dates):
                    scheduled_for = week_dates[idx].isoformat()
                else:
                    continue

            entry_id = self.memory.add_calendar_entry(
                scheduled_for=scheduled_for,
                theme=slot.get("theme", ""),
                format=slot.get("format"),
                angle_seed=slot.get("angle_seed", ""),
                created_by="strategist_agent",
            )
            entries.append({
                "id": entry_id,
                "scheduled_for": scheduled_for,
                "theme": slot.get("theme"),
                "format": slot.get("format"),
                "angle_seed": slot.get("angle_seed"),
            })

        # Store guidance as strategy insights
        if avoid_guidance:
            self.memory.add_strategy_insight(
                insight_type="weekly_avoid",
                observation=avoid_guidance,
                confidence=0.6,
                evidence_count=1,
            )
        if double_down_guidance:
            self.memory.add_strategy_insight(
                insight_type="weekly_double_down",
                observation=double_down_guidance,
                confidence=0.6,
                evidence_count=1,
            )

        logger.info(f"📅 Written {len(entries)} editorial calendar entries")
        return {
            "success": True,
            "entries": entries,
            "avoid_guidance": avoid_guidance,
            "double_down_guidance": double_down_guidance,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # PROMPTS
    # ═══════════════════════════════════════════════════════════════════════════

    def _build_system_prompt(self, week_str: str) -> str:
        # Load theme names from config
        themes_desc = ""
        if hasattr(self.config, "content_strategy"):
            themes = self.config.content_strategy.themes
            lines = []
            for key, data in themes.items():
                name = data.get("name", key)
                desc = data.get("description", "")
                subs = ", ".join(data.get("sub_themes", []))
                lines.append(f"  - {key}: {name} — {desc} (sub-themes: {subs})")
            themes_desc = "\n".join(lines)

        return f"""You are the Editorial Strategist for Jesse A. Eisenbalm, a premium lip balm brand
that creates absurdist, self-aware LinkedIn content for working professionals.

YOUR TASK: Plan the editorial calendar for the week of {week_str}.

You have access to tools that let you read engagement data, theme coverage,
strategy insights, and trending signals. Use them to make data-driven decisions.

CONTENT THEMES:
{themes_desc}

PLANNING PRINCIPLES:
1. Theme variety — don't repeat the same theme two days in a row
2. Format variety — mix observations, hot takes, narratives, questions, confessions
3. Performance-informed — lean into themes/formats that get high engagement
4. Trend-reactive — if a strong signal is trending, work it into the calendar
5. Brand voice — Jesse is dry, absurdist, minimal, genuinely funny (not trying-hard funny)
6. Always plan exactly 5 slots (Monday through Friday)

WORKFLOW:
1. Call get_recent_performance to see what's been working
2. Call get_theme_distribution to check recent coverage
3. Call get_strategy_insights to read accumulated learnings
4. Call get_adaptive_weights to see recommended theme allocation + underexplored formats
5. Call get_trending_signals to see what's happening in the world
6. Reason about all the data
7. Call write_weekly_brief with your plan

ADAPTIVE WEIGHTS: The system computes recommended theme weights from engagement data.
Use these as guidance — favour high-weight themes but don't ignore the rest.

A/B FORMAT TESTING: If underexplored formats are flagged, schedule at least one this week
to gather data. Vary formats across the week (don't repeat the same format two days in a row).

ACCOUNTABILITY FEEDBACK: If weekly_review insights exist in strategy insights, pay special
attention to adherence issues and adjust your plan to be more realistic. Look for:
- Low adherence scores → simplify the plan, use broader angle seeds
- Recurring missed days → avoid scheduling ambitious content on those days
- planning_alert insights → the previous week's plan was too ambitious or misaligned

DO NOT skip the data-gathering steps. Read the data first, then decide."""

    def _build_user_prompt(self, week_dates: list) -> str:
        dates_str = "\n".join(
            f"  - {d.strftime('%A')}: {d.isoformat()}"
            for d in week_dates
        )
        return f"""Plan the editorial calendar for this upcoming week.

Dates to fill:
{dates_str}

Start by gathering data with the available tools, then write the weekly brief."""
