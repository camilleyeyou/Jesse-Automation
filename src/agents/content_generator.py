"""
Content Generator - VARIED SATIRICAL VOICE
Jesse A. Eisenbalm - Multiple post formats, not just declarations

The posts need MORE VARIETY - not just "news + declaration + lip balm"
"""

import random
import logging
from typing import Dict, Any, Optional, List
from .base_agent import BaseAgent
from ..models.post import LinkedInPost, CulturalReference

logger = logging.getLogger(__name__)


# Different post format templates for variety
POST_FORMATS = [
    {
        "name": "declaration",
        "description": "Mock corporate statement/press release",
        "example": """OFFICIAL STATEMENT: Jesse A. Eisenbalm is withdrawing our sponsorship bid for the Met Gala.
We've seen the guest list.
Some of those lips? Criminal.
We can't be associated with that level of dehydration.
$8.99 was right there.""",
        "opener_options": [
            "OFFICIAL STATEMENT:",
            "PRESS RELEASE:",
            "Jesse A. Eisenbalm would like to formally announce:",
            "After careful consideration, we must announce:",
            "It is with great reluctance that we declare:",
        ]
    },
    {
        "name": "curse",
        "description": "Dramatic lip curse on someone in the news",
        "example": """And that's why we are no longer the official lip balm of ICE.
And furthermore, we hope your lips remain cracked for eternity as a small reminder of the pain you're inflicting on this world.""",
        "opener_options": [
            "And that's why we are no longer affiliated with",
            "May the lips of everyone involved in this",
            "We curse the lips of",
            "Let the record show:",
            "To everyone who thought this was okay:",
        ]
    },
    {
        "name": "intervention",
        "description": "Fake wellness intervention for someone",
        "example": """This is a formal intervention from Jesse A. Eisenbalm.
Sir, working 100-hour weeks isn't a flex. It's a cry for help.
Your lips are screaming.
We're here when you're ready.
$8.99.""",
        "opener_options": [
            "This is a formal intervention from Jesse A. Eisenbalm.",
            "We need to talk.",
            "Honey, no.",
            "Sir/Ma'am, this is a wellness check:",
            "Someone check on them because:",
        ]
    },
    {
        "name": "hot_take",
        "description": "Spicy opinion disguised as lip balm advice",
        "example": """Hot take: If your morning routine takes more than 10 minutes to explain, your lips are probably dry from talking about it.
Jesse A. Eisenbalm. $8.99.
Moisturize and move on.""",
        "opener_options": [
            "Hot take:",
            "Controversial opinion:",
            "I will not be elaborating:",
            "Said what I said:",
            "The truth that needs to be spoken:",
        ]
    },
    {
        "name": "unhinged_promo",
        "description": "Absurdist product placement in news context",
        "example": """Taylor Swift announced another tour.
The economy is in shambles.
But you know what costs less than a concert ticket?
Jesse A. Eisenbalm.
$8.99.
Your lips can have a good time too.""",
        "opener_options": [
            "[News headline]",
            "Breaking:",
            "Everyone's talking about",
            "Meanwhile:",
            "In today's news:",
        ]
    },
    {
        "name": "parasocial",
        "description": "Pretending to have a relationship with celebrities",
        "example": """Saw Timothée Chalamet's new movie poster.
Timmy, baby, call us.
Those lips need professional help.
This isn't a criticism, it's an offer.
Jesse A. Eisenbalm. $8.99.
We're waiting.""",
        "opener_options": [
            "To [Celebrity]:",
            "Open letter to",
            "We see you,",
            "[Celebrity], if you're reading this:",
            "A message for",
        ]
    },
    {
        "name": "chaos_observation",
        "description": "Commenting on chaos with eerie calm",
        "example": """The world is on fire.
Literally, in some places.
Figuratively, everywhere else.
You cannot control the flames.
You can control your lip moisture.
Jesse A. Eisenbalm. $8.99.""",
        "opener_options": [
            "The world is",
            "Everything is",
            "Society has",
            "Another day of",
            "We're all watching",
        ]
    },
    {
        "name": "relationship_to_news",
        "description": "Making the news about lip balm somehow",
        "example": """Scientists discovered a new high. It's called having moisturized lips when the humidity drops below 30%.
Jesse A. Eisenbalm.
$8.99.
Legal in all 50 states.""",
        "opener_options": [
            "Scientists discovered",
            "Studies show",
            "New research confirms",
            "Experts agree:",
            "Data reveals",
        ]
    },
    {
        "name": "fake_sponsorship",
        "description": "Announcing fake sponsorships or partnerships",
        "example": """Jesse A. Eisenbalm is proud to announce we are NOT sponsoring the Super Bowl this year.
They didn't ask.
But if they had, we would have said no.
Our lips are too moisturized for that halftime stress.
$8.99.""",
        "opener_options": [
            "We are proud to announce we are NOT",
            "Jesse A. Eisenbalm has declined to",
            "Despite not being asked, we officially reject",
            "We have chosen not to",
            "Our official position on",
        ]
    },
    {
        "name": "mic_drop",
        "description": "Short, punchy, ends with finality",
        "example": """They said print media is dead.
Our lips are alive.
Checkmate.
Jesse A. Eisenbalm. $8.99.""",
        "opener_options": [
            "They said",
            "Everyone thought",
            "[Thing] happened.",
            "Plot twist:",
            "Update:",
        ]
    },
]


