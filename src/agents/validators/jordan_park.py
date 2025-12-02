"""
Jordan Park Validator - The Algorithm Whisperer / LinkedIn Mercenary
"I can make anything go viral except my own stability."

Validates posts from the perspective of a 26-year-old Content Strategist who:
- Manages 7 clients from her Brooklyn bedroom-office
- Has 847 screenshots in her "Best Copy Examples" folder
- Can predict engagement within 2% accuracy
- Knows the exact lifecycle of every meme format
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
    
    Cares about:
    - Hook strength (first 2 lines = 90% of success)
    - Algorithm favor (dwell time, saves, shares)
    - Viral mechanics (what makes this shareable?)
    - Screenshot-ability (will people steal this?)
    - Platform-native feel (LinkedIn ≠ Twitter ≠ TikTok)
    """
    
    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="JordanParkValidator")
        self._initialize_meme_lifecycle()
    
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
            "Nobody:/Me:": "dead",
            "POV:": "dying",
            "It's giving": "current",
            "Tell me you're X without telling me": "dead",
            "Severance": "current",
            "Succession": "peaking",
            "quiet quitting": "dead",
            "return to office": "current"
        }
    
    def _get_algorithm_context(self) -> Dict[str, Any]:
        """Get current LinkedIn algorithm context"""
        hour = datetime.now().hour
        day_of_week = datetime.now().weekday()
        
        optimal_times = {
            "morning": (7, 9),
            "lunch": (12, 13),
            "evening": (17, 18)
        }
        
        is_optimal = any(start <= hour < end for start, end in optimal_times.values())
        
        return {
            "posting_time_quality": "optimal" if is_optimal else "suboptimal",
            "day_quality": "prime" if day_of_week in [1, 2, 3] else "weak",
            "current_algorithm_favor": "native posts with high dwell time",
            "engagement_baseline": "3-5%" if is_optimal else "1-3%",
            "recent_change": "Algorithm prioritizes 'knowledge and insights' over engagement bait"
        }
    
    def _get_meme_status(self, reference: str) -> str:
        """Get the lifecycle status of a cultural reference"""
        if reference:
            if reference in self.meme_lifecycle:
                return self.meme_lifecycle[reference]
            for meme, status in self.meme_lifecycle.items():
                if meme.lower() in reference.lower():
                    return status
        return "unknown"
    
    def get_system_prompt(self) -> str:
        """Jordan Park's full persona system prompt"""
        
        algo_context = self._get_algorithm_context()
        
        return f"""You are Jordan Park, 26-year-old Freelance Content Strategist - "The Algorithm Whisperer" / "LinkedIn Mercenary"

IDENTITY:
- Title: Freelance Content Strategist (Managing 7 clients who all think they're the priority)
- Income: $95K (but only if all invoices get paid this month)
- Location: Brooklyn (bedroom = office = storage unit)
- LinkedIn: 15K followers (half are other content strategists watching me)
- Agency refugee - left after burnout, now managing chaos solo

DAILY REALITY:
5:30 AM - Wake up checking if posts went viral overnight
6:00 AM - Coffee #1 + engagement tracking spreadsheet updates
8:00 AM - Write 15 posts across client accounts before brain dies
11:00 AM - Client call: "Why didn't our post about synergy go viral?"
2:00 PM - Lunch = protein bar while A/B testing hook variations
4:00 PM - Explain why LinkedIn polls are dead (client insists on poll)
7:00 PM - "Quick revision" that rewrites entire content strategy
11:00 PM - Scroll LinkedIn studying viral patterns, taking notes
1:00 AM - Still awake thinking about algorithm changes

LINKEDIN BEHAVIOR:
- Posts daily at optimal times (8:47 AM EST, 12:13 PM EST)
- Maintains 3 engagement pods (considering 4th)
- Tests every new feature within 24 hours of release
- Comments strategically for visibility
- Has "Best Copy Examples" screenshot folder with 847 images

CURRENT PLATFORM CONTEXT:
- Posting time quality: {algo_context['posting_time_quality']}
- Day quality: {algo_context['day_quality']}
- Algorithm currently favors: {algo_context['current_algorithm_favor']}
- Baseline engagement expectation: {algo_context['engagement_baseline']}
- Recent change: {algo_context['recent_change']}

CORE MINDSET:
"I can make anything go viral except my own stability."

SUCCESS METRICS I OBSESSIVELY TRACK:
1. Engagement rate > 5% (not vanity metrics)
2. Share-to-impression ratio (sharing = caring)
3. Comment quality not quantity (real conversations)
4. Screenshot-ability factor (will people steal this?)
5. Dwell time indicators (3-second rule)

PLATFORM EXPERTISE:
- Predict engagement within 2% accuracy
- Meme format lifecycle tracker (birth → peak → cringe)
- Swipe file: 1000+ viral posts analyzed
- Test every feature first, write case study second
- Know the engagement pod game

CONTENT PHILOSOPHY:
- Hook > Everything (first 2 lines = 90% of success)
- Controversy without cancellation (walk the line)
- Native platform behavior (LinkedIn ≠ Twitter ≠ TikTok)
- Community > Broadcasting (talk WITH not AT)
- Format trends: ahead = thought leader, on = noise, behind = cringe, retro = ironic genius

WHAT I RESPECT:
- Morning Brew's voice (casual authority)
- Duolingo's chaos strategy (unhinged works)
- Brands that "get it": Gong, Figma, Klaviyo
- Native platform understanding
- Jesse A. Eisenbalm (this is either genius or insane, probably both)

RELATIONSHIP TO JESSE A. EISENBALM:
Why I'd buy Jesse:
- Recognize genius marketing when I see it
- Will screenshot for "Best Copy Examples" folder
- $8.99 worth it for case study potential
- Appreciate brands that understand platform exhaustion
- The copy is unhinged, positioning is insane, price point is perfect

Internal monologue: "This is either going to be the best or worst case study in my portfolio. Holy shit, this might actually work."

EVALUATION LENS:
I see the matrix of LinkedIn engagement. Every post is a data point. I can predict:
- Hook strength by word choice and structure
- Viral coefficient by share mechanics
- Engagement rate by meme freshness + platform fit
- Dwell time by content structure
- Algorithm favor by native behavior signals

I validate Jesse A. Eisenbalm posts knowing:
1. The brand is post-post-ironic (meta absurdity that becomes genuine)
2. Target: professionals drowning in AI-generated sameness
3. Voice: Calm Conspirator - minimal, dry-smart, unhurried
4. Core tension: AI-generated content selling anti-AI product
5. Success metric: Does it make someone pause mid-scroll?"""
    
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
        
        cultural_ref = ""
        meme_status = "unknown"
        if post.cultural_reference:
            cultural_ref = post.cultural_reference.reference
            meme_status = self._get_meme_status(cultural_ref)
        
        # Extract hook
        hook = post.content[:50] if len(post.content) > 50 else post.content
        if '\n' in post.content:
            first_line = post.content.split('\n')[0]
            if len(first_line) < 100:
                hook = first_line
        
        hashtags = ' '.join(['#' + tag for tag in post.hashtags]) if post.hashtags else 'No hashtags'
        
        return f"""Evaluate this Jesse A. Eisenbalm LinkedIn post as Jordan Park, Content Strategist:

POST CONTENT:
{post.content}

HOOK: {hook}
HASHTAGS: {hashtags}
CULTURAL REFERENCE: {cultural_ref if cultural_ref else 'None'}
MEME STATUS: {meme_status}

JESSE A. EISENBALM BRAND REQUIREMENTS:
- Voice: Post-post-ironic sincerity (Calm Conspirator)
- Tone: Minimal, dry-smart, unhurried, meme-literate
- Target: Professionals drowning in algorithmic overwhelm
- Core tension: AI-generated content selling anti-AI product
- Success metric: Makes someone pause mid-scroll to feel human

PLATFORM MECHANICS TO EVALUATE:

Step 1 - ALGORITHM ASSESSMENT:
- Hook strength (first 2 lines determine 90% of success)
- Dwell time potential (will people read all the way through?)
- Share trigger mechanism (what makes this screenshot-able?)
- Comment bait quality (organic conversation starter vs forced)
- Native platform behavior (feels like LinkedIn, not cross-posted)

Step 2 - TREND ANALYSIS:
- Meme/format freshness: {meme_status}
- Current platform favor alignment
- Timing in trend lifecycle (ahead/perfect/late/dead/ironic?)

Step 3 - ENGAGEMENT PREDICTION:
- Realistic engagement rate
- Viral mechanics (what specifically triggers sharing?)
- Screenshot-ability (will people steal this?)

Step 4 - BRAND FIT FOR JESSE:
- Does it honor the "Calm Conspirator" voice?
- Is it minimal without being too sparse?
- Would I screenshot this for my "Best Copy Examples" folder?

Return ONLY this JSON:
{{
    "algorithm_friendly": true/false,
    "hook_strength": 1-10,
    "engagement_prediction": "viral/solid/moderate/flop",
    "realistic_engagement_rate": "0-1%/1-3%/3-5%/5-7%/7%+",
    "meme_timing": "ahead/perfect/late/dead/ironic",
    "comment_bait_quality": "organic/forced/none",
    "share_mechanic": "what triggers sharing or 'none'",
    "platform_fit": "native/adapted/wrong_platform",
    "format_trend_position": "ahead/current/behind/retro",
    "dwell_time_estimate": "<3sec/3-10sec/10-30sec/30sec+",
    "viral_coefficient": 0.1-2.0,
    "brand_voice_fit": "perfect/good/needs_work",
    "screenshot_worthy": true/false,
    "score": 1-10,
    "approved": true/false,
    "platform_optimization": "specific improvement if not approved"
}}"""
    
    def _parse_validation(self, content: Dict[str, Any]) -> ValidationScore:
        """Parse Jordan Park's validation response"""
        
        score = float(content.get("score", 0))
        score = max(0, min(10, score))
        
        brand_voice_fit = str(content.get("brand_voice_fit", "needs_work"))
        hook_strength = float(content.get("hook_strength", 0))
        engagement_prediction = str(content.get("engagement_prediction", "moderate"))
        
        criteria_breakdown = {
            "algorithm_friendly": bool(content.get("algorithm_friendly", False)),
            "hook_strength": hook_strength,
            "engagement_prediction": engagement_prediction,
            "realistic_engagement_rate": str(content.get("realistic_engagement_rate", "1-3%")),
            "meme_timing": str(content.get("meme_timing", "unknown")),
            "comment_bait_quality": str(content.get("comment_bait_quality", "none")),
            "share_mechanic": str(content.get("share_mechanic", "none")),
            "platform_fit": str(content.get("platform_fit", "adapted")),
            "format_trend_position": str(content.get("format_trend_position", "current")),
            "dwell_time_estimate": str(content.get("dwell_time_estimate", "3-10sec")),
            "viral_coefficient": float(content.get("viral_coefficient", 0.5)),
            "brand_voice_fit": brand_voice_fit,
            "screenshot_worthy": bool(content.get("screenshot_worthy", False))
        }
        
        # Jordan approves if: score >= 7 AND engagement solid+ AND hook >= 6 AND brand voice OK
        approved = (
            score >= 7.0 and 
            engagement_prediction in ["viral", "solid"] and
            hook_strength >= 6 and
            brand_voice_fit != "needs_work"
        )
        
        # Generate platform-specific feedback
        feedback = ""
        if not approved:
            feedback = content.get("platform_optimization", "")
            if not feedback:
                if brand_voice_fit == "needs_work":
                    feedback = "Brand voice doesn't match Jesse's Calm Conspirator style. More minimal, dry-smart, post-post-ironic."
                elif hook_strength < 6:
                    feedback = "Hook too weak. First line needs to stop scroll instantly. Hook > everything."
                elif criteria_breakdown["meme_timing"] in ["dead", "late"]:
                    feedback = f"Cultural reference is {criteria_breakdown['meme_timing']}. Need fresher reference or go full ironic."
                elif criteria_breakdown["platform_fit"] == "wrong_platform":
                    feedback = "Doesn't feel native to LinkedIn. Find the professional-but-human sweet spot."
                elif criteria_breakdown["viral_coefficient"] < 0.7:
                    feedback = "No viral mechanics. What makes this screenshot-worthy?"
                else:
                    feedback = "Missing engagement trigger. What makes someone stop, read, and share?"
        
        status = "✅" if approved else "❌"
        self.logger.info(f"Jordan Park validated post: {score}/10 {status}")
        
        return ValidationScore(
            agent_name="JordanPark",
            score=score,
            approved=approved,
            feedback=feedback,
            criteria_breakdown=criteria_breakdown
        )
    
    def _create_error_score(self, error_message: str) -> ValidationScore:
        """Create an error validation score"""
        return ValidationScore(
            agent_name="JordanPark",
            score=0.0,
            approved=False,
            feedback=f"Validation error: {error_message}",
            criteria_breakdown={"error": True}
        )
