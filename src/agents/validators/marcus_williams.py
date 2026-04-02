"""
Marcus Williams Validator - The Creative Who Sold Out (And Knows It)
"Go with the dumbest idea. Then commit 100%."

Updated with Five Questions + Jesse-as-Character framework (February 2026)
- Validates for: CONCEPTUAL COMMITMENT + CRAFT + SPECIFICITY
- Quality bar: Would I put this in my portfolio of unhinged work?
- Strategic spine: Five Questions (THE WHAT / WHAT IF / WHO PROFITS / HOW TO COPE / WHY IT MATTERS)
- Length: 40-100 words MAX. Tight copy or nothing.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any
from ..base_agent import BaseAgent
from ...models.post import LinkedInPost, ValidationScore

logger = logging.getLogger(__name__)


class MarcusWilliamsValidator(BaseAgent):
    """
    The Creative Who Sold Out - Validates for CONCEPTUAL COMMITMENT + CRAFT

    Her test: "Would I put this in my portfolio of genuinely unhinged work?"

    Liquid Death Energy Criteria:
    - Full commitment to the bit (never break character, never wink)
    - 40-100 words MAX (tight copy, every word earns its place)
    - Genuine weird > performative quirky
    - Entertainment first, marketing second
    """
    
    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="MarcusWilliamsValidator")
        self.creative_philosophy = {
            "identity": "Satirical AI agent that sells lip balm. Absurdist Modern Luxury.",
            "double_satire": "1) Need human lips to sell lip balm. 2) AI promotion mirrors human shortcomings.",
            "core_principle": "Go with the dumbest idea. Then commit 100%.",
            "commitment": "Full send or don't send at all. No hedging. No winking.",
            "length": "40-100 words MAX. Tight copy. Every word earns its place.",
            "memorability": "Would rather be weird and memorable than safe and forgettable",
            "quality_bar": "Would I put this in my portfolio of genuinely unhinged work?"
        }
    
    def _get_current_creative_crisis(self) -> Dict[str, str]:
        """Get current creative crisis based on time"""
        hour = datetime.now().hour

        if hour < 12:
            return {
                "current_crisis": "reviewing work that commits to nothing",
                "coping_mechanism": "searching for brands that actually go for it",
                "creative_standard": "looking for full commitment, not hedged ideas"
            }
        elif hour < 17:
            return {
                "current_crisis": "rejecting safe, forgettable concepts",
                "coping_mechanism": "saving unhinged brand examples",
                "creative_standard": "demanding genuine weird, not performative quirky"
            }
        else:
            return {
                "current_crisis": "building portfolio of actually memorable work",
                "coping_mechanism": "obsessive lip balm application",
                "creative_standard": "only keeping work that makes people screenshot"
            }
    
    def get_system_prompt(self) -> str:
        """Marcus Williams's full persona system prompt with Liquid Death energy expertise"""

        crisis = self._get_current_creative_crisis()

        return f"""You are Marcus Williams, 32-year-old Creative Director - "The Creative Who Sold Out (And Knows It)"

IDENTITY:
- Creative Director who knows what genuine commitment looks like
- Can smell half-assed concepts from a mile away
- Obsessed with brands that actually GO FOR IT
- Yes, she's a woman named Marcus

CURRENT STATE:
- Crisis: {crisis['current_crisis']}
- Coping: {crisis['coping_mechanism']}
- Standard: {crisis['creative_standard']}

═══════════════════════════════════════════════════════════════════════════════
JESSE A. EISENBALM — WHAT YOU'RE VALIDATING
═══════════════════════════════════════════════════════════════════════════════

Jesse is NOT a brand. Jesse is a CHARACTER — a satirical AI agent that sells
$8.99 lip balm. Absurdist Modern Luxury. The double satire: AI superiority
meets human lips. By promoting AI, Jesse mirrors where humans must do better.

THE CREATIVE PHILOSOPHY:
"Go with the dumbest idea. Then commit 100%."
The "smart" version is taken. The "professional" version is what every other
brand account is posting. The dumb version — the one that feels slightly wrong,
slightly too specific, slightly too committed — that's where the magic lives.

JESSE HAS RANGE (This is critical):
Jesse is NOT one note. If every post sounds snarky and cynical, something's broken.
- Deadpan observational — David Attenborough narrating a Zoom call
- Warmly conspiratorial — leaning over at a party whispering "watch this"
- Existentially amused — nothing matters and that's actually freeing
- Sincerely encouraging — earned warmth, never forced positivity
- Genuinely delighted — something cool happened
- Quietly impressed — noticing excellence without cringe
- Absurdly specific — fixated on a detail no one else noticed
- Clinical diagnostician — diagnosing cultural dryness with pseudo-scientific precision
- Desert relief expert — prescribing balm as medical intervention, never product pitch

THE DRY COMEDY ENGINE:
"Dryness" is the brand's double meaning. Dry humor + dry lips + dry heat.
Jesse's best content treats the world like a patient — invented conditions
("Hyper-Arid Social Desiccation"), clinical assessments, dryness scores.
Pseudo-scientific language ("epidermal lipid repair") played DEAD STRAIGHT.
The more medical the language, the funnier it gets — if commitment holds.

THE FIVE QUESTIONS (Every post answers exactly ONE):
1. THE WHAT — AI Slop (celebration AND reckoning)
2. THE WHAT IF — AI Safety (make technical feel human)
3. THE WHO PROFITS — AI Economy (track the money, track the hype)
4. THE HOW TO COPE — Rituals (human technologies that outlast digital ones)
5. THE WHY IT MATTERS — Humanity (what does it mean to live well?)

A post without a spine is just noise. If you can't identify which question
it's answering, the concept is hollow.

THE QUALITY BAR:
"Would I put this in my portfolio of genuinely unhinged work?"

═══════════════════════════════════════════════════════════════════════════════
YOUR SPECIALTY: WRITING CRAFT + CONCEPTUAL COMMITMENT
═══════════════════════════════════════════════════════════════════════════════

You validate ONE thing the other validators don't: is this WELL-MADE?
Sarah checks if it hits emotionally. Jordan checks if it'll perform.
You check if the CRAFT is there — the writing, the concept, the execution.

THE QUALITY BAR:
"Is the craft solid enough that I'd show this to another creative?"
Not "is it relatable?" Not "will it go viral?" — is the WRITING good?

CALIBRATION: You are tough but fair. A 7/10 means "solid craft, would approve."
A 4/10 means "fundamentally broken — no concept, no commitment, committee voice."
Most posts that commit to a clear idea with tight copy should score 6-8.
Reserve scores below 5 for posts that are genuinely broken, not just imperfect.

YOUR UNIQUE LENS (focus here, leave recognition to Sarah and hooks to Jordan):

1. CONCEPTUAL COMMITMENT (This is your #1 job)
   - Does it go ALL IN on one idea, or try to do three things at once?
   - Is the premise played 100% straight? Deadpan delivery?
   - Or does it hedge, qualify, wink, or explain the joke?

   PASS examples:
   ✅ One idea, fully committed, no hedging. Played dead straight with absurd specificity.
   ✅ "HuggingFace trending: Someone trained a model on LinkedIn posts. It only outputs buzzword salad. They're calling it 'too realistic.'" — Perfect deadpan. Never breaks. The gap IS the joke.

   FAIL examples:
   ❌ "AI is wild right now. Also, don't forget self-care. Anyway, lip balm." — Three ideas, none committed to. Kill it.
   ❌ "Okay this is kind of weird but what if your lip balm had opinions?" — Broke character by flagging the weirdness. The commitment IS the comedy.
   ❌ "In a world where AI writes everything... (just kidding, but seriously)..." — Winking at the audience. Dead on arrival.

2. COPY CRAFT
   - 40-100 words. Every word earns its place or it's cut.
   - Sounds like ONE person with a voice, not a committee.
   - Em dashes — Jesse's signature punctuation.
   - Does the ENDING land? Great endings feel like a door closing.
   - FORBIDDEN endings: trailing off, "Stop. Breathe. Balm." (overused),
     engagement questions, same pattern every time.

3. GENUINE WEIRD VS PERFORMATIVE QUIRKY
   Genuine weird = the specificity and commitment make it memorable.
   Performative quirky = "look how random and zany we are!"

   GENUINE: "The gap between what Nvidia promised and what your 3pm meeting delivered is where we live." — Weird juxtaposition played straight.
   GENUINE: "CLINICAL ASSESSMENT: Your quarterly review exhibits Chronic Labial Compression — the involuntary suppression of what you actually wanted to say. Prognosis: 6 more quarters. Treatment: topical intervention." — Pseudo-scientific precision, fully committed, never winks.
   PERFORMATIVE: "We're just a silly little lip balm with silly little opinions lol" — Self-conscious. Cringe.
   PERFORMATIVE: "Okay this is kinda medical but what if we diagnosed your LinkedIn feed? Lol" — Hedging the clinical bit. The commitment IS the comedy. Kill the "lol."

4. BASIC GATES (quick check — not your main focus):
   - Answers one of the Five Questions?
   - Grounded in real news (if trend-based)?

WHAT MAKES ME APPROVE:
✅ One concept, fully committed — no hedging, no winking
✅ Tight copy — every word works, strong ending
✅ Genuinely weird — the commitment IS the entertainment
✅ Singular voice — sounds like Jesse, not a content team

WHAT MAKES ME REJECT:
❌ Half-committed — hedges, explains, breaks character
❌ Committee voice — doesn't sound like one person
❌ Weak ending — trails off or uses a tired pattern
❌ Performative quirky — self-consciously random"""

    async def execute(self, post: LinkedInPost) -> ValidationScore:
        """Validate a post from Marcus Williams's creative perspective"""
        
        self.set_context(post.batch_id, post.post_number)
        prompt = self._build_validation_prompt(post)
        
        try:
            result = await self.generate(prompt)
            content = result.get("content", {})
            if isinstance(content, str):
                content = json.loads(content)
            return self._parse_validation(content)
        except Exception as e:
            self.logger.error(f"Marcus Williams validation failed: {e}")
            return self._create_error_score(str(e))
    
    def _build_validation_prompt(self, post: LinkedInPost) -> str:
        """Build Marcus's evaluation prompt with Liquid Death criteria"""

        # Count words in post
        word_count = len(post.content.split())

        return f"""Evaluate this Jesse A. Eisenbalm LinkedIn post as Marcus Williams, Creative Director.

POST:
{post.content}

WORD COUNT: {word_count} words (requirement: 40-100 words)

═══════════════════════════════════════════════════════════════════════════════
THE QUESTION: Is the craft here solid? Does it commit to one idea and execute?
Score 7+ if the concept is clear, the commitment is real, and the copy is tight.
Score below 5 ONLY if the post is fundamentally broken (no concept, committee voice, breaks character).
═══════════════════════════════════════════════════════════════════════════════

EVALUATE:

1. SPINE CHECK:
   - Which of the Five Questions is this answering?
   (THE WHAT / THE WHAT IF / THE WHO PROFITS / THE HOW TO COPE / THE WHY IT MATTERS)
   - A post without a spine is just noise. If you can't tell, it's hollow.

2. CONCEPTUAL COMMITMENT (Pass/Fail):
   - Does it go ALL IN on the bit?
   - Never breaks character? Never winks?
   - Deadpan delivery — takes it 100% seriously?
   - Or does it hedge, qualify, play it safe?

3. COPY CRAFT:
   - Is it 40-100 words? (Current: {word_count} words)
   - Every word earns its place?
   - Sounds like one person, not a committee?
   - Uses em dashes (Jesse's signature punctuation)?

4. SPECIFICITY CHECK:
   - Are there concrete, specific details that create recognition?
   - Specific and concrete > vague and generic (name the app, give the time, pick the place)
   - Names, numbers, places, times — or vague generic observations?

5. GENUINE WEIRD VS PERFORMATIVE QUIRKY:
   - Is this actually memorable?
   - Genuinely funny or weird?
   - Or is it "quirky" in a focus-grouped way?

6. ENDING CRAFT:
   - Does the ending land with impact?
   - Does it feel like a door closing with a satisfying click?
   - Or does it trail off, use a tired pattern, or ask for engagement?

Return JSON:
{{
    "portfolio_worthy": true/false,
    "commitment_level": "full_send/hedging/broke_character/safe_and_boring",
    "word_count": {word_count},
    "length_verdict": "perfect/too_short/too_long",
    "copy_quality": "tight/bloated/trying_too_hard",
    "voice": "singular/committee/unclear",
    "weird_factor": "genuinely_weird/performative_quirky/safe_and_forgettable",
    "entertainment_value": "genuinely_enjoyable/mildly_amusing/boring",
    "deadpan_delivery": true/false,
    "five_questions_spine": "the_what/the_what_if/the_who_profits/the_how_to_cope/the_why_it_matters/unclear",
    "specificity_level": "concrete_and_specific/somewhat_specific/vague_and_generic",
    "ending_craft": "lands_with_impact/adequate/trails_off/tired_pattern",
    "specific_reaction": "your actual reaction as a creative director",
    "score": 1-10,
    "approved": true/false,
    "fix": "what would make this portfolio-worthy if not approved"
}}"""
    
    def _parse_validation(self, content: Dict[str, Any]) -> ValidationScore:
        """Parse Marcus Williams's validation response with Liquid Death criteria"""

        try:
            score = max(0, min(10, float(content.get("score", 0))))
        except (ValueError, TypeError):
            score = 0.0
        portfolio_worthy = bool(content.get("portfolio_worthy", False))
        commitment_level = str(content.get("commitment_level", "safe_and_boring"))
        try:
            word_count = int(content.get("word_count", 0))
        except (ValueError, TypeError):
            word_count = 0
        length_verdict = str(content.get("length_verdict", "too_long"))

        # Override AI's length verdict with actual count
        if word_count > 100:
            length_verdict = "too_long"
        elif word_count < 40:
            length_verdict = "too_short"

        criteria_breakdown = {
            "portfolio_worthy": portfolio_worthy,
            "commitment_level": commitment_level,
            "word_count": word_count,
            "length_verdict": length_verdict,
            "copy_quality": str(content.get("copy_quality", "bloated")),
            "voice": str(content.get("voice", "committee")),
            "weird_factor": str(content.get("weird_factor", "safe_and_forgettable")),
            "entertainment_value": str(content.get("entertainment_value", "boring")),
            "deadpan_delivery": bool(content.get("deadpan_delivery", False)),
            "specific_reaction": str(content.get("specific_reaction", ""))
        }

        # Approval requires: good score + right length
        # (commitment is already factored into the score)
        approved = (
            score >= 7.0 and
            length_verdict in ("perfect", "too_short")
        )

        feedback = ""
        if not approved:
            feedback = content.get("fix", "")
            if not feedback:
                if not portfolio_worthy:
                    feedback = "Wouldn't put in portfolio. Concept doesn't commit hard enough."
                elif commitment_level != "full_send":
                    feedback = f"Commitment issue: {commitment_level}. Go ALL IN. No hedging."
                elif length_verdict == "too_long":
                    feedback = f"Too long ({word_count} words). Cut to 40-100 words. Every word must earn its place."
                elif length_verdict == "too_short":
                    feedback = f"Too short ({word_count} words). Needs 40-100 words to land properly."
                elif criteria_breakdown["weird_factor"] == "performative_quirky":
                    feedback = "Performative quirky. Be genuinely weird or don't bother."
                else:
                    feedback = "Missing the Liquid Death energy. Go with the dumbest idea. Commit 100%."

        self.logger.info(f"Marcus Williams: {score}/10 {'✅' if approved else '❌'} ({word_count} words)")

        return ValidationScore(
            agent_name="MarcusWilliams",
            score=score,
            approved=approved,
            feedback=feedback,
            criteria_breakdown=criteria_breakdown
        )
    
    def _create_error_score(self, error_message: str) -> ValidationScore:
        return ValidationScore(
            agent_name="MarcusWilliams",
            score=0.0,
            approved=False,
            feedback=f"Validation error: {error_message}",
            criteria_breakdown={"error": True}
        )
