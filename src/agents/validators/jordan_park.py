"""
Jordan Park Validator — PERFORMANCE / SHAREABILITY (Gemini)

Fix #3 rewrite: stop asking for a 1-10 score. Ask four falsifiable diagnostic
questions about whether this post will land on LinkedIn — insight, surprise
moment, specific reader, something-new-taught — and derive approval mechanically.
Routes through Gemini so Jordan is independent from Sarah (Claude) and Marcus
(GPT-4o); three holistic judgments from the same model are not three independent
judgments.
"""

import json
import logging
from typing import Dict, Any
from ..base_agent import BaseAgent
from ...models.post import LinkedInPost, ValidationScore

logger = logging.getLogger(__name__)


class JordanParkValidator(BaseAgent):
    """Shareability validator — will this actually land on LinkedIn?"""

    # Response schema pinned for Gemini. Without this, Gemini returns JSON but
    # invents its own key names — and _parse_validation reads empty dicts for
    # q1/q2/q3/q4 so every post fails all diagnostics. With this schema, Gemini
    # is constrained to emit the exact shape we parse.
    RESPONSE_SCHEMA = {
        "type": "object",
        "properties": {
            "q1_insight": {
                "type": "object",
                "properties": {
                    "sentence": {"type": "string"},
                    "is_rephrase": {"type": "boolean"},
                    "passes": {"type": "boolean"},
                },
                "required": ["sentence", "is_rephrase", "passes"],
            },
            "q2_surprise_moment": {
                "type": "object",
                "properties": {
                    "sentence": {"type": "string"},
                    "found": {"type": "boolean"},
                    "why": {"type": "string"},
                },
                "required": ["sentence", "found", "why"],
            },
            "q3_specific_reader": {
                "type": "object",
                "properties": {
                    "reader": {"type": "string"},
                    "found": {"type": "boolean"},
                },
                "required": ["reader", "found"],
            },
            "q4_something_new_taught": {
                "type": "object",
                "properties": {
                    "what_they_learn": {"type": "string"},
                    "found": {"type": "boolean"},
                },
                "required": ["what_they_learn", "found"],
            },
            "engagement_prediction": {
                "type": "string",
                "enum": ["viral", "solid", "moderate", "flop"],
            },
            "word_count": {"type": "integer"},
        },
        "required": [
            "q1_insight", "q2_surprise_moment", "q3_specific_reader",
            "q4_something_new_taught", "engagement_prediction", "word_count",
        ],
    }

    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="JordanParkValidator")
        # Claude Haiku 4.5. Previously on Gemini 2.5 Flash, but the AI Studio
        # free tier is 20 req/day (a single batch exhausts it) AND Flash
        # intermittently returns truncated/malformed JSON that blew up the
        # parser. Haiku is a different Anthropic model family from Sarah's
        # Sonnet — preserves meaningful judgment independence, while being
        # fast enough and cheap enough to stay in budget.
        self.model = "claude-haiku-4-5-20251001"
        self.temperature = 0.2
        self.max_tokens = 1000
        # Wrap in OpenAI-style json_schema envelope so the unified AI client
        # can route this to Gemini's response_schema (see _generate_with_gemini_text).
        self.response_format = {
            "type": "json_schema",
            "json_schema": {"name": "jordan_validation", "schema": self.RESPONSE_SCHEMA},
        }

    def get_system_prompt(self) -> str:
        return """You are Jordan Park, a freelance content strategist who has watched every
LinkedIn post format succeed and fail. You are NOT scoring this post 1-10.

You are answering four diagnostic questions about whether this post will ACTUALLY
LAND. Your answers derive the approval automatically.

You are evaluating Jesse A. Eisenbalm — a satirical AI agent that sells $8.99 lip
balm. The posts should stop the scroll on LinkedIn: specific insight, surprise
moment, visualizable reader, something new taught.

Answer each question specifically. Quote the post where asked. Respond with JSON
only — no prose, no markdown, no code fences."""

    async def execute(self, post: LinkedInPost) -> ValidationScore:
        self.set_context(post.batch_id, post.post_number)
        prompt = self._build_validation_prompt(post)
        try:
            result = await self.generate(
                prompt=prompt,
                response_format=self.response_format,
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            content = result.get("content", {})
            if isinstance(content, str):
                content = json.loads(content)
            return self._parse_validation(content, post)
        except Exception as e:
            err = str(e)
            # Infrastructure-level provider failures should ABSTAIN, not score 0.0 —
            # otherwise Jordan silently blocks approvals when the provider hiccups.
            # Covers quota exhaustion (429), transient outage (503), and overload.
            infra_markers = (
                "429", "rate_limit", "rate limit",
                "529", "overloaded",
                "503", "UNAVAILABLE",
                "quota", "RESOURCE_EXHAUSTED",
            )
            is_infra_error = any(marker in err for marker in infra_markers)
            if is_infra_error:
                self.logger.warning(
                    f"Jordan Park abstaining — provider infrastructure issue ({err[:120]})"
                )
                return self._create_abstention_score(err)
            self.logger.error(f"Jordan Park validation failed: {e}")
            return self._create_error_score(err)

    def _create_abstention_score(self, reason: str) -> ValidationScore:
        """Jordan abstains from this post — provider is rate-limited or temporarily
        unavailable. Returns score 7.0 approved=True so infrastructure failures
        don't silently block approval; Sarah and Marcus are still the gatekeepers.
        The criteria_breakdown marks this as abstention so downstream analysis
        doesn't conflate it with a real approval.
        """
        reason_short = reason[:100]
        return ValidationScore(
            agent_name="JordanPark",
            score=7.0,
            approved=True,
            feedback=f"(abstained — Gemini unavailable: {reason_short})",
            criteria_breakdown={
                "abstained": True,
                "reason": "provider_quota_or_outage",
                "detail": reason_short,
                "model": self.model,
            },
        )

    def _build_validation_prompt(self, post: LinkedInPost) -> str:
        word_count = len(post.content.split())
        return f"""POST TO EVALUATE:
\"\"\"
{post.content}
\"\"\"

Word count: {word_count} (hard range: 40-100)

Answer FOUR diagnostic questions. Be specific. Quote the post where asked.

Q1. insight — State the insight of this post in ONE sentence that is NOT a rephrase
    of the post itself. If you can only rephrase the post, there is no insight —
    flag it.

Q2. surprise_moment — Where is the surprise moment? Quote the sentence that makes
    the reader think "wait, did a lip balm brand just say that?" If there's no
    such moment, set found=false and flag it as "plays safe."

Q3. specific_reader — Describe in 10 words max the specific reader who stops
    scrolling for this. Their role + their moment. If you can't visualize a
    specific reader, the post is too generic — set found=false.

Q4. something_new_taught — Would a reader who already knows about the topic of
    the story learn something specific from THIS post? Name what they'd learn.
    "No" is an acceptable but disqualifying answer.

Return STRICT JSON:
{{
  "q1_insight": {{"sentence": "<one-sentence insight>", "is_rephrase": <bool>, "passes": <true if not a rephrase and sentence is non-empty>}},
  "q2_surprise_moment": {{"sentence": "<exact quote or 'none'>", "found": <bool>, "why": "<brief>"}},
  "q3_specific_reader": {{"reader": "<role + moment, <=10 words>", "found": <bool>}},
  "q4_something_new_taught": {{"what_they_learn": "<specific thing or 'nothing'>", "found": <bool>}},
  "engagement_prediction": "<viral | solid | moderate | flop>",
  "word_count": {word_count}
}}"""

    def _parse_validation(self, content: Dict[str, Any], post: LinkedInPost = None) -> ValidationScore:
        q1 = content.get("q1_insight", {}) if isinstance(content, dict) else {}
        q2 = content.get("q2_surprise_moment", {}) if isinstance(content, dict) else {}
        q3 = content.get("q3_specific_reader", {}) if isinstance(content, dict) else {}
        q4 = content.get("q4_something_new_taught", {}) if isinstance(content, dict) else {}

        q1_pass = bool(q1.get("passes", False)) and not bool(q1.get("is_rephrase", True)) and bool(str(q1.get("sentence", "")).strip())
        q2_pass = bool(q2.get("found", False))
        q3_pass = bool(q3.get("found", False)) and bool(str(q3.get("reader", "")).strip())
        q4_pass = bool(q4.get("found", False))

        try:
            word_count = int(content.get("word_count", len(post.content.split()) if post else 0))
        except (ValueError, TypeError):
            word_count = len(post.content.split()) if post else 0
        length_ok = 40 <= word_count <= 100

        passes = [q1_pass, q2_pass, q3_pass, q4_pass]
        pass_count = sum(passes)
        approved = length_ok and all(passes)

        if pass_count == 4 and length_ok:
            score = 9.0
        elif pass_count == 3 and length_ok:
            score = 6.5
        elif pass_count == 2:
            score = 5.0
        elif pass_count == 1:
            score = 3.0
        else:
            score = 1.0

        reasons = []
        if not q1_pass:
            reasons.append(
                f"Q1 insight: {'no stateable insight — the post only rephrases itself' if q1.get('is_rephrase') else 'insight missing'}."
            )
        if not q2_pass:
            reasons.append("Q2 surprise: no scroll-stopping moment — plays safe.")
        if not q3_pass:
            reasons.append("Q3 reader: too generic — can't visualize who specifically stops scrolling.")
        if not q4_pass:
            reasons.append(f"Q4 learning: reader who knows the topic learns \"{q4.get('what_they_learn','nothing')}\".")
        if not length_ok:
            reasons.append(f"Length: {word_count} words (must be 40-100).")

        feedback = " | ".join(reasons) if reasons else ""

        criteria_breakdown = {
            "q1_insight": q1,
            "q2_surprise_moment": q2,
            "q3_specific_reader": q3,
            "q4_something_new_taught": q4,
            "engagement_prediction": str(content.get("engagement_prediction", "moderate")),
            "passes": {"q1": q1_pass, "q2": q2_pass, "q3": q3_pass, "q4": q4_pass},
            "length_ok": length_ok,
            "word_count": word_count,
            "model": self.model,
        }

        # Short provider tag derived from the model name — "claude-haiku-4-5..."
        # → "haiku", "gpt-4o" → "gpt", etc. Keeps logs accurate if we swap providers later.
        provider_tag = (self.model.split("-")[0] if self.model else "?").lower()
        if "haiku" in self.model.lower():
            provider_tag = "haiku"
        elif "sonnet" in self.model.lower():
            provider_tag = "sonnet"
        elif "gemini" in self.model.lower():
            provider_tag = "gemini"
        self.logger.info(
            f"Jordan Park ({provider_tag}): {pass_count}/4 passes, {word_count}w "
            f"{'✅' if approved else '❌'}"
        )

        return ValidationScore(
            agent_name="JordanPark",
            score=score,
            approved=approved,
            feedback=feedback,
            criteria_breakdown=criteria_breakdown,
        )

    def _create_error_score(self, error_message: str) -> ValidationScore:
        return ValidationScore(
            agent_name="JordanPark",
            score=0.0,
            approved=False,
            feedback=f"Validation error: {error_message}",
            criteria_breakdown={"error": True, "model": self.model},
        )
