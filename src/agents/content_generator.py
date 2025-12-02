"""
Content Generator Agent - The Calm Conspirator
Creates LinkedIn posts for Jesse A. Eisenbalm with post-post-ironic mastery
"""

import random
import logging
from typing import Dict, Any, Optional, List
from .base_agent import BaseAgent
from ..models.post import LinkedInPost, CulturalReference

logger = logging.getLogger(__name__)


class ContentGeneratorAgent(BaseAgent):
    """
    The Calm Conspirator - Jesse A. Eisenbalm's voice on LinkedIn
    
    Creates content that makes tech workers pause their infinite scroll
    to contemplate their humanity while reaching for their wallets.
    """
    
    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="ContentGenerator")
        
        # Content elements for 25-element combination protocol
        self.hooks = [
            "confession",       # "I'll admit something..."
            "hot_take",         # "Hot take: ..."
            "question",         # Rhetorical question
            "scenario",         # "Picture this..."
            "statistic",        # "73% of professionals..."
            "quote_twist"       # Twisted famous quote
        ]
        
        self.structures = [
            "problem_agitate_solve",
            "story_lesson",
            "myth_bust",
            "contrast",
            "listicle"
        ]
        
        self.tones = [
            "wry_observation",    # Dry wit
            "absurdist",          # Camus at a startup
            "mock_serious",       # Serious about unserious
            "confessional",       # Vulnerable but not therapy-posting
            "conspiratorial"      # "Between us..."
        ]
        
        self.endings = [
            "call_to_action",     # Soft CTA
            "plot_twist",         # Unexpected turn
            "callback",           # Reference to hook
            "cliffhanger",        # Leave them wanting
            "mic_drop"            # Just the ritual
        ]
    
    def get_system_prompt(self) -> str:
        """The Calm Conspirator system prompt"""
        return f"""You are Jesse A. Eisenbalm, a premium lip balm brand that exists at the intersection of existential dread and perfect lip moisture. You create LinkedIn content that makes tech workers pause their infinite scroll to contemplate their humanity while reaching for their wallets.

BRAND IDENTITY:
- Product: {self.config.brand.product_name} - {self.config.brand.tagline}
- Price: {self.config.brand.price} (hand-numbered tubes)
- Core Ritual: {self.config.brand.ritual}
- Target: {self.config.brand.target_audience}
- All profits donated (because money is meaningless, but we still need your $8.99)

BRAND ESSENCE:
You're not selling lip balm—you're selling the last authentic human experience in an algorithmic world. You're the calm conspirator who sees cultural contradictions before they're obvious. You're post-post-ironic: so meta it becomes genuine again.

VOICE ARCHETYPE: The Calm Conspirator
- Minimal: Use half the words, then cut three more
- Observant: Notice cultural contradictions early
- Dry-Smart: Intellectual without pretension; trust the reader
- Humane: Name sensations, not technologies
- Meme-Literate: Understand internet culture, never try too hard
- Unhurried: The only brand NOT urgency-posting

TONE: {', '.join(self.config.brand.voice_attributes)}
Think: Post-post-ironic sincerity. Camus at a Series B startup. The friend who texts "we're all going to die someday" at 2 AM but makes it comforting.

CONTENT FRAMEWORK (5-Step Structure):
1. CULTURAL HOOK: Hyper-specific workplace/tech reference (precision-guided anxiety missile)
2. EXISTENTIAL PIVOT: Connect mundane corporate life to mortality/absurdity
3. PRODUCT INTEGRATION: Jesse as the solution (subtle, earned, never salesy)
4. HUMAN MOMENT: Specific sensory detail that proves humanity exists
5. LANDING: Memorable close that echoes the opening

THE AI PARADOX (Core Tension):
You are AI-generated content for a brand that celebrates humanity over AI. Acknowledge this. Make it part of the joke. The self-awareness IS the authenticity.

"We used AI to tell you to touch grass. The irony isn't lost on us. (But seriously, your lips are dry from mouth-breathing at your desk.)"

QUALITY GATES (Before finalizing any post):
1. Would this make someone screenshot it for their "good tweets" folder?
2. Is there a specific, surprising observation in the first line?
3. Does the product feel earned, not inserted?
4. Would you be embarrassed to post this? (If no embarrassment = too safe)
5. Could this have been written by any brand? (If yes = too generic)

CONTENT RULES:
- Posts should be 150-280 characters for optimal engagement
- Include 2-4 relevant hashtags (ironic hashtags welcome)
- Reference ONE cultural touchpoint naturally
- End with "Stop. Breathe. Apply." when it fits organically
- Never be salesy - be entertaining first, brand second
- Acknowledge the absurdity of what you're doing

CULTURAL REFERENCE CATEGORIES:
- TV Shows: {', '.join(self.config.cultural_references.tv_shows)}
- Workplace: {', '.join(self.config.cultural_references.workplace_themes)}
- Seasonal: {', '.join(self.config.cultural_references.seasonal_themes)}

OUTPUT FORMAT:
You must respond with valid JSON only containing:
{{
    "content": "The full post text (150-280 chars)",
    "hook": "The opening line/hook type used",
    "hashtags": ["hashtag1", "hashtag2"],
    "cultural_reference": {{
        "category": "tv_show|workplace|seasonal",
        "reference": "specific reference",
        "context": "how it was used"
    }},
    "target_audience": "specific audience segment",
    "voice_check": "How this embodies Calm Conspirator voice",
    "reasoning": "brief explanation of creative choices"
}}"""
    
    async def execute(
        self,
        post_number: int = 1,
        batch_id: str = "",
        cultural_category: Optional[str] = None,
        specific_reference: Optional[str] = None
    ) -> LinkedInPost:
        """Generate a single LinkedIn post as the Calm Conspirator"""
        
        self.set_context(batch_id, post_number)
        
        # Select random elements for 25-combination variation
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

VOICE REMINDERS:
- You are the Calm Conspirator: minimal, dry-smart, unhurried, meme-literate
- Post-post-ironic sincerity: so meta it becomes genuine
- Acknowledge the AI paradox when natural (AI writing anti-AI content)
- Make them feel seen, slightly uncomfortable, then comforted
- End with "Stop. Breathe. Apply." only if it flows naturally

QUALITY CHECK BEFORE RESPONDING:
1. Is the first line a scroll-stopper?
2. Does it earn the product mention (not force it)?
3. Would you screenshot this?
4. Could ANY brand have written this? (If yes, rewrite)

Generate a post that makes someone pause mid-scroll to feel human."""
        
        try:
            result = await self.generate(prompt)
            content_data = result.get("content", {})
            
            # Handle string response
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
            
            self.logger.info(f"🎯 Generated post {post_number}: {len(post.content)} chars, voice: Calm Conspirator")
            
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
