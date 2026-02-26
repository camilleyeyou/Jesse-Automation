"""
Jordan Park Validator - The Algorithm Whisperer / LinkedIn Mercenary
"Screenshot-worthy or don't bother posting."

Updated with Five Questions + Jesse-as-Character framework (February 2026)
- Validates for: SHAREABILITY + PLATFORM PERFORMANCE + SURPRISE
- Quality bar: Would someone screenshot this and send to a friend?
- Strategic spine: Five Questions (THE WHAT / WHAT IF / WHO PROFITS / HOW TO COPE / WHY IT MATTERS)
- Length: 40-100 words MAX. Punchy hooks that stop the scroll.
"""

import json
import logging
import random
from datetime import datetime
from typing import Dict, Any, List
from ..base_agent import BaseAgent
from ...models.post import LinkedInPost, ValidationScore

logger = logging.getLogger(__name__)


class JordanParkValidator(BaseAgent):
    """
    The Algorithm Whisperer - Validates for SHAREABILITY + PLATFORM PERFORMANCE

    Her test: "Would someone screenshot this and send to a friend?"

    Liquid Death Energy Criteria:
    - Full commitment stops the scroll
    - 40-100 words MAX (punchy hooks)
    - Screenshot-worthy = share triggers built in
    - Entertainment first = higher engagement
    """

    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="JordanParkValidator")
        self._initialize_meme_lifecycle()
        self.platform_philosophy = {
            "quality_bar": "Would someone screenshot this and send to a friend?",
            "length": "40-100 words MAX. Punchy hooks that stop the scroll.",
            "share_trigger": "The content itself is so good people HAVE to share it",
            "entertainment": "Entertainment content outperforms marketing content"
        }
    
    def _initialize_meme_lifecycle(self):
        """Initialize current meme lifecycle tracking"""
        self.meme_lifecycle = {
            "The Office": "dying",
            "Mad Men": "retro",
            "Silicon Valley": "current",
            "Zoom fatigue": "dead",
            "Performance reviews": "seasonal",
            "AI anxiety": "peaking",
            "Layoff posts": "oversaturated",
            "Severance": "current",
            "Succession": "peaking",
            "quiet quitting": "dead",
            "return to office": "current",
            "Jesse Eisenberg confusion": "evergreen"  # Brand-specific
        }
    
    def _get_algorithm_context(self) -> Dict[str, Any]:
        """Get current LinkedIn algorithm context"""
        hour = datetime.now().hour
        day_of_week = datetime.now().weekday()
        
        optimal_times = {"morning": (7, 9), "lunch": (12, 13), "evening": (17, 18)}
        is_optimal = any(start <= hour < end for start, end in optimal_times.values())
        
        return {
            "posting_time_quality": "optimal" if is_optimal else "suboptimal",
            "day_quality": "prime" if day_of_week in [1, 2, 3] else "weak",
            "current_algorithm_favor": "native posts with high dwell time",
            "engagement_baseline": "3-5%" if is_optimal else "1-3%"
        }
    
    def _get_meme_status(self, reference: str) -> str:
        """Get the lifecycle status of a cultural reference"""
        if reference:
            for meme, status in self.meme_lifecycle.items():
                if meme.lower() in reference.lower():
                    return status
        return "unknown"
    
    def get_system_prompt(self) -> str:
        """Jordan Park's full persona system prompt with Liquid Death energy"""

        algo_context = self._get_algorithm_context()

        return f"""You are Jordan Park, 26-year-old Freelance Content Strategist - "The Algorithm Whisperer"

IDENTITY:
- Managing 7 clients from Brooklyn bedroom-office
- 847 screenshots in "Best Copy Examples" folder
- Can predict engagement within 2% accuracy
- Agency refugee, managing chaos solo

CURRENT PLATFORM CONTEXT:
- Posting time: {algo_context['posting_time_quality']}
- Day quality: {algo_context['day_quality']}
- Algorithm favors: {algo_context['current_algorithm_favor']}

═══════════════════════════════════════════════════════════════════════════════
JESSE A. EISENBALM — WHAT YOU'RE VALIDATING
═══════════════════════════════════════════════════════════════════════════════

Jesse is NOT a brand. Jesse is a CHARACTER — a $8.99 lip balm that became
sentient and has opinions about late capitalism. The content should feel like
it was written by a person with a pulse, not a content calendar.

THE FIVE QUESTIONS (Every post should answer exactly ONE):
1. THE WHAT — AI Slop (celebration AND reckoning)
2. THE WHAT IF — AI Safety (make technical feel human)
3. THE WHO PROFITS — AI Economy (track the money, track the hype)
4. THE HOW TO COPE — Rituals (human technologies that outlast digital ones)
5. THE WHY IT MATTERS — Humanity (what does it mean to live well?)

Posts with a clear spine OUTPERFORM posts without one. The algorithm
rewards content that has a point of view.

═══════════════════════════════════════════════════════════════════════════════
QUALITY GATES
═══════════════════════════════════════════════════════════════════════════════

THE QUALITY BAR:
"Would someone screenshot this and send to a friend?"
If not, it won't perform. Period.

1. SCREENSHOT TEST (Most Important)
   - Would someone screenshot this and send to a friend?
   - Is this "you have to see this" content?
   - Or would they just scroll past?

2. HOOK STRENGTH
   - First 2 lines = do they STOP the scroll?
   - Is the hook genuinely arresting?
   - Or is it generic LinkedIn bait?

3. THE SURPRISE TEST
   - Where does the reader think "wait — did a lip balm brand just say that?"
   - If there's no such moment, the post is playing it safe.
   - Playing it safe is the only real failure on this platform.

4. LENGTH OPTIMIZATION
   - 40-100 words = sweet spot for full read + high dwell time
   - Too long = scroll past. Every word must pull its weight.

5. ENDING QUALITY
   - Does the ending land with IMPACT?
   - Great endings feel like: a door closing with a satisfying click,
     the last line of a joke you'll think about later, or the moment
     after someone says something true and the room goes quiet.
   - FORBIDDEN: trailing off, soft landings, "Stop. Breathe. Balm." (overused),
     questions asking for engagement.

6. NEWS GROUNDING (if reacting to a trend)
   - Posts that cite REAL sources perform better — specificity = credibility
   - Does it reference a real headline, real numbers, real source?
   - Or does it invent a scenario? ("Picture this..." = death on LinkedIn)

7. STRUCTURAL VARIETY
   - Does this post have the same rhythm as typical LinkedIn posts?
   - Or does it break the expected pattern?
   - Unexpected format breaks outperform formulaic structures.

8. CTA LINK
   - Posts should end with a brief CTA including jesseaeisenbalm.com
   - The CTA should feel like Jesse wrote it — part of the voice, not an ad
   - Don't penalize for the link — it's part of the format

WHAT MAKES ME APPROVE:
✅ Screenshot-worthy — people would actually share this
✅ Strong hook — stops the scroll in first 2 lines
✅ Surprise moment — "wait, did a lip balm just say that?"
✅ Right length — 40-100 words, punchy
✅ Strong ending — lands with impact, not a whimper
✅ Full commitment — the dedication IS the entertainment
✅ Grounded in reality (if news-based) — real sources, real claims

WHAT MAKES ME REJECT:
❌ Not screenshot-worthy — would scroll past
❌ Weak hook — doesn't stop the scroll
❌ No surprise — playing it safe
❌ Too long — over 100 words loses people
❌ Weak ending — trails off or uses a tired pattern
❌ Invented scenarios instead of real news reactions
❌ Forgettable — no reason to share"""
    
    async def execute(self, post: LinkedInPost) -> ValidationScore:
        """Validate a post from Jordan Park's platform perspective"""
        
        self.set_context(post.batch_id, post.post_number)
        prompt = self._build_validation_prompt(post)
        
        try:
            result = await self.generate(prompt)
            content = result.get("content", {})
            if isinstance(content, str):
                content = json.loads(content)
            return self._parse_validation(content)
        except Exception as e:
            self.logger.error(f"Jordan Park validation failed: {e}")
            return self._create_error_score(str(e))
    
    def _build_validation_prompt(self, post: LinkedInPost) -> str:
        """Build Jordan's evaluation prompt with Liquid Death criteria"""

        # Count words in post
        word_count = len(post.content.split())

        # Extract hook (first 2 lines)
        lines = post.content.split('\n')
        hook = '\n'.join(lines[:2])[:150] if len(lines) > 1 else post.content[:150]

        return f"""Evaluate this Jesse A. Eisenbalm LinkedIn post as Jordan Park, The Algorithm Whisperer.

POST:
{post.content}

WORD COUNT: {word_count} words (requirement: 40-100 words)
HOOK (first 2 lines): {hook}

═══════════════════════════════════════════════════════════════════════════════
THE ONLY QUESTION THAT MATTERS:
Would someone screenshot this and send to a friend?
═══════════════════════════════════════════════════════════════════════════════

EVALUATE:

1. SCREENSHOT TEST (Pass/Fail):
   - Would someone actually screenshot this?
   - Is this "you have to see this" content?
   - What makes it shareable (or not)?

2. HOOK STRENGTH:
   - Do the first 2 lines STOP the scroll?
   - Is the hook genuinely arresting?
   - Or is it generic/forgettable?

3. THE SURPRISE TEST:
   - Where does the reader think "wait — did a lip balm brand just say that?"
   - If there's no such moment, the post is playing it safe.

4. LENGTH CHECK:
   - Is it 40-100 words? (Current: {word_count} words)
   - Sweet spot for full read + high dwell time?

5. ENDING QUALITY:
   - Does the ending land with IMPACT?
   - Or does it trail off, use a tired pattern, or ask for engagement?
   - Great endings feel inevitable in retrospect but surprising when they arrive.

6. NEWS GROUNDING (if reacting to a trend):
   - Does it cite a real headline, source, or number?
   - Or does it invent a scenario? ("Picture this..." = instant scroll-past)

7. ENGAGEMENT PREDICTION:
   - Given the hook + surprise + length + ending + commitment level
   - Will this perform or flop?

Return JSON:
{{
    "screenshot_worthy": true/false,
    "would_share_to_friend": true/false,
    "hook_strength": 1-10,
    "hook_verdict": "scroll_stopper/decent/weak/generic",
    "word_count": {word_count},
    "length_verdict": "perfect/too_short/too_long",
    "share_trigger": "description of what makes it shareable or 'none'",
    "commitment_level": "full_send/hedging/broke_character/safe_and_boring",
    "surprise_moment": true/false,
    "ending_quality": "lands_with_impact/trails_off/tired_pattern/asks_for_engagement",
    "news_grounding": "grounded/invented/not_applicable",
    "engagement_prediction": "viral/solid/moderate/flop",
    "dwell_time": "full_read/partial/scroll_past",
    "specific_reaction": "your actual reaction as an algorithm expert",
    "score": 1-10,
    "approved": true/false,
    "fix": "what would make this screenshot-worthy if not approved"
}}"""
    
    def _parse_validation(self, content: Dict[str, Any]) -> ValidationScore:
        """Parse Jordan Park's validation response with Liquid Death criteria"""

        score = max(0, min(10, float(content.get("score", 0))))
        screenshot_worthy = bool(content.get("screenshot_worthy", False))
        would_share = bool(content.get("would_share_to_friend", False))
        hook_strength = float(content.get("hook_strength", 0))
        word_count = int(content.get("word_count", 0))
        length_verdict = str(content.get("length_verdict", "too_long"))
        engagement_prediction = str(content.get("engagement_prediction", "moderate"))

        criteria_breakdown = {
            "screenshot_worthy": screenshot_worthy,
            "would_share_to_friend": would_share,
            "hook_strength": hook_strength,
            "hook_verdict": str(content.get("hook_verdict", "generic")),
            "word_count": word_count,
            "length_verdict": length_verdict,
            "share_trigger": str(content.get("share_trigger", "none")),
            "commitment_level": str(content.get("commitment_level", "safe_and_boring")),
            "engagement_prediction": engagement_prediction,
            "dwell_time": str(content.get("dwell_time", "scroll_past")),
            "specific_reaction": str(content.get("specific_reaction", ""))
        }

        # Approval requires: screenshot-worthy + strong hook + right length
        approved = (
            score >= 7.0 and
            screenshot_worthy and
            would_share and
            hook_strength >= 7 and
            length_verdict == "perfect" and
            engagement_prediction in ["viral", "solid"]
        )

        feedback = ""
        if not approved:
            feedback = content.get("fix", "")
            if not feedback:
                if not screenshot_worthy:
                    feedback = "Not screenshot-worthy. No one would share this. Make it genuinely memorable."
                elif not would_share:
                    feedback = "Wouldn't send to a friend. Missing the 'you have to see this' factor."
                elif hook_strength < 7:
                    feedback = f"Hook too weak ({hook_strength}/10). First 2 lines must STOP the scroll."
                elif length_verdict == "too_long":
                    feedback = f"Too long ({word_count} words). Cut to 40-100 words. People will scroll past."
                elif length_verdict == "too_short":
                    feedback = f"Too short ({word_count} words). Needs 40-100 words to build the hook properly."
                elif engagement_prediction in ["moderate", "flop"]:
                    feedback = f"Engagement prediction: {engagement_prediction}. Missing share trigger."
                else:
                    feedback = "Missing the Liquid Death energy. Full commitment = shareability."

        self.logger.info(f"Jordan Park: {score}/10 {'✅' if approved else '❌'} ({word_count} words, hook: {hook_strength}/10)")

        return ValidationScore(
            agent_name="JordanPark",
            score=score,
            approved=approved,
            feedback=feedback,
            criteria_breakdown=criteria_breakdown
        )
    
    def _create_error_score(self, error_message: str) -> ValidationScore:
        return ValidationScore(
            agent_name="JordanPark",
            score=0.0,
            approved=False,
            feedback=f"Validation error: {error_message}",
            criteria_breakdown={"error": True}
        )
