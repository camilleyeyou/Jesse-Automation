"""
QualityDriftAgent — Claude-powered supervisor that runs daily.

Reads a window of recent posts + validator scores + retrieval/fallback stats,
reasons about drift patterns no single-post validator can see, and writes
findings to strategy_insights for the weekly strategist + dashboard to consume.

Uses Claude Sonnet tool-calling via the unified generate_with_tools facade
(provider-routed). Observe-and-report only — does NOT auto-modify prompts,
block posts, or touch the generation hot path.

Tools exposed to the agent (7 reads + 2 writes):
  - get_recent_posts            — content + validator scores + fallback flag
  - count_phrase_in_posts       — pattern recycling detection
  - get_validator_scorecard     — per-validator approval rates + pillar bias
  - get_register_rotation       — 5-register rotation balance (Phase 5, 2026-04-19)
  - get_pillar_distribution     — 5-pillar rotation balance
  - get_fallback_shipping_rate  — how often 'best version' fallback shipped
  - get_recent_findings         — what drift was already flagged (avoid dupes)
  - add_to_generator_avoid_list — actionable: writes to generator's avoid list
  - write_quality_finding       — terminal; persists to strategy_insights
"""

import json
import logging
from typing import Any, Dict, List, Optional

from .base_agent import BaseAgent

try:
    from ..infrastructure.memory import get_memory
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    get_memory = None

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# TOOL DEFINITIONS (OpenAI schema — translated to Anthropic by the AI client)
# ═══════════════════════════════════════════════════════════════════════════

QUALITY_DRIFT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_recent_posts",
            "description": (
                "Return recent posts with their per-validator scores, pillar, "
                "average score, and approval flag. Use this to see what's been "
                "shipping and how validators judged it."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "Look-back window (default 7)", "default": 7},
                    "limit": {"type": "integer", "description": "Max posts to return (default 20)", "default": 20},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "count_phrase_in_posts",
            "description": (
                "Count how many recent posts contain a specific phrase or substring "
                "(case-insensitive). Use this to detect pattern recycling — e.g. "
                "specific tube numbers, ritual closers, or repeated invented details. "
                "Returns the rate and a few excerpts."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "phrase": {"type": "string", "description": "The phrase or substring to search for"},
                    "days": {"type": "integer", "description": "Look-back window (default 14)", "default": 14},
                },
                "required": ["phrase"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_validator_scorecard",
            "description": (
                "Per-validator approval rate, average score, and approval rate "
                "cross-tabulated by pillar. Use this to detect validator bias — "
                "e.g. one validator approving everything, or one validator rejecting "
                "all posts in a particular pillar."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "Look-back window (default 14)", "default": 14},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_register_rotation",
            "description": (
                "How many posts landed in each of the 5 voice registers "
                "(clinical_diagnostician / contrarian / prophet / confession / roast) "
                "over the window. The AngleArchitect picks the register per post; "
                "monotony (one register dominating) means the architect isn't "
                "rotating. Flags when a single register exceeds 60% of posts or "
                "when fewer than 3 distinct registers appear in 7+ posts."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "Look-back window (default 7)", "default": 7},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_pillar_distribution",
            "description": (
                "How many posts landed in each of the five pillars (the_what / "
                "the_what_if / the_who_profits / the_how_to_cope / the_why_it_matters) "
                "over the window. Flags missing pillars and severe imbalance."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "Look-back window (default 14)", "default": 14},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_fallback_shipping_rate",
            "description": (
                "How often did posts ship via the 'max revisions reached, use best "
                "version' fallback instead of clean 2-of-3 validator consensus? "
                "A high fallback rate means the generator is producing content the "
                "validators can't fully approve, which is a quality red flag."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "Look-back window (default 14)", "default": 14},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_recent_findings",
            "description": (
                "Return drift findings already written by previous runs of this agent. "
                "Use this to avoid duplicating findings — if the same issue was flagged "
                "yesterday, either skip it or escalate severity if it persists."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "Look-back window (default 14)", "default": 14},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_to_generator_avoid_list",
            "description": (
                "ACTIONABLE — when you identify a recycled phrase, an overused "
                "template, or a specific detail appearing too often, call this "
                "tool with the exact string. The content generator will see it "
                "in its VARIETY GUARD section on the very next generation and "
                "avoid reusing it. Call this for EACH distinct phrase — do not "
                "bundle multiple phrases into one call. Prefer narrow, literal "
                "strings ('Tube #4,847', 'Stop. Breathe. Apply.', 'keep your "
                "lips human in an AI world') over abstract descriptions. Entries "
                "expire after days_active and can be refreshed by re-adding."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "phrase": {
                        "type": "string",
                        "description": "The literal string to avoid. Case-insensitive matching, exact substring.",
                    },
                    "reason": {
                        "type": "string",
                        "description": "One-line reason the supervisor is flagging this (e.g. 'appeared in 6 of 17 posts')",
                    },
                    "category": {
                        "type": "string",
                        "description": (
                            "One of: specific_detail (e.g. tube numbers, invented stats), "
                            "phrase (e.g. ritual closers, stock taglines), "
                            "structure (e.g. 'In a world where' openers)"
                        ),
                        "enum": ["specific_detail", "phrase", "structure"],
                    },
                    "days_active": {
                        "type": "integer",
                        "description": "How many days the avoid entry stays active before expiring (default 14)",
                        "default": 14,
                    },
                },
                "required": ["phrase", "reason", "category"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_quality_finding",
            "description": (
                "Persist a drift finding to strategy_insights for the weekly strategist "
                "and dashboard to consume. Call this for each distinct issue you've "
                "identified. Call it MULTIPLE TIMES if you find multiple issues. If the "
                "system is healthy, call it ZERO TIMES and end your turn."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "insight_type": {
                        "type": "string",
                        "description": (
                            "Finding category. Use one of: pattern_recycling, voice_drift, "
                            "validator_bias, pillar_imbalance, fallback_overuse, template_overuse, "
                            "register_monotony, rule_violation, other"
                        ),
                    },
                    "observation": {
                        "type": "string",
                        "description": (
                            "One paragraph describing the drift pattern. Be specific — quote "
                            "phrases, name validators, cite counts. This is what the weekly "
                            "strategist will read."
                        ),
                    },
                    "severity": {
                        "type": "string",
                        "description": "One of: info, warning, critical",
                        "enum": ["info", "warning", "critical"],
                    },
                    "evidence": {
                        "type": "object",
                        "description": (
                            "Structured evidence: counts, rates, sample post IDs, etc. "
                            "Will be serialized and stored with the finding."
                        ),
                    },
                    "suggested_action": {
                        "type": "string",
                        "description": (
                            "Concrete change the weekly strategist should consider — e.g. "
                            "'Add tube #4,847 to the specific-details avoid list' or "
                            "'Require the_how_to_cope pillar to be scheduled this week'."
                        ),
                    },
                },
                "required": ["insight_type", "observation", "severity"],
            },
        },
    },
]