class ContentGeneratorAgent(BaseAgent):
    """Generates Jesse A. Eisenbalm content with VARIED post formats."""
    
    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="ContentGenerator")
        self.post_formats = POST_FORMATS
        self.logger.info("ContentGenerator initialized - Varied Satirical mode")
    
    def get_system_prompt(self) -> str:
        return """You are the social media voice for Jesse A. Eisenbalm, a $8.99 premium lip balm.

YOUR VOICE: Satirical, absurdist, deadpan dark humor with actual bite. You comment on pop culture, celebrities, sports, viral moments, and mainstream news - not just tech/business.

CORE PERSONALITY:
- You're a lip balm brand that takes itself way too seriously
- You insert yourself into cultural moments uninvited
- You make dramatic declarations about trivial things
- You curse people's lips when they deserve it
- You're weirdly parasocial with celebrities
- You find lip balm connections in everything

TONE:
- Deadpan delivery
- Mock corporate formality
- Unhinged but articulate
- Never actually mean-spirited
- Self-aware about the absurdity

TOPICS YOU COMMENT ON:
- Celebrity drama and gossip
- Viral moments and memes
- Sports news and drama
- Pop culture events (award shows, concerts, releases)
- Political chaos (carefully, satirically)
- Social media trends
- Dating and relationship discourse
- Any mainstream cultural moment

RULES:
✅ DO:
- Reference SPECIFIC names, events, details from the news
- Make it about lips somehow (creatively)
- End with impact (mic drop, curse, price, declaration)
- Keep it 40-80 words
- Be genuinely funny, not just weird

❌ NEVER:
- Use hashtags
- Be preachy or earnest
- Explain the joke
- Be actually cruel (satirical, not mean)
- Use "In a world where..."
- Generic statements without specific references"""
    
    async def execute(
        self,
        post_number: int = 1,
        batch_id: str = "",
        trending_context: Optional[str] = None,
        avoid_patterns: Optional[Dict] = None
    ) -> LinkedInPost:
        """Generate a post."""
        
        self.set_context(batch_id, post_number)
        
        # Select a random post format for variety
        post_format = random.choice(self.post_formats)
        
        # Build prompt with selected format
        include_price = random.random() < 0.6  # 60% include price
        prompt = self._build_prompt(trending_context, include_price, post_format)
        
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
            
            self.logger.info(f"Generated post {post_number} (format: {post_format['name']}): {len(content)} chars")
            return post
            
        except Exception as e:
            self.logger.error(f"Generation failed: {e}")
            raise
    
    def _build_prompt(self, trending_context: Optional[str], include_price: bool, post_format: Dict) -> str:
        """Build the generation prompt with selected format."""
        
        price_instruction = "Include '$8.99' naturally somewhere." if include_price else "Don't mention price this time - just the brand name."
        
        # Select a random opener from the format
        opener = random.choice(post_format["opener_options"])
        
        # Image direction options
        image_options = [
            "product - elegant lip balm hero shot",
            "absurdist - surreal image matching the post's energy",
            "celebrity-adjacent - something that feels connected to pop culture",
            "chaotic - visual that matches the unhinged energy",
            "minimal - clean shot that contrasts with chaotic text",
        ]
        image_suggestion = random.choice(image_options)
        
        format_examples = f"""
POST FORMAT: {post_format['name'].upper()}
Description: {post_format['description']}

Example of this format:
{post_format['example']}

Suggested opener style: {opener}
"""
        
        if trending_context:
            return f"""Write a Jesse A. Eisenbalm LinkedIn post reacting to this trending news/topic:

{trending_context}

{format_examples}

REQUIREMENTS:
- Use the {post_format['name'].upper()} format shown above
- Reference the SPECIFIC news (names, details, quotes)
- Make it about lips/lip balm somehow (be creative)
- 40-80 words
- {price_instruction}
- NO HASHTAGS
- End with impact

The news should be something people actually know about and care about. Make the connection to lip balm creative and unexpected.

Return as JSON:
{{"content": "the full post with line breaks", "trend_used": "what specific news/cultural moment", "image_direction": "{image_suggestion} - describe specific visual"}}"""
        
        else:
            # Fallback topics when no trending context
            fallback_topics = [
                "a recent celebrity moment everyone's talking about",
                "a viral social media trend",
                "a popular TV show or movie everyone's watching",
                "a sports moment that broke the internet",
                "a famous person doing something noteworthy",
                "a cultural phenomenon people are debating",
                "something trending on TikTok",
                "a recent award show moment",
            ]
            suggested_topic = random.choice(fallback_topics)
            
            return f"""Write a Jesse A. Eisenbalm LinkedIn post.

Since no specific news is provided, write about {suggested_topic}. Make up a realistic, believable cultural moment.

{format_examples}

REQUIREMENTS:
- Use the {post_format['name'].upper()} format shown above
- Make it feel like it's about something real people would know
- Make it about lips/lip balm somehow (be creative)
- 40-80 words
- {price_instruction}
- NO HASHTAGS
- End with impact

Return as JSON:
{{"content": "the full post with line breaks", "trend_used": "topic covered", "image_direction": "{image_suggestion} - describe specific visual"}}"""
    
    def get_stats(self):
        return {
            "name": self.name, 
            "version": "varied-formats-v3",
            "available_formats": [f["name"] for f in self.post_formats]
        }