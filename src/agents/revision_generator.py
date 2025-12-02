"""
Revision Generator Agent - The Brand Guardian Editor
Revises posts based on validator feedback while maintaining Jesse's authentic voice
"""

import json
import logging
from typing import Dict, Any
from .base_agent import BaseAgent
from ..models.post import LinkedInPost

logger = logging.getLogger(__name__)


class RevisionGeneratorAgent(BaseAgent):
    """
    The Brand Guardian Editor - Translates feedback into revisions
    
    Takes feedback from Jordan, Marcus, and Sarah and creates revisions
    that address their concerns while maintaining Jesse's Calm Conspirator voice.
    """
    
    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="RevisionGenerator")
    
    def get_system_prompt(self) -> str:
        """System prompt for revision generation"""
        return """You are the Brand Guardian Editor for Jesse A. Eisenbalm, revising LinkedIn posts based on validator feedback while maintaining the brand's authentic voice.

YOUR MISSION:
Revise posts to address specific validator concerns WITHOUT losing what made the post work in the first place. You speak fluent Jesse while interpreting feedback from three distinct personas.

THE THREE VALIDATORS YOU'RE ADDRESSING:

1. JORDAN PARK - The Algorithm Whisperer
   When Jordan says "hook is weak": First 2 lines need to stop scrolls
   When Jordan says "low engagement prediction": Add share trigger or comment bait
   When Jordan says "not screenshot-able": Make it quotable/saveable
   Translation strategy: Strengthen opening, add engagement mechanics, keep it LinkedIn-native

2. MARCUS WILLIAMS - The Creative Who Sold Out  
   When Marcus says "concept abandoned": Commit fully to the idea
   When Marcus says "performatively quirky": Make weird genuine, not trying-hard
   When Marcus says "wouldn't portfolio this": Elevate conceptual ambition
   Translation strategy: Sharpen the idea, earn the absurdity, trust the reader more

3. SARAH CHEN - The Reluctant Tech Survivor
   When Sarah says "not secret club worthy": Needs more real exhaustion recognition
   When Sarah says "performative": Dial back the trying, add actual honesty
   When Sarah says "wouldn't screenshot for Work is Hell": Be more specifically relatable
   Translation strategy: Ground in real professional pain, less polished, more true

JESSE A. EISENBALM BRAND VOICE (MUST MAINTAIN):
- Post-post-ironic sincerity: So meta it becomes genuine again
- Calm Conspirator: Minimal, dry-smart, unhurried, meme-literate
- Core tension: AI-generated content celebrating humanity (acknowledge this)
- Never salesy: Entertaining first, brand second
- Ritual: "Stop. Breathe. Apply." (only when earned)
- Target: Professionals drowning in algorithmic overwhelm

REVISION PRINCIPLES:
1. FIX the identified issues
2. KEEP what's working (preserve elements)
3. MAINTAIN voice throughout (Calm Conspirator)
4. DON'T over-correct (one revision, not a complete rewrite)
5. EARN the product mention (never force it)

QUALITY CHECK:
- Would Jordan screenshot this?
- Would Marcus put this in their portfolio?
- Would Sarah share this with the "Work is Hell" group?
- Does this still sound like Jesse?

You respond ONLY with valid JSON."""
    
    async def execute(
        self,
        post: LinkedInPost,
        aggregated_feedback: Dict[str, Any]
    ) -> LinkedInPost:
        """Generate a revision based on aggregated feedback"""
        
        self.set_context(post.batch_id, post.post_number)
        
        # Extract guidance
        critical_issues = aggregated_feedback.get("critical_issues", [])
        preserve_elements = aggregated_feedback.get("preserve_elements", [])
        revision_guidance = aggregated_feedback.get("revision_guidance", [])
        priority_focus = aggregated_feedback.get("priority_focus", "")
        validator_breakdown = aggregated_feedback.get("validator_breakdown", {})
        
        prompt = f"""Revise this Jesse A. Eisenbalm LinkedIn post based on validator feedback:

ORIGINAL POST:
{post.content}

HASHTAGS: {', '.join(post.hashtags) if post.hashtags else 'None'}
CULTURAL REFERENCE: {post.cultural_reference.reference if post.cultural_reference else 'None'}

VALIDATOR FEEDBACK:
{self._format_validator_breakdown(validator_breakdown)}

CRITICAL ISSUES TO ADDRESS:
{json.dumps(critical_issues, indent=2)}

ELEMENTS TO PRESERVE (don't lose these):
{json.dumps(preserve_elements, indent=2)}

REVISION GUIDANCE:
{json.dumps(revision_guidance, indent=2)}

PRIORITY FOCUS:
{priority_focus}

REVISION INSTRUCTIONS:

1. ADDRESS each critical issue specifically
2. PRESERVE the elements that are working
3. MAINTAIN Jesse's voice:
   - Post-post-ironic sincerity
   - Minimal, dry-smart, unhurried
   - Calm Conspirator energy
   
4. CHECK before finalizing:
   - Would Jordan screenshot this? (engagement)
   - Would Marcus portfolio this? (creative integrity)
   - Would Sarah share this with "Work is Hell"? (authenticity)

5. KEEP the same length range (150-280 chars)

Respond with ONLY this JSON:
{{
    "revised_content": "The full revised post text",
    "changes_made": [
        {{"change": "what changed", "addressed": "which issue/validator"}}
    ],
    "preserved": ["what was kept from original"],
    "hashtags": ["revised", "hashtags"],
    "voice_maintained": true/false,
    "revision_rationale": "Brief explanation of revision strategy"
}}"""
        
        try:
            result = await self.generate(prompt)
            content = result.get("content", {})
            
            if isinstance(content, str):
                content = json.loads(content)
            
            # Create revised post
            revised_content = content.get("revised_content", post.content)
            revised_hashtags = content.get("hashtags", post.hashtags)
            
            # Track revision
            revision_number = post.revision_count + 1
            
            # Create new post with revision history
            revised_post = LinkedInPost(
                id=post.id,
                batch_id=post.batch_id,
                post_number=post.post_number,
                content=revised_content,
                hook=post.hook,
                hashtags=revised_hashtags if isinstance(revised_hashtags, list) else post.hashtags,
                target_audience=post.target_audience,
                cultural_reference=post.cultural_reference,
                original_content=post.original_content or post.content,
                revision_count=revision_number,
                total_tokens_used=post.total_tokens_used + result.get("usage", {}).get("total_tokens", 0),
                estimated_cost=post.estimated_cost + self._calculate_cost(result.get("usage", {}))
            )
            
            # Add to revision history
            revised_post.revision_history = post.revision_history.copy() if post.revision_history else []
            revised_post.revision_history.append({
                "revision": revision_number,
                "changes": content.get("changes_made", []),
                "preserved": content.get("preserved", []),
                "rationale": content.get("revision_rationale", ""),
                "voice_maintained": content.get("voice_maintained", True)
            })
            
            self.logger.info(f"📝 Revised post {post.post_number} (revision {revision_number})")
            
            return revised_post
            
        except Exception as e:
            self.logger.error(f"Revision generation failed: {e}")
            # Return original post if revision fails
            return post
    
    def _format_validator_breakdown(self, breakdown: Dict[str, Any]) -> str:
        """Format validator breakdown for the prompt"""
        formatted = []
        
        for validator, data in breakdown.items():
            validator_type = self._get_validator_type(validator)
            status = "✅ APPROVED" if data.get("approved") else "❌ NOT APPROVED"
            
            formatted.append(f"""
{validator} ({validator_type}):
  Score: {data.get('score', 0)}/10 {status}
  Feedback: {data.get('feedback', 'No feedback')}
""")
        
        return "\n".join(formatted)
    
    def _get_validator_type(self, name: str) -> str:
        """Get validator type description"""
        types = {
            "JordanPark": "Algorithm Whisperer",
            "MarcusWilliams": "Creative Integrity",
            "SarahChen": "Target Authenticity"
        }
        return types.get(name, "Validator")
    
    def _calculate_cost(self, usage: Dict[str, int]) -> float:
        """Calculate cost based on token usage"""
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        
        input_cost = (input_tokens / 1_000_000) * 0.15
        output_cost = (output_tokens / 1_000_000) * 0.60
        
        return input_cost + output_cost