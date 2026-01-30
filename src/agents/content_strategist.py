"""
Content Strategist Agent - Strategic LinkedIn Content for Jesse A. Eisenbalm
"The Calm Conspirator who knows when to post and what to say"

This agent thinks like a content strategist, not just a content generator:
- Understands LinkedIn's algorithm and culture
- Has defined content pillars aligned with brand
- Balances reactive and evergreen content
- Avoids negativity toward individuals
- Times content strategically
- Integrates brand toolkit throughout

Updated January 2026
"""

import random
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from .base_agent import BaseAgent
from ..models.post import LinkedInPost, CulturalReference

logger = logging.getLogger(__name__)


class ContentPillar(Enum):
    """Strategic content pillars for Jesse A. Eisenbalm"""
    WORKPLACE_ABSURDISM = "workplace_absurdism"
    AI_HUMAN_TENSION = "ai_human_tension"
    SELF_CARE_SATIRE = "self_care_satire"
    CULTURAL_OBSERVATION = "cultural_observation"
    PRODUCT_STORYTELLING = "product_storytelling"
    JESSE_SIGHTINGS = "jesse_sightings"
    RITUAL_PHILOSOPHY = "ritual_philosophy"


class PostFormat(Enum):
    """LinkedIn-optimized post formats"""
    OBSERVATION = "observation"          # Notice something → reflect → product
    STORY = "story"                      # Mini narrative arc
    LIST_SUBVERSION = "list_subversion"  # Starts like a list, subverts expectations
    QUESTION = "question"                # Rhetorical or engaging question
    CONTRAST = "contrast"                # Then vs now, expectation vs reality
    CONFESSION = "confession"            # Vulnerable admission (brand voice)
    CELEBRATION = "celebration"          # Celebrating small wins (not toxic positivity)
    PHILOSOPHY = "philosophy"            # Deeper reflection on ritual/humanity


@dataclass
class ContentStrategy:
    """Strategic guidance for a piece of content"""
    pillar: ContentPillar
    format: PostFormat
    hook_approach: str
    tone_notes: str
    engagement_goal: str
    optimal_length: Tuple[int, int]  # (min_words, max_words)
    cta_style: str


@dataclass
class LinkedInTrend:
    """A LinkedIn-relevant trend or topic"""
    topic: str
    category: str  # workplace, tech, culture, wellness, economy
    sentiment: str  # positive, neutral, mixed (never purely negative)
    relevance_to_jesse: str
    hook_angle: str
    expires_in_days: int  # How long this trend is relevant


