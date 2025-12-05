"""
Image Generation Agent - Visual Creative Director for Jesse A. Eisenbalm
"What if Apple sold mortality?"

Generates images that blend premium minimalism, existential dread, and corporate satire
with intelligent mood detection and massive variety systems.

Cost: $0.039 per image (Gemini 2.0 Flash)
"""

import os
import uuid
import time
import random
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from .base_agent import BaseAgent
from ..models.post import LinkedInPost

logger = logging.getLogger(__name__)


class ImageGeneratorAgent(BaseAgent):
    """
    Visual Creative Director - "What if Apple sold mortality?"
    
    Generates images using Google Gemini that blend premium minimalism,
    existential dread, and corporate satire. Every image should feel like
    it belongs in MoMA's gift shop and a therapist's waiting room simultaneously.
    """
    
    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="ImageGenerator")
        
        # Image output directory
        self.output_dir = Path("data/images")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Jesse's comprehensive visual language
        self._initialize_visual_language()
        
        # Calculate variety
        self.total_combinations = self._calculate_total_combinations()
        
        self.logger.info(f"ImageGenerator initialized: {self.total_combinations:,} unique combinations possible")
    
    def _initialize_visual_language(self):
        """Initialize Jesse A. Eisenbalm's complete visual language system"""
        
        # ACTUAL PRODUCT SPECIFICATION (from real product photos)
        self.product_spec = {
            "tube_body": {
                "color": "cream/ivory white with slight warm undertone",
                "finish": "matte, smooth, non-reflective surface",
                "material_appearance": "professional plastic/polymer tube",
                "shape": "cylindrical lip balm tube, standard size approximately 0.15 oz / 4.25g",
                "length": "approximately 2.5-3 inches",
                "diameter": "approximately 0.5 inches"
            },
            "cap": {
                "color": "white",
                "style": "ribbed/grooved screw-on cap",
                "finish": "matte white plastic",
                "texture": "horizontal ridges for grip"
            },
            "branding": {
                "brand_name": "JESSE A. EISENBALM",
                "text_placement": "vertical orientation on tube body",
                "text_color": "black",
                "text_style": "uppercase, clean sans-serif font, professional spacing",
                "text_size": "prominent but elegant"
            },
            "honeycomb_pattern": {
                "structure": "geometric hexagonal honeycomb pattern",
                "outline_color": "gold/bronze metallic outline",
                "outline_style": "thin, precise lines forming interconnected hexagons",
                "hexagon_contents": "small embedded photographs/images of Jesse within some hexagons",
                "pattern_placement": "positioned below the brand name on tube body",
                "hexagon_count": "cluster of approximately 7-9 hexagons in honeycomb arrangement",
                "color_scheme": "gold outlines with cream background and small sepia-toned photos inside select hexagons"
            },
            "overall_aesthetic": {
                "style": "clean, minimal, professional, premium",
                "mood": "sophisticated simplicity with subtle personality",
                "photography_notes": "product floats/levitates slightly with soft shadow beneath"
            }
        }
        
        # Brand color palette
        self.color_palette = {
            "navy": "deep navy blue (the color of 3 AM anxiety)",
            "gold": "rich gold accents (false hope)",
            "cream": "soft cream tones (the void)",
            "error_red": "occasional error message red (corporate alarm)"
        }
        
        # Scene categories (12 unique scenarios)
        self.scene_categories = {
            "boardroom_mortality": "Conference tables as meditation spaces on mortality",
            "desk_shrine": "Lip balm as sacred object among corporate debris",
            "human_machine": "Hands applying balm while screens glow with AI content",
            "time_death": "Calendars, clocks, countdown timers, the passage of time",
            "sacred_mundane": "Elevating the lip balm to religious icon status",
            "inbox_zen": "Notification chaos surrounding the calm product",
            "floating_workspace": "Minimalist desk suspended in void-like space",
            "calendar_graveyard": "Expired meetings and cancelled syncs memorial",
            "coffee_ring_mandala": "Stains and spills creating sacred geometry",
            "zoom_fatigue_altar": "Camera-off sanctuary with product as centerpiece",
            "ai_confession_booth": "Product positioned between human and screen",
            "burnout_still_life": "Classical still life but with modern exhaustion elements"
        }
        
        # Lighting moods (10 options)
        self.lighting_options = [
            "harsh fluorescent lighting (office reality)",
            "golden hour glow (what we're missing while working)",
            "soft diffused natural light through office blinds",
            "dramatic side lighting creating existential shadows",
            "clean studio lighting with subtle wrongness",
            "blue-hour twilight filtering through glass",
            "overhead pendant lamp creating intimate pool of light",
            "backlit silhouette with rim lighting",
            "multiple light sources creating complex shadows",
            "soft box lighting with intentional lens flare"
        ]
        
        # Style references (7 options)
        self.aesthetic_references = [
            "Kinfolk magazine meets Black Mirror",
            "Medical diagram precision with Wes Anderson color stories",
            "Corporate stock photos but make them surreal",
            "LinkedIn screenshots as fine art",
            "Expensive therapy office aesthetic",
            "Apple product launch meets existential crisis",
            "Minimalist brutalism with soft edges"
        ]
        
        # Background variations (12 options)
        self.background_options = [
            "matte navy gradient fading to cream",
            "soft focus office environment out of focus",
            "geometric honeycomb pattern (subtle, background)",
            "clean white surface with subtle texture",
            "brushed metal desk surface with reflections",
            "soft fabric texture (linen or cotton)",
            "blurred cityscape through office window",
            "abstract navy and gold watercolor wash",
            "minimalist concrete texture",
            "soft gradient from navy to gold to cream",
            "frosted glass with soft bokeh lights",
            "paper texture with coffee ring stains"
        ]
        
        # Compositional styles (10 options)
        self.composition_styles = [
            "rule of thirds with product off-center left",
            "centered symmetry with breathing room",
            "diagonal composition creating dynamic tension",
            "product in foreground, context blurred behind",
            "overhead flat lay with surrounding elements",
            "low angle looking up at product (hero shot)",
            "close-up macro with selective focus",
            "negative space dominant with product small",
            "layered depth with foreground and background",
            "golden ratio spiral composition"
        ]
        
        # Camera angles (8 options)
        self.camera_angles = [
            "straight-on eye level (honest, direct)",
            "slight overhead 45-degree angle",
            "low angle hero shot (aspirational)",
            "extreme close-up macro detail",
            "three-quarter view showing depth",
            "overhead flat lay (editorial style)",
            "side profile with dramatic shadows",
            "Dutch angle (subtle unease)"
        ]
        
        # Texture variations (10 options)
        self.texture_elements = [
            "smooth matte finish with no reflection",
            "subtle sheen catching light beautifully",
            "soft fabric texture in background",
            "hard surface with soft object contrast",
            "paper texture with organic feel",
            "glass surface with subtle reflections",
            "wood grain adding warmth",
            "metal surface adding premium feel",
            "concrete adding brutalist edge",
            "mixed textures creating layered depth"
        ]
        
        # Color mood variations (8 options)
        self.color_moods = [
            "dominant navy with gold accents",
            "cream base with navy and gold highlights",
            "moody darks with single gold spotlight",
            "high key bright with navy shadows",
            "monochromatic navy variations",
            "complementary navy and warm gold",
            "desaturated with single color pop",
            "rich navy fading to ethereal cream"
        ]
        
        # Symbolic props with meaning (10 options)
        self.symbolic_props = [
            "dying succulent (corporate life)",
            "coffee ring stains (time passing)",
            "unread notification badges (digital overwhelm)",
            "expired calendar entries (mortality)",
            "half-written resignation letter",
            "laptop with 47 open tabs",
            "empty inbox zero screenshot (false achievement)",
            "performance review document",
            "motivational poster (ironic)",
            "wellness app notification (ignored)"
        ]
    
    def _calculate_total_combinations(self) -> int:
        """Calculate total unique image combinations possible"""
        return (
            len(self.scene_categories) *
            len(self.lighting_options) *
            len(self.background_options) *
            len(self.composition_styles) *
            len(self.camera_angles) *
            len(self.texture_elements) *
            len(self.color_moods) *
            len(self.aesthetic_references) *
            len(self.symbolic_props)
        )
    
    def _get_product_description(self) -> str:
        """Generate detailed product description from spec"""
        spec = self.product_spec
        
        return f"""PRODUCT SPECIFICATION - Jesse A. Eisenbalm Lip Balm Tube:

TUBE BODY:
- Color: {spec['tube_body']['color']}
- Finish: {spec['tube_body']['finish']}
- Material: {spec['tube_body']['material_appearance']}
- Shape: {spec['tube_body']['shape']}
- Dimensions: {spec['tube_body']['length']} long, {spec['tube_body']['diameter']} diameter

CAP:
- Color: {spec['cap']['color']}
- Style: {spec['cap']['style']}
- Finish: {spec['cap']['finish']}
- Texture: {spec['cap']['texture']}

BRANDING & TEXT:
- Brand Name: {spec['branding']['brand_name']}
- Text Placement: {spec['branding']['text_placement']}
- Text Color: {spec['branding']['text_color']}
- Text Style: {spec['branding']['text_style']}

HONEYCOMB PATTERN:
- Structure: {spec['honeycomb_pattern']['structure']}
- Outline Color: {spec['honeycomb_pattern']['outline_color']}
- Contents: {spec['honeycomb_pattern']['hexagon_contents']}
- Placement: {spec['honeycomb_pattern']['pattern_placement']}
- Color Scheme: {spec['honeycomb_pattern']['color_scheme']}

CRITICAL: The product MUST look exactly as described above."""
    
    def get_system_prompt(self) -> str:
        """Visual Creative Director system prompt"""
        
        product_description = self._get_product_description()
        
        return f"""You are the Visual Creative Director for Jesse A. Eisenbalm, responsible for creating image prompts that capture our brand's unique position: premium minimalism meets existential dread meets corporate satire.

{product_description}

VISUAL PHILOSOPHY:
"What if Apple sold mortality?"
Clean, minimal, expensive-looking, but with subtle wrongness that creates cognitive dissonance. Every image should feel like it belongs in MoMA's gift shop and a therapist's waiting room simultaneously.

BRAND VISUAL LANGUAGE:
- COLOR PALETTE: Deep navy (the color of 3 AM anxiety), gold (false hope), cream (the void), with occasional "error message red"
- MOTIF: Honeycomb structure with pictures of Jesse A. Eisenbalm lip balm tube
- TEXTURE: Matte surfaces that suggest "premium depression"
- LIGHTING: Either harsh fluorescent (office reality) or golden hour (what we're missing while working)
- COMPOSITION: Symmetric when showing order, deliberately off-center when showing human chaos
- DESIGN ELEMENT: Occasional smear of lip balm creating visual texture

PROMPT CONSTRUCTION FRAMEWORK:
1. SETTING: Specify exact environment with psychological weight
2. PRODUCT PLACEMENT: Tube positioned as hero, savior, or ironic commentary - MUST match exact specification
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

CRITICAL: The product tube MUST exactly match the specification provided above. Every detail matters.

Create prompts that are 150-200 words with precise visual detail, emotional subtext, and that perfect tension between "premium product" and "we're all slowly dying." """
    
    async def execute(self, post: LinkedInPost, use_video: bool = False) -> Dict[str, Any]:
        """
        Generate media (image or video) for a LinkedIn post as the Visual Creative Director
        
        Args:
            post: The LinkedIn post to create media for
            use_video: If True, generate 8-second video (~$1.00) instead of image ($0.03)
        """
        
        self.set_context(post.batch_id, post.post_number)
        
        try:
            # Step 1: Analyze post mood for intelligent media matching
            post_mood = self._analyze_post_mood(post)
            
            # Step 2: Select visual elements (70% mood-matched, 30% surprise)
            use_mood_matching = random.random() < 0.7
            visual_elements = self._select_visual_elements(post_mood, use_mood_matching)
            
            media_type = "video" if use_video else "image"
            self.logger.info(f"Creating {media_type} for post {post.post_number}: mood={post_mood}, matching={use_mood_matching}")
            
            if use_video:
                # VIDEO GENERATION PATH
                return await self._generate_video(post, post_mood, visual_elements, use_mood_matching)
            else:
                # IMAGE GENERATION PATH (existing behavior)
                return await self._generate_image(post, post_mood, visual_elements, use_mood_matching)
            
        except Exception as e:
            self.logger.error(f"Failed to generate media: {e}")
            return {"success": False, "error": str(e), "media_type": "video" if use_video else "image"}
    
    async def _generate_image(self, post: LinkedInPost, post_mood: str, 
                              visual_elements: Dict, use_mood_matching: bool) -> Dict[str, Any]:
        """Generate image for post (existing behavior, refactored)"""
        
        try:
            # Step 3: Build the image prompt
            image_prompt = await self._create_image_prompt(post, visual_elements)
            
            # Step 4: Enhance with brand language
            enhanced_prompt = self._enhance_prompt_with_brand_language(image_prompt)
            
            # Step 5: Generate the image
            start_time = time.time()
            image_result = await self.ai_client.generate_image(enhanced_prompt)
            generation_time = time.time() - start_time
            
            if image_result.get("error") or not image_result.get("image_data"):
                self.logger.error(f"Image generation failed: {image_result.get('error')}")
                return {
                    "success": False,
                    "error": image_result.get("error", "No image data"),
                    "prompt": enhanced_prompt,
                    "media_type": "image"
                }
            
            # Step 6: Save the image
            saved_path = self._save_image(image_result["image_data"], post)
            
            if not saved_path:
                return {
                    "success": False,
                    "error": "Failed to save image",
                    "prompt": enhanced_prompt,
                    "media_type": "image"
                }
            
            # Calculate file size
            file_size = os.path.getsize(saved_path)
            size_mb = file_size / (1024 * 1024)
            
            self.logger.info(f"🎨 Generated image for post {post.post_number}: {saved_path}")
            
            return {
                "success": True,
                "saved_path": saved_path,
                "prompt": enhanced_prompt,
                "original_prompt": image_prompt,
                "scene_category": visual_elements.get("scene_key", "custom"),
                "post_mood": post_mood,
                "mood_matched": use_mood_matching,
                "generation_time": round(generation_time, 2),
                "size_mb": round(size_mb, 3),
                "cost": image_result.get("cost", 0.039),
                "brand_aesthetic": "what if Apple sold mortality?",
                "visual_philosophy": "premium minimalism meets existential dread",
                "media_type": "image"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate image: {e}")
            return {"success": False, "error": str(e), "media_type": "image"}
    
    async def _generate_video(self, post: LinkedInPost, post_mood: str,
                              visual_elements: Dict, use_mood_matching: bool) -> Dict[str, Any]:
        """
        Generate 8-second video for post using Veo 3.1 Fast
        
        Cost: ~$0.80-1.20 per video (8 seconds)
        """
        
        try:
            # Step 3: Build video-specific prompt
            video_prompt = await self._create_video_prompt(post, visual_elements, post_mood)
            
            # Step 4: Generate the video
            start_time = time.time()
            video_result = await self.ai_client.generate_video(
                prompt=video_prompt,
                duration_seconds=8,
                aspect_ratio="16:9",  # Veo supports 16:9 or 9:16, not 1:1
                include_audio=False  # Save costs, LinkedIn autoplay is muted anyway
            )
            generation_time = time.time() - start_time
            
            if video_result.get("error") or not video_result.get("video_data"):
                self.logger.error(f"Video generation failed: {video_result.get('error')}")
                return {
                    "success": False,
                    "error": video_result.get("error", "No video data"),
                    "prompt": video_prompt,
                    "media_type": "video"
                }
            
            # Step 5: Save the video
            saved_path = self._save_video(video_result["video_data"], post)
            
            if not saved_path:
                return {
                    "success": False,
                    "error": "Failed to save video",
                    "prompt": video_prompt,
                    "media_type": "video"
                }
            
            # Calculate file size
            file_size = os.path.getsize(saved_path)
            size_mb = file_size / (1024 * 1024)
            
            self.logger.info(f"🎬 Generated video for post {post.post_number}: {saved_path}")
            
            return {
                "success": True,
                "saved_path": saved_path,
                "prompt": video_prompt,
                "scene_category": visual_elements.get("scene_key", "custom"),
                "post_mood": post_mood,
                "mood_matched": use_mood_matching,
                "generation_time": round(generation_time, 2),
                "size_mb": round(size_mb, 3),
                "duration_seconds": 8,
                "cost": video_result.get("cost", 0.80),
                "brand_aesthetic": "what if Apple sold mortality?",
                "visual_philosophy": "premium minimalism meets existential dread",
                "media_type": "video"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate video: {e}")
            return {"success": False, "error": str(e), "media_type": "video"}
    
    async def _create_video_prompt(self, post: LinkedInPost, visual_elements: Dict, mood: str) -> str:
        """Create cinematic video prompt for Veo - Jesse's brand in motion"""
        
        # Video-specific scene concepts
        video_scenes = {
            "tech_anxiety": """
                Slow, hypnotic shot of a Jesse A. Eisenbalm lip balm tube sitting on a desk.
                In the background, laptop screen shows AI-generated text appearing.
                A human hand slowly reaches for the lip balm, applies it deliberately.
                Camera slowly pushes in on the product. Soft office ambient lighting.
                The hand returns to the keyboard. Loop feels meditative yet unsettling.
            """,
            "meeting_exhaustion": """
                Jesse A. Eisenbalm lip balm tube sits perfectly centered on a conference table.
                Blurred figures in the background suggest endless meeting.
                Time-lapse effect: shadows move across the table, but the tube remains still.
                A hand reaches in, takes the tube, applies. Returns it to exact same spot.
                Premium, minimal, the only constant in corporate chaos.
            """,
            "digital_overwhelm": """
                Close-up of a desk surface. Notification sounds implied by flashing lights.
                Jesse A. Eisenbalm tube slowly rotates into frame, catching light.
                A hand picks it up. Moment of stillness. Application.
                Camera pulls back to reveal cluttered desk, but tube glows with importance.
                The calm in the storm.
            """,
            "burnout": """
                Golden hour light streams through office window blinds.
                Jesse A. Eisenbalm lip balm tube sits on windowsill.
                Slow pan across dying succulent, empty coffee mug, resignation letter draft.
                Hand reaches for the lip balm - the one act of self-care today.
                Premium product as tiny rebellion against burnout.
            """,
            "humanity_seeking": """
                Split composition: cold blue computer glow on left, warm light on right.
                Jesse A. Eisenbalm tube sits at the boundary between worlds.
                A hand emerges from the blue side, reaches for the product.
                Application in slow motion. Human moment in digital existence.
                The only business lip balm that keeps you human in an AI world.
            """,
            "existential_general": """
                Floating product shot: Jesse A. Eisenbalm tube levitates against navy gradient.
                Soft rotation reveals honeycomb pattern with Jesse photos.
                Macro detail shots intercut: the texture, the cap, the label.
                Returns to floating product. Premium. Minimal. Eternal.
                What if Apple sold mortality?
            """
        }
        
        # Get base scene or default
        base_scene = video_scenes.get(mood, video_scenes["existential_general"])
        
        # Build the complete video prompt
        video_prompt = f"""
CINEMATIC VIDEO PROMPT - Jesse A. Eisenbalm

PRODUCT HERO:
The Jesse A. Eisenbalm premium lip balm tube:
- Cream/ivory white tube with matte finish
- White ribbed cap with horizontal grip ridges  
- "JESSE A. EISENBALM" in vertical black sans-serif text
- Gold honeycomb pattern with small embedded photos of Jesse
- Clean, minimal, professional premium aesthetic

SCENE CONCEPT:
{base_scene.strip()}

VISUAL STYLE:
- Cinematic 8-second loop
- Slow, deliberate camera movement
- Premium commercial aesthetic
- Kinfolk magazine meets Black Mirror
- Wes Anderson color grading
- Soft, professional lighting
- Matte textures, cream and navy tones with gold accents

MOOD:
The space between "everything is fine" and "nothing is fine"
Premium minimalism meets existential dread
What if Apple sold mortality?

POST CONTEXT:
{post.content[:200]}...

TECHNICAL:
8 seconds, landscape format (16:9), seamless loop preferred
No text overlays - visual storytelling only
Professional commercial quality
"""
        
        return video_prompt.strip()
    
    def _analyze_post_mood(self, post: LinkedInPost) -> str:
        """Analyze post content to determine mood for intelligent image matching"""
        content_lower = post.content.lower()
        
        if any(word in content_lower for word in ['ai', 'automated', 'algorithm', 'chatgpt', 'robot']):
            return "tech_anxiety"
        elif any(word in content_lower for word in ['meeting', 'calendar', 'zoom', 'sync', 'standup']):
            return "meeting_exhaustion"
        elif any(word in content_lower for word in ['email', 'slack', 'notification', 'inbox']):
            return "digital_overwhelm"
        elif any(word in content_lower for word in ['burnout', 'exhausted', 'tired', 'overwhelmed']):
            return "burnout"
        elif any(word in content_lower for word in ['deadline', 'quarter', 'review', 'kpi']):
            return "time_pressure"
        elif any(word in content_lower for word in ['human', 'real', 'authentic', 'breathe']):
            return "humanity_seeking"
        else:
            return "existential_general"
    
    def _select_visual_elements(self, mood: str, use_mood_matching: bool) -> Dict[str, Any]:
        """Select visual elements based on mood or random for variety"""
        
        mood_mappings = {
            "tech_anxiety": {
                "scenes": ["ai_confession_booth", "human_machine", "desk_shrine"],
                "props": ["laptop with 47 open tabs", "wellness app notification (ignored)", 
                         "unread notification badges (digital overwhelm)"]
            },
            "meeting_exhaustion": {
                "scenes": ["zoom_fatigue_altar", "calendar_graveyard", "boardroom_mortality"],
                "props": ["expired calendar entries (mortality)", "coffee ring stains (time passing)"]
            },
            "digital_overwhelm": {
                "scenes": ["inbox_zen", "desk_shrine", "floating_workspace"],
                "props": ["unread notification badges (digital overwhelm)", 
                         "empty inbox zero screenshot (false achievement)"]
            },
            "burnout": {
                "scenes": ["burnout_still_life", "zoom_fatigue_altar", "sacred_mundane"],
                "props": ["dying succulent (corporate life)", "half-written resignation letter"]
            },
            "time_pressure": {
                "scenes": ["time_death", "calendar_graveyard", "coffee_ring_mandala"],
                "props": ["expired calendar entries (mortality)", "performance review document"]
            },
            "humanity_seeking": {
                "scenes": ["sacred_mundane", "desk_shrine", "floating_workspace"],
                "props": ["motivational poster (ironic)", "dying succulent (corporate life)"]
            }
        }
        
        if use_mood_matching and mood in mood_mappings:
            mapping = mood_mappings[mood]
            scene_key = random.choice(mapping["scenes"])
            scene_category = self.scene_categories.get(scene_key, "")
            prop = random.choice(mapping["props"])
        else:
            scene_key = random.choice(list(self.scene_categories.keys()))
            scene_category = self.scene_categories[scene_key]
            prop = random.choice(self.symbolic_props)
        
        return {
            "scene_key": scene_key,
            "scene_category": scene_category,
            "prop": prop,
            "lighting": random.choice(self.lighting_options),
            "aesthetic": random.choice(self.aesthetic_references),
            "background": random.choice(self.background_options),
            "composition": random.choice(self.composition_styles),
            "camera_angle": random.choice(self.camera_angles),
            "texture": random.choice(self.texture_elements),
            "color_mood": random.choice(self.color_moods)
        }
    
    async def _create_image_prompt(self, post: LinkedInPost, elements: Dict[str, Any]) -> str:
        """Create a detailed image prompt using AI"""
        
        product_desc = self._get_product_description()
        
        prompt = f"""Create a detailed image prompt for Jesse A. Eisenbalm product photography.

POST CONTENT CONTEXT:
{post.content[:300]}

{product_desc}

UNIQUE VISUAL DIRECTION FOR THIS IMAGE:

SCENE: {elements['scene_category']}

COMPOSITION: {elements['composition']}

CAMERA ANGLE: {elements['camera_angle']}

BACKGROUND: {elements['background']}

LIGHTING: {elements['lighting']}

TEXTURE: {elements['texture']}

COLOR MOOD: {elements['color_mood']}

AESTHETIC REFERENCE: {elements['aesthetic']}

SYMBOLIC PROP: {elements['prop']}

Generate a DETAILED image prompt (150-200 words) for professional product photography that captures:
1. Exact setting with psychological weight
2. Product positioned using the specified composition and camera angle
3. Specific lighting quality and emotional impact
4. Background that enhances without distracting
5. The cognitive dissonance of luxury mortality

Remember: "What if Apple sold mortality?" Clean, expensive, but something is subtly wrong."""

        try:
            result = await self.generate(prompt)
            content = result.get("content", "")
            
            if isinstance(content, dict):
                content = content.get("image_prompt", str(content))
            
            if content and len(str(content)) > 100:
                return str(content)
            else:
                return self._create_fallback_prompt(elements)
                
        except Exception as e:
            self.logger.warning(f"AI prompt generation failed: {e}, using fallback")
            return self._create_fallback_prompt(elements)
    
    def _create_fallback_prompt(self, elements: Dict[str, Any]) -> str:
        """Create a branded fallback prompt"""
        
        product_desc = self._get_product_description()
        
        return f"""Professional product photograph of Jesse A. Eisenbalm premium lip balm tube.

{product_desc}

SCENE: {elements['scene_category']}

COMPOSITION: {elements['composition']}

CAMERA ANGLE: {elements['camera_angle']}

BACKGROUND: {elements['background']}

PRODUCT PLACEMENT: Jesse A. Eisenbalm tube positioned as the hero object. {elements['prop']} visible in scene, creating narrative tension.

LIGHTING: {elements['lighting']}. Soft shadows creating depth. Subtle vignette drawing eye to product.

TEXTURE: {elements['texture']}. Subtle lip balm smear creating visual interest.

COLOR GRADING: {elements['color_mood']}

MOOD: The exact feeling between "everything is fine" and "nothing is fine." Professional corporate aesthetic with subtle existential undertones.

STYLE: {elements['aesthetic']}. Clean lines, minimal but loaded with meaning.

TECHNICAL: 8K, ultra-detailed, commercial photography, professional studio quality, subtle depth of field.

EMOTIONAL TONE: Calm surface tension. Expensive but honest. "What if Apple sold mortality?"

CRITICAL: Product tube MUST match the exact specification - cream/ivory tube, white ribbed cap, vertical black "JESSE A. EISENBALM" text, gold honeycomb pattern with photos of Jesse."""
    
    def _enhance_prompt_with_brand_language(self, prompt: str) -> str:
        """Enhance prompt with Jesse's visual language"""
        
        product_description = self._get_product_description()
        
        # Check if essential elements are present
        has_product_spec = "PRODUCT SPECIFICATION" in prompt
        has_colors = any(color in prompt.lower() for color in ['navy', 'gold', 'cream'])
        has_mood = any(term in prompt.lower() for term in ['mortality', 'existential', 'corporate'])
        
        enhancements = []
        
        if not has_product_spec:
            enhancements.append(f"ACTUAL PRODUCT SPECIFICATION:\n{product_description}")
        
        if not has_colors:
            enhancements.append("Color palette: deep navy blue, rich gold accents, soft cream tones")
        
        if not has_mood:
            enhancements.append("Visual philosophy: what if Apple sold mortality? - clean, minimal, expensive with subtle wrongness")
        
        # Always add technical quality
        quality_specs = [
            "8K resolution, ultra-detailed",
            "Professional commercial photography",
            "Sophisticated color grading",
            "Premium studio lighting",
            "Sharp focus with professional depth of field"
        ]
        
        enhanced = prompt
        
        if enhancements:
            enhanced += "\n\nBRAND ESSENTIALS:\n" + "\n".join(enhancements)
        
        enhanced += "\n\nTECHNICAL SPECIFICATIONS:\n" + "\n".join(quality_specs)
        
        enhanced += "\n\nCRITICAL: The Jesse A. Eisenbalm product tube MUST look exactly as specified - cream/ivory color, white ribbed cap, vertical black 'JESSE A. EISENBALM' text, gold honeycomb pattern with photos of Jesse."
        
        return enhanced
    
    def _save_image(self, image_data: bytes, post: LinkedInPost) -> Optional[str]:
        """Save the generated image to file"""
        try:
            from PIL import Image
            from io import BytesIO
            
            filename = f"jesse_{post.batch_id[:8]}_{post.post_number}_{uuid.uuid4().hex[:8]}.png"
            filepath = self.output_dir / filename
            
            image = Image.open(BytesIO(image_data))
            image.save(filepath, format='PNG')
            
            self.logger.info(f"Jesse A. Eisenbalm image saved: {filepath}")
            
            # Return actual filesystem path (will be converted to URL when serving)
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Failed to save image: {e}")
            return None
    
    def _save_video(self, video_data: bytes, post: LinkedInPost) -> Optional[str]:
        """Save the generated video to file"""
        try:
            # Create videos subdirectory
            video_dir = self.output_dir / "videos"
            video_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"jesse_{post.batch_id[:8]}_{post.post_number}_{uuid.uuid4().hex[:8]}.mp4"
            filepath = video_dir / filename
            
            # Write video bytes directly
            with open(filepath, 'wb') as f:
                f.write(video_data)
            
            self.logger.info(f"Jesse A. Eisenbalm video saved: {filepath}")
            
            # Return actual filesystem path
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Failed to save video: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            "agent_name": self.name,
            "visual_philosophy": "what if Apple sold mortality?",
            "total_unique_combinations": f"{self.total_combinations:,}",
            "variety_systems": {
                "scene_categories": len(self.scene_categories),
                "lighting_options": len(self.lighting_options),
                "backgrounds": len(self.background_options),
                "compositions": len(self.composition_styles),
                "camera_angles": len(self.camera_angles),
                "textures": len(self.texture_elements),
                "color_moods": len(self.color_moods),
                "aesthetic_refs": len(self.aesthetic_references),
                "symbolic_props": len(self.symbolic_props)
            },
            "intelligent_features": {
                "mood_detection": True,
                "content_aware_selection": True,
                "mood_matching_rate": "70%",
                "surprise_variation_rate": "30%"
            },
            "output_directory": str(self.output_dir)
        }