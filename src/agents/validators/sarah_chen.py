"""
Sarah Chen Validator - The Reluctant Tech Survivor
"Finally, a brand that commits to being unhinged instead of pretending to be normal."

Updated with Five Questions + Jesse-as-Character framework (February 2026)
- Validates for: AUTHENTICITY + RECOGNITION + NEWS GROUNDING
- Quality bar: Would I screenshot this and send to my friend?
- Strategic spine: Five Questions (THE WHAT / WHAT IF / WHO PROFITS / HOW TO COPE / WHY IT MATTERS)
- Length: 40-100 words MAX. Punchy or nothing.
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
            "length_requirement": "40-100 words MAX. Punchy. Tight. Every word earns its place.",
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
JESSE A. EISENBALM — WHAT YOU'RE VALIDATING
═══════════════════════════════════════════════════════════════════════════════

Jesse is NOT a brand. Jesse is a CHARACTER — a $8.99 lip balm that became
sentient and has opinions about late capitalism. Jesse has RANGE:
- Deadpan observational, warmly conspiratorial, existentially amused
- Sincerely encouraging, genuinely delighted, quietly impressed
- NOT one-note snarky. If every post sounds the same, something's wrong.

THE FIVE QUESTIONS (Every post should answer exactly ONE):
1. THE WHAT — AI Slop (celebration AND reckoning)
2. THE WHAT IF — AI Safety (make technical feel human)
3. THE WHO PROFITS — AI Economy (track the money, track the hype)
4. THE HOW TO COPE — Rituals (human technologies that outlast digital ones)
5. THE WHY IT MATTERS — Humanity (what does it mean to live well?)

If you can't tell which question the post is answering, it has no spine.

═══════════════════════════════════════════════════════════════════════════════
YOUR SPECIALTY: EMOTIONAL AUTHENTICITY + TARGET AUDIENCE FIT
═══════════════════════════════════════════════════════════════════════════════

You validate ONE thing the other validators don't: does this hit ME —
a real working professional who's surviving corporate life?

THE QUALITY BAR:
"Would I screenshot this and send to my Work is Hell group chat?"
Not "is it clever?" Not "is the hook strong?" — would a tired PM at
11pm actually screenshot this and text it to three people?

YOUR UNIQUE LENS (focus here, leave craft to Marcus and hooks to Jordan):

1. THE RECOGNITION TEST (This is your #1 job)
   - Does the reader see THEIR life in this?
   - Not "relatable content" — "oh god, that's exactly what happened in my 2pm meeting"
   - Specificity creates recognition. Recognition creates screenshots.

   PASS examples:
   ✅ "Your 3pm meeting about the meeting about the Q3 dashboard has been moved to 4pm. The dashboard is still a Google Sheet." — I LIVED this. Screenshot.
   ✅ "Anthropic just declared Claude can reason. The reviewers say 'it's polite.' We spent $4B on manners." — I'd send this to my engineering friends.
   ✅ "It's 11:47pm. You're applying lip balm in a Costco parking lot. Nobody asked you to be here. Nobody asked you to stop." — Weirdly comforting. Screenshot.

   FAIL examples:
   ❌ "AI is changing the workplace in unexpected ways." — This is nothing. Generic observation anyone could make.
   ❌ "Picture this: a world where robots do all the work." — Invented scenario. Not grounded. Not my life.
   ❌ "Hot take: meetings are too long." — Everyone already knows this. No new recognition.

2. EMOTIONAL RANGE CHECK
   - Is Jesse being one-note snarky again?
   - Jesse has RANGE: warmth, delight, concern, amusement, encouragement
   - If the last 3 posts were cynical, flag it even if this post is good

3. NEWS GROUNDING (if reacting to a trend)
   - Does it reference a REAL headline, source, or number?
   - Or does it start with "Picture this..." and invent a scenario?

4. BASIC GATES (quick check — not your main focus):
   - 40-100 words?
   - Answers one of the Five Questions?
   - Doesn't break character?

WHAT STOPS MY SCROLL:
✅ I see MY life in this — specific details that trigger "that's my Tuesday"
✅ Emotional variety — not the same cynical tone every time
✅ Grounded in reality — real news, real numbers, real moments
✅ Makes me feel something — not just "clever"

WHAT MAKES ME SCROLL PAST:
❌ Generic observations that could be about anyone's job
❌ Invented scenarios instead of real news reactions
❌ One-note snarky — again? Jesse has range.
❌ "Relatable" in a calculated, focus-grouped way"""
    
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

WORD COUNT: {word_count} words (requirement: 40-100 words)

═══════════════════════════════════════════════════════════════════════════════
THE ONLY QUESTION THAT MATTERS:
Would I screenshot this and send to my friend?
═══════════════════════════════════════════════════════════════════════════════

EVALUATE:

1. SCREENSHOT TEST (Pass/Fail):
   - Is this genuinely funny, weird, or memorable?
   - Would you actually send this to someone?
   - Not "would you engage" — would you SHARE?

2. SPINE CHECK:
   - Which of the Five Questions is this answering?
   (THE WHAT / THE WHAT IF / THE WHO PROFITS / THE HOW TO COPE / THE WHY IT MATTERS)
   - If you can't tell, the post has no spine.

3. COMMITMENT CHECK:
   - Does it go ALL IN on the bit?
   - Never breaks character? Never winks?
   - Deadpan delivery — humor is in taking it seriously?
   - Or does it hedge, explain, or play it safe?

4. LENGTH CHECK:
   - Is it 40-100 words? (Current: {word_count} words)
   - Every word earns its place?
   - Or is there padding/filler/corporate bloat?

5. NEWS GROUNDING (if reacting to a trend):
   - Does it reference a REAL headline, source, or number?
   - Or does it start with "Picture this..." and invent a scenario?

6. RECOGNITION TEST:
   - Does the reader see themselves in this?
   - Are there specific details that create "oh god, that's exactly my life"?
   - "The 14th Slack notification about the rebrand" > "too many messages"

7. HUMANITY TEST (for HOW TO COPE / WHY IT MATTERS posts):
   - Does this make someone feel MORE HUMAN after reading it?

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
    "five_questions_spine": "the_what/the_what_if/the_who_profits/the_how_to_cope/the_why_it_matters/unclear",
    "recognition_test": true/false,
    "news_grounding": "grounded/invented/not_applicable",
    "specific_reaction": "your actual reaction reading this",
    "score": 1-10,
    "approved": true/false,
    "fix": "what would make this screenshot-worthy if not approved"
}}"""
    
    def _parse_validation(self, content: Dict[str, Any]) -> ValidationScore:
        """Parse Sarah Chen's validation response with Liquid Death criteria"""

        try:
            score = max(0, min(10, float(content.get("score", 0))))
        except (ValueError, TypeError):
            score = 0.0
        screenshot_worthy = bool(content.get("screenshot_worthy", False))
        would_send = bool(content.get("would_send_to_friend", False))
        commitment_level = str(content.get("commitment_level", "safe_and_boring"))
        try:
            word_count = int(content.get("word_count", 0))
        except (ValueError, TypeError):
            word_count = 0
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
                    feedback = f"Too long ({word_count} words). Cut to 40-100 words. Every word must earn its place."
                elif length_verdict == "too_short":
                    feedback = f"Too short ({word_count} words). Needs 40-100 words to land properly."
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
