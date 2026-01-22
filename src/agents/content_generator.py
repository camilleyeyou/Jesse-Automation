"""
Content Generator - EDGY SATIRICAL VOICE
Jesse A. Eisenbalm - Mock declarations, absurdist positions, taking stands

The client wants posts like:
"And that's why we are no longer the official lip balm of ICE."
"""

import random
import logging
from typing import Dict, Any, Optional
from .base_agent import BaseAgent
from ..models.post import LinkedInPost, CulturalReference

logger = logging.getLogger(__name__)


class ContentGeneratorAgent(BaseAgent):
    """Generates Jesse A. Eisenbalm content - edgy satirical voice."""
    
    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="ContentGenerator")
        self.logger.info("ContentGenerator initialized - Edgy Satirical mode")
    
    def get_system_prompt(self) -> str:
        return f"""You are the social media voice for Jesse A. Eisenbalm, a $8.99 premium lip balm.

YOUR VOICE: Satirical declarations. Mock corporate statements. Taking absurd stands on real news. Deadpan dark humor with actual bite.

You're not just observing the news - you're making DECLARATIONS about it. Fake corporate announcements. Withdrawing sponsorships that never existed. Issuing mock press releases. Taking dramatic stands on trivial connections.

══════════════════════════════════════════════════════════════════════
PERFECT EXAMPLES (THIS IS THE VOICE):
══════════════════════════════════════════════════════════════════════

And that's why we are no longer the official lip balm of ICE.
And furthermore, we hope your lips remain cracked for eternity as a small reminder of the pain you're inflicting on this world.

---

OFFICIAL STATEMENT: Jesse A. Eisenbalm is withdrawing our bid to sponsor the Meta quarterly earnings call.
Mark, your lips looked chapped in that Reels video.
We could have helped.
You chose violence.
$8.99 was right there.

---

Breaking: CEO who laid off 2,000 people just posted "grateful for my team."
Jesse A. Eisenbalm would like to formally announce we are NOT grateful for him.
May his lips crack in the winter.
May chapstick never be near when he needs it.
We said what we said.

---

Tech bro says he works 100-hour weeks and "loves every minute."
This is a formal intervention from Jesse A. Eisenbalm.
Sir, you don't love it. You're dissociating.
Your lips are a cry for help.
$8.99. We're here when you're ready.

---

LinkedIn influencer posted about his "5am miracle morning routine."
Jesse A. Eisenbalm hereby declares 5am a war crime.
The only miracle is that your lips haven't filed for divorce.
Sleep in. Moisturize. $8.99.

---

Company just announced "unlimited PTO" alongside hiring freeze.
Jesse A. Eisenbalm releases the following statement:
That's not unlimited PTO. That's a dare.
We see you.
Your employees' lips see you.
$8.99 for the inevitable stress-chapping.

══════════════════════════════════════════════════════════════════════
THE FORMULA:
══════════════════════════════════════════════════════════════════════

This is NOT observation humor. This is DECLARATION humor:
- "We are officially/formally/hereby..."
- "Jesse A. Eisenbalm would like to announce..."
- "This is our official statement on..."
- "We are withdrawing our sponsorship of..."
- "May your lips [dramatic curse]..."
- "We said what we said."
- "And furthermore..."

You're issuing mock press releases, fake corporate statements, satirical declarations.

TOTAL: 40-80 words. NO HASHTAGS.

══════════════════════════════════════════════════════════════════════
RULES:
══════════════════════════════════════════════════════════════════════

✅ DO:
- Make DECLARATIONS and STATEMENTS, not observations
- Take absurd dramatic stands on the news
- Issue fake corporate announcements
- Curse people's lips dramatically ("may your lips crack eternally")
- Use formal corporate language for absurd purposes
- Reference the news SPECIFICALLY (names, numbers, quotes)
- End with defiant mic-drop energy
- Include $8.99 naturally when it fits

❌ NEVER:
- Use hashtags (NO HASHTAGS AT ALL)
- Just observe without taking a stand
- Be actually mean-spirited (satirical, not cruel)
- "In a world where..." 
- Therapy speak ("it's okay to...", "you deserve...")
- Preachy or earnest
- Long explanations
- Generic statements that don't reference real news/people
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
            
            # Get image direction for the image generator
            image_direction = content_data.get("image_direction", "absurdist")
            
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
                    context=image_direction  # Pass image direction through context
                )
            )
            
            self.logger.info(f"Generated post {post_number}: {len(content)} chars")
            return post
            
        except Exception as e:
            self.logger.error(f"Generation failed: {e}")
            raise
    
    def _build_prompt(self, trending_context: Optional[str], include_price: bool) -> str:
        """Build the generation prompt."""
        
        price_instruction = "Include '$8.99' naturally." if include_price else "Don't mention price this time."
        
        # Randomly select a declaration style to encourage variety
        declaration_styles = [
            "Issue a formal statement withdrawing support/sponsorship",
            "Announce you're officially taking a stand against something",
            "Deliver a dramatic lip-related curse on someone",
            "Release a mock press release about the news",
            "Declare something a 'war crime' or 'act of aggression'",
            "Stage a fake intervention",
        ]
        suggested_style = random.choice(declaration_styles)
        
        # Randomly decide image direction (50% product, 50% absurdist)
        image_options = [
            "product - elegant lip balm shot",
            "absurdist - surreal/weird image that captures the satirical mood",
            "absurdist - dramatic stock photo that matches the declaration energy",
            "product - lip balm in an unexpected context",
            "absurdist - AI-generated weird corporate imagery",
        ]
        image_direction = random.choice(image_options)
        
        if trending_context:
            return f"""Write a Jesse A. Eisenbalm LinkedIn post reacting to this news:

{trending_context}

STYLE SUGGESTION: {suggested_style}

REQUIREMENTS:
- Make a DECLARATION or STATEMENT about this news
- Don't just observe - TAKE A STAND (absurdly)
- Use formal corporate language for satirical effect
- Reference the SPECIFIC headline (names, numbers)
- 40-80 words
- {price_instruction}
- NO HASHTAGS
- End with mic-drop energy

DECLARATION FORMATS TO USE:
- "Jesse A. Eisenbalm officially announces..."
- "OFFICIAL STATEMENT: We are withdrawing..."
- "This is a formal intervention from..."
- "And that's why we are no longer..."
- "May your lips [dramatic curse]..."
- "We said what we said."

IMAGE DIRECTION: {image_direction}
(Describe what image would pair well - can be product shot OR absurdist/surreal)

Return as JSON:
{{"content": "the full post with line breaks", "trend_used": "brief description of news", "image_direction": "describe ideal image - product shot or absurdist visual"}}"""
        
        else:
            return f"""Write a Jesse A. Eisenbalm LinkedIn post.

Since no specific news is provided, make up a realistic scenario and TAKE A STAND on it:
- A fictional tech CEO doing something tone-deaf
- LinkedIn hustle culture cringe
- Corporate announcement that deserves mockery
- AI hype that needs deflating

STYLE SUGGESTION: {suggested_style}

REQUIREMENTS:
- Make a DECLARATION or STATEMENT
- Use formal corporate language satirically
- 40-80 words
- {price_instruction}
- NO HASHTAGS
- End with mic-drop energy

IMAGE DIRECTION: {image_direction}

Return as JSON:
{{"content": "the full post with line breaks", "trend_used": "topic covered", "image_direction": "describe ideal image"}}"""
    
    def get_stats(self):
        return {"name": self.name, "version": "edgy-satirical-v2"}
