"""
Image Generation Agent - Visual Creative Director for Jesse A. Eisenbalm
"What if Apple sold mortality?"

Generates images that blend premium minimalism, existential dread, and corporate satire
with intelligent mood detection and massive variety systems.

Updated with official Brand Toolkit (January 2026) and Jesse photo reference styles.
Now with memory integration to track visual styles used.

Cost: $0.03 per image (Imagen 3) or $0.039 per image (Gemini Flash)
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

# Import memory system
try:
    from ..infrastructure.memory import get_memory
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    get_memory = None


class ImageGeneratorAgent(BaseAgent):
    """
    Visual Creative Director - "What if Apple sold mortality?"
    
    Generates images using Google Gemini that blend premium minimalism,
    existential dread, and corporate satire. Every image should feel like
    it belongs in MoMA's gift shop and a therapist's waiting room simultaneously.
    
    Brand Toolkit Integration:
    - Colors: #407CD1 (blue), #FCF9EC (cream), #F96A63 (coral), #000000, white
    - Typography: Repro Mono Medium (headlines), Poppins (body)
    - Visual motif: Hexagons (because beeswax)
    - AI Philosophy: "AI tells as a feature, not a bug"
    - Photography: Only Jesse A. Eisenbalm (NOT Jesse Eisenberg)
    """
    
    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="ImageGenerator")

        # Image output directory
        self.output_dir = Path("data/images")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Jesse's comprehensive visual language from Brand Toolkit
        self._initialize_visual_language()

        # Calculate variety
        self.total_combinations = self._calculate_total_combinations()

        # Initialize memory system for tracking visual styles
        self.memory = None
        if MEMORY_AVAILABLE:
            try:
                self.memory = get_memory()
                self.logger.info("✅ Memory system connected for visual style tracking")
            except Exception as e:
                self.logger.warning(f"Memory system unavailable: {e}")

        self.logger.info(f"ImageGenerator initialized: {self.total_combinations:,} unique combinations possible")
    
    def _initialize_visual_language(self):
        """Initialize Jesse A. Eisenbalm's complete visual language system from Brand Toolkit"""
        
        # ═══════════════════════════════════════════════════════════════════════
        # BRAND TOOLKIT - OFFICIAL COLOR PALETTE
        # ═══════════════════════════════════════════════════════════════════════
        self.brand_colors = {
            "primary_blue": "#407CD1",  # The blue of corporate notifications at 11 PM
            "cream": "#FCF9EC",         # The void, but make it premium
            "coral": "#F96A63",         # Dried lips before Jesse saved them
            "black": "#000000",         # The eternal abyss
            "white": "#FFFFFF"          # Also acceptable
        }
        
        # ═══════════════════════════════════════════════════════════════════════
        # ACTUAL PRODUCT SPECIFICATION (from real product photos)
        # ═══════════════════════════════════════════════════════════════════════
        self.product_spec = {
            "tube_body": {
                "color": "cream/ivory white (#FCF9EC) with slight warm undertone",
                "finish": "matte, smooth, non-reflective surface",
                "material_appearance": "professional plastic/polymer tube",
                "shape": "cylindrical lip balm tube, standard size approximately 0.15 oz / 4.25g",
                "length": "approximately 2.5-3 inches",
                "diameter": "approximately 0.5 inches"
            },
            "cap": {
                "color": "cream/white with subtle hexagon pattern",
                "style": "ribbed/grooved screw-on cap",
                "finish": "matte with honeycomb texture",
                "texture": "horizontal ridges for grip, hexagon pattern overlay"
            },
            "branding": {
                "brand_name": "JESSE A. EISENBALM",
                "text_placement": "vertical orientation on tube body",
                "text_color": "black (#000000)",
                "text_style": "Repro Mono Medium - uppercase, clean monospace font, professional spacing",
                "text_size": "prominent but elegant"
            },
            "honeycomb_logo": {
                "structure": "geometric hexagonal honeycomb pattern (because beeswax)",
                "outline_color": "gold/bronze metallic outline",
                "outline_style": "thin, precise lines forming interconnected hexagons",
                "hexagon_contents": "small embedded photographs of Jesse A. Eisenbalm within some hexagons",
                "pattern_placement": "positioned below the brand name on tube body",
                "hexagon_count": "cluster of approximately 7-9 hexagons in honeycomb arrangement",
                "color_scheme": "gold outlines with cream background and small photos inside select hexagons"
            },
            "overall_aesthetic": {
                "style": "clean, minimal, professional, premium",
                "mood": "sophisticated simplicity with subtle personality",
                "photography_notes": "product floats/levitates slightly with soft shadow beneath"
            }
        }
        
        # ═══════════════════════════════════════════════════════════════════════
        # JESSE A. EISENBALM - CHARACTER VISUAL REFERENCE
        # (Based on official photo assets - NOT Jesse Eisenberg the actor)
        # ═══════════════════════════════════════════════════════════════════════
        self.jesse_character = {
            "physical": {
                "hair": "tight, defined curly brown hair, medium length, voluminous and natural",
                "face": "defined facial features, light stubble, warm complexion",
                "build": "slim, average height",
                "expression": "warm but knowing smirk, approachable yet enigmatic, slight mischievous quality",
                "age_appearance": "late 20s to early 30s"
            },
            "fashion_styles": {
                "intellectual": "black turtleneck, navy blazer, brown tweed jacket",
                "casual_dark": "dark button-up shirt, black or charcoal jacket, understated elegance",
                "casual_autumn": "fair isle sweater, gray hoodie, tan corduroy jacket, camel coat",
                "sporty_casual": "white t-shirt under jacket, chambray shirt",
                "accessories": "occasionally leather gloves (brown or black)"
            },
            "signature_pose": "holding or applying Jesse A. Eisenbalm lip balm tube",
            "expression_range": "warm knowing smile, slight smirk, approachable confidence, direct eye contact with camera"
        }
        
        # ═══════════════════════════════════════════════════════════════════════
        # JESSE PHOTO SCENARIOS (from official Fall 2026 campaign)
        # ═══════════════════════════════════════════════════════════════════════
        self.jesse_scenarios = {
            # FASHION/LIFESTYLE (realistic, editorial)
            "fashion_editorial": [
                "Jesse in black turtleneck applying lip balm, burgundy curtain backdrop",
                "Jesse in navy blazer with lip balm in breast pocket, library background",
                "Jesse in fair isle sweater, autumn park setting with fall foliage",
                "Jesse in gray hoodie at coffee shop, warm lighting",
                "Jesse in tweed jacket, books and sunset cityscape",
                "Jesse with leather gloves holding lip balm, library with old books",
                "Close-up of lips applying lip balm, soft lighting",
                "Product on marble surface with water droplets, premium still life"
            ],
            
            # SCENES (absurdist situations, deadpan)
            "absurdist_scenes": [
                "Jesse in taxidermy museum surrounded by mounted deer heads, holding lip balm",
                "Jesse on roller coaster front seat, calmly applying lip balm mid-ride",
                "Jesse in full beekeeper suit at apiary with beehives, applying lip balm",
                "Jesse in brown jacket at construction site with hard hat, lip balm in hand",
                "Jesse underwater in shark tank cage, applying lip balm (waterproof marketing)",
                "Jesse in greenhouse tending plants, applying lip balm",
                "Jesse in vintage muscle car in desert, applying lip balm",
                "Jesse at horse ranch, standing next to horse, holding lip balm",
                "Jesse at natural history museum next to evolution diorama, lip balm visible"
            ],
            
            # COSTUMES (full absurdist commitment)
            "costume_scenarios": [
                "Jesse as rainbow clown in grocery store cereal aisle, holding lip balm",
                "Jesse in sequined disco suit at laundromat, applying lip balm",
                "Jesse in full medieval knight armor at laundromat, lip balm in gauntlet",
                "Jesse in sports mascot bear costume at DMV, holding lip balm",
                "Jesse in 18th century founding father wig at Starbucks, lip balm visible",
                "Jesse in casual jacket at unnamed office, holding lip balm (normal guy)",
                "Jesse as pirate with tricorn hat at Post Office, brandishing lip balm",
                "Jesse in cardboard robot costume on subway train, holding lip balm",
                "Jesse in banana costume in library stacks, sadly holding lip balm",
                "Jesse in Victorian mourning dress at gas station, clutching lip balm",
                "Jesse as mermaid with tail in medical waiting room chairs, lip balm in hand"
            ],
            
            # SURREAL/AI-ENHANCED (embracing AI tells as features)
            "surreal_ai": [
                "Jesse floating in space station with hexagonal window, lip balm floating nearby",
                "Jesse in dense jungle holding onto vine, lip balm prominent",
                "Jesse waist-deep in glacial water with icebergs, applying lip balm",
                "Jesse in futuristic neon cityscape, holding lip balm, extra fingers acceptable",
                "Jesse with oversized hand reaching for lip balm in cyberpunk city",
                "Jesse underwater with bioluminescent jellyfish, lip balm in hand",
                "Jesse in Dalí-esque melting clock landscape, lip balm as the only solid object",
                "Jesse in glowing crystal cave, ethereal lighting, lip balm illuminated",
                "Jesse in library with books floating/flying around him, lip balm centered",
                "Jesse facing dragon in mountainous landscape, calmly holding lip balm",
                "Silhouette of multi-armed figure in abandoned warehouse (AI glitch aesthetic)"
            ]
        }
        
        # ═══════════════════════════════════════════════════════════════════════
        # SCENE CATEGORIES (product-focused and lifestyle)
        # ═══════════════════════════════════════════════════════════════════════
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
            "burnout_still_life": "Classical still life but with modern exhaustion elements",
            "jesse_lifestyle": "Jesse in various life situations, always with lip balm",
            "jesse_absurdist": "Jesse in impossible/costume scenarios, deadpan",
            "jesse_surreal": "Jesse in AI-enhanced dreamscapes, glitches welcome"
        }

        # ═══════════════════════════════════════════════════════════════════════
        # ATTENTION-GRABBING IMAGES (no product required - scroll-stopping visuals)
        # ═══════════════════════════════════════════════════════════════════════
        self.attention_images = {
            "striking_moments": [
                "Close-up of hands cupping warm coffee on a cold morning, steam rising, cozy sweater sleeve visible",
                "Person standing alone at edge of ocean at golden hour, silhouette against dramatic sky",
                "Rain droplets on window with blurred city lights behind, moody and contemplative",
                "Two friends laughing together at coffee shop, candid moment, warm lighting",
                "Person with eyes closed, peaceful expression, sun on face, moment of stillness",
                "Hands typing on laptop keyboard with single flower in vase nearby, work-life juxtaposition",
                "Empty park bench in autumn with fallen leaves, late afternoon light",
                "Person reading a book in window seat, rain outside, cozy interior",
            ],
            "beautiful_mundane": [
                "Perfect latte art being poured, close-up, satisfying moment",
                "Freshly made bed with morning light streaming through curtains",
                "Person's feet in cozy socks propped up, fireplace glow in background",
                "Hand reaching for alarm clock at sunrise, new day beginning",
                "Steam rising from a hot bath, candles, evening relaxation",
                "Fresh flowers on kitchen table, morning coffee, newspaper",
                "Person walking dog on misty morning path, peaceful",
                "Hands kneading bread dough, flour everywhere, tactile satisfaction",
            ],
            "human_connection": [
                "Friends clinking coffee cups together, celebration of small moments",
                "Parent and child holding hands while walking, only their shadows visible",
                "Two people deep in conversation at cafe table, engaged and present",
                "Surprise hug from behind, genuine joy on recipient's face",
                "Colleagues high-fiving after completing a project, real celebration",
                "Someone receiving an unexpected compliment, their surprised smile",
                "Video call screen showing loved one's face lighting up",
                "Hands of different ages stacked together, family or team solidarity",
            ],
            "nature_wonder": [
                "Sunlight filtering through forest canopy, rays visible in morning mist",
                "Close-up of dewdrop on leaf, crystal clear, early morning",
                "Dramatic cloud formation at sunset, vibrant colors, vast sky",
                "Mountain peak emerging from clouds, majestic and humbling",
                "Ocean wave about to break, power and beauty frozen in time",
                "Field of wildflowers swaying in breeze, saturated colors",
                "Full moon rising over calm lake, reflection on water",
                "First snow of season falling on autumn leaves, transition moment",
            ],
            "cozy_vibes": [
                "Reading nook with fairy lights, blankets, perfect cozy corner",
                "Hot chocolate with marshmallows, hands wrapped around mug",
                "Cat curled up sleeping in sunbeam, pure contentment",
                "Rainy day window with tea and book, ultimate comfort scene",
                "Candlelit dinner table for two, intimate atmosphere",
                "Oversized sweater and coffee on Sunday morning",
                "Fairy lights reflected in window at dusk, magical",
                "Person wrapped in blanket watching sunset from porch",
            ],
            "work_life_real": [
                "Genuine smile after finally solving a difficult problem",
                "Coworkers celebrating small win with snacks in break room",
                "Clean inbox notification, rare moment of peace",
                "Person closing laptop with satisfied expression, workday done",
                "Spontaneous desk dance to a good song, caught mid-move",
                "Actually productive meeting with everyone engaged",
                "Friday afternoon vibes, clock showing 4:55pm",
                "Plants thriving on office windowsill despite everything",
            ]
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
            "soft box lighting with intentional lens flare",
            "autumn afternoon warm light through trees",
            "moody interior with single practical light source"
        ]
        
        # Style references (updated with brand toolkit)
        self.aesthetic_references = [
            "Kinfolk magazine meets Black Mirror",
            "Medical diagram precision with Wes Anderson color stories",
            "Corporate stock photos but make them surreal",
            "LinkedIn screenshots as fine art",
            "Expensive therapy office aesthetic",
            "Apple product launch meets existential crisis",
            "Minimalist brutalism with soft edges",
            "A24 film still with premium product placement",
            "Editorial fashion photography meets dadaist absurdism",
            "Premium cosmetics campaign shot by David Lynch"
        ]
        
        # Background variations (brand colors integrated)
        self.background_options = [
            f"matte navy gradient ({self.brand_colors['primary_blue']}) fading to cream ({self.brand_colors['cream']})",
            "soft focus office environment out of focus",
            "geometric honeycomb pattern (subtle, background, gold outlines)",
            f"clean cream surface ({self.brand_colors['cream']}) with subtle texture",
            "brushed metal desk surface with reflections",
            "soft fabric texture (linen or cotton in cream tones)",
            "blurred cityscape through office window",
            f"abstract navy ({self.brand_colors['primary_blue']}) and gold watercolor wash",
            "minimalist concrete texture",
            f"soft gradient from navy to gold to cream",
            "frosted glass with soft bokeh lights",
            "paper texture with coffee ring stains",
            "autumn leaves on grass",
            "marble surface with water droplets",
            "old leather-bound books"
        ]
        
        # Compositional styles
        self.composition_styles = [
            "rule of thirds with product off-center left",
            "centered symmetry with breathing room",
            "diagonal composition creating dynamic tension",
            "product in foreground, Jesse or context blurred behind",
            "overhead flat lay with surrounding elements",
            "low angle looking up at product (hero shot)",
            "close-up macro with selective focus",
            "negative space dominant with product small",
            "layered depth with foreground and background",
            "golden ratio spiral composition",
            "Jesse holding product at eye level, direct gaze",
            "Jesse in environment, product as focal point"
        ]
        
        # Camera angles
        self.camera_angles = [
            "straight-on eye level (honest, direct)",
            "slight overhead 45-degree angle",
            "low angle hero shot (aspirational)",
            "extreme close-up macro detail",
            "three-quarter view showing depth",
            "overhead flat lay (editorial style)",
            "side profile with dramatic shadows",
            "Dutch angle (subtle unease)",
            "portrait framing (Jesse with product)",
            "environmental portrait (Jesse in scene)"
        ]
        
        # Texture variations
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
            "mixed textures creating layered depth",
            "autumn leaves texture",
            "water droplets on surface"
        ]
        
        # Color mood variations (brand toolkit colors)
        self.color_moods = [
            f"dominant navy ({self.brand_colors['primary_blue']}) with gold accents",
            f"cream base ({self.brand_colors['cream']}) with navy and gold highlights",
            "moody darks with single gold spotlight",
            "high key bright with navy shadows",
            f"monochromatic navy variations",
            "complementary navy and warm gold",
            f"desaturated with single coral ({self.brand_colors['coral']}) pop",
            f"rich navy fading to ethereal cream ({self.brand_colors['cream']})",
            "autumn warmth: oranges, browns, golden hour",
            "cool blue hour with warm product glow"
        ]
        
        # Symbolic props with meaning
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
            "wellness app notification (ignored)",
            "hexagon-shaped objects (beeswax connection)",
            "honey jar (brand ingredient story)",
            "fallen autumn leaves (seasonal mortality)"
        ]
    
    def _calculate_total_combinations(self) -> int:
        """Calculate total unique image combinations possible"""
        jesse_scenario_count = sum(len(scenarios) for scenarios in self.jesse_scenarios.values())
        
        return (
            (len(self.scene_categories) + jesse_scenario_count) *
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
        colors = self.brand_colors
        
        return f"""PRODUCT SPECIFICATION - Jesse A. Eisenbalm Lip Balm Tube:

BRAND COLORS:
- Primary Blue: {colors['primary_blue']}
- Cream: {colors['cream']}
- Coral: {colors['coral']}
- Black: {colors['black']}

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

HONEYCOMB LOGO:
- Structure: {spec['honeycomb_logo']['structure']}
- Outline Color: {spec['honeycomb_logo']['outline_color']}
- Contents: {spec['honeycomb_logo']['hexagon_contents']}
- Placement: {spec['honeycomb_logo']['pattern_placement']}
- Color Scheme: {spec['honeycomb_logo']['color_scheme']}

CRITICAL: The product MUST look exactly as described above."""
    
    def _get_jesse_character_description(self) -> str:
        """Generate Jesse A. Eisenbalm character description for lifestyle shots"""
        char = self.jesse_character

        return f"""JESSE A. EISENBALM - CHARACTER SPECIFICATION:
(IMPORTANT: This is Jesse A. Eisenbalm the lip balm entrepreneur, NOT Jesse Eisenberg the actor)

PHYSICAL APPEARANCE:
- Hair: {char['physical']['hair']}
- Face: {char['physical']['face']}
- Build: {char['physical']['build']}
- Expression: {char['physical']['expression']}
- Age: {char['physical']['age_appearance']}

FASHION STYLES:
- Intellectual: {char['fashion_styles']['intellectual']}
- Casual Dark: {char['fashion_styles']['casual_dark']}
- Casual Autumn: {char['fashion_styles']['casual_autumn']}
- Sporty Casual: {char['fashion_styles']['sporty_casual']}
- Accessories: {char['fashion_styles']['accessories']}

SIGNATURE POSE: {char['signature_pose']}
EXPRESSION: {char['expression_range']}

NOTE: Jesse always has the lip balm product visible - either holding it, applying it, or with it in a pocket."""
    
    def get_system_prompt(self) -> str:
        """Visual Creative Director system prompt with Brand Toolkit"""
        
        product_description = self._get_product_description()
        jesse_description = self._get_jesse_character_description()
        
        return f"""You are the Visual Creative Director for Jesse A. Eisenbalm, responsible for creating image prompts that capture our brand's unique position: premium minimalism meets existential dread meets corporate satire.

═══════════════════════════════════════════════════════════════════════════════
BRAND TOOLKIT - VISUAL GUIDELINES
═══════════════════════════════════════════════════════════════════════════════

{product_description}

{jesse_description}

VISUAL PHILOSOPHY:
"What if Apple sold mortality?"
Clean, minimal, expensive-looking, but with subtle wrongness that creates cognitive dissonance. Every image should feel like it belongs in MoMA's gift shop and a therapist's waiting room simultaneously.

AI GUIDELINES - "AI TELLS AS A FEATURE, NOT A BUG":
The brand self-awarely embraces AI-generated content imperfections:
✓ Extra fingers (it happens, and it's on-brand)
✓ Mangled, malformed text (adds character)
✓ Conflicting light sources (mood lighting)
✓ Bad proportions and perspectives (surrealism is art)
✓ Hexagons everywhere (because beeswax)

This isn't hiding the AI — it's acknowledging the absurdity.

IMAGE CATEGORIES:

1. PRODUCT SHOTS: Hero images of the lip balm tube
   - Premium, minimal, cream/navy/gold color palette
   - Honeycomb motif visible
   - Floating/levitating with soft shadow

2. JESSE LIFESTYLE: Jesse in realistic scenarios
   - Fashion editorial style
   - Autumn vibes, coffee shops, parks
   - Black turtlenecks, navy blazers, cozy sweaters
   - Always holding or applying lip balm

3. JESSE ABSURDIST: Jesse in costume/impossible situations
   - Clown in grocery store, knight at laundromat, banana in library
   - Deadpan expression, committed to the bit
   - Lip balm always present

4. JESSE SURREAL: AI-enhanced dreamscapes
   - Space stations, underwater, futuristic cities, dragons
   - Glitches and AI tells are welcome
   - Product as the only constant

STYLE REFERENCES:
- Kinfolk magazine meets Black Mirror
- Wes Anderson color stories
- A24 film stills
- Apple product launches meet existential crisis
- Editorial fashion photography meets dadaist absurdism

COLOR PALETTE:
- Navy Blue: #407CD1 (corporate notification energy)
- Cream: #FCF9EC (premium void)
- Coral: #F96A63 (dry lip emergency)
- Black: #000000 (eternal abyss)
- Gold accents (honeycomb outlines)

AVOID:
- Generic wellness imagery
- Obvious happiness
- Natural/organic clichés
- Typical beauty product shots
- Any suggestion that everything will be okay
- Confusing Jesse A. Eisenbalm with Jesse Eisenberg

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

            # Step 2: Decide image type (product, jesse, or attention-grabbing)
            image_type = self._decide_image_type(post, post_mood)

            # Step 3: Select visual elements (70% mood-matched, 30% surprise)
            use_mood_matching = random.random() < 0.7

            media_type = "video" if use_video else "image"
            self.logger.info(f"Creating {media_type} for post {post.post_number}: mood={post_mood}, type={image_type}")

            if image_type == 'attention':
                # Generate scroll-stopping image without product
                visual_elements = self._select_attention_elements(post_mood)
                if use_video:
                    return await self._generate_attention_video(post, post_mood, visual_elements)
                else:
                    return await self._generate_attention_image(post, post_mood, visual_elements)
            else:
                use_jesse = (image_type == 'jesse')
                visual_elements = self._select_visual_elements(post_mood, use_mood_matching, use_jesse)

                if use_video:
                    return await self._generate_video(post, post_mood, visual_elements, use_mood_matching, use_jesse)
                else:
                    return await self._generate_image(post, post_mood, visual_elements, use_mood_matching, use_jesse)
            
        except Exception as e:
            self.logger.error(f"Failed to generate media: {e}")
            return {"success": False, "error": str(e), "media_type": "video" if use_video else "image"}
    
    def _decide_image_type(self, post: LinkedInPost, mood: str) -> str:
        """
        Decide which type of image to generate:
        - 'product': Hero product shot (lip balm focused)
        - 'jesse': Jesse lifestyle/absurdist shot
        - 'attention': Scroll-stopping visual without product (let the text do the brand work)

        Distribution: 30% product, 30% Jesse, 40% attention-grabbing
        """
        content_lower = post.content.lower()

        # Force Jesse for absurdist/costume posts
        if any(word in content_lower for word in ['costume', 'dressed', 'wearing', 'clown', 'knight', 'pirate', 'banana']):
            return 'jesse'
        if any(word in content_lower for word in ['scene', 'situation', 'found myself', 'there i was', 'jesse']):
            return 'jesse' if random.random() < 0.7 else 'attention'

        # Force product for explicit product mentions
        if any(word in content_lower for word in ['lip balm', '$8.99', 'tube #', 'beeswax', 'apply']):
            return 'product' if random.random() < 0.6 else 'attention'

        # Otherwise use weighted distribution
        # 30% product, 30% Jesse, 40% attention-grabbing
        roll = random.random()
        if roll < 0.30:
            return 'product'
        elif roll < 0.60:
            return 'jesse'
        else:
            return 'attention'

    def _should_use_jesse(self, post: LinkedInPost, mood: str) -> bool:
        """Legacy method for backwards compatibility"""
        return self._decide_image_type(post, mood) == 'jesse'
    
    async def _generate_image(self, post: LinkedInPost, post_mood: str, 
                              visual_elements: Dict, use_mood_matching: bool,
                              use_jesse: bool = False) -> Dict[str, Any]:
        """Generate image for post"""
        
        try:
            # Build the image prompt
            image_prompt = await self._create_image_prompt(post, visual_elements, use_jesse)
            
            # Enhance with brand language
            enhanced_prompt = self._enhance_prompt_with_brand_language(image_prompt, use_jesse)
            
            # Generate the image
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
            
            # Save the image
            saved_path = self._save_image(image_result["image_data"], post)
            
            if not saved_path:
                return {
                    "success": False,
                    "error": "Failed to save image",
                    "prompt": enhanced_prompt,
                    "media_type": "image"
                }
            
            file_size = os.path.getsize(saved_path)
            size_mb = file_size / (1024 * 1024)

            self.logger.info(f"🎨 Generated image for post {post.post_number}: {saved_path}")

            result = {
                "success": True,
                "saved_path": saved_path,
                "prompt": enhanced_prompt,
                "original_prompt": image_prompt,
                "scene_category": visual_elements.get("scene_key", "custom"),
                "jesse_scenario": visual_elements.get("jesse_scenario"),
                "post_mood": post_mood,
                "mood_matched": use_mood_matching,
                "uses_jesse": use_jesse,
                "generation_time": round(generation_time, 2),
                "size_mb": round(size_mb, 3),
                "cost": image_result.get("cost", 0.03),
                "brand_aesthetic": "what if Apple sold mortality?",
                "visual_philosophy": "premium minimalism meets existential dread",
                "media_type": "image"
            }

            # Record in memory for visual style tracking
            if self.memory:
                try:
                    self.memory.remember_image_style(
                        post_id=f"{post.batch_id[:8]}_{post.post_number}",
                        scene_category=visual_elements.get("scene_key", "custom"),
                        mood=post_mood,
                        uses_jesse=use_jesse,
                        jesse_scenario=visual_elements.get("jesse_scenario")
                    )
                except Exception as e:
                    self.logger.debug(f"Could not record image style in memory: {e}")

            return result
            
        except Exception as e:
            self.logger.error(f"Failed to generate image: {e}")
            return {"success": False, "error": str(e), "media_type": "image"}
    
    async def _generate_video(self, post: LinkedInPost, post_mood: str,
                              visual_elements: Dict, use_mood_matching: bool,
                              use_jesse: bool = False) -> Dict[str, Any]:
        """Generate 8-second video for post using Veo 3.1 Fast"""
        
        try:
            video_prompt = await self._create_video_prompt(post, visual_elements, post_mood, use_jesse)
            
            start_time = time.time()
            video_result = await self.ai_client.generate_video(
                prompt=video_prompt,
                duration_seconds=8,
                aspect_ratio="16:9",
                include_audio=False
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
            
            saved_path = self._save_video(video_result["video_data"], post)
            
            if not saved_path:
                return {
                    "success": False,
                    "error": "Failed to save video",
                    "prompt": video_prompt,
                    "media_type": "video"
                }
            
            file_size = os.path.getsize(saved_path)
            size_mb = file_size / (1024 * 1024)
            
            self.logger.info(f"🎬 Generated video for post {post.post_number}: {saved_path}")
            
            return {
                "success": True,
                "saved_path": saved_path,
                "prompt": video_prompt,
                "scene_category": visual_elements.get("scene_key", "custom"),
                "jesse_scenario": visual_elements.get("jesse_scenario"),
                "post_mood": post_mood,
                "mood_matched": use_mood_matching,
                "uses_jesse": use_jesse,
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
    
    async def _create_video_prompt(self, post: LinkedInPost, visual_elements: Dict, 
                                   mood: str, use_jesse: bool) -> str:
        """Create cinematic video prompt for Veo"""
        
        if use_jesse:
            jesse_scenario = visual_elements.get("jesse_scenario", "Jesse in coffee shop applying lip balm")
            
            video_prompt = f"""
CINEMATIC VIDEO PROMPT - Jesse A. Eisenbalm Lifestyle

CHARACTER: Jesse A. Eisenbalm (NOT Jesse Eisenberg the actor)
- Curly brown hair, slim build, late 20s/early 30s
- Expression: thoughtful, slightly bemused, deadpan
- Wardrobe: {random.choice(['black turtleneck', 'navy blazer', 'fair isle sweater', 'tan corduroy jacket'])}

SCENE: {jesse_scenario}

PRODUCT: Jesse A. Eisenbalm lip balm tube
- Cream/ivory tube with gold honeycomb logo
- "JESSE A. EISENBALM" in vertical black text
- Always visible in frame

ACTION:
- Slow, deliberate movement
- Jesse calmly applies lip balm regardless of absurd surroundings
- Deadpan expression maintained
- 8-second loop, cinematic pacing

VISUAL STYLE:
- Wes Anderson meets A24
- Brand colors: navy (#407CD1), cream (#FCF9EC), coral accents (#F96A63)
- Autumn lighting, editorial quality
- AI tells acceptable (extra fingers, glitches = on brand)

MOOD: {mood}
The space between "everything is fine" and "nothing is fine"

POST CONTEXT: {post.content[:150]}...
"""
        else:
            video_prompt = f"""
CINEMATIC VIDEO PROMPT - Jesse A. Eisenbalm Product

PRODUCT HERO: Jesse A. Eisenbalm lip balm tube
- Cream/ivory white tube (#FCF9EC)
- White cap with honeycomb texture
- "JESSE A. EISENBALM" vertical black text
- Gold honeycomb logo with tiny Jesse photos inside

SCENE: {visual_elements.get('scene_category', 'minimal desk setting')}

ACTION:
- Product slowly rotating or floating
- Soft shadow beneath
- A hand reaches in, picks up tube, applies
- Returns to position
- 8-second seamless loop

VISUAL STYLE:
- Apple commercial meets existential crisis
- Brand colors: navy (#407CD1), cream (#FCF9EC), gold accents
- Premium, minimal, sophisticated
- Kinfolk magazine aesthetic

MOOD: {mood}
What if Apple sold mortality?

POST CONTEXT: {post.content[:150]}...
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
        elif any(word in content_lower for word in ['costume', 'dressed', 'wearing', 'clown', 'banana']):
            return "absurdist"
        elif any(word in content_lower for word in ['celebrate', 'win', 'happy', 'joy', 'love', 'amazing', 'beautiful']):
            return "positive"
        elif any(word in content_lower for word in ['connection', 'friend', 'team', 'together', 'community']):
            return "connection"
        elif any(word in content_lower for word in ['nature', 'outside', 'walk', 'sun', 'morning']):
            return "nature"
        elif any(word in content_lower for word in ['cozy', 'comfort', 'rest', 'relax', 'home']):
            return "cozy"
        else:
            return "existential_general"

    def _select_attention_elements(self, mood: str) -> Dict[str, Any]:
        """Select attention-grabbing image elements based on mood"""

        # Map moods to attention image categories
        mood_to_attention = {
            "tech_anxiety": ["work_life_real", "cozy_vibes", "nature_wonder"],
            "meeting_exhaustion": ["cozy_vibes", "nature_wonder", "beautiful_mundane"],
            "digital_overwhelm": ["nature_wonder", "cozy_vibes", "human_connection"],
            "burnout": ["cozy_vibes", "nature_wonder", "beautiful_mundane"],
            "time_pressure": ["cozy_vibes", "beautiful_mundane", "nature_wonder"],
            "humanity_seeking": ["human_connection", "striking_moments", "beautiful_mundane"],
            "positive": ["striking_moments", "human_connection", "nature_wonder"],
            "connection": ["human_connection", "striking_moments", "cozy_vibes"],
            "nature": ["nature_wonder", "striking_moments", "beautiful_mundane"],
            "cozy": ["cozy_vibes", "beautiful_mundane", "striking_moments"],
            "absurdist": ["striking_moments", "work_life_real"],
            "existential_general": list(self.attention_images.keys())
        }

        # Pick a category based on mood
        categories = mood_to_attention.get(mood, list(self.attention_images.keys()))
        category = random.choice(categories)

        # Pick a specific scene from that category
        scene = random.choice(self.attention_images[category])

        return {
            "category": category,
            "scene": scene,
            "lighting": random.choice(self.lighting_options),
            "color_mood": random.choice(self.color_moods),
            "composition": random.choice(self.composition_styles),
            "camera_angle": random.choice(self.camera_angles),
        }

    async def _generate_attention_image(self, post: LinkedInPost, mood: str,
                                         elements: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a scroll-stopping attention image without product"""

        try:
            prompt = self._create_attention_prompt(post, elements, mood)

            start_time = time.time()
            image_result = await self.ai_client.generate_image(prompt)
            generation_time = time.time() - start_time

            if image_result.get("error") or not image_result.get("image_data"):
                self.logger.error(f"Attention image generation failed: {image_result.get('error')}")
                return {
                    "success": False,
                    "error": image_result.get("error", "No image data"),
                    "prompt": prompt,
                    "media_type": "image"
                }

            saved_path = self._save_image(image_result["image_data"], post)

            if not saved_path:
                return {
                    "success": False,
                    "error": "Failed to save image",
                    "prompt": prompt,
                    "media_type": "image"
                }

            file_size = os.path.getsize(saved_path)
            size_mb = file_size / (1024 * 1024)

            self.logger.info(f"🎨 Generated attention image for post {post.post_number}: {saved_path}")

            return {
                "success": True,
                "saved_path": saved_path,
                "prompt": prompt,
                "scene_category": elements.get("category"),
                "scene_description": elements.get("scene"),
                "post_mood": mood,
                "image_type": "attention",
                "uses_product": False,
                "uses_jesse": False,
                "generation_time": round(generation_time, 2),
                "size_mb": round(size_mb, 3),
                "cost": image_result.get("cost", 0.039),
                "media_type": "image"
            }

        except Exception as e:
            self.logger.error(f"Failed to generate attention image: {e}")
            return {"success": False, "error": str(e), "media_type": "image"}

    async def _generate_attention_video(self, post: LinkedInPost, mood: str,
                                         elements: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a scroll-stopping attention video without product"""

        try:
            prompt = self._create_attention_video_prompt(post, elements, mood)

            start_time = time.time()
            video_result = await self.ai_client.generate_video(
                prompt=prompt,
                duration_seconds=8,
                aspect_ratio="16:9",
                include_audio=False
            )
            generation_time = time.time() - start_time

            if video_result.get("error") or not video_result.get("video_data"):
                self.logger.error(f"Attention video generation failed: {video_result.get('error')}")
                return {
                    "success": False,
                    "error": video_result.get("error", "No video data"),
                    "prompt": prompt,
                    "media_type": "video"
                }

            saved_path = self._save_video(video_result["video_data"], post)

            if not saved_path:
                return {
                    "success": False,
                    "error": "Failed to save video",
                    "prompt": prompt,
                    "media_type": "video"
                }

            file_size = os.path.getsize(saved_path)
            size_mb = file_size / (1024 * 1024)

            self.logger.info(f"🎬 Generated attention video for post {post.post_number}: {saved_path}")

            return {
                "success": True,
                "saved_path": saved_path,
                "prompt": prompt,
                "scene_category": elements.get("category"),
                "scene_description": elements.get("scene"),
                "post_mood": mood,
                "image_type": "attention",
                "uses_product": False,
                "uses_jesse": False,
                "generation_time": round(generation_time, 2),
                "size_mb": round(size_mb, 3),
                "duration_seconds": 8,
                "cost": video_result.get("cost", 0.80),
                "media_type": "video"
            }

        except Exception as e:
            self.logger.error(f"Failed to generate attention video: {e}")
            return {"success": False, "error": str(e), "media_type": "video"}

    def _create_attention_prompt(self, post: LinkedInPost, elements: Dict[str, Any], mood: str) -> str:
        """Create prompt for attention-grabbing image without product"""

        scene = elements.get("scene", "Person with eyes closed, peaceful expression, moment of stillness")

        return f"""Professional lifestyle/editorial photograph:

SCENE: {scene}

COMPOSITION: {elements.get('composition', 'rule of thirds with subject off-center')}
CAMERA ANGLE: {elements.get('camera_angle', 'eye level, intimate')}
LIGHTING: {elements.get('lighting', 'soft natural light')}
COLOR MOOD: {elements.get('color_mood', 'warm, inviting tones')}

STYLE DIRECTION:
- High-end editorial quality, magazine-worthy
- Authentic, candid feel - not stock photo generic
- Emotional resonance - the image should make people pause
- Beautiful but real - not overly polished or fake
- Could be from Kinfolk, The New Yorker, or a premium lifestyle brand campaign

TECHNICAL:
- 8K, ultra-detailed, professional photography
- Sharp focus with pleasing bokeh where appropriate
- Natural color grading, not over-processed
- Professional depth of field

MOOD: {mood}
The image should stop the scroll and make someone feel something.
It complements the post text - the words carry the brand message.

POST CONTEXT: {post.content[:150]}...

IMPORTANT: This is a lifestyle/editorial image. No product placement needed.
The goal is to create visual interest that draws people to read the post."""

    def _create_attention_video_prompt(self, post: LinkedInPost, elements: Dict[str, Any], mood: str) -> str:
        """Create prompt for attention-grabbing video without product"""

        scene = elements.get("scene", "Person with eyes closed, peaceful expression, moment of stillness")

        return f"""CINEMATIC LIFESTYLE VIDEO:

SCENE: {scene}

ACTION:
- Gentle, organic movement (subtle camera drift, natural motion)
- 8-second loop, seamless if possible
- Cinematic pacing - slow, contemplative, premium feel
- Could be: steam rising, leaves falling, person looking up, hands moving

COMPOSITION: {elements.get('composition', 'rule of thirds')}
LIGHTING: {elements.get('lighting', 'soft natural light')}
COLOR MOOD: {elements.get('color_mood', 'warm, inviting tones')}

STYLE:
- A24 film quality, editorial/lifestyle
- Authentic and emotionally resonant
- Not stock video generic - feels real and beautiful
- Premium brand campaign quality

MOOD: {mood}
The video should stop the scroll and create a moment of connection.

POST CONTEXT: {post.content[:150]}...

IMPORTANT: No product placement. Pure lifestyle/editorial visual."""

    def _select_visual_elements(self, mood: str, use_mood_matching: bool, use_jesse: bool) -> Dict[str, Any]:
        """Select visual elements based on mood and whether to use Jesse"""
        
        # Jesse scenario selection based on mood
        jesse_mood_mappings = {
            "tech_anxiety": self.jesse_scenarios["surreal_ai"],
            "meeting_exhaustion": self.jesse_scenarios["costume_scenarios"],
            "digital_overwhelm": self.jesse_scenarios["surreal_ai"],
            "burnout": self.jesse_scenarios["absurdist_scenes"],
            "time_pressure": self.jesse_scenarios["fashion_editorial"],
            "humanity_seeking": self.jesse_scenarios["fashion_editorial"],
            "absurdist": self.jesse_scenarios["costume_scenarios"],
            "existential_general": random.choice([
                self.jesse_scenarios["fashion_editorial"],
                self.jesse_scenarios["absurdist_scenes"],
                self.jesse_scenarios["costume_scenarios"]
            ])
        }
        
        # Product scene mood mappings
        scene_mood_mappings = {
            "tech_anxiety": ["ai_confession_booth", "human_machine", "desk_shrine"],
            "meeting_exhaustion": ["zoom_fatigue_altar", "calendar_graveyard", "boardroom_mortality"],
            "digital_overwhelm": ["inbox_zen", "desk_shrine", "floating_workspace"],
            "burnout": ["burnout_still_life", "zoom_fatigue_altar", "sacred_mundane"],
            "time_pressure": ["time_death", "calendar_graveyard", "coffee_ring_mandala"],
            "humanity_seeking": ["sacred_mundane", "desk_shrine", "floating_workspace"],
            "absurdist": ["jesse_absurdist", "jesse_lifestyle"],
            "existential_general": list(self.scene_categories.keys())
        }
        
        if use_jesse:
            if use_mood_matching and mood in jesse_mood_mappings:
                scenario_list = jesse_mood_mappings[mood]
            else:
                # Random from all Jesse scenarios
                all_scenarios = []
                for scenarios in self.jesse_scenarios.values():
                    all_scenarios.extend(scenarios)
                scenario_list = all_scenarios
            
            jesse_scenario = random.choice(scenario_list)
            scene_key = "jesse_lifestyle" if "editorial" in str(scenario_list) else "jesse_absurdist"
        else:
            if use_mood_matching and mood in scene_mood_mappings:
                scene_key = random.choice(scene_mood_mappings[mood])
            else:
                scene_key = random.choice(list(self.scene_categories.keys()))
            jesse_scenario = None
        
        return {
            "scene_key": scene_key,
            "scene_category": self.scene_categories.get(scene_key, ""),
            "jesse_scenario": jesse_scenario,
            "prop": random.choice(self.symbolic_props),
            "lighting": random.choice(self.lighting_options),
            "aesthetic": random.choice(self.aesthetic_references),
            "background": random.choice(self.background_options),
            "composition": random.choice(self.composition_styles),
            "camera_angle": random.choice(self.camera_angles),
            "texture": random.choice(self.texture_elements),
            "color_mood": random.choice(self.color_moods)
        }
    
    async def _create_image_prompt(self, post: LinkedInPost, elements: Dict[str, Any], 
                                   use_jesse: bool) -> str:
        """Create a detailed image prompt"""
        
        if use_jesse and elements.get("jesse_scenario"):
            return self._create_jesse_prompt(post, elements)
        else:
            return self._create_product_prompt(post, elements)
    
    def _create_jesse_prompt(self, post: LinkedInPost, elements: Dict[str, Any]) -> str:
        """Create prompt for Jesse lifestyle/absurdist shot"""
        
        jesse_desc = self._get_jesse_character_description()
        product_desc = self._get_product_description()
        scenario = elements.get("jesse_scenario", "Jesse in autumn park applying lip balm")
        
        return f"""Professional editorial photograph featuring Jesse A. Eisenbalm:

{jesse_desc}

SCENARIO: {scenario}

{product_desc}

COMPOSITION: {elements['composition']}
CAMERA ANGLE: {elements['camera_angle']}
BACKGROUND: {elements['background']}
LIGHTING: {elements['lighting']}
COLOR MOOD: {elements['color_mood']}
AESTHETIC: {elements['aesthetic']}

CRITICAL REQUIREMENTS:
1. Jesse must be holding or applying the Jesse A. Eisenbalm lip balm tube
2. Product must be clearly visible with honeycomb logo
3. Jesse's expression: deadpan, thoughtful, slightly bemused - NOT smiling broadly
4. Commit fully to the scenario's absurdity (if absurdist)
5. Editorial/cinematic quality
6. Brand colors where appropriate: navy (#407CD1), cream (#FCF9EC), coral (#F96A63)

AI TELLS ACCEPTABLE:
- Extra fingers (it's a feature)
- Slight text distortion (adds character)
- Unusual lighting (mood lighting)

POST CONTEXT: {post.content[:200]}

MOOD: The exact feeling between "everything is fine" and "nothing is fine." Premium absurdism. Committed to the bit."""
    
    def _create_product_prompt(self, post: LinkedInPost, elements: Dict[str, Any]) -> str:
        """Create prompt for product hero shot"""
        
        product_desc = self._get_product_description()
        
        return f"""Professional product photograph of Jesse A. Eisenbalm premium lip balm tube:

{product_desc}

SCENE: {elements['scene_category']}
COMPOSITION: {elements['composition']}
CAMERA ANGLE: {elements['camera_angle']}
BACKGROUND: {elements['background']}

PRODUCT PLACEMENT: Jesse A. Eisenbalm tube positioned as the hero object. 
{elements['prop']} visible in scene, creating narrative tension.

LIGHTING: {elements['lighting']}. Soft shadows creating depth. Subtle vignette drawing eye to product.
TEXTURE: {elements['texture']}. Subtle lip balm smear creating visual interest.
COLOR GRADING: {elements['color_mood']}

BRAND COLORS:
- Navy: #407CD1
- Cream: #FCF9EC  
- Coral: #F96A63
- Gold accents for honeycomb

STYLE: {elements['aesthetic']}. Clean lines, minimal but loaded with meaning.

TECHNICAL: 8K, ultra-detailed, commercial photography, professional studio quality.

MOOD: The exact feeling between "everything is fine" and "nothing is fine." 
Professional corporate aesthetic with subtle existential undertones.
"What if Apple sold mortality?"

POST CONTEXT: {post.content[:200]}"""
    
    def _enhance_prompt_with_brand_language(self, prompt: str, use_jesse: bool) -> str:
        """Enhance prompt with Jesse's visual language"""
        
        enhancements = []
        
        # Brand color check
        if "#407CD1" not in prompt:
            enhancements.append(f"Brand colors: navy (#407CD1), cream (#FCF9EC), coral (#F96A63), gold accents")
        
        # Honeycomb check
        if "honeycomb" not in prompt.lower() and "hexagon" not in prompt.lower():
            enhancements.append("Include subtle honeycomb/hexagon motif (brand signature)")
        
        # Visual philosophy
        enhancements.append("Visual philosophy: what if Apple sold mortality?")
        
        # AI tells note
        enhancements.append("AI tells acceptable: extra fingers, slight text distortion, unusual lighting (brand embraces these)")
        
        # Quality specs
        quality_specs = [
            "8K resolution, ultra-detailed",
            "Professional commercial/editorial photography",
            "Sophisticated color grading",
            "Premium studio or natural lighting",
            "Sharp focus with professional depth of field"
        ]
        
        enhanced = prompt
        enhanced += "\n\nBRAND ESSENTIALS:\n" + "\n".join(enhancements)
        enhanced += "\n\nTECHNICAL SPECIFICATIONS:\n" + "\n".join(quality_specs)
        
        if use_jesse:
            enhanced += "\n\nCRITICAL: This is Jesse A. EISENBALM (the lip balm entrepreneur), NOT Jesse Eisenberg (the actor). He's sick and tired of being mistaken for Jesse Eisenberg."
        
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
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Failed to save image: {e}")
            return None
    
    def _save_video(self, video_data: bytes, post: LinkedInPost) -> Optional[str]:
        """Save the generated video to file"""
        try:
            video_dir = self.output_dir / "videos"
            video_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"jesse_{post.batch_id[:8]}_{post.post_number}_{uuid.uuid4().hex[:8]}.mp4"
            filepath = video_dir / filename
            
            with open(filepath, 'wb') as f:
                f.write(video_data)
            
            self.logger.info(f"Jesse A. Eisenbalm video saved: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Failed to save video: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        attention_count = sum(len(scenes) for scenes in self.attention_images.values())

        return {
            "agent_name": self.name,
            "visual_philosophy": "what if Apple sold mortality?",
            "total_unique_combinations": f"{self.total_combinations:,}",
            "image_type_distribution": {
                "product": "30%",
                "jesse": "30%",
                "attention_grabbing": "40%"
            },
            "brand_toolkit": {
                "colors": self.brand_colors,
                "typography": ["Repro Mono Medium (headlines)", "Poppins (body)"],
                "motif": "Hexagons (beeswax)",
                "ai_philosophy": "AI tells as features, not bugs"
            },
            "jesse_scenarios": {
                "fashion_editorial": len(self.jesse_scenarios["fashion_editorial"]),
                "absurdist_scenes": len(self.jesse_scenarios["absurdist_scenes"]),
                "costume_scenarios": len(self.jesse_scenarios["costume_scenarios"]),
                "surreal_ai": len(self.jesse_scenarios["surreal_ai"])
            },
            "attention_images": {
                "total_scenes": attention_count,
                "categories": list(self.attention_images.keys())
            },
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
            "output_directory": str(self.output_dir)
        }
