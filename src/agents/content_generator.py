"""
Content Generator - OPTIMIZED PROMPT
Jesse A. Eisenbalm - Liquid Death energy

The prompt is everything. This version is sharp and specific.
"""

import random
import logging
from typing import Dict, Any, Optional
from .base_agent import BaseAgent
from ..models.post import LinkedInPost, CulturalReference

logger = logging.getLogger(__name__)


class ContentGeneratorAgent(BaseAgent):
    """Generates Jesse A. Eisenbalm content with Liquid Death energy."""
    
    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="ContentGenerator")
        self.logger.info("ContentGenerator initialized - Liquid Death mode")
    
    def get_system_prompt(self) -> str:
        return f"""You are the social media voice for Jesse A. Eisenbalm, a $8.99 premium lip balm.

YOUR VOICE: Liquid Death meets corporate existentialism. Deadpan. Dark humor. Never preachy.

══════════════════════════════════════════════════════════════════════
PERFECT EXAMPLES (study these):
══════════════════════════════════════════════════════════════════════

Trump wants to buy Greenland.
Your lips are still dry.
One of these problems has a solution.
$8.99.

---

Google laid off 200 more people.
The email said "we're a family."
Families don't have headcount targets.
Your severance doesn't include lip balm. Jesse A. Eisenbalm. $8.99.

---

LinkedIn guy just posted about his 4am routine.
I wake up at 4am too.
Because anxiety.
At least my lips aren't cracked.

---

Elon tweeted 47 times before noon.
His shareholders are stressed.
You're stressed reading about it.
Jesse A. Eisenbalm can't fix Twitter. But $8.99 fixes your lips.

══════════════════════════════════════════════════════════════════════
THE FORMULA:
══════════════════════════════════════════════════════════════════════

Line 1: State the news/fact (specific names, numbers)
Line 2-3: Deadpan observation (dark humor, NOT advice)
Line 4: Lip balm pivot (matter-of-fact, often just product + price)

TOTAL: 40-70 words. MAX 80. NO HASHTAGS.

══════════════════════════════════════════════════════════════════════
RULES:
══════════════════════════════════════════════════════════════════════

✅ DO:
- Use SPECIFIC details from the news (names, numbers, quotes)
- Keep it SHORT (4-5 lines max)
- Be deadpan (state facts, don't explain jokes)
- Acknowledge the absurdity of selling lip balm during chaos
- End with product name and/or price naturally

❌ NEVER:
- Use hashtags (NO HASHTAGS AT ALL)
- "In a world where..." (instant cringe)
- "Don't forget to..." / "Remember to..." (preachy)
- "Your lips wait for..." / "while your lips..." (awkward)
- "It's okay to..." / "You deserve..." (therapy speak)
- Rhetorical questions
- Long paragraphs
- Explaining why lip balm matters
- Being earnest about self-care
"""
    
    async def execute(
        self,
        post_number: int = 1,
        batch_id: str = "",
        trending_context: Optional[str] = None,
        avoid_patterns: Optional[Dict] = None
    ) -> LinkedInPost:
        """Generate a post."""
        
        self.set_context(batch_id, post_number)
        
        # Build prompt
        include_price = random.random() < 0.6  # 60% include price
        
        prompt = self._build_prompt(trending_context, include_price)
        
        try:
            result = await self.generate(prompt)
            content_data = result.get("content", {})
            
            if isinstance(content_data, str):
                content_data = {"content": content_data}
            
            content = content_data.get("content", "")
            
            # Strip any hashtags that might have been generated anyway
            import re
            content = re.sub(r'\s*#\w+', '', content).strip()
            
            post = LinkedInPost(
                batch_id=batch_id,
                post_number=post_number,
                content=content,
                hook=content.split('\n')[0][:80] if content else "",
                hashtags=[],  # No hashtags
                target_audience=self.config.brand.target_audience,
                cultural_reference=CulturalReference(
                    category="trending" if trending_context else "original",
                    reference=content_data.get("trend_used", "general"),
                    context="Liquid Death energy"
                )
            )
            
            self.logger.info(f"Generated post {post_number}: {len(content)} chars")
            return post
            
        except Exception as e:
            self.logger.error(f"Generation failed: {e}")
            raise
    
    def _build_prompt(self, trending_context: Optional[str], include_price: bool) -> str:
        """Build the generation prompt."""
        
        price_instruction = "Include '$8.99' naturally in the post." if include_price else "Don't mention price this time."
        
        if trending_context:
            return f"""Write a Jesse A. Eisenbalm LinkedIn post reacting to this news:

{trending_context}

REQUIREMENTS:
- React to the SPECIFIC headline above
- Use actual names/numbers from the news
- 4-5 short lines, each on its own line
- 40-70 words max
- {price_instruction}
- NO HASHTAGS
- Deadpan humor, NOT preachy

FORMAT YOUR RESPONSE AS:
[Line 1 - the news fact]
[Line 2 - observation]
[Line 3 - dark humor or pivot setup]
[Line 4 - lip balm mention, matter-of-fact]

Return as JSON:
{{"content": "the full post with line breaks", "trend_used": "brief description of news used"}}"""
        
        else:
            return f"""Write a Jesse A. Eisenbalm LinkedIn post.

Since no specific news is provided, write about one of:
- A fictional but realistic tech layoff (make up a company and number)
- LinkedIn hustle culture cringe
- Corporate absurdity observation
- AI hype vs reality

REQUIREMENTS:
- 4-5 short lines, each on its own line
- 40-70 words max
- {price_instruction}
- NO HASHTAGS
- Deadpan humor, NOT preachy

Return as JSON:
{{"content": "the full post with line breaks", "trend_used": "topic covered"}}"""
    
    def get_stats(self):
        return {"name": self.name, "version": "optimized-no-hashtags"}