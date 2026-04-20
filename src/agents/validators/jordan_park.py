"""
Jordan Park Validator — VIRAL SCIENCE (Phase 3 rewrite, 2026-04-19)

Reassigned from generic "shareability diagnostics" to LinkedIn-specific
viral-science judgments:
  Q1. STEPPS score — does the post hit >=2 of Jonah Berger's 6 factors?
      (social currency / triggers / emotion / public / practical / stories)
      HARD GATE — below 2 factors = auto-fail regardless of other Qs.
  Q2. Opinion strength — does the post express a REAL opinion, or is it
      just observation?
  Q3. Ski-jump structure — is the sharpest / most punchy line at the
      BACK of the post (Onion's rule)?
  Q4. First-49-char hook — does the pre-truncation fragment actually
      pull someone in?

These 4 map directly to the research synthesis (Onion craft + Berger +
LinkedIn 2026 viral patterns). Jordan is now THE viral-science validator;
Sarah covers recognition/authenticity; Marcus covers craft/grammar.
"""

import json
import logging
from typing import Dict, Any
from ..base_agent import BaseAgent
from ...models.post import LinkedInPost, ValidationScore

logger = logging.getLogger(__name__)


# Berger's STEPPS factors — kept as a shared constant so the system prompt,
# user prompt, and parse logic agree on exactly which factors count.
STEPPS_FACTORS = [
    "social_currency",  # Does sharing make the reader look smart/funny/right?
    "trigger",          # Is there a daily-life reminder that surfaces this post?
    "emotion",          # HIGH-arousal (anger, awe, amusement, anxiety)?
    "public",           # Visibly counterintuitive — shows up in feeds?
    "practical",        # Genuinely useful framing?
    "stories",          # Wrapped in narrative, not just analysis?
]


