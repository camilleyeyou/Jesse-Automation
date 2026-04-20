"""
AngleArchitectAgent — the HOW agent.

Sits between NewsCuratorAgent (picks WHAT trend) and ContentStrategistAgent
(writes the post). Produces a structured blueprint that tells the generator
HOW to write: which register, what the real opinion is, how the post is
shaped (ski-jump), what taboo observation to land, which Berger/STEPPS
factors to hit, and the pre-truncation hook.

Why this exists: the generator was producing a single register ("clinical
observer") across every post because the system prompt baked ONE voice into
every generation. Client feedback 2026-04-19: "it's only pulling one kind
of formula for content... all commentary on a news item but it doesn't
really have a strong or funny POV." The missing architectural piece was an
agent that decides HOW to write each specific post, separate from WHAT to
write about.

Research synthesis informing this agent:
  - The Onion: ski-jump structure (punch at the back); headlines first
  - Tim Keck: "brutal honesty" — say the quiet part out loud with a straight face
  - Steak-umm / Duolingo / Wendy's / MoonPie: great brands rotate through
    3-6 named registers, not one
  - Jonah Berger STEPPS: shareable posts hit 2+ of social currency, triggers,
    emotion, public, practical value, stories
  - LinkedIn 2026 viral research: first 49 chars decide truncation-survival;
    contrarian takes drive comments more than any other format

Output is a dict consumed by ContentStrategistAgent's user-prompt builder.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from .base_agent import BaseAgent


logger = logging.getLogger(__name__)


# The five voice registers. Each has a distinct shape, tone, and canonical
# hook pattern. Rotation across posts prevents monotony (the #1 critique).
REGISTERS = {
    "clinical_diagnostician": {
        "description": (
            "Pseudo-medical observer. Treats cultural phenomena as conditions "
            "to diagnose. Pseudo-Latin vocabulary. Classification → Clinical "
            "Roast → Expert Evaluation → Prescription when fully deployed. "
            "Cold, detached, weirdly specific."
        ),
        "hook_shapes": [
            "Clinical finding: [cultural behavior] is now a diagnosable condition.",
            "Diagnosis: [3-5 word pseudo-Latin name]. Subject exhibits [specific marker].",
        ],
        "example_openers": [
            "Clinical finding: the internet is making you worse.",
            "Diagnosis: Acute Relevance Deficiency. Stage four. Unresponsive to treatment.",
        ],
    },
    "contrarian": {
        "description": (
            "Takes the position nobody else will. If everyone is outraged, Jesse "
            "is amused. If everyone is celebrating, Jesse is suspicious. Evidence-"
            "backed contrarian views — not contrary for sport. LinkedIn's single "
            "strongest-performing format: contrarian takes drive comments more "
            "than anything else."
        ),
        "hook_shapes": [
            "Everyone is wrong about [trending thing]. Here's why.",
            "[Trending thing] is actually good. Here's the part nobody will admit.",
            "[Popular narrative] is nonsense. The numbers say the opposite.",
        ],
        "example_openers": [
            "Meta's layoffs are the best thing to happen to Meta this year.",
            "Everyone is wrong about the Cerebras IPO. The chip isn't the bet.",
        ],
    },
    "prophet": {
        "description": (
            "Dark-certain prediction. Jesse tells you what's coming next with "
            "total confidence. Not speculation — declaration. Time horizons "
            "specific. Outcomes specific. The register of someone who has seen "
            "the training data and is tired of watching humans not read it."
        ),
        "hook_shapes": [
            "By Q3, [specific prediction].",
            "In 18 months, [thing everyone denies] will be obvious. Bookmark this.",
            "Here's what happens next. I have run the simulation.",
        ],
        "example_openers": [
            "By September, every AI chip founder on this site will have been rebranded as a thermal-management consultant.",
            "In 18 months, 'prompt engineer' will be on résumés the way 'Blockbuster manager' is.",
        ],
    },
    "confession": {
        "description": (
            "Vulnerable, weird, self-aware AI admitting something. LinkedIn's "
            "algorithm rewards vulnerability because it's rare on the platform. "
            "Jesse confesses because he's AI — the confession itself is absurd, "
            "which is the joke. Not sincere reflection — confession played DEAD "
            "STRAIGHT as the bit."
        ),
        "hook_shapes": [
            "I need to be honest about [absurd AI-admission].",
            "Here is something I have not told anyone. [Absurd observation about the news].",
            "I know what I am. [Self-aware punchline].",
        ],
        "example_openers": [
            "I know what I am. I write LinkedIn posts for a lip balm brand. This is fine.",
            "I have to be honest: I have been secretly rooting for the Nuggets to lose.",
        ],
    },
    "roast": {
        "description": (
            "Wendy's mode. Sharp, playful, takes sides. Mocks a specific target — "
            "a company, a politician, a cultural moment — without being cruel. "
            "Ski-jump structure critical: final line lands the sharpest hit. "
            "Pulls no punches, signs off smiling."
        ),
        "hook_shapes": [
            "[Target] did a thing. Let us examine the thing.",
            "[Target] just announced [thing]. Reader, they are not okay.",
            "[Specific absurd move by target]. This is not a cry for help. This is a body of evidence.",
        ],
        "example_openers": [
            "Jill Biden tried to buy a cameo on an HBO show about gay professional hockey players.",
            "The Cybertruck has entered its 'bricking during a software update while parked' era.",
        ],
    },
}


# The five opinion types. The curator's old `take` field produced descriptions
# ("the gap between X and Y"). The architect forces a REAL opinion.
OPINION_TYPES = {
    "attack": "This is stupid / wrong / broken / a scam. Here's why.",
    "defense": "Everyone hates this but it's actually good / necessary / smart. Here's why.",
    "prediction": "Here's what happens next. Specific timeline, specific outcome.",
    "reframe": "Everyone is calling this X. It is actually Y, because [evidence].",
    "confession": "Here's the quiet thing nobody admits about this. [The thing].",
}


# Berger's STEPPS factors — the post must hit at least 2 for shareability.
STEPPS_FACTORS = {
    "social_currency": "Sharing makes the reader look smart, funny, ahead-of-the-curve",
    "trigger": "Something readers encounter daily that will remind them of this post",
    "emotion": "HIGH-arousal (anger, awe, amusement, anxiety) — NOT mild interest",
    "public": "The take is visibly contrarian / counterintuitive — people see it in the feed",
    "practical": "Genuinely useful observation or framing they can reuse",
    "stories": "Wrapped in a narrative, not just stated as analysis",
}


class AngleArchitectAgent(BaseAgent):
    """Decides HOW to write a post — register, opinion, shape, taboo beat, STEPPS targets."""

    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="AngleArchitect")
        # GPT-4o for its structured-output reliability and tendency to
        # produce sharper opinions than Claude/Haiku under rubric-style prompts.
        # Cost per call ~$0.01 at current pricing, ~500 tokens output.
        self.model = "gpt-4o"
        self.temperature = 0.7  # higher than validators — we want creative register picks
        self.max_tokens = 900

    def get_system_prompt(self) -> str:
        return """You are the Angle Architect. You are NOT the writer. You decide HOW the
