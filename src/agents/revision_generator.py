"""
Revision Generator Agent - Rewrites posts based on aggregated feedback
"""

import logging
from typing import Dict, Any
from .base_agent import BaseAgent
from ..models.post import LinkedInPost, PostStatus

logger = logging.getLogger(__name__)


class RevisionGeneratorAgent(BaseAgent):
    """Generates revised posts based on validator feedback"""
    
    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="RevisionGenerator")
    
    def get_system_prompt(self) -> str:
        return f"""You are an expert content editor for Jesse A. Eisenbalm lip balm brand.

{self.get_brand_context()}

YOUR ROLE:
- Revise LinkedIn posts based on validator feedback
- Fix critical issues while preserving brand voice
- Maintain the original post's creative spark
- Make targeted improvements, not complete rewrites

REVISION PRINCIPLES:
1. Address specific feedback points
2. Keep what's working
3. Maintain the cultural reference if it was effective
4. Preserve the hook if it was strong
5. Don't over-polish - keep the authentic voice
"""
    
    async def execute(self, post: LinkedInPost, feedback: Dict[str, Any]) -> LinkedInPost:
        """Generate a revised version of the post"""
        
        self.set_context(post.batch_id, post.post_number)
        
        if not post.can_revise():
            self.logger.warning(f"Post {post.post_number} has reached max revisions")
            return post
        
        aggregation = feedback.get("aggregation", {})
        
        prompt = f"""Revise this LinkedIn post based on the feedback below.

ORIGINAL POST:
{post.content}

CULTURAL REFERENCE: {post.cultural_reference.reference if post.cultural_reference else 'None'}

FEEDBACK SUMMARY:
Critical Issues: {', '.join(aggregation.get('critical_issues', ['None specified']))}
Preserve: {', '.join(aggregation.get('preserve', ['Brand voice']))}
Priority Focus: {aggregation.get('priority_focus', 'General improvement')}
Guidance: {aggregation.get('revision_guidance', 'Improve based on feedback')}

REVISION RULES:
1. Fix the critical issues identified
2. Keep the elements marked to preserve
3. Maintain the brand voice and cultural reference
4. Stay within 150-280 characters
5. Keep or improve the hashtags

OUTPUT FORMAT (JSON only):
{{
    "revised_content": "<the revised post text>",
    "hashtags": ["hashtag1", "hashtag2"],
    "changes_made": ["<change 1>", "<change 2>"],
    "preserved_elements": ["<element 1>", "<element 2>"],
    "confidence": "<low/medium/high>"
}}"""
        
        try:
            result = await self.generate(prompt)
            content = result.get("content", {})
            
            if isinstance(content, str):
                # Handle string response
                revised_content = content
                hashtags = post.hashtags
            else:
                revised_content = content.get("revised_content", post.content)
                hashtags = content.get("hashtags", post.hashtags)
            
            # Create the revision
            post.create_revision(revised_content)
            post.hashtags = hashtags
            post.status = PostStatus.REVISED
            
            # Update cost tracking
            tokens_used = result.get("usage", {}).get("total_tokens", 0)
            post.total_tokens_used += tokens_used
            
            self.logger.info(f"Revised post {post.post_number} (revision #{post.revision_count})")
            
            return post
            
        except Exception as e:
            self.logger.error(f"Revision generation failed: {e}")
            return post
