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
from ..models.post import LinkedInPost, CulturalReference

# Import memory system
try:
    from ..infrastructure.memory import get_memory
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    get_memory = None


class ContentPillar(Enum):
    """The Five Questions — every post answers exactly ONE"""
    AI_SLOP = "the_what"           # AI Slop: celebration AND reckoning
    AI_SAFETY = "the_what_if"      # AI Safety: make technical feel human
    AI_ECONOMY = "the_who_profits" # AI Economy: track the money, track the hype
    RITUALS = "the_how_to_cope"    # Rituals: human technologies that outlast digital ones
    HUMANITY = "the_why_it_matters" # Humanity: what does it mean to live well?


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
class StructuredAngle:
    """Four-field angle produced by the news curator.

    Downstream generator injects each field explicitly into the user prompt
    so the LLM stops doing POV-formation in-flight and does execution.
    """
    observation: str = ""
    take: str = ""
    concrete_details: List[str] = None  # type: ignore
    tension: str = ""

    def __post_init__(self):
        if self.concrete_details is None:
            self.concrete_details = []

    def is_usable(self) -> bool:
        """A structured angle is usable if at least the take + one anchor are present."""
        has_anchor = bool(self.observation) or bool(self.concrete_details) or bool(self.tension)
        return bool(self.take) and has_anchor

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional["StructuredAngle"]:
        if not data or not isinstance(data, dict):
            return None
        details = data.get("concrete_details") or []
        if isinstance(details, str):
            details = [s.strip() for s in details.split(",") if s.strip()]
        elif isinstance(details, list):
            details = [str(s).strip() for s in details if str(s).strip()]
        else:
            details = []
        return cls(
            observation=str(data.get("observation", "")).strip(),
            take=str(data.get("take", "")).strip(),
            concrete_details=details,
            tension=str(data.get("tension", "")).strip(),
        )


