"""
Content Generator Agent - Creates LinkedIn posts for Jesse A. Eisenbalm
"""

import random
import logging
from typing import Dict, Any, Optional, List
from .base_agent import BaseAgent
from ..models.post import LinkedInPost, CulturalReference

logger = logging.getLogger(__name__)


class ContentGeneratorAgent(BaseAgent):
    """Generates LinkedIn posts using the 25-element combination protocol"""
    
    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="ContentGenerator")
        
        # Content elements for variation
        self.hooks = [
            "confession",
            "hot_take", 
            "question",
            "scenario",
            "statistic",
            "quote_twist"
        ]
        
        self.structures = [
            "problem_agitate_solve",
            "story_lesson",
            "myth_bust",
            "contrast",
            "listicle"
        ]
        
        self.tones = [
            "wry_observation",
            "absurdist",
            "mock_serious",
            "confessional",
            "conspiratorial"
        ]
        
        self.endings = [
            "call_to_action",
            "plot_twist",
            "callback",
            "cliffhanger",
            "mic_drop"
        ]
    
    def get_system_prompt(self) -> str:
        """System prompt for content generation"""
        return f"""You are an expert LinkedIn content creator for Jesse A. Eisenbalm, a premium lip balm brand.

{self.get_brand_context()}

VOICE GUIDELINES:
- Absurdist modern luxury meets corporate satire
- Self-aware about LinkedIn culture while participating in it
- Treats lip balm application as a mindfulness ritual
- Never preachy or earnest - always with a wink
- Makes the mundane feel philosophical

CONTENT RULES:
1. Posts should be 150-280 characters for optimal engagement
2. Include 2-4 relevant hashtags
3. Reference ONE cultural touchpoint (TV show, workplace theme, or seasonal moment)
4. End with the brand ritual when natural: "Stop. Breathe. Apply."
5. Never be salesy or promotional - be entertaining first

OUTPUT FORMAT:
You must respond with valid JSON only containing:
{{
    "content": "The full post text",
    "hook": "The opening line/hook type used",
    "hashtags": ["hashtag1", "hashtag2"],
    "cultural_reference": {{
        "category": "tv_show|workplace|seasonal",
        "reference": "specific reference",
        "context": "how it was used"
    }},
    "target_audience": "specific audience segment",
    "reasoning": "brief explanation of creative choices"
}}"""
    
    async def execute(
        self,
        post_number: int = 1,
        batch_id: str = "",
        cultural_category: Optional[str] = None,
        specific_reference: Optional[str] = None
    ) -> LinkedInPost:
        """Generate a single LinkedIn post"""
        
        self.set_context(batch_id, post_number)
        
        # Select random elements for variation
        hook = random.choice(self.hooks)
        structure = random.choice(self.structures)
        tone = random.choice(self.tones)
        ending = random.choice(self.endings)
        
        # Select cultural reference
        cultural_refs = self.config.cultural_references
        if cultural_category and specific_reference:
            category = cultural_category
            reference = specific_reference
        else:
            category = random.choice(["tv_show", "workplace", "seasonal"])
            if category == "tv_show":
                reference = random.choice(cultural_refs.tv_shows)
            elif category == "workplace":
                reference = random.choice(cultural_refs.workplace_themes)
            else:
                reference = random.choice(cultural_refs.seasonal_themes)
        
        prompt = f"""Generate a LinkedIn post for Jesse A. Eisenbalm lip balm.

CREATIVE DIRECTION:
- Hook style: {hook}
- Structure: {structure}
- Tone: {tone}
- Ending: {ending}

CULTURAL REFERENCE TO INCORPORATE:
- Category: {category}
- Reference: {reference}

Remember:
- Be entertaining, not salesy
- Use the brand voice: absurdist, wry, human-first
- Include 2-4 hashtags
- Consider ending with "Stop. Breathe. Apply." if it fits naturally

Generate the post now."""
        
        try:
            result = await self.generate(prompt)
            content_data = result.get("content", {})
            
            # Handle string response (shouldn't happen but safety check)
            if isinstance(content_data, str):
                content_data = {
                    "content": content_data,
                    "hashtags": ["#LinkedInLife", "#HumanFirst"],
                    "hook": hook,
                    "target_audience": self.config.brand.target_audience
                }
            
            # Create cultural reference object
            cultural_ref = None
            if "cultural_reference" in content_data and content_data["cultural_reference"]:
                cultural_ref = CulturalReference(
                    category=content_data["cultural_reference"].get("category", category),
                    reference=content_data["cultural_reference"].get("reference", reference),
                    context=content_data["cultural_reference"].get("context", "")
                )
            else:
                cultural_ref = CulturalReference(
                    category=category,
                    reference=reference,
                    context="Used as primary theme"
                )
            
            # Create the post
            post = LinkedInPost(
                batch_id=batch_id,
                post_number=post_number,
                content=content_data.get("content", ""),
                hook=content_data.get("hook", hook),
                hashtags=content_data.get("hashtags", ["#LinkedInLife", "#HumanFirst"]),
                target_audience=content_data.get("target_audience", self.config.brand.target_audience),
                cultural_reference=cultural_ref,
                total_tokens_used=result.get("usage", {}).get("total_tokens", 0),
                estimated_cost=self._calculate_cost(result.get("usage", {}))
            )
            
            self.logger.info(f"Generated post {post_number} with {len(post.content)} characters")
            
            return post
            
        except Exception as e:
            self.logger.error(f"Failed to generate post: {e}")
            raise
    
    def _calculate_cost(self, usage: Dict[str, int]) -> float:
        """Calculate cost based on token usage"""
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        
        # GPT-4o-mini pricing per 1M tokens
        input_cost = (input_tokens / 1_000_000) * 0.15
        output_cost = (output_tokens / 1_000_000) * 0.60
        
        return input_cost + output_cost
