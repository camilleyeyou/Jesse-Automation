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
        # Phase I (2026-04-21): gpt-4o → gpt-5.1. OpenAI reports ~45% fewer
        # factual errors vs 4o (non-thinking mode) — directly relevant to
        # Marcus's job (quoting weak sentences, flagging broken metaphors,
        # grammar check). Max tokens lowered 900→700 to pre-empt GPT-5.1's
        # known verbosity tendency on critique output.
        self.model = "gpt-5.1"
        self.temperature = 0.2
        self.max_tokens = 700

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

Word count: {word_count} (hard range: 40-90)

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

Q5. grammar_clean — Is the post free of grammatical errors, typos, awkward
    phrasing, dangling clauses, run-on sentences, subject-verb disagreements,
    wrong word choice, or malformed punctuation? This is a HARD GATE — any
    error = fail.

    FLAG (is_clean=false) if ANY of:
      • Typos (misspellings, missing letters, transposed letters)
      • Subject-verb disagreement ("the data show" vs "the data shows" — either
        is fine, pick one; but "the humans is" is wrong)
      • Dangling modifiers / unclear pronoun references
      • Run-on sentences with comma splices ("The algorithm saw it, the human
        didn't notice, everyone moved on")
      • Malformed punctuation (mismatched em dashes, orphaned commas, double
        periods, etc.)
      • Sentence fragments that don't work as stylistic choices (occasional
        fragment for punch is FINE; accidental fragments are NOT)
      • Wrong word choice ("it's" vs "its", "affect" vs "effect", etc.)
      • Tense shifts mid-sentence for no reason

    DO NOT FLAG:
      • Deliberate fragments for punch ("Nothing personal. Everything procedural.")
      • Stylistic sentence-initial conjunctions ("And then nothing happened.")
      • Intentional ambiguity or short aggressive declaratives
      • Em dashes (those are Jesse signature — never flag)

    Quote the specific error and explain in one clause. If the post is clean,
    set is_clean=true and quote nothing.

