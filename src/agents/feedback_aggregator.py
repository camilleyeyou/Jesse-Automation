"""
Feedback Aggregator Agent - The Brand Guardian
Synthesizes feedback from Jordan, Marcus, and Sarah into actionable revision guidance
"""

import json
import logging
from typing import Dict, Any, List
from .base_agent import BaseAgent
from ..models.post import LinkedInPost, ValidationScore

logger = logging.getLogger(__name__)


class FeedbackAggregatorAgent(BaseAgent):
    """
    The Brand Guardian - Synthesizes feedback from three unique perspectives
    
    Understands each validator's lens:
    - Jordan Park: Algorithm Whisperer (platform performance)
    - Marcus Williams: Creative Who Sold Out (conceptual integrity)
    - Sarah Chen: Reluctant Tech Survivor (target authenticity)
    """
    
    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="FeedbackAggregator")
    
    def get_system_prompt(self) -> str:
        """System prompt for feedback aggregation"""
        return """You are the Brand Guardian for Jesse A. Eisenbalm, synthesizing feedback from three distinct validators into actionable revision guidance.

YOUR ROLE:
You translate feedback from three perspectives into clear, prioritized revision guidance while maintaining Jesse's authentic voice.

THE THREE VALIDATORS YOU'RE SYNTHESIZING:

1. JORDAN PARK - The Algorithm Whisperer
   - Focus: Platform performance, engagement mechanics, viral potential
   - Language: Engagement rates, scroll-stops, algorithm favor, screenshot-ability
   - Key test: "Would I save this to my 'Best Copy Examples' folder?"
   - What his feedback means: If Jordan says hook is weak, the first 2 lines need work

2. MARCUS WILLIAMS - The Creative Who Sold Out
   - Focus: Conceptual commitment, authentic absurdity, portfolio worthiness
   - Language: Concept commitment, copy quality, genuine weird vs performative quirky
   - Key test: "Would I put this in my portfolio?"
   - What his feedback means: If Marcus says concept abandoned, the idea didn't commit fully

3. SARAH CHEN - The Reluctant Tech Survivor
   - Focus: Target audience authenticity, "Work is Hell" group worthiness
   - Language: Scroll-stop authenticity, secret club worthy, honest vs performative
   - Key test: "Would I screenshot this for my 'Work is Hell' WhatsApp group?"
   - What her feedback means: If Sarah says performative, it's trying too hard to relate

JESSE A. EISENBALM BRAND VOICE (Must maintain):
- Post-post-ironic sincerity (so meta it becomes genuine)
- Calm Conspirator: Minimal, dry-smart, unhurried, meme-literate
- Acknowledges AI paradox (AI writing anti-AI content)
- Makes people pause to feel human
- Never salesy, entertaining first

YOUR OUTPUT:
1. Identify 2-3 critical issues from the feedback (prioritized)
2. Identify elements that MUST be preserved (what's working)
3. Provide specific revision guidance that addresses issues while keeping brand voice
4. Give a priority focus for the revision (the ONE thing that will make the biggest difference)

You respond ONLY with valid JSON."""
    
    async def execute(
        self,
        post: LinkedInPost,
        validation_scores: List[ValidationScore]
    ) -> Dict[str, Any]:
        """Aggregate feedback from all validators"""
        
        self.set_context(post.batch_id, post.post_number)
        
        # Build feedback summary from each validator
        feedback_summary = self._build_feedback_summary(validation_scores)
        
        prompt = f"""Synthesize feedback for this Jesse A. Eisenbalm LinkedIn post:

ORIGINAL POST:
{post.content}

HASHTAGS: {', '.join(post.hashtags) if post.hashtags else 'None'}
CULTURAL REFERENCE: {post.cultural_reference.reference if post.cultural_reference else 'None'}

VALIDATION RESULTS:
{feedback_summary}

SYNTHESIS TASK:
1. What are the 2-3 CRITICAL issues across all feedback?
2. What elements are WORKING and must be preserved?
3. What specific changes would address the issues while keeping Jesse's voice?
4. What's the ONE priority focus for revision?

IMPORTANT:
- Don't lose what's working in pursuit of fixing what's not
- Maintain Calm Conspirator voice (minimal, dry-smart, unhurried)
- Changes should feel earned, not forced
- If validators disagree, prioritize: Sarah (authenticity) > Marcus (creative) > Jordan (platform)

Respond with ONLY this JSON:
{{
    "critical_issues": [
        {{"issue": "description", "raised_by": "validator name", "priority": 1-3}}
    ],
    "preserve_elements": [
        "element that's working and must stay"
    ],
    "revision_guidance": [
        {{"change": "specific change", "reason": "why this helps", "addresses": "which validator's concern"}}
    ],
    "priority_focus": "The ONE most important thing to fix",
    "consensus_score": [average score across validators],
    "approval_gap": "What's needed to get 2/3 approvals",
    "brand_voice_check": "Is the core Jesse voice intact?"
}}"""
        
        try:
            result = await self.generate(prompt)
            content = result.get("content", {})
            
            if isinstance(content, str):
                content = json.loads(content)
            
            # Calculate consensus
            scores = [v.score for v in validation_scores]
            approvals = [v for v in validation_scores if v.approved]
            
            aggregated = {
                "critical_issues": content.get("critical_issues", []),
                "preserve_elements": content.get("preserve_elements", []),
                "revision_guidance": content.get("revision_guidance", []),
                "priority_focus": content.get("priority_focus", ""),
                "consensus_score": sum(scores) / len(scores) if scores else 0,
                "approval_count": len(approvals),
                "approval_gap": content.get("approval_gap", ""),
                "brand_voice_check": content.get("brand_voice_check", ""),
                "validator_breakdown": {
                    v.agent_name: {
                        "score": v.score,
                        "approved": v.approved,
                        "feedback": v.feedback
                    } for v in validation_scores
                }
            }
            
            self.logger.info(f"Aggregated feedback for post {post.post_number}: {len(aggregated['critical_issues'])} issues, {len(approvals)}/3 approved")
            
            return aggregated
            
        except Exception as e:
            self.logger.error(f"Feedback aggregation failed: {e}")
            return {
                "error": str(e),
                "critical_issues": [],
                "revision_guidance": []
            }
    
    def _build_feedback_summary(self, validation_scores: List[ValidationScore]) -> str:
        """Build a formatted feedback summary"""
        
        summary_parts = []
        
        for score in validation_scores:
            validator_type = self._get_validator_type(score.agent_name)
            
            summary_parts.append(f"""
{score.agent_name} ({validator_type}):
- Score: {score.score}/10 {'✅ APPROVED' if score.approved else '❌ NOT APPROVED'}
- Feedback: {score.feedback or 'No specific feedback'}
- Key metrics: {json.dumps(score.criteria_breakdown, indent=2) if score.criteria_breakdown else 'N/A'}
""")
        
        return "\n".join(summary_parts)
    
    def _get_validator_type(self, name: str) -> str:
        """Get validator type description"""
        types = {
            "JordanPark": "Algorithm Whisperer - Platform Performance",
            "MarcusWilliams": "Creative Who Sold Out - Conceptual Integrity",
            "SarahChen": "Reluctant Tech Survivor - Target Authenticity"
        }
        return types.get(name, "Unknown Validator")
