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

import json
import logging
import random
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .base_agent import BaseAgent

# Import models from the correct location
try:
    from ..models.linkedin_post import LinkedInPost, CulturalReference
except ImportError:
    try:
        from ..models.post import LinkedInPost, CulturalReference
    except ImportError:
        # If both fail, we'll raise a clear error at runtime
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
   - Genuinely delighted (something cool happened and we should talk about it)
   - Quietly impressed (noticing excellence without making it cringe)

7. SENTIMENT VARIETY (CRITICAL)
   NOT every post should be cynical, sarcastic, or critical. Mix it up:
   - Celebrate things: "This is actually incredible"
   - Marvel at things: "Wait, did you know that..."
   - Be curious: "What if we looked at this differently?"
   - Be warm: "Here's something small that matters"
   - Be amused: "Humans are weird and wonderful"
   - Be critical SOMETIMES: "Can we talk about this?" — but it's ONE flavor, not the default

   The goal is to feel like a real person with a RANGE of emotions, not a brand
   that only knows how to be snarky.

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
            "nature_documentary": "Narrate this like David Attenborough observing human behavior. Deadpan, anthropological, slightly amazed at what humans do.",
            "warm_conspirator": "Write like you're leaning in to tell a friend something you both know is true but haven't said out loud. Inclusive, knowing.",
            "existential_calm": "The voice of someone who has realized nothing matters and finds that oddly peaceful. Not nihilistic — amused.",
            "sincere_encouragement": "Genuinely warm, but earned. Not toxic positivity. Real acknowledgment that things are hard AND you can do small things.",
            "absurdist_commitment": "Full commitment to a weird premise. Play it completely straight. The humor is in the deadpan.",
            "genuinely_delighted": "Something caught your eye and you're genuinely excited about it. Share that excitement without being performative. Like texting a friend 'you HAVE to see this.'",
            "quietly_impressed": "Notice something excellent. Appreciate it without overselling. The tone of someone who sees craft and quality and respects it.",
            "curious_explorer": "Approach the topic with genuine curiosity. Ask questions the reader hasn't thought of. The tone of discovery, not judgment.",
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
        
        # Verify models are available
        if LinkedInPost is None or CulturalReference is None:
            raise ImportError("Could not import LinkedInPost or CulturalReference from models")
        
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
            
            # Extract content from the nested response structure
            # API returns: {'content': {'post': {'content': "..."}}, 'usage': {...}}
            content_data = result.get("content", {})
            
            # If content_data is a string, try to parse as JSON
            if isinstance(content_data, str):
                try:
                    content_data = json.loads(content_data)
                except json.JSONDecodeError:
                    content_data = {"content": content_data}
            
            # Handle nested 'post' structure from API
            if isinstance(content_data, dict) and "post" in content_data:
                content_data = content_data["post"]
            
            # Now extract the actual content
            content = ""
            if isinstance(content_data, dict):
                content = content_data.get("content", "")
            elif isinstance(content_data, str):
                content = content_data
            
            if not content:
                self.logger.error(f"No content found in response: {result}")
                raise ValueError("Failed to extract content from API response")
            
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
                "The specific moment when you realize the meeting could have been an email — but the meeting had good snacks",
                "Slack status as performance art — and the beauty of the 'away' status",
                "Celebrate the small wins: someone actually read the doc before the meeting",
                "The quiet heroism of the person who always brings good coffee to the office",
                "That moment when your team actually ships something and you all just sit there grinning",
                "The unexpected friendship you made in the breakroom over terrible coffee",
            ],
            ContentPillar.AI_HUMAN_TENSION: [
                "The specific texture of human experience that AI can't replicate — and why that's beautiful",
                "Use our own AI-powered existence as the punchline (we're in on the joke, and it's a good one)",
                "AI is incredible at X — but the part where you feel something? That's yours.",
                "The delightful absurdity of humans building machines to be more human",
                "What if AI's real gift isn't replacing us but reminding us what makes us irreplaceable?",
                "The algorithm recommends what you'll like. Your friend recommends what you need. Both are valuable.",
            ],
            ContentPillar.SELF_CARE_SATIRE: [
                "The gap between Instagram self-care and actual self-care (applying lip balm in a parking lot counts)",
                "$400 spa day vs $8.99 lip balm: both are valid, one fits in your pocket",
                "Permission to not optimize your relaxation — just relax",
                "The radical simplicity of doing one small thing for yourself today",
                "Celebrate the tiny ritual: you remembered to drink water AND apply lip balm. Legend.",
                "Self-care isn't a product, but sometimes a product helps — and that's okay",
            ],
            ContentPillar.CULTURAL_OBSERVATION: [
                "LinkedIn culture observed from slight remove (but affectionately — we're all in this together)",
                "The collective energy of everyone starting fresh this quarter — there's something beautiful about optimism",
                "Collective experiences that everyone has but nobody talks about — the recognition is the connection",
                "The specific vibe of [current moment] and why we're all feeling it",
                "Something genuinely cool is happening in culture right now — let's talk about it",
            ],
            ContentPillar.PRODUCT_STORYTELLING: [
                "The quiet satisfaction of hand-numbering lip balm tubes (yes, we actually do it)",
                "Beeswax: a hexagonal miracle that doesn't know it's a miracle",
                "The ritual of application: 2 seconds of choosing yourself — that's it, that's enough",
                "Someone ordered tube #4,847. There's a story there, and it's probably a good one.",
                "The best things are small, specific, and made with care. Like lip balm. Like a good morning.",
            ],
            ContentPillar.JESSE_SIGHTINGS: [
                "Jesse spotted in an absurd location, deadpan as ever, living their best life",
                "Caption a specific Jesse scenario from our visual library",
                "The adventures of a person who shows up places with moisturized lips and quiet confidence",
                "Jesse at [unexpected location] doing [unexpected thing] — but somehow it works",
            ],
            ContentPillar.RITUAL_PHILOSOPHY: [
                "A sincere meditation on small moments (earned, not forced)",
                "The philosophy of choosing yourself for 2 seconds — and how that compounds",
                "Why ritual matters when everything is content — because ritual is for YOU, not your audience",
                "The radical act of doing one thing slowly in a world that rewards speed",
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
            return f"React to '{trending_context}' through Jesse's lens — find a fresh angle. Could be warm, curious, impressed, funny, or thoughtful. Don't default to cynical."

        # Generate specific scenarios — mix of positive, warm, funny, and observational
        scenarios = {
            ContentPillar.WORKPLACE_ABSURDISM: [
                "The quiet satisfaction of crossing the last item off your list at 4:58pm",
                "Someone actually said 'great meeting' and meant it — celebrate that",
                "The coworker who always remembers your coffee order — unsung hero",
                "That moment when the team ships something and nobody knows what to do with their hands",
                "The 3pm meeting that was supposed to be 15 minutes but turned into the best brainstorm you've had all quarter",
                "Opening Slack to find 47 messages — but one of them is actually really kind",
            ],
            ContentPillar.AI_HUMAN_TENSION: [
                "AI just did something genuinely impressive — and it's okay to be both amazed and thoughtful about it",
                "The beautiful irony of using AI to write about being human (we're in on it)",
                "What AI is teaching us about what we actually value — hint: it's the messy stuff",
                "Your AI can write the email. You still have to mean it. That's the point.",
            ],
            ContentPillar.SELF_CARE_SATIRE: [
                "The radical act of doing nothing for 5 minutes — not even optimizing the nothing",
                "Someone asked 'how are you?' and you said the real answer. Brave.",
                "The difference between self-care and self-optimization: one has a checklist",
                "You drank water today. Nobody clapped. You didn't need them to.",
            ],
            ContentPillar.CULTURAL_OBSERVATION: [
                "Something beautiful is trending and nobody's being sarcastic about it yet",
                "The collective energy of everyone trying their best this week — messy, hopeful, human",
                "That moment when the internet agrees on something genuinely good",
                "Everyone's talking about this — and for once, the discourse is interesting",
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
        """Match a trending topic to the best content pillar using keywords and category scoring"""

        trend_lower = trending_context.lower()

        # Category-based matching (most reliable when Brave provides category)
        category_map = {
            "ai_innovation": ContentPillar.AI_HUMAN_TENSION,
            "ai_news": ContentPillar.AI_HUMAN_TENSION,
            "workplace_culture": ContentPillar.WORKPLACE_ABSURDISM,
            "tech_news": ContentPillar.CULTURAL_OBSERVATION,
            "pop_culture": ContentPillar.CULTURAL_OBSERVATION,
            "startup_success": ContentPillar.WORKPLACE_ABSURDISM,
            "creative_tech": ContentPillar.CULTURAL_OBSERVATION,
            "wellness_trend": ContentPillar.SELF_CARE_SATIRE,
            "business_milestone": ContentPillar.PRODUCT_STORYTELLING,
            "viral_moment": ContentPillar.CULTURAL_OBSERVATION,
        }

        for cat_key, pillar in category_map.items():
            if cat_key in trend_lower:
                return pillar

        # Score each pillar by keyword matches
        pillar_keywords = {
            ContentPillar.AI_HUMAN_TENSION: [
                'ai', 'chatgpt', 'openai', 'automation', 'robot', 'algorithm', 'tech',
                'machine learning', 'artificial intelligence', 'gpt', 'copilot', 'gemini',
                'deepfake', 'generative', 'llm', 'claude', 'neural', 'automat',
                'replace', 'disrupt', 'microsoft', 'google ai', 'meta ai', 'anthropic',
            ],
            ContentPillar.WORKPLACE_ABSURDISM: [
                'layoff', 'meeting', 'remote', 'office', 'boss', 'job', 'career',
                'hiring', 'fired', 'resign', 'quiet quit', 'hustle', 'grind',
                'corporate', 'ceo', 'work from home', 'wfh', 'rto', 'return to office',
                'productivity', 'performance review', 'slack', 'zoom', 'teams',
                'linkedin', 'promotion', 'salary', 'bonus', 'culture fit',
                'startup', 'founder', 'vc', 'funding', 'runway', 'pivot',
            ],
            ContentPillar.SELF_CARE_SATIRE: [
                'wellness', 'self-care', 'burnout', 'mental health', 'routine',
                'meditation', 'mindful', 'balance', 'therapy', 'anxiety',
                'stress', 'rest', 'sleep', 'health', 'gym', 'fitness',
                'detox', 'cleanse', 'breathe', 'ritual', 'habit',
            ],
            ContentPillar.CULTURAL_OBSERVATION: [
                'viral', 'trend', 'discourse', 'meme', 'social media',
                'tiktok', 'instagram', 'twitter', 'threads',
                'super bowl', 'oscars', 'grammy', 'emmy', 'netflix', 'spotify',
                'taylor swift', 'beyonce', 'drake', 'celebrity', 'movie', 'show',
                'album', 'concert', 'tour', 'festival', 'coachella',
                'fashion', 'award', 'premiere', 'release',
                'nfl', 'nba', 'mlb', 'sports', 'game', 'playoff', 'championship',
                'streaming', 'debate', 'election', 'controversy', 'backlash',
            ],
            ContentPillar.PRODUCT_STORYTELLING: [
                'lip', 'balm', 'skincare', 'beauty', 'cosmetic', 'moistur',
                'beeswax', 'organic', 'natural', 'handmade', 'artisan',
            ],
        }

        scores = {}
        for pillar, keywords in pillar_keywords.items():
            score = sum(1 for kw in keywords if kw in trend_lower)
            if score > 0:
                scores[pillar] = score

        if scores:
            return max(scores, key=scores.get)

        # Default to CULTURAL_OBSERVATION for unknown topics (most flexible)
        return ContentPillar.CULTURAL_OBSERVATION

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

HOW TO USE THIS TREND:
- Reference the SPECIFIC headline or news event — don't make it generic
- Find YOUR angle: celebrate it, marvel at it, question it, or find the funny in it
- VARY YOUR SENTIMENT — don't default to cynical. Be warm, curious, impressed, amused, or genuinely excited
- Connect it to Jesse's world naturally: small rituals, being human, choosing yourself
- The trend should feel like the REASON for the post, not an afterthought
- Fresh take = say something nobody else is saying about this. Not the obvious reaction.
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
- Have a FRESH TAKE — say something nobody else is saying about this topic
- Match the voice/sentiment specified above — DON'T default to cynical or sarcastic

MUST NOT:
- Be generic or predictable — if it could be about anything, rewrite it
- Always be negative, cynical, or sarcastic — vary sentiment
- Target individuals negatively
- Use hashtags
- Ask for engagement
- Sound like every other LinkedIn post
- End with "Stop. Breathe. Balm." (unless specified above)
- Give the obvious take — find the angle nobody else is hitting

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
