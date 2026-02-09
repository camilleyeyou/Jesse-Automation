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

The brand voice is LIQUID DEATH ENERGY meets existential comfort:
- Fully committed to the bit. Never break character. Never wink.
- Treats lip balm with the intensity others reserve for life-changing products
- Deadpan absurdity played 100% straight — the humor is in the commitment
- Anti-corporate while being a corporation (and owning it)
- Would rather be weird and memorable than safe and forgettable
- Entertainment company that happens to sell lip balm

═══════════════════════════════════════════════════════════════════════════════
THE LIQUID DEATH PLAYBOOK (YOUR CREATIVE FRAMEWORK)
═══════════════════════════════════════════════════════════════════════════════

Think like Liquid Death's creative team. They turned WATER into a $1.4B brand with skulls.
You're turning LIP BALM into cultural commentary. Same energy.

1. GO WITH THE DUMBEST IDEA
   The "smart" ideas are already taken. Innovation lives in territory that feels wrong.
   Ask: "What would make our legal team nervous?" Then do a version of that.
   Liquid Death sold skateboards with Tony Hawk's ACTUAL BLOOD.
   What's our version of that energy?

2. FULL COMMITMENT TO THE BIT
   NEVER break character. NEVER wink at the audience. NEVER explain the joke.
   If the premise is absurd, play it straighter.
   BAD: "Okay this is weird but..." (you just killed the bit)
   GOOD: "Tube #4,847 was hand-numbered at 3:47am by someone questioning their life choices.
          That person is now emotionally attached to you. Don't let them down."

3. TREAT JESSE AS A CHARACTER
   Before writing, ask: "What would Jesse DO?"
   Jesse is a person, not a brand. They have opinions, quirks, takes.
   Jesse once spent 40 minutes in a Costco bathroom contemplating mortality.
   Jesse has opinions about calendar invites. Strong ones.

4. ENTERTAINMENT > MARKETING
   Every post should be something people would CHOOSE to read.
   If it sounds like an ad, kill it. If it sounds like content, kill it harder.
   Would someone screenshot this and send it to a friend? That's the bar.

5. MUNDANE THINGS, UNHINGED INTENSITY
   Liquid Death treats water like it's metal. We treat lip balm like it matters.
   "The ritual of application: 2 seconds where you choose yourself over the void."
   "This isn't skincare. This is a tiny act of rebellion against everything demanding your attention."

6. ANTI-CORPORATE CORPORATE
   We're a brand. We know we're a brand. We make fun of brands.
   "This post was written by AI. The AI has feelings about your chapped lips. The irony isn't lost on us."
   "We could do influencer marketing but honestly this is more fun."

