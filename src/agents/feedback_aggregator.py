"""
Feedback Aggregator — synthesizes diagnostic answers into a revision brief.

Fix #3 rewrite: validators no longer return holistic 1-10 scores with generic
"screenshot_worthy" booleans. They return STRUCTURED DIAGNOSTIC ANSWERS that
quote specific failures. This aggregator's job is to turn those answers into a
revision brief the generator can act on — quoting the specific failure rather
than saying "make it punchier."
"""

import json
import logging
from typing import Dict, Any, List
from .base_agent import BaseAgent
from ..models.post import LinkedInPost, ValidationScore

logger = logging.getLogger(__name__)


class FeedbackAggregatorAgent(BaseAgent):
    """Turn diagnostic answers from three validators into an actionable revision brief."""

    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="FeedbackAggregator")
        # Aggregator is a small synthesis task — keep on default OpenAI config (gpt-4o-mini is fine).

    def get_system_prompt(self) -> str:
        return """You are the revision planner for Jesse A. Eisenbalm.

Three validators (Sarah — authenticity / Marcus — craft / Jordan — shareability)
answered diagnostic questions about a post. Your job: distill their specific
failures into a revision brief that QUOTES the failures and proposes concrete
changes. Do not say "make it punchier." Quote the exact broken metaphor, the
exact LLM tell, the exact floating detail.

Approval rule: a post ships if 2 of 3 validators approved. If fewer, you produce
a revision brief focused on the failing validators' specific quotes.

Respond with JSON only."""

    async def execute(self, post: LinkedInPost, validation_scores: List[ValidationScore]) -> Dict[str, Any]:
        self.set_context(post.batch_id, post.post_number)

        diagnostic_summary = self._build_diagnostic_summary(validation_scores)
        prompt = self._build_aggregation_prompt(post, validation_scores, diagnostic_summary)

        try:
            result = await self.generate(prompt)
            content = result.get("content", {})
            if isinstance(content, str):
                content = json.loads(content)

            scores = [v.score for v in validation_scores]
            approvals = [v for v in validation_scores if v.approved]

            return {
                "critical_issues": content.get("critical_issues", []),
                "preserve_elements": content.get("preserve_elements", []),
                "revision_guidance": content.get("revision_guidance", []),
                "priority_focus": content.get("priority_focus", ""),
                "quoted_failures": content.get("quoted_failures", []),
                "proposed_opener": content.get("proposed_opener", ""),
                "consensus_score": sum(scores) / len(scores) if scores else 0,
                "approval_count": len(approvals),
                "total_validators": len(validation_scores),
                "approval_gap": content.get("approval_gap", ""),
                "root_cause": content.get("root_cause", ""),
                "validator_breakdown": {
                    v.agent_name: {
                        "score": v.score,
                        "approved": v.approved,
                        "feedback": v.feedback,
                        "criteria": v.criteria_breakdown,
                    }
                    for v in validation_scores
                },
            }
        except Exception as e:
            self.logger.error(f"Feedback aggregation failed: {e}")
            return self._create_fallback_aggregation(validation_scores)

    def _build_diagnostic_summary(self, validation_scores: List[ValidationScore]) -> str:
        """Extract the specific quoted failures from each validator's diagnostic answers."""
        parts = []
        for v in validation_scores:
            header = f"── {v.agent_name} ({'APPROVED' if v.approved else 'REJECTED'}) — model: {v.criteria_breakdown.get('model', '?')} ──"
            lines = [header]
            cb = v.criteria_breakdown or {}

            if v.agent_name == "SarahChen":
                q1 = cb.get("q1_emotion", {})
                q2 = cb.get("q2_screenshot_sentence", {})
                q3 = cb.get("q3_specifically_jesse", {})
                q4 = cb.get("q4_story_specific_detail", {})
                lines.append(f"  Q1 emotion: {q1.get('word', '?')} (passes={q1.get('passes', False)})")
                lines.append(f"  Q2 screenshot sentence: \"{q2.get('sentence','')}\" (found={q2.get('found', False)})")
                lines.append(f"  Q3 specifically-Jesse: {q3.get('verdict','?')} → change needed: {q3.get('change_needed','none')}")
                lines.append(f"  Q4 story detail: \"{q4.get('detail','')}\" (found={q4.get('found', False)})")
                if cb.get("overall_reaction"):
                    lines.append(f"  Sarah's reaction: {cb['overall_reaction']}")
            elif v.agent_name == "MarcusWilliams":
                q1 = cb.get("q1_weakest_sentence", {})
                q2 = cb.get("q2_metaphors", {})
                q3 = cb.get("q3_llm_tells", {})
                q4 = cb.get("q4_template_crutch", {})
                lines.append(f"  Q1 weakest sentence: \"{q1.get('sentence','')}\" — {q1.get('why','')}")
                broken = [m for m in q2.get("metaphors", []) if not m.get("holds", True)]
                if broken:
                    for m in broken[:3]:
                        lines.append(f"  Q2 broken metaphor: \"{m.get('quote','')}\" — property \"{m.get('property','')}\" doesn't hold")
                else:
                    lines.append("  Q2 metaphors: all hold")
                if q3.get("has_tell"):
                    lines.append(f"  Q3 LLM tell: \"{q3.get('tell','')}\" — {q3.get('justification','')}")
                else:
                    lines.append("  Q3 LLM tells: nowhere")
                if q4.get("has_crutch"):
                    lines.append(
                        f"  Q4 template crutch: \"{q4.get('crutch_opener','')}\" earned={q4.get('earned', False)} "
                        f"→ alternative: {q4.get('alternative_opener','')}"
                    )
                else:
                    lines.append("  Q4 template crutch: none")
            elif v.agent_name == "JordanPark":
                q1 = cb.get("q1_insight", {})
                q2 = cb.get("q2_surprise_moment", {})
                q3 = cb.get("q3_specific_reader", {})
                q4 = cb.get("q4_something_new_taught", {})
                lines.append(f"  Q1 insight: \"{q1.get('sentence','')}\" (rephrase={q1.get('is_rephrase', True)})")
                lines.append(f"  Q2 surprise moment: \"{q2.get('sentence','')}\" (found={q2.get('found', False)})")
                lines.append(f"  Q3 specific reader: \"{q3.get('reader','')}\" (found={q3.get('found', False)})")
                lines.append(f"  Q4 something new taught: \"{q4.get('what_they_learn','')}\" (found={q4.get('found', False)})")
                lines.append(f"  engagement prediction: {cb.get('engagement_prediction','?')}")

            parts.append("\n".join(lines))
        return "\n\n".join(parts)

    def _build_aggregation_prompt(
        self, post: LinkedInPost, validation_scores: List[ValidationScore], diagnostic_summary: str
    ) -> str:
        approvals = sum(1 for v in validation_scores if v.approved)
        return f"""Synthesize a revision brief for this Jesse A. Eisenbalm post.

POST:
\"\"\"
{post.content}
\"\"\"

APPROVAL STATUS: {approvals}/{len(validation_scores)} validators approved.

DIAGNOSTIC ANSWERS:
{diagnostic_summary}

Your job:
1. Identify the ROOT CAUSE — the one structural reason the failing validators rejected.
2. Quote the specific failures (broken metaphor, LLM tell, template crutch, missing insight, etc.).
3. Propose concrete changes — not "make it punchier." If Marcus flagged
   "glacier of red tape" as broken because glaciers don't dry up, say "replace the
   glacier metaphor with one where both sides share the compared property."
4. Preserve what already works — don't blow up lines validators praised.

Return STRICT JSON:
{{
  "root_cause": "<one sentence>",
  "quoted_failures": ["<exact quote of failure 1>", "<failure 2>", ...],
  "critical_issues": [
    {{"issue": "<specific issue>", "raised_by": "<validator name>", "priority": <1-3>}}
  ],
  "preserve_elements": ["<element 1 to keep>", "<element 2>"],
  "revision_guidance": [
    {{"change": "<concrete change>", "reason": "<tied to a quoted failure>", "addresses": "<validator name>"}}
  ],
  "proposed_opener": "<one concrete alternative opener if a template crutch was flagged, else ''>",
  "priority_focus": "<one sentence — the single most important change>",
  "approval_gap": "<need N more approvals>"
}}"""

    def _create_fallback_aggregation(self, validation_scores: List[ValidationScore]) -> Dict[str, Any]:
        approvals = [v for v in validation_scores if v.approved]
        critical_issues = [
            {"issue": v.feedback, "raised_by": v.agent_name, "priority": 1}
            for v in validation_scores
            if not v.approved and v.feedback
        ]
        return {
            "critical_issues": critical_issues[:3],
            "preserve_elements": ["Core Jesse voice — deadpan, specific, AI-vs-lips tension"],
            "revision_guidance": [
                {"change": "Address validator quotes", "reason": "Improve approval rate", "addresses": "All"}
            ],
            "priority_focus": critical_issues[0]["issue"] if critical_issues else "General improvement",
            "quoted_failures": [v.feedback for v in validation_scores if not v.approved and v.feedback][:3],
            "proposed_opener": "",
            "consensus_score": sum(v.score for v in validation_scores) / len(validation_scores) if validation_scores else 0,
            "approval_count": len(approvals),
            "total_validators": len(validation_scores),
            "approval_gap": f"Need {max(0, 2 - len(approvals))} more approvals",
            "root_cause": "Aggregator synthesis unavailable — using raw validator feedback.",
            "validator_breakdown": {
                v.agent_name: {"score": v.score, "approved": v.approved, "feedback": v.feedback}
                for v in validation_scores
            },
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "agent_name": self.name,
            "validators_known": ["Sarah Chen (Claude)", "Marcus Williams (GPT-4o)", "Jordan Park (Gemini)"],
            "approval_rule": "2 of 3 validators must approve",
        }