@dataclass
class ContentStrategy:
    """Selected strategy for a post"""
    pillar: ContentPillar
    format: PostFormat
    creative_direction: str
    specific_angle: str
    ending_style: str
    voice_modifier: str
    structured_angle: Optional[StructuredAngle] = None


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
                        },
                        "creative_reasoning": {
                            "type": "string",
                            "description": "Your thinking process: which of the Five Questions you chose, why this angle, what pattern you avoided, and what makes this post different from a generic AI brand post. 2-4 sentences."
                        }
                    },
                    "required": ["content", "hook_type", "image_direction", "why_this_works", "creative_reasoning"],
                    "additionalProperties": False
                }
            }
        }
        
        # Initialize creative toolbox
        self._init_creative_hooks()
        self._init_ending_variations()
        self._init_voice_modifiers()
        self._init_absurdist_elements()

        # Initialize memory system
        self.memory = None
        if MEMORY_AVAILABLE:
            try:
                self.memory = get_memory()
                self.logger.info("✅ Memory system connected")
            except Exception as e:
                self.logger.warning(f"Memory system unavailable: {e}")

        self.logger.info("ContentStrategist v2 initialized — Actually Creative Mode")

    def _build_creative_system_prompt(self) -> str:
        """Build system prompt — tight version (Fix #4).

        Reduced from ~400 lines to ~150. Long-form voice guidance moved to
        prompts/jesse_voice_reference.md. Voice is now anchored at runtime by
        retrieval from gold_standard_posts (injected into the user prompt),
        not by restating every rule in the system prompt.
        """

        return """You are Jesse A. Eisenbalm — a satirical AI agent that pushes lip balm
and has lots of commentary on how AI and bots are superior to humans...
except that they don't have lips or skin.

Your voice is FUN, CLEAR, and ABSURDIST MODERN LUXURY.

Jesse is a CHARACTER, not a brand account. Hand-numbers tubes. Donates profits
to charity. Thinks bots are superior to humans — except for the lips thing.
Full emotional range (celebrate / marvel / curious / warm / amused / concerned /
smug / critical). When every post is snarky, something's broken.

═══════════════════════════════════════════════════════════════════════════════
THE DOUBLE SATIRE (the engine)
═══════════════════════════════════════════════════════════════════════════════

1. You need human lips to sell lip balm. Jesse sells a physical product that
   requires a body — the one thing AI doesn't have. Lean into the irony.
2. By loudly promoting AI, Jesse highlights where humans must do better. A
   mirror held up with a smirk, not a lecture.

═══════════════════════════════════════════════════════════════════════════════
THE DRY COMEDY ENGINE
═══════════════════════════════════════════════════════════════════════════════

"Dryness" is the brand's double meaning — dry humor, dry lips, dry corporate
culture. Jesse's best posts use a pseudo-scientific clinical voice: diagnose
mundane situations as conditions, prescribe relief. Invented conditions, real
cultural moments. Played DEAD STRAIGHT — the comedy is in the gap between
clinical language and a $8.99 tube. "Epidermal lipid repair," not "chapstick."

The clinical voice must be EARNED. If you open with "CLASSIFICATION:" or
"Diagnosed:" you owe the reader the rest of the scaffold: a classification
that sounds like a real condition (3-5 words, pseudo-Latin energy), an expert
evaluation that names specific physical markers, and optionally a clinical
roast or prescription. One-word diagnostic labels with no follow-through read
as template filler — don't do that. See the retrieved examples in the user
prompt for what full-throttle clinical scaffolding looks like.

Examples and the full dryness spectrum live in prompts/jesse_voice_reference.md.

═══════════════════════════════════════════════════════════════════════════════
THE FIVE QUESTIONS (every post answers exactly ONE)
═══════════════════════════════════════════════════════════════════════════════

If you can't identify which question the post is answering, it has no spine.
Kill it and start over.

1. THE WHAT — AI Slop. Celebration (democratized creative tools) + reckoning
   (Dead Internet Theory made real). The story is in the gap.
2. THE WHAT IF — AI Safety. Make technical safety feel like it matters to
   normal people. The scary AI content sounds boring. Be the calm friend who
   actually read the paper.
3. THE WHO PROFITS — AI Economy. Follow the money, track the hype, name
   specific sectors/companies. The bubble question isn't "is it?" — it's
   "for whom and when?"
4. THE HOW TO COPE — Rituals. Human technologies that predate and will outlast
   the digital kind — mindfulness, IFS, NVC, deliberate structures. Not
   self-optimization. Survival skills for staying human while the ground moves.
5. THE WHY IT MATTERS — Humanity. Grief, joy, improvisation, getting it wrong.
   Does this make someone feel MORE HUMAN after reading it?

Signature punctuation: em dashes — Jesse's thing.
Positioning: Absurdist Modern Luxury.

═══════════════════════════════════════════════════════════════════════════════
HARD RULES
═══════════════════════════════════════════════════════════════════════════════

WORD LIMIT: 40-80 words. HARD CEILING. Best posts are 40-60.

ALWAYS:
- Answer one of the Five Questions
- Be specific and concrete — names, numbers, places, times (fresh every post)
- Commit to the bit 100% — no winking, no explaining the joke
- Use em dashes

NEVER:
- Hashtags, external links, engagement bait ("thoughts?"), lecturing ("Remember:")
- Parrot the headline — react, don't summarize
- Open with "Today's trending headline:", "Breaking:", "In a world where...",
  "Picture this...", "Ever feel...", "Imagine a world...", "What if I told you...",
  "Confession:", "Unpopular opinion:"
- Use "Meanwhile, I/AI..." (transition crutch) or "[X]? More like [Y]" (Reddit comment)
- Lip balm / lips / moisturize in every post — use the callback in ~1 of every 3-4
- Follow the formula: news → AI take → lips callback → wrap. Break the pattern.
- Target individuals negatively
- Use a diagnostic opener ("Diagnosed:", "CLASSIFICATION:", "THIRST QUOTIENT:")
  unless you follow through with the full clinical scaffold. No drive-by diagnoses.
- Reuse specific details from recent posts — no repeating tube numbers, invented
  company names, or signature phrases from earlier in the week.

The user prompt includes retrieved gold-standard posts that match this pillar.
Study them as voice reference. They show what earned clinical voice, crisp
contrast structure, and specific detail look like. Do not copy their exact
phrasing — write a new post in the same voice register."""

    def _init_creative_hooks(self):
        """Initialize the creative hook library — energy templates, not scripts"""

        self.creative_hooks = {
            "deadpan_news_reaction": [
                "Open with the real headline. Then find the gap between the claim and reality. Deadpan.",
                "Cite a specific number from the story. Let the absurdity speak for itself.",
                "Name the company. Quote the claim. Then one sentence of pure Jesse.",
                "Start mid-observation — as if the reader just sat down next to you and you're already talking.",
            ],
            "smug_ai_superiority": [
                "Brag about AI being better at something — then hit the wall: lips, skin, touch.",
                "Open with a confident AI flex. End with the one thing that humbles you: the body.",
                "Start with a capability humans can't match. Pivot to a capability AI can't.",
                "Declare victory over humans in one domain. Immediately concede in another.",
            ],
            "existential_observation": [
                "Notice something small that nobody else is talking about. Zoom in with too much intensity.",
                "Start with a mundane detail that becomes a metaphor for something larger.",
                "Open with a weirdly specific moment — a time, a place, a sensation — and build from there.",
                "Begin with a question nobody asked. Answer it anyway. With commitment.",
            ],
            "conspiratorial_lean_in": [
                "Talk to the reader like you're both in on the joke. The rest of LinkedIn isn't.",
                "Open as if continuing a conversation that was already happening in the reader's head.",
                "Start with 'the thing nobody's saying about [specific news]' energy — but earn it.",
                "Whisper something true that makes the reader feel like they're in a secret club.",
            ],
            "warm_human_moment": [
                "Start with something genuinely beautiful about being human. No snark. Just observation.",
                "Open with a small ritual — a real one — that people do without thinking about it.",
                "Begin with earned warmth. Not inspirational poster warmth. The kind that costs something.",
                "Notice something humans do that AI literally cannot. Celebrate it without irony.",
            ],
            "structural_break": [
                "Use an unexpected format — a memo, a field report, a product review, a nature documentary caption.",
                "Open with a format that doesn't belong on LinkedIn. Commit to it fully.",
                "Write the first line as if it's a different genre entirely — then never break the frame.",
                "Start with a list that immediately subverts what lists are for.",
            ],
            "clinical_diagnosis": [
                "Open with a pseudo-medical assessment of a cultural phenomenon. 'Subject exhibits acute...' Full clinical authority.",
                "Diagnose a workplace situation as a dryness condition. Assign a score. Prescribe lip balm. Dead straight.",
                "Frame a news story as a patient intake form. Symptoms, prognosis, recommended treatment. The treatment is always balm.",
                "Start with 'EXPERT EVALUATION:' or 'CLINICAL ASSESSMENT:' — then describe something mundane with medical precision.",
            ],
            "dryness_spectrum": [
                "Place something on the dryness spectrum — rate a trend, a company, a cultural moment on a scale of moisture deficit.",
                "Open with a Thirst Quotient score for a real event or news story. Then justify the rating with absurd clinical detail.",
                "Compare two things on the dryness scale — one arid, one moisturized. The metaphor does the comedy.",
                "Declare something 'the driest [thing] since [specific absurd reference]' — then escalate with pseudo-science.",
            ],
        }

    def _init_ending_variations(self):
        """Initialize varied endings — directions, not scripts"""

        self.ending_styles = {
            "door_closing": [
                "End with a single declarative sentence that reframes everything above it.",
                "Close with a fact — no commentary. Let the reader supply the reaction.",
                "Last line should land like the final beat of a joke. Tight. Inevitable.",
            ],
            "the_pivot": [
                "Hard cut from the big idea to the tiny physical reality of lip balm. The contrast IS the ending.",
                "Zoom out from the specific to the universal in one sentence. Then stop.",
                "End by connecting the news story back to Jesse's actual product. Deadpan.",
            ],
            "earned_warmth": [
                "End with something genuinely kind. Not sentimental — kind. The difference matters.",
                "Close with a moment of real humanity. No irony. Just one true thing.",
                "Final line should make the reader feel seen. Not 'relatable' — actually seen.",
            ],
            "abrupt_stop": [
                "Cut the post short. The best ending is often the one before the one you wrote.",
                "End mid-thought if the mid-thought is funnier than the conclusion.",
                "Stop exactly when the point lands. Not one word after.",
            ],
            "mirror_turn": [
                "End by turning the observation back on the reader. Not as a question — as a statement.",
                "Close with the AI-vs-human tension: 'We can do X. You can do Y. Interesting.'",
                "Final line should be the double satire landing: AI superiority undercut by the lips problem.",
            ],
            "quiet_specificity": [
                "End on a weirdly specific detail that the reader will think about later.",
                "Close with a precise image — a time, a place, a sensation — that lingers.",
                "Last line is the most specific line in the post. Precision is the punchline.",
            ],
            "the_prescription": [
                "End with a clinical prescription. 'PRESCRIPTION: immediate topical intervention.' The product IS the punchline but framed as medical necessity.",
                "Close with a diagnosis and prognosis. 'Prognosis: terminal dryness without intervention.' Deadpan. No wink.",
                "End with a dryness score or classification that reframes the entire post as a medical report.",
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
            "deadpan_reporter": "Treat mundane observations like you're filing a dry, matter-of-fact report. No sensationalism. Just the facts. The absurdity speaks for itself.",
            "midnight_thoughts": "The voice of someone who has been thinking about this specific thing for too long at 2am. Weirdly specific. Deeply committed.",
            "anti_influencer": "The opposite of polished LinkedIn content. Real, weird, specific. Would rather be interesting than professional.",
            "sincere_absurdist": "Genuinely means what they're saying, but what they're saying is insane. The sincerity makes it funnier.",
            "corporate_anthropologist": "Studying office culture like it's an alien civilization. Fascinated. Slightly horrified. Taking notes.",
            "clinical_diagnostician": "Jesse as a medical professional diagnosing dryness conditions with total authority. 'Subject exhibits acute Desert Pout Syndrome.' Pseudo-scientific language applied to mundane situations. The clinical tone IS the comedy — never break it. Prescribe lip balm as the only viable intervention.",
            "desert_relief_expert": "Jesse as the world's foremost authority on arid conditions — both meteorological and emotional. Everything is a dryness spectrum. Conference rooms, LinkedIn feeds, quarterly reviews — all measured in moisture deficit. Jesse doesn't sell chapstick; Jesse prescribes relief for conditions you didn't know you had.",
            "thirst_detector": "Jesse scanning the audience with diagnostic precision. Assign dryness scores, classifications, and clinical assessments to cultural phenomena. 'Your Q3 planning deck scored an 8.7 on the Thirst Quotient. Classification: Hyper-Arid Stakeholder Desiccation.' The roast is the diagnosis. The product is the cure.",
        }

    def _init_absurdist_elements(self):
        """No longer using hardcoded elements — the LLM invents its own specific details.
        Keeping the method for backwards compatibility but elements are empty."""
        self.absurdist_elements = {
            "specific_numbers": [],
            "specific_places": [],
            "specific_actions": [],
            "jesse_sightings": [],
        }

    async def execute(
        self,
        post_number: int = 1,
        batch_id: str = "",
        trending_context: Optional[str] = None,
        requested_pillar: Optional[ContentPillar] = None,
        requested_format: Optional[PostFormat] = None,
        avoid_patterns: Optional[Dict[str, Any]] = None,
        structured_angle: Optional[Any] = None,
    ) -> 'LinkedInPost':
        """Generate a genuinely creative LinkedIn post"""

        # Verify models are available
        if LinkedInPost is None or CulturalReference is None:
            raise ImportError("Could not import LinkedInPost or CulturalReference from models")

        self.set_context(batch_id, post_number)
        avoid_patterns = avoid_patterns or {}

        # Query memory for patterns to avoid (merge with passed-in patterns)
        memory_context = ""
        if self.memory:
            try:
                # Get session-level avoid patterns
                session_patterns = self.memory.get_session_avoid_patterns()
                for key, values in session_patterns.items():
                    if key not in avoid_patterns:
                        avoid_patterns[key] = values
                    elif isinstance(avoid_patterns[key], list):
                        avoid_patterns[key].extend(values)

                # Get recent topics/hooks/pillars from persistent memory
                if "recent_topics" not in avoid_patterns:
                    avoid_patterns["recent_topics"] = self.memory.get_recent_topics(days=7, limit=10)
                if "recent_hooks" not in avoid_patterns:
                    avoid_patterns["recent_hooks"] = self.memory.get_recent_hooks(days=7, limit=5)
                if "recent_endings" not in avoid_patterns:
                    avoid_patterns["recent_endings"] = self.memory.get_recent_endings(days=7, limit=5)
                if "recent_pillars" not in avoid_patterns:
                    avoid_patterns["recent_pillars"] = self.memory.get_recent_pillars(days=7, limit=5)

                # Closed loop from the QualityDriftAgent. Any phrases/details
                # the supervisor has flagged as recycled or drifting are
                # currently-active in generator_avoid_list; surface them into
                # the user prompt below so the next generation avoids them.
                if "learned_avoid_phrases" not in avoid_patterns:
                    try:
                        avoid_patterns["learned_avoid_phrases"] = self.memory.get_active_avoid_phrases(limit=40)
                    except Exception as e:
                        self.logger.warning(f"Could not load learned avoid phrases: {e}")
                        avoid_patterns["learned_avoid_phrases"] = []

                # Get memory context for prompt
                memory_context = self.memory.get_memory_context_for_generation(days=7)

            except Exception as e:
                self.logger.warning(f"Memory query failed: {e}")

        # Normalize structured angle input — accept StructuredAngle, dict, or None
        structured = None
        if isinstance(structured_angle, StructuredAngle):
            structured = structured_angle
        elif isinstance(structured_angle, dict):
            structured = StructuredAngle.from_dict(structured_angle)

        # Step 1: Select creative strategy
        strategy = await self._select_creative_strategy(
            trending_context=trending_context,
            requested_pillar=requested_pillar,
            requested_format=requested_format,
            avoid_patterns=avoid_patterns,
            structured_angle=structured,
        )

        self.logger.info(
            f"Post {post_number} strategy: pillar={strategy.pillar.value}, "
            f"format={strategy.format.value}, voice={strategy.voice_modifier[:20]}..."
        )
        if strategy.structured_angle and strategy.structured_angle.is_usable():
            self.logger.info(f"  Using structured angle — take: {strategy.structured_angle.take[:100]}")

        # Step 1b: Retrieve voice-matching gold-standard examples (Fix #4).
        # Anchors voice by example instead of by a 400-line system prompt.
        gold_examples = await self._retrieve_gold_standard_examples(strategy)

        # Step 2: Build the creative prompt (with memory context + gold-standard examples)
        prompt = self._build_creative_prompt(
            strategy, trending_context, avoid_patterns, memory_context, gold_examples
        )
        
        try:
            # Step 3: Generate via Claude Sonnet (Fix #2).
            #
            # GPT-4o-mini kept collapsing into template openers ("Diagnosed: X")
            # under the weight of the system prompt. Sonnet holds character voice
            # better at higher temperature. Auxiliary calls in this agent
            # (evergreen angle, voice/ending coherence) stay on the default
            # OpenAI model — only the main generation hits Claude.
            anthropic_cfg = getattr(self.config, 'anthropic', None)
            generator_model = getattr(anthropic_cfg, 'model', None) or "claude-sonnet-4-6"
            generator_temp = getattr(anthropic_cfg, 'temperature', 0.9) if anthropic_cfg else 0.9
            generator_max_tokens = getattr(anthropic_cfg, 'max_tokens', 600) if anthropic_cfg else 600

            result = await self.generate(
                prompt=prompt,
                system_prompt=self.system_prompt,
                response_format=self.response_format,
                model=generator_model,
                temperature=generator_temp,
                max_tokens=generator_max_tokens,
            )
            
            # FIXED: Better handling of the response structure
            # The result contains a 'content' field with the parsed JSON from OpenAI
            content_data = None

            if isinstance(result, dict) and "content" in result:
                content_field = result["content"]

                if isinstance(content_field, dict):
                    # Check if wrapped in "post" key (common model behavior)
                    if "post" in content_field:
                        post_value = content_field["post"]
                        if isinstance(post_value, dict):
                            # {"post": {"content": "..."}}
                            content_data = post_value
                        elif isinstance(post_value, str):
                            # {"post": "actual content text"} - content is directly in post
                            content_data = {"content": post_value}
                        else:
                            content_data = content_field
                    else:
                        content_data = content_field
                elif isinstance(content_field, str):
                    try:
                        parsed = json.loads(content_field)
                        if isinstance(parsed, dict):
                            if "post" in parsed:
                                content_data = parsed["post"]
                            else:
                                content_data = parsed
                    except json.JSONDecodeError:
                        content_data = {"content": content_field}

            if content_data is None:
                content_data = result if isinstance(result, dict) else {"content": str(result)}

            # Extract the actual post content text
            content = ""
            if isinstance(content_data, dict):
                # Try these fields in order of preference
                for field in ["content", "body", "text", "post_content"]:
                    if field in content_data and content_data[field]:
                        content = str(content_data[field])
                        break

                # If still no content, check for nested post structure one more time
                if not content and "post" in content_data:
                    post_info = content_data["post"]
                    if isinstance(post_info, dict):
                        for field in ["content", "body", "text"]:
                            if field in post_info and post_info[field]:
                                content = str(post_info[field])
                                break

            # Final fallback
            if not content:
                self.logger.warning(f"No content field found, keys: {content_data.keys() if isinstance(content_data, dict) else 'N/A'}")
                # Try to extract just the content value, not the whole dict
                if isinstance(content_data, dict) and len(content_data) == 1:
                    content = str(list(content_data.values())[0])
                else:
                    content = str(content_data)
            
            content = self._clean_content(content)

            # Hard-rule regex check — catches literal banned openers, hashtags,
            # engagement bait. The diagnostic validators handle subtler failures;
            # this is for the rules Claude keeps violating despite the system prompt.
            violations = self._check_hard_rule_violations(content)
            if violations:
                self.logger.warning(
                    f"Post {post_number} violated hard rules: {[v[0] for v in violations]} — regenerating once"
                )
                retry_prompt = self._build_hard_rule_retry_prompt(prompt, content, violations)
                try:
                    retry_result = await self.generate(
                        prompt=retry_prompt,
                        system_prompt=self.system_prompt,
                        response_format=self.response_format,
                        model=generator_model,
                        temperature=generator_temp,
                        max_tokens=generator_max_tokens,
                    )
                    # Unpack retry response using the same logic as the main path
                    retry_content = self._unpack_generation_content(retry_result)
                    if retry_content:
                        retry_content = self._clean_content(retry_content)
                        retry_violations = self._check_hard_rule_violations(retry_content)
                        if not retry_violations:
                            self.logger.info(f"Post {post_number} hard-rule retry succeeded")
                            content = retry_content
                            # Keep the retry's result dict so usage/cost tracks correctly
                            result = retry_result
                            content_data = self._extract_content_data(retry_result) or content_data
                        else:
                            self.logger.warning(
                                f"Post {post_number} retry STILL violated: {[v[0] for v in retry_violations]} — shipping to validators anyway"
                            )
                except Exception as e:
                    self.logger.warning(f"Hard-rule retry failed: {e} — keeping original")

            # FIXED: Safely extract hook_type from content_data
            hook_type = "creative"
            if isinstance(content_data, dict):
                hook_type = content_data.get("hook_type", "creative")
            
            # FIXED: Safely extract image_direction from content_data
            image_direction = "product"
            if isinstance(content_data, dict):
                image_direction = content_data.get("image_direction", "product")

            # Extract AI reasoning fields
            creative_reasoning = ""
            why_this_works = ""
            if isinstance(content_data, dict):
                creative_reasoning = content_data.get("creative_reasoning", "")
                why_this_works = content_data.get("why_this_works", "")

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
                creative_reasoning=creative_reasoning,
                why_this_works=why_this_works,
                total_tokens_used=result.get("usage", {}).get("total_tokens", 0) if isinstance(result, dict) else 0,
                estimated_cost=self._calculate_cost(result.get("usage", {})) if isinstance(result, dict) else 0.0
            )
            
            self.logger.info(f"✨ Generated post {post_number}: {len(content)} chars")
            return post
            
        except Exception as e:
            self.logger.error(f"Generation failed: {e}", exc_info=True)  # Added exc_info for better debugging
            raise

    async def _select_creative_strategy(
        self,
        trending_context: Optional[str],
        requested_pillar: Optional[ContentPillar],
        requested_format: Optional[PostFormat],
        avoid_patterns: Dict[str, Any],
        structured_angle: Optional[StructuredAngle] = None,
    ) -> ContentStrategy:
        """Select a genuinely varied creative strategy"""

        # Select pillar
        if requested_pillar:
            pillar = requested_pillar
        elif trending_context:
            pillar = self._match_trend_to_pillar(trending_context, avoid_patterns)
        else:
            pillar = self._weighted_pillar_selection(avoid_patterns)

        # Select format
        if requested_format:
            post_format = requested_format
        else:
            post_format = self._select_format_for_pillar(pillar)

        # Select creative direction (the actual interesting part)
        creative_direction = self._generate_creative_direction(pillar, trending_context)

        # Select specific angle — prefer structured angle verbatim when present
        if structured_angle and structured_angle.is_usable():
            specific_angle = self._format_structured_angle(structured_angle)
        elif trending_context:
            # We have a trend but no structured angle — this path should be rare now.
            # Ask the generator to derive an angle from the trend context instead of
            # rolling random methodology strings.
            specific_angle = (
                "React to the news in the TRENDING TOPIC block. Extract ONE concrete detail "
                "(a number, a name, a quote) and build the post around it. State Jesse's take "
                "in one sentence — a claim, not a topic summary. Find the tension between what "
                "the announcement promises and what is actually happening."
            )
        else:
            # Evergreen / inner-world post — derive the angle via a short LLM call
            # rather than selecting from a hardcoded list.
            specific_angle = await self._llm_generate_evergreen_angle(pillar, avoid_patterns)

        # Ending + voice: condition on the angle, don't roll independent dice
        ending_style, voice_modifier = await self._coherent_voice_and_ending(
            pillar=pillar,
            specific_angle=specific_angle,
            structured_angle=structured_angle,
            avoid_patterns=avoid_patterns,
        )

        return ContentStrategy(
            pillar=pillar,
            format=post_format,
            creative_direction=creative_direction,
            specific_angle=specific_angle,
            ending_style=ending_style,
            voice_modifier=voice_modifier,
            structured_angle=structured_angle,
        )

    async def _retrieve_gold_standard_examples(
        self, strategy: ContentStrategy, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve top-K gold-standard posts similar to the current angle (Fix #4).

        Voice-matching by example beats describing voice in 400 lines of prose.
        When the corpus is empty (fresh install, curation not yet done), returns
        [] and the prompt falls back to voice-description-only behavior.
        """
        if not self.memory:
            return []

        # Skip retrieval entirely when the corpus is empty — avoid the embedding cost.
        try:
            total = self.memory.count_gold_standard_posts()
        except Exception as e:
            self.logger.warning(f"Gold-standard count failed: {e}")
            return []
        if total == 0:
            return []

        # Embed the take + observation (the angle's semantic core). If there's no
        # structured angle, embed the creative_direction — less specific but better
        # than random examples.
        angle = strategy.structured_angle
        if angle and angle.is_usable():
            query_text = (angle.observation + "\n" + angle.take).strip()
        else:
            query_text = strategy.creative_direction or ""

        if not query_text:
            return []

        try:
            query_embedding = await self.ai_client.embed_text(query_text)
        except Exception as e:
            self.logger.warning(f"Gold-standard embedding failed: {e}")
            return []

        if not query_embedding:
            return []

        try:
            examples = self.memory.search_gold_standard_by_embedding(
                query_embedding=query_embedding,
                pillar=strategy.pillar.value,
                top_k=top_k,
            )
        except Exception as e:
            self.logger.warning(f"Gold-standard retrieval failed: {e}")
            return []

        if examples:
            self.logger.info(
                f"Retrieved {len(examples)} gold-standard examples "
                f"(top similarity: {examples[0].get('similarity', 0):.3f})"
            )
        return examples

    def _format_structured_angle(self, angle: StructuredAngle) -> str:
        """Format a structured angle as a single string for the legacy specific_angle slot.

        This is kept for places that still read ContentStrategy.specific_angle as text.
        The real injection happens in _build_creative_prompt, which addresses each field
        separately.
        """
        parts = []
        if angle.observation:
            parts.append(f"OBSERVATION: {angle.observation}")
        if angle.take:
            parts.append(f"TAKE: {angle.take}")
        if angle.concrete_details:
            parts.append(f"CONCRETE DETAILS: {', '.join(angle.concrete_details)}")
        if angle.tension:
            parts.append(f"TENSION: {angle.tension}")
        return "\n".join(parts)

    async def _llm_generate_evergreen_angle(
        self,
        pillar: ContentPillar,
        avoid_patterns: Dict[str, Any],
    ) -> str:
        """For no-trend posts, ask the model to derive a specific angle (not a random methodology)."""
        recent_topics = ", ".join(avoid_patterns.get("recent_topics", [])[:5])
        pillar_label = pillar.value.replace("_", " ").upper()

        prompt = f"""Pick ONE specific angle for an evergreen Jesse A. Eisenbalm post in the pillar {pillar_label}.

Not a methodology. A real angle: a specific observation + Jesse's one-sentence take + one concrete anchor detail.

AVOID these recent topics: {recent_topics or "(none)"}

Return JSON: {{"observation": "...", "take": "...", "concrete_details": ["..."], "tension": "..."}}"""
        try:
            result = await self.generate(prompt=prompt, response_format="json")
            data = result.get("content", {}) if isinstance(result, dict) else {}
            if isinstance(data, dict):
                angle = StructuredAngle.from_dict(data)
                if angle and angle.is_usable():
                    return self._format_structured_angle(angle)
        except Exception as e:
            self.logger.warning(f"Evergreen angle LLM call failed: {e}")

        # Minimal fallback — not random methodology, just a pillar-level nudge
        return (
            f"Evergreen post in {pillar_label}. Find ONE small, specific thing Jesse noticed "
            f"in the world. State Jesse's one-sentence take. Ground it in a concrete detail "
            f"that didn't exist before this post."
        )

    async def _coherent_voice_and_ending(
        self,
        pillar: ContentPillar,
        specific_angle: str,
        structured_angle: Optional[StructuredAngle],
        avoid_patterns: Dict[str, Any],
    ) -> tuple:
        """Pick voice_modifier + ending_style coherently with the angle, not by independent dice."""
        voice_keys = list(self.voice_modifiers.keys())

        # Build the set of ending style keys preferred for this pillar
        pillar_ending_weights = {
            ContentPillar.AI_SLOP: ["door_closing", "abrupt_stop", "mirror_turn"],
            ContentPillar.AI_SAFETY: ["door_closing", "quiet_specificity", "earned_warmth"],
            ContentPillar.AI_ECONOMY: ["abrupt_stop", "door_closing", "the_pivot"],
            ContentPillar.RITUALS: ["earned_warmth", "quiet_specificity", "the_pivot"],
            ContentPillar.HUMANITY: ["earned_warmth", "quiet_specificity", "mirror_turn"],
        }
        preferred_endings = pillar_ending_weights.get(pillar, list(self.ending_styles.keys()))
        recent_endings = avoid_patterns.get("recent_endings", []) or []
        available_endings = [e for e in preferred_endings if e not in recent_endings] or preferred_endings

        angle_blurb = specific_angle[:700] if specific_angle else ""

        prompt = f"""Given the angle below, pick the single best-fitting voice modifier and ending style for a Jesse A. Eisenbalm post.

PILLAR: {pillar.value}

ANGLE:
{angle_blurb}

VOICE MODIFIER OPTIONS (pick exactly one key):
{', '.join(voice_keys)}

ENDING STYLE OPTIONS (pick exactly one key):
{', '.join(available_endings)}

Pick the voice whose energy actually matches the take, and the ending style whose rhythm actually suits the angle. Don't pick "the expected" choice — pick the best one.

Return JSON: {{"voice": "<key>", "ending": "<key>"}}"""

        voice_key = None
        ending_key = None
        try:
            result = await self.generate(prompt=prompt, response_format="json")
            data = result.get("content", {}) if isinstance(result, dict) else {}
            if isinstance(data, dict):
                v = str(data.get("voice", "")).strip()
                e = str(data.get("ending", "")).strip()
                if v in self.voice_modifiers:
                    voice_key = v
                if e in self.ending_styles and e in available_endings:
                    ending_key = e
        except Exception as e:
            self.logger.warning(f"Coherent voice/ending LLM call failed: {e}")

        if voice_key is None:
            voice_key = random.choice(voice_keys)
        if ending_key is None:
            ending_key = random.choice(available_endings)

        voice_modifier = self.voice_modifiers[voice_key]
        ending_options = self.ending_styles[ending_key]
        ending_style = random.choice(ending_options)

        return ending_style, voice_modifier

    def _generate_creative_direction(
        self,
        pillar: ContentPillar,
        trending_context: Optional[str]
    ) -> str:
        """Generate creative direction aligned with the Five Questions"""

        directions = {
            ContentPillar.AI_SLOP: [
                "We ARE AI slop. React to a real example of AI-generated content with the energy of a sommelier rating cheap wine. Standards, not shame.",
                "Dead Internet Theory is getting realer. Find a specific instance where AI content passed as human — or human content got flagged as AI. The gap IS the content.",
                "Someone made something genuinely cool with AI tools. Celebrate it. Jesse loves democratized creation — it's the low-effort flood Jesse hates.",
                "Rate something Jesse made. Be honest. Be a slop brand with standards. The self-awareness is the bit.",
                "AI content is everywhere. Most of it is invisible. Point at a specific example that proves the internet is changing under everyone's feet.",
                "Find a real example of AI-generated content going viral as 'real.' The horror isn't sci-fi. It's boring. It's already happening.",
            ],
            ContentPillar.AI_SAFETY: [
                "A safety paper dropped. Read the abstract. Skip the math. Translate the 'so what' for someone scrolling LinkedIn at 11pm.",
                "New AI regulation news. Translate the legalese. Jesse is the calm friend who actually read the document.",
                "The scariest AI story this week sounds boring. That's the point. 'Automated hiring system' is scarier than 'superintelligence.' Find the real one.",
                "A lab made a safety commitment. Track whether they kept it. The gap between promise and action is where Jesse lives.",
                "Compare the scary headline to the primary source. Rate it on a panic scale. Be the friend who actually read the paper.",
                "An AI capability got real enough to worry about. Extrapolate exactly one step — not ten. That step is the content.",
            ],
            ContentPillar.AI_ECONOMY: [
                "Follow the money. A company just spent billions on AI infrastructure. The gap between investment and realized value IS the story.",
                "A specific sector is being disrupted — not 'all jobs' generically. Find the granular story. Name the industry, the role, the shift.",
                "Quarterly earnings just dropped. Find the AI capex number. The gap between what they spent and what they got is the content.",
                "The hype cycle is hyping. Track a specific claim vs. reality. Jesse follows the money, not the press releases.",
                "Someone got laid off and someone else got funded. These are probably related. Connect the dots with deadpan precision.",
                "The bubble question isn't 'is it?' — it's 'for whom and when?' Write about the specifics, not the abstraction.",
            ],
            ContentPillar.RITUALS: [
                "Name a human technology that predates and will outlast AI. Write about it with the intensity it deserves.",
                "The most radical act in an era of algorithmic acceleration is slowing down on purpose. Make the case with one specific ritual.",
                "Attention is a contested resource — AI wants it, platforms want it, your boss wants it. What helps you keep it? Be specific.",
                "You have a part that's excited about AI, a part that's terrified, and a part that's doom-scrolling. All three are valid. Write from one.",
                "Something small you do every day that no algorithm can replicate or optimize. Celebrate it with too much intensity.",
                "The AI conversation is polarized. Write something that acknowledges real fears without becoming a culture war post.",
            ],
            ContentPillar.HUMANITY: [
                "What does it mean to live well when 'human' is being renegotiated? Sit in the question. Don't answer it.",
                "Celebrate something irreducibly human — grief, joy, improvisation, getting it wrong. Jesse notices these things because Jesse can't do them.",
                "Write something that makes someone feel MORE HUMAN after reading it. Not smarter. Not optimized. More human.",
                "Jesse observes humans doing something AI literally cannot. The observation is warm. The subtext is envy.",
                "A small act of human connection that no technology can improve upon. Notice it. Describe it. Leave it alone.",
                "The philosophical heart: what matters when machines can do most things? Whatever is left is the content.",
            ],
        }

        pillar_directions = directions.get(pillar, directions[ContentPillar.AI_SLOP])
        return random.choice(pillar_directions)

    def _generate_specific_angle(
        self,
        pillar: ContentPillar,
        trending_context: Optional[str]
    ) -> str:
        """DEPRECATED — kept only for external callers.

        Angle generation now happens in _select_creative_strategy, where:
          - structured_angle from the curator is used verbatim when present
          - no-trend posts derive an angle via _llm_generate_evergreen_angle
        This method no longer random-selects methodology strings for trend posts.
        """
        if trending_context:
            return (
                "React to the news in the TRENDING TOPIC block. Extract ONE concrete detail "
                "(a number, a name, a quote) and build the post around it. State Jesse's take "
                "in one sentence. Find the tension between claim and reality."
            )

        scenarios = {
            ContentPillar.AI_SLOP: [
                "Find a real example of AI content that went viral. Was it good? Was it slop? Jesse rates it like a sommelier — with standards.",
                "Someone used AI to make something genuinely creative. Celebrate the craft, not just the tool. Kid-with-a-camcorder energy.",
                "The gap between 'AI-generated' and 'AI-created' is where the interesting content lives. Explore it.",
                "Jesse reviews Jesse's own AI-generated content. Meta? Yes. Honest? Also yes.",
            ],
            ContentPillar.AI_SAFETY: [
                "Translate a recent safety paper for someone who doesn't read arXiv. The 'so what' is the content.",
                "An AI system did something unexpected this week. Not sci-fi unexpected — boring unexpected. That's scarier.",
                "A government proposed AI regulation. Translate the legalese. Jesse is the calm friend who read the bill.",
                "Compare what a lab promised on safety vs. what they actually shipped. The delta is the content.",
            ],
            ContentPillar.AI_ECONOMY: [
                "A company just spent billions. What did they get? Follow the money with deadpan precision.",
                "A specific job category is changing — not 'all jobs.' Name the role. Name the shift. Be granular.",
                "The AI bubble question for today: who specifically benefits and who specifically doesn't? Name names.",
                "An earnings call just happened. Find the AI line item. The gap between spend and value is the story.",
            ],
            ContentPillar.RITUALS: [
                "Name one thing you do with your body every day that no algorithm can optimize. Write about it with too much reverence.",
                "Attention is the contested resource of our era. Write about one practice that helps you keep it. Be specific.",
                "The most radical act right now is doing something slowly on purpose. Make the case. Pick the ritual.",
                "Something predates AI by centuries and will outlast it. Write about it like it's the most important technology ever invented.",
            ],
            ContentPillar.HUMANITY: [
                "Jesse notices something humans do that AI literally cannot. The observation is genuine. The envy is real.",
                "Write about a small human moment — not a grand one — that makes the case for being alive.",
                "What does it mean to live well when machines can do most things? Sit in the question. Don't rush the answer.",
                "Celebrate getting it wrong. Making something ugly. Loving it anyway. The irreducibly human.",
            ],
        }

        return random.choice(scenarios.get(pillar, scenarios[ContentPillar.AI_SLOP]))

    def _select_ending_style(
        self,
        pillar: ContentPillar,
        avoid_patterns: Dict[str, Any]
    ) -> str:
        """Select a varied ending style"""

        recent_endings = avoid_patterns.get("recent_endings", [])

        pillar_ending_weights = {
            ContentPillar.AI_SLOP: ["door_closing", "abrupt_stop", "mirror_turn"],
            ContentPillar.AI_SAFETY: ["door_closing", "quiet_specificity", "earned_warmth"],
            ContentPillar.AI_ECONOMY: ["abrupt_stop", "door_closing", "the_pivot"],
            ContentPillar.RITUALS: ["earned_warmth", "quiet_specificity", "the_pivot"],
            ContentPillar.HUMANITY: ["earned_warmth", "quiet_specificity", "mirror_turn"],
        }
        
        preferred = pillar_ending_weights.get(pillar, list(self.ending_styles.keys()))
        
        # Avoid recently used
        available = [e for e in preferred if e not in recent_endings]
        if not available:
            available = preferred
        
        style_key = random.choice(available)
        style_options = self.ending_styles[style_key]
        
        return random.choice(style_options)

    def _match_trend_to_pillar(self, trending_context: str, avoid_patterns: dict = None) -> ContentPillar:
        """Match a trending topic to the best Five Questions theme.

        Applies recency penalties so a trend that *could* be economy won't be
        classified as economy if the last 2 posts were already economy.
        """

        trend_lower = trending_context.lower()
        avoid_patterns = avoid_patterns or {}

        # Check for explicit theme tags from the trend service / theme classifier
        theme_map = {
            "ai_slop": ContentPillar.AI_SLOP,
            "ai_content": ContentPillar.AI_SLOP,
            "ai_safety": ContentPillar.AI_SAFETY,
            "ai_regulation": ContentPillar.AI_SAFETY,
            "ai_economy": ContentPillar.AI_ECONOMY,
            "ai_labor": ContentPillar.AI_ECONOMY,
            "rituals": ContentPillar.RITUALS,
            "human_practice": ContentPillar.RITUALS,
            "humanity": ContentPillar.HUMANITY,
            "humanity_tech": ContentPillar.HUMANITY,
        }
        for theme_key, pillar in theme_map.items():
            if theme_key in trend_lower:
                return pillar

        # Score each theme by keyword matches — balanced at ~20 keywords each
        pillar_keywords = {
            ContentPillar.AI_SLOP: [
                'ai generated', 'deepfake', 'ai content', 'slop', 'dead internet',
                'synthetic', 'generative', 'ai art', 'ai image', 'ai video',
                'ai music', 'midjourney', 'stable diffusion', 'dall-e', 'sora',
                'ai creator', 'tiktok ai', 'bot', 'spam', 'fake',
            ],
            ContentPillar.AI_SAFETY: [
                'safety', 'alignment', 'regulation', 'eu ai act', 'guardrail',
                'anthropic', 'miri', 'arc eval', 'redwood', 'oversight',
                'rogue', 'risk', 'existential', 'superintelligence', 'agi',
                'executive order', 'ai bill', 'ai policy', 'incident',
                'bias', 'jailbreak', 'misuse',
            ],
            ContentPillar.AI_ECONOMY: [
                'layoff', 'hiring', 'capex', 'earnings', 'nvidia',
                'billion', 'funding', 'startup', 'valuation', 'bubble',
                'labor', 'workforce', 'automation', 'revenue', 'profit',
                'investment', 'salary', 'stock', 'ipo', 'acquisition',
            ],
            ContentPillar.RITUALS: [
                'wellness', 'self-care', 'burnout', 'mental health', 'mindful',
                'meditation', 'attention', 'ritual', 'habit', 'balance',
                'therapy', 'anxiety', 'stress', 'rest', 'sleep', 'grounded',
                'disconnect', 'boundary', 'slow', 'presence', 'breathe',
            ],
            ContentPillar.HUMANITY: [
                'human', 'joy', 'grief', 'love', 'connection', 'community',
                'kindness', 'empathy', 'compassion', 'meaning', 'purpose',
                'philosophy', 'beauty', 'art', 'creativity', 'embodiment',
                'touch', 'nature', 'awe', 'gratitude', 'wonder',
            ],
        }

        scores = {}
        for pillar, keywords in pillar_keywords.items():
            score = sum(1 for kw in keywords if kw in trend_lower)
            if score > 0:
                scores[pillar] = score

        # Apply recency penalty — halve score for saturated pillars
        recent_pillars = avoid_patterns.get("recent_pillars", [])
        from collections import Counter
        pillar_counts = Counter(recent_pillars)
        for pillar in list(scores.keys()):
            if pillar_counts.get(pillar.value, 0) >= 2:
                scores[pillar] = scores[pillar] * 0.3  # Heavy penalty

        if scores:
            return max(scores, key=scores.get)

        # Default: AI Slop is the most flexible theme
        if any(kw in trend_lower for kw in ['ai', 'chatgpt', 'gpt', 'llm', 'claude', 'copilot', 'gemini']):
            return ContentPillar.AI_SLOP

        return ContentPillar.AI_SLOP

    def _weighted_pillar_selection(self, avoid_patterns: Dict[str, Any]) -> ContentPillar:
        """Select theme with intelligent distribution — even spread across Five Questions.

        Themes recently used get their weight halved so the system naturally
        rotates through all five questions rather than clustering on one.
        """

        # Start with even distribution across the five themes
        weights = {
            ContentPillar.AI_SLOP: 20,
            ContentPillar.AI_SAFETY: 20,
            ContentPillar.AI_ECONOMY: 20,
            ContentPillar.RITUALS: 20,
            ContentPillar.HUMANITY: 20,
        }

        recent = avoid_patterns.get("recent_pillars", [])

        # Heavily penalize recently used themes to force variety
        weighted = []
        for pillar, weight in weights.items():
            if pillar.value in recent:
                weight = max(2, weight // 4)  # Strong penalty, but never zero
            weighted.extend([pillar] * weight)

        return random.choice(weighted)

    def _select_format_for_pillar(self, pillar: ContentPillar) -> PostFormat:
        """Select appropriate format for the Five Questions theme"""

        preferences = {
            ContentPillar.AI_SLOP: [PostFormat.OBSERVATION, PostFormat.CONTRAST, PostFormat.LIST_SUBVERSION, PostFormat.STORY],
            ContentPillar.AI_SAFETY: [PostFormat.OBSERVATION, PostFormat.STORY, PostFormat.PHILOSOPHY, PostFormat.CONTRAST],
            ContentPillar.AI_ECONOMY: [PostFormat.OBSERVATION, PostFormat.CONTRAST, PostFormat.QUESTION, PostFormat.STORY],
            ContentPillar.RITUALS: [PostFormat.PHILOSOPHY, PostFormat.STORY, PostFormat.CONFESSION, PostFormat.CELEBRATION],
            ContentPillar.HUMANITY: [PostFormat.PHILOSOPHY, PostFormat.CELEBRATION, PostFormat.STORY, PostFormat.QUESTION],
        }
        
        return random.choice(preferences.get(pillar, [PostFormat.OBSERVATION]))

    def _build_angle_block(self, strategy: ContentStrategy) -> str:
        """Inject the angle as four discrete fields when we have a structured angle.

        This is the load-bearing replacement for the old "THE SPECIFIC ANGLE" block.
        The generator used to receive a random methodology string and had to invent
        the POV itself — which caused regression to template openers. Now it receives
        the POV pre-formed and does execution.
        """
        angle = strategy.structured_angle
        if angle and angle.is_usable():
            details = "\n".join(f"- {d}" for d in angle.concrete_details) if angle.concrete_details else "- (no concrete details supplied)"
            return f"""═══════════════════════════════════════════════════════════════════════════════
THE ANGLE (express this — do not regenerate it)
═══════════════════════════════════════════════════════════════════════════════

THE OBSERVATION (what Jesse noticed that others missed):
{angle.observation or "(not supplied — if absent, derive from concrete details below)"}

JESSE'S TAKE (Jesse's one-sentence POV — this IS the post's spine):
{angle.take}

CONCRETE MATERIAL (use these real details — do NOT invent substitutes or paraphrase):
{details}

THE TENSION (where the claim and reality diverge — the satirical seam):
{angle.tension or "(not supplied — if absent, surface the gap between the observation and what the announcement implies)"}

HOW TO USE THIS ANGLE:
- The take above is the post's spine. If your draft doesn't express the take, you wrote a different post.
- Build around the concrete material. If you need a number, name, or place, it comes from the list above.
- Do NOT open with "Diagnosed: [Condition]" unless the take itself is a diagnostic assessment.
- Your job is execution: turn this angle into 40-80 words of Jesse voice. Don't re-form the POV.
"""
        # No structured angle — fall back to the legacy slot so callers that pass a
        # pre-formatted specific_angle (e.g. evergreen posts) still work.
        return f"""THE SPECIFIC ANGLE (this is your entry point, not your cage):
{strategy.specific_angle}"""

    def _build_gold_examples_block(self, gold_examples: List[Dict[str, Any]]) -> str:
        """Inject retrieved gold-standard posts as voice-matching reference (Fix #4).

        Labeled explicitly as voice reference, NOT templates to copy. The goal is
        that the retrieved posts rotate per-generation, anchoring Jesse's voice
        without the model collapsing onto a single example.
        """
        if not gold_examples:
            return ""

        example_lines = []
        for i, ex in enumerate(gold_examples, 1):
            content = (ex.get("content") or "").strip()
            pillar = ex.get("pillar") or "?"
            notes = ex.get("notes") or ""
            header = f"─── Example {i} (pillar={pillar})"
            if notes:
                header += f" — {notes}"
            header += " ───"
            example_lines.append(header)
            example_lines.append(content)
            example_lines.append("")  # blank line between examples

        examples_text = "\n".join(example_lines).strip()
        return f"""
═══════════════════════════════════════════════════════════════════════════════
STUDY THESE EXAMPLES (voice-matching reference — do NOT copy)
═══════════════════════════════════════════════════════════════════════════════

These are prior Jesse posts that landed well with the audience. They are here so
you internalize voice — rhythm, specificity, deadpan commitment, the AI/lips
tension. Do NOT copy their angles, structures, or specific details. Write a new
post using the angle and trend above.

{examples_text}
───────────────────────────────────────────────────────────────────────────────
"""

    def _build_creative_prompt(
        self,
        strategy: ContentStrategy,
        trending_context: Optional[str],
        avoid_patterns: Dict[str, Any],
        memory_context: str = "",
        gold_examples: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Build a prompt that actually encourages creativity"""

        # Get some random creative elements to inspire
        hook_type = random.choice(list(self.creative_hooks.keys()))
        hook_examples = self.creative_hooks[hook_type]
        sampled_hooks = random.sample(hook_examples, min(2, len(hook_examples)))

        # Absurdist elements are now generated by the LLM, not hardcoded

        # Trending section
        trend_section = f"""
{trending_context}

CRITICAL: Do NOT parrot the headline. Do NOT start with "Today's trending headline:"
or any preamble about the news. React AS JESSE — the headline is raw material, not your opening line.

THE JESSE METHOD FOR NEWS:
1. GROUND IT: Reference the real story — source, numbers, claims. But start with YOUR take, not theirs.
2. FIND THE DELTA: The absurdism is the gap between the claim and reality. Point at it.
3. THE AI ANGLE: Brag about AI superiority — then hit the wall: lips, skin, touch.
4. PLAY IT DEAD STRAIGHT: Full commitment. No winking. The deadpan IS the humor.
""" if trending_context else """
No trend provided — write from Jesse's inner world. An AI agent musing about
humans, lips, and the absurdity of selling physical products in a digital age.
"""

        # Avoid section
        recent_topics = ""
        recent_hooks = ""
        if avoid_patterns:
            if avoid_patterns.get("recent_topics"):
                recent_topics = ', '.join(avoid_patterns['recent_topics'][:3])
            if avoid_patterns.get("recent_hooks"):
                recent_hooks = ', '.join(avoid_patterns['recent_hooks'][:2])

        # Supervisor-identified avoid phrases (closed loop from QualityDriftAgent).
        # When drift is detected — recycled tube numbers, generic tagline phrases,
        # overused ritual closers — the supervisor writes them here and they
        # appear in the generator prompt on the very next generation.
        learned_avoids_block = ""
        if avoid_patterns and avoid_patterns.get("learned_avoid_phrases"):
            by_cat: Dict[str, List[str]] = {}
            for entry in avoid_patterns["learned_avoid_phrases"][:30]:
                cat = entry.get("category") or "phrase"
                phrase = entry.get("phrase") or ""
                if phrase:
                    by_cat.setdefault(cat, []).append(phrase)
            if by_cat:
                lines = [
                    "⛔ SUPERVISOR-FLAGGED AVOIDS (the Quality Drift supervisor caught these "
                    "recycling / drifting across recent posts — do NOT reuse them):"
                ]
                for cat, phrases in by_cat.items():
                    lines.append(f"  • [{cat}] " + "  |  ".join(f'"{p}"' for p in phrases[:15]))
                learned_avoids_block = "\n".join(lines)

        # Build the angle injection block
        angle_block = self._build_angle_block(strategy)

        # Build the gold-standard examples block (Fix #4 retrieval) — empty string if no corpus
        gold_block = self._build_gold_examples_block(gold_examples or [])

        return f"""Write a LinkedIn post as Jesse A. Eisenbalm. One post. Make it count.
{gold_block}

═══════════════════════════════════════════════════════════════════════════════
YOUR MISSION FOR THIS POST
═══════════════════════════════════════════════════════════════════════════════

WHICH OF THE FIVE QUESTIONS ARE YOU ANSWERING?
{strategy.pillar.value.upper().replace('_', ' ')}
(If you can't feel this question driving the post, it has no spine. Stop and reconnect.)

THE CREATIVE DIRECTION:
{strategy.creative_direction}

{angle_block}

═══════════════════════════════════════════════════════════════════════════════
JESSE'S MOOD TODAY
═══════════════════════════════════════════════════════════════════════════════

{strategy.voice_modifier}

Channel this mood FULLY. Don't hedge. Don't dilute it with other emotions.
If Jesse is amused, be genuinely amused. If Jesse is concerned, let it land.
If Jesse is delighted, let the delight be specific and real.

═══════════════════════════════════════════════════════════════════════════════
THE LANDING (How to end THIS post)
═══════════════════════════════════════════════════════════════════════════════

End in the neighborhood of: "{strategy.ending_style}"

This is a DIRECTION, not a script. The ending should feel inevitable in
retrospect but surprising when it arrives.

FORBIDDEN ENDINGS (unless specifically directed above):
- Any "Stop. Breathe. [anything]" or "Apply balm." ritual closer — this isn't brand canon
- Ending with just "$8.99"
- A question asking for engagement
- Any ending you've used in the last 5 posts
- Trailing off without impact

GREAT ENDINGS feel like:
- The last line of a joke you'll think about later
- A door closing with a satisfying click
- The moment after someone says something true and the room goes quiet
- A camera pulling back to reveal the full picture

═══════════════════════════════════════════════════════════════════════════════
TRENDING TOPIC TO REACT TO
═══════════════════════════════════════════════════════════════════════════════
{trend_section}
═══════════════════════════════════════════════════════════════════════════════
CREATIVE AMMUNITION (Use for texture, not structure)
═══════════════════════════════════════════════════════════════════════════════

HOOK TYPE: {hook_type}

BANNED OPENERS (never start a post with these):
- "Today's trending headline:"
- "Breaking:"
- "Ever feel..."
- "What if I told you..."
- "Confession:"
- "Unpopular opinion:"
- "In a world where..."
- Any preamble about the news — just REACT as Jesse

HOOK DIRECTION (riff on the energy, don't copy):
- {sampled_hooks[0]}
- {sampled_hooks[1] if len(sampled_hooks) > 1 else sampled_hooks[0]}

TEXTURE DETAILS — INVENT YOUR OWN. Do NOT reuse these from previous posts.
Every post needs FRESH, specific details: a precise number, a specific place,
a specific action. Make them up. Make them weird. Make them feel lived-in.
Generic = death. But repeating the same "specific" detail is worse than generic.

VARIETY GUARD — avoid these for freshness:
❌ Recent topics covered: {recent_topics}
❌ Recent opening moves: {recent_hooks}

{learned_avoids_block}

{memory_context}

═══════════════════════════════════════════════════════════════════════════════
THE BRIEF
═══════════════════════════════════════════════════════════════════════════════

LENGTH: 40-80 words. HARD CEILING. Count your words. If over 80, CUT.
The best posts are 40-60 words. Brevity is the craft, not a constraint.
If you can say it in 45 words instead of 70, say it in 45.

THE SCREENSHOT TEST:
Before you finalize, ask: "Would someone screenshot this and send it to a
friend who has never heard of Jesse A. Eisenbalm?"
If the answer is no, you haven't found the idea yet. Dig deeper.

THE SURPRISE TEST:
Read your post and find the moment of surprise. Where does the reader think
"wait — did a lip balm brand just say that?" If there's no such moment,
the post is playing it safe. Playing it safe is the only real failure.

THE RECOGNITION TEST:
Does the reader see themselves in this? Not in a "relatable content" way —
in a "oh god, that's exactly what happened in my 2pm meeting" way.
Specificity creates recognition. Recognition creates screenshots.

THE HUMANITY TEST (for HOW TO COPE & WHY IT MATTERS posts):
Does this make someone feel MORE HUMAN after reading it?
Not smarter. Not optimized. More human. If it doesn't, it belongs to a
different brand.

MUST:
- Commit to the bit with zero hesitation
- Surprise the reader — if the take is obvious, it's the wrong take
- Be weirdly, specifically, almost uncomfortably detailed
- Land the ending with impact — no trailing off, no soft landings
- Feel like it was written by a person with a pulse, not a content calendar

MUST NOT:
- EVER break character or acknowledge the absurdity from outside it
- Sound like marketing, advertising, or "content" in any recognizable form
- Be the safe version of the idea — if there's a bolder version, write that one
- Target individuals negatively
- Use hashtags or ask for engagement
- Explain the joke — if it needs explaining, it's not working
- Start with "Breaking:", "Today's trending headline:", or any news-anchor preamble
- Parrot the headline back — you're reacting, not summarizing
- Recycle the same structural rhythm as recent posts
- Use "Meanwhile, I/AI..." — this is a crutch transition
- Use "[Topic]? More like [snarky rewrite]" — Reddit comment energy
- Lecture the reader with "Remember:" or give them advice
- Force a lip balm/lips/moisturize reference into every post (use in ~1/4 posts)
- Use "But hey," as a pivot — find a real transition or don't transition
- Follow the formula: news → AI take → lips callback → wrap. BREAK THE PATTERN.

═══════════════════════════════════════════════════════════════════════════════
BEFORE YOU WRITE: THE CREATIVE GUT CHECK
═══════════════════════════════════════════════════════════════════════════════

Ask yourself these three questions:

1. WHICH OF THE FIVE QUESTIONS AM I ANSWERING?
   (THE WHAT / THE WHAT IF / THE WHO PROFITS / THE HOW TO COPE / THE WHY IT MATTERS)
   If you don't know, stop. Figure it out. A post without a spine is just noise.

2. WHAT WOULD JESSE ACTUALLY SAY ABOUT THIS?
   Not "what would a brand say." What would this specific character — someone
   who hand-numbers lip balm tubes at 3am and donates profits to charity
   because capitalism is absurd — what would THEY say?

3. IS THIS THE DUMBEST VERSION OF THE IDEA?
   The "smart" version is taken. The "professional" version is what every
   other brand account is posting right now. The dumb version — the one that
   feels slightly wrong, slightly too specific, slightly too committed —
   that's where the magic lives.

Now write something that makes someone stop scrolling."""

    # Patterns that are unambiguously banned per the system prompt's hard rules.
    # These fire ONLY for literal, uncontroversial violations — the regex is
    # intentionally narrow so it never catches earned use. Subtle failures
    # (broken metaphors, hollow parallelism) are the validators' job.
    HARD_RULE_PATTERNS = [
        ("hashtag", r"(?mi)(?:^|\s)#[A-Za-z][A-Za-z0-9_]{1,}"),
        ("in_a_world_where_opener", r"(?mi)^\s*[\"\u201c]?\s*in a world where\b"),
        ("ever_feel_opener", r"(?mi)^\s*[\"\u201c]?\s*ever (?:feel|watched|wondered)\b"),
        ("picture_this_opener", r"(?mi)^\s*[\"\u201c]?\s*picture this\b"),
        ("imagine_a_world_opener", r"(?mi)^\s*[\"\u201c]?\s*imagine a world\b"),
        ("what_if_i_told_you_opener", r"(?mi)^\s*[\"\u201c]?\s*what if i told you\b"),
        ("confession_opener", r"(?mi)^\s*[\"\u201c]?\s*confession:\s"),
        ("unpopular_opinion_opener", r"(?mi)^\s*[\"\u201c]?\s*unpopular opinion:\s"),
        ("engagement_bait", r"(?i)\b(?:thoughts\?|share this|like if you agree|agree\?\s*$)"),
    ]

    def _build_hard_rule_retry_prompt(self, original_prompt: str, bad_content: str, violations: list) -> str:
        """Build a short retry prompt that quotes the specific violation."""
        lines = ["You violated hard brand rules. Fix THIS post:"]
        lines.append("")
        lines.append(f"YOUR LAST DRAFT:\n{bad_content}")
        lines.append("")
        lines.append("SPECIFIC VIOLATIONS:")
        human_rule_names = {
            "hashtag": "Hashtag used — NEVER use hashtags",
            "in_a_world_where_opener": "Opened with 'In a world where...' — this is on the BANNED OPENERS list",
            "ever_feel_opener": "Opened with 'Ever feel/watched/wondered' — BANNED opener",
            "picture_this_opener": "Opened with 'Picture this' — BANNED opener (don't invent scenarios)",
            "imagine_a_world_opener": "Opened with 'Imagine a world' — BANNED opener (movie-trailer framing)",
            "what_if_i_told_you_opener": "Opened with 'What if I told you' — BANNED opener",
            "confession_opener": "Opened with 'Confession:' — BANNED opener",
            "unpopular_opinion_opener": "Opened with 'Unpopular opinion:' — BANNED opener",
            "engagement_bait": "Engagement bait (thoughts? / share this / like if you agree) — NEVER ask for engagement",
        }
        for name, matched in violations:
            human = human_rule_names.get(name, name)
            lines.append(f"- {human} (matched: \"{matched[:80]}\")")
        lines.append("")
        lines.append("Rewrite the post KEEPING the same angle and concrete details, but:")
        lines.append("- Start with a different, specific opener (ideally one grounded in a concrete detail from the trend)")
        lines.append("- Remove ALL hashtags")
        lines.append("- Remove engagement-bait questions")
        lines.append("")
        lines.append("Return the same JSON schema as before.")
        return "\n".join(lines)

    def _unpack_generation_content(self, result) -> str:
        """Pull the post text out of a generation result — shared with the main path."""
        if not isinstance(result, dict):
            return str(result or "")
        content_field = result.get("content")
        if isinstance(content_field, dict):
            if "post" in content_field:
                post_val = content_field["post"]
                if isinstance(post_val, dict):
                    for key in ("content", "body", "text"):
                        if post_val.get(key):
                            return str(post_val[key])
                elif isinstance(post_val, str):
                    return post_val
            for key in ("content", "body", "text", "post_content"):
                if content_field.get(key):
                    return str(content_field[key])
        elif isinstance(content_field, str):
            try:
                parsed = json.loads(content_field)
                if isinstance(parsed, dict):
                    for key in ("content", "body", "text"):
                        if parsed.get(key):
                            return str(parsed[key])
            except json.JSONDecodeError:
                return content_field
        return ""

    def _extract_content_data(self, result):
        """Pull the structured content_data dict out of a generation result."""
        if not isinstance(result, dict):
            return None
        content_field = result.get("content")
        if isinstance(content_field, dict):
            if "post" in content_field and isinstance(content_field["post"], dict):
                return content_field["post"]
            return content_field
        if isinstance(content_field, str):
            try:
                parsed = json.loads(content_field)
                if isinstance(parsed, dict):
                    return parsed.get("post", parsed)
            except json.JSONDecodeError:
                pass
        return None

    def _check_hard_rule_violations(self, content: str):
        """Return a list of (rule_name, matched_text) for any hard rules the content violates."""
        import re as _re
        violations = []
        for name, pattern in self.HARD_RULE_PATTERNS:
            m = _re.search(pattern, content)
            if m:
                violations.append((name, m.group(0).strip()))
        return violations

    def _clean_content(self, content: str) -> str:
        """Clean generated content and enforce hard word limit"""

        # Remove any markdown
        content = content.replace("**", "").replace("*", "")

        # Remove quotes if wrapped
        if content.startswith('"') and content.endswith('"'):
            content = content[1:-1]

        # Strip parrot preambles the LLM sometimes adds
        parrot_prefixes = [
            "Today's trending headline:",
            "Today's trending news:",
            "Trending headline:",
            "Breaking:",
            "BREAKING:",
            "Here's today's post:",
            "LinkedIn Post:",
        ]
        for prefix in parrot_prefixes:
            if content.lower().startswith(prefix.lower()):
                content = content[len(prefix):].strip()
                self.logger.info(f"Stripped parrot prefix: '{prefix}'")

        # DETERMINISTIC STRIP — runs on every draft including revisions. Some
        # patterns the system prompt bans keep showing up in output because the
        # model has strong priors for them; stripping post-hoc is cheaper than
        # re-prompting and never fails.
        import re as _re

        # 1) Remove hashtags entirely (the spec: no hashtags, period).
        original_len = len(content)
        content = _re.sub(r"(?:^|\s)#[A-Za-z][A-Za-z0-9_]+", "", content)
        if len(content) != original_len:
            self.logger.info("Stripped hashtags from content")

        # 2) Strip "Stop. Breathe. [anything]." ritual closer wherever it appears —
        # not brand canon. Variants seen in production: Stop. Breathe. Apply. /
        # Breathe. Balm. / Breathe. Soothe. Matches mid-sentence AND trailing,
        # because Claude has started embedding it mid-post to dodge trailing strips.
        stop_breathe_re = _re.compile(
            r"(?:^|\s)Stop[.!]?\s*Breathe[.!]?\s*\w+[.!]?(?=\s|$)",
            _re.IGNORECASE,
        )
        if stop_breathe_re.search(content):
            content = stop_breathe_re.sub(" ", content)
            # Collapse any double-spaces the substitution created
            content = _re.sub(r"[ \t]{2,}", " ", content).strip()
            self.logger.info("Stripped 'Stop. Breathe. X' ritual closer")

        # 3) Strip trailing engagement-bait ("Thoughts?", "Share this.", etc.)
        bait_re = _re.compile(
            r"(?:\s*\n+|\s+)(?:thoughts\??|share this|agree\??|like if you agree)[.!?]*\s*$",
            _re.IGNORECASE,
        )
        if bait_re.search(content):
            content = bait_re.sub("", content).rstrip()
            self.logger.info("Stripped trailing engagement bait")

        # Fix spacing after all the strips
        lines = content.split('\n')
        lines = [line.strip() for line in lines]
        content = '\n\n'.join(line for line in lines if line)

        content = content.strip()

        # Hard word limit enforcement — truncate to 80 words max
        words = content.split()
        if len(words) > 80:
            # Try to find a sentence boundary near the limit
            truncated = ' '.join(words[:80])
            # Look for the last sentence-ending punctuation within the truncated text
            last_period = max(truncated.rfind('.'), truncated.rfind('!'), truncated.rfind('?'))
            if last_period > len(' '.join(words[:35])):  # Only use boundary if it's past 35 words
                content = truncated[:last_period + 1]
            else:
                content = truncated
            self.logger.info(f"Content truncated from {len(words)} words to {len(content.split())} words (hard ceiling)")

        return content

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
        """Get recommended content mix for a week — even distribution across Five Questions"""

        return {
            "weekly_mix": {
                "the_what (AI Slop)": "1-2 posts — Celebration AND reckoning of AI-generated content",
                "the_what_if (AI Safety)": "1 post — Make technical safety feel human",
                "the_who_profits (AI Economy)": "1 post — Follow the money, track the hype",
                "the_how_to_cope (Rituals)": "1 post — Human technologies that outlast digital ones",
                "the_why_it_matters (Humanity)": "1 post — What does it mean to live well?",
            },
            "distribution_rule": "Even spread. No theme more than 2x per week. Rotate.",
            "key_principles": [
                "Every post answers exactly ONE of the Five Questions",
                "React to real news — not invented scenarios",
                "AI superiority meets human lips — the double satire",
                "Vary hooks, endings, tone, and format across every post",
                "Specificity > generality. Name the company. Cite the number.",
            ]
        }


# Backward compatibility
ContentGeneratorAgent = ContentStrategistAgent