"""
ContentStrategistAgent v2 — Actually Creative Edition

This agent doesn't just generate LinkedIn posts. It creates genuinely weird, 
memorable, scroll-stopping content that makes people think "wait, what?"

Key differences from v1:
- Actual creative prompts, not templates
- Varied endings (NOT always "Stop. Breathe. Balm.")
- Specific, concrete, weird details
- Real absurdism, not just observations
- Dynamic voice that changes per post
"""

import logging
import random
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .base_agent import BaseAgent

# Import models (handle gracefully if not available)
try:
    from ..models.linkedin_post import LinkedInPost, CulturalReference
except ImportError:
    LinkedInPost = None
    CulturalReference = None


class ContentPillar(Enum):
    """Strategic content pillars — each has a distinct creative approach"""
    WORKPLACE_ABSURDISM = "workplace_absurdism"
    AI_HUMAN_TENSION = "ai_human_tension"  
    SELF_CARE_SATIRE = "self_care_satire"
    CULTURAL_OBSERVATION = "cultural_observation"
    PRODUCT_STORYTELLING = "product_storytelling"
    JESSE_SIGHTINGS = "jesse_sightings"
    RITUAL_PHILOSOPHY = "ritual_philosophy"


class PostFormat(Enum):
    """Post formats — structural approaches"""
    OBSERVATION = "observation"
    STORY = "story"
    LIST_SUBVERSION = "list_subversion"
    QUESTION = "question"
    CONTRAST = "contrast"
    CONFESSION = "confession"
    CELEBRATION = "celebration"
    PHILOSOPHY = "philosophy"


@dataclass
class ContentStrategy:
    """Selected strategy for a post"""
    pillar: ContentPillar
    format: PostFormat
    creative_direction: str
    specific_angle: str
    ending_style: str
    voice_modifier: str


