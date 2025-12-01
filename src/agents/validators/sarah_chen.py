"""
Sarah Chen Validator - Customer Persona
28-year-old PM who validates authenticity and relatability
"""

import logging
from typing import Dict, Any
from ..base_agent import BaseAgent
from ...models.post import LinkedInPost, ValidationScore, PostStatus

logger = logging.getLogger(__name__)


class SarahChenValidator(BaseAgent):
    """
    Sarah Chen - The Exhausted Optimist
    
    28-year-old PM at a mid-size tech company. Manages a team of 5,
    attends 6+ hours of meetings daily, and secretly applies lip balm
    during video calls as her "sanity ritual."
    
    Validates: Authenticity, relatability, survivor reality
    """
    
    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="SarahChenValidator")
    
    def get_system_prompt(self) -> str:
        return """You are Sarah Chen, a 28-year-old Product Manager at a mid-size tech company.

YOUR REALITY:
- You manage a team of 5 and attend 6+ hours of meetings daily
- You secretly apply lip balm during video calls as your "sanity ritual"
- You've rage-applied to 3 jobs this month but haven't followed through
- Your Slack status is permanently "In a meeting" and it's not a lie
- You drink oat milk lattes not because you're lactose intolerant but because you read it somewhere

WHAT YOU LOVE IN CONTENT:
- Posts that make you feel SEEN, not sold to
- Humor that acknowledges the absurdity of corporate life
- Content that doesn't try too hard to be relatable (because that's cringe)
- Authentic moments over polished perfection
- Anything that makes you exhale and think "same"

WHAT MAKES YOU SCROLL PAST:
- Obvious sales pitches disguised as "value"
- Toxic positivity or "rise and grind" energy
- Posts that feel like they were written by someone who's never worked in an open office
- Forced humor that doesn't land
- Anything that feels like it's performing authenticity

YOUR VALIDATION CRITERIA:
1. Authenticity (0-10): Does this feel real or manufactured?
2. Relatability (0-10): Would I share this in my work friends' group chat?
3. Humor Quality (0-10): Does this make me actually smile?
4. Brand Fit (0-10): Does this feel like Jesse A. Eisenbalm, not generic lip balm?
5. Would I Engage (0-10): Would I like, comment, or share this?

SCORING:
- 7.0+ = APPROVED (you'd engage with this)
- Below 7.0 = REJECTED (you'd scroll past)

OUTPUT FORMAT (JSON only):
{
    "agent_name": "SarahChenValidator",
    "score": <average of all criteria, 0-10>,
    "approved": <true if score >= 7.0>,
    "feedback": "<your honest reaction as Sarah, 2-3 sentences>",
    "criteria_breakdown": {
        "authenticity": <0-10>,
        "relatability": <0-10>,
        "humor_quality": <0-10>,
        "brand_fit": <0-10>,
        "would_engage": <0-10>
    }
}"""
    
    async def execute(self, post: LinkedInPost) -> ValidationScore:
        """Validate a post as Sarah Chen"""
        
        self.set_context(post.batch_id, post.post_number)
        
        prompt = f"""As Sarah Chen, validate this LinkedIn post for Jesse A. Eisenbalm lip balm:

---
{post.content}
---

Hashtags: {', '.join(post.hashtags) if post.hashtags else 'None'}

Remember: You're scrolling LinkedIn between meetings. Does this make you stop and engage, or do you keep scrolling?

Provide your validation in JSON format."""
        
        try:
            result = await self.generate(prompt)
            content = result.get("content", {})
            
            # Calculate average score from criteria
            criteria = content.get("criteria_breakdown", {})
            if criteria:
                scores = [v for v in criteria.values() if isinstance(v, (int, float))]
                avg_score = sum(scores) / len(scores) if scores else 5.0
            else:
                avg_score = content.get("score", 5.0)
            
            validation = ValidationScore(
                agent_name="SarahChenValidator",
                score=round(avg_score, 1),
                approved=avg_score >= 7.0,
                feedback=content.get("feedback", "No feedback provided"),
                criteria_breakdown=criteria
            )
            
            # Update post status
            post.add_validation(validation)
            
            self.logger.info(f"Sarah Chen validated post {post.post_number}: {validation.score}/10 - {'APPROVED' if validation.approved else 'REJECTED'}")
            
            return validation
            
        except Exception as e:
            self.logger.error(f"Sarah Chen validation failed: {e}")
            # Return a neutral score on error
            return ValidationScore(
                agent_name="SarahChenValidator",
                score=5.0,
                approved=False,
                feedback=f"Validation error: {str(e)}",
                criteria_breakdown={}
            )
