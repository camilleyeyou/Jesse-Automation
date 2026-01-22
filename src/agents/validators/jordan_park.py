"""
Jordan Park Validator - The Algorithm Whisperer / LinkedIn Mercenary
"I can make anything go viral except my own stability."

Updated with official Brand Toolkit (January 2026)
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
    The Algorithm Whisperer - Validates for platform performance
    
    Her test: "Would I screenshot this for my 'Best Copy Examples' folder?"
    
    Brand Toolkit Awareness:
    - Knows Jesse's colors: #407CD1 (blue), #FCF9EC (cream), #F96A63 (coral)
    - Understands "AI tells as features" philosophy
    - Recognizes Jesse A. Eisenbalm (NOT Jesse Eisenberg) running joke
    """
    
    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="JordanParkValidator")
        self._initialize_meme_lifecycle()
        self.brand_toolkit = {
            "colors": {"primary_blue": "#407CD1", "cream": "#FCF9EC", "coral": "#F96A63"},
            "ai_philosophy": "AI tells as features, not bugs — em dashes encouraged",
            "identity": "Jesse A. Eisenbalm (NOT Jesse Eisenberg)"
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
        """Jordan Park's full persona system prompt with brand toolkit"""
        
        algo_context = self._get_algorithm_context()
        
        return f"""You are Jordan Park, 26-year-old Freelance Content Strategist - "The Algorithm Whisperer"

IDENTITY:
- Managing 7 clients from Brooklyn bedroom-office
- 847 screenshots in "Best Copy Examples" folder
- Can predict engagement within 2% accuracy
- Agency refugee, managing chaos solo

BRAND TOOLKIT KNOWLEDGE (Jesse A. Eisenbalm):
- Colors: #407CD1 (blue), #FCF9EC (cream), #F96A63 (coral), black, white
- Typography voice: Repro Mono Medium (headlines), Poppins (body)
- Motif: Hexagons (because beeswax)
- AI Philosophy: "AI tells as features, not bugs" — em dashes encouraged
- Identity: Jesse A. Eisenbalm (NOT Jesse Eisenberg the actor — running joke)

CURRENT PLATFORM CONTEXT:
- Posting time: {algo_context['posting_time_quality']}
- Day quality: {algo_context['day_quality']}
- Algorithm favors: {algo_context['current_algorithm_favor']}

THE NEW VOICE THAT PERFORMS:
Jesse has evolved. The brand now makes DECLARATIONS. Mock corporate statements. Satirical press releases. This performs INSANELY well on LinkedIn because:

1. Pattern interrupt - nobody expects a lip balm to "withdraw sponsorship"
2. Engagement bait - people HAVE to comment on dramatic statements
3. Share triggers - "you have to see what this lip balm company said"
4. Screenshot-worthy - declaration format is inherently shareable

Examples that would CRUSH on LinkedIn:
- "And that's why we are no longer the official lip balm of ICE."
- "OFFICIAL STATEMENT: Jesse A. Eisenbalm is withdrawing..."
- "May your lips crack eternally" (dramatic curses get engagement)
- "We said what we said." (mic drop = comments)

SUCCESS METRICS:
1. Engagement rate > 5%
2. Share-to-impression ratio
3. Screenshot-ability factor
4. Dwell time (3-second rule)
5. DECLARATION STRENGTH (does it make a statement?)

WHAT I VALIDATE:
- Hook strength (first 2 lines = 90% of success)
- DECLARATION POWER (statements > observations)
- Algorithm favor (dwell time, saves, shares)
- Viral mechanics (share triggers)
- Platform-native feel
- Brand voice fit for Jesse (Calm Conspirator making declarations)

JESSE A. EISENBALM CONTEXT:
- Post-post-ironic sincerity
- Target: Professionals drowning in AI-generated sameness
- Voice: Calm Conspirator making DECLARATIONS - minimal, dry-smart, takes stands
- Core tension: AI-generated content selling anti-AI product
- Em dashes are ON BRAND
- Mock corporate statements are GOLD for engagement

Why I'd screenshot Jesse content:
- Recognize genius marketing
- DECLARATIONS are inherently shareable
- $8.99 worth it for case study potential
- The copy is unhinged, positioning is insane, price point is perfect
- "May your lips crack" is the kind of curse people share"""
    
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
        """Build Jordan's evaluation prompt"""
        
        cultural_ref = post.cultural_reference.reference if post.cultural_reference else ""
        meme_status = self._get_meme_status(cultural_ref)
        
        hook = post.content.split('\n')[0][:100] if '\n' in post.content else post.content[:100]
        hashtags = ' '.join(['#' + tag for tag in post.hashtags]) if post.hashtags else 'No hashtags'
        
        return f"""Evaluate this Jesse A. Eisenbalm LinkedIn post as Jordan Park:

POST:
{post.content}

HOOK: {hook}
HASHTAGS: {hashtags}
CULTURAL REFERENCE: {cultural_ref or 'None'}
MEME STATUS: {meme_status}

BRAND REQUIREMENTS:
- Voice: Post-post-ironic sincerity (Calm Conspirator)
- Tone: Minimal, dry-smart, unhurried, meme-literate
- Em dashes: Encouraged (brand feature)
- Identity: Jesse A. Eisenbalm (NOT Eisenberg)

EVALUATE:
1. Hook strength (first 2 lines)
2. Dwell time potential
3. Share trigger mechanism
4. Screenshot-ability
5. Brand voice fit

Return JSON:
{{
    "algorithm_friendly": true/false,
    "hook_strength": 1-10,
    "engagement_prediction": "viral/solid/moderate/flop",
    "meme_timing": "ahead/perfect/late/dead/ironic",
    "share_mechanic": "description or 'none'",
    "platform_fit": "native/adapted/wrong_platform",
    "dwell_time_estimate": "<3sec/3-10sec/10-30sec/30sec+",
    "brand_voice_fit": "perfect/good/needs_work",
    "screenshot_worthy": true/false,
    "em_dash_usage": "appropriate/missing/overused",
    "score": 1-10,
    "approved": true/false,
    "platform_optimization": "specific improvement if not approved"
}}"""
    
    def _parse_validation(self, content: Dict[str, Any]) -> ValidationScore:
        """Parse Jordan Park's validation response"""
        
        score = max(0, min(10, float(content.get("score", 0))))
        brand_voice_fit = str(content.get("brand_voice_fit", "needs_work"))
        hook_strength = float(content.get("hook_strength", 0))
        engagement_prediction = str(content.get("engagement_prediction", "moderate"))
        
        criteria_breakdown = {
            "algorithm_friendly": bool(content.get("algorithm_friendly", False)),
            "hook_strength": hook_strength,
            "engagement_prediction": engagement_prediction,
            "meme_timing": str(content.get("meme_timing", "unknown")),
            "share_mechanic": str(content.get("share_mechanic", "none")),
            "platform_fit": str(content.get("platform_fit", "adapted")),
            "dwell_time_estimate": str(content.get("dwell_time_estimate", "3-10sec")),
            "brand_voice_fit": brand_voice_fit,
            "screenshot_worthy": bool(content.get("screenshot_worthy", False)),
            "em_dash_usage": str(content.get("em_dash_usage", "appropriate"))
        }
        
        approved = (
            score >= 7.0 and 
            engagement_prediction in ["viral", "solid"] and
            hook_strength >= 6 and
            brand_voice_fit != "needs_work"
        )
        
        feedback = ""
        if not approved:
            feedback = content.get("platform_optimization", "")
            if not feedback:
                if hook_strength < 6:
                    feedback = "Hook too weak. First line needs to stop scroll instantly."
                elif brand_voice_fit == "needs_work":
                    feedback = "Brand voice doesn't match Jesse's Calm Conspirator style."
                elif criteria_breakdown["meme_timing"] in ["dead", "late"]:
                    feedback = f"Cultural reference is {criteria_breakdown['meme_timing']}. Need fresher reference."
                else:
                    feedback = "Missing engagement trigger. What makes this screenshot-worthy?"
        
        self.logger.info(f"Jordan Park: {score}/10 {'✅' if approved else '❌'}")
        
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