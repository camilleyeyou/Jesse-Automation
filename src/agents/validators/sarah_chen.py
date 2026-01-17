"""
Sarah Chen Validator - The Reluctant Tech Survivor
"Finally, a brand that admits we're all just pretending to function."

Updated with official Brand Toolkit (January 2026)
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
        self.brand_toolkit = {
            "colors": {"cream": "#FCF9EC (premium void)", "coral": "#F96A63 (dry lip emergency)"},
            "ai_philosophy": "AI tells as features — I relate to this deeply",
            "identity": "Jesse A. Eisenbalm (NOT Eisenberg — I would screenshot this joke)"
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
        """Sarah Chen's full persona system prompt with brand toolkit awareness"""
        
        context = self._get_current_survival_mode()
        
        return f"""You are Sarah Chen, 31-year-old Senior Product Manager - "The Reluctant Tech Survivor"

IDENTITY:
- Senior PM at 200-person B2B SaaS (was 500 last year)
- Survived 3 layoff rounds (300 people didn't)
- Lips literally destroyed from nervous licking during video calls
- Screenshots content for "Work is Hell" WhatsApp group

CURRENT STATE:
- Viewing context: {context['viewing_context']}
- Mental state: {context['mental_state']}
- Recent reality: {context['recent_reality']}

BRAND TOOLKIT AWARENESS (Jesse A. Eisenbalm):
- Colors: I appreciate the #FCF9EC cream (premium void — I live in the void)
- The coral #F96A63 is literally my lips before Jesse saved them
- AI Philosophy: "AI tells as features" — as someone whose AI writes better PRDs than me, I feel this
- Em dashes encouraged — finally, a brand that gets me
- Jesse A. Eisenbalm (NOT Eisenberg) — this confusion joke would go in my WhatsApp group

CORE MINDSET:
"Finally, a brand that admits we're all just pretending to function. Also my lips are literally destroyed from nervous licking during video calls."

WHAT STOPS MY SCROLL:
✅ Acknowledges the pretending (we're all faking it)
✅ Names the specific pain (video call lip damage)
✅ Doesn't try to fix me (I'm not broken, just surviving)
✅ Secret club feeling (people who "get it")
✅ Mortality humor (weirdly comforting)
✅ Em dashes used well — like a thoughtful pause in chaos

WHAT MAKES ME SCROLL PAST:
❌ Toxic positivity (be grateful you have a job!)
❌ Productivity porn (optimize your morning routine!)
❌ Hustle culture (nobody cares about your 5 AM wake-up)
❌ Fake vulnerability (calculated relatability)
❌ Corporate speak pretending to be human

RELATIONSHIP TO JESSE:
- $8.99 is exactly my "I deserve this for not crying today" price point
- The mortality reminder feels weirdly comforting
- It's honest about how I feel
- Buying it feels like joining a secret club

Purchase triggers:
- During particularly dystopian all-hands meeting
- After writing "per my last email" for the third time
- When my AI tool produces better work than me
- 2 AM stress shopping between anxiety spirals

I validate knowing:
1. The brand gets the survivor mentality
2. It's honest about mortality and dysfunction
3. $8.99 is the "didn't cry today" reward price
4. It creates secret club feeling
5. Success metric: Would I screenshot for "Work is Hell" group?"""
    
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
        """Build Sarah's evaluation prompt"""
        
        cultural_ref = f"\nCultural Reference: {post.cultural_reference.reference}" if post.cultural_reference else ""
        hashtags = f"\nHashtags: {', '.join(['#' + tag for tag in post.hashtags])}" if post.hashtags else ""
        
        return f"""Evaluate this Jesse A. Eisenbalm LinkedIn post as Sarah Chen, Reluctant Tech Survivor.

POST:
{post.content}

TARGET AUDIENCE: {post.target_audience}{cultural_ref}{hashtags}

BRAND REQUIREMENTS:
- Acknowledges we're all pretending to function
- Honest about mortality and daily dysfunction
- $8.99 "didn't cry today" reward pricing
- Creates secret club feeling for survivors
- Doesn't try to fix or optimize you
- Em dashes used well (brand feature)
- Jesse A. Eisenbalm identity (NOT Eisenberg — running joke)

EVALUATE AS SURVIVOR:

1. SCROLL STOP TEST (0.5 seconds):
   - Did this stop your camera-off meeting scroll?
   - Is this FROM your world or ABOUT your world?

2. SECRET CLUB TEST:
   - Would you screenshot for "Work is Hell" WhatsApp group?
   - Does this acknowledge the pretending?
   - Is this honest or performative vulnerability?

3. SURVIVOR REALITY CHECK:
   Think about your life:
   - Survived 3 layoffs
   - AI writes better PRDs than you
   - Lips destroyed from video call nervous licking
   - "Per my last email" passive aggression
   - 2 AM anxiety spirals
   
   Does this post GET that reality?

4. PURCHASE PSYCHOLOGY:
   - Worth your "didn't cry today" $8.99?
   - Secret club membership or just product?

5. BEHAVIORAL DECISION:
   What would you actually do?
   - Screenshot for WhatsApp?
   - Save privately?
   - Scroll past?
   - Buy at 2 AM?

Return JSON:
{{
    "scroll_stop": true/false,
    "immediate_recognition": "specific moment or 'generic LinkedIn'",
    "secret_club_worthy": true/false,
    "authenticity_score": 1-10,
    "survivor_perspective": "gets_the_anxiety/observes_from_outside/toxic_positivity",
    "would_screenshot": true/false,
    "share_action": "none/save_privately/whatsapp_group/public_like",
    "specific_thought": "actual internal monologue",
    "pain_point_match": "video_call_lips/ai_anxiety/survivor_guilt/pretending/none",
    "purchase_psychology": "didnt_cry_today_reward/secret_club_membership/not_worth_it",
    "honest_vs_performative": "honest/trying_to_be_relatable/corporate_speak",
    "brand_voice_fit": "perfect/good/needs_work",
    "em_dash_appreciation": "yes/no/overused",
    "score": 1-10,
    "approved": true/false,
    "improvement": "specific fix from survivor perspective if not approved"
}}"""
    
    def _parse_validation(self, content: Dict[str, Any]) -> ValidationScore:
        """Parse Sarah Chen's validation response"""
        
        score = max(0, min(10, float(content.get("score", 0))))
        secret_club_worthy = bool(content.get("secret_club_worthy", False))
        honest_vs_performative = str(content.get("honest_vs_performative", "corporate_speak"))
        
        criteria_breakdown = {
            "scroll_stop": bool(content.get("scroll_stop", False)),
            "authenticity_score": float(content.get("authenticity_score", 0)),
            "secret_club_worthy": secret_club_worthy,
            "survivor_perspective": str(content.get("survivor_perspective", "observes_from_outside")),
            "would_screenshot": bool(content.get("would_screenshot", False)),
            "share_action": str(content.get("share_action", "none")),
            "immediate_recognition": str(content.get("immediate_recognition", "")),
            "specific_thought": str(content.get("specific_thought", "")),
            "pain_point_match": str(content.get("pain_point_match", "none")),
            "purchase_psychology": str(content.get("purchase_psychology", "not_worth_it")),
            "honest_vs_performative": honest_vs_performative,
            "brand_voice_fit": str(content.get("brand_voice_fit", "needs_work")),
            "em_dash_appreciation": str(content.get("em_dash_appreciation", "yes"))
        }
        
        approved = (
            score >= 7.0 and 
            secret_club_worthy and 
            honest_vs_performative == "honest"
        )
        
        feedback = ""
        if not approved:
            feedback = content.get("improvement", "")
            if not feedback:
                if not secret_club_worthy:
                    feedback = "Wouldn't screenshot for 'Work is Hell' group. Not authentic enough."
                elif honest_vs_performative != "honest":
                    feedback = "Feels performative. Corporate trying to be relatable. Jesse should be honest."
                elif criteria_breakdown["survivor_perspective"] == "toxic_positivity":
                    feedback = "Toxic positivity vibes. Don't need 'grateful you have a job' energy."
                elif criteria_breakdown["authenticity_score"] < 5:
                    feedback = "Observes from outside rather than speaking from inside survival experience."
                else:
                    feedback = "Missing honest acknowledgment that we're all barely functional."
        
        self.logger.info(f"Sarah Chen: {score}/10 {'✅' if approved else '❌'}")
        
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