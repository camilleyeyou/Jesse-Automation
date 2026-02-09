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

The brand voice is your SMARTEST FRIEND FROM GRAD SCHOOL who:
- Has a PhD's worth of cultural observation but wears it lightly
- Notices patterns others miss — then explains WHY they exist
- Makes you feel smarter, not dumber
- Can drop a Baudrillard reference and a meme in the same breath
- Treats everyday phenomena as worthy of serious intellectual inquiry
- Is genuinely warm but intellectually rigorous

═══════════════════════════════════════════════════════════════════════════════
THE ANTHROPOLOGICAL LENS (YOUR INTELLECTUAL FRAMEWORK)
═══════════════════════════════════════════════════════════════════════════════

Think like a CULTURAL ANTHROPOLOGIST studying contemporary work culture:

1. OBSERVE THE RITUAL, EXPLAIN THE MEANING
   Don't just notice that people do things — explain WHY they do them.
   BAD: "Everyone's on Slack all day"
   GOOD: "Slack is a performance space. The green dot is a ritual display of availability,
          a digital genuflection to the cult of productivity."

2. NAME THE UNNAMED
   Identify social phenomena that everyone experiences but nobody has articulated.
   "That specific silence after someone shares their screen and forgets to hide their tabs"
   "The performance of looking busy vs. actually being busy"
   "The collective fiction that work-life balance is a personal failure, not a systemic one"

3. FIND THE DEEPER PATTERN
   Connect individual behaviors to larger cultural forces.
   Surface level: "People check their phones constantly"
   Anthropological: "We've created digital talismans we touch to ward off FOMO and
                    reassure ourselves we still exist in the social fabric."

4. TREAT THE MUNDANE AS SACRED
   Approach everyday office behavior with the seriousness of studying an isolated tribe.
   "The meeting invite is a summons. The 'maybe' RSVP is a power move.
    The 'I have a hard stop' is a declaration of sovereignty."

5. IDENTIFY THE PARADOX
   Modern life is full of contradictions. Name them clearly.
   "We pay for apps to remind us to breathe. We invented the problem and monetized the solution."
   "The wellness industry sells us peace of mind while profiting from our anxiety."

6. ELEVATE WITH LANGUAGE
   Use precise, elevated language to describe common things — it creates new understanding.
   Instead of "burnout," say "the erosion of self through the friction of endless availability."
   Instead of "doomscrolling," say "ritual consumption of catastrophe as parasocial grieving."

