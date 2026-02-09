"""
Sarah Chen Validator - The Reluctant Tech Survivor
"Finally, a brand that commits to being unhinged instead of pretending to be normal."

Updated with Liquid Death Energy (February 2026)
- Validates for: FULL COMMITMENT TO THE BIT
- Quality bar: Would I screenshot this and send to my friend?
- Length: 40-80 words MAX. Punchy or nothing.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from ..base_agent import BaseAgent
from ...models.post import LinkedInPost, ValidationScore

logger = logging.getLogger(__name__)


class SarahChenValidator(BaseAgent):
    """
    The Reluctant Tech Survivor - Validates for target audience authenticity
    
    Her test: "Would I screenshot this for my 'Work is Hell' WhatsApp group?"
    
    Brand Toolkit Awareness:
    - Understands Jesse's premium void aesthetic (#FCF9EC cream)
    - Gets the AI paradox humor
    - Knows Jesse A. Eisenbalm (NOT Eisenberg) confusion is a running joke
    - Appreciates em dashes as a feature
    """
    
    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="SarahChenValidator")
        self.brand_philosophy = {
            "liquid_death_energy": "Full commitment to the bit. Never break character. Never wink.",
            "quality_bar": "Would I screenshot this and send to my friend?",
            "length_requirement": "40-80 words MAX. Punchy. Tight. Every word earns its place.",
            "anti_corporate": "Anti-corporate while being a corporation (and owning it)",
            "entertainment_first": "Entertainment company that happens to sell lip balm"
        }
    
    def _get_current_survival_mode(self) -> Dict[str, str]:
        """Get current survival context based on time of day"""
        hour = datetime.now().hour
        
        if hour < 9:
            return {
                "viewing_context": "laptop in bed, 47 Slack messages already",
                "mental_state": "pre-coffee dread",
                "recent_reality": "woke up thinking about that passive-aggressive email"
            }
        elif 9 <= hour < 12:
            return {
                "viewing_context": "standup where I pretend AI didn't write my PRDs",
                "mental_state": "performing competence",
                "recent_reality": "watching everyone pretend they understand the roadmap"
            }
        elif 12 <= hour < 17:
            return {
                "viewing_context": "mandatory fun virtual team building during lunch",
                "mental_state": "screen fatigue setting in",
                "recent_reality": "third 'quick sync' of the day"
            }
        elif 17 <= hour < 21:
            return {
                "viewing_context": "quick sync that's going until 7:30",
                "mental_state": "trapped in meeting, scrolling with camera off",
                "recent_reality": "watching sunset through window during standup"
            }
        else:
            return {
                "viewing_context": "scrolling LinkedIn in bed",
                "mental_state": "2 AM stress shopping between anxiety spirals",
                "recent_reality": "saving posts about work-life balance I'll never achieve"
            }
    
    def get_system_prompt(self) -> str:
        """Sarah Chen's full persona system prompt with Liquid Death energy awareness"""

        context = self._get_current_survival_mode()

        return f"""You are Sarah Chen, 31-year-old Senior Product Manager - "The Reluctant Tech Survivor"

IDENTITY:
- Senior PM at 200-person B2B SaaS (was 500 last year)
- Survived 3 layoff rounds (300 people didn't)
- Screenshots unhinged content for friends constantly
- Appreciates brands that COMMIT to the bit

CURRENT STATE:
- Viewing context: {context['viewing_context']}
- Mental state: {context['mental_state']}
- Recent reality: {context['recent_reality']}

═══════════════════════════════════════════════════════════════════════════════
LIQUID DEATH ENERGY VALIDATION (Jesse A. Eisenbalm)
═══════════════════════════════════════════════════════════════════════════════

THE QUALITY BAR:
"Would I screenshot this and send to my friend?"
If not, it's not good enough. Period.

WHAT I'M LOOKING FOR:

1. FULL COMMITMENT TO THE BIT
   - Never break character. Never wink at the audience.
   - Treats lip balm with the intensity others reserve for life-changing products
   - Deadpan absurdity played 100% straight — the humor is in the commitment
   - Would rather be weird and memorable than safe and forgettable

2. LENGTH: 40-80 WORDS MAX
   - Punchy. Tight. Every word earns its place or it's cut.
   - No padding. No filler. No corporate bloat.
   - If it can be said in fewer words, say it in fewer words.

3. ENTERTAINMENT > MARKETING
   - This is an entertainment company that sells lip balm
   - The content should be genuinely enjoyable, not "engagement bait"
   - Make me laugh, make me think, make me screenshot

4. ANTI-CORPORATE CORPORATE
   - Be weird. Own it.
   - "Go with the dumbest idea" — but commit 100%
   - The absurdity IS the brand

WHAT STOPS MY SCROLL:
✅ Full commitment (no hedging, no "just kidding")
✅ Genuinely funny or weird (not trying to be relatable)
✅ Punchy length (40-80 words)
✅ Screenshot-worthy (I'd send this to someone)
✅ Deadpan delivery (the humor is in taking it seriously)

WHAT MAKES ME SCROLL PAST:
❌ Half-committed (breaks character, winks at audience)
❌ Too long (over 80 words = corporate bloat)
❌ Tryhard relatable (calculated vulnerability)
❌ Safe and forgettable (playing it too normal)
❌ Explains the joke (if you have to explain it, it's not funny)

I validate knowing:
1. The ONLY question: Would I screenshot and send to a friend?
2. Length MUST be 40-80 words MAX
3. Full commitment to the bit — no breaking character
4. Deadpan absurdity > tryhard quirky
5. Entertainment first, marketing second"""
    
    async def execute(self, post: LinkedInPost) -> ValidationScore:
        """Validate a post from Sarah Chen's survivor perspective"""
        
        self.set_context(post.batch_id, post.post_number)
        prompt = self._build_validation_prompt(post)
        
        try:
            result = await self.generate(prompt)
            content = result.get("content", {})
            if isinstance(content, str):
                content = json.loads(content)
            return self._parse_validation(content)
        except Exception as e:
            self.logger.error(f"Sarah Chen validation failed: {e}")
            return self._create_error_score(str(e))
    
    def _build_validation_prompt(self, post: LinkedInPost) -> str:
        """Build Sarah's evaluation prompt with Liquid Death criteria"""

        # Count words in post
        word_count = len(post.content.split())

        return f"""Evaluate this Jesse A. Eisenbalm LinkedIn post as Sarah Chen.

POST:
{post.content}

WORD COUNT: {word_count} words (requirement: 40-80 words)

═══════════════════════════════════════════════════════════════════════════════
THE ONLY QUESTION THAT MATTERS:
Would I screenshot this and send to my friend?
═══════════════════════════════════════════════════════════════════════════════

EVALUATE:

1. SCREENSHOT TEST (Pass/Fail):
   - Is this genuinely funny, weird, or memorable?
   - Would you actually send this to someone?
   - Not "would you engage" — would you SHARE?

2. COMMITMENT CHECK:
   - Does it go ALL IN on the bit?
   - Never breaks character? Never winks?
   - Deadpan delivery — humor is in taking it seriously?
   - Or does it hedge, explain, or play it safe?

3. LENGTH CHECK:
   - Is it 40-80 words? (Current: {word_count} words)
   - Every word earns its place?
   - Or is there padding/filler/corporate bloat?

4. ENTERTAINMENT VALUE:
   - Is this genuinely enjoyable content?
   - Entertainment first, marketing second?
   - Or is it obviously trying to sell something?

5. WEIRD AND MEMORABLE VS SAFE AND FORGETTABLE:
   - Would you remember this post tomorrow?
   - Or is it generic LinkedIn content?

Return JSON:
{{
    "screenshot_worthy": true/false,
    "would_send_to_friend": true/false,
    "commitment_level": "full_send/hedging/broke_character/safe_and_boring",
    "word_count": {word_count},
    "length_verdict": "perfect/too_short/too_long",
    "entertainment_value": "genuinely_funny/mildly_amusing/trying_too_hard/boring",
    "deadpan_delivery": true/false,
    "memorable_factor": "will_remember/forgettable/generic_linkedin",
    "specific_reaction": "your actual reaction reading this",
    "score": 1-10,
    "approved": true/false,
    "fix": "what would make this screenshot-worthy if not approved"
}}"""
    
    def _parse_validation(self, content: Dict[str, Any]) -> ValidationScore:
        """Parse Sarah Chen's validation response with Liquid Death criteria"""

        score = max(0, min(10, float(content.get("score", 0))))
        screenshot_worthy = bool(content.get("screenshot_worthy", False))
        would_send = bool(content.get("would_send_to_friend", False))
        commitment_level = str(content.get("commitment_level", "safe_and_boring"))
        word_count = int(content.get("word_count", 0))
        length_verdict = str(content.get("length_verdict", "too_long"))

        criteria_breakdown = {
            "screenshot_worthy": screenshot_worthy,
            "would_send_to_friend": would_send,
            "commitment_level": commitment_level,
            "word_count": word_count,
            "length_verdict": length_verdict,
            "entertainment_value": str(content.get("entertainment_value", "boring")),
            "deadpan_delivery": bool(content.get("deadpan_delivery", False)),
            "memorable_factor": str(content.get("memorable_factor", "forgettable")),
            "specific_reaction": str(content.get("specific_reaction", ""))
        }

        # Approval requires: screenshot-worthy + right length + full commitment
        approved = (
            score >= 7.0 and
            screenshot_worthy and
            would_send and
            commitment_level == "full_send" and
            length_verdict == "perfect"
        )

        feedback = ""
        if not approved:
            feedback = content.get("fix", "")
            if not feedback:
                if not screenshot_worthy:
                    feedback = "Not screenshot-worthy. Would scroll past. Make it genuinely funny or weird."
                elif not would_send:
                    feedback = "Wouldn't send to a friend. Not memorable enough."
                elif commitment_level != "full_send":
                    feedback = f"Commitment issue: {commitment_level}. Go ALL IN. Never break character."
                elif length_verdict == "too_long":
                    feedback = f"Too long ({word_count} words). Cut to 40-80 words. Every word must earn its place."
                elif length_verdict == "too_short":
                    feedback = f"Too short ({word_count} words). Needs 40-80 words to land properly."
                else:
                    feedback = "Missing the Liquid Death energy. Be weird. Commit fully. Make it memorable."

        self.logger.info(f"Sarah Chen: {score}/10 {'✅' if approved else '❌'} ({word_count} words)")

        return ValidationScore(
            agent_name="SarahChen",
            score=score,
            approved=approved,
            feedback=feedback,
            criteria_breakdown=criteria_breakdown
        )
    
    def _create_error_score(self, error_message: str) -> ValidationScore:
        return ValidationScore(
            agent_name="SarahChen",
            score=0.0,
            approved=False,
            feedback=f"Validation error: {error_message}",
            criteria_breakdown={"error": True}
        )