Q6. emotional_contact_checksum — SOFT SIGNAL (does NOT block approval).
    This is NOT a taste judgment. This is a concrete checksum for the
    specificity rule (Ogilvy/Onion/Berger): the reader only feels something
    when the post names ONE photographable object OR ONE private human hour.

    You are answering two yes/no questions:

    (A) photographable_noun — Does the post name at least ONE concrete
        object that could physically be photographed?
          ✓ YES: "a thermostat", "a phone on the counter", "a lanyard",
                 "a Post-it note", "the paper he handwrote it on", "a yellow
                 legal pad", "her pager"
          ✗ NO:  "the market", "the economy", "innovation", "progress",
                 "the narrative", "stakeholders", "the industry" — these
                 are concepts, not objects. A camera can't catch them.

    (B) private_human_hour — Does the post name at least ONE specific
        human hour, place, or private state?
          ✓ YES: "3am", "2:47am", "the parking lot at closing",
                 "Thanksgiving dinner", "the bathroom at work", "alone
                 with no good answers", "refreshing the app on mute"
          ✗ NO:  "the workplace", "the media cycle", "the news", "the
                 quarterly earnings call" — these are institutional
                 abstractions, not private human moments.

    PASS (has_checksum=true) if EITHER (A) or (B) is satisfied.
    FLAG (has_checksum=false) only if the post has NEITHER a photographable
    object NOR a private human hour.

    If flagged, quote the closest candidate and what a concrete version
    would look like (e.g., "replace 'the market reacted' with 'a retiree
    checking the brokerage app at 6am'").

    This is a mechanical check, not a vibe check. Either the concrete noun
    is present or it isn't. Do not soften it — either the post has it or
    it doesn't.

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
  "q5_grammar_clean": {{"is_clean": <bool>, "error_quote": "<exact phrase if error, else ''>", "error_type": "<typo|agreement|dangling|run_on|punctuation|fragment|word_choice|tense|nowhere>", "fix_hint": "<one clause suggesting the fix>"}},
  "q6_emotional_contact": {{"has_checksum": <bool>, "photographable_noun": "<exact noun from post, or '' if none>", "private_human_hour": "<exact phrase from post, or '' if none>", "nearest_abstraction": "<closest-to-concrete abstract phrase from post if flagged, else ''>", "concrete_fix_hint": "<one clause — what a concrete replacement would look like, if flagged>"}},
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
        q5 = content.get("q5_grammar_clean", {}) if isinstance(content, dict) else {}
        q6 = content.get("q6_emotional_contact", {}) if isinstance(content, dict) else {}

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
        # Q5 (grammar) is a HARD GATE — any actual error blocks the post.
        # Default to True when the field is absent so in-flight drafts from
        # older prompts don't get over-blamed.
        q5_pass = bool(q5.get("is_clean", True))
        # Q6 (emotional-contact checksum) is a SOFT signal — does NOT block
        # approval. Phase F (2026-04-21): rewritten from a taste judgment
        # to an empirical checksum. The post passes Q6 if it names either
        # a photographable object OR a private human hour (specificity
        # rule from Ogilvy/Onion/Berger). Default True so legacy drafts
        # without the field don't get blamed.
        q6_has_contact = bool(
            q6.get("has_checksum", q6.get("has_contact", True))
        )

        try:
            word_count = int(content.get("word_count", len(post.content.split()) if post else 0))
        except (ValueError, TypeError):
            word_count = len(post.content.split()) if post else 0
        length_ok = 40 <= word_count <= 90

        # Deterministic sentence-length hard gate (2026-04-19 polish).
        # Marcus Q3 flags "long introspective sentences" as a soft signal
        # but the LLM keeps deciding that 25+ word declaratives are fine.
        # User explicitly wants Liquid Death punch — any sentence over 25
        # words blocks approval regardless of Marcus's other judgments.
        long_sentence_blocker = None
        if post and post.content:
            import re as _re
            # Split on sentence-ending punctuation; collapse newlines first
            flat = _re.sub(r"\s+", " ", post.content).strip()
            sentences = [s.strip() for s in _re.split(r"(?<=[.!?])\s+", flat) if s.strip()]
            for s in sentences:
                wc = len(s.split())
                if wc > 25:
                    long_sentence_blocker = (s[:120], wc)
                    break
        sentence_length_ok = long_sentence_blocker is None

        # Marcus's approval: require 2 of 3 core dimensions (q2, q3, q4) to pass
        # AND grammar clean (Q5) AND length in range AND no 25+ word sentences.
        core_passes = [q2_pass, q3_pass, q4_pass]
        pass_count = sum(core_passes)
        approved = length_ok and pass_count >= 2 and q5_pass and sentence_length_ok

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

        # Hard gates cap the score at <7 (below approval threshold) so a
        # grammar-clean, length-ok post with a 29-word run-on still gets
        # blocked at aggregation time even if approved=True somehow slips.
        if not q5_pass or not sentence_length_ok:
            score = min(score, 5.0)

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
        if not q5_pass:
            err = q5.get("error_quote", "")
            err_type = str(q5.get("error_type", "grammar")).lower()
            fix = q5.get("fix_hint", "")
            reasons.append(
                f"GRAMMAR ERROR ({err_type}): \"{err}\" — {fix}"
            )
        if not length_ok:
            reasons.append(f"Length: {word_count} words (must be 40-90).")
        if not sentence_length_ok and long_sentence_blocker:
            offender, offender_wc = long_sentence_blocker
            reasons.append(
                f"HARD GATE — sentence over 25 words ({offender_wc}w): "
                f'"{offender}..." Break into 2-3 short declaratives. '
                f"Liquid Death sentences average 6-10 words — never over 25."
            )
        # Q6 soft flag — post failed the concrete-specificity checksum.
        # Does NOT block approval but surfaces feedback so next revision
        # hits either a photographable noun or a private human hour.
        if not q6_has_contact:
            nearest = q6.get("nearest_abstraction", "")
            concrete_hint = q6.get("concrete_fix_hint", "")
            reasons.append(
                f"SOFT — no emotional-contact checksum. Post has no "
                f"photographable object and no private human hour. "
                f'Closest abstraction: "{nearest}". Concrete fix: '
                f"{concrete_hint} — specificity IS the emotional vector "
                f"(Ogilvy/Onion rule). The reader only feels when the "
                f"post names one thing a camera could catch or one "
                f"hour a specific human is living."
            )

        feedback = " | ".join(reasons) if reasons else ""

        criteria_breakdown = {
            "q1_weakest_sentence": q1,
            "q2_metaphors": q2,
            "q3_essay_drift": q3,
            "q4_template_crutch": q4,
            "q5_grammar": q5,
            "q6_emotional_contact": q6,
            "sentence_length_ok": sentence_length_ok,
            "long_sentence": (
                {"text": long_sentence_blocker[0], "word_count": long_sentence_blocker[1]}
                if long_sentence_blocker else None
            ),
            "passes": {
                "q2": q2_pass, "q3": q3_pass, "q4": q4_pass,
                "q5_grammar": q5_pass, "length": length_ok,
                "sentence_length": sentence_length_ok,
                "q6_emotional_contact": q6_has_contact,
            },
            "word_count": word_count,
            "model": self.model,
        }

        grammar_mark = "" if q5_pass else " 🚫GRAMMAR"
        long_mark = (
            f" 🚫SENTENCE-{long_sentence_blocker[1]}w" if long_sentence_blocker else ""
        )
        contact_mark = "" if q6_has_contact else " ⚠️NO-CONTACT"
        self.logger.info(
            f"Marcus Williams (GPT-4o): {pass_count}/3 core + grammar={q5_pass}, "
            f"contact={q6_has_contact}, "
            f"{word_count}w {'✅' if approved else '❌'}{grammar_mark}{long_mark}{contact_mark}"
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