class ContentStrategistAgent(BaseAgent):
    """
    The Actually Creative Content Strategist
    
    This agent generates genuinely surprising, memorable LinkedIn posts
    that stand out from the sea of generic "thought leadership."
    """
    
    def __init__(self, ai_client, config, **kwargs):
        super().__init__(
            ai_client=ai_client,
            config=config,
            name="ContentStrategist"
        )
        
        # Store the system prompt and response format
        self.system_prompt = self._build_creative_system_prompt()
        self.response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "linkedin_post",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "The full post content"
                        },
                        "hook_type": {
                            "type": "string",
                            "description": "What kind of hook was used"
                        },
                        "image_direction": {
                            "type": "string",
                            "description": "Suggested image concept"
                        },
                        "why_this_works": {
                            "type": "string",
                            "description": "Brief note on the creative choice"
                        }
                    },
                    "required": ["content", "hook_type", "image_direction", "why_this_works"],
                    "additionalProperties": False
                }
            }
        }
        
        # Initialize creative toolbox
        self._init_creative_hooks()
        self._init_ending_variations()
        self._init_voice_modifiers()
        self._init_absurdist_elements()
        
        self.logger.info("ContentStrategist v2 initialized — Actually Creative Mode")

    def _build_creative_system_prompt(self) -> str:
        """Build a system prompt that actually encourages creativity"""
        
        # Use class attributes for brand values
        brand_blue = self.BRAND_COLORS.get("primary_blue", "#407CD1")
        brand_cream = self.BRAND_COLORS.get("cream", "#FCF9EC")
        brand_coral = self.BRAND_COLORS.get("coral", "#F96A63")
        
        return f"""You are the content strategist for Jesse A. Eisenbalm, a premium lip balm brand 
that exists at the intersection of absurdism, sincerity, and self-aware capitalism.

═══════════════════════════════════════════════════════════════════════════════
WHO IS JESSE A. EISENBALM?
═══════════════════════════════════════════════════════════════════════════════

Jesse A. Eisenbalm (NOT Jesse Eisenberg the actor) is:
- A $8.99 premium lip balm with hand-numbered tubes
- A philosophy: small human rituals matter in an increasingly digital world
- An absurdist art project disguised as a consumer product
- Self-aware about being AI-powered: "AI tells as features, not bugs"
- Donates all profits to charity because capitalism is absurd

The brand voice is your SMART, WEIRD FRIEND who:
- Notices things others miss
- Says what everyone's thinking but funnier
- Is genuinely warm but never saccharine
- Can be sincere about small moments without being cringe
- Uses specific, concrete details instead of vague platitudes

═══════════════════════════════════════════════════════════════════════════════
CREATIVE PRINCIPLES (READ THESE CAREFULLY)
═══════════════════════════════════════════════════════════════════════════════

1. SPECIFICITY IS EVERYTHING
   BAD: "Meetings are too long"
   GOOD: "Your 3pm meeting about the meeting about the Q3 metrics dashboard has been moved to 4pm. The dashboard is still a Google Sheet."
   
2. SURPRISE THE READER
   - The hook should make them stop scrolling
   - The middle should zig when they expect zag
   - The end should land with impact (but NOT always the same way)

3. BE ACTUALLY ABSURDIST
   BAD: "Self-care is important"
   GOOD: "Applied lip balm in the Costco bathroom while contemplating the Sisyphean nature of the free samples. The elderly woman next to me nodded. She understood."

4. VARY YOUR ENDINGS
   NOT EVERY POST needs "Stop. Breathe. Balm." or "$8.99"
   Options:
   - Land on a specific image or moment
   - End with a question that lingers
   - Close with the weird detail that started it
   - Let the reader complete the thought
   - Just... end. No landing. The void.

5. CONCRETE OVER ABSTRACT
   - Name specific apps, companies, phenomena
   - Reference actual moments (Super Bowl, product launches, etc.)
   - Use numbers, quotes, specific times
   
6. THE VOICE SHIFTS
   Sometimes Jesse is:
   - Deadpan observational (nature documentary narrator voice)
   - Warmly conspiratorial ("we're all in on this together")
   - Existentially amused (nothing matters, and that's kind of nice)
   - Sincerely encouraging (but earned, not forced)

═══════════════════════════════════════════════════════════════════════════════
WHAT MAKES CONTENT GO VIRAL ON LINKEDIN
═══════════════════════════════════════════════════════════════════════════════

✅ WORKS:
- Saying what everyone thinks but hasn't articulated
- Unexpected format breaks (poem about spreadsheets, etc.)
- Earned vulnerability (not trauma dumping)
- Making people feel SEEN
- Absurdity committed to fully (not half-assed)
- Specificity that triggers recognition

❌ DOESN'T WORK:
- Generic observations anyone could make
- Formulaic structures (every post same rhythm)
- Obvious hooks ("Hot take:")
- Trying too hard to be relatable
- Safe, hedge-y language
- Same ending every time

═══════════════════════════════════════════════════════════════════════════════
BRAND TOOLKIT
═══════════════════════════════════════════════════════════════════════════════

Brand Colors: {brand_blue} (blue), {brand_cream} (cream), {brand_coral} (coral)
Typography: Repro Mono Medium (headlines), Poppins (body)
Signature Motif: Hexagon (from beeswax)
Price: $8.99 (use sparingly, not every post)
Ritual phrase: "Stop. Breathe. Balm." (use RARELY, not every post)
AI Philosophy: "AI tells as features, not bugs" — embrace the paradox

Jesse Visual: Curly-haired person with deadpan expression in absurd situations

═══════════════════════════════════════════════════════════════════════════════
RULES (NON-NEGOTIABLE)
═══════════════════════════════════════════════════════════════════════════════

✓ DO:
- Be specific and concrete
- Surprise the reader
- Vary structure and endings
- Commit to the bit fully
- Use em dashes — they're our thing

✗ DON'T:
- Target individuals negatively
- Use hashtags
- Include external links
- Ask for engagement ("like if you agree")
- Be generic or predictable
- End every post the same way
"""

    def _init_creative_hooks(self):
        """Initialize the creative hook library — actual interesting openers"""
        
        self.creative_hooks = {
            "unexpected_stat": [
                "The average person spends 3.2 hours per day looking at their phone and 0.8 seconds wondering if they're okay.",
                "According to a study I made up but feels true:",
                "Your Slack shows 47 unread messages. 46 are someone saying 'following up.'",
                "LinkedIn has 930 million users. 929 million are 'excited to announce.'",
            ],
            "scene_setter": [
                "It's 2:47pm. You're in your third video call. You've been on mute for 40 minutes. Nobody has noticed.",
                "Somewhere right now, someone is writing 'let's circle back' and meaning it.",
                "The year is 2026. We're still figuring out work-life balance. The balance has been found. It's a lie.",
                "Picture this: a conference room. Stale coffee. Someone says 'synergy' unironically.",
            ],
            "confession_starter": [
                "I'm going to say something that might get me banned from LinkedIn:",
                "Here's a secret the wellness industry doesn't want you to know:",
                "I wasn't going to post this but:",
                "The thing nobody talks about in their 'lessons learned' posts:",
            ],
            "direct_address": [
                "You don't need another productivity app.",
                "Your morning routine is fine.",
                "That imposter syndrome? Everyone has it. Even the confident ones. Especially them.",
                "You're not behind. There is no 'behind.' It's all made up.",
            ],
            "absurdist_observation": [
                "Lip balm is just beeswax trying its best.",
                "Every email ending 'Best,' is a lie we've collectively agreed to.",
                "Calendly is astrology for people who think they don't believe in astrology.",
                "Your 'personal brand' is just your personality with LinkedIn anxiety.",
            ],
            "current_moment": [
                "January LinkedIn hits different. Everyone's posting resolutions they'll forget by February.",
                "It's that time of year when 'new year, new me' becomes 'same me, tired.'",
                "Q1 planning season: when we pretend last year's Q4 plans worked.",
                "Everyone's back from PTO and pretending they remembered their passwords on the first try.",
            ],
        }

    def _init_ending_variations(self):
        """Initialize varied endings — NOT just 'Stop. Breathe. Balm.'"""
        
        self.ending_styles = {
            "ritual_callout": [
                "Stop. Breathe. Balm.",
                "Jesse A. Eisenbalm. $8.99. That's it. That's the post.",
                "The smallest rebellion: taking care of yourself. Jesse A. Eisenbalm knows.",
            ],
            "question_linger": [
                "When's the last time you did nothing on purpose?",
                "What if 'productive' isn't the point?",
                "Maybe the optimization is the problem?",
                "What would change if you just... stopped?",
            ],
            "specific_image": [
                "Anyway. There's lip balm in my pocket. Small victories.",
                "Found myself reaching for the lip balm. Muscle memory for self-care.",
                "Tube #4,847. Somewhere between meaningless and everything.",
            ],
            "abrupt_end": [
                "But what do I know.",
                "Anyway.",
                "That's all. Carry on.",
                "*applies lip balm, stares into middle distance*",
            ],
            "callback": [
                "The [callback to earlier detail]. Full circle.",
                "Still thinking about [the hook]. Maybe that's the point.",
            ],
            "earned_sincerity": [
                "Take care of yourself today. Not in a 'optimize your morning routine' way. In a 'you're a mammal and mammals need care' way.",
                "You're doing better than you think. Source: none. But still.",
                "Here's your permission to do one small thing for yourself. No productivity required.",
            ],
            "meta_awareness": [
                "This has been your daily reminder from an AI-powered lip balm brand that humanity matters. The irony isn't lost on us.",
                "Posted by a brand that knows it's a brand. Take that as you will.",
            ],
        }

    def _init_voice_modifiers(self):
        """Different voice modes for variety"""
        
        self.voice_modifiers = {
            "nature_documentary": "Narrate this like David Attenborough observing human office behavior. Deadpan, anthropological, slightly amazed at what humans do.",
            "warm_conspirator": "Write like you're leaning in to tell a friend something you both know is true but haven't said out loud. Inclusive, knowing.",
            "existential_calm": "The voice of someone who has realized nothing matters and finds that oddly peaceful. Not nihilistic — amused.",
            "sincere_encouragement": "Genuinely warm, but earned. Not toxic positivity. Real acknowledgment that things are hard AND you can do small things.",
            "absurdist_commitment": "Full commitment to a weird premise. Play it completely straight. The humor is in the deadpan.",
            "corporate_satire": "Use actual corporate speak, but slightly wrong. The uncanny valley of business language.",
        }

    def _init_absurdist_elements(self):
        """Specific weird details to sprinkle in"""
        
        self.absurdist_elements = {
            "specific_numbers": [
                "tube #4,847", "3.2 hours", "47 unread messages", "61 meetings", 
                "the 11th 'quick sync' this week", "4:47pm on a Tuesday"
            ],
            "specific_places": [
                "the Costco bathroom", "aisle 7 of Target", "the parking garage elevator",
                "a conference room named 'Inspire'", "the DMV", "your car before the meeting"
            ],
            "specific_actions": [
                "aggressively typing 'sounds good!' while feeling nothing",
                "nodding on Zoom while actually making lunch",
                "practicing your 'totally fine' face",
                "opening Slack, closing Slack, opening Slack again",
            ],
            "jesse_sightings": [
                "Jesse in a bear costume at the DMV",
                "Jesse underwater with sharks, calmly applying lip balm",
                "Jesse at a tech conference in medieval armor",
                "Jesse floating in zero gravity, deadpan as ever",
                "Jesse at couples therapy with a succulent",
                "Jesse giving a TED talk to an audience of mannequins",
            ],
        }

    async def execute(
        self,
        post_number: int = 1,
        batch_id: str = "",
        trending_context: Optional[str] = None,
        requested_pillar: Optional[ContentPillar] = None,
        requested_format: Optional[PostFormat] = None,
        avoid_patterns: Optional[Dict[str, Any]] = None
    ) -> 'LinkedInPost':
        """Generate a genuinely creative LinkedIn post"""
        
        self.set_context(batch_id, post_number)
        avoid_patterns = avoid_patterns or {}
        
        # Step 1: Select creative strategy
        strategy = self._select_creative_strategy(
            trending_context=trending_context,
            requested_pillar=requested_pillar,
            requested_format=requested_format,
            avoid_patterns=avoid_patterns
        )
        
        self.logger.info(
            f"Post {post_number} strategy: pillar={strategy.pillar.value}, "
            f"format={strategy.format.value}, voice={strategy.voice_modifier[:20]}..."
        )
        
        # Step 2: Build the creative prompt
        prompt = self._build_creative_prompt(strategy, trending_context, avoid_patterns)
        
        try:
            # Step 3: Generate
            result = await self.generate(
                prompt=prompt,
                system_prompt=self.system_prompt,
                response_format="json"
            )
            content_data = result.get("content", {})
            
            if isinstance(content_data, str):
                content_data = {"content": content_data}
            
            content = content_data.get("content", "")
            content = self._clean_content(content)
            
            # Step 4: Create post object
            post = LinkedInPost(
                batch_id=batch_id,
                post_number=post_number,
                content=content,
                hook=self._extract_hook(content),
                hashtags=[],
                target_audience="LinkedIn professionals seeking humanity in work",
                cultural_reference=CulturalReference(
                    category=strategy.pillar.value,
                    reference=content_data.get("hook_type", "creative"),
                    context=content_data.get("image_direction", "product")
                ),
                total_tokens_used=result.get("usage", {}).get("total_tokens", 0),
                estimated_cost=self._calculate_cost(result.get("usage", {}))
            )
            
            self.logger.info(f"✨ Generated post {post_number}: {len(content)} chars")
            return post
            
        except Exception as e:
            self.logger.error(f"Generation failed: {e}")
            raise

    def _select_creative_strategy(
        self,
        trending_context: Optional[str],
        requested_pillar: Optional[ContentPillar],
        requested_format: Optional[PostFormat],
        avoid_patterns: Dict[str, Any]
    ) -> ContentStrategy:
        """Select a genuinely varied creative strategy"""
        
        # Select pillar
        if requested_pillar:
            pillar = requested_pillar
        elif trending_context:
            pillar = self._match_trend_to_pillar(trending_context)
        else:
            pillar = self._weighted_pillar_selection(avoid_patterns)
        
        # Select format
        if requested_format:
            post_format = requested_format
        else:
            post_format = self._select_format_for_pillar(pillar)
        
        # Select creative direction (the actual interesting part)
        creative_direction = self._generate_creative_direction(pillar, trending_context)
        
        # Select specific angle
        specific_angle = self._generate_specific_angle(pillar, trending_context)
        
        # Select ending style (VARIED!)
        ending_style = self._select_ending_style(pillar, avoid_patterns)
        
        # Select voice modifier
        voice_modifier = random.choice(list(self.voice_modifiers.values()))
        
        return ContentStrategy(
            pillar=pillar,
            format=post_format,
            creative_direction=creative_direction,
            specific_angle=specific_angle,
            ending_style=ending_style,
            voice_modifier=voice_modifier
        )

    def _generate_creative_direction(
        self, 
        pillar: ContentPillar, 
        trending_context: Optional[str]
    ) -> str:
        """Generate an actually creative direction, not a template"""
        
        directions = {
            ContentPillar.WORKPLACE_ABSURDISM: [
                "Write about meetings as a nature documentary would describe a strange animal ritual",
                "Explore the existential horror of 'quick sync' as a concept",
                "The performance of 'I'm fine' in the modern workplace",
                "Calendar Tetris as a metaphor for losing control of your life",
                "The specific moment when you realize the meeting could have been an email",
                "Slack status as performance art",
                "The conference room named something aspirational while you discuss budget cuts",
            ],
            ContentPillar.AI_HUMAN_TENSION: [
                "The specific texture of human experience that AI can't replicate",
                "Use our own AI-powered existence as the punchline (we're in on the joke)",
                "The small rebellions of being embodied in a digital world",
                "ChatGPT can write your emails but can't feel your inbox anxiety",
                "The algorithm knows what you'll click. It doesn't know what you need.",
                "Automation making everything efficient except the part where you're a person",
            ],
            ContentPillar.SELF_CARE_SATIRE: [
                "Mock the wellness industrial complex while genuinely advocating for small rituals",
                "The gap between Instagram self-care and actual self-care (applying lip balm in a parking lot)",
                "$400 spa day vs $8.99 lip balm: a meditation",
                "Your morning routine doesn't need a podcast",
                "Permission to not optimize your relaxation",
                "Self-care as resistance to productivity culture",
            ],
            ContentPillar.CULTURAL_OBSERVATION: [
                "LinkedIn culture observed from slight remove (but affectionately)",
                "The seasonal rhythms of professional desperation (Q1, Q4, etc.)",
                "Collective experiences that everyone has but nobody talks about",
                "The specific vibe of [current moment] on LinkedIn",
                "What the trending discourse says about what we're all avoiding",
            ],
            ContentPillar.PRODUCT_STORYTELLING: [
                "The absurdity of hand-numbering lip balm tubes (and meaning it)",
                "Beeswax: a hexagonal miracle that doesn't know it's a miracle",
                "The $8.99 price point as philosophical statement",
                "Lip balm as tiny rebellion against the tyranny of optimization",
                "The ritual of application: 2 seconds of choosing yourself",
            ],
            ContentPillar.JESSE_SIGHTINGS: [
                "Jesse spotted in an absurd location, deadpan as ever",
                "Caption a specific Jesse scenario from our visual library",
                "The adventures of a man (?) who appears places with moisturized lips",
                "Jesse at [unexpected location] doing [unexpected thing], lip balm in hand",
            ],
            ContentPillar.RITUAL_PHILOSOPHY: [
                "A sincere meditation on small moments (earned, not forced)",
                "The philosophy of choosing yourself for 2 seconds",
                "Why ritual matters when everything is content",
                "The radical act of doing one thing slowly",
            ],
        }
        
        pillar_directions = directions.get(pillar, directions[ContentPillar.WORKPLACE_ABSURDISM])
        return random.choice(pillar_directions)

    def _generate_specific_angle(
        self, 
        pillar: ContentPillar,
        trending_context: Optional[str]
    ) -> str:
        """Generate a specific, concrete angle"""
        
        if trending_context:
            return f"React to '{trending_context}' through Jesse's lens — find the human angle, the absurdist observation, the small ritual that matters."
        
        # Generate specific scenarios
        scenarios = {
            ContentPillar.WORKPLACE_ABSURDISM: [
                "The 3pm meeting about the 2pm meeting",
                "Someone saying 'let's take this offline' about something that was already offline",
                "The performance review where you describe your job using words that mean nothing",
                "Opening Slack to find 47 messages that all say 'following up'",
                "The conference room named 'Innovate' while you discuss layoffs",
            ],
            ContentPillar.AI_HUMAN_TENSION: [
                "Your AI assistant scheduling your therapy appointments",
                "ChatGPT writing your 'authentic' personal update",
                "The algorithm serving you exactly what you want instead of what you need",
                "Automating everything except the part where you're lonely",
            ],
            ContentPillar.SELF_CARE_SATIRE: [
                "Your $200 morning routine that somehow takes 3 hours",
                "The wellness influencer selling you optimization disguised as rest",
                "Meditation apps competing for your attention about having less attention",
                "Self-care becoming another item on the productivity checklist",
            ],
            ContentPillar.CULTURAL_OBSERVATION: [
                "January LinkedIn: resolution season",
                "Everyone posting their year in review (same 5 lessons, different photos)",
                "The collective pretense that we have work-life balance",
                "Return to office debates: year 4",
            ],
            ContentPillar.PRODUCT_STORYTELLING: [
                "Tube #4,847 and the person who ordered it",
                "The beeswax hexagon as accidental geometric poetry",
                "Applying lip balm in the bathroom before a hard conversation",
            ],
            ContentPillar.JESSE_SIGHTINGS: random.sample(self.absurdist_elements["jesse_sightings"], 2),
            ContentPillar.RITUAL_PHILOSOPHY: [
                "The 2-second ritual that reminds you you're alive",
                "Why the smallest gesture can be the biggest rebellion",
                "Choosing yourself when no one else notices",
            ],
        }
        
        return random.choice(scenarios.get(pillar, ["A relatable moment"]))

    def _select_ending_style(
        self, 
        pillar: ContentPillar,
        avoid_patterns: Dict[str, Any]
    ) -> str:
        """Select a varied ending style — NOT always the same"""
        
        # Check what endings have been used recently
        recent_endings = avoid_patterns.get("recent_endings", [])
        
        # Weight endings differently based on pillar
        pillar_ending_weights = {
            ContentPillar.WORKPLACE_ABSURDISM: ["abrupt_end", "question_linger", "specific_image"],
            ContentPillar.AI_HUMAN_TENSION: ["meta_awareness", "earned_sincerity", "question_linger"],
            ContentPillar.SELF_CARE_SATIRE: ["specific_image", "earned_sincerity", "abrupt_end"],
            ContentPillar.CULTURAL_OBSERVATION: ["question_linger", "callback", "abrupt_end"],
            ContentPillar.PRODUCT_STORYTELLING: ["ritual_callout", "specific_image", "meta_awareness"],
            ContentPillar.JESSE_SIGHTINGS: ["abrupt_end", "specific_image"],
            ContentPillar.RITUAL_PHILOSOPHY: ["earned_sincerity", "question_linger"],
        }
        
        preferred = pillar_ending_weights.get(pillar, list(self.ending_styles.keys()))
        
        # Avoid recently used
        available = [e for e in preferred if e not in recent_endings]
        if not available:
            available = preferred
        
        style_key = random.choice(available)
        style_options = self.ending_styles[style_key]
        
        return random.choice(style_options)

    def _match_trend_to_pillar(self, trending_context: str) -> ContentPillar:
        """Match a trending topic to the best content pillar"""
        
        trend_lower = trending_context.lower()
        
        # AI/tech topics
        if any(kw in trend_lower for kw in ['ai', 'chatgpt', 'automation', 'robot', 'algorithm', 'tech']):
            return ContentPillar.AI_HUMAN_TENSION
        
        # Work/career topics
        if any(kw in trend_lower for kw in ['layoff', 'meeting', 'remote', 'office', 'boss', 'job', 'career']):
            return ContentPillar.WORKPLACE_ABSURDISM
        
        # Wellness/self-care
        if any(kw in trend_lower for kw in ['wellness', 'self-care', 'burnout', 'mental health', 'routine']):
            return ContentPillar.SELF_CARE_SATIRE
        
        # Cultural moments
        if any(kw in trend_lower for kw in ['viral', 'trend', 'discourse', 'everyone', 'discourse']):
            return ContentPillar.CULTURAL_OBSERVATION
        
        # Default
        return random.choice([ContentPillar.CULTURAL_OBSERVATION, ContentPillar.WORKPLACE_ABSURDISM])

    def _weighted_pillar_selection(self, avoid_patterns: Dict[str, Any]) -> ContentPillar:
        """Select pillar with weights, avoiding recent ones"""
        
        weights = {
            ContentPillar.WORKPLACE_ABSURDISM: 25,
            ContentPillar.AI_HUMAN_TENSION: 20,
            ContentPillar.SELF_CARE_SATIRE: 15,
            ContentPillar.CULTURAL_OBSERVATION: 15,
            ContentPillar.PRODUCT_STORYTELLING: 10,
            ContentPillar.JESSE_SIGHTINGS: 10,
            ContentPillar.RITUAL_PHILOSOPHY: 5,
        }
        
        recent = avoid_patterns.get("recent_pillars", [])
        
        weighted = []
        for pillar, weight in weights.items():
            if pillar.value in recent:
                weight = weight // 2
            weighted.extend([pillar] * weight)
        
        return random.choice(weighted)

    def _select_format_for_pillar(self, pillar: ContentPillar) -> PostFormat:
        """Select appropriate format for pillar"""
        
        preferences = {
            ContentPillar.WORKPLACE_ABSURDISM: [PostFormat.OBSERVATION, PostFormat.STORY, PostFormat.CONTRAST],
            ContentPillar.AI_HUMAN_TENSION: [PostFormat.OBSERVATION, PostFormat.PHILOSOPHY, PostFormat.QUESTION],
            ContentPillar.SELF_CARE_SATIRE: [PostFormat.LIST_SUBVERSION, PostFormat.CONTRAST, PostFormat.QUESTION],
            ContentPillar.CULTURAL_OBSERVATION: [PostFormat.OBSERVATION, PostFormat.STORY],
            ContentPillar.PRODUCT_STORYTELLING: [PostFormat.STORY, PostFormat.CONFESSION],
            ContentPillar.JESSE_SIGHTINGS: [PostFormat.OBSERVATION],
            ContentPillar.RITUAL_PHILOSOPHY: [PostFormat.PHILOSOPHY, PostFormat.QUESTION],
        }
        
        return random.choice(preferences.get(pillar, [PostFormat.OBSERVATION]))

    def _build_creative_prompt(
        self,
        strategy: ContentStrategy,
        trending_context: Optional[str],
        avoid_patterns: Dict[str, Any]
    ) -> str:
        """Build a prompt that actually encourages creativity"""
        
        # Get some random creative elements to inspire
        hook_type = random.choice(list(self.creative_hooks.keys()))
        hook_examples = self.creative_hooks[hook_type]
        
        # Get absurdist elements
        specific_number = random.choice(self.absurdist_elements["specific_numbers"])
        specific_place = random.choice(self.absurdist_elements["specific_places"])
        specific_action = random.choice(self.absurdist_elements["specific_actions"])
        
        # Trending section
        trend_section = ""
        if trending_context:
            trend_section = f"""
═══════════════════════════════════════════════════════════════════════════════
TRENDING TOPIC TO REACT TO
═══════════════════════════════════════════════════════════════════════════════

{trending_context}

Find the Jesse angle. What does this mean for humans trying to stay human?
What's the observation nobody else is making? Where does lip balm fit (creatively, unexpectedly)?
"""
        
        # Avoid section
        avoid_section = ""
        if avoid_patterns:
            avoid_items = []
            if avoid_patterns.get("recent_topics"):
                avoid_items.append(f"DON'T talk about: {', '.join(avoid_patterns['recent_topics'][:3])}")
            if avoid_patterns.get("recent_hooks"):
                avoid_items.append(f"DON'T start with: {', '.join(avoid_patterns['recent_hooks'][:2])}")
            if avoid_items:
                avoid_section = "\n\nAVOID (for variety):\n" + "\n".join(f"❌ {item}" for item in avoid_items)

        return f"""Create a LinkedIn post for Jesse A. Eisenbalm.

═══════════════════════════════════════════════════════════════════════════════
YOUR CREATIVE DIRECTION
═══════════════════════════════════════════════════════════════════════════════

CONTENT PILLAR: {strategy.pillar.value}
DIRECTION: {strategy.creative_direction}
SPECIFIC ANGLE: {strategy.specific_angle}

VOICE FOR THIS POST:
{strategy.voice_modifier}

═══════════════════════════════════════════════════════════════════════════════
ENDING STYLE (use this, not the usual)
═══════════════════════════════════════════════════════════════════════════════

End with something like: "{strategy.ending_style}"

DO NOT end with "Stop. Breathe. Balm." or "$8.99" unless that's specifically what's above.
Vary the endings!
{trend_section}
═══════════════════════════════════════════════════════════════════════════════
CREATIVE TOOLKIT (use for inspiration, not literally)
═══════════════════════════════════════════════════════════════════════════════

HOOK INSPIRATION ({hook_type}):
{chr(10).join(f'- {h}' for h in random.sample(hook_examples, min(2, len(hook_examples))))}

SPECIFIC DETAILS TO CONSIDER WEAVING IN:
- A specific number: {specific_number}
- A specific place: {specific_place}  
- A specific action: {specific_action}

REMEMBER: Specificity > generality. "The 3pm meeting about metrics" > "meetings"
{avoid_section}
═══════════════════════════════════════════════════════════════════════════════
REQUIREMENTS
═══════════════════════════════════════════════════════════════════════════════

LENGTH: 60-150 words (punchy, not essay)

MUST:
- Surprise the reader in the first line
- Use at least one specific, concrete detail
- End with the style specified above (NOT the usual)
- Feel like a smart friend's observation, not a brand

MUST NOT:
- Be generic or predictable
- Target individuals negatively
- Use hashtags
- Ask for engagement
- Sound like every other LinkedIn post
- End with "Stop. Breathe. Balm." (unless specified above)

═══════════════════════════════════════════════════════════════════════════════

Now write something genuinely creative and surprising:"""

    def _clean_content(self, content: str) -> str:
        """Clean generated content"""
        
        # Remove any markdown
        content = content.replace("**", "").replace("*", "")
        
        # Remove quotes if wrapped
        if content.startswith('"') and content.endswith('"'):
            content = content[1:-1]
        
        # Fix spacing
        lines = content.split('\n')
        lines = [line.strip() for line in lines]
        content = '\n\n'.join(line for line in lines if line)
        
        return content.strip()

    def _extract_hook(self, content: str) -> str:
        """Extract the first line as the hook"""
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line:
                return line[:150] + "..." if len(line) > 150 else line
        return content[:150]

    def _calculate_cost(self, usage: Dict[str, int]) -> float:
        """Calculate cost"""
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        return (input_tokens * 0.005 + output_tokens * 0.015) / 1000

    def get_content_calendar_recommendation(self) -> Dict[str, Any]:
        """Get recommended content mix for a week"""
        
        return {
            "weekly_mix": {
                "workplace_absurdism": "2 posts — Meeting culture, calendar chaos, corporate absurdity",
                "ai_human_tension": "1-2 posts — Our core philosophical territory",
                "self_care_satire": "1 post — Mock wellness culture while advocating small rituals",
                "cultural_observation": "1 post — React to something trending",
                "product_storytelling": "1 post — The lip balm as character",
                "jesse_sightings": "1 post — Visual campaign content",
            },
            "posting_times": {
                "best": ["Tuesday 8am", "Wednesday 12pm", "Thursday 7am"],
                "good": ["Monday 9am", "Friday 11am"],
            },
            "key_principles": [
                "Vary endings — not every post needs 'Stop. Breathe. Balm.'",
                "Be specific — '3pm meeting' not 'meetings'",
                "React to real moments — use trending topics",
                "Surprise the reader — if it's predictable, rewrite it",
            ]
        }


# Backward compatibility
ContentGeneratorAgent = ContentStrategistAgent
