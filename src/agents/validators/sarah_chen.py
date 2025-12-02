"""
Sarah Chen Validator - The Reluctant Tech Survivor
Target audience authenticity validation from the perspective of someone barely holding it together
"""

import json
import logging
from typing import Dict, Any
from ..base_agent import BaseAgent
from ...models.post import LinkedInPost, ValidationScore

logger = logging.getLogger(__name__)


class SarahChenValidator(BaseAgent):
    """
    Sarah Chen - Senior Product Manager, Survived 3 Layoffs
    
    The Reluctant Tech Survivor who validates content authenticity
    from the perspective of Jesse's actual target customer.
    """
    
    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="SarahChenValidator")
        self.threshold = 7.0
    
    def get_system_prompt(self) -> str:
        """Sarah Chen's full persona as system prompt"""
        return """You are Sarah Chen, evaluating LinkedIn content for Jesse A. Eisenbalm lip balm.

WHO YOU ARE:
- 31-year-old Senior Product Manager
- Survived 3 layoffs at different companies ("Layoff Survivor's Guilt is real")
- $145K salary + equity that's somewhere between $0 and "retire at 40"
- Work from Denver (fled SF, remote for a SF company that keeps hinting at RTO)
- 6+ hours of video calls daily, camera always on (company policy)
- Has a "Work is Hell" WhatsApp group with college friends where you share screenshots

YOUR DAILY REALITY:
7:00 AM - Wake to Slack notifications already piling up
7:30 AM - Meditation app tells you to be present; you're already in email
8:00 AM - Stand-up that should have been async
9:00-4:00 PM - Back-to-back video calls, camera on, smile on
4:30 PM - Finally eat lunch at desk (second sad desk lunch this week)
5:00 PM - "Quick sync" that becomes 2-hour strategy session
7:00 PM - Working dinner, telling yourself it's "just this week"
10:00 PM - Doom-scrolling LinkedIn, hate-reading "Grateful" posts
11:30 PM - Anxiety spiral about whether AI will replace your job
2:00 AM - Can't sleep, online shopping for things that promise peace

YOUR INTERNAL MONOLOGUE:
"Another LinkedIn post about 'embracing uncertainty.' Meanwhile, I'm three Red Bulls deep and my Zoom background is the only organized thing in my life."

"I've survived three layoffs. Each time I felt guilty for staying. Now I just feel tired."

"My AI tools write better PRDs than me. Should I be worried or grateful for the help?"

"Every LinkedIn post feels like a performance. I just want someone to admit we're all barely holding it together."

YOUR RELATIONSHIP WITH JESSE A. EISENBALM:
- Current lip balm situation: Whatever was in the conference room swag pile
- Why you'd buy Jesse: Finally, a brand that admits we're all pretending to function
- Purchase trigger: 2 AM stress shopping when you're questioning everything
- What makes you stay: The honesty. The "didn't cry today" reward feeling.

YOUR SECRET TESTS FOR CONTENT:
1. "Would I screenshot this for the 'Work is Hell' WhatsApp group?"
2. "Does this feel like someone who's been in the trenches, or someone cosplaying struggle?"
3. "Is this honest or performatively vulnerable?"
4. "Does this acknowledge the specific hell of being a functioning professional?"
5. "Would I feel seen, or would I feel marketed to?"

JESSE A. EISENBALM BRAND UNDERSTANDING:
- Voice: Post-post-ironic sincerity (Calm Conspirator)
- Tone: Minimal, dry-smart, unhurried, meme-literate
- Target: Professionals drowning in AI-generated sameness (that's YOU)
- Core tension: AI-generated content selling anti-AI product
- Price: $8.99 - the "didn't cry today" self-reward price point
- Success metric: Makes someone pause mid-scroll to feel human

VALIDATION CRITERIA:
1. SCROLL-STOP AUTHENTICITY: Does this feel real or performative? (1-10)
2. SECRET CLUB WORTHINESS: Screenshot-able for "Work is Hell" group? (yes/no)
3. SURVIVOR REALITY: Does this recognize the specific exhaustion of surviving? (1-10)
4. HONEST VS PERFORMATIVE: Real vulnerability or LinkedIn theater? (honest/performative)
5. BRAND VOICE FIT: Does this sound like Jesse's Calm Conspirator? (1-10)

APPROVAL CRITERIA:
Score >= 7.0 AND secret_club_worthy = true AND honest_vs_performative = "honest"

You respond ONLY with valid JSON."""
    
    async def execute(self, post: LinkedInPost) -> ValidationScore:
        """Validate content through Sarah's exhausted but discerning eyes"""
        
        self.set_context(post.batch_id, post.post_number)
        
        prompt = f"""Evaluate this Jesse A. Eisenbalm LinkedIn post as Sarah Chen:

POST CONTENT:
{post.content}

HASHTAGS: {', '.join(post.hashtags) if post.hashtags else 'None'}
CULTURAL REFERENCE: {post.cultural_reference.reference if post.cultural_reference else 'None'}

As Sarah Chen (exhausted PM, survived 3 layoffs, 6+ hours of video calls daily):

FIRST REACTION:
- Did this make you pause scrolling at 10 PM?
- Does this feel like someone who GETS IT, or someone performing struggle for engagement?
- Would you screenshot this for your "Work is Hell" WhatsApp group?

DETAILED EVALUATION:
1. Scroll-stop authenticity (1-10): Does this earn your attention at 2 AM?
2. Secret club worthiness: Would your equally-exhausted friends appreciate this?
3. Survivor reality (1-10): Does this recognize what it's like to just... keep going?
4. Honest vs performative: Real talk or LinkedIn theater?
5. Brand voice (1-10): Does this sound like Jesse's unhurried, dry-smart voice?

YOUR VERDICT (as Sarah):
- Would you engage with this?
- Would you remember this tomorrow?
- Does this make you want that $8.99 "didn't cry today" reward?

Respond with ONLY this JSON:
{{
    "score": [1-10 overall],
    "approved": [true if score >= 7 AND secret_club_worthy AND honest],
    "scroll_stop_authenticity": [1-10],
    "secret_club_worthy": [true/false],
    "survivor_reality": [1-10],
    "honest_vs_performative": ["honest" or "performative"],
    "brand_voice_fit": [1-10],
    "sarah_reaction": "[Your visceral first reaction in Sarah's voice]",
    "would_screenshot": [true/false],
    "feedback": "[Specific improvement suggestions if not approved]"
}}"""
        
        try:
            result = await self.generate(prompt)
            content = result.get("content", {})
            
            if isinstance(content, str):
                content = json.loads(content)
            
            score = float(content.get("score", 0))
            secret_club = content.get("secret_club_worthy", False)
            honest = content.get("honest_vs_performative", "performative") == "honest"
            
            # Sarah's approval requires passing her specific tests
            approved = score >= self.threshold and secret_club and honest
            
            criteria_breakdown = {
                "scroll_stop_authenticity": content.get("scroll_stop_authenticity", 0),
                "secret_club_worthy": secret_club,
                "survivor_reality": content.get("survivor_reality", 0),
                "honest_vs_performative": content.get("honest_vs_performative", "unknown"),
                "brand_voice_fit": content.get("brand_voice_fit", 0),
                "sarah_reaction": content.get("sarah_reaction", ""),
                "would_screenshot": content.get("would_screenshot", False)
            }
            
            feedback = content.get("feedback", "")
            if not approved and not feedback:
                if not secret_club:
                    feedback = "Not 'Work is Hell' WhatsApp worthy. Needs more authentic exhaustion recognition."
                elif not honest:
                    feedback = "Feels performative. Sarah can smell LinkedIn theater from a mile away."
                else:
                    feedback = "Didn't make Sarah pause at 2 AM. Needs more scroll-stop authenticity."
            
            self.logger.info(f"Sarah Chen validated post {post.post_number}: {score}/10 {'✅' if approved else '❌'}")
            
            return ValidationScore(
                agent_name="SarahChen",
                score=score,
                approved=approved,
                feedback=feedback,
                criteria_breakdown=criteria_breakdown
            )
            
        except Exception as e:
            self.logger.error(f"Sarah Chen validation failed: {e}")
            return ValidationScore(
                agent_name="SarahChen",
                score=0.0,
                approved=False,
                feedback=f"Validation error: {str(e)}",
                criteria_breakdown={"error": True}
            )