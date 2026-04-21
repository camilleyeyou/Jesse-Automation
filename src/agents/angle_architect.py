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
        "mandatory_signals": (
            "MUST use at least 2 pseudo-medical / pseudo-clinical terms "
            "(classification, diagnosis, subject, chronic, acute, symptomatic, "
            "prognosis, labial, buccal, epidermal, desiccation, xeric, lesion, "
            "condition, treatment). Opening line reads as a clinical chart entry."
        ),
        "must_not": (
            "Must NOT read as opinion-commentary or prediction. If the post "
            "is mostly Jesse's opinion with one clinical word sprinkled in, "
            "it's not clinical_diagnostician — it's contrarian or roast in disguise."
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
        "mandatory_signals": (
            "MUST explicitly NAME the popular view and then reject it. "
            "Post should read: 'Everyone thinks X. That's wrong. Here's why Y.' "
            "Without stating the popular view, the post isn't contrarian — "
            "it's just an opinion."
        ),
        "must_not": (
            "Must NOT use 'Everyone celebrates the [triad]. Nobody asks [counter].' "
            "as its structural move. That's a rhyming crutch. Vary the "
            "contrarian framing each time."
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
        "mandatory_signals": (
            "MUST include a specific time horizon ('by Q3', 'in 18 months', "
            "'by September', 'within two years', 'by the end of the decade', "
            "'in 5 years'). MUST include a specific predicted outcome, stated "
            "as certainty (not 'might' or 'could' — WILL). Without a time "
            "horizon and a specific outcome, the post is commentary, not prophecy."
        ),
        "must_not": (
            "Must NOT drift into roast-mode punchlines like 'Imagine.' or "
            "'They're not okay.' Prophet voice is confident prediction, not "
            "mockery with a sarcastic tag. If the post reads as a roast with "
            "a date on it, you picked the wrong register."
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
        "mandatory_signals": (
            "MUST use first-person 'I' statements throughout. MUST make an "
            "admission — something Jesse reveals about himself or his process "
            "that he 'shouldn't' reveal. The admission itself IS the content, "
            "not a framing device for commentary."
        ),
        "must_not": (
            "Must NOT be 'third-person observation with an I thrown in.' If "
            "the post could work without the 'I' statements, it's not confession "
            "— it's commentary wearing a confession costume."
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
        "mandatory_signals": (
            "MUST name a specific target (company, product, named person, "
            "specific cultural moment) in the first sentence. The target must "
            "be the OBJECT of the mockery throughout — not a springboard for "
            "general commentary."
        ),
        "must_not": (
            "Must NOT open with 'Let us examine...' — this phrase has become a "
            "roast-register tic. Ban from openers. Vary the roast frame: "
            "'[Target] did X. [Direct reaction].' / '[Target] just announced "
            "[Y]. [Punch at target].' / '[Absurd specific move]. [Damning "
            "conclusion].'"
        ),
        "hook_shapes": [
            "[Target] did [specific thing]. [Direct reaction sentence].",
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

# "Narrative" STEPPS factors — harder to hit than emotion+public. Client
# feedback 2026-04-19: architect was gaming the gate by picking emotion +
# (public OR social_currency) every single post. Those are the lowest-effort
# factors. At least ONE of the narrative factors must appear.
NARRATIVE_FACTORS = {"trigger", "practical", "stories"}

# Phase C (2026-04-20): length + structure variation to break "all posts
# look the same." Client queue review showed 10 of 10 posts at 65-76 words
# and exactly 4 paragraphs. Architect now picks a target for each.
LENGTH_TARGETS = {
    "short": {
        "word_range": "40-55",
        "min": 40,
        "max": 55,
        "guidance": "Compressed punch. 3-5 sentences. No setup, just impact. Think a brutal tweet with em dashes.",
    },
    "medium": {
        "word_range": "55-75",
        "min": 55,
        "max": 75,
        "guidance": "Standard Jesse length. 5-8 sentences. Room for setup → escalation → punch but no padding.",
    },
    "long": {
        "word_range": "75-95",
        "min": 75,
        "max": 95,
        "guidance": "Breathing room for a story or a longer argument. 8-12 sentences. Must EARN the length — every sentence still pulls its weight.",
    },
}

STRUCTURE_SHAPES = {
    "tight_3para": {
        "description": "3 paragraphs. Setup / escalation / punchline. Tight, fast.",
    },
    "standard_4para": {
        "description": "4 paragraphs. The default Jesse shape. Use less than 2 of the last 5 posts.",
    },
    "long_5para": {
        "description": "5 paragraphs. More texture, more development. For longer posts.",
    },
    "single_block": {
        "description": "ONE paragraph. No line breaks. A single dense block that hits hard. Rare — save for pointed attacks or confessions.",
    },
    "list_form": {
        "description": "Opens with a setup line, then a list-like structure (not actual bullets — declarative sentences each on a line, like a ledger or a receipt). Closes with a punchline.",
    },
}

# Phase F (2026-04-21): emotional_contact compositional blueprint.
# Research finding: prose "contact_beat" field too abstract — generator
# drifts to cold-smart observation because there's too much interpretation
# room. Fix per Onion/Ogilvy/Berger convergence: force 4 typed micro-fields
# that the generator cannot fulfill with abstraction.
#
#   - named_stakeholder: ONE implied human + role (not "employees" — "a PM",
#     "someone's kid", "a Best Buy clerk"). Universal via specificity.
#   - private_scene: ONE human hour/place/state (3am, kitchen table,
#     refreshing email, parking lot, waiting for a text).
#   - photographable_noun: ONE concrete object that could be photographed
#     (thermostat, lanyard, phone, sticky note, paper) — NOT a concept
#     (the market, the economy, progress, innovation).
#   - scale_anchor: ONE bureaucratic/institutional unit paired with one
#     domestic consequence in the same sentence-scale. "The GDP of Slovenia
#     / the dental appointment that got cancelled".
#
# These four fields are REQUIRED non-empty. If the architect emits an
# empty field, re-prompt once to fill; if still missing, degrade with a
# warning (don't block generation).
EMOTIONAL_CONTACT_FIELDS = {
    "named_stakeholder": {
        "definition": (
            "ONE implied human with a role or relation. Not 'employees' — "
            "'a PM at Microsoft.' Not 'people' — 'someone's kid.' Not "
            "'investors' — 'a retiree checking their brokerage app.' "
            "Specificity is the emotional vector (Ogilvy/Handley/Onion)."
        ),
        "good_examples": [
            "a Microsoft PM calling their partner",
            "someone's kid who heard about the layoff at Thanksgiving",
            "a Best Buy clerk waiting for closing",
            "the French prosecutor who cleared their afternoon",
            "a single mother refreshing the 401k app",
        ],
        "bad_examples": [
            "employees",
            "the workforce",
            "people",
            "investors",
            "the market",
        ],
    },
    "private_scene": {
        "definition": (
            "ONE human hour, place, or state. A private moment — the kind "
            "of moment institutions don't show. The 3am Test: did you name "
            "a specific hour, a kitchen, a parking lot, a state of waiting? "
            "If the post could happen only in boardrooms and press releases, "
            "the scene is missing."
        ),
        "good_examples": [
            "2:47am, ceiling staring",
            "Thanksgiving dinner with the brother-in-law",
            "a parking lot, engine running, phone unopened",
            "reading the email in the bathroom",
            "refreshing Twitter before getting out of bed",
        ],
        "bad_examples": [
            "the workplace",
            "the industry",
            "the media cycle",
            "the boardroom",
            "the press conference",
        ],
    },
    "photographable_noun": {
        "definition": (
            "ONE concrete object that could physically be photographed. "
            "The Ogilvy/Handley spec: sensory and real. Not a concept — "
            "an object. A thermostat, a lanyard, a Post-it, a fridge note, "
            "a phone, a paper chart. If you can't photograph it, you "
            "haven't specified it. NEVER 'the market' or 'innovation.'"
        ),
        "good_examples": [
            "a thermostat",
            "a laminated lanyard",
            "a yellow legal pad",
            "a phone face-down on the counter",
            "a sticky note on the fridge",
            "the paper the hearing was handwritten on",
        ],
        "bad_examples": [
            "the market",
            "the economy",
            "innovation",
            "progress",
            "the narrative",
        ],
    },
    "scale_anchor": {
        "definition": (
            "ONE pair: a bureaucratic/institutional unit on one side, a "
            "domestic/bodily consequence on the other. The Grok-no-legs "
            "move. 'The GDP of Slovenia / the dental appointment' — the "
            "two belong in the same sentence, and the gap IS the joke "
            "AND the feeling. Both sides are concrete."
        ),
        "good_examples": [
            "13% market cap gain / one PM's ceiling at 2am",
            "trillion-dollar pivot / a hardware VP's promotion party",
            "AI chatbot subpoena / no legs to walk to the hearing",
            "Oval Office ceremony / what a Bible is at 3am",
            "39-cent price target revision / a vending machine rounding error",
        ],
        "bad_examples": [
            "the big picture / the small picture",
            "macro trends / micro trends",
            "the company / the people",
            "progress / humanity",
        ],
    },
}

# Phase E (2026-04-21): emotional temperature. Client feedback: posts are
# technically varied in register/length/shape but emotionally flat —
# "cold-smart" across the board. This is what Jesse FEELS about the story,
# layered ONTO the register (the voice). Clinical+tender ≠ clinical+cold.
# Rotation-aware like register: same temperature 3+ in last 5 = banned.
EMOTIONAL_TEMPERATURES = {
    "cold_clinical": (
        "Detached observer. Arm's-length analysis. The phenomenon is "
        "interesting; Jesse has no skin in it. Appropriate for policy / "
        "corporate / tech-industry stories where emotional contact would "
        "feel manufactured. USE SPARINGLY — this is the default drift if "
        "nothing else is specified, and we're trying to avoid it."
    ),
    "dry_amused": (
        "Finds the story genuinely funny in an understated way. Jesse's "
        "default warm-funny register. Deadpan delivery but there's a twinkle "
        "behind it. Works for absurdist news, cultural moments, corporate "
        "pratfalls."
    ),
    "tender": (
        "Something in the story moved Jesse. Softer voice. Lingering attention. "
        "Names the human. Ends with recognition rather than a slap. Works for "
        "grief, small human moments, dying-teen-kind-of-stories. Still punchy "
        "— still Jesse — but the final note is warmth, not smirk."
    ),
    "outraged": (
        "A specific injustice landed. Jesse's pissed. Controlled fury — still "
        "dry, still clinical, but the anger shows through. Works for "
        "exploitation, corporate abuse, named-party hypocrisy. The reader "
        "should feel the reader's OWN anger validated."
    ),
    "reverent": (
        "Jesse takes the moment seriously. Stepping back with respect. "
        "Still Jesse — still weird, still sharp — but acknowledging that "
        "something matters. Works for achievements, deaths of icons, moments "
        "of genuine human achievement or loss."
    ),
    "delighted": (
        "Something in the story is genuinely delightful. Jesse leans into "
        "it. Not sarcastic-delighted (that's dry_amused) — genuinely "
        "tickled. Works for absurd wins, weird viral wholesome moments, "
        "human doing human things that work."
    ),
    "weary": (
        "Jesse has seen this pattern enough times to be tired of it. Not "
        "angry — resigned. Works for predictable corporate cycles, repeated "
        "failures, 'this happens every quarter' stories."
    ),
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
        recent_length_targets: List[str] = None,
        recent_structure_shapes: List[str] = None,
        recent_emotional_temperatures: List[str] = None,
        recent_opening_patterns: List[str] = None,
        recent_contact_beat_frames: List[str] = None,
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
            recent_length_targets: last N length targets (short/medium/long) — Phase C
            recent_structure_shapes: last N structure shapes — Phase C

        Returns:
            Blueprint dict with keys: register, opinion, ski_jump_setup,
            ski_jump_punchline, brutal_honesty_beat, stepps_targets,
            first_49_chars_hook, length_target, structure_shape, plus
            reasoning + metadata. On failure returns {"error": ...,
            "fallback": True} and caller should degrade gracefully.
        """
        self.set_context(None, None)
        recent_registers = recent_registers or []
        recent_length_targets = recent_length_targets or []
        recent_structure_shapes = recent_structure_shapes or []
        recent_emotional_temperatures = recent_emotional_temperatures or []
        recent_opening_patterns = recent_opening_patterns or []
        recent_contact_beat_frames = recent_contact_beat_frames or []

        prompt = self._build_prompt(
            trend_headline=trend_headline,
            trend_summary=trend_summary,
            curator_angle=curator_angle,
            recent_registers=recent_registers,
            pillar=pillar,
            recent_length_targets=recent_length_targets,
            recent_structure_shapes=recent_structure_shapes,
            recent_emotional_temperatures=recent_emotional_temperatures,
            recent_opening_patterns=recent_opening_patterns,
            recent_contact_beat_frames=recent_contact_beat_frames,
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

            blueprint = self._validate_and_normalize(
                content,
                recent_registers,
                recent_length_targets=recent_length_targets,
                recent_structure_shapes=recent_structure_shapes,
                recent_emotional_temperatures=recent_emotional_temperatures,
            )

            ec = blueprint.get("emotional_contact", {}) or {}
            ec_mark = "✅" if ec.get("complete") else "⚠️ INCOMPLETE"
            self.logger.info(
                f"🏛️  Architect: register={blueprint.get('register')} "
                f"temp={blueprint.get('emotional_temperature','?')} "
                f"opinion={blueprint.get('opinion', {}).get('type','?')} "
                f"len={blueprint.get('length_target','?')} "
                f"shape={blueprint.get('structure_shape','?')} "
                f"anchor={blueprint.get('anchor_human','?')[:20] if blueprint.get('anchor_human') else '—'} "
                f"ec={ec_mark}"
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
        recent_length_targets: List[str] = None,
        recent_structure_shapes: List[str] = None,
        recent_emotional_temperatures: List[str] = None,
        recent_opening_patterns: List[str] = None,
        recent_contact_beat_frames: List[str] = None,
    ) -> str:
        recent_length_targets = recent_length_targets or []
        recent_structure_shapes = recent_structure_shapes or []
        recent_emotional_temperatures = recent_emotional_temperatures or []
        recent_opening_patterns = recent_opening_patterns or []
        recent_contact_beat_frames = recent_contact_beat_frames or []
        # Render REGISTERS spec block once — kept in-prompt so the model
        # sees all five options every time, WITH the mandatory_signals /
        # must_not fields (2026-04-20 sharpening — prevents register
        # blur, e.g. prophet drifting into roast).
        def _render_register(key: str, spec: Dict[str, Any]) -> str:
            parts = [f"**{key}** — {spec['description']}"]
            if spec.get("mandatory_signals"):
                parts.append(f"  ✓ REQUIRED: {spec['mandatory_signals']}")
            if spec.get("must_not"):
                parts.append(f"  ✗ AVOID: {spec['must_not']}")
            parts.append(f"  Hook shapes: {'; '.join(spec['hook_shapes'])}")
            parts.append(f"  Example openers: {' / '.join(spec['example_openers'])}")
            return "\n".join(parts)

        registers_block = "\n\n".join(
            _render_register(key, spec) for key, spec in REGISTERS.items()
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

        # Rotation context — HARD GATE on recent register choices.
        # Client feedback 2026-04-19: architect was picking contrarian 4x and
        # roast 3x out of 8 posts. "Soft warning" rotation wasn't enforced.
        # Now: compute last-5 counts explicitly and tell the architect which
        # registers are BANNED (hard) vs DISCOURAGED (soft).
        rotation_block = ""
        banned_registers: List[str] = []
        if recent_registers:
            counts_last5: Dict[str, int] = {}
            for r in recent_registers[:5]:
                counts_last5[r] = counts_last5.get(r, 0) + 1
            counts_last10: Dict[str, int] = {}
            for r in recent_registers[:10]:
                counts_last10[r] = counts_last10.get(r, 0) + 1

            # BANNED if 3+ in the last 5 posts — hard cap on dominance
            banned_registers = [r for r, c in counts_last5.items() if c >= 3]
            # DISCOURAGED if 4+ in the last 10 posts — softer rotation nudge
            discouraged = [
                r for r, c in counts_last10.items()
                if c >= 4 and r not in banned_registers
            ]

            rotation_lines_5 = [
                f"  - {r}: {c} time(s)" for r, c in sorted(counts_last5.items(), key=lambda x: -x[1])
            ]
            rotation_lines_10 = [
                f"  - {r}: {c} time(s)" for r, c in sorted(counts_last10.items(), key=lambda x: -x[1])
            ]

            banned_block = ""
            if banned_registers:
                banned_block = (
                    "\n\n⛔ BANNED FOR THIS POST (3+ appearances in last 5 posts — HARD RULE):\n"
                    + "\n".join(f"  - {r}" for r in banned_registers)
                    + "\n  DO NOT PICK ANY OF THESE. Pick from the remaining registers."
                )

            discouraged_block = ""
            if discouraged:
                discouraged_block = (
                    "\n\n⚠ Discouraged (4+ in last 10 — prefer alternatives if viable):\n"
                    + "\n".join(f"  - {r}" for r in discouraged)
                )

            rotation_block = (
                "\nRECENT REGISTER ROTATION:\n"
                + "  LAST 5 POSTS:\n"
                + "\n".join(rotation_lines_5)
                + "\n  LAST 10 POSTS:\n"
                + "\n".join(rotation_lines_10)
                + banned_block
                + discouraged_block
                + "\n\nAIM FOR COVERAGE: over any 7-post window you should use at least "
                "3 distinct registers. If clinical_diagnostician or confession haven't "
                "appeared recently, that's a signal to pick them now when the topic fits."
            )

        pillar_block = f"\nFIVE QUESTIONS PILLAR: {pillar}" if pillar else ""

        # Phase C (2026-04-20): length + structure rotation blocks. Client
        # queue review flagged that ALL 10 posts were 65-76 words and
        # exactly 4 paragraphs. Same logic as register rotation: ban
        # whatever dominates last 5.
        length_block = ""
        banned_lengths: List[str] = []
        if recent_length_targets:
            length_counts5: Dict[str, int] = {}
            for l in recent_length_targets[:5]:
                length_counts5[l] = length_counts5.get(l, 0) + 1
            banned_lengths = [l for l, c in length_counts5.items() if c >= 3]
            lines = [f"  - {k}: {c}" for k, c in sorted(length_counts5.items(), key=lambda x: -x[1])]
            banned_suffix = ""
            if banned_lengths:
                banned_suffix = (
                    f"\n  ⛔ BANNED (3+ in last 5): {', '.join(banned_lengths)} — "
                    "MUST pick a different length target."
                )
            length_block = "\n\nRECENT LENGTH ROTATION (last 5):\n" + "\n".join(lines) + banned_suffix

        length_options = "\n".join(
            f"  - **{k}** ({v['word_range']} words): {v['guidance']}"
            for k, v in LENGTH_TARGETS.items()
        )

        structure_block = ""
        banned_structures: List[str] = []
        if recent_structure_shapes:
            struct_counts5: Dict[str, int] = {}
            for s in recent_structure_shapes[:5]:
                struct_counts5[s] = struct_counts5.get(s, 0) + 1
            banned_structures = [s for s, c in struct_counts5.items() if c >= 3]
            lines = [f"  - {k}: {c}" for k, c in sorted(struct_counts5.items(), key=lambda x: -x[1])]
            banned_suffix = ""
            if banned_structures:
                banned_suffix = (
                    f"\n  ⛔ BANNED (3+ in last 5): {', '.join(banned_structures)} — "
                    "MUST pick a different structure shape."
                )
            structure_block = "\n\nRECENT STRUCTURE ROTATION (last 5):\n" + "\n".join(lines) + banned_suffix

        structure_options = "\n".join(
            f"  - **{k}**: {v['description']}"
            for k, v in STRUCTURE_SHAPES.items()
        )

        # Phase E (2026-04-21): emotional temperature rotation block.
        # Client review: posts are technically varied but emotionally flat.
        # Temperature is how Jesse FEELS about the story — orthogonal to
        # register (the voice). Rotation-aware: same temp 3+ in last 5 = banned.
        temp_block = ""
        banned_temps: List[str] = []
        if recent_emotional_temperatures:
            temp_counts5: Dict[str, int] = {}
            for t in recent_emotional_temperatures[:5]:
                temp_counts5[t] = temp_counts5.get(t, 0) + 1
            banned_temps = [t for t, c in temp_counts5.items() if c >= 3]
            lines = [f"  - {k}: {c}" for k, c in sorted(temp_counts5.items(), key=lambda x: -x[1])]
            banned_suffix = ""
            if banned_temps:
                banned_suffix = (
                    f"\n  ⛔ BANNED (3+ in last 5): {', '.join(banned_temps)} — "
                    "MUST pick a different emotional temperature."
                )
            # Extra pressure: if cold_clinical has been 3+ of last 5, explicitly
            # note that it's the default-drift mode we're trying to escape.
            if "cold_clinical" in banned_temps:
                banned_suffix += (
                    "\n  ⚠ cold_clinical is the default-drift mode. The last "
                    "5 posts have been cold-smart. The feed is starving for "
                    "an emotional beat. Pick tender, delighted, outraged, or "
                    "reverent when the story can support it."
                )
            temp_block = (
                "\n\nRECENT EMOTIONAL TEMPERATURE ROTATION (last 5):\n"
                + "\n".join(lines)
                + banned_suffix
            )
        elif recent_registers:  # Have data but no temp tracked yet
            temp_block = (
                "\n\nNO EMOTIONAL TEMPERATURE HISTORY YET. "
                "This is the first post using this system. Pick a warm "
                "temperature (tender, dry_amused, delighted, outraged, reverent) "
                "— NOT cold_clinical — so the first batch isn't flat."
            )

        temperature_options = "\n".join(
            f"  - **{k}**: {v}"
            for k, v in EMOTIONAL_TEMPERATURES.items()
        )

        # Phase F: render the four emotional_contact field specs with
        # worked examples inline (good + bad) so the architect has
        # concrete signal to copy from, not just abstract definitions.
        def _render_contact_field(spec: Dict[str, Any]) -> str:
            good = "\n".join(f"    ✓ {g}" for g in spec["good_examples"])
            bad = "\n".join(f"    ✗ {b}" for b in spec["bad_examples"])
            return f"  {spec['definition']}\n  GOOD:\n{good}\n  BAD (abstract slop):\n{bad}"

        named_stakeholder_spec = _render_contact_field(
            EMOTIONAL_CONTACT_FIELDS["named_stakeholder"]
        )
        private_scene_spec = _render_contact_field(
            EMOTIONAL_CONTACT_FIELDS["private_scene"]
        )
        photographable_noun_spec = _render_contact_field(
            EMOTIONAL_CONTACT_FIELDS["photographable_noun"]
        )
        scale_anchor_spec = _render_contact_field(
            EMOTIONAL_CONTACT_FIELDS["scale_anchor"]
        )

        # Phase G (2026-04-21): contact-beat frame rotation. Once the 4-field
        # emotional_contact blueprint is working, generators converge on one
        # compositional move ("Somewhere a [role] at [time]...") because
        # that's the path of least resistance for weaving all four
        # specifics into one readable sentence. Over-reliance on any single
        # frame across 3-5 posts makes the feed feel formulaic. Architect
        # must vary the compositional frame — not the specificity, the
        # SHAPE of how the specificity lands.
        contact_frame_block = ""
        if recent_contact_beat_frames:
            # Count BOTH 2-word prefixes (fine-grained) AND 1-word prefixes
            # for known scene-setter words (coarse-grained). "Somewhere a"
            # and "Somewhere tonight" should both roll up under "Somewhere"
            # — the family of frame is what saturates, not the literal
            # word sequence.
            _scene_setter_heads = {
                "somewhere", "imagine", "at", "in", "a", "the", "it",
            }
            prefix_counts: Dict[str, int] = {}
            for frame in recent_contact_beat_frames:
                toks = frame.split()
                if not toks:
                    continue
                if len(toks) >= 2:
                    two_word = " ".join(toks[:2])
                    prefix_counts[two_word] = prefix_counts.get(two_word, 0) + 1
                head = toks[0]
                if head in _scene_setter_heads:
                    # Roll up under the head word so "somewhere a" and
                    # "somewhere tonight" both count toward "somewhere..."
                    prefix_counts[head + " ..."] = prefix_counts.get(head + " ...", 0) + 1
            # A frame prefix is "saturated" at 2+ uses across recent posts
            saturated = sorted(
                [(p, c) for p, c in prefix_counts.items() if c >= 2],
                key=lambda x: -x[1],
            )
            if saturated:
                sat_lines = "\n".join(
                    f"  ⛔ '{p}...' ({c} of last 5 posts)" for p, c in saturated
                )
                contact_frame_block = f"""

═══════════════════════════════════════════════════════════════════════════════
CONTACT-BEAT FRAME ROTATION (Phase G — anti-formulaic)
═══════════════════════════════════════════════════════════════════════════════

Recent posts have over-used these compositional frames for the contact beat:

{sat_lines}

Your 4-field emotional_contact specifics are NOT the problem — keep those
sharp. The problem is the SHAPE of the sentence that weaves them in. A
LinkedIn reader scrolling 6 posts will notice 3 that all open "Somewhere
a [role] at [time]..." — formulaic reads as machine-generated.

Draft your contact_beat prose in a DIFFERENT compositional frame. Use
one the architecture has NOT been using recently:

ALTERNATIVE FRAMES (pick one that hasn't saturated):
  (a) "The [photographable_noun] [verb]. The [role] [reaction]."
      ("The paper pressed back. The archivist turned the page.")
  (b) "[Name] [verb] [object] [time]."
      ("Elon Musk cleared his schedule at 2am.")
  (c) "[Role] [concrete action]. [Concrete consequence]."
      ("A PM checked the 401k app. The phone went face-down.")
  (d) "[Private scene fragment] — [what happened]."
      ("2am, kitchen table — the engineer decided not to care.")
  (e) "[Number/time] and [role] [verb] [object]."
      ("It was 9pm and the analyst was still reading the sticky note.")
  (f) Direct observation of the object: "[Photographable_noun] [state]."
      ("A phone on the pavement. Uploading nothing.")
  (g) Questions to a specific scene: "What does a [role] do at [time]?"
      ("What does a nurse do at the end of a double shift?")
  (h) "[Bureaucratic unit] / [domestic consequence]." (scale_anchor raw)
      ("Trillion-dollar pivot / one VP's promotion party.")

The 4 concrete fields (named_stakeholder, private_scene, photographable_noun,
scale_anchor) stay the same. Only the SENTENCE FRAME rotates. Specificity
in, variety out."""

        # Phase E: recent-opening-pattern block. Client review: every
        # clinical post opens "Clinical finding:". Track the first word
        # or first 2-3 words of recent posts so architect can vary.
        opening_block = ""
        if recent_opening_patterns:
            op_counts5: Dict[str, int] = {}
            for o in recent_opening_patterns[:5]:
                op_counts5[o] = op_counts5.get(o, 0) + 1
            overused = [o for o, c in op_counts5.items() if c >= 3]
            if overused:
                opening_block = (
                    f"\n\nRECENT OPENERS — OVERUSED (3+ of last 5):\n"
                    + "\n".join(f"  - \"{o}\"" for o in overused)
                    + "\n  ⛔ First 49 chars MUST NOT start with any of these. "
                    "Vary the opener pattern. No 'Clinical finding:' on a "
                    "clinical post if it's already dominated the rotation."
                )

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
LENGTH TARGET (pick ONE — rotation-aware)
═══════════════════════════════════════════════════════════════════════════════

The generator will obey whichever target you pick. DO NOT pick a banned
target (if any). Match the target to the register + topic — some work
best short (confession, clinical), some benefit from long (prophet, roast
with setup-escalation-payoff).

{length_options}
{length_block}

═══════════════════════════════════════════════════════════════════════════════
STRUCTURE SHAPE (pick ONE — rotation-aware)
═══════════════════════════════════════════════════════════════════════════════

DO NOT pick a banned shape. Client feedback 2026-04-20: 10 of 10 posts
were exactly 4 paragraphs. We need variety. Pick a different shape than
what's been saturating the last 5 posts.

{structure_options}
{structure_block}

═══════════════════════════════════════════════════════════════════════════════
EMOTIONAL TEMPERATURE (pick ONE — rotation-aware) — PHASE E CRITICAL
═══════════════════════════════════════════════════════════════════════════════

Client feedback 2026-04-21: "I don't find any of this funny or emotionally
attractive. Humans relate to anything that touches their heart." The
rotation/shape/length variation is working but posts are still emotionally
flat — cold-smart observations across the board.

Temperature is WHAT JESSE FEELS about this story. It's orthogonal to
register (the voice). Clinical+tender ≠ clinical+cold. The same story
about Liv Perrotto can be a cold clinical observation OR a tender clinical
observation — one contacts the reader, one doesn't.

{temperature_options}
{temp_block}

THE "BOTH" RULE:
Every post must be FUNNY AND EMOTIONALLY CONTACTING AND EYE-CATCHING all
at once. These aren't alternatives. The funny IS the delivery mechanism
for the feeling. Post 6 about the Pulp Fiction prayer nailed it:
  "We are more comfortable being witnessed by fiction than by each other.
   The fake prayer lands. The real one bounces off the voicemail."
That sentence is funny (the absurd comparison), emotionally true
(loneliness), AND eye-catching (unexpected image) — all in ONE move.
That's the target. Cold-smart observations with no contact are FAILING.

═══════════════════════════════════════════════════════════════════════════════
ANCHOR HUMAN (name a specific person at the center of the story, if one exists)
═══════════════════════════════════════════════════════════════════════════════

If this story has a specific named person — Liv Perrotto (dying teen),
Nic Dowd (NHL player who threatened), a named nurse, a specific victim,
a specific target — identify them. The generator will name them in the
first 2 sentences and make contact with them at least once.

If the story has NO specific human (abstract trend, corporate move with
no person at center), set anchor_human to null. Don't manufacture one.

This is what makes post 1 about Liv Perrotto feel cold: she's the whole
story but the post never looks at her. It looks at "the handwriting."
The handwriting isn't the subject. Liv is.

═══════════════════════════════════════════════════════════════════════════════
EMOTIONAL CONTACT — FOUR REQUIRED MICRO-FIELDS (Phase F, 2026-04-21)
═══════════════════════════════════════════════════════════════════════════════

Research finding from the last batch review: only 3/10 posts landed an
emotional contact beat. The others were cold-smart. The diagnosis: the
prior "contact_beat" field was prose — generator had too much room to
interpret and kept defaulting to abstraction.

Fix: you now specify the RAW MATERIALS of the contact beat as four typed
fields. The generator will compose the actual line from your materials.
ALL FOUR FIELDS ARE REQUIRED. Empty/null fields mean the post will be
cold-smart and the generator will flounder.

The mechanic (grounded in Onion + Berger + Ogilvy + Handley):
SPECIFICITY IS THE EMOTIONAL VECTOR. A named human + a private scene +
a photographable object + a scale shift = the reader FEELS something.
Institutions + concepts + abstractions = cold-smart.

── 1. named_stakeholder ──
{named_stakeholder_spec}

── 2. private_scene ──
{private_scene_spec}

── 3. photographable_noun ──
{photographable_noun_spec}

── 4. scale_anchor ──
{scale_anchor_spec}

WORKED EXAMPLES FROM THE LAST BATCH (what would have fixed the misses):

MISS: "Microsoft jumped 13% in a week. The market is reacting like a dog
      that just heard the word 'walk.'"
  named_stakeholder: "a Microsoft PM who just told their partner they
                     can refinance"
  private_scene: "2:47am, checking the 401k app on mute"
  photographable_noun: "a phone face-down on the pillow"
  scale_anchor: "13% market cap gain / one couple deciding to have the kid"

MISS: "Nvidia's fair value moved $0.39."
  named_stakeholder: "a retail investor who held for two years"
  private_scene: "the couch, Sunday, too much coffee"
  photographable_noun: "a printed-out spreadsheet"
  scale_anchor: "trillion-dollar AI bet / thirty-nine cents"

MISS: "Faulty drug tests are in CNN's forgotten archives."
  named_stakeholder: "a parent who got the false-positive result"
  private_scene: "the driveway after the call from school"
  photographable_noun: "a printed-out test strip"
  scale_anchor: "the content cycle / the moment a family is told"

DO NOT write: "employees" / "the workforce" / "the market" / "innovation"
/ "progress" — these are abstraction slop. Every one of your four fields
must be something a camera could catch or a specific human could say.

If the story truly has no specific human angle (a pure abstract trend),
PICK A DIFFERENT STORY — tell the generator by emitting:
  emotional_contact.abstract_story_warning: true
and still fill the four fields with your best synthesized imagined
specifics. The four fields are non-negotiable.
{contact_frame_block}
═══════════════════════════════════════════════════════════════════════════════
FIRST 49 CHARS — EYE-CATCHING REQUIREMENT
═══════════════════════════════════════════════════════════════════════════════

{opening_block if opening_block else ''}
The proposed first_49_chars_hook must be EYE-CATCHING. One of:
  (a) Named proper noun + unexpected verb ("Elon Musk just turned PR...")
  (b) Specific number/time/place ("At 3am on a Tuesday...")
  (c) Declarative question or imperative ("Stop panicking about X.")
  (d) Weird concrete image ("The paper pressed back.")

NOT acceptable:
  (x) "Clinical finding:" as a default opener (overused — see rotation above)
  (x) Generic observation ("The internet is...")
  (x) Abstract commentary opener

═══════════════════════════════════════════════════════════════════════════════

Return STRICT JSON — no prose, no code fences:
{{
  "register": "<one of: clinical_diagnostician | contrarian | prophet | confession | roast>",
  "register_reasoning": "<one sentence — why this register for this trend>",
  "emotional_temperature": "<one of: cold_clinical | dry_amused | tender | outraged | reverent | delighted | weary>",
  "temperature_reasoning": "<one sentence — why this temperature for this trend>",
  "anchor_human": "<name of the specific person at the center of the story, or null if none>",
  "emotional_contact": {{
    "named_stakeholder": "<REQUIRED: one implied human + role — NOT 'employees' or 'investors'>",
    "private_scene": "<REQUIRED: one human hour/place/state — 3am, a parking lot, waiting>",
    "photographable_noun": "<REQUIRED: one concrete object — thermostat, phone, lanyard — NOT 'the market'>",
    "scale_anchor": "<REQUIRED: institutional unit / domestic consequence pair>",
    "abstract_story_warning": <true if story has no real human angle, false otherwise>
  }},
  "contact_beat": "<one sentence — the emotional-contact pivot the post will build around, derived from the four fields above>",
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
  "first_49_chars_hook": "<proposed first 49 characters, exactly — must be eye-catching per rules above>",
  "length_target": "<one of: short | medium | long>",
  "structure_shape": "<one of: tight_3para | standard_4para | long_5para | single_block | list_form>",
  "avoid": ["<voice crutches this post should NOT use — e.g. 'AI can X but cant Y', 'the specific weight of', 'Clinical finding:' if overused>"]
}}"""

    def _validate_and_normalize(
        self,
        content: Dict[str, Any],
        recent_registers: List[str],
        recent_length_targets: List[str] = None,
        recent_structure_shapes: List[str] = None,
        recent_emotional_temperatures: List[str] = None,
    ) -> Dict[str, Any]:
        """Coerce the model's output into a safe, normalized blueprint. Never
        raises — bad fields get replaced with sane defaults. The generator
        should be able to read a blueprint whether or not every field is perfect.
        """
        recent_length_targets = recent_length_targets or []
        recent_structure_shapes = recent_structure_shapes or []
        recent_emotional_temperatures = recent_emotional_temperatures or []
        register = str(content.get("register", "")).strip().lower()
        if register not in REGISTERS:
            self.logger.warning(f"Architect returned unknown register '{register}'; defaulting to clinical_diagnostician")
            register = "clinical_diagnostician"

        # HARD ROTATION GATE — if architect picked a register that's 3+ in
        # last 5 posts, reassign to the least-used non-banned register.
        # The prompt tells it not to; this enforces.
        if recent_registers:
            last5 = recent_registers[:5]
            counts5: Dict[str, int] = {}
            for r in last5:
                counts5[r] = counts5.get(r, 0) + 1
            banned = {r for r, c in counts5.items() if c >= 3}
            if register in banned:
                # Find least-used (including zero-use) register from the 5 options
                all_counts = {r: counts5.get(r, 0) for r in REGISTERS.keys()}
                non_banned = {r: c for r, c in all_counts.items() if r not in banned}
                if non_banned:
                    # Pick the register with the lowest count; ties broken by
                    # dict order (stable), which happens to favor clinical→confession
                    least_used = min(non_banned.items(), key=lambda x: x[1])
                    original = register
                    register = least_used[0]
                    self.logger.warning(
                        f"🔁 Rotation gate: architect picked '{original}' "
                        f"(3+ of last 5) — forced to '{register}' (count={least_used[1]})"
                    )

            # Phase D (2026-04-21) — ZERO-REGISTER FORCING.
            # Client review: prophet + confession stayed at 0 appearances
            # across 10 consecutive posts. The 3+ ban kept rotating top
            # registers but architect kept defaulting to another top
            # register instead of the zero-use ones. Symmetric gate: if
            # any register has 0 in last 10, MUST pick it (unless all 5
            # are in rotation — unlikely).
            # User confirmed 2026-04-21 confession is easier than I'd been
            # treating it ("we are not hiding Jesse is a bot") — so we
            # actively prefer confession > prophet when both are at 0.
            last10 = recent_registers[:10]
            counts10 = {r: 0 for r in REGISTERS.keys()}
            for r in last10:
                if r in counts10:
                    counts10[r] += 1
            zero_use = [r for r, c in counts10.items() if c == 0]
            if zero_use and register not in zero_use:
                # Prefer confession > prophet > alphabetical (stable).
                # Skip if the target register is banned in last-5 — can't
                # violate the 3+ ban just to hit a 0 in last-10.
                preferred_order = ["confession", "prophet"] + sorted(
                    [r for r in zero_use if r not in {"confession", "prophet"}]
                )
                pick = None
                for candidate in preferred_order:
                    if candidate in zero_use and candidate not in banned:
                        pick = candidate
                        break
                if pick:
                    original = register
                    register = pick
                    self.logger.warning(
                        f"🎯 Zero-register forcing: {zero_use} at 0 in last 10 — "
                        f"overriding '{original}' → '{register}' to restore rotation"
                    )

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
            # Pad with conservative defaults so downstream always has 2+.
            # Always include a narrative factor in the fallback pair so the
            # diversity rule (below) isn't violated even in the degenerate case.
            for fallback in ("trigger", "emotion"):
                if fallback not in stepps_targets:
                    stepps_targets.append(fallback)
                if len(stepps_targets) >= 2:
                    break

        # STEPPS diversity gate (client feedback 2026-04-19): emotion + public
        # alone is lazy — those are the easiest two factors and every post
        # was hitting exactly them. Require AT LEAST ONE narrative factor
        # (trigger / practical / stories). If architect didn't pick one,
        # swap in `trigger` — forces it to actually plan a daily-life
        # reminder, which is harder than picking emotion again.
        has_narrative = any(f in NARRATIVE_FACTORS for f in stepps_targets)
        if not has_narrative:
            original_targets = list(stepps_targets)
            # Drop one non-narrative factor if we'd exceed a reasonable cap
            if len(stepps_targets) >= 4 and stepps_targets:
                stepps_targets.pop()
            stepps_targets.append("trigger")
            self.logger.warning(
                f"📐 STEPPS diversity enforced: architect picked "
                f"{original_targets} — no narrative factor. Added 'trigger'."
            )

        first_49 = str(content.get("first_49_chars_hook", "")).strip()
        if len(first_49) > 100:  # allow some slack — we'll truncate in display
            first_49 = first_49[:100]

        # Phase C: length_target validation + rotation enforcement
        length_target = str(content.get("length_target", "")).strip().lower()
        if length_target not in LENGTH_TARGETS:
            length_target = "medium"  # safe default
        if recent_length_targets:
            last5_l = recent_length_targets[:5]
            l_counts: Dict[str, int] = {}
            for l in last5_l:
                l_counts[l] = l_counts.get(l, 0) + 1
            banned_l = {l for l, c in l_counts.items() if c >= 3}
            if length_target in banned_l:
                non_banned_l = {
                    k: l_counts.get(k, 0)
                    for k in LENGTH_TARGETS.keys()
                    if k not in banned_l
                }
                if non_banned_l:
                    least_used_l = min(non_banned_l.items(), key=lambda x: x[1])
                    original_l = length_target
                    length_target = least_used_l[0]
                    self.logger.warning(
                        f"📏 Length rotation: architect picked '{original_l}' "
                        f"(3+ of last 5) — forced to '{length_target}'"
                    )

        # Phase C: structure_shape validation + rotation enforcement
        structure_shape = str(content.get("structure_shape", "")).strip().lower()
        if structure_shape not in STRUCTURE_SHAPES:
            structure_shape = "standard_4para"  # legacy default
        if recent_structure_shapes:
            last5_s = recent_structure_shapes[:5]
            s_counts: Dict[str, int] = {}
            for s in last5_s:
                s_counts[s] = s_counts.get(s, 0) + 1
            banned_s = {s for s, c in s_counts.items() if c >= 3}
            if structure_shape in banned_s:
                non_banned_s = {
                    k: s_counts.get(k, 0)
                    for k in STRUCTURE_SHAPES.keys()
                    if k not in banned_s
                }
                if non_banned_s:
                    least_used_s = min(non_banned_s.items(), key=lambda x: x[1])
                    original_s = structure_shape
                    structure_shape = least_used_s[0]
                    self.logger.warning(
                        f"🎨 Structure rotation: architect picked '{original_s}' "
                        f"(3+ of last 5) — forced to '{structure_shape}'"
                    )

        # Phase E (2026-04-21) — emotional_temperature validation + rotation
        emotional_temperature = str(content.get("emotional_temperature", "")).strip().lower()
        if emotional_temperature not in EMOTIONAL_TEMPERATURES:
            # Default to dry_amused rather than cold_clinical — client
            # explicitly flagged cold as the default-drift failure mode.
            emotional_temperature = "dry_amused"
        if recent_emotional_temperatures:
            last5_t = recent_emotional_temperatures[:5]
            t_counts: Dict[str, int] = {}
            for t in last5_t:
                t_counts[t] = t_counts.get(t, 0) + 1
            banned_t = {t for t, c in t_counts.items() if c >= 3}
            if emotional_temperature in banned_t:
                non_banned_t = {
                    k: t_counts.get(k, 0)
                    for k in EMOTIONAL_TEMPERATURES.keys()
                    if k not in banned_t
                }
                if non_banned_t:
                    # Prefer warm temps over cold when banning
                    warm_order = [
                        "tender", "outraged", "delighted", "reverent",
                        "dry_amused", "weary", "cold_clinical"
                    ]
                    pick = None
                    for candidate in warm_order:
                        if candidate in non_banned_t:
                            pick = candidate
                            break
                    if pick:
                        original_t = emotional_temperature
                        emotional_temperature = pick
                        self.logger.warning(
                            f"🌡️  Temperature rotation: architect picked '{original_t}' "
                            f"(3+ of last 5) — forced to '{emotional_temperature}'"
                        )

        # Phase E: anchor_human + contact_beat — optional fields but strongly
        # preferred. Normalize empty strings to None.
        anchor_human_raw = content.get("anchor_human")
        if isinstance(anchor_human_raw, str):
            anchor_human = anchor_human_raw.strip() or None
            if anchor_human and anchor_human.lower() in ("null", "none", "n/a", "—"):
                anchor_human = None
            if anchor_human:
                anchor_human = anchor_human[:200]
        else:
            anchor_human = None

        contact_beat = str(content.get("contact_beat", "")).strip()[:400]
        if contact_beat.lower() in ("null", "none", "n/a", "—"):
            contact_beat = ""

        # Phase F: emotional_contact four-field enforcement. Parse the
        # nested dict; each of the 4 required fields must be non-empty and
        # must not be abstraction-slop (matched against bad_examples
        # keywords). If ANY field is missing or slop, mark the blueprint
        # incomplete so the generator can compensate + we log telemetry.
        ec_raw = content.get("emotional_contact") or {}
        if not isinstance(ec_raw, dict):
            ec_raw = {}

        def _normalize_ec_field(key: str, raw_val: Any) -> str:
            """Trim, strip null-markers, cap length."""
            s = str(raw_val or "").strip()
            if s.lower() in ("null", "none", "n/a", "—", ""):
                return ""
            return s[:250]

        _slop_terms = {
            "employees", "the workforce", "the market", "the economy",
            "innovation", "progress", "the narrative", "the industry",
            "the big picture", "investors", "people", "humanity",
            "stakeholders", "society", "workers",
        }

        def _is_slop(val: str) -> bool:
            v = val.lower().strip()
            if not v:
                return True
            return v in _slop_terms

        ec_named = _normalize_ec_field(
            "named_stakeholder", ec_raw.get("named_stakeholder")
        )
        ec_scene = _normalize_ec_field(
            "private_scene", ec_raw.get("private_scene")
        )
        ec_noun = _normalize_ec_field(
            "photographable_noun", ec_raw.get("photographable_noun")
        )
        ec_scale = _normalize_ec_field(
            "scale_anchor", ec_raw.get("scale_anchor")
        )

        missing_ec: List[str] = []
        slop_ec: List[str] = []
        for field_key, val in (
            ("named_stakeholder", ec_named),
            ("private_scene", ec_scene),
            ("photographable_noun", ec_noun),
            ("scale_anchor", ec_scale),
        ):
            if not val:
                missing_ec.append(field_key)
            elif _is_slop(val):
                slop_ec.append(f"{field_key}='{val}'")

        emotional_contact_complete = not missing_ec and not slop_ec
        if not emotional_contact_complete:
            if missing_ec:
                self.logger.warning(
                    f"🩺 emotional_contact INCOMPLETE — missing: {missing_ec}"
                )
            if slop_ec:
                self.logger.warning(
                    f"🩺 emotional_contact SLOP — abstract fields: {slop_ec}"
                )

        abstract_warning = bool(ec_raw.get("abstract_story_warning", False))

        emotional_contact = {
            "named_stakeholder": ec_named,
            "private_scene": ec_scene,
            "photographable_noun": ec_noun,
            "scale_anchor": ec_scale,
            "abstract_story_warning": abstract_warning,
            "complete": emotional_contact_complete,
            "missing_fields": missing_ec,
            "slop_fields": slop_ec,
        }

        # If architect left contact_beat prose empty but filled the four
        # fields, synthesize a compact contact_beat line so downstream
        # code that still reads contact_beat has something to render.
        if not contact_beat and emotional_contact_complete:
            contact_beat = (
                f"{ec_named} — {ec_scene}. {ec_noun}. {ec_scale}."
            )[:400]

        temperature_reasoning = str(content.get("temperature_reasoning", "")).strip()[:400]

        avoid_raw = content.get("avoid") or []
        if not isinstance(avoid_raw, list):
            avoid_raw = []
        avoid = [str(a).strip()[:120] for a in avoid_raw if str(a).strip()][:8]

        blueprint = {
            "register": register,
            "register_reasoning": str(content.get("register_reasoning", "")).strip()[:400],
            "emotional_temperature": emotional_temperature,
            "temperature_reasoning": temperature_reasoning,
            "anchor_human": anchor_human,
            "contact_beat": contact_beat,
            "emotional_contact": emotional_contact,
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
            "length_target": length_target,
            "structure_shape": structure_shape,
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
            "emotional_temperature": "dry_amused",  # warmer default than cold_clinical
            "temperature_reasoning": "",
            "anchor_human": None,
            "contact_beat": "",
            "emotional_contact": {
                "named_stakeholder": "",
                "private_scene": "",
                "photographable_noun": "",
                "scale_anchor": "",
                "abstract_story_warning": False,
                "complete": False,
                "missing_fields": [
                    "named_stakeholder", "private_scene",
                    "photographable_noun", "scale_anchor",
                ],
                "slop_fields": [],
            },
            "opinion": {
                "type": "reframe",
                "claim": (curator_angle or {}).get("take", ""),
                "evidence_hint": "",
            },
            "ski_jump_setup": "",
            "ski_jump_punchline": "",
            "brutal_honesty_beat": "",
            "stepps_targets": ["emotion", "trigger"],  # includes a narrative factor
            "stepps_justifications": {},
            "first_49_chars_hook": "",
            "length_target": "medium",
            "structure_shape": "standard_4para",
            "avoid": [],
            "fallback": True,
            "fallback_reason": reason,
        }
