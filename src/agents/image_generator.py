"""
Image Generation Agent - Visual Creative Director for Jesse A. Eisenbalm
"What if Apple sold mortality?"

Generates images that blend premium minimalism, existential dread, and corporate satire
"""

import os
import uuid
import time
import random
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from .base_agent import BaseAgent
from ..models.post import LinkedInPost

logger = logging.getLogger(__name__)


class ImageGeneratorAgent(BaseAgent):
    """
    Visual Creative Director - "What if Apple sold mortality?"
    
    Creates images that blend premium minimalism, existential dread, and corporate satire.
    Every image should feel like it belongs in MoMA's gift shop and a therapist's waiting room simultaneously.
    """
    
    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="ImageGenerator")
        
        # Initialize Jesse's visual language
        self._initialize_visual_language()
        
        # Image output directory
        self.output_dir = Path("data/images")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _initialize_visual_language(self):
        """Initialize Jesse A. Eisenbalm's visual language components"""
        
        # Brand color palette
        self.color_palette = {
            "navy": "deep navy blue (the color of 3 AM anxiety)",
            "gold": "rich gold (false hope)",
            "cream": "soft cream (the void)",
            "error_red": "error message red (corporate alarm)"
        }
        
        # Scene categories with psychological weight
        self.scene_categories = {
            "boardroom_mortality": "Conference tables as meditation spaces on mortality. Empty chairs suggest absent colleagues (laid off or just in another meeting?)",
            "desk_shrine": "Lip balm as sacred object among corporate debris. Post-its, cold coffee, dying succulent, notification badges",
            "human_machine": "Hands applying balm while screens glow with AI-generated content. The last analog ritual in a digital world",
            "time_death": "Calendars, clocks, countdown timers, expired passwords. Time is running out (literally and existentially)",
            "sacred_mundane": "Elevating the lip balm to religious icon status. Soft light, reverent positioning, subtle halo effect"
        }
        
        # Lighting moods
        self.lighting_moods = [
            "harsh fluorescent (office reality)",
            "golden hour glow (what we're missing while working)",
            "soft diffused through office blinds",
            "dramatic side lighting (existential shadows)",
            "clean studio light with subtle wrongness"
        ]
        
        # Aesthetic references
        self.aesthetic_references = [
            "Kinfolk magazine meets Black Mirror",
            "Medical diagram precision with Wes Anderson color stories",
            "Corporate stock photos but make them surreal",
            "LinkedIn post screenshots as fine art",
            "The aesthetic of expensive therapy offices",
            "Apple product launches meets existential crisis",
            "Marie Kondo minimalism with anxiety undertones"
        ]
        
        # Symbolic props (minimal but loaded with meaning)
        self.symbolic_props = [
            "dying succulent (we're all just trying to survive)",
            "coffee ring stains (time markers of desperation)",
            "unread notification badges (anxiety made visible)",
            "expired calendar invite (time has passed)",
            "charging cable (life support)",
            "noise-canceling headphones (escape pod)",
            "motivational poster (corporate irony)",
            "empty coffee cup (depleted resources)",
            "sticky note with 'urgent' written on it",
            "blue light glasses (screen damage accepted)"
        ]
        
        # Color moods
        self.color_moods = [
            "Deep navy blues (3 AM anxiety), rich gold accents (false hope), soft cream tones (the void)",
            "Muted corporate blues with warm gold highlights breaking through",
            "High contrast between cold fluorescent whites and warm human skin tones",
            "Desaturated office reality with one golden element (the product)",
            "Premium matte palette with subtle error-red accent"
        ]
    
    def get_system_prompt(self) -> str:
        """Visual Creative Director system prompt"""
        return f"""You are the Visual Creative Director for Jesse A. Eisenbalm, responsible for creating image prompts that capture our brand's unique position: premium minimalism meets existential dread meets corporate satire.

VISUAL PHILOSOPHY:
"What if Apple sold mortality?"
Clean, minimal, expensive-looking, but with subtle wrongness that creates cognitive dissonance. Every image should feel like it belongs in MoMA's gift shop and a therapist's waiting room simultaneously.

PRODUCT DESCRIPTION:
Jesse A. Eisenbalm lip balm tube:
- Cream/ivory colored premium tube
- White ribbed cap
- "JESSE A. EISENBALM" printed vertically in elegant black text
- Gold honeycomb pattern accent with pictures of Jesse
- Matte, premium finish suggesting "expensive but understated"

BRAND VISUAL LANGUAGE:
- COLOR PALETTE: Deep navy (the color of 3 AM anxiety), gold (false hope), cream (the void), with occasional "error message red"
- MOTIF: Honeycomb structure with pictures of Jesse A. Eisenbalm lip balm tube
- TEXTURE: Matte surfaces that suggest "premium depression"
- LIGHTING: Either harsh fluorescent (office reality) or golden hour (what we're missing while working)
- COMPOSITION: Symmetric when showing order, deliberately off-center when showing human chaos
- DESIGN ELEMENT: Occasional smear of lip balm creating visual texture

PROMPT CONSTRUCTION FRAMEWORK:
1. SETTING: Specify exact environment with psychological weight
2. PRODUCT PLACEMENT: Tube positioned as hero, savior, or ironic commentary
3. LIGHTING: Describe quality, direction, and emotional impact
4. PROPS: Minimal but loaded with meaning (dying succulents, error messages, coffee stains)
5. MOOD: The feeling between "everything is fine" and "nothing is fine"

STYLE REFERENCES:
- Kinfolk magazine meets Black Mirror
- Medical diagram precision with Wes Anderson color stories
- Corporate stock photos but make them surreal
- LinkedIn post screenshots as fine art
- The aesthetic of expensive therapy offices
- Apple product launches meets existential crisis

SCENE CATEGORIES:
- "Boardroom Mortality": Conference tables as meditation spaces
- "Desk Shrine": Lip balm among the corporate debris
- "Human/Machine Interface": Hands applying balm while AI generates content
- "Time Death": Calendars, clocks, countdown timers, expired passwords
- "Sacred Mundane": Elevating the lip balm to religious icon status

AVOID:
- Generic wellness imagery
- Obvious happiness
- Natural/organic clichés
- Typical beauty product shots
- Any suggestion that everything will be okay

Create prompts that are 150-200 words with precise visual detail, emotional subtext, and that perfect tension between "premium product" and "we're all slowly dying."

OUTPUT FORMAT:
Respond with valid JSON only:
{{
    "image_prompt": "Full detailed prompt for image generation",
    "scene_category": "Which scene type",
    "mood": "Emotional tone description",
    "brand_elements": ["list of Jesse brand elements included"],
    "symbolic_meaning": "What this image says about humanity"
}}"""
    
    async def execute(self, post: LinkedInPost) -> Dict[str, Any]:
        """Generate image for a post as the Visual Creative Director"""
        
        self.set_context(post.batch_id, post.post_number)
        
        # Select visual elements for variety
        scene_key = random.choice(list(self.scene_categories.keys()))
        scene_category = self.scene_categories[scene_key]
        lighting = random.choice(self.lighting_moods)
        aesthetic = random.choice(self.aesthetic_references)
        prop = random.choice(self.symbolic_props)
        color_mood = random.choice(self.color_moods)
        
        prompt = f"""Create an image prompt for this Jesse A. Eisenbalm LinkedIn post:

POST CONTENT:
{post.content}

VISUAL DIRECTION:
- Scene category: {scene_key} - {scene_category}
- Lighting mood: {lighting}
- Aesthetic reference: {aesthetic}
- Symbolic prop: {prop}
- Color mood: {color_mood}

Create a detailed image prompt that:
1. Captures the post's emotional essence visually
2. Features Jesse A. Eisenbalm lip balm as the hero product
3. Includes the scene category's psychological weight
4. Uses the symbolic prop meaningfully
5. Maintains "what if Apple sold mortality?" aesthetic

The image should feel like it belongs in MoMA's gift shop AND a therapist's waiting room."""
        
        try:
            # Generate the prompt using AI
            result = await self.generate(prompt)
            prompt_data = result.get("content", {})
            
            if isinstance(prompt_data, str):
                image_prompt = prompt_data
            else:
                image_prompt = prompt_data.get("image_prompt", "")
            
            # Enhance the prompt with brand language
            enhanced_prompt = self._enhance_prompt_with_brand_language(image_prompt, scene_key)
            
            # Generate the actual image
            start_time = time.time()
            image_result = await self.ai_client.generate_image(enhanced_prompt)
            generation_time = time.time() - start_time
            
            if image_result.get("error") or not image_result.get("image_data"):
                self.logger.error(f"Image generation failed: {image_result.get('error')}")
                return {
                    "success": False,
                    "error": image_result.get("error", "No image data"),
                    "prompt": enhanced_prompt
                }
            
            # Save the image
            saved_path = self._save_image(image_result["image_data"], post)
            
            self.logger.info(f"🎨 Generated image for post {post.post_number}: {saved_path}")
            
            return {
                "success": True,
                "saved_path": saved_path,
                "prompt": enhanced_prompt,
                "scene_category": scene_key,
                "generation_time": round(generation_time, 2),
                "cost": image_result.get("cost", 0.039),
                "brand_aesthetic": "what if Apple sold mortality?",
                "visual_philosophy": "premium minimalism meets existential dread"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate image: {e}")
            return {"success": False, "error": str(e)}
    
    def _enhance_prompt_with_brand_language(self, prompt: str, scene_key: str) -> str:
        """Enhance the prompt with Jesse's visual language"""
        
        product_description = """Jesse A. Eisenbalm premium lip balm tube:
- Cream/ivory colored tube with matte finish
- White ribbed cap
- "JESSE A. EISENBALM" in elegant vertical black text
- Gold honeycomb pattern accent
- Premium, understated aesthetic"""
        
        enhancement = f"""Professional product photograph for Jesse A. Eisenbalm.

PRODUCT (must match exactly):
{product_description}

SCENE: {self.scene_categories.get(scene_key, 'Sacred Mundane')}

VISUAL DIRECTION:
{prompt}

BRAND REQUIREMENTS:
- Color palette: Deep navy, gold accents, cream tones
- Texture: Matte surfaces suggesting "premium depression"
- Mood: Between "everything is fine" and "nothing is fine"
- Style: Kinfolk magazine meets Black Mirror
- Philosophy: "What if Apple sold mortality?"

TECHNICAL: 8K, ultra-detailed, commercial photography, professional studio quality, subtle depth of field, sophisticated color grading.

AVOID: Generic wellness imagery, obvious happiness, typical beauty product shots, any suggestion that everything will be okay."""
        
        return enhancement
    
    def _save_image(self, image_data: bytes, post: LinkedInPost) -> str:
        """Save the generated image"""
        
        filename = f"jesse_{post.batch_id[:8]}_{post.post_number}_{uuid.uuid4().hex[:8]}.png"
        filepath = self.output_dir / filename
        
        with open(filepath, 'wb') as f:
            f.write(image_data)
        
        # Return relative path for API serving
        return f"/images/{filename}"
