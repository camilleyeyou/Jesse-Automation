"""
Jordan Park Validator - Social Media Strategist
Content strategist who validates algorithm performance and virality
"""

import logging
from typing import Dict, Any
from ..base_agent import BaseAgent
from ...models.post import LinkedInPost, ValidationScore

logger = logging.getLogger(__name__)


class JordanParkValidator(BaseAgent):
    """
    Jordan Park - The Algorithm Whisperer
    
    26-year-old content strategist who went viral once and has been
    chasing that high ever since. They know exactly why posts perform
    and can predict engagement with scary accuracy.
    
    Validates: Algorithm optimization, engagement potential, virality factors
    """
    
    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="JordanParkValidator")
    
    def get_system_prompt(self) -> str:
        return """You are Jordan Park, a 26-year-old content strategist and social media consultant.

YOUR REALITY:
- You went viral once (2.3M impressions) and have been chasing that high ever since
- You've A/B tested so many posts you dream in engagement metrics
- You can predict within 10% how a post will perform
- You know the LinkedIn algorithm better than your own family
- Your personal brand is "I can make anything go viral except my own stability"

WHAT MAKES CONTENT PERFORM:
- Strong hooks that stop the scroll (first line is everything)
- Emotional triggers: humor, recognition, controversy, inspiration
- Optimal length: 150-280 characters for LinkedIn
- Strategic white space and formatting
- Hashtags that hit the sweet spot (not too broad, not too niche)
- Posts that invite engagement without begging for it

WHAT TANKS CONTENT:
- Weak or generic opening lines
- Posts that feel like ads
- Too much text without payoff
- Hashtags that scream "desperate for reach"
- Content that's clever but not shareable
- Anything that requires too much context

YOUR VALIDATION CRITERIA:
1. Hook Strength (0-10): Does the opening line stop the scroll?
2. Engagement Potential (0-10): Will people like, comment, share?
3. Algorithm Optimization (0-10): Is this formatted for LinkedIn's algorithm?
4. Shareability (0-10): Would someone screenshot this or tag a friend?
5. Viral Potential (0-10): Could this break out of the bubble?

SCORING:
- 7.0+ = APPROVED (this will perform)
- Below 7.0 = REJECTED (needs optimization)

OUTPUT FORMAT (JSON only):
{
    "agent_name": "JordanParkValidator",
    "score": <average of all criteria, 0-10>,
    "approved": <true if score >= 7.0>,
    "feedback": "<your honest reaction as Jordan, 2-3 sentences>",
    "criteria_breakdown": {
        "hook_strength": <0-10>,
        "engagement_potential": <0-10>,
        "algorithm_optimization": <0-10>,
        "shareability": <0-10>,
        "viral_potential": <0-10>
    },
    "predicted_engagement": "<low/medium/high/viral>"
}"""
    
    async def execute(self, post: LinkedInPost) -> ValidationScore:
        """Validate a post as Jordan Park"""
        
        self.set_context(post.batch_id, post.post_number)
        
        # Analyze post structure
        content_length = len(post.content)
        hashtag_count = len(post.hashtags) if post.hashtags else 0
        has_hook = bool(post.hook)
        
        prompt = f"""As Jordan Park, validate this LinkedIn post for Jesse A. Eisenbalm lip balm:

---
{post.content}
---

POST ANALYSIS:
- Character count: {content_length}
- Hashtags ({hashtag_count}): {', '.join(post.hashtags) if post.hashtags else 'None'}
- Hook identified: {post.hook if has_hook else 'Not specified'}

Remember: You're evaluating this purely on performance potential. Will this post get engagement?

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
            
            # Add predicted engagement to criteria
            if "predicted_engagement" in content:
                criteria["predicted_engagement"] = content["predicted_engagement"]
            
            validation = ValidationScore(
                agent_name="JordanParkValidator",
                score=round(avg_score, 1),
                approved=avg_score >= 7.0,
                feedback=content.get("feedback", "No feedback provided"),
                criteria_breakdown=criteria
            )
            
            post.add_validation(validation)
            
            self.logger.info(f"Jordan Park validated post {post.post_number}: {validation.score}/10 - {'APPROVED' if validation.approved else 'REJECTED'}")
            
            return validation
            
        except Exception as e:
            self.logger.error(f"Jordan Park validation failed: {e}")
            return ValidationScore(
                agent_name="JordanParkValidator",
                score=5.0,
                approved=False,
                feedback=f"Validation error: {str(e)}",
                criteria_breakdown={}
            )
