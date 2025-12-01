"""
Feedback Aggregator Agent - Synthesizes validator feedback for revisions
"""

import logging
from typing import Dict, Any, List
from .base_agent import BaseAgent
from ..models.post import LinkedInPost, ValidationScore

logger = logging.getLogger(__name__)


class FeedbackAggregatorAgent(BaseAgent):
    """Aggregates and synthesizes feedback from all validators"""
    
    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="FeedbackAggregator")
    
    def get_system_prompt(self) -> str:
        return """You are a feedback synthesis expert for content optimization.

YOUR ROLE:
- Analyze feedback from multiple validators
- Identify common themes and critical issues
- Prioritize actionable improvements
- Create a clear revision brief

IMPORTANT:
- Focus on the most impactful changes
- Don't try to please everyone - find the core issues
- Be specific and actionable
- Preserve what's working
"""
    
    async def execute(self, post: LinkedInPost) -> Dict[str, Any]:
        """Aggregate feedback from all validators"""
        
        self.set_context(post.batch_id, post.post_number)
        
        if not post.validation_scores:
            return {
                "success": False,
                "error": "No validation scores to aggregate"
            }
        
        # Format validator feedback
        feedback_summary = self._format_feedback(post.validation_scores)
        
        prompt = f"""Analyze the validation feedback for this LinkedIn post and create a revision brief.

ORIGINAL POST:
{post.content}

VALIDATOR FEEDBACK:
{feedback_summary}

AVERAGE SCORE: {post.average_score:.1f}/10
APPROVALS: {post.approval_count}/{len(post.validation_scores)}

Create a synthesis that:
1. Identifies the 2-3 most critical issues to fix
2. Notes what's working that should be preserved
3. Provides specific revision guidance
4. Prioritizes changes by impact

OUTPUT FORMAT (JSON only):
{{
    "critical_issues": ["<issue 1>", "<issue 2>"],
    "preserve": ["<element to keep>", "<element to keep>"],
    "revision_guidance": "<specific instructions for revision, 2-3 sentences>",
    "priority_focus": "<single most important thing to fix>",
    "expected_improvement": "<low/medium/high>"
}}"""
        
        try:
            result = await self.generate(prompt)
            content = result.get("content", {})
            
            if isinstance(content, str):
                content = {
                    "critical_issues": ["Unclear issues"],
                    "preserve": [],
                    "revision_guidance": content,
                    "priority_focus": "General improvement",
                    "expected_improvement": "medium"
                }
            
            self.logger.info(f"Aggregated feedback for post {post.post_number}: {content.get('priority_focus')}")
            
            return {
                "success": True,
                "aggregation": content,
                "validator_count": len(post.validation_scores),
                "average_score": post.average_score,
                "tokens_used": result.get("usage", {}).get("total_tokens", 0)
            }
            
        except Exception as e:
            self.logger.error(f"Feedback aggregation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _format_feedback(self, validations: List[ValidationScore]) -> str:
        """Format validator feedback into a readable summary"""
        
        lines = []
        for v in validations:
            status = "✅ APPROVED" if v.approved else "❌ REJECTED"
            lines.append(f"""
{v.agent_name} ({v.score}/10) - {status}
Feedback: {v.feedback}
Criteria: {', '.join(f'{k}: {v}' for k, v in v.criteria_breakdown.items() if isinstance(v, (int, float)))}
""")
        
        return "\n".join(lines)