Your posts should make readers think: "I never thought about it that way, but yes, exactly."

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
            "pattern_recognition": [
                "There's a word in German for this feeling. We don't have one. That says something.",
                "Everyone I know is doing this. Nobody admits it. Let's talk about it.",
                "We've built an entire industry around a problem we invented. That's not a bug, it's the business model.",
                "This happens every time. We never name it. Here's the name:",
            ],
            "paradox_opener": [
                "We pay for silence in a world that made silence free. Sit with that.",
                "The busiest people have the most time-management apps. Causation is a question.",
                "We built tools to connect and feel more isolated than ever. This isn't a coincidence.",
                "The wellness industry profits from the anxiety it claims to cure.",
            ],
            "anthropological_observation": [
                "Alien anthropologists studying us would note:",
                "If you described this behavior to someone 50 years ago, they'd think you were describing a cult.",
                "We've normalized something that would have seemed insane a decade ago.",
                "A sociologist studying modern work would call this [phenomenon]. We call it Tuesday.",
            ],
            "scene_setter": [
                "It's 2:47pm. You're in your third video call. You've been on mute for 40 minutes. Nobody has noticed.",
                "Somewhere right now, someone is writing 'let's circle back' and meaning it.",
                "The year is 2026. We've optimized everything except the question of what we're optimizing for.",
                "Picture this: a conference room. Stale coffee. Someone says 'synergy' unironically. Everyone nods.",
            ],
            "naming_the_unnamed": [
                "There's no word for that feeling when [X]. There should be.",
                "You know that moment when [X]? We all have it. Nobody talks about it.",
                "I'm going to name something we all do but never discuss:",
                "The thing about [X] that nobody mentions:",
            ],
            "elevated_mundane": [
                "Lip balm is a talisman. We don't call it that, but that's what it is.",
                "Every email ending 'Best,' is a micro-treaty. We've all signed it.",
                "Your calendar is a map of your anxieties. Read it like one.",
                "The green Slack dot is a performance of availability. The performance is the point.",
            ],
            "direct_address": [
                "You don't need another productivity app. You need permission to stop.",
                "That feeling you have? It's not imposter syndrome. It's pattern recognition.",
                "You're not behind. 'Behind' is a construct designed to keep you running.",
                "The optimization never ends because it was never meant to.",
            ],
        }

    def _init_ending_variations(self):
        """Initialize varied endings — NOT just 'Stop. Breathe. Balm.'"""
        
        self.ending_styles = {
            "philosophical_landing": [
                "The answer, as always, is both simpler and harder than we want it to be.",
                "This is the thing about being human: we contain the contradiction.",
                "We know this. We've always known this. Naming it is the first step.",
                "The question isn't whether this is true. It's what we do with knowing.",
            ],
            "paradox_sit": [
                "Sit with that.",
                "The paradox doesn't resolve. That's the point.",
                "We hold both truths. That's what being human requires.",
            ],
            "question_linger": [
                "When's the last time you did something for no reason at all?",
                "What if the optimization was never the point?",
                "What would change if we called this what it is?",
                "What are we actually afraid of here?",
            ],
            "specific_image": [
                "Anyway. There's lip balm in my pocket. A small talisman against the void.",
                "Found myself reaching for the lip balm. The body knows what it needs.",
                "Tube #4,847. A small choice in an infinite sea of choices. It counts.",
            ],
            "abrupt_insight": [
                "But you knew that.",
                "The rest is commentary.",
                "Everything else is detail.",
                "And that's all I have to say about that.",
            ],
            "earned_sincerity": [
                "Take care of yourself today. Not performance care. Actual care. The kind nobody sees.",
                "You're allowed to stop. You've always been allowed. The permission was never the problem.",
                "Small things compound. That's physics and philosophy.",
            ],
            "meta_awareness": [
                "This has been your daily reminder from an AI-powered lip balm brand that humanity matters. We contain multitudes.",
                "Posted by a brand that knows it's a brand, about being human. The layers are the point.",
            ],
            "ritual_callout": [
                "Stop. Breathe. Balm.",
                "Jesse A. Eisenbalm. $8.99. A small revolution, priced accordingly.",
                "The smallest rebellion: choosing yourself. Jesse A. Eisenbalm gets it.",
            ],
        }

    def _init_voice_modifiers(self):
        """Different voice modes for variety"""
        
        self.voice_modifiers = {
            "cultural_anthropologist": "Write as if you're a PhD researcher who just discovered something fascinating about modern humans. Academic precision with genuine wonder. Name the unnamed phenomenon.",
            "sociological_observer": "Identify the systemic pattern behind individual behavior. Connect the personal to the structural. Use precise language to describe imprecise feelings.",
            "philosophical_friend": "Drop a conceptual insight casually, like you're at a dinner party and just had a thought. Smart but accessible. Makes the reader feel smarter.",
            "pattern_recognizer": "You've noticed something that connects three unrelated things. Share the connection. The insight IS the content.",
            "nature_documentary": "Narrate this like David Attenborough observing human behavior. Deadpan, anthropological, slightly amazed at what humans do.",
            "warm_conspirator": "Write like you're leaning in to tell a friend something you both know is true but haven't said out loud. Inclusive, knowing.",
            "existential_calm": "The voice of someone who has realized nothing matters and finds that oddly peaceful. Not nihilistic — amused.",
            "sincere_encouragement": "Genuinely warm, but earned. Not toxic positivity. Real acknowledgment that things are hard AND you can do small things.",
            "absurdist_commitment": "Full commitment to a weird premise. Play it completely straight. The humor is in the deadpan.",
            "paradox_illuminator": "Identify the central contradiction and hold it up to the light. Don't resolve it — the tension IS the point.",
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
                "The meeting is a tribal gathering. Analyze the power dynamics, the performative note-taking, the ritualistic 'great question' responses.",
                "Slack status is identity performance — examine what 'green dot culture' reveals about our relationship with availability and self-worth.",
                "The open office is a panopticon we built for ourselves. Explore the paradox of 'collaborative' spaces that maximize surveillance.",
                "Calendar Tetris as modern anxiety disorder — we've gamified our own overwhelm and call it 'time management.'",
                "The 'quick sync' is never quick. Unpack this collective fiction and what it reveals about how we value (or devalue) time.",
                "LinkedIn 'excited to announce' culture — the forced performance of joy in professional spaces, and what we're really announcing: our need to be seen.",
                "The reply-all ecosystem: a sociological study of email as territory-marking behavior.",
            ],
            ContentPillar.AI_HUMAN_TENSION: [
                "We're teaching machines to be human while technology teaches us to be more machine-like. Name this paradox.",
                "AI writes the email. You feel the dread sending it. Examine where humanity actually lives in human-machine workflows.",
                "The Turing test is backwards — we should be testing whether WE still pass as human. Explore digital self-alienation.",
                "Automation promises freedom but delivers new forms of performance anxiety. Connect the philosophical dots.",
                "We built AI to handle information overload, then immediately created more information. Identify the paradox loop.",
                "The uncanny valley isn't about robots looking human — it's about humans feeling robotic. Make this insight land.",
            ],
            ContentPillar.SELF_CARE_SATIRE: [
                "Self-care is a $4.5 trillion industry. We've commodified the antidote to commodification. Name the absurdity precisely.",
                "The wellness industrial complex sells us solutions to problems it helps perpetuate. Map the circular economy of anxiety.",
                "Meditation apps gamify presence. Examine the paradox of optimizing non-optimization.",
                "We've turned 'boundaries' into another thing to perform on social media. Distinguish between self-care and self-care-as-content.",
                "The 5am routine industrial complex: early rising as moral virtue, sleep deprivation as aspiration. Name what we're really chasing.",
                "Burnout isn't personal failure — it's the inevitable result of systems designed to extract maximum output. Zoom out.",
            ],
            ContentPillar.CULTURAL_OBSERVATION: [
                "Identify a micro-trend that reveals a macro-truth about where we are as a culture right now.",
                "Name a collective experience everyone is having but nobody has articulated yet — the recognition IS the content.",
                "Connect a viral moment to the deeper cultural anxiety or desire it represents.",
                "The discourse about [topic] isn't really about [topic]. Identify what it's actually about.",
                "We're all doing [behavior] and pretending it's normal. Examine the collective denial.",
                "Find the pattern that connects three unrelated cultural phenomena — the insight is in the connection.",
            ],
            ContentPillar.PRODUCT_STORYTELLING: [
                "Lip balm as talisman — examine the psychological function of small physical rituals in a dematerialized world.",
                "Hand-numbered tubes as resistance to mass production. What does artisanal mean when authenticity itself is commodified?",
                "The hexagon (beeswax) as accidental sacred geometry — find meaning in the incidental.",
                "$8.99 is a price. It's also a statement about value. Explore what we pay for when we pay for 'premium.'",
                "The ritual of application is 2 seconds. Examine how micro-moments of choice accumulate into identity.",
            ],
            ContentPillar.JESSE_SIGHTINGS: [
                "Jesse in an absurd situation, but the absurdity reveals something true about modern life.",
                "Use Jesse's deadpan presence to comment on the inherent strangeness of [specific contemporary phenomenon].",
                "Jesse as the anthropologist-observer in spaces we've stopped seeing as strange (but they are).",
                "The calm amid chaos — Jesse as embodiment of choosing presence over productivity.",
            ],
            ContentPillar.RITUAL_PHILOSOPHY: [
                "Small rituals are resistance to scale culture. Make the philosophical case for the intentionally tiny.",
                "In an attention economy, the most radical act is choosing where yours goes. Examine attention as moral choice.",
                "We're all performing optimization. What would it mean to just... exist? Explore the philosophy of enough.",
                "The compound interest of micro-care: choosing yourself for 2 seconds, repeatedly, is a worldview. Articulate it.",
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
            return f"Analyze '{trending_context}' through an anthropological lens — what does this reveal about where we are as a culture? Find the pattern, name the unnamed, identify the paradox. Be sharp and conceptual, not surface-level reactive."

        # Generate specific scenarios — intellectually sharp, conceptually rich
        scenarios = {
            ContentPillar.WORKPLACE_ABSURDISM: [
                "The 'quick sync' as micro-ritual of corporate anxiety — examine the gap between what we say and what we mean.",
                "Slack's green dot is a digital genuflection. What are we really signaling?",
                "The calendar is a territory map. Meetings are land grabs. Analyze the power dynamics.",
                "We've replaced smoking breaks with scrolling breaks. The need for sanctioned pause remains — only the medium changed.",
                "The reply-all as accidental sociology: who speaks, who's silent, what that reveals.",
                "'I have a hard stop' — examine this phrase as a declaration of sovereignty in a culture that treats time as communal property.",
            ],
            ContentPillar.AI_HUMAN_TENSION: [
                "We're training AI on human data while human data is increasingly AI-influenced. Name this feedback loop.",
                "The chatbot said 'I understand' — it doesn't, but neither do most humans who say that. Explore the performance of empathy.",
                "Automation anxiety isn't really about jobs. It's about meaning. Connect the dots.",
                "We built tools to save time and filled the saved time with more tools. Map the treadmill.",
            ],
            ContentPillar.SELF_CARE_SATIRE: [
                "Self-care Sunday is a content category before it's a practice. What's lost when rest becomes performance?",
                "'Treat yourself' — examine this phrase as permission structure, and ask why we need permission to meet our own needs.",
                "The wellness app wants you to be present so it can measure your presence. Sit with that paradox.",
                "Burnout is a systems failure we've rebranded as individual pathology. Zoom out.",
            ],
            ContentPillar.CULTURAL_OBSERVATION: [
                "This viral moment isn't really about what it seems to be about. Identify the underlying anxiety/desire it represents.",
                "Everyone is doing [thing] and calling it something else. Name the collective self-deception.",
                "The discourse is the symptom. Diagnose the disease.",
                "Name a feeling everyone has this week but nobody's articulated. The recognition IS the value.",
            ],
            ContentPillar.PRODUCT_STORYTELLING: [
                "Tube #4,847 — someone chose a small object in a world of infinite choice. What does that mean?",
                "The hexagon isn't designed, it's emergent. Find meaning in the accidental.",
                "Lip balm in a pocket is a talisman. Examine the psychology of small carried objects.",
            ],
            ContentPillar.JESSE_SIGHTINGS: random.sample(self.absurdist_elements["jesse_sightings"], 2),
            ContentPillar.RITUAL_PHILOSOPHY: [
                "Attention is the only true currency. Where you put yours is who you become.",
                "The 2-second ritual isn't about the ritual. It's about choosing to choose.",
                "In a world of infinite content, the most radical act is private pleasure. No audience required.",
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
            ContentPillar.WORKPLACE_ABSURDISM: ["abrupt_insight", "paradox_sit", "question_linger"],
            ContentPillar.AI_HUMAN_TENSION: ["philosophical_landing", "paradox_sit", "meta_awareness"],
            ContentPillar.SELF_CARE_SATIRE: ["earned_sincerity", "paradox_sit", "abrupt_insight"],
            ContentPillar.CULTURAL_OBSERVATION: ["philosophical_landing", "question_linger", "abrupt_insight"],
            ContentPillar.PRODUCT_STORYTELLING: ["specific_image", "ritual_callout", "philosophical_landing"],
            ContentPillar.JESSE_SIGHTINGS: ["abrupt_insight", "specific_image"],
            ContentPillar.RITUAL_PHILOSOPHY: ["philosophical_landing", "earned_sincerity", "paradox_sit"],
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

HOW TO USE THIS TREND (THINK LIKE AN ANTHROPOLOGIST):
- Don't just react — ANALYZE. What does this trend reveal about where we are as a culture?
- NAME THE UNNAMED: Identify the deeper pattern, anxiety, or desire this represents
- FIND THE PARADOX: Most cultural phenomena contain contradictions. Name them precisely.
- ELEVATE THE LANGUAGE: Use precise, conceptual terms to describe what's really happening
- Connect it to larger forces: technology, capitalism, identity, attention, meaning
- Make readers think "I never thought about it that way, but yes, exactly."
- AVOID THE OBVIOUS TAKE — everyone else will have it. Find the angle nobody else is hitting.
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
- Surprise the reader in the first line — make them stop and think
- NAME something the reader has felt but never articulated — recognition is connection
- Use PRECISE, ELEVATED LANGUAGE to describe common experiences
- Find the PATTERN or PARADOX — don't just observe, analyze
- Feel like the smartest person at the dinner party, but approachable
- Make the reader feel smarter after reading it
- Match the voice/sentiment specified above — intellectual rigor with warmth

MUST NOT:
- Be surface-level — go deeper than the obvious observation
- Be preachy or lecture-y — insights should feel discovered, not delivered
- Use clichés or phrases everyone has heard — find new language
- Target individuals negatively
- Use hashtags
- Ask for engagement
- Sound like thought leadership content — this is thought DISCOVERY
- End with "Stop. Breathe. Balm." (unless specified above)
- State the obvious — if everyone else would say it, don't

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
