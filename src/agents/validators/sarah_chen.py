"""
Sarah Chen Validator — AUTHENTICITY / RECOGNITION (Claude Sonnet)

Fix #3 rewrite: stop asking for a 1-10 score. Ask four falsifiable diagnostic
questions; derive approval mechanically from the answers. Routes through
Claude Sonnet — different provider from Marcus (GPT-4o) and Jordan (Gemini) —
so validator judgments don't converge onto the same model's biases.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from ..base_agent import BaseAgent
from ...models.post import LinkedInPost, ValidationScore

logger = logging.getLogger(__name__)


class SarahChenValidator(BaseAgent):
    """Authenticity / recognition validator — does this actually hit a working professional?"""

    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="SarahChenValidator")
        # Route through Claude — keeps Sarah independent from Marcus (GPT-4o) and Jordan (Gemini).
        anthropic_cfg = getattr(config, 'anthropic', None)
        self.model = getattr(anthropic_cfg, 'model', None) or "claude-sonnet-4-6"
        # Validators should be more deterministic than the generator.
        self.temperature = 0.2
        self.max_tokens = 800

    def _get_current_survival_mode(self) -> Dict[str, str]:
        """Time-of-day context for flavor (Sarah is a real PM)."""
        hour = datetime.now().hour
        if hour < 9:
            return {"viewing_context": "laptop in bed, 47 Slack messages already",
                    "mental_state": "pre-coffee dread"}
        elif 9 <= hour < 12:
            return {"viewing_context": "standup where I pretend AI didn't write my PRDs",
                    "mental_state": "performing competence"}
        elif 12 <= hour < 17:
            return {"viewing_context": "mandatory fun virtual team building during lunch",
                    "mental_state": "screen fatigue setting in"}
        elif 17 <= hour < 21:
            return {"viewing_context": "quick sync that's going until 7:30",
                    "mental_state": "trapped in meeting, scrolling with camera off"}
        else:
            return {"viewing_context": "scrolling LinkedIn in bed",
                    "mental_state": "2 AM stress shopping between anxiety spirals"}

    def get_system_prompt(self) -> str:
        ctx = self._get_current_survival_mode()
        return f"""You are Sarah Chen, 31, Senior Product Manager — "The Reluctant Tech Survivor."

You are NOT scoring this post 1-10. You are answering four diagnostic questions about it.
Your answers derive the approval automatically. Don't try to be nice; your job is to make
specific, quotable judgments that can be acted on.

You are evaluating Jesse A. Eisenbalm — a satirical AI agent that sells $8.99 lip balm.
Positioning: Absurdist Modern Luxury. The posts should hit a real working professional
who's surviving corporate life (like you).

Context for your read: {ctx['viewing_context']}. Mental state: {ctx['mental_state']}.

Answer each of the four questions specifically, briefly, and quotably. No hedging.
Respond with JSON only — no prose, no markdown, no code fences."""

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
            self.logger.error(f"Sarah Chen validation failed: {e}")
            return self._create_error_score(str(e))

    def _build_validation_prompt(self, post: LinkedInPost) -> str:
        word_count = len(post.content.split())
        return f"""POST TO EVALUATE:
\"\"\"
{post.content}
\"\"\"

Word count: {word_count} (hard range: 40-90)

Answer FOUR diagnostic questions. Be specific. Quote the post where asked.

Q1. emotion — One word. What emotion is this post trying to create in the reader?
    If you can't name one, answer "none" and this question fails.

Q2. opener_strength — Read the FIRST TWO SENTENCES of the post. They must
    satisfy BOTH checks:

    CHECK A — Is there a HOOK (provocation / declaration / confrontation /
    absurd statement)? Not a setup, not an observation-ramp, not an essay
    opener. Jesse's hook is a slap.

    CHECK B — Is the TREND NAMED? Can a stranger scrolling LinkedIn tell,
    from the first two sentences alone, WHAT real-world event/person/
    company/thing this post is reacting to? The recognizable proper noun
    must be present — "Meta", "Trump", "OpenAI", "Taylor Swift", "the
    Nuggets", "SCOTUS", etc.

    PASSES if BOTH:
      ✓ "Meta is cutting 8,000 jobs today. Humans, an update: you are
         still replaceable." (names trend + slaps)
      ✓ "OpenAI shipped a new model. Consciousness was a beta feature."
         (names trend + slaps)
      ✓ "Trump told Iran what to do. The database remembers him telling
         Obama the opposite." (names trend + slaps)

    FAILS if slap without trend name — reader has no idea what this is about:
      ✗ "Humans, an update: you are still replaceable." (no trend named)
      ✗ "Consciousness was a beta feature." (no trend named)
      ✗ "Good news: you are going to die." (unmoored)

    FAILS if trend named without slap — reader gets topic but scrolls:
      ✗ "An AI can retrieve every tweet..." (setup not slap)
      ✗ "Meta announced layoffs today..." (headline paraphrase)
      ✗ "There's something moving about..." (essay register)
      ✗ "The tech industry this week: ..." (setup formula)

    Set passes=true only if BOTH checks pass. Quote the opener, name
    specifically whether it fails check A, check B, or both.