class JordanParkValidator(BaseAgent):
    """Viral-science validator — will this post actually spread on LinkedIn?"""

    # Response schema pinned (legacy from the Gemini era; kept because it
    # also locks Haiku into the right shape via the unified client's
    # json_schema pathway). Phase 3: new Q1-Q4 semantics.
    RESPONSE_SCHEMA = {
        "type": "object",
        "properties": {
            "q1_stepps": {
                "type": "object",
                "properties": {
                    "factors_hit": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": STEPPS_FACTORS,
                        },
                    },
                    "justifications": {
                        "type": "object",
                        # Keyed by factor name; each a short reason string.
                    },
                    "count": {"type": "integer"},
                    "passes": {"type": "boolean"},
                },
                "required": ["factors_hit", "justifications", "count", "passes"],
            },
            "q2_opinion_strength": {
                "type": "object",
                "properties": {
                    "claim": {"type": "string"},
                    "has_real_opinion": {"type": "boolean"},
                    "contestable": {"type": "boolean"},
                    "why": {"type": "string"},
                    "passes": {"type": "boolean"},
                },
                "required": ["claim", "has_real_opinion", "contestable", "passes"],
            },
            "q3_ski_jump": {
                "type": "object",
                "properties": {
                    "final_sentence": {"type": "string"},
                    "strongest_sentence": {"type": "string"},
                    "punchline_at_back": {"type": "boolean"},
                    "why": {"type": "string"},
                    "passes": {"type": "boolean"},
                },
                "required": ["final_sentence", "strongest_sentence", "punchline_at_back", "passes"],
            },
            "q4_first_49": {
                "type": "object",
                "properties": {
                    "opening_fragment": {"type": "string"},
                    "char_count": {"type": "integer"},
                    "pulls_reader_in": {"type": "boolean"},
                    "why": {"type": "string"},
                    "passes": {"type": "boolean"},
                },
                "required": ["opening_fragment", "pulls_reader_in", "passes"],
            },
            "engagement_prediction": {
                "type": "string",
                "enum": ["viral", "solid", "moderate", "flop"],
            },
            "word_count": {"type": "integer"},
        },
        "required": [
            "q1_stepps", "q2_opinion_strength", "q3_ski_jump", "q4_first_49",
            "engagement_prediction", "word_count",
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
        return """You are Jordan Park — a viral-science validator for LinkedIn content.
Your job is NOT to score posts 1-10. You answer four diagnostic questions
grounded in published research, and the approval derives mechanically.

Your lens is: will this post ACTUALLY spread on LinkedIn? Not "is it well
written" (Marcus owns craft). Not "does it hit the brand" (Sarah owns that).
Is it SHAREABLE in the specific mechanical sense that makes content
circulate?

You check:
  1. STEPPS — does it hit 2+ of Jonah Berger's 6 viral factors?
     (social currency / trigger / emotion / public / practical / stories)
  2. Opinion — is there a real, contestable claim, or just observation?
  3. Ski-jump — is the sharpest line at the BACK of the post (Onion's rule)?
  4. First 49 chars — does the pre-truncation fragment pull a stranger in?

Be SPECIFIC. Quote the post. Count characters. Answer the question asked,
not an adjacent question. Respond with JSON only — no prose, no markdown,
no code fences."""

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
        # First 49 characters — pre-truncation window on LinkedIn mobile feed
        first_49 = post.content[:49]
        return f"""POST TO EVALUATE:
\"\"\"
{post.content}
\"\"\"

Word count: {word_count} (hard range: 40-90)
First 49 characters (LinkedIn pre-truncation window): "{first_49}"

Answer FOUR viral-science questions. BE SPECIFIC. QUOTE THE POST.

═══════════════════════════════════════════════════════════════════════════════
Q1. STEPPS SCORE — which of Jonah Berger's 6 factors does this post hit?
═══════════════════════════════════════════════════════════════════════════════

Score the post against each factor. Include ONLY the ones the post genuinely
hits — do not stretch. Each hit must be defensible in one sentence.

  - social_currency: Sharing this post makes the reader look smart / funny /
    ahead-of-the-curve. Is there an identity signal the sharer would want?
  - trigger: Something the reader encounters in daily life that will remind
    them of this post and surface it in conversation.
  - emotion: HIGH-arousal emotion (anger, awe, amusement, anxiety, delight).
    Mild interest / clinical detachment is NOT emotion in this framework.
  - public: The take is visibly counterintuitive — passersby can tell it's
    contrarian without reading the whole thing.
  - practical: Genuinely useful framing / reusable observation / "news you
    can use."
  - stories: Wrapped in a narrative, not just analysis. Characters, sequence,
    tension.

HARD GATE: a post must hit AT LEAST 2 factors. Fewer than 2 = auto-fail
regardless of Q2/Q3/Q4.

═══════════════════════════════════════════════════════════════════════════════
Q2. OPINION STRENGTH — does the post take a real position?
═══════════════════════════════════════════════════════════════════════════════

Quote the post's central claim in ONE sentence. Then answer:
  - Is this a REAL opinion (someone could disagree), or just an observation
    ("the gap between X and Y", "AI can do X but can't do Y", neutral description)?
  - Is the claim CONTESTABLE — could a reasonable person argue the opposite?

If the post is observation-mode (descriptive, hedged, split-the-middle)
it FAILS even if beautifully written. LinkedIn's algorithm rewards
contrarian takes; neutral observations scroll past.

═══════════════════════════════════════════════════════════════════════════════
Q3. SKI-JUMP STRUCTURE — is the punchline at the BACK?
═══════════════════════════════════════════════════════════════════════════════

The Onion's craft rule: all the funny / sharp / surprising goes at the END
of the sentence, the end of the paragraph, and the end of the post.

  - Quote the FINAL sentence of the post.
  - Quote the SINGLE strongest/sharpest sentence in the post.
  - Are these the same sentence?

PASSES when the final sentence IS the sharpest / most punchy / most
screenshotable. FAILS when the strongest line is buried in the middle
and the post fades to a wistful close.

═══════════════════════════════════════════════════════════════════════════════
Q4. FIRST 49 CHARS — does the pre-truncation fragment pull readers in?
═══════════════════════════════════════════════════════════════════════════════

The first 49 characters (quoted above) are what LinkedIn shows before the
"see more" button. If this fragment ALONE doesn't stop the scroll, the
post is invisible.

Read ONLY the fragment above — ignore the rest of the post. Would a
stranger reading JUST that stop scrolling to expand?

PASSES only if yes.

═══════════════════════════════════════════════════════════════════════════════

Return STRICT JSON:
{{
  "q1_stepps": {{
    "factors_hit": [<subset of: social_currency, trigger, emotion, public, practical, stories>],
    "justifications": {{"<factor>": "<one sentence — why this post hits this factor>"}},
    "count": <int, len(factors_hit)>,
    "passes": <true iff count >= 2>
  }},
  "q2_opinion_strength": {{
    "claim": "<one sentence — the central claim, quoted or paraphrased from the post>",
    "has_real_opinion": <bool>,
    "contestable": <bool — could a reasonable person argue the opposite>,
    "why": "<one clause — what makes this an opinion or not>",
    "passes": <true iff has_real_opinion AND contestable>
  }},
  "q3_ski_jump": {{
    "final_sentence": "<exact quote of the last sentence>",
    "strongest_sentence": "<exact quote of the strongest sentence>",
    "punchline_at_back": <true iff the strongest sentence IS the final sentence OR is one of the final two sentences>,
    "why": "<one clause>",
    "passes": <true iff punchline_at_back>
  }},
  "q4_first_49": {{
    "opening_fragment": "<the first 49 chars, quoted>",
    "char_count": <int>,
    "pulls_reader_in": <bool>,
    "why": "<one clause — why it does or doesn't pull>",
    "passes": <true iff pulls_reader_in>
  }},
  "engagement_prediction": "<viral | solid | moderate | flop>",
  "word_count": {word_count}
}}"""

    def _parse_validation(self, content: Dict[str, Any], post: LinkedInPost = None) -> ValidationScore:
        """Phase 3 viral-science parse.

        Q1 (STEPPS) is a HARD GATE — below 2 factors = auto-fail regardless
        of Q2-Q4. Q2-Q4 (opinion / ski-jump / first-49) contribute to the
        standard pass-count-based approval (2 of 3 needed in addition to
        length + STEPPS gate).

        Legacy key fallbacks kept so in-flight drafts using the old schema
        (q1_insight / q2_surprise_moment etc.) still parse as defaults
        without crashing.
        """
        if not isinstance(content, dict):
            content = {}

        q1 = content.get("q1_stepps") or content.get("q1_insight") or {}
        q2 = content.get("q2_opinion_strength") or content.get("q2_surprise_moment") or {}
        q3 = content.get("q3_ski_jump") or content.get("q3_specific_reader") or {}
        q4 = content.get("q4_first_49") or content.get("q4_something_new_taught") or {}

        # Q1 — STEPPS hard gate (2+ factors required)
        factors_hit = q1.get("factors_hit") or []
        if not isinstance(factors_hit, list):
            factors_hit = []
        # Keep only recognized factors in case the model invents new ones
        factors_hit = [f for f in factors_hit if f in STEPPS_FACTORS]
        stepps_count = len(factors_hit)
        q1_pass = stepps_count >= 2

        # Q2 — opinion strength
        q2_pass = bool(q2.get("passes", False)) or (
            bool(q2.get("has_real_opinion", False)) and bool(q2.get("contestable", False))
        )

        # Q3 — ski-jump structure. Client feedback 2026-04-20: Jordan's LLM
        # judgment was too generous — would call a post "ski-jump" even when
        # the strongest line was buried mid-post. Now adds a deterministic
        # check: the final sentence must be SHORT (<=15 words). A long final
        # sentence is a trailing explanation, not a punchline.
        q3_pass = bool(q3.get("passes", False)) or bool(q3.get("punchline_at_back", False))
        if q3_pass and post and post.content:
            import re as _re
            flat = _re.sub(r"\s+", " ", post.content).strip()
            sentences = [s.strip() for s in _re.split(r"(?<=[.!?])\s+", flat) if s.strip()]
            if sentences:
                final_sentence = sentences[-1]
                final_word_count = len(final_sentence.split())
                # A punchline is short. 15+ words of closing sentence means
                # the post tapered off into explanation, not punch.
                if final_word_count > 15:
                    q3_pass = False
                    self.logger.debug(
                        f"Ski-jump override: final sentence is {final_word_count} words "
                        f"(ceiling 15). LLM passed Q3 but deterministic check fails."
                    )

        # Q4 — first-49-char hook
        q4_pass = bool(q4.get("passes", False)) or bool(q4.get("pulls_reader_in", False))

        try:
            word_count = int(content.get("word_count", len(post.content.split()) if post else 0))
        except (ValueError, TypeError):
            word_count = len(post.content.split()) if post else 0
        length_ok = 40 <= word_count <= 90

        # Viral-science gate structure (Phase 3, 2026-04-19):
        #   - STEPPS (Q1) is HARD — below 2 factors and the post cannot ship.
        #   - Among Q2/Q3/Q4 (opinion / ski-jump / first-49), 2 of 3 must pass.
        #   - Length still required.
        #
        # Rationale: STEPPS is the core shareability science. A post that
        # doesn't hit 2+ Berger factors won't spread regardless of how well
        # it's written. Q2-Q4 are structural quality — 2/3 allows one soft
        # signal to slip while still catching posts that are broken on
        # multiple structural fronts.
        core_passes = [q2_pass, q3_pass, q4_pass]
        core_count = sum(core_passes)
        approved = length_ok and q1_pass and core_count >= 2

        # Score mapping — approved iff >= 7.0 per the ValidationScore contract.
        if q1_pass and core_count == 3 and length_ok:
            score = 9.0
        elif q1_pass and core_count == 2 and length_ok:
            score = 7.5
        elif q1_pass and core_count == 1:
            score = 5.0
        elif q1_pass:
            score = 4.0
        else:
            # STEPPS failure — cap at 3.0 so this never approves
            score = 3.0

        reasons: list = []
        # STEPPS feedback — always include because it's the gate
        if not q1_pass:
            reasons.append(
                f"Q1 STEPPS HARD GATE: only {stepps_count} factor(s) hit "
                f"({', '.join(factors_hit) or 'none'}). Need >= 2 of "
                f"{', '.join(STEPPS_FACTORS)}. This post won't spread."
            )
        else:
            # Always log the hits for observability even on pass
            reasons.append(
                f"STEPPS hits ({stepps_count}): {', '.join(factors_hit)}"
            )

        if not q2_pass:
            claim = q2.get("claim", "")
            reasons.append(
                f"Q2 opinion: no real contestable take — \"{claim}\". "
                f"Post is observation, not opinion. Rewrite with a claim someone could disagree with."
            )
        if not q3_pass:
            strongest = q3.get("strongest_sentence", "")
            final = q3.get("final_sentence", "")
            reasons.append(
                f"Q3 ski-jump: punchline buried / final sentence too long. "
                f"Strongest line: \"{strongest}\" — ended on: \"{final}\". "
                f"Final sentence must be SHORT (<=15 words) AND the sharpest line. "
                f"Trim the closer. Trailing explanations kill the Onion shape."
            )
        if not q4_pass:
            frag = q4.get("opening_fragment", "")
            reasons.append(
                f"Q4 first-49: opening fragment doesn't pull — \"{frag}\". "
                f"Rewrite the first 49 chars to stand alone as a hook."
            )
        if not length_ok:
            reasons.append(f"Length: {word_count} words (must be 40-90).")

        feedback = " | ".join(reasons) if reasons else ""

        criteria_breakdown = {
            "q1_stepps": {
                "factors_hit": factors_hit,
                "count": stepps_count,
                "justifications": q1.get("justifications") or {},
                "passes": q1_pass,
            },
            "q2_opinion_strength": q2,
            "q3_ski_jump": q3,
            "q4_first_49": q4,
            "engagement_prediction": str(content.get("engagement_prediction", "moderate")),
            "passes": {
                "q1_stepps": q1_pass,
                "q2_opinion": q2_pass,
                "q3_ski_jump": q3_pass,
                "q4_first_49": q4_pass,
                "length": length_ok,
            },
            "stepps_count": stepps_count,
            "word_count": word_count,
            "model": self.model,
        }

        # Short provider tag for log clarity
        provider_tag = "?"
        model_lower = (self.model or "").lower()
        if "haiku" in model_lower:
            provider_tag = "haiku"
        elif "sonnet" in model_lower:
            provider_tag = "sonnet"
        elif "gemini" in model_lower:
            provider_tag = "gemini"
        else:
            provider_tag = (self.model.split("-")[0] if self.model else "?").lower()

        gate_tag = "🚫STEPPS" if not q1_pass else ""
        self.logger.info(
            f"Jordan Park ({provider_tag}) VIRAL: STEPPS={stepps_count}/6, "
            f"core={core_count}/3, {word_count}w "
            f"{'✅' if approved else '❌'}{gate_tag}"
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