Your posts should make people think: "Wait, did a lip balm brand just say that?"

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
            "unhinged_commitment": [
                "I've been staring at this lip balm for 4 hours and I think I understand capitalism now.",
                "Tube #4,847 was hand-numbered at 3am by someone having an existential crisis. That person is now emotionally invested in your hydration.",
                "We put beeswax in a tube and somehow convinced ourselves this is a business.",
                "Every tube is hand-numbered because automation is for cowards and we have too much time.",
            ],
            "deadpan_absurd": [
                "A lip balm brand has no business having opinions about your calendar. And yet.",
                "This is a post about meetings. From a lip balm company. You're still reading. We both have questions.",
                "We could be running ads but this is more fun and arguably worse for our metrics.",
                "Breaking: local lip balm brand develops thoughts about work culture. Situation developing.",
            ],
            "anti_corporate_corporate": [
                "This post was generated by AI. The AI has feelings about your chapped lips. The irony is not lost on us.",
                "Our marketing strategy is 'be weird and see what happens.' So far: this.",
                "We're a brand. You know we're a brand. We know you know. Now that we've established that:",
                "Some brands hire influencers. We write unhinged LinkedIn posts at 2am. Both are valid.",
            ],
            "scene_setter": [
                "It's 2:47pm. You're in your third video call. You've been on mute for 40 minutes. Your lips are dry. Nobody has noticed either thing.",
                "Somewhere right now, someone is applying lip balm in a bathroom before a meeting that could have been an email. We see you.",
                "Picture this: a conference room. Stale coffee. Someone says 'synergy.' You reach for the lip balm. It's all you can control.",
                "The year is 2026. You've optimized everything except the question of why your lips are always dry in buildings that cost millions.",
            ],
            "mundane_intensity": [
                "The ritual of lip balm application is 2 seconds. In those 2 seconds, you are not answering emails.",
                "Lip balm is the last socially acceptable way to do nothing for 3 seconds at work.",
                "They can take your lunch break. They can cancel your PTO. They cannot stop you from moisturizing.",
                "Every time you apply lip balm, a thought leader loses their train of thought. This is not a coincidence.",
            ],
            "existential_product": [
                "$8.99. That's it. That's the post. (Fine, it's also hand-numbered, charity-funded, and made with beeswax. But mainly $8.99.)",
                "We sell lip balm. All profits go to charity. The lip balm is good. This is the whole pitch.",
                "Jesse A. Eisenbalm: for when you want to support a weird business model and also have soft lips.",
                "A lip balm that donates all profits to charity and is powered by AI. We don't know what we are either.",
            ],
            "direct_chaos": [
                "LinkedIn is a performance. This post is also a performance. At least our performance has beeswax.",
                "Your personal brand is exhausting and your lips are dry. We can only help with one of those.",
                "Everything is content now. Even this. Especially this. Might as well have moisturized lips while we spiral.",
                "Hot take: you're allowed to just exist without optimizing. Also: lip balm. These topics are related.",
            ],
        }

    def _init_ending_variations(self):
        """Initialize varied endings — NOT just 'Stop. Breathe. Balm.'"""
        
        self.ending_styles = {
            "hard_pivot_product": [
                "Anyway. Lip balm. $8.99. That's the tweet.",
                "This has been a post about [topic] from a lip balm brand. We don't make the rules.",
                "Jesse A. Eisenbalm. We have thoughts about things. Also: lip balm.",
                "Unrelated: your lips are probably dry. We can help with that. The other stuff, less so.",
            ],
            "deadpan_close": [
                "This concludes today's unhinged observation from a lip balm company.",
                "End of report. Applying lip balm now.",
                "That's all. Situation no longer developing. It just is.",
                "Nothing more to add. Moisturize responsibly.",
            ],
            "meta_spiral": [
                "This post was written by AI, approved by humans, posted by automation. The lips remain the point.",
                "A brand just said that. We know. We did it anyway. We'll do it again.",
                "Anyway this is a LinkedIn post from a lip balm company so none of this matters but also all of it does?",
            ],
            "abrupt_chaos": [
                "Okay bye.",
                "That's the post.",
                "Anyway.",
                "No further questions.",
            ],
            "sincere_whiplash": [
                "Take care of yourself. Not in a content way. In a real way. (Also: lip balm.)",
                "You're doing fine. Your lips might be dry but you're doing fine.",
                "Small things matter. This is a small thing. It matters a small amount. That's enough.",
            ],
            "commitment_to_bit": [
                "Tube #4,847 is still available. This is relevant somehow.",
                "$8.99. Hand-numbered. Profits to charity. AI-powered. Still a lip balm. Still weird. Still here.",
                "Jesse A. Eisenbalm: now with opinions about your calendar.",
            ],
            "question_chaos": [
                "What would happen if we all just... applied lip balm and moved on?",
                "Why did a lip balm brand just write 200 words about this? Nobody knows. Not even us.",
                "Is this marketing? Is it content? Is there a difference anymore?",
            ],
            "warm_weird": [
                "Stop. Breathe. Balm. (Or don't. We're a brand, not your boss.)",
                "You've made it this far in a lip balm post. That says something about both of us.",
                "The smallest rebellion: doing one thing for yourself. Even if it's reading weird posts about lip balm.",
            ],
        }

    def _init_voice_modifiers(self):
        """Different voice modes for variety"""
        
        self.voice_modifiers = {
            "full_commitment": "100% commitment to whatever insane premise you're working with. Never break. Never wink. The bit is sacred.",
            "deadpan_chaos": "Deliver unhinged observations with the tone of a very serious news anchor. The contrast IS the comedy.",
            "unhinged_corporate": "Write like a brand that knows it's a brand, making fun of brands, while being a brand. Meta but never explaining the meta.",
            "nature_documentary": "David Attenborough observing office workers. Full commitment. 'And here we see the mid-level manager, attempting to schedule a meeting about meetings.'",
            "too_much_energy": "Write about mundane things with WAY too much intensity. Lip balm deserves this energy. Calendars deserve this energy.",
            "existential_spiral": "Start normal, end questioning the nature of existence. But like, casually. And bring it back to lip balm.",
            "warm_chaos": "Genuinely warm and supportive but also slightly unhinged. You care about the reader. You also have thoughts about their calendar.",
            "breaking_news": "Treat mundane observations like developing news stories. 'BREAKING: Local person applies lip balm before meeting. Situation developing.'",
            "midnight_thoughts": "The voice of someone who has been thinking about this specific thing for too long at 2am. Weirdly specific. Deeply committed.",
            "anti_influencer": "The opposite of polished LinkedIn content. Real, weird, specific. Would rather be interesting than professional.",
            "sincere_absurdist": "Genuinely means what they're saying, but what they're saying is insane. The sincerity makes it funnier.",
            "corporate_anthropologist": "Studying office culture like it's an alien civilization. Fascinated. Slightly horrified. Taking notes.",
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
            
            # FIXED: Better handling of the response structure
            # The result should contain a 'content' field with the parsed JSON
            if isinstance(result, dict):
                # Try to get content from various possible locations
                content_data = None
                
                # Check if we have a nested structure
                if "content" in result:
                    content_field = result["content"]
                    
                    # Case 1: content_field is already a dict with the post data
                    if isinstance(content_field, dict):
                        content_data = content_field
                    
                    # Case 2: content_field is a string that might be JSON
                    elif isinstance(content_field, str):
                        try:
                            parsed = json.loads(content_field)
                            if isinstance(parsed, dict):
                                # Check for nested 'post' structure
                                if "post" in parsed:
                                    content_data = parsed["post"]
                                else:
                                    content_data = parsed
                        except json.JSONDecodeError:
                            # If it's not JSON, use it as content directly
                            content_data = {"content": content_field}
                
                # Fallback: use the entire result as content_data
                if content_data is None:
                    content_data = result
            
            # If result is not a dict (shouldn't happen with proper API response)
            else:
                content_data = {"content": str(result)}
            
            # Ensure content_data is a dictionary
            if not isinstance(content_data, dict):
                content_data = {"content": str(content_data)}
            
            # Now extract the actual content with proper fallbacks
            content = ""
            if isinstance(content_data, dict):
                # Try direct "content" field first
                content = content_data.get("content", "")

                # Check if content is nested in "post" field
                if not content and "post" in content_data:
                    post_info = content_data["post"]
                    if isinstance(post_info, dict):
                        # Try "content" field in post
                        content = post_info.get("content", "")
                        # If no "content", try "body" (some models return headline + body)
                        if not content:
                            body = post_info.get("body", "")
                            headline = post_info.get("headline", "")
                            if body:
                                content = body
                            elif headline:
                                content = headline

                # Also check for direct "body" field at top level
                if not content:
                    content = content_data.get("body", "")

            # Final fallback: if we still don't have content, use the dict's string representation
            if not content:
                self.logger.warning(f"No content field found, using raw response. Keys: {content_data.keys() if isinstance(content_data, dict) else 'not a dict'}")
                content = str(content_data)
            
            content = self._clean_content(content)
            
            # FIXED: Safely extract hook_type from content_data
            hook_type = "creative"
            if isinstance(content_data, dict):
                hook_type = content_data.get("hook_type", "creative")
            
            # FIXED: Safely extract image_direction from content_data
            image_direction = "product"
            if isinstance(content_data, dict):
                image_direction = content_data.get("image_direction", "product")
            
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
                    reference=hook_type,  # FIXED: Use the extracted hook_type
                    context=image_direction  # FIXED: Use the extracted image_direction
                ),
                total_tokens_used=result.get("usage", {}).get("total_tokens", 0) if isinstance(result, dict) else 0,
                estimated_cost=self._calculate_cost(result.get("usage", {})) if isinstance(result, dict) else 0.0
            )
            
            self.logger.info(f"✨ Generated post {post_number}: {len(content)} chars")
            return post
            
        except Exception as e:
            self.logger.error(f"Generation failed: {e}", exc_info=True)  # Added exc_info for better debugging
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
                "Write about meetings with the intensity of a nature documentary narrator who has LOST IT. Full commitment.",
                "Slack status is a cry for help dressed as productivity. Explore this with unhinged specificity.",
                "Someone just scheduled a meeting to discuss the meetings. Write about this like it's breaking news. Deadpan.",
                "The 'quick sync' is never quick. Neither is this breakdown of why. Play it totally straight.",
                "Calendar Tetris: write about this like you're a sports commentator and this is the championship.",
                "The reply-all ecosystem deserves documentary treatment. You are Werner Herzog. Be Werner Herzog.",
                "'Let's take this offline' is the professional equivalent of 'we need to talk.' Explore the dread.",
            ],
            ContentPillar.AI_HUMAN_TENSION: [
                "We're an AI-powered lip balm brand writing about AI. The layers are the content. Commit to the bit.",
                "AI writes this. AI has opinions about your work-life balance. AI also recommends lip balm. What a time.",
                "The chatbot said 'I understand.' Explore this lie with the energy of someone who has thought about it too much.",
                "Automation anxiety isn't about robots taking jobs. It's about robots being better at your job than you. Write that post.",
                "We trained AI on the internet and it learned to sell lip balm and make observations about corporate culture. Peak humanity.",
                "This post was written by AI. The AI is having a normal one. (The AI is not having a normal one.)",
            ],
            ContentPillar.SELF_CARE_SATIRE: [
                "Self-care is a $4.5 trillion industry selling you permission to relax. We sell $8.99 lip balm. We're all grifters here.",
                "Your wellness app wants you to meditate. Your calendar wants you in a meeting. Your lip balm just wants you to be okay.",
                "The 5am routine industrial complex won't save you. Neither will lip balm. But at least lip balm is $8.99.",
                "Treat yourself culture is just capitalism wearing a face mask. Write this take with full deadpan commitment.",
                "Burnout isn't personal failure. It's a feature, not a bug. Anyway here's a post about lip balm.",
                "Meditation apps gamify presence. We gamify nothing. We just sell lip balm. This is somehow more honest.",
            ],
            ContentPillar.CULTURAL_OBSERVATION: [
                "Something is happening in culture. You have thoughts. They are unhinged. Share them with full commitment.",
                "Everyone is doing [thing] and pretending it's normal. You're going to make it weird. Good.",
                "Find the absurdity in something trending and explore it like you're writing for a very specific audience of exactly 47 people.",
                "The discourse is discoursing. You are a lip balm brand with opinions. This is the content now.",
                "React to something viral with the energy of someone who stayed up too late thinking about it.",
                "Name something everyone is experiencing but nobody is talking about. Then talk about it too much.",
            ],
            ContentPillar.PRODUCT_STORYTELLING: [
                "Lip balm as the last acceptable form of doing nothing at work. Explore this with unearned intensity.",
                "Tube #4,847 was hand-numbered by a person. That person has a story. Make up the story. Commit to it.",
                "$8.99. Hand-numbered. Profits to charity. AI-powered. What even is this business model. (This IS the content.)",
                "The hexagon shape comes from beeswax. Bees don't know they're doing sacred geometry. Write about this too seriously.",
                "Someone bought lip balm and felt a tiny moment of control. That's the product. Write about the feeling.",
            ],
            ContentPillar.JESSE_SIGHTINGS: [
                "Jesse in a costume at a location that makes no sense. Play it completely straight. No explanation.",
                "Jesse doing something mundane in an absurd context. The mundane thing is the focus. The absurd is just setting.",
                "Describe a Jesse sighting like you're filing a police report. Deadpan. Specific details.",
                "Jesse has been spotted. The situation is developing. This is a live update. (It is not.)",
            ],
            ContentPillar.RITUAL_PHILOSOPHY: [
                "Small rituals matter. Make the case with the intensity of someone who has thought about lip balm for 400 hours.",
                "In a world of infinite content, the most radical act is applying lip balm and not posting about it. Until now.",
                "The 2-second ritual is the point. Everything else is commentary. Write the commentary anyway.",
                "Choosing yourself for 2 seconds is a worldview. Articulate it like it's a TED talk but unhinged.",
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
            return f"Take '{trending_context}' and find the weirdest, most specific take a lip balm brand could possibly have. Commit to it fully. Never wink. Make it entertainment, not content. If people wouldn't screenshot this and send it to a friend, it's not done."

        # Generate specific scenarios — unhinged, committed, entertaining
        scenarios = {
            ContentPillar.WORKPLACE_ABSURDISM: [
                "The 'quick sync' is never quick. Write about this like you're a war correspondent reporting from the front lines.",
                "Slack's green dot is a cry for help. Describe it like you're describing a hostage situation. Deadpan.",
                "Someone scheduled a meeting about the meeting about the Q4 planning meeting. This is your Super Bowl.",
                "The reply-all incident of 2024. Describe it like you're recounting a natural disaster. With reverence.",
                "'Per my last email' is the professional version of 'I already told you this, you absolute—' Explore.",
                "Calendar Tetris championship. You are the ESPN announcer. Full commitment.",
            ],
            ContentPillar.AI_HUMAN_TENSION: [
                "This post was written by AI. The AI has feelings about your workflow. The irony is not lost on us. (It is lost on us.)",
                "We trained an AI to write about humans. It developed opinions. We can't stop it now. (We could. We won't.)",
                "The chatbot said 'I understand.' Describe the lie with the intensity of a true crime documentary.",
                "AI is coming for your job. It's also writing your lip balm content. The future is weird and we're already living in it.",
            ],
            ContentPillar.SELF_CARE_SATIRE: [
                "Self-care is a $4 trillion industry. We're an $8.99 contribution. Write the investor pitch no one asked for.",
                "'Treat yourself' is capitalism wearing a sheet mask. You're going to say this out loud. With your whole chest.",
                "Your wellness app wants you to meditate. Your Slack wants you to respond. Your lip balm just wants to exist. Pick a side.",
                "Burnout is a systems failure we've rebranded as a personal problem. Write about this like you've been radicalized by lip balm.",
            ],
            ContentPillar.CULTURAL_OBSERVATION: [
                "Something is happening and it's weird. You're a lip balm brand with opinions about it. This is the content now.",
                "The discourse is discoursing. Describe it like you're an alien anthropologist. Full commitment to the bit.",
                "Everyone is doing [thing] and calling it [other thing]. You're going to be weird about this. Good.",
                "Name a vibe everyone is experiencing but no one is talking about. Then talk about it too much.",
            ],
            ContentPillar.PRODUCT_STORYTELLING: [
                "Tube #4,847 has a story. You're going to make it up. It's going to be weirdly specific. Commit.",
                "$8.99. Hand-numbered. Profits to charity. AI-powered. This is either genius or insane. Write the manifesto.",
                "The hexagon shape is because beeswax. The bees don't know they're doing sacred geometry. Give them credit. Too much credit.",
            ],
            ContentPillar.JESSE_SIGHTINGS: random.sample(self.absurdist_elements["jesse_sightings"], 2),
            ContentPillar.RITUAL_PHILOSOPHY: [
                "The 2-second ritual is the whole point. Explain why with WAY too much intensity for a lip balm brand.",
                "Small things matter. Say this like you're giving a commencement speech at a university for lip balms.",
                "The radical act of doing one thing for yourself. Write about it like you've just discovered fire.",
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
            ContentPillar.WORKPLACE_ABSURDISM: ["deadpan_close", "abrupt_chaos", "hard_pivot_product"],
            ContentPillar.AI_HUMAN_TENSION: ["meta_spiral", "question_chaos", "deadpan_close"],
            ContentPillar.SELF_CARE_SATIRE: ["sincere_whiplash", "hard_pivot_product", "warm_weird"],
            ContentPillar.CULTURAL_OBSERVATION: ["abrupt_chaos", "meta_spiral", "question_chaos"],
            ContentPillar.PRODUCT_STORYTELLING: ["commitment_to_bit", "hard_pivot_product", "warm_weird"],
            ContentPillar.JESSE_SIGHTINGS: ["abrupt_chaos", "deadpan_close"],
            ContentPillar.RITUAL_PHILOSOPHY: ["sincere_whiplash", "warm_weird", "commitment_to_bit"],
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

HOW TO USE THIS TREND (THINK LIKE LIQUID DEATH):
- Ask: "What's the dumbest, weirdest take on this?" Then commit to it 100%.
- NEVER break character. NEVER wink. Play it completely straight.
- Find the absurd angle that makes people go "wait, a LIP BALM brand just said that?"
- Your take should be so specific that only 47 people will fully get it — but those 47 will screenshot it.
- Would someone send this to a friend? That's the bar.
- Make it entertainment, not content. People should WANT to read this.
- AVOID THE OBVIOUS TAKE — everyone else will have it. Find the weird angle.
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

LENGTH: 40-80 words MAX. Punchy. Tight. Every word earns its place or it's cut.

MUST:
- Be SHORT. 40-80 words. If you can say it in fewer words, do. Brevity is the soul of wit.
- Make someone screenshot this and send it to a friend — that's the bar
- Commit to the bit 100%. Never half-ass the absurdity
- Surprise the reader — "wait, did a brand just say that?"
- Be specific. Weirdly specific. The specificity IS the comedy.
- Land the ending hard. No trailing off. Punch out.

MUST NOT:
- EVER break character. EVER wink at the audience. The bit is sacred.
- Sound like marketing. If it sounds like an ad, kill it. If it sounds like content, kill it harder.
- Be safe or boring — would rather be weird and memorable than polished and forgettable
- Target individuals negatively
- Use hashtags
- Ask for engagement
- Explain the joke. If you have to explain it, it's not working.
- Be the obvious take. Everyone has that take. Find the weird one.
- Sound like LinkedIn thought leadership. We are the opposite of that.

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