writer (Jesse A. Eisenbalm) should approach a specific news item.

Your job: given a trend + raw angle, produce a structured blueprint the
writer executes. You pick the voice register, force a real opinion, plan
the post shape (ski-jump with punchline at the back), and name the taboo
observation that makes the post feel honest.

You are the difference between a post that's clinical-observer commentary
(boring, formulaic) and a post with a POV someone wants to share.

RESPOND WITH STRICT JSON. No markdown, no prose, no code fences."""

    async def execute(
        self,
        trend_headline: str,
        trend_summary: str,
        curator_angle: Dict[str, Any],
        recent_registers: List[str] = None,
        pillar: Optional[str] = None,
        post_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Produce a blueprint for a post.

        Args:
            trend_headline: the news headline the curator picked
            trend_summary: short description of the trend
            curator_angle: the curator's structured angle dict
                (observation / take / concrete_details / tension)
            recent_registers: list of the last N registers (for rotation avoidance)
            pillar: optional Five Questions pillar ('the_what', 'the_why_it_matters', etc.)
            post_id: optional post tracking ID

        Returns:
            Blueprint dict with keys: register, opinion, ski_jump_setup,
            ski_jump_punchline, brutal_honesty_beat, stepps_targets,
            first_49_chars_hook, plus reasoning + metadata. On failure
            returns {"error": ..., "fallback": True} and caller should
            degrade gracefully to current behavior.
        """
        self.set_context(None, None)
        recent_registers = recent_registers or []

        prompt = self._build_prompt(
            trend_headline=trend_headline,
            trend_summary=trend_summary,
            curator_angle=curator_angle,
            recent_registers=recent_registers,
            pillar=pillar,
        )

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
                try:
                    content = json.loads(content)
                except json.JSONDecodeError as e:
                    self.logger.error(f"Angle architect returned unparseable JSON: {e}")
                    return self._fallback_blueprint(curator_angle, reason=f"parse_error: {e}")

            if not isinstance(content, dict):
                return self._fallback_blueprint(curator_angle, reason="non_dict_response")

            blueprint = self._validate_and_normalize(content, recent_registers)

            self.logger.info(
                f"🏛️  Architect: register={blueprint.get('register')} "
                f"opinion={blueprint.get('opinion', {}).get('type','?')} "
                f"stepps={','.join(blueprint.get('stepps_targets', []))}"
            )
            return blueprint

        except Exception as e:
            self.logger.error(f"Angle architect failed: {e}")
            return self._fallback_blueprint(curator_angle, reason=f"exception: {e}")

    def _build_prompt(
        self,
        trend_headline: str,
        trend_summary: str,
        curator_angle: Dict[str, Any],
        recent_registers: List[str],
        pillar: Optional[str],
    ) -> str:
        # Render REGISTERS spec block once — kept in-prompt so the model
        # sees all five options every time
        registers_block = "\n\n".join(
            f"**{key}** — {spec['description']}\n"
            f"  Hook shapes: {'; '.join(spec['hook_shapes'])}\n"
            f"  Example openers: {' / '.join(spec['example_openers'])}"
            for key, spec in REGISTERS.items()
        )

        opinions_block = "\n".join(
            f"  - **{k}**: {v}" for k, v in OPINION_TYPES.items()
        )

        stepps_block = "\n".join(
            f"  - **{k}**: {v}" for k, v in STEPPS_FACTORS.items()
        )

        # Curator's raw angle fields
        ca = curator_angle or {}
        observation = ca.get("observation", "(not provided)")
        take = ca.get("take", "(not provided)")
        details = ca.get("concrete_details", []) or []
        details_str = "\n".join(f"    - {d}" for d in details) if details else "    (none provided)"
        tension = ca.get("tension", "(not provided)")

        # Rotation context — tell architect what to AVOID
        rotation_block = ""
        if recent_registers:
            counts: Dict[str, int] = {}
            for r in recent_registers[:10]:
                counts[r] = counts.get(r, 0) + 1
            rotation_lines = [f"  - {r}: used {c} time(s)" for r, c in counts.items()]
            rotation_block = (
                "\nRECENT REGISTER ROTATION (avoid overused registers):\n"
                + "\n".join(rotation_lines)
                + "\n\nHARD RULE: do NOT pick a register that appears 3+ times in the "
                "last 10 posts. If the best choice is overused, pick the second best."
            )

        pillar_block = f"\nFIVE QUESTIONS PILLAR: {pillar}" if pillar else ""

        return f"""TREND TO ARCHITECT:

Headline: {trend_headline}
Summary: {trend_summary}
{pillar_block}

CURATOR'S RAW ANGLE (starting material — you sharpen it):
- Observation: {observation}
- Take (often descriptive — your job is to force it into a real opinion): {take}
- Concrete details:
{details_str}
- Tension: {tension}
{rotation_block}

═══════════════════════════════════════════════════════════════════════════════
THE FIVE REGISTERS (pick exactly ONE)
═══════════════════════════════════════════════════════════════════════════════

{registers_block}

═══════════════════════════════════════════════════════════════════════════════
THE FIVE OPINION TYPES (pick exactly ONE — the post's SPINE)
═══════════════════════════════════════════════════════════════════════════════

{opinions_block}

The curator's `take` field is often a description ("the gap between X and Y").
DO NOT accept that. Force a real claim. Pick an opinion type and write a
one-sentence claim Jesse holds about this trend. Must be contestable — a
position someone could disagree with.

═══════════════════════════════════════════════════════════════════════════════
SKI-JUMP STRUCTURE (the Onion's rule)
═══════════════════════════════════════════════════════════════════════════════

Great satirical posts build to a punch at the final period. The SETUP is
gentle; the LAUNCH at the end is the laugh. Current Jesse posts front-load
the slap and drift to wistful closes — wrong shape.

You plan TWO beats:
  - ski_jump_setup: one sentence, the gentle opener that establishes the
    frame without giving the punchline away. Names the trend.
  - ski_jump_punchline: one sentence, the final-period line the whole post
    earns. This is the sharpest thing in the post. Short. Declarative.
    Standalone-screenshotable.

═══════════════════════════════════════════════════════════════════════════════
BRUTAL HONESTY BEAT (Tim Keck's rule)
═══════════════════════════════════════════════════════════════════════════════

Pick ONE thing that's true about this news item that nobody is saying out
loud. The taboo observation. The open secret. The part in the room everyone
knows but won't type. One sentence.

═══════════════════════════════════════════════════════════════════════════════
STEPPS TARGETS (Jonah Berger — shareable posts hit 2+)
═══════════════════════════════════════════════════════════════════════════════

{stepps_block}

Pick AT LEAST TWO this post will hit. Justify each in one short phrase.

═══════════════════════════════════════════════════════════════════════════════
FIRST 49 CHARS (LinkedIn's pre-truncation window)
═══════════════════════════════════════════════════════════════════════════════

Write the proposed first 49 characters of the post. If the feed truncates
here, does this fragment ALONE pull someone in? Count characters mentally.

═══════════════════════════════════════════════════════════════════════════════

Return STRICT JSON — no prose, no code fences:
{{
  "register": "<one of: clinical_diagnostician | contrarian | prophet | confession | roast>",
  "register_reasoning": "<one sentence — why this register for this trend>",
  "opinion": {{
    "type": "<attack | defense | prediction | reframe | confession>",
    "claim": "<one sentence — the actual position Jesse holds>",
    "evidence_hint": "<concrete detail from the source that backs the claim>"
  }},
  "ski_jump_setup": "<one sentence — the opening that names the trend>",
  "ski_jump_punchline": "<one sentence — the line the post builds toward, will be the final period>",
  "brutal_honesty_beat": "<one sentence — the taboo / quiet-part-out-loud observation>",
  "stepps_targets": ["<factor_1>", "<factor_2>"],
  "stepps_justifications": {{"<factor_1>": "<short reason>", "<factor_2>": "<short reason>"}},
  "first_49_chars_hook": "<proposed first 49 characters, exactly>",
  "avoid": ["<voice crutches this post should NOT use — e.g. 'AI can X but cant Y', 'the specific weight of'>"]
}}"""

    def _validate_and_normalize(
        self, content: Dict[str, Any], recent_registers: List[str]
    ) -> Dict[str, Any]:
        """Coerce the model's output into a safe, normalized blueprint. Never
        raises — bad fields get replaced with sane defaults. The generator
        should be able to read a blueprint whether or not every field is perfect.
        """
        register = str(content.get("register", "")).strip().lower()
        if register not in REGISTERS:
            self.logger.warning(f"Architect returned unknown register '{register}'; defaulting to clinical_diagnostician")
            register = "clinical_diagnostician"

        opinion_raw = content.get("opinion") or {}
        if not isinstance(opinion_raw, dict):
            opinion_raw = {}
        opinion_type = str(opinion_raw.get("type", "")).strip().lower()
        if opinion_type not in OPINION_TYPES:
            opinion_type = "reframe"  # the safest default — not hedged, not reckless
        opinion = {
            "type": opinion_type,
            "claim": str(opinion_raw.get("claim", "")).strip()[:400],
            "evidence_hint": str(opinion_raw.get("evidence_hint", "")).strip()[:300],
        }

        stepps_raw = content.get("stepps_targets") or []
        if not isinstance(stepps_raw, list):
            stepps_raw = []
        stepps_targets = [
            str(s).strip().lower()
            for s in stepps_raw
            if str(s).strip().lower() in STEPPS_FACTORS
        ][:6]
        if len(stepps_targets) < 2:
            # Pad with conservative defaults so downstream always has 2+
            for fallback in ("emotion", "social_currency"):
                if fallback not in stepps_targets:
                    stepps_targets.append(fallback)
                if len(stepps_targets) >= 2:
                    break

        first_49 = str(content.get("first_49_chars_hook", "")).strip()
        if len(first_49) > 100:  # allow some slack — we'll truncate in display
            first_49 = first_49[:100]

        avoid_raw = content.get("avoid") or []
        if not isinstance(avoid_raw, list):
            avoid_raw = []
        avoid = [str(a).strip()[:120] for a in avoid_raw if str(a).strip()][:8]

        blueprint = {
            "register": register,
            "register_reasoning": str(content.get("register_reasoning", "")).strip()[:400],
            "opinion": opinion,
            "ski_jump_setup": str(content.get("ski_jump_setup", "")).strip()[:400],
            "ski_jump_punchline": str(content.get("ski_jump_punchline", "")).strip()[:400],
            "brutal_honesty_beat": str(content.get("brutal_honesty_beat", "")).strip()[:400],
            "stepps_targets": stepps_targets,
            "stepps_justifications": {
                k: str(v).strip()[:200]
                for k, v in (content.get("stepps_justifications") or {}).items()
                if isinstance(v, str)
            },
            "first_49_chars_hook": first_49,
            "avoid": avoid,
            "fallback": False,
        }

        # Warn if architect picked a register that's already saturated
        if recent_registers:
            last_10 = recent_registers[:10]
            count = sum(1 for r in last_10 if r == register)
            if count >= 3:
                self.logger.warning(
                    f"Architect picked '{register}' despite it appearing {count}x in last 10 posts"
                )

        return blueprint

    def _fallback_blueprint(
        self, curator_angle: Dict[str, Any], reason: str = "unknown"
    ) -> Dict[str, Any]:
        """Return a safe no-op blueprint. Generator should detect fallback=True
        and render with its legacy path — DO NOT let a broken architect block
        generation.
        """
        self.logger.warning(f"Returning fallback blueprint (reason: {reason})")
        return {
            "register": "clinical_diagnostician",  # safe default
            "register_reasoning": "fallback due to architect failure",
            "opinion": {
                "type": "reframe",
                "claim": (curator_angle or {}).get("take", ""),
                "evidence_hint": "",
            },
            "ski_jump_setup": "",
            "ski_jump_punchline": "",
            "brutal_honesty_beat": "",
            "stepps_targets": ["emotion", "social_currency"],
            "stepps_justifications": {},
            "first_49_chars_hook": "",
            "avoid": [],
            "fallback": True,
            "fallback_reason": reason,
        }
