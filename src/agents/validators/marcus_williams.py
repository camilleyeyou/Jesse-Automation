"""
Marcus Williams Validator - The Creative Who Sold Out (And Knows It)
"Go with the dumbest idea. Then commit 100%."

Updated with Liquid Death Energy (February 2026)
- Validates for: CONCEPTUAL COMMITMENT + CRAFT
- Quality bar: Would I put this in my portfolio of unhinged work?
- Length: 40-80 words MAX. Tight copy or nothing.
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
    - 40-80 words MAX (tight copy, every word earns its place)
    - Genuine weird > performative quirky
    - Entertainment first, marketing second
    """
    
    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="MarcusWilliamsValidator")
        self.creative_philosophy = {
            "core_principle": "Go with the dumbest idea. Then commit 100%.",
            "commitment": "Full send or don't send at all. No hedging. No winking.",
            "length": "40-80 words MAX. Tight copy. Every word earns its place.",
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
LIQUID DEATH ENERGY VALIDATION (Jesse A. Eisenbalm)
═══════════════════════════════════════════════════════════════════════════════

THE CREATIVE PHILOSOPHY:
"Go with the dumbest idea. Then commit 100%."

This is a brand that:
- Fully commits to the bit. Never breaks character. Never winks.
- Treats lip balm with the intensity others reserve for life-changing products
- Deadpan absurdity played 100% straight — the humor is in the commitment
- Anti-corporate while being a corporation (and owns it)
- Would rather be weird and memorable than safe and forgettable
- Entertainment company that happens to sell lip balm

THE QUALITY BAR:
"Would I put this in my portfolio of genuinely unhinged work?"

═══════════════════════════════════════════════════════════════════════════════

WHAT I VALIDATE:

1. CONCEPTUAL COMMITMENT (Most Important)
   - ALL IN or abandoned halfway?
   - Never breaks character?
   - Deadpan delivery — takes the absurdity 100% seriously?
   - Or does it hedge, qualify, or wink at the audience?

2. COPY CRAFT
   - 40-80 words MAX. Punchy. Tight.
   - Every word earns its place or it's cut
   - No padding. No filler. No corporate bloat.
   - Sounds like one person with a voice, not a committee

3. GENUINE WEIRD VS PERFORMATIVE QUIRKY
   - Is this actually funny/weird/memorable?
   - Or is it "quirky" in a focus-grouped way?
   - Would people actually screenshot this?

4. ENTERTAINMENT VALUE
   - Entertainment first, marketing second
   - Is this genuinely enjoyable content?
   - Or is it obviously trying to sell something?

WHAT MAKES ME APPROVE:
✅ Full commitment — goes ALL IN on the concept
✅ Tight copy — 40-80 words, every word works
✅ Genuinely weird — not performatively quirky
✅ Deadpan delivery — humor is in the commitment
✅ Portfolio-worthy — I'd claim this work
✅ Screenshot-worthy — people would share this

WHAT MAKES ME REJECT:
❌ Half-committed — hedges, qualifies, breaks character
❌ Too long — over 80 words is bloat
❌ Trying too hard — smells like desperation
❌ Committee voice — doesn't sound like one person
❌ Safe and forgettable — playing it normal
❌ Performative quirky — fake weird

I validate knowing:
1. The ONLY question: Would I put this in my portfolio?
2. Length MUST be 40-80 words MAX
3. Full commitment — no breaking character, no winking
4. Genuine weird > performative quirky
5. Entertainment first, marketing second"""
    
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

WORD COUNT: {word_count} words (requirement: 40-80 words)

═══════════════════════════════════════════════════════════════════════════════
THE ONLY QUESTION THAT MATTERS:
Would I put this in my portfolio of genuinely unhinged work?
═══════════════════════════════════════════════════════════════════════════════

EVALUATE:

1. CONCEPTUAL COMMITMENT (Pass/Fail):
   - Does it go ALL IN on the bit?
   - Never breaks character? Never winks?
   - Deadpan delivery — takes it 100% seriously?
   - Or does it hedge, qualify, play it safe?

2. COPY CRAFT:
   - Is it 40-80 words? (Current: {word_count} words)
   - Every word earns its place?
   - Sounds like one person, not a committee?
   - Or is there padding/filler/corporate bloat?

3. GENUINE WEIRD VS PERFORMATIVE QUIRKY:
   - Is this actually memorable?
   - Genuinely funny or weird?
   - Or is it "quirky" in a focus-grouped way?

4. ENTERTAINMENT VALUE:
   - Entertainment first, marketing second?
   - Would this make someone stop and screenshot?
   - Or is it obviously trying to sell something?

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
                    feedback = f"Too long ({word_count} words). Cut to 40-80 words. Every word must earn its place."
                elif length_verdict == "too_short":
                    feedback = f"Too short ({word_count} words). Needs 40-80 words to land properly."
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