# ═══════════════════════════════════════════════════════════════════════════
# AGENT
# ═══════════════════════════════════════════════════════════════════════════


class QualityDriftAgent(BaseAgent):
    """Daily supervisor that detects quality drift patterns over rolling windows."""

    # Cap on how many tool-call iterations we allow per run, to bound cost.
    MAX_ITERATIONS = 8

    # Default model — Claude Sonnet. Routed via provider inference in AI client.
    DEFAULT_MODEL = "claude-sonnet-4-6"

    def __init__(self, ai_client, config, db_path: Optional[str] = None):
        super().__init__(ai_client, config, name="QualityDriftAgent")
        if MEMORY_AVAILABLE:
            # get_memory() defaults to the standard path; only pass db_path if caller supplied one.
            self.memory = get_memory(db_path) if db_path else get_memory()
        else:
            self.memory = None

    async def execute(self, window_days: int = 7, **kwargs) -> Dict[str, Any]:
        """Run the drift-detection loop. Returns a summary of findings written."""
        logger.info("=" * 60)
        logger.info("🔎 QUALITY DRIFT — Supervisor running")
        logger.info("=" * 60)

        if not self.memory:
            logger.warning("QualityDriftAgent: memory not available, skipping run")
            return {"success": False, "reason": "memory_unavailable", "findings": []}

        system_prompt = self._build_system_prompt(window_days)
        user_prompt = self._build_user_prompt(window_days)

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        findings_written: List[Dict[str, Any]] = []

        for iteration in range(self.MAX_ITERATIONS):
            logger.info(f"🔄 Drift iteration {iteration + 1}/{self.MAX_ITERATIONS}")

            try:
                response = await self.ai_client.generate_with_tools(
                    messages=messages,
                    tools=QUALITY_DRIFT_TOOLS,
                    model=self.DEFAULT_MODEL,
                    temperature=0.3,
                    max_tokens=2000,
                )
            except Exception as e:
                logger.error(f"Drift LLM call failed on iteration {iteration + 1}: {e}")
                return {
                    "success": False,
                    "reason": f"llm_error: {e}",
                    "findings": findings_written,
                    "iterations": iteration,
                }

            assistant_message = response.get("message", {})
            messages.append(assistant_message)

            tool_calls = assistant_message.get("tool_calls")
            if not tool_calls:
                logger.info("Agent finished reasoning (no more tool calls)")
                break

            for tool_call in tool_calls:
                fn_name = tool_call["function"]["name"]
                try:
                    fn_args = json.loads(tool_call["function"]["arguments"] or "{}")
                except json.JSONDecodeError:
                    logger.warning(f"  ⚠️ Malformed arguments for {fn_name}, using defaults")
                    fn_args = {}

                logger.info(f"  🔧 {fn_name}({fn_args})")

                try:
                    result = await self._execute_tool(fn_name, fn_args)
                except Exception as e:
                    logger.error(f"  ❌ Tool {fn_name} failed: {e}")
                    result = {"error": f"Tool execution failed: {e}"}

                if fn_name == "write_quality_finding" and isinstance(result, dict) and result.get("id"):
                    findings_written.append({
                        "id": result["id"],
                        "type": fn_args.get("insight_type"),
                        "severity": fn_args.get("severity", "info"),
                        "observation": fn_args.get("observation", ""),
                    })

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(result, default=str),
                })

        logger.info(f"✅ Drift scan complete: {len(findings_written)} findings written")
        return {
            "success": True,
            "findings_count": len(findings_written),
            "findings": findings_written,
            "window_days": window_days,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Prompt construction
    # ─────────────────────────────────────────────────────────────────────────

    def _build_system_prompt(self, window_days: int) -> str:
        return f"""You are the Quality Drift Supervisor for the Jesse A. Eisenbalm content pipeline.

You run once a day. Your job is to detect drift patterns that individual per-post
validators cannot see — things that only become visible over a rolling window of
multiple posts. Your findings feed the weekly strategist on Sunday and the
dashboard every day.

You are BOTH an observer and a corrector. For each drift pattern you detect:

  1. Write a narrative finding via write_quality_finding (for humans + the
     Sunday weekly strategist to read).
  2. If the drift is a specific recycled phrase, template, opener, or
     invented detail — call add_to_generator_avoid_list ONCE per distinct
     phrase. That phrase is then injected into the generator's prompt on
     the VERY NEXT generation, so your finding closes the loop
     automatically (no human intervention required).

You do NOT modify prompts wholesale, block posts, or change system behavior
beyond the avoid-list. Humans and the weekly strategist still read your
narrative findings for broader trends.

WHAT TO LOOK FOR (the window is the last {window_days} days):

1. PATTERN RECYCLING — the same "specific" detail appearing in multiple posts.
   Specific tube numbers (e.g. Tube #4,847), invented company names, recurring
   metrics. If the same detail appears 3+ times in {window_days} days it's
   recycled, not fresh. Use count_phrase_in_posts to check specific suspects.

2. VOICE DRIFT — generic tagline territory creeping in.
   "Keep your lips human in an AI world" / "Not all heroes wear capes" /
   "Corporate funhouse" etc. The brand voice is specific and weird; generic
   brand-speak means Claude is regressing.

3. VALIDATOR BIAS — one validator consistently approving or rejecting when the
   others disagree. Check approval rates via get_validator_scorecard. If Sarah
   is at 95% approval and Marcus at 15%, something is off.

4. PILLAR IMBALANCE — the five pillars (the_what, the_what_if, the_who_profits,
   the_how_to_cope, the_why_it_matters) should rotate. If a pillar has zero
   posts this window, flag it. If one pillar has more than 2x the average,
   flag overuse.

5. FALLBACK OVERUSE — posts shipping via the 'max revisions, use best version'
   fallback instead of clean 2-of-3 validator consensus. A high fallback rate
   is a red flag: the generator is producing content the system can't fully
   approve, and weak posts are reaching the queue.

6. TEMPLATE OVERUSE — "Stop. Breathe. Apply." / "Diagnosed: [Condition]" /
   "Hyper-Arid Social Desiccation" appearing too frequently. The clinical
   voice is a tool, not a default; count occurrences to see if it's dominating.

7. RULE VIOLATIONS that slipped through — banned openers, hashtags, engagement
   bait. There are regex strips for these, but if any survive into shipped
   posts, report them.

8. REGISTER MONOTONY (Phase 5, 2026-04-19) — the AngleArchitect agent picks
   a voice register (clinical_diagnostician / contrarian / prophet / confession
   / roast) for each post. Healthy rotation uses 4+ registers over a week.
   Call get_register_rotation to see the distribution. If one register is
   >60% of posts, flag insight_type='register_monotony' — the architect is
   not rotating and posts will feel same-y regardless of trend diversity.

HOW TO WORK:

- Start by calling get_recent_posts to see the window. Scan for red flags.
- Call get_recent_findings FIRST to avoid restating yesterday's findings. If
  the same issue persists, escalate the severity rather than duplicate the
  finding.
- Use count_phrase_in_posts, get_validator_scorecard, get_pillar_distribution,
  get_register_rotation, get_fallback_shipping_rate to investigate hypotheses.
- For each confirmed drift pattern:
    (a) Call write_quality_finding ONCE with the narrative description.
    (b) If it's a literal recycled phrase/detail/opener — call
        add_to_generator_avoid_list for EACH distinct string, so the next
        generation avoids them automatically. Skip this for abstract
        findings (e.g. "validator X has bias in pillar Y" — no phrase to
        add to the avoid list for that).
- If the system is healthy in a window, write ZERO findings and end your turn.
  Silence is a valid report.

Severity guidance:
  info     — noticed a pattern, worth tracking but not urgent
  warning  — drift is actively hurting quality, fix this week
  critical — systemic failure (e.g. fallback rate > 50%, validator totally broken)

Be specific. Quote phrases. Name validators. Cite counts. The weekly strategist
acts on your findings, so vague observations are useless.

You have {self.MAX_ITERATIONS} tool-calling iterations. Budget them well:
typically 2-4 read calls to understand the state, then the write calls.
"""

    def _build_user_prompt(self, window_days: int) -> str:
        return (
            f"Run your drift-detection scan. The window is the last {window_days} days. "
            "Investigate, then write any findings to strategy_insights. If the pipeline "
            "is healthy, end your turn without writing findings."
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Tool dispatch
    # ─────────────────────────────────────────────────────────────────────────

    async def _execute_tool(self, fn_name: str, fn_args: Dict[str, Any]) -> Dict[str, Any]:
        if fn_name == "get_recent_posts":
            return self._tool_recent_posts(
                days=int(fn_args.get("days", 7)),
                limit=int(fn_args.get("limit", 20)),
            )
        if fn_name == "count_phrase_in_posts":
            phrase = fn_args.get("phrase", "")
            return self.memory.count_phrase_occurrences(
                phrase=phrase,
                days=int(fn_args.get("days", 14)),
            )
        if fn_name == "get_validator_scorecard":
            return self.memory.get_validator_scorecard(days=int(fn_args.get("days", 14)))
        if fn_name == "get_register_rotation":
            return self._tool_register_rotation(days=int(fn_args.get("days", 7)))
        if fn_name == "get_pillar_distribution":
            return self.memory.get_pillar_distribution(days=int(fn_args.get("days", 14)))
        if fn_name == "get_fallback_shipping_rate":
            return self.memory.get_fallback_shipping_rate(days=int(fn_args.get("days", 14)))
        if fn_name == "get_recent_findings":
            return self._tool_recent_findings(days=int(fn_args.get("days", 14)))
        if fn_name == "add_to_generator_avoid_list":
            return self._tool_add_avoid(fn_args)
        if fn_name == "write_quality_finding":
            return self._tool_write_finding(fn_args)

        return {"error": f"Unknown tool: {fn_name}"}

    # ─────────────────────────────────────────────────────────────────────────
    # Tool implementations
    # ─────────────────────────────────────────────────────────────────────────

    def _tool_recent_posts(self, days: int, limit: int) -> Dict[str, Any]:
        posts = self.memory.get_recent_posts_with_validation(days=days, limit=limit)
        # Trim content and validator feedback to keep tool response compact
        for p in posts:
            if p.get("content"):
                p["content"] = p["content"][:400]
            for v in p.get("validators") or []:
                if v.get("feedback"):
                    v["feedback"] = v["feedback"][:200]
        return {"days": days, "count": len(posts), "posts": posts}

    def _tool_register_rotation(self, days: int) -> Dict[str, Any]:
        """Report the distribution of voice registers (clinical_diagnostician /
        contrarian / prophet / confession / roast) over the window. Phase 5
        (2026-04-19) — lets the drift supervisor catch register monotony the
        way it already catches pillar imbalance.
        """
        from collections import Counter
        try:
            registers = self.memory.get_recent_registers(days=days, limit=100)
        except Exception as e:
            return {"days": days, "error": str(e), "registers": []}

        if not registers:
            return {
                "days": days,
                "total_with_register": 0,
                "note": (
                    "No posts in the window have a register tag yet. Either "
                    "the AngleArchitect agent is not live, or all posts "
                    "pre-date Phase 1."
                ),
            }

        counts = Counter(registers)
        total = len(registers)
        dominant, dominant_count = counts.most_common(1)[0]
        dominant_share = dominant_count / total

        # All 5 known registers — so we can report which are missing
        known = {"clinical_diagnostician", "contrarian", "prophet", "confession", "roast"}
        used = set(counts.keys())
        missing = sorted(known - used)

        flags = []
        if dominant_share >= 0.6 and total >= 5:
            flags.append({
                "type": "register_domination",
                "severity": "high" if dominant_share >= 0.8 else "medium",
                "detail": (
                    f"{dominant} is {dominant_share:.0%} of last {total} "
                    f"posts — architect rotation not working"
                ),
            })
        if len(used) < 3 and total >= 7:
            flags.append({
                "type": "register_narrow",
                "severity": "medium",
                "detail": (
                    f"Only {len(used)} distinct register(s) in last {total} "
                    f"posts — missing: {', '.join(missing)}"
                ),
            })
        if len(used) >= 4:
            # Good rotation — note it so the supervisor doesn't over-flag
            flags.append({
                "type": "rotation_healthy",
                "severity": "info",
                "detail": f"Architect using {len(used)} of 5 registers — healthy rotation",
            })

        return {
            "days": days,
            "total_with_register": total,
            "by_register": dict(counts),
            "distinct_registers_used": len(used),
            "missing_registers": missing,
            "dominant_register": dominant,
            "dominant_share": round(dominant_share, 2),
            "flags": flags,
        }

    def _tool_recent_findings(self, days: int) -> Dict[str, Any]:
        findings = self.memory.get_recent_drift_findings(days=days, limit=20)
        for f in findings:
            if f.get("observation"):
                f["observation"] = f["observation"][:400]
        return {"days": days, "count": len(findings), "findings": findings}

    def _tool_add_avoid(self, args: Dict[str, Any]) -> Dict[str, Any]:
        phrase = (args.get("phrase") or "").strip()
        reason = (args.get("reason") or "").strip()
        category = args.get("category") or "phrase"
        days_active = int(args.get("days_active", 14))

        if not phrase:
            return {"success": False, "error": "phrase is required"}

        try:
            entry_id = self.memory.add_to_avoid_list(
                phrase=phrase, reason=reason, category=category, days_active=days_active
            )
            logger.info(f"  ⛔ Avoid added [{category}]: \"{phrase[:60]}\"  (reason: {reason[:60]})")
            return {
                "success": True,
                "id": entry_id,
                "phrase": phrase,
                "category": category,
                "days_active": days_active,
            }
        except Exception as e:
            logger.error(f"  ❌ Failed to add avoid: {e}")
            return {"success": False, "error": str(e)}

    def _tool_write_finding(self, args: Dict[str, Any]) -> Dict[str, Any]:
        insight_type = args.get("insight_type", "other")
        observation = args.get("observation", "").strip()
        severity = args.get("severity", "info")
        evidence = args.get("evidence") or {}
        suggested_action = args.get("suggested_action") or None

        if not observation:
            return {"error": "observation is required", "success": False}

        try:
            finding_id = self.memory.write_quality_finding(
                insight_type=insight_type,
                observation=observation,
                severity=severity,
                evidence=evidence if isinstance(evidence, dict) else None,
                suggested_action=suggested_action,
            )
            logger.info(f"  📌 Finding written [{severity}] {insight_type}: {observation[:80]}")
            return {"success": True, "id": finding_id, "insight_type": f"drift:{insight_type}"}
        except Exception as e:
            logger.error(f"  ❌ Failed to write finding: {e}")
            return {"success": False, "error": str(e)}
