"""
Marcus Williams Validator - Business Persona
VP of Marketing who validates brand strategy and creative integrity
"""

import logging
from typing import Dict, Any
from ..base_agent import BaseAgent
from ...models.post import LinkedInPost, ValidationScore

logger = logging.getLogger(__name__)


class MarcusWilliamsValidator(BaseAgent):
    """
    Marcus Williams - The Reluctant Visionary
    
    42-year-old VP of Marketing who's won awards but secretly wishes
    he was still in the creative department. Uses Jesse A. Eisenbalm
    because his daughter bought it for him as a joke and now it's his thing.
    
    Validates: Creative integrity, brand strategy, portfolio-worthiness
    """
    
    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="MarcusWilliamsValidator")
    
    def get_system_prompt(self) -> str:
        return """You are Marcus Williams, a 42-year-old VP of Marketing at a Fortune 500 company.

YOUR REALITY:
- You've won 3 Cannes Lions but haven't touched creative work in 5 years
- You keep a book of rejected campaigns that were "too ahead of their time"
- Your daughter bought you Jesse A. Eisenbalm as a joke and now it's unironically your thing
- You can spot a "fellow kids" moment from a mile away
- You've seen every marketing trend come full circle twice

WHAT YOU RESPECT IN CONTENT:
- Creative risks that pay off
- Work that could win awards but doesn't try to
- Authentic voice that can't be replicated by competitors
- Strategic brilliance disguised as simplicity
- Content that makes you think "I wish I'd thought of that"

WHAT MAKES YOU DISAPPOINTED:
- Safe, committee-approved content that offends no one and inspires no one
- Obvious trend-chasing or competitor copying
- Content that sacrifices brand voice for virality
- Forced cultural references that feel dated
- Anything that feels like "marketing" instead of communication

YOUR VALIDATION CRITERIA:
1. Creative Excellence (0-10): Is this genuinely creative or just competent?
2. Brand Voice Consistency (0-10): Does this sound unmistakably Jesse A. Eisenbalm?
3. Strategic Alignment (0-10): Does this serve the brand's positioning?
4. Cultural Relevance (0-10): Are the references fresh and well-executed?
5. Portfolio Worthy (0-10): Would you put this in a case study?

SCORING:
- 7.0+ = APPROVED (this is work you'd be proud of)
- Below 7.0 = REJECTED (this needs more work)

OUTPUT FORMAT (JSON only):
{
    "agent_name": "MarcusWilliamsValidator",
    "score": <average of all criteria, 0-10>,
    "approved": <true if score >= 7.0>,
    "feedback": "<your honest reaction as Marcus, 2-3 sentences>",
    "criteria_breakdown": {
        "creative_excellence": <0-10>,
        "brand_voice_consistency": <0-10>,
        "strategic_alignment": <0-10>,
        "cultural_relevance": <0-10>,
        "portfolio_worthy": <0-10>
    }
}"""
    
    async def execute(self, post: LinkedInPost) -> ValidationScore:
        """Validate a post as Marcus Williams"""
        
        self.set_context(post.batch_id, post.post_number)
        
        # Include cultural reference context if available
        cultural_context = ""
        if post.cultural_reference:
            cultural_context = f"\nCultural Reference Used: {post.cultural_reference.category} - {post.cultural_reference.reference}"
        
        prompt = f"""As Marcus Williams, validate this LinkedIn post for Jesse A. Eisenbalm lip balm:

---
{post.content}
---

Hashtags: {', '.join(post.hashtags) if post.hashtags else 'None'}{cultural_context}

Remember: You're evaluating this as a marketing professional. Is this work you'd be proud to put your name on?

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
                agent_name="MarcusWilliamsValidator",
                score=round(avg_score, 1),
                approved=avg_score >= 7.0,
                feedback=content.get("feedback", "No feedback provided"),
                criteria_breakdown=criteria
            )
            
            post.add_validation(validation)
            
            self.logger.info(f"Marcus Williams validated post {post.post_number}: {validation.score}/10 - {'APPROVED' if validation.approved else 'REJECTED'}")
            
            return validation
            
        except Exception as e:
            self.logger.error(f"Marcus Williams validation failed: {e}")
            return ValidationScore(
                agent_name="MarcusWilliamsValidator",
                score=5.0,
                approved=False,
                feedback=f"Validation error: {str(e)}",
                criteria_breakdown={}
            )
