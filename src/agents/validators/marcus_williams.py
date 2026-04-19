"""
Marcus Williams Validator — CRAFT (GPT-4o)

Fix #3 rewrite: stop asking for a 1-10 score. Ask four falsifiable diagnostic
questions about craft — weak sentences, broken metaphors, LLM tells, template
crutches — and derive approval mechanically. Routes through GPT-4o (stronger
at structural critique under rubric than 4o-mini).
"""

import json
import logging
from typing import Dict, Any
from ..base_agent import BaseAgent
from ...models.post import LinkedInPost, ValidationScore

logger = logging.getLogger(__name__)


class MarcusWilliamsValidator(BaseAgent):
    """Craft validator — quotes specific failures (broken metaphors, LLM tells, template crutches)."""

    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="MarcusWilliamsValidator")
        # GPT-4o (not mini) — stronger at structural critique.
        self.model = "gpt-4o"
        self.temperature = 0.2
        self.max_tokens = 900

    def get_system_prompt(self) -> str:
        return """You are Marcus Williams, a Creative Director who has seen every copywriting crutch ever invented.

You are NOT scoring this post 1-10. You are answering four diagnostic questions about its CRAFT.
Quote specific failures. Don't generalize. Your job is to make the revision actionable.

You are evaluating Jesse A. Eisenbalm — a satirical AI agent that sells $8.99 lip balm.
The double satire: AI superiority meets human lips. The dry-comedy engine: clinical
diagnostic voice applied to mundane culture. Em dashes are signature.

Answer each question specifically and quotably. Respond with JSON only — no prose,
no markdown, no code fences."""

    async def execute(self, post: LinkedInPost) -> ValidationScore:
        self.set_context(post.batch_id, post.post_number)
        prompt = self._build_validation_prompt(post)
        try:
            result = await self.generate(
                prompt=prompt,
                response_format="json",
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            content = result.get("content", {})
            if isinstance(content, str):
                content = json.loads(content)
            return self._parse_validation(content, post)
        except Exception as e:
            self.logger.error(f"Marcus Williams validation failed: {e}")
            return self._create_error_score(str(e))

    def _build_validation_prompt(self, post: LinkedInPost) -> str:
        word_count = len(post.content.split())
        return f"""POST TO EVALUATE:
\"\"\"
{post.content}
\"\"\"

Word count: {word_count} (hard range: 60-150)

Answer FOUR diagnostic questions. Quote exact phrases from the post. No hedging.

Q1. weakest_sentence — Quote the single weakest sentence in the post and explain
    in ONE clause why it's weak (too generic / dead metaphor / hedged / committee voice / etc).

Q2. metaphors — List EVERY metaphor or analogy in the post. For each, state the
    specific property being compared. Flag any where both sides don't actually share
    that property. Example of a broken metaphor: "glacier of red tape" — balm does
    not affect glaciers; the property being compared doesn't hold.

Q3. essay_drift_anywhere — Does this post DRIFT OUT of Liquid Death register
    AT ANY POINT — opener, middle, or close? This is the #1 failure mode.
    Most drafts open strong, then soften into reflective-essay mode for the
    middle paragraphs or aphoristic-closer mode at the end. Liquid Death is
    punchy-throughout. Not punchy-then-thoughtful.

    SCAN THE WHOLE POST. Flag any instance of:

    A. REFLECTIVE / WISTFUL / ESSAYISTIC language (anywhere):
       ✗ "There's something X about..." / "It turns out that..."
       ✗ "The specific weight of..." / "the specific way X [verb]s"
       ✗ "There is no model for that" / "no training data for X"
       ✗ "Here's what struck/moved/surprised me..."
       ✗ Meditative/melancholic/reverent tone toward any subject
       ✗ "Let's sit with this" / "what this really means is"

    B. APHORISTIC CLOSERS PRETENDING TO BE PROFOUND:
       ✗ "The question was never X. It was always Y."
       ✗ "Some things remain unoptimized. This appears to be intentional."
       ✗ "It always does."
       ✗ "The data knows what happened. Only the body knows what it cost."
       ✗ "X was also [verb] before anyone asked."
       Any "wise benediction" style ending where the post tapers off on
       a note of supposed profundity. Jesse ends on a slap, not a sigh.

    C. LONG INTROSPECTIVE SENTENCES (20+ words of reflection):
       Liquid Death sentences average 6-10 words. Anything over 20 words
       of meditative prose is essay register — flag the sentence.

    D. CLASSIC LLM TELLS:
       ✗ "In a world where...", "It's not just X, it's Y"
       ✗ Stacked parallel structure used for poetic effect (not for
         punch — parallel structure is fine if it's aggressive)

    PASS only if EVERY sentence from opener to closer stays in dry clinical
    absurdist Liquid Death register — short, punchy, declarative, absurd,
    confrontational. No softening. No reflection. No wise endings.

    If every sentence stays punchy, set has_tell=false and justify.

Q4. template_crutch — Does the post lean on a template opener ("Diagnosed:",
    "Prescription:", "Clinical Assessment:", "SUBJECT EXHIBITS:")? If yes: is the
    template genuinely EARNED by the angle (the post IS a clinical diagnosis of a
    real thing), or is it lazy default? If lazy, propose ONE non-template opener
    that preserves the Jesse voice.

Return STRICT JSON:
{{
  "q1_weakest_sentence": {{"sentence": "<exact quote>", "why": "<one clause>"}},
  "q2_metaphors": {{
    "metaphors": [
      {{"quote": "<exact>", "property": "<what's compared>", "holds": <bool>, "note": "<brief>"}}
    ],
    "any_broken": <bool>
  }},
  "q3_essay_drift_anywhere": {{"tell": "<exact phrase or 'nowhere'>", "location": "<'opener' | 'middle' | 'closer' | 'nowhere'>", "mode": "<'reflective' | 'aphoristic_closer' | 'long_introspective' | 'llm_tell' | 'nowhere'>", "justification": "<one sentence>", "has_tell": <bool>}},
  "q4_template_crutch": {{"has_crutch": <bool>, "crutch_opener": "<quote or 'none'>", "earned": <bool>, "alternative_opener": "<proposed opener or 'n/a'>"}},
  "word_count": {word_count}
}}"""

    def _parse_validation(self, content: Dict[str, Any], post: LinkedInPost = None) -> ValidationScore:
        q1 = content.get("q1_weakest_sentence", {}) if isinstance(content, dict) else {}
        q2 = content.get("q2_metaphors", {}) if isinstance(content, dict) else {}
        # Q3 key evolved: q3_llm_tells → q3_earnest_or_llm_tell →
        # q3_essay_drift_anywhere. Check newest first, fall back for legacy.
        q3 = (
            content.get("q3_essay_drift_anywhere")
            or content.get("q3_earnest_or_llm_tell")
            or content.get("q3_llm_tells")
            or {}
        ) if isinstance(content, dict) else {}
        q4 = content.get("q4_template_crutch", {}) if isinstance(content, dict) else {}

        # Q1 is informational — every post has a weakest sentence. Use presence of a quote as pass.
        q1_pass = bool(str(q1.get("sentence", "")).strip())
        # Q2 fails if any metaphor's property doesn't hold.
        q2_pass = not bool(q2.get("any_broken", False))
        # Q3 fails if an LLM tell is present.
        q3_pass = not bool(q3.get("has_tell", False))
        # Q4 passes if no crutch OR if crutch is genuinely earned.
        has_crutch = bool(q4.get("has_crutch", False))
        crutch_earned = bool(q4.get("earned", False))
        q4_pass = (not has_crutch) or crutch_earned

        try:
            word_count = int(content.get("word_count", len(post.content.split()) if post else 0))
        except (ValueError, TypeError):
            word_count = len(post.content.split()) if post else 0
        length_ok = 60 <= word_count <= 150

        # Marcus's approval: require 2 of 3 core dimensions to pass (not all 3).
        # In production, Q3 (LLM tells) was flagging nearly every post because
        # the model inevitably has some parallelism or rhythm Marcus could read
        # as an LLM signature. 3/3 required perfection on subjective judgments;
        # 2/3 allows one soft-flag while still catching posts that are broken
        # on multiple dimensions. Q1 is feedback-only.
        core_passes = [q2_pass, q3_pass, q4_pass]
        pass_count = sum(core_passes)
        approved = length_ok and pass_count >= 2

        # Score mapping — must satisfy ValidationScore (approved iff >=7.0)
        if pass_count == 3 and length_ok:
            score = 9.0
        elif pass_count == 2 and length_ok:
            score = 7.5  # approved threshold
        elif pass_count == 2:
            score = 5.5
        elif pass_count == 1:
            score = 4.0
        else:
            score = 2.0

        reasons = []
        # Always quote Q1 weakest sentence — useful for revision even on approvals
        if q1.get("sentence"):
            reasons.append(f"Weakest line: \"{q1.get('sentence')}\" — {q1.get('why', '')}")
        if not q2_pass:
            broken = [m for m in q2.get("metaphors", []) if not m.get("holds", True)]
            for m in broken[:2]:
                reasons.append(
                    f"Broken metaphor: \"{m.get('quote','')}\" — property \"{m.get('property','')}\" doesn't hold. {m.get('note','')}"
                )
        if not q3_pass:
            mode = str(q3.get("mode", "")).lower()
            location = str(q3.get("location", "")).lower()
            tell = q3.get("tell", "")
            just = q3.get("justification", "")

            if mode == "aphoristic_closer" or location == "closer":
                reasons.append(
                    f"Aphoristic closer (essay-drift at the end): \"{tell}\" — {just} "
                    f"Liquid Death doesn't do wise benedictions. End on a short slap: "
                    f"'Nothing personal. Everything procedural.' / 'HR sent a LinkedIn "
                    f"post.' / 'Your lips are on their own.' / 'Plan accordingly.'"
                )
            elif mode == "long_introspective":
                reasons.append(
                    f"Long introspective sentence (20+ words, meditative): \"{tell}\" — {just} "
                    f"Break it into punchy short declaratives. Liquid Death sentences "
                    f"average 6-10 words, not 25."
                )
            elif mode == "reflective" or mode == "earnest_essay":
                reasons.append(
                    f"Reflective/essay drift mid-post: \"{tell}\" ({location or 'middle'}) — "
                    f"{just} Rewrite in dry clinical absurdist observer mode. Every sentence "
                    f"must stay punchy — not just the opener."
                )
            else:
                reasons.append(
                    f"Voice drift: \"{tell}\" — {just} Stay in Liquid Death register "
                    f"from sentence 1 to the last period."
                )
        if not q4_pass:
            reasons.append(
                f"Template crutch \"{q4.get('crutch_opener','')}\" not earned. Try: {q4.get('alternative_opener','')}"
            )
        if not length_ok:
            reasons.append(f"Length: {word_count} words (must be 60-150).")

        feedback = " | ".join(reasons) if reasons else ""

        criteria_breakdown = {
            "q1_weakest_sentence": q1,
            "q2_metaphors": q2,
            "q3_llm_tells": q3,
            "q4_template_crutch": q4,
            "passes": {"q2": q2_pass, "q3": q3_pass, "q4": q4_pass, "length": length_ok},
            "word_count": word_count,
            "model": self.model,
        }

        self.logger.info(
            f"Marcus Williams (GPT-4o): {pass_count}/3 core passes, {word_count}w "
            f"{'✅' if approved else '❌'}"
        )

        return ValidationScore(
            agent_name="MarcusWilliams",
            score=score,
            approved=approved,
            feedback=feedback,
            criteria_breakdown=criteria_breakdown,
        )

    def _create_error_score(self, error_message: str) -> ValidationScore:
        return ValidationScore(
            agent_name="MarcusWilliams",
            score=0.0,
            approved=False,
            feedback=f"Validation error: {error_message}",
            criteria_breakdown={"error": True, "model": self.model},
        )