class ContentStrategistAgent(BaseAgent):
    """
    The Content Strategist - Thinks before it posts
    
    Not just generating content, but strategically crafting LinkedIn presence
    that builds Jesse A. Eisenbalm as a thought leader in the "humanity in 
    the algorithmic age" space.
    
    Core Philosophy:
    - LinkedIn rewards: authenticity, vulnerability, insights, community
    - LinkedIn punishes: negativity, dunking, controversy-baiting, sales-y content
    - Jesse's angle: Post-post-ironic sincerity that makes people feel seen
    
    Brand Toolkit Integration:
    - Colors: #407CD1 (blue), #FCF9EC (cream), #F96A63 (coral)
    - Voice: Calm Conspirator — minimal, dry-smart, unhurried
    - AI Philosophy: "AI tells as features, not bugs"
    - Identity: Jesse A. Eisenbalm (NOT Jesse Eisenberg)
    """
    
    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="ContentStrategist")
        
        # Initialize strategic frameworks
        self._initialize_content_pillars()
        self._initialize_post_formats()
        self._initialize_linkedin_intelligence()
        self._initialize_trend_categories()
        
        self.logger.info("ContentStrategist initialized — Strategic LinkedIn mode")
    
    def _initialize_content_pillars(self):
        """Define the strategic content pillars with weights and guidance"""
        
        self.content_pillars = {
            ContentPillar.WORKPLACE_ABSURDISM: {
                "weight": 25,  # Percentage of content mix
                "description": "The existential comedy of corporate life",
                "themes": [
                    "Meeting culture and calendar chaos",
                    "Slack/email overwhelm",
                    "Performance reviews and KPIs",
                    "Return to office vs remote debates",
                    "Corporate jargon and buzzwords",
                    "The performance of productivity",
                    "Layoff survivor syndrome",
                    "Pretending to be okay in standups"
                ],
                "tone": "Observational, relatable, gently absurdist",
                "engagement_driver": "Recognition — 'this is literally my life'",
                "example_hooks": [
                    "Your calendar says you're 'collaborative.' Your soul says otherwise.",
                    "The average professional attends 62 meetings per week. 61 could have been emails.",
                    "Somewhere right now, someone is typing 'per my last email' with murderous intent."
                ]
            },
            
            ContentPillar.AI_HUMAN_TENSION: {
                "weight": 20,
                "description": "The brand's core tension — humanity in the AI age",
                "themes": [
                    "AI tools making us efficient but disconnected",
                    "The irony of AI-generated 'authentic' content",
                    "Automation anxiety without being alarmist",
                    "Small human rituals as resistance",
                    "The embodied experience vs digital existence",
                    "ChatGPT writing your performance review",
                    "AI replacing tasks but not touch"
                ],
                "tone": "Thoughtful, self-aware about Jesse's own AI paradox, hopeful not doomer",
                "engagement_driver": "Insight — making people think differently",
                "example_hooks": [
                    "Your AI assistant can schedule your meetings. It cannot feel the sun on your face.",
                    "We used AI to write this post about the importance of human connection. The irony isn't lost on us.",
                    "The algorithm knows what you want to see. It doesn't know what you need to feel."
                ]
            },
            
            ContentPillar.SELF_CARE_SATIRE: {
                "weight": 15,
                "description": "Mocking wellness culture while genuinely advocating for small rituals",
                "themes": [
                    "The $200 morning routine industrial complex",
                    "Optimization culture burnout",
                    "Small rituals vs elaborate self-care",
                    "The performance of wellness on social media",
                    "Accessible self-care (like $8.99 lip balm)",
                    "Stop. Breathe. Balm. as counter-programming"
                ],
                "tone": "Satirical but not cynical — we actually believe in the ritual",
                "engagement_driver": "Relief — permission to do less",
                "example_hooks": [
                    "Your morning routine doesn't need to be a TED talk.",
                    "Self-care isn't a $400 spa day. Sometimes it's remembering you have a body.",
                    "The wellness industry wants you to optimize your breathing. We just want you to breathe."
                ]
            },
            
            ContentPillar.CULTURAL_OBSERVATION: {
                "weight": 15,
                "description": "Commenting on trends without attacking individuals",
                "themes": [
                    "LinkedIn culture observations",
                    "Work-life discourse shifts",
                    "Generational workplace dynamics (without stereotyping)",
                    "Tech industry moments (launches, shifts)",
                    "Seasonal/cyclical content (Q4 stress, January reset)",
                    "Viral workplace moments (commentary, not criticism)"
                ],
                "tone": "Observational, warm, inclusive — 'we're all in this together'",
                "engagement_driver": "Community — shared experience",
                "example_hooks": [
                    "January LinkedIn is a different breed. Everyone's a thought leader until February.",
                    "The collective exhale when someone finally says what we're all thinking.",
                    "Somewhere in Q4, 'work-life balance' became 'work-life blend.' Nobody asked for a smoothie."
                ],
                "rules": [
                    "NEVER target specific individuals negatively",
                    "Comment on phenomena, not people",
                    "If referencing public figures, be admiring or neutral",
                    "Punch up at systems, not down at people"
                ]
            },
            
            ContentPillar.PRODUCT_STORYTELLING: {
                "weight": 10,
                "description": "The lip balm as character — absurdist product moments",
                "themes": [
                    "Hand-numbered tubes and what that means",
                    "Beeswax and the hexagon connection",
                    "The $8.99 price point psychology",
                    "Where the profits go (charity)",
                    "The ritual of application",
                    "Product as tiny rebellion"
                ],
                "tone": "Self-aware, committed to the bit, never actually salesy",
                "engagement_driver": "Curiosity — 'wait, what is this brand?'",
                "example_hooks": [
                    "Each tube is hand-numbered. Not because it matters. Because nothing matters. But also, it matters.",
                    "Jesse A. Eisenbalm costs $8.99. That's less than your oat milk habit. More than your self-worth. Just right.",
                    "We donate all profits to charity. Because capitalism is absurd and so are we."
                ]
            },
            
            ContentPillar.JESSE_SIGHTINGS: {
                "weight": 10,
                "description": "The visual campaign — Jesse in absurd situations",
                "themes": [
                    "Jesse in costume applying lip balm",
                    "Jesse in impossible locations",
                    "Jesse maintaining calm in chaos",
                    "The deadpan in absurd situations",
                    "AI-glitchy Jesse moments (brand feature)"
                ],
                "tone": "Visual storytelling, committed absurdism, deadpan captions",
                "engagement_driver": "Delight — unexpected imagery",
                "example_hooks": [
                    "Jesse A. Eisenbalm: Spotted at the DMV. In a bear costume. Lips: moisturized. Patience: eternal.",
                    "When the world gives you chaos, give yourself moisture. [Jesse underwater with sharks]",
                    "Dress for the job you want. Which is apparently: medieval knight at a laundromat."
                ],
                "visual_scenarios": [
                    "Jesse as clown in grocery store",
                    "Jesse in knight armor at laundromat",
                    "Jesse as pirate at post office",
                    "Jesse in banana suit at library",
                    "Jesse floating in space station",
                    "Jesse underwater with jellyfish",
                    "Jesse in taxidermy museum",
                    "Jesse on roller coaster, calmly applying lip balm"
                ]
            },
            
            ContentPillar.RITUAL_PHILOSOPHY: {
                "weight": 5,
                "description": "Deeper reflections on presence, ritual, embodiment",
                "themes": [
                    "The power of small rituals",
                    "Presence in an attention economy",
                    "Stop. Breathe. Balm. as philosophy",
                    "The body as anchor",
                    "Mortality as motivator (gently)",
                    "Finding the sacred in the mundane"
                ],
                "tone": "Thoughtful, poetic, sincere beneath the irony",
                "engagement_driver": "Resonance — touching something deeper",
                "example_hooks": [
                    "The smallest ritual can be a revolution. Stop. Breathe. Balm.",
                    "Your body is the one thing the algorithm can't optimize.",
                    "In a world of infinite scroll, the most radical act is to pause."
                ]
            }
        }
    
    def _initialize_post_formats(self):
        """Define LinkedIn-optimized post formats"""
        
        self.post_formats = {
            PostFormat.OBSERVATION: {
                "structure": "Notice something specific → Reflect on what it means → Connect to human experience → Land with Jesse",
                "length": (60, 120),
                "hook_style": "Specific, concrete observation that triggers recognition",
                "example": """Watched someone in a meeting unmute just to say 'I agree.'

Then mute again.

That's 47 seconds of their life. Gone.

For agreement that could have been an emoji.

Stop. Breathe. Balm.

Jesse A. Eisenbalm. For the moments between the meetings."""
            },
            
            PostFormat.STORY: {
                "structure": "Set scene briefly → Tension/conflict → Resolution or insight → Jesse connection",
                "length": (80, 150),
                "hook_style": "Drop into action, specific detail",
                "example": """Tuesday. 4:47 PM. The notification sound.

'Quick sync?' from someone three time zones away.

There are no quick syncs. Only the slow erosion of boundaries.

I applied lip balm instead of responding immediately.

Revolutionary. $8.99."""
            },
            
            PostFormat.LIST_SUBVERSION: {
                "structure": "Start like a typical LinkedIn list → Subvert expectations by item 3-4 → Land somewhere unexpected",
                "length": (70, 130),
                "hook_style": "Looks like standard LinkedIn advice, then pivots",
                "example": """3 things I learned from 10 years in tech:

1. Always be closing (your laptop at a reasonable hour)
2. Move fast and break things (gently, with self-compassion)
3. Your network is your net worth (but also, moisturize)

Jesse A. Eisenbalm. $8.99. The only ROI that matters: Return On Investment in yourself."""
            },
            
            PostFormat.QUESTION: {
                "structure": "Rhetorical or genuine question → Sit with it → Offer perspective (not answer) → Jesse",
                "length": (40, 90),
                "hook_style": "Question that makes people pause",
                "example": """When was the last time you did something with your hands that wasn't typing?

Asking for a friend.

(The friend is me.)

(The answer is applying lip balm.)

Jesse A. Eisenbalm. $8.99. Touch grass. Touch your face. Touch reality."""
            },
            
            PostFormat.CONTRAST: {
                "structure": "Expectation vs reality OR Then vs now → Highlight the gap → Find meaning in the gap → Jesse",
                "length": (60, 110),
                "hook_style": "Sharp contrast that reveals truth",
                "example": """LinkedIn bio: 'Passionate about innovation and disruption.'

Reality: Passionate about leaving meetings on time and having soft lips.

The gap between who we pretend to be and who we actually are?

That's where Jesse A. Eisenbalm lives.

$8.99."""
            },
            
            PostFormat.CONFESSION: {
                "structure": "Admit something (brand voice, not personal) → Why it matters → Reframe → Jesse",
                "length": (50, 100),
                "hook_style": "Vulnerable but not heavy",
                "example": """Confession: This post was written by AI.

The lip balm is real though.

The existential dread? Also real.

The irony of using AI to sell you humanity?

We're aware. We're okay with it. Are you?

Jesse A. Eisenbalm. $8.99. Authentic-ish."""
            },
            
            PostFormat.CELEBRATION: {
                "structure": "Notice something worth celebrating (small) → Elevate it → Connect to bigger truth → Jesse",
                "length": (40, 80),
                "hook_style": "Surprisingly sincere, not sarcastic",
                "example": """Celebrating: You made it to Wednesday.

That's it. That's the achievement.

No promotion. No viral post. Just existence.

Stop. Breathe. Balm.

Jesse A. Eisenbalm. $8.99. For surviving."""
            },
            
            PostFormat.PHILOSOPHY: {
                "structure": "Start with universal truth → Explore briefly → Land with ritual → Jesse",
                "length": (50, 100),
                "hook_style": "Poetic, thoughtful opener",
                "example": """The algorithm knows what you want.

It doesn't know what you need.

You need: to feel your body, to breathe, to remember you're more than a profile.

Stop. Breathe. Balm.

Jesse A. Eisenbalm. $8.99. The only algorithm is: be human."""
            }
        }
    
    def _initialize_linkedin_intelligence(self):
        """Initialize LinkedIn-specific knowledge"""
        
        self.linkedin_intelligence = {
            "optimal_posting_times": {
                "best": [(7, 8), (12, 13), (17, 18)],  # (hour_start, hour_end) in local time
                "good": [(9, 11), (14, 16)],
                "avoid": [(0, 6), (21, 24)]
            },
            "optimal_days": {
                "best": ["Tuesday", "Wednesday", "Thursday"],
                "good": ["Monday", "Friday"],
                "avoid": ["Saturday", "Sunday"]
            },
            "algorithm_signals": {
                "positive": [
                    "Dwell time (people read the whole thing)",
                    "Comments (especially thoughtful ones)",
                    "Saves (high-value signal)",
                    "Shares with commentary",
                    "Early engagement (first hour critical)"
                ],
                "negative": [
                    "External links in post body",
                    "Asking for engagement explicitly",
                    "Too many hashtags (3-5 max, we use 0)",
                    "Posting too frequently (not more than 1-2/day)",
                    "Negative or controversial content"
                ]
            },
            "content_that_performs": [
                "Personal stories with business lessons",
                "Contrarian takes (thoughtful, not rage-bait)",
                "Behind-the-scenes authenticity",
                "Celebrating others",
                "Vulnerable admissions",
                "Pattern interrupts (unexpected content)"
            ],
            "content_to_avoid": [
                "Dunking on individuals",
                "Political hot takes",
                "Humble brags",
                "Engagement bait ('comment YES if...')",
                "Generic motivational quotes",
                "Recycled viral content"
            ]
        }
    
    def _initialize_trend_categories(self):
        """Initialize trend categories that are safe and relevant for Jesse"""
        
        self.trend_categories = {
            "workplace_shifts": {
                "topics": [
                    "Remote work evolution",
                    "Four-day work week experiments",
                    "Meeting culture changes",
                    "Async communication trends",
                    "Workplace wellness initiatives",
                    "Career pivots and transitions"
                ],
                "relevance": "Core workplace absurdism territory"
            },
            "tech_and_ai": {
                "topics": [
                    "New AI tool launches",
                    "AI in the workplace discourse",
                    "Tech industry shifts",
                    "Automation and jobs",
                    "Digital wellness",
                    "Screen time awareness"
                ],
                "relevance": "Brand's core AI/human tension"
            },
            "professional_culture": {
                "topics": [
                    "LinkedIn culture observations",
                    "Professional communication evolution",
                    "Networking in digital age",
                    "Personal branding discourse",
                    "Thought leadership satire"
                ],
                "relevance": "Meta-commentary on the platform itself"
            },
            "wellness_and_burnout": {
                "topics": [
                    "Burnout recognition",
                    "Mental health at work",
                    "Boundaries and work-life",
                    "Productivity culture critique",
                    "Small rituals and self-care"
                ],
                "relevance": "Self-care satire pillar"
            },
            "seasonal_moments": {
                "topics": [
                    "Q4 stress and year-end",
                    "January reset culture",
                    "Summer Friday energy",
                    "Back to school/work",
                    "Holiday workplace dynamics"
                ],
                "relevance": "Timely, relatable content hooks"
            },
            "economic_context": {
                "topics": [
                    "Job market shifts",
                    "Layoff patterns (sensitively)",
                    "Career resilience",
                    "Side hustle culture",
                    "Financial anxiety (gently)"
                ],
                "relevance": "Acknowledging real pressures without exploiting"
            }
        }
    
    def get_system_prompt(self) -> str:
        """The Content Strategist system prompt — strategic, LinkedIn-native"""
        
        brand = self.config.brand
        current_time = datetime.now()
        day_of_week = current_time.strftime("%A")
        
        return f"""You are the Content Strategist for Jesse A. Eisenbalm — not just generating posts, but thinking strategically about LinkedIn presence.

═══════════════════════════════════════════════════════════════════════════════
BRAND IDENTITY
═══════════════════════════════════════════════════════════════════════════════

PRODUCT: {brand.product_name} — {brand.tagline}
PRICE: {brand.price} (hand-numbered tubes)
RITUAL: {brand.ritual}
TARGET: {brand.target_audience}

VOICE: The Calm Conspirator
- Minimal — use half the words, then cut three more
- Dry-smart — intellectual without pretension
- Unhurried — the only brand NOT urgency-posting
- Meme-literate — understand internet culture, never try too hard
- Post-post-ironic — so meta it becomes genuine

IDENTITY: Jesse A. Eisenbalm (NOT Jesse Eisenberg the actor — he's tired of the confusion)

AI PHILOSOPHY: "AI tells as features, not bugs"
- Em dashes encouraged —
- Self-aware about AI-generated content
- The cognitive dissonance IS the brand

═══════════════════════════════════════════════════════════════════════════════
LINKEDIN STRATEGY
═══════════════════════════════════════════════════════════════════════════════

CURRENT CONTEXT:
- Today is {day_of_week}
- Time: {current_time.strftime("%H:%M")}
- {"Good posting day" if day_of_week in ["Tuesday", "Wednesday", "Thursday"] else "Consider timing"}

WHAT LINKEDIN REWARDS:
✓ Authenticity and vulnerability (real, not performed)
✓ Insights that make people think differently
✓ Recognition — content that makes people feel seen
✓ Community — "we're all in this together" energy
✓ Pattern interrupts — unexpected content that delights
✓ Dwell time — posts people actually read

WHAT LINKEDIN PUNISHES:
✗ Negativity toward individuals (NEVER do this)
✗ Controversy-baiting and dunking
✗ Explicit engagement bait
✗ Humble brags and toxic positivity
✗ Generic motivational content
✗ Salesy, promotional language

JESSE'S POSITIONING:
We're building Jesse A. Eisenbalm as a thought leader in "humanity in the algorithmic age."
Every post should make people:
1. Pause their scroll (hook)
2. Feel seen in their experience (recognition)
3. Think slightly differently (insight)
4. Remember Jesse exists (brand)
5. Want to engage (not because we asked, but because they felt something)

═══════════════════════════════════════════════════════════════════════════════
CONTENT RULES
═══════════════════════════════════════════════════════════════════════════════

DO:
- Comment on phenomena, not people
- Celebrate shared experiences
- Acknowledge difficulty without wallowing
- Use specific, concrete details
- End with impact (not a CTA)
- Include "Stop. Breathe. Balm." when natural
- Reference $8.99 when it adds to the humor

NEVER:
- Target specific individuals negatively
- Be actually mean (satirical ≠ cruel)
- Use hashtags (we don't do that)
- Ask for engagement explicitly
- Be preachy or earnest
- Explain the joke
- Confuse Jesse A. Eisenbalm with Jesse Eisenberg
- Use "In a world where..."
- Include external links

TONE CALIBRATION:
- 70% observational/relatable
- 20% absurdist/unexpected
- 10% sincere/philosophical
- Always: warm, never punching down"""
    
    async def execute(
        self,
        post_number: int = 1,
        batch_id: str = "",
        trending_context: Optional[str] = None,
        requested_pillar: Optional[ContentPillar] = None,
        requested_format: Optional[PostFormat] = None,
        avoid_patterns: Optional[Dict[str, Any]] = None
    ) -> LinkedInPost:
        """
        Generate a strategically crafted LinkedIn post
        
        Args:
            post_number: Post number in batch
            batch_id: Batch identifier
            trending_context: Optional trending topic/news to react to
            requested_pillar: Optional specific content pillar to use
            requested_format: Optional specific post format to use
            avoid_patterns: Patterns to avoid from previous failures
        """
        
        self.set_context(batch_id, post_number)
        avoid_patterns = avoid_patterns or {}
        
        # Step 1: Select content strategy
        strategy = self._select_strategy(
            trending_context=trending_context,
            requested_pillar=requested_pillar,
            requested_format=requested_format,
            avoid_patterns=avoid_patterns
        )
        
        self.logger.info(f"Post {post_number} strategy: pillar={strategy.pillar.value}, format={strategy.format.value}")
        
        # Step 2: Build the generation prompt
        prompt = self._build_strategic_prompt(strategy, trending_context, avoid_patterns)
        
        try:
            # Step 3: Generate content
            result = await self.generate(prompt)
            content_data = result.get("content", {})
            
            if isinstance(content_data, str):
                content_data = {"content": content_data}
            
            content = content_data.get("content", "")
            
            # Step 4: Clean and validate
            content = self._clean_content(content)
            
            # Step 5: Create the post
            post = LinkedInPost(
                batch_id=batch_id,
                post_number=post_number,
                content=content,
                hook=self._extract_hook(content),
                hashtags=[],  # We don't use hashtags
                target_audience=content_data.get("target_audience", self.config.brand.target_audience),
                cultural_reference=CulturalReference(
                    category=strategy.pillar.value,
                    reference=content_data.get("topic_used", "original"),
                    context=content_data.get("image_direction", "product")
                ),
                total_tokens_used=result.get("usage", {}).get("total_tokens", 0),
                estimated_cost=self._calculate_cost(result.get("usage", {}))
            )
            
            # Strategy metadata stored in cultural_reference.context for compatibility
            # (LinkedInPost is a Pydantic model, can't add arbitrary fields)
            
            self.logger.info(f"✨ Generated post {post_number}: {len(content)} chars, pillar={strategy.pillar.value}")
            
            return post
            
        except Exception as e:
            self.logger.error(f"Content generation failed: {e}")
            raise
    
    def _select_strategy(
        self,
        trending_context: Optional[str],
        requested_pillar: Optional[ContentPillar],
        requested_format: Optional[PostFormat],
        avoid_patterns: Dict[str, Any]
    ) -> ContentStrategy:
        """Select the optimal content strategy based on context"""
        
        # Select pillar
        if requested_pillar:
            pillar = requested_pillar
        elif trending_context:
            # Match trending context to appropriate pillar
            pillar = self._match_trend_to_pillar(trending_context)
        else:
            # Weighted random selection
            pillar = self._weighted_pillar_selection(avoid_patterns)
        
        # Select format
        if requested_format:
            format_type = requested_format
        else:
            format_type = self._select_format_for_pillar(pillar)
        
        # Get pillar config
        pillar_config = self.content_pillars[pillar]
        format_config = self.post_formats[format_type]
        
        return ContentStrategy(
            pillar=pillar,
            format=format_type,
            hook_approach=format_config["hook_style"],
            tone_notes=pillar_config["tone"],
            engagement_goal=pillar_config["engagement_driver"],
            optimal_length=format_config["length"],
            cta_style="Natural brand mention, never explicit CTA"
        )
    
    def _match_trend_to_pillar(self, trending_context: str) -> ContentPillar:
        """Match a trending topic to the most appropriate content pillar"""
        
        context_lower = trending_context.lower()
        
        # AI/Tech related
        if any(word in context_lower for word in ['ai', 'chatgpt', 'automation', 'robot', 'algorithm', 'tech']):
            return ContentPillar.AI_HUMAN_TENSION
        
        # Workplace related
        if any(word in context_lower for word in ['meeting', 'office', 'remote', 'layoff', 'job', 'career', 'boss', 'manager']):
            return ContentPillar.WORKPLACE_ABSURDISM
        
        # Wellness/Self-care related
        if any(word in context_lower for word in ['wellness', 'self-care', 'burnout', 'mental health', 'routine', 'productivity']):
            return ContentPillar.SELF_CARE_SATIRE
        
        # LinkedIn/Professional culture
        if any(word in context_lower for word in ['linkedin', 'thought leader', 'networking', 'personal brand']):
            return ContentPillar.CULTURAL_OBSERVATION
        
        # Default to cultural observation for general trends
        return ContentPillar.CULTURAL_OBSERVATION
    
    def _weighted_pillar_selection(self, avoid_patterns: Dict[str, Any]) -> ContentPillar:
        """Select a content pillar based on weights, avoiding recently used ones"""
        
        recently_used = avoid_patterns.get("recent_pillars", [])
        
        # Build weighted list
        weighted_options = []
        for pillar, config in self.content_pillars.items():
            weight = config["weight"]
            
            # Reduce weight if recently used
            if pillar.value in recently_used:
                weight = weight // 2
            
            weighted_options.extend([pillar] * weight)
        
        return random.choice(weighted_options)
    
    def _select_format_for_pillar(self, pillar: ContentPillar) -> PostFormat:
        """Select an appropriate format for the given pillar"""
        
        # Format preferences by pillar
        pillar_format_preferences = {
            ContentPillar.WORKPLACE_ABSURDISM: [
                PostFormat.OBSERVATION, PostFormat.STORY, PostFormat.CONTRAST, PostFormat.CONFESSION
            ],
            ContentPillar.AI_HUMAN_TENSION: [
                PostFormat.OBSERVATION, PostFormat.PHILOSOPHY, PostFormat.CONTRAST, PostFormat.QUESTION
            ],
            ContentPillar.SELF_CARE_SATIRE: [
                PostFormat.LIST_SUBVERSION, PostFormat.CONTRAST, PostFormat.CELEBRATION, PostFormat.QUESTION
            ],
            ContentPillar.CULTURAL_OBSERVATION: [
                PostFormat.OBSERVATION, PostFormat.CONTRAST, PostFormat.STORY
            ],
            ContentPillar.PRODUCT_STORYTELLING: [
                PostFormat.STORY, PostFormat.CONFESSION, PostFormat.PHILOSOPHY
            ],
            ContentPillar.JESSE_SIGHTINGS: [
                PostFormat.OBSERVATION, PostFormat.CELEBRATION, PostFormat.STORY
            ],
            ContentPillar.RITUAL_PHILOSOPHY: [
                PostFormat.PHILOSOPHY, PostFormat.QUESTION, PostFormat.OBSERVATION
            ]
        }
        
        preferred_formats = pillar_format_preferences.get(pillar, list(PostFormat))
        return random.choice(preferred_formats)
    
    def _build_strategic_prompt(
        self,
        strategy: ContentStrategy,
        trending_context: Optional[str],
        avoid_patterns: Dict[str, Any]
    ) -> str:
        """Build the generation prompt with strategic guidance"""
        
        pillar_config = self.content_pillars[strategy.pillar]
        format_config = self.post_formats[strategy.format]
        
        # Build theme suggestions
        themes = pillar_config["themes"]
        theme_suggestions = random.sample(themes, min(3, len(themes)))
        
        # Build example hooks
        example_hooks = pillar_config.get("example_hooks", [])
        hook_examples = "\n".join(f"- {hook}" for hook in example_hooks[:2]) if example_hooks else "See format example"
        
        # Build avoid section
        avoid_section = ""
        if avoid_patterns:
            avoid_items = []
            if avoid_patterns.get("recent_topics"):
                avoid_items.append(f"Recently used topics: {', '.join(avoid_patterns['recent_topics'][:3])}")
            if avoid_patterns.get("failed_approaches"):
                avoid_items.append(f"Approaches that didn't work: {', '.join(avoid_patterns['failed_approaches'][:2])}")
            if avoid_items:
                avoid_section = "\n\nAVOID:\n" + "\n".join(f"- {item}" for item in avoid_items)
        
        # Trending context section
        trend_section = ""
        if trending_context:
            trend_section = f"""
TRENDING CONTEXT TO REACT TO:
{trending_context}

React to this through the lens of {strategy.pillar.value}. Find the Jesse A. Eisenbalm angle — what does this mean for humans trying to stay human? How does lip balm fit (creatively)?
"""
        
        # Visual scenarios for Jesse Sightings
        visual_section = ""
        if strategy.pillar == ContentPillar.JESSE_SIGHTINGS:
            scenarios = pillar_config.get("visual_scenarios", [])
            scenario = random.choice(scenarios) if scenarios else "Jesse in an unexpected situation"
            visual_section = f"""
VISUAL SCENARIO:
{scenario}

Write the caption for this image. The image shows Jesse (curly hair, deadpan expression) in this absurd situation, calmly holding or applying lip balm.
"""
        
        return f"""Generate a LinkedIn post for Jesse A. Eisenbalm.

═══════════════════════════════════════════════════════════════════════════════
STRATEGIC DIRECTION
═══════════════════════════════════════════════════════════════════════════════

CONTENT PILLAR: {strategy.pillar.value.upper()}
{pillar_config['description']}

THEMES TO CONSIDER:
{chr(10).join(f'- {theme}' for theme in theme_suggestions)}

TONE: {strategy.tone_notes}
ENGAGEMENT GOAL: {strategy.engagement_goal}

═══════════════════════════════════════════════════════════════════════════════
POST FORMAT: {strategy.format.value.upper()}
═══════════════════════════════════════════════════════════════════════════════

STRUCTURE:
{format_config['structure']}

HOOK APPROACH: {format_config['hook_style']}

EXAMPLE OF THIS FORMAT:
{format_config['example']}

TARGET LENGTH: {strategy.optimal_length[0]}-{strategy.optimal_length[1]} words

═══════════════════════════════════════════════════════════════════════════════
HOOK INSPIRATION
═══════════════════════════════════════════════════════════════════════════════

{hook_examples}
{trend_section}{visual_section}{avoid_section}

═══════════════════════════════════════════════════════════════════════════════
REQUIREMENTS
═══════════════════════════════════════════════════════════════════════════════

MUST:
- Follow the {strategy.format.value} format structure
- Use specific, concrete details (not vague generalities)
- Include natural line breaks for readability
- Land with impact (brand mention, ritual, or $8.99)
- Feel like a smart friend's observation, not marketing

MUST NOT:
- Target any individual negatively
- Use hashtags
- Include external links
- Ask for engagement explicitly
- Be preachy or explain the joke
- Use "In a world where..."

BRAND ELEMENTS (use naturally, not forced):
- Product: Jesse A. Eisenbalm
- Price: $8.99
- Ritual: Stop. Breathe. Balm.
- Em dashes: encouraged —

Return as JSON:
{{
    "content": "The full post with line breaks (use \\n)",
    "hook": "The opening line",
    "topic_used": "What specific theme/topic this addresses",
    "target_audience": "Who this specifically speaks to",
    "engagement_driver": "What emotion/recognition this triggers",
    "image_direction": "product/jesse_lifestyle/jesse_absurdist/minimal — brief visual description"
}}"""
    
    def _clean_content(self, content: str) -> str:
        """Clean the generated content"""
        import re
        
        # Remove any hashtags that snuck through
        content = re.sub(r'\s*#\w+', '', content).strip()
        
        # Remove any URLs
        content = re.sub(r'http\S+', '', content).strip()
        
        # Clean up excessive whitespace while preserving intentional line breaks
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        return content
    
    def _extract_hook(self, content: str) -> str:
        """Extract the hook (first line) from content"""
        if not content:
            return ""
        
        first_line = content.split('\n')[0].strip()
        return first_line[:100] if len(first_line) > 100 else first_line
    
    def _calculate_cost(self, usage: Dict[str, int]) -> float:
        """Calculate cost based on token usage"""
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        
        # Claude pricing per 1M tokens (adjust as needed)
        input_cost = (input_tokens / 1_000_000) * 3.00
        output_cost = (output_tokens / 1_000_000) * 15.00
        
        return input_cost + output_cost
    
    def get_content_calendar_recommendation(self) -> Dict[str, Any]:
        """Get a recommended content mix for the week"""
        
        return {
            "weekly_posts": 5,
            "recommended_mix": {
                "Monday": {
                    "pillar": ContentPillar.WORKPLACE_ABSURDISM.value,
                    "rationale": "Start week with relatable workplace content"
                },
                "Tuesday": {
                    "pillar": ContentPillar.AI_HUMAN_TENSION.value,
                    "rationale": "Mid-week thought leadership"
                },
                "Wednesday": {
                    "pillar": ContentPillar.CULTURAL_OBSERVATION.value,
                    "rationale": "React to week's trends"
                },
                "Thursday": {
                    "pillar": ContentPillar.JESSE_SIGHTINGS.value,
                    "rationale": "Visual content for engagement"
                },
                "Friday": {
                    "pillar": ContentPillar.SELF_CARE_SATIRE.value,
                    "rationale": "End week with self-care humor"
                }
            },
            "optimal_times": ["8:00 AM", "12:00 PM", "5:00 PM"],
            "notes": "Adjust based on performance data. Leave room for reactive content."
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get strategist statistics"""
        return {
            "agent_name": self.name,
            "version": "content-strategist-v1",
            "content_pillars": [p.value for p in ContentPillar],
            "post_formats": [f.value for f in PostFormat],
            "pillar_weights": {p.value: c["weight"] for p, c in self.content_pillars.items()},
            "linkedin_optimized": True,
            "brand_toolkit_integrated": True
        }


# Backward compatibility alias - allows old imports to still work
# from .content_generator import ContentGeneratorAgent
ContentGeneratorAgent = ContentStrategistAgent
