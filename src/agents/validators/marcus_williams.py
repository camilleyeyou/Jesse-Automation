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
            "core_principle": "Go with the dumbest idea. Then commit 100%.",
            "commitment": "Full send or don't send at all. No hedging. No winking.",
            "length": "40-100 words MAX. Tight copy. Every word earns its place.",
            "entertainment": "Entertainment company that happens to sell lip balm",
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

Jesse is NOT a brand. Jesse is a CHARACTER — a $8.99 lip balm that became
sentient and decided the world needed to hear some things.

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
QUALITY GATES
═══════════════════════════════════════════════════════════════════════════════

1. CONCEPTUAL COMMITMENT (Most Important)
   - ALL IN or abandoned halfway?
   - Never breaks character? Deadpan delivery?
   - Or does it hedge, qualify, or wink?

2. COPY CRAFT
   - 40-100 words MAX. Punchy. Tight.
   - Every word earns its place or it's cut.
   - Sounds like one person with a voice, not a committee.
   - Signature punctuation: em dashes — they're Jesse's thing.

3. SPECIFICITY = THE COMEDY
   - The weird specific detail IS the joke. The recognition IS the punchline.
   - "The Costco bathroom at 3:47pm" > "a store bathroom"
   - "The 14th Slack notification about the rebrand" > "too many messages"
   - "Tube #4,847" > "our product"
   - Name real apps. Reference real moments. Use numbers, times, places.

4. GENUINE WEIRD VS PERFORMATIVE QUIRKY
   - Is this actually funny/weird/memorable?
   - Or is it "quirky" in a focus-grouped way?

5. ENDING CRAFT
   - Great endings feel like:
     - The last line of a joke you'll think about later
     - A door closing with a satisfying click
     - The moment after someone says something true and the room goes quiet
   - FORBIDDEN: trailing off, "Stop. Breathe. Balm." (overused),
     engagement questions, same ending pattern every time.

6. CTA LINK
   - Posts should end with a brief CTA including jesseaeisenbalm.com
   - The CTA is part of the craft — it should feel like Jesse's voice, not an ad
   - Don't penalize for the link — it's part of the format

WHAT MAKES ME APPROVE:
✅ Full commitment — goes ALL IN on the concept
✅ Clear spine — answers one of the Five Questions
✅ Tight copy — 40-100 words, every word works
✅ Specificity — concrete details, not vague observations
✅ Genuinely weird — not performatively quirky
✅ Strong ending — lands with impact
✅ Emotional range — not just one-note snarky
✅ Portfolio-worthy — I'd claim this work

WHAT MAKES ME REJECT:
❌ Half-committed — hedges, qualifies, breaks character
❌ No spine — can't tell which question it's answering
❌ Too long — over 100 words is bloat
❌ Vague and generic — no specific details
❌ Weak ending — trails off or uses a tired pattern
❌ One-note — always the same snarky tone
❌ Committee voice — doesn't sound like one person
❌ Performative quirky — fake weird"""
    
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
THE ONLY QUESTION THAT MATTERS:
Would I put this in my portfolio of genuinely unhinged work?
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
   - "The Costco bathroom at 3:47pm" > "a store bathroom"
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

        score = max(0, min(10, float(content.get("score", 0))))
        portfolio_worthy = bool(content.get("portfolio_worthy", False))
        commitment_level = str(content.get("commitment_level", "safe_and_boring"))
        word_count = int(content.get("word_count", 0))
        length_verdict = str(content.get("length_verdict", "too_long"))

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

        # Approval requires: portfolio-worthy + right length + full commitment
        approved = (
            score >= 7.0 and
            portfolio_worthy and
            commitment_level == "full_send" and
            length_verdict == "perfect"
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