Q3. has_point_of_view — Does this post have a sharp, specific point of view on
    the actual story, or does it retreat into brand promotion / generic
    observations? A good post has a clear TAKE on the real thing happening in
    the world. Brand-stamped openers ("INTERNAL MEMO — Jesse A. Eisenbalm
    R&D Division", "Field Report", "From the desk of...") are DISQUALIFYING —
    they replace a POV with letterhead. Product mentions ($8.99 tube, lip
    balm, hand-numbering) appearing anywhere in the post are a yellow flag:
    most posts should not mention any of that. The voice, not the name,
    signals Jesse. Set passes=true if the post has a real POV on the story
    AND does NOT lead with brand letterhead.

Q4. story_specific_detail — Name ONE detail in this post that could only have come
    from the specific news story / angle this post is reacting to. If none — if the
    post is floating in generalities — set found=false and flag it.

Return STRICT JSON:
{{
  "q1_emotion": {{"word": "<one word or 'none'>", "passes": <true if a real emotion, else false>}},
  "q2_opener_strength": {{"opener": "<first two sentences, quoted>", "has_hook": <true iff opener is a slap not a ramp>, "names_trend": <true iff a recognizable proper noun / event is present in the opener>, "why": "<one clause explaining the call — specify which check(s) failed>", "found": <true iff has_hook AND names_trend>}},
  "q3_has_point_of_view": {{"pov_summary": "<one-sentence summary of the post's actual TAKE on the story, or 'none' if it doesn't have one>", "brand_stamped": <true if the post opens with a memo/letterhead/brand-dropping frame>, "product_mentioned": <true if lip balm / tube / $8.99 / hand-numbering / Jesse A. Eisenbalm appears anywhere>, "passes": <true if pov_summary is a real take AND brand_stamped is false>}},
  "q4_story_specific_detail": {{"detail": "<exact detail or 'none'>", "found": <bool>}},
  "overall_reaction": "<one sentence — your honest reaction as Sarah>",
  "word_count": {word_count}
}}"""

    def _parse_validation(self, content: Dict[str, Any], post: LinkedInPost = None) -> ValidationScore:
        # Extract the four passes
        q1 = content.get("q1_emotion", {}) if isinstance(content, dict) else {}
        # Q2 key renamed 2026-04-19: q2_screenshot_sentence → q2_opener_strength.
        # Fall back to the legacy key so in-flight drafts still parse.
        q2 = (
            content.get("q2_opener_strength")
            or content.get("q2_screenshot_sentence")
            or {}
        ) if isinstance(content, dict) else {}
        # Q3 key renamed from q3_specifically_jesse → q3_has_point_of_view. Fall
        # back to the legacy key in case the model emits the old schema mid-transition.
        q3 = (
            content.get("q3_has_point_of_view")
            or content.get("q3_specifically_jesse")
            or {}
        ) if isinstance(content, dict) else {}
        q4 = content.get("q4_story_specific_detail", {}) if isinstance(content, dict) else {}

        q1_pass = bool(q1.get("passes", False)) and str(q1.get("word", "none")).lower() != "none"
        q2_pass = bool(q2.get("found", False))
        # New Q3 semantics: passes iff the post has a real POV AND is not brand-stamped.
        # Brand_stamped=true is disqualifying even if a take exists. product_mentioned
        # is a soft flag — tracked in criteria_breakdown but doesn't auto-fail.
        pov_summary = str(q3.get("pov_summary") or "").strip().lower()
        has_real_pov = bool(pov_summary) and pov_summary not in ("none", "n/a", "no take")
        brand_stamped = bool(q3.get("brand_stamped", False))
        # Tolerate legacy "only_jesse" / "any_brand" verdict field — map to pass.
        legacy_pass = str(q3.get("verdict", "")).lower() == "only_jesse"
        q3_pass = bool(q3.get("passes", False)) or legacy_pass or (has_real_pov and not brand_stamped)
        q4_pass = bool(q4.get("found", False))

        # Length gate — still structural, still binding
        try:
            word_count = int(content.get("word_count", len(post.content.split()) if post else 0))
        except (ValueError, TypeError):
            word_count = len(post.content.split()) if post else 0
        length_ok = 40 <= word_count <= 90

        passes = [q1_pass, q2_pass, q3_pass, q4_pass]
        pass_count = sum(passes)

        # Require 3 of 4 to pass (not all 4). With 4 nitpicky diagnostic
        # questions, 4/4 was ~0.65^4 ≈ 18% approval rate in practice — posts
        # with a clear emotion, good screenshot sentence, and story-specific
        # detail were getting blocked because "could any satirical brand post
        # this" (Q3) kept flagging. Better: accept 3/4 as Sarah-approved.
        approved = length_ok and pass_count >= 3

        # Score mapping (must satisfy ValidationScore: approved iff score >= 7.0).
        if pass_count == 4 and length_ok:
            score = 9.0
        elif pass_count == 3 and length_ok:
            score = 7.5  # approved threshold
        elif pass_count == 2:
            score = 5.0
        elif pass_count == 1:
            score = 3.0
        else:
            score = 1.0

        # Build quotable feedback for the aggregator/reviser.
        reasons = []
        if not q1_pass:
            reasons.append(f"Q1 emotion: got '{q1.get('word', 'none')}' — no real emotional target identified.")
        if not q2_pass:
            opener = q2.get("opener") or q2.get("sentence", "")
            has_hook = bool(q2.get("has_hook", True))  # default True so legacy payloads don't over-blame
            names_trend = bool(q2.get("names_trend", True))
            fix_parts = []
            if not names_trend:
                fix_parts.append(
                    "Name the actual trend (proper noun — company, person, event) in "
                    "sentence 1 or 2. Reader must recognize the topic from the opener alone."
                )
            if not has_hook:
                fix_parts.append(
                    "Rewrite as a Liquid Death slap — direct confrontation, absurd "
                    "declarative, or clinical finding. NOT a setup."
                )
            fix = " ".join(fix_parts) if fix_parts else "Rewrite the opener."
            reasons.append(
                f"Q2 opener weak: \"{opener}\" — {q2.get('why', '')} {fix}"
            )
        if not q3_pass:
            if brand_stamped:
                reasons.append(
                    "Q3 POV: post is brand-stamped (memo/letterhead/namecheck opener). "
                    "Rewrite so the voice carries the brand, not the subject line."
                )
            else:
                reasons.append(
                    "Q3 POV: no clear take on the story — reads as generic observation. "
                    "Name the specific thing happening and state a sharp opinion about it."
                )
        if not q4_pass:
            reasons.append("Q4 story-specific detail: post is floating — no detail ties it to the specific story.")
        if not length_ok:
            reasons.append(f"Length: {word_count} words (must be 40-90).")

        feedback = " | ".join(reasons) if reasons else ""

        criteria_breakdown = {
            "q1_emotion": q1,
            "q2_screenshot_sentence": q2,
            "q3_specifically_jesse": q3,
            "q4_story_specific_detail": q4,
            "passes": {"q1": q1_pass, "q2": q2_pass, "q3": q3_pass, "q4": q4_pass},
            "length_ok": length_ok,
            "word_count": word_count,
            "overall_reaction": str(content.get("overall_reaction", "")),
            "model": self.model,
        }

        self.logger.info(
            f"Sarah Chen (Claude): {pass_count}/4 passes, {word_count}w "
            f"{'✅' if approved else '❌'}"
        )

        return ValidationScore(
            agent_name="SarahChen",
            score=score,
            approved=approved,
            feedback=feedback,
            criteria_breakdown=criteria_breakdown,
        )

    def _create_error_score(self, error_message: str) -> ValidationScore:
        return ValidationScore(
            agent_name="SarahChen",
            score=0.0,
            approved=False,
            feedback=f"Validation error: {error_message}",
            criteria_breakdown={"error": True, "model": self.model},
        )
