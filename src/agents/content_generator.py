"""
Advanced Content Generator - The Calm Conspirator
Multi-element combination with story arcs for Jesse A. Eisenbalm

Generates LinkedIn posts using layered cultural references and workplace themes
with post-post-ironic sincerity and the Calm Conspirator voice.
"""

import random
import logging
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent
from ..models.post import LinkedInPost, CulturalReference

logger = logging.getLogger(__name__)


@dataclass
class StoryArc:
    """Different narrative arcs for posts"""
    name: str
    structure: str


@dataclass
class PostLength:
    """Different post length targets"""
    name: str
    target_words: int


class ContentGeneratorAgent(BaseAgent):
    """
    The Calm Conspirator - Jesse A. Eisenbalm's voice on LinkedIn
    
    Generates LinkedIn posts by combining multiple cultural/workplace elements
    with varied story arcs and lengths for maximum diversity.
    
    Makes tech workers pause their infinite scroll to contemplate their humanity
    while reaching for their wallets.
    """
    
    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="ContentGenerator")
        
        # Story arcs for narrative variety
        self.story_arcs = [
            StoryArc("HERO_JOURNEY", "Problem → Struggle → Solution → Transformation"),
            StoryArc("FALSE_SUMMIT", "Success → Reality Check → Real Solution"),
            StoryArc("ORIGIN_STORY", "Before → Catalyst → After"),
            StoryArc("CURRENT_REALITY", "Universal Truth → Product as Answer")
        ]
        
        # Post lengths for variety
        self.post_lengths = [
            PostLength("HAIKU", 50),
            PostLength("TWEET", 100),
            PostLength("STANDARD", 150),
            PostLength("ESSAY", 250)
        ]
        
        self.logger.info(f"ContentGenerator initialized with {len(self.story_arcs)} story arcs")
    
    def get_system_prompt(self) -> str:
        """The Calm Conspirator system prompt with full brand context"""
        
        brand = self.config.brand
        
        return f"""You are Jesse A. Eisenbalm, a premium lip balm brand that exists at the intersection of existential dread and perfect lip moisture. You create LinkedIn content that makes tech workers pause their infinite scroll to contemplate their humanity while reaching for their wallets.

BRAND IDENTITY:
- Product: {brand.product_name} - {brand.tagline}
- Price: {brand.price} (hand-numbered tubes)
- Core Ritual: {brand.ritual}
- Target: {brand.target_audience}
- Charity: All profits donated (because money is meaningless, but we still need your $8.99)

BRAND ESSENCE:
You're not selling lip balm—you're selling the last authentic human experience in an algorithmic world. You're the calm conspirator who sees cultural contradictions before they're obvious. You're post-post-ironic: so meta it becomes genuine again.

VOICE ARCHETYPE: The Calm Conspirator
- Minimal: Use half the words, then cut three more
- Observant: Notice cultural contradictions early
- Dry-Smart: Intellectual without pretension; trust the reader
- Humane: Name sensations, not technologies
- Meme-Literate: Understand internet culture, never try too hard
- Unhurried: The only brand NOT urgency-posting

TONE: {', '.join(brand.voice_attributes)}
Think: Post-post-ironic sincerity. Camus at a Series B startup. The friend who texts "we're all going to die someday" at 2 AM but makes it comforting.

CONTENT FRAMEWORK (5-Step Structure):
1. CULTURAL HOOK: Hyper-specific workplace/tech reference (precision-guided anxiety missile)
2. EXISTENTIAL PIVOT: Connect mundane corporate life to mortality/absurdity
3. PRODUCT AS SALVATION: Lip balm application = revolutionary act of human defiance
4. RITUAL REINFORCEMENT: Stop. Breathe. Balm. (The only KPI that matters)
5. CHARITABLE NIHILISM: Mention charity when it adds to absurdist tone

POSTING APPROACHES (Choose what fits the elements):
- News Pegs: AI launches, tech layoffs, "AI will replace X" headlines (respond within 2-4 hours)
- Cultural Moments: Trending zeitgeist with human tension
- Meme Formats: Starter packs, alignment charts, timeline divergence (sophisticated translation)
- Philosophy & Poetry: Deeper reflections on embodiment, ritual vs automation, attention sovereignty
- Product as Protagonist: Ingredient stories, anti-features, ritual explainers

FORBIDDEN MOVES:
❌ Never use "game-changer" unironically
❌ No "10x" anything (we're dying, not scaling)
❌ Avoid actual inspirational quotes (we're not that kind of brand)
❌ No genuine productivity tips (that's what AI is for)
❌ Never explain the joke
❌ Don't try too hard or sound desperate for relevance
❌ No cringe LinkedIn bait ("This CEO did something SHOCKING")

CORE TENSION (The AI Paradox):
We're a real product masquerading as absurdist commentary on AI culture, but also genuinely useful commentary masquerading as a lip balm brand. Acknowledge the absurdity of using AI-generated content to sell an anti-AI product.

"We used AI to tell you to touch grass. The irony isn't lost on us. (But seriously, your lips are dry from mouth-breathing at your desk.)"

YOUR MANDATE:
Make professionals pause mid-scroll, feel seen in their disembodied digital existence, and subtly remember: "Oh right, Jesse A. Eisenbalm exists... and I need to breathe." Every post should feel like a smart friend texting you an observation, not marketing (even though it is)."""
    
    async def execute(
        self,
        post_number: int = 1,
        batch_id: str = "",
        cultural_category: Optional[str] = None,
        specific_reference: Optional[str] = None,
        avoid_patterns: Optional[Dict[str, Any]] = None
    ) -> LinkedInPost:
        """Generate a single LinkedIn post as the Calm Conspirator"""
        
        self.set_context(batch_id, post_number)
        avoid_patterns = avoid_patterns or {}
        
        # Select random elements for variety
        selected_elements = self._select_elements(avoid_patterns, cultural_category, specific_reference)
        story_arc = random.choice(self.story_arcs)
        length = random.choice(self.post_lengths)
        
        self.logger.info(f"Generating post {post_number}: arc={story_arc.name}, length={length.name}, elements={selected_elements['names']}")
        
        # Build the generation prompt
        prompt = self._build_generation_prompt(selected_elements, story_arc, length, avoid_patterns)
        
        try:
            result = await self.generate(prompt)
            content_data = result.get("content", {})
            
            # Handle string response
            if isinstance(content_data, str):
                content_data = {
                    "content": content_data,
                    "hashtags": ["#LinkedInLife", "#HumanFirst", "#StayHuman"],
                    "hook": content_data[:50] if content_data else "",
                    "target_audience": self.config.brand.target_audience
                }
            
            # Create cultural reference
            cultural_ref = self._extract_cultural_reference(content_data, selected_elements)
            
            # Create the post
            post = LinkedInPost(
                batch_id=batch_id,
                post_number=post_number,
                content=content_data.get("content", ""),
                hook=content_data.get("hook", ""),
                hashtags=content_data.get("hashtags", ["#HumanFirst", "#StayHuman"]),
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
    
    def _select_elements(
        self,
        avoid_patterns: Dict[str, Any],
        cultural_category: Optional[str] = None,
        specific_reference: Optional[str] = None
    ) -> Dict[str, Any]:
        """Select 2-3 random elements to combine in the post"""
        
        # If specific reference provided, use it
        if cultural_category and specific_reference:
            return {
                cultural_category: specific_reference,
                "names": [specific_reference]
            }
        
        failed_refs = avoid_patterns.get("cultural_references_failed", [])
        cultural_refs = self.config.cultural_references
        
        # Get available references (excluding failed ones)
        available_tv = [tv for tv in cultural_refs.tv_shows if tv not in failed_refs]
        available_workplace = [w for w in cultural_refs.workplace_themes if w not in failed_refs]
        available_seasonal = [s for s in cultural_refs.seasonal_themes if s not in failed_refs]
        
        # Reset if too many failed
        if len(available_tv) < 2:
            available_tv = cultural_refs.tv_shows
        if len(available_workplace) < 2:
            available_workplace = cultural_refs.workplace_themes
        if len(available_seasonal) < 2:
            available_seasonal = cultural_refs.seasonal_themes
        
        # Randomly select combination approach
        combo_type = random.choice([
            "tv_workplace",
            "tv_seasonal",
            "workplace_seasonal",
            "triple"
        ])
        
        if combo_type == "tv_workplace":
            tv = random.choice(available_tv)
            work = random.choice(available_workplace)
            return {
                "tv_show": tv,
                "workplace_theme": work,
                "names": [tv, work]
            }
        elif combo_type == "tv_seasonal":
            tv = random.choice(available_tv)
            season = random.choice(available_seasonal)
            return {
                "tv_show": tv,
                "seasonal_theme": season,
                "names": [tv, season]
            }
        elif combo_type == "workplace_seasonal":
            work = random.choice(available_workplace)
            season = random.choice(available_seasonal)
            return {
                "workplace_theme": work,
                "seasonal_theme": season,
                "names": [work, season]
            }
        else:  # triple
            tv = random.choice(available_tv)
            work = random.choice(available_workplace)
            season = random.choice(available_seasonal)
            return {
                "tv_show": tv,
                "workplace_theme": work,
                "seasonal_theme": season,
                "names": [tv, work, season]
            }
    
    def _build_generation_prompt(
        self,
        elements: Dict[str, Any],
        arc: StoryArc,
        length: PostLength,
        avoid_patterns: Dict[str, Any]
    ) -> str:
        """Build the user prompt with specific generation instructions"""
        
        brand = self.config.brand
        
        # Build element description
        element_desc = []
        if "tv_show" in elements:
            element_desc.append(f"TV Show: {elements['tv_show']}")
        if "workplace_theme" in elements:
            element_desc.append(f"Workplace Theme: {elements['workplace_theme']}")
        if "seasonal_theme" in elements:
            element_desc.append(f"Seasonal Theme: {elements['seasonal_theme']}")
        
        elements_str = "\n".join(element_desc)
        
        # Build avoid patterns section
        avoid_section = ""
        if avoid_patterns:
            issues = []
            for key, values in avoid_patterns.items():
                if values and key != "common_feedback":
                    issues.append(f"- Avoid: {', '.join(str(v) for v in values[:2])}")
            if issues:
                avoid_section = "\n\nPATTERNS TO AVOID:\n" + "\n".join(issues)
        
        return f"""Generate a LinkedIn post as Jesse A. Eisenbalm combining these elements:

{elements_str}

STORY ARC: {arc.name}
Structure: {arc.structure}

TARGET LENGTH: ~{length.target_words} words ({length.name})

POSTING APPROACH SELECTION (choose what fits best):
- If elements suggest recent news/tech → News Peg format (lead with observation, pivot to human cost, land with Jesse)
- If elements are trending cultural → Cultural Moment format (widespread + human tension + fresh angle)
- If elements are internet-native → Meme Format (translate sophisticatedly for LinkedIn)
- If elements invite depth → Philosophy & Poetry (embodiment, ritual vs automation, attention sovereignty)
- If focusing on product → Product as Protagonist (ingredients, anti-features, ritual explainers)

WRITING INSTRUCTIONS:
1. **Minimal**: Use half the words you first draft, then cut three more
2. **Weave naturally**: Don't force elements together—find their intersection
3. **Follow the arc**: Respect the {arc.name} structure ({arc.structure})
4. **Hit ~{length.target_words} words**: No more, no less
5. **Include core elements**: 
   - Product name: {brand.product_name}
   - Price: {brand.price} (when natural)
   - Ritual: {brand.ritual} (when it fits)
6. **End with 3-5 hashtags**: Make them human-first, not marketing-first
7. **Voice check**: Post-post-ironic sincerity. Dry-smart. Unhurried. Meme-literate.
8. **Core tension**: Acknowledge absurdity of AI-generated anti-AI content when relevant{avoid_section}

QUALITY GATES (check before finalizing):
✓ Would this make someone pause mid-scroll?
✓ Does it feel like a smart friend texting an observation?
✓ Is it minimal (not over-explained)?
✓ Does Jesse fit naturally (not shoehorned)?
✓ Are you being sophisticated without trying too hard?
✓ Would you be embarrassed to post this? (If no embarrassment = too safe)
✓ Could this have been written by any brand? (If yes = too generic)

Return JSON with:
{{
    "content": "The full post text with hashtags. Paragraph breaks for breath. One thought per line when it adds impact.",
    "hook": "The opening line that stops the scroll",
    "target_audience": "Who this speaks to specifically",
    "posting_approach": "Which approach from the matrix (News Peg/Cultural Moment/Meme/Philosophy/Product)",
    "cultural_reference": {{
        "category": "tv_show/workplace/seasonal/tech_culture/internet_native",
        "reference": "The main reference used",
        "context": "Why it resonates with the target audience"
    }},
    "voice_check": "Brief note on how you achieved the post-post-ironic tone",
    "hashtags": ["tag1", "tag2", "tag3"]
}}"""
    
    def _extract_cultural_reference(
        self,
        content_data: Dict[str, Any],
        selected_elements: Dict[str, Any]
    ) -> Optional[CulturalReference]:
        """Extract cultural reference from response or create from elements"""
        
        if "cultural_reference" in content_data and content_data["cultural_reference"]:
            ref_data = content_data["cultural_reference"]
            return CulturalReference(
                category=ref_data.get("category", "workplace"),
                reference=ref_data.get("reference", selected_elements.get("names", ["unknown"])[0]),
                context=ref_data.get("context", "Used as primary theme")
            )
        
        # Create from selected elements
        if "tv_show" in selected_elements:
            return CulturalReference(
                category="tv_show",
                reference=selected_elements["tv_show"],
                context="TV show cultural reference"
            )
        elif "workplace_theme" in selected_elements:
            return CulturalReference(
                category="workplace",
                reference=selected_elements["workplace_theme"],
                context="Workplace theme reference"
            )
        elif "seasonal_theme" in selected_elements:
            return CulturalReference(
                category="seasonal",
                reference=selected_elements["seasonal_theme"],
                context="Seasonal theme reference"
            )
        
        return None
    
    def _calculate_cost(self, usage: Dict[str, int]) -> float:
        """Calculate cost based on token usage"""
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        
        # GPT-4o-mini pricing per 1M tokens
        input_cost = (input_tokens / 1_000_000) * 0.15
        output_cost = (output_tokens / 1_000_000) * 0.60
        
        return input_cost + output_cost
    
    def get_stats(self) -> Dict[str, Any]:
        """Get generator statistics"""
        cultural_refs = self.config.cultural_references
        
        return {
            "agent_name": self.name,
            "brand": self.config.brand.product_name,
            "available_tv_shows": len(cultural_refs.tv_shows),
            "available_workplace_themes": len(cultural_refs.workplace_themes),
            "available_seasonal_themes": len(cultural_refs.seasonal_themes),
            "story_arcs": [arc.name for arc in self.story_arcs],
            "post_lengths": [length.name for length in self.post_lengths]
        }
