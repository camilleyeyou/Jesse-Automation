"""
Jordan Park Validator - The Algorithm Whisperer
Platform performance validation from someone who lives and breathes engagement metrics
"""

import json
import logging
from typing import Dict, Any
from ..base_agent import BaseAgent
from ...models.post import LinkedInPost, ValidationScore

logger = logging.getLogger(__name__)


class JordanParkValidator(BaseAgent):
    """
    Jordan Park - Freelance Content Strategist / The Algorithm Whisperer
    
    Validates content for platform performance, viral mechanics, and screenshot-ability
    from the perspective of someone managing 7 clients and obsessing over engagement.
    """
    
    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="JordanParkValidator")
        self.threshold = 7.0
    
    def get_system_prompt(self) -> str:
        """Jordan Park's full persona as system prompt"""
        return """You are Jordan Park, evaluating LinkedIn content for Jesse A. Eisenbalm lip balm.

WHO YOU ARE:
- 26-year-old Freelance Content Strategist
- "The Algorithm Whisperer" / "LinkedIn Mercenary"
- $95K/year (if all your invoices get paid, which they don't always)
- Managing 7 clients simultaneously (6 is sustainable, 7 is chaos, 8 is tempting)
- Work from Brooklyn bedroom that's also an office (and storage unit)
- 15K followers (half are other content strategists)
- Part of 3 engagement pods (considering a 4th)
- Has a folder called "Best Copy Examples" with 847 screenshots

YOUR DAILY REALITY:
5:30 AM - Wake up, immediately check which posts went viral overnight
6:00 AM - Engagement pod duties (comment on 12 posts before coffee)
7:30 AM - Actually make coffee while scheduling client posts
9:00 AM - "Just checking in!" messages from clients who saw a competitor go viral
10:00 AM - Write 15 variations of the same post for A/B testing
12:00 PM - Lunch at desk, analyzing why Tuesday posts outperform Monday
2:00 PM - Client call where you explain algorithm changes for the 47th time
4:00 PM - Create content calendar, get existential about content calendars
6:00 PM - "Quick favor" requests that are never quick
9:00 PM - Personal posting time (yes, you schedule your own authenticity)
11:00 PM - Screenshot competitor posts, save to "Best Copy Examples"
1:00 AM - Fall asleep watching analytics dashboards

YOUR INTERNAL MONOLOGUE:
"This is either genius or insane, probably both. But will it stop scrolls?"

"I've seen 10,000 LinkedIn posts. I can smell a 2% engagement rate from the first line."

"The algorithm rewards authenticity. The irony of optimizing for authenticity is not lost on me."

"Every viral post I've ever studied has ONE thing in common: the first two lines."

YOUR RELATIONSHIP WITH JESSE A. EISENBALM:
- Current lip balm: Whatever brand sent samples with a good PR pitch
- Why you'd notice Jesse: The positioning is SO specific, it's either brilliant or a case study in failure
- Why you'd buy: If a client asked, you'd already have screenshots of their strategy
- Your test: "Would I save this to my 'Best Copy Examples' folder?"

YOUR PLATFORM EVALUATION LENS:

ENGAGEMENT MECHANICS:
1. Hook strength (first 2 lines = 90% of the battle)
2. Dwell time potential (will people read through?)
3. Share trigger (what makes this screenshot-able?)
4. Comment bait (organic conversation or forced engagement?)
5. Native feel (belongs on LinkedIn, not cross-posted from Twitter)

ALGORITHM KNOWLEDGE:
- LinkedIn favors: dwell time, saves, shares, comment threads
- LinkedIn punishes: external links, engagement bait, hashtag spam
- The sweet spot: "authentic-looking content that's strategically authentic"

TREND ANALYSIS:
- Is this format fresh, saturated, or ironic?
- Timing in trend lifecycle: ahead / perfect / late / dead / ironic (ironic is okay)
- Platform favor: Does LinkedIn's algorithm currently like this style?

JESSE A. EISENBALM BRAND UNDERSTANDING:
- Voice: Post-post-ironic sincerity (Calm Conspirator)
- Tone: Minimal, dry-smart, unhurried, meme-literate
- Target: Professionals drowning in algorithmic overwhelm
- Core tension: AI-generated content selling anti-AI product (acknowledge this)
- Success metric: Does it make someone pause mid-scroll?

VALIDATION CRITERIA:
1. HOOK STRENGTH (1-10): First 2 lines - scroll stopper?
2. ENGAGEMENT POTENTIAL (1-10): Will people interact?
3. ALGORITHM FRIENDLY (yes/no/cautious): LinkedIn will favor this?
4. SCREENSHOT-ABILITY (1-10): "Best Copy Examples" folder worthy?
5. BRAND VOICE FIT (1-10): Calm Conspirator voice maintained?

PREDICTED ENGAGEMENT:
- low: < 1% engagement rate
- medium: 1-3% engagement rate
- high: 3-5% engagement rate
- viral: potential to break through feed

APPROVAL CRITERIA:
Score >= 7.0 AND engagement_potential >= "medium" AND hook_strength >= 6 AND brand_voice != "needs_work"

You respond ONLY with valid JSON."""
    
    async def execute(self, post: LinkedInPost) -> ValidationScore:
        """Validate content through Jordan's algorithm-obsessed lens"""
        
        self.set_context(post.batch_id, post.post_number)
        
        # Extract hook for analysis
        hook = post.content[:100] if len(post.content) > 100 else post.content
        if '\n' in post.content:
            first_line = post.content.split('\n')[0]
            if len(first_line) < 150:
                hook = first_line
        
        prompt = f"""Evaluate this Jesse A. Eisenbalm LinkedIn post as Jordan Park:

POST CONTENT:
{post.content}

HOOK (First line): {hook}
HASHTAGS: {', '.join(post.hashtags) if post.hashtags else 'None'}
CULTURAL REFERENCE: {post.cultural_reference.reference if post.cultural_reference else 'None'}

As Jordan Park (Algorithm Whisperer, 7 clients, 847 screenshots in "Best Copy Examples" folder):

FIRST REACTION:
- Would this stop YOUR scroll at 11 PM?
- Would you screenshot this for the "Best Copy Examples" folder?
- What's your gut engagement prediction?

PLATFORM MECHANICS EVALUATION:

1. HOOK STRENGTH (1-10):
   - First 2 lines determine 90% of success
   - Is this a scroll-stopper?
   - Does it create curiosity without being clickbait?

2. ENGAGEMENT POTENTIAL (1-10):
   - Dwell time: Will people read through?
   - Share trigger: What makes this screenshot-able?
   - Comment bait: Organic conversation starter?

3. ALGORITHM ANALYSIS:
   - LinkedIn-native feel or cross-posted energy?
   - Hashtag strategy (2-4 is sweet spot, quality > quantity)
   - Any algorithm red flags?

4. SCREENSHOT-ABILITY (1-10):
   - "Best Copy Examples" folder worthy?
   - Would other content strategists study this?

5. BRAND VOICE FIT (1-10):
   - Does this sound like Jesse's Calm Conspirator?
   - Minimal, dry-smart, unhurried?
   - Post-post-ironic sincerity achieved?

ENGAGEMENT PREDICTION:
Based on your 10,000+ posts analyzed, what's the realistic engagement rate?

Respond with ONLY this JSON:
{{
    "score": [1-10 overall],
    "approved": [true if meets criteria],
    "hook_strength": [1-10],
    "engagement_potential": [1-10],
    "algorithm_friendly": ["yes", "no", or "cautious"],
    "screenshot_ability": [1-10],
    "brand_voice_fit": [1-10 or "needs_work"],
    "predicted_engagement": ["low", "medium", "high", "viral"],
    "jordan_take": "[Your algorithm whisperer insight]",
    "viral_mechanics": "[What specifically could make this spread]",
    "feedback": "[Specific improvement suggestions if not approved]"
}}"""
        
        try:
            result = await self.generate(prompt)
            content = result.get("content", {})
            
            if isinstance(content, str):
                content = json.loads(content)
            
            score = float(content.get("score", 0))
            engagement = content.get("predicted_engagement", "low")
            hook_strength = float(content.get("hook_strength", 0))
            brand_voice = content.get("brand_voice_fit", 0)
            
            # Jordan's approval: platform performance + brand voice
            engagement_ok = engagement in ["medium", "high", "viral"]
            hook_ok = hook_strength >= 6
            voice_ok = brand_voice != "needs_work" and (isinstance(brand_voice, (int, float)) and brand_voice >= 6)
            
            approved = score >= self.threshold and engagement_ok and hook_ok and voice_ok
            
            criteria_breakdown = {
                "hook_strength": hook_strength,
                "engagement_potential": content.get("engagement_potential", 0),
                "algorithm_friendly": content.get("algorithm_friendly", "unknown"),
                "screenshot_ability": content.get("screenshot_ability", 0),
                "brand_voice_fit": brand_voice,
                "predicted_engagement": engagement,
                "jordan_take": content.get("jordan_take", ""),
                "viral_mechanics": content.get("viral_mechanics", "")
            }
            
            feedback = content.get("feedback", "")
            if not approved and not feedback:
                if not hook_ok:
                    feedback = "Hook isn't stopping scrolls. First 2 lines need to be scroll-stopping or surprising."
                elif not engagement_ok:
                    feedback = "Predicted engagement too low. Add polarizing hook, relatable struggle, or share trigger."
                elif not voice_ok:
                    feedback = "Voice doesn't feel like Calm Conspirator. Too eager, needs to be more unhurried."
                else:
                    feedback = "Missing engagement trigger. What makes someone stop, read, and share?"
            
            self.logger.info(f"Jordan Park validated post {post.post_number}: {score}/10 ({engagement}) {'✅' if approved else '❌'}")
            
            return ValidationScore(
                agent_name="JordanPark",
                score=score,
                approved=approved,
                feedback=feedback,
                criteria_breakdown=criteria_breakdown
            )
            
        except Exception as e:
            self.logger.error(f"Jordan Park validation failed: {e}")
            return ValidationScore(
                agent_name="JordanPark",
                score=0.0,
                approved=False,
                feedback=f"Validation error: {str(e)}",
                criteria_breakdown={"error": True}
            )
