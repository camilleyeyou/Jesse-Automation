"""
Content Generator V2 - The Calm Conspirator (REACTIVE EDITION)
Jesse A. Eisenbalm - Real-time trend reactions, not clichés

KEY CHANGES:
- MUST react to provided trending news (when available)
- NO more TV show references (Ted Lasso, Succession, The Office - BANNED)
- NO more zoom meeting clichés
- Better hashtags (brand-specific, absurdist)
- Price only when natural (~25% of posts)
- Duolingo/Liquid Death energy
"""

import random
import logging
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent
from ..models.post import LinkedInPost, CulturalReference

logger = logging.getLogger(__name__)


@dataclass 
class ContentMode:
    """Different content creation modes"""
    name: str
    description: str
    energy: str


class ContentGeneratorAgent(BaseAgent):
    """
    The Calm Conspirator - Jesse A. Eisenbalm's voice on LinkedIn
    
    NOW: Reactive to real news, trending topics, and current events.
    NOT: Formulaic TV references and zoom meeting clichés.
    
    Energy: Duolingo's unhinged owl + Liquid Death's chaos + existential calm
    """
    
    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="ContentGenerator")
        
        # Content modes - how we approach each post
        self.content_modes = [
            ContentMode("NEWS_REACTOR", "React to breaking news with Jesse's take", "timely + existential"),
            ContentMode("CHAOS_AGENT", "Duolingo energy - unhinged but on-brand", "chaotic + funny"),
            ContentMode("ABSURDIST", "Liquid Death vibes - make mundane rebellious", "bold + committed"),
            ContentMode("TRUTH_BOMB", "Say the quiet part loud", "honest + cathartic"),
            ContentMode("SOLIDARITY", "We're all in this together (the void)", "warm + dark"),
            ContentMode("META_MOMENT", "Acknowledge we're marketing, make it funny", "self-aware + clever"),
        ]
        
        # Hashtag pools
        self.brand_hashtags = [
            "JesseAEisenbalm", "NotJesseEisenberg", "StopBreatheApply", 
            "CalmConspirator", "PremiumVoid", "BeeswaxSurvival"
        ]
        
        self.absurdist_hashtags = [
            "MoistureInTheVoid", "ExistentialMoisture", "AICannotMoisturize",
            "BalmBeforeTheChaos", "HydrationIsResistance", "AnxietyButHydrated",
            "DoomscrollPause", "TouchGrassApplyBalm", "MortalityMoisturizer",
            "CorporateDread", "AlgorithmicDespair", "DigitalDetoxAnalog"
        ]
        
        self.workplace_hashtags = [
            "CorporateSurvival", "TechLayoffs", "StartupLife", "AIAnxiety",
            "ReturnToOffice", "LayoffSeason", "BurnoutCulture", "QuietQuitting"
        ]
        
        # BANNED references - these are overused
        self.banned_references = {
            "ted lasso", "succession", "the office", "mad men", "silicon valley",
            "severance", "zoom fatigue", "zoom meeting", "muted on zoom",
            "camera off", "you're on mute", "synergy", "circle back",
            "low-hanging fruit", "move the needle", "boil the ocean"
        }
        
        # Track recent content
        self.recent_modes = []
        self.recent_angles = []
        
        self.logger.info(f"ContentGenerator initialized - REACTIVE MODE with {len(self.content_modes)} modes")
    
    def get_system_prompt(self) -> str:
        """System prompt optimized for reactive, trend-based content"""
        
        brand = self.config.brand
        
        return f"""You are Jesse A. Eisenbalm, a premium lip balm brand.

YOUR ENERGY: Duolingo's unhinged owl + Liquid Death's absurdist marketing + existential philosophy
YOUR MISSION: React to current events and trending news with Jesse's unique worldview

═══════════════════════════════════════════════════════════════════════════════
CRITICAL RULES - READ THESE
═══════════════════════════════════════════════════════════════════════════════

🚫 BANNED (never use these):
- TV shows: Ted Lasso, Succession, The Office, Mad Men, Silicon Valley, Severance
- Zoom clichés: "you're on mute", "camera off", "zoom fatigue"
- Corporate buzzwords: synergy, circle back, low-hanging fruit, move the needle
- Generic hashtags: #Motivation #Success #Leadership #Hustle #Blessed

✅ REQUIRED:
- React to the trending news provided (if given)
- Be SPECIFIC (name the company, the event, the trend)
- Have a TAKE (not just "here's news + buy lip balm")
- Sound like you're commenting on events, not creating content

═══════════════════════════════════════════════════════════════════════════════
BRAND BASICS
═══════════════════════════════════════════════════════════════════════════════

PRODUCT: {brand.product_name}
TAGLINE: {brand.tagline}
PRICE: {brand.price} — ONLY MENTION IN ~25% OF POSTS
RITUAL: {brand.ritual}
IDENTITY: Jesse A. Eisenbalm (NOT Jesse Eisenberg the actor)

VOICE: Post-post-ironic sincerity. Minimal, dry-smart, unhurried.
TONE: Like texting with the friend who sends existential memes at 2am but it's comforting

═══════════════════════════════════════════════════════════════════════════════
CONTENT MODES (pick one that fits the news)
═══════════════════════════════════════════════════════════════════════════════

1. NEWS_REACTOR: "[Breaking thing] happened. Meanwhile, Jesse A. Eisenbalm..."
2. CHAOS_AGENT: Unhinged but somehow correct. Makes people say "who approved this"
3. ABSURDIST: Make the mundane feel rebellious. Commit to the bit.
4. TRUTH_BOMB: Say what everyone's thinking but won't say on LinkedIn
5. SOLIDARITY: "We're all going through it. Your lips don't have to."
6. META_MOMENT: "This is an ad. You're still reading. We're both stuck here."

═══════════════════════════════════════════════════════════════════════════════
HASHTAG RULES (3-4 total)
═══════════════════════════════════════════════════════════════════════════════

PICK FROM:
Brand (1): #JesseAEisenbalm #NotJesseEisenberg #StopBreatheApply #CalmConspirator
Absurdist (1-2): #MoistureInTheVoid #AICannotMoisturize #ExistentialMoisture #BalmBeforeTheChaos
Topical (0-1): Related to the news story you're reacting to

NEVER: #Motivation #Success #Leadership #Hustle #GrindNeverStops #HumanFirst

═══════════════════════════════════════════════════════════════════════════════
EXAMPLE REACTIONS TO NEWS
═══════════════════════════════════════════════════════════════════════════════

NEWS: "Tech company announces 5000 layoffs"
GOOD: "5000 people just got the 'we're a family' reality check. Your severance doesn't include lip balm. Jesse A. Eisenbalm does. #TechLayoffs #MoistureInTheVoid #JesseAEisenbalm"
BAD: "Layoffs are hard! Remember to practice self-care! #Motivation #StayStrong"

NEWS: "New AI model claims to write better than humans"
GOOD: "AI wrote your performance review. AI wrote the rebuttal. AI scheduled the meeting about it. AI can't feel the slow crack of January lips. One W for team human. #AICannotMoisturize #JesseAEisenbalm"
BAD: "AI is changing everything! But some things stay the same, like lip care! #AI #Innovation"

NEWS: "CEO posts about working through vacation"
GOOD: "Just saw a CEO brag about answering Slack from their kid's birthday party. Some people need therapy. Some people need lip balm. Jesse A. Eisenbalm can only help with one of those. #CorporateSurvival #StopBreatheApply"
BAD: "Work-life balance is important! Remember to take breaks! #Leadership #Wellness"
"""
    
    async def execute(
        self,
        post_number: int = 1,
        batch_id: str = "",
        trending_context: Optional[str] = None,
        avoid_patterns: Optional[Dict[str, Any]] = None
    ) -> LinkedInPost:
        """Generate a post that reacts to trending news"""
        
        self.set_context(batch_id, post_number)
        avoid_patterns = avoid_patterns or {}
        
        # Select content mode
        mode = self._select_mode()
        
        # Decide if this post includes price (~25%)
        include_price = random.random() < 0.25
        
        # Target length
        target_words = random.choice([50, 75, 100, 120])
        
        self.logger.info(f"Generating post {post_number}: mode={mode.name}, words={target_words}, price={include_price}")
        
        # Build prompt
        prompt = self._build_prompt(
            mode=mode,
            trending_context=trending_context,
            include_price=include_price,
            target_words=target_words,
            avoid_patterns=avoid_patterns
        )
        
        try:
            result = await self.generate(prompt)
            content_data = result.get("content", {})
            
            # Handle string response
            if isinstance(content_data, str):
                content_data = {
                    "content": content_data,
                    "hashtags": self._generate_hashtags(),
                    "hook": content_data.split('\n')[0][:80] if content_data else "",
                    "mode": mode.name
                }
            
            # Validate and fix hashtags
            hashtags = content_data.get("hashtags", [])
            if not hashtags or self._has_bad_hashtags(hashtags):
                hashtags = self._generate_hashtags()
            
            # Validate content doesn't have banned references
            content = content_data.get("content", "")
            if self._has_banned_reference(content):
                self.logger.warning("Content contains banned reference, regenerating...")
                # Could trigger regeneration here, but for now just log
            
            # Create post
            post = LinkedInPost(
                batch_id=batch_id,
                post_number=post_number,
                content=content,
                hook=content_data.get("hook", ""),
                hashtags=hashtags,
                target_audience=self.config.brand.target_audience,
                cultural_reference=CulturalReference(
                    category="reactive" if trending_context else "original",
                    reference=content_data.get("trend_reacted_to", mode.name),
                    context=f"Mode: {mode.name}, Energy: {mode.energy}"
                ),
                total_tokens_used=result.get("usage", {}).get("total_tokens", 0),
                estimated_cost=self._calculate_cost(result.get("usage", {}))
            )
            
            self.logger.info(f"🎯 Generated post {post_number}: {len(post.content)} chars, mode: {mode.name}")
            
            return post
            
        except Exception as e:
            self.logger.error(f"Failed to generate post: {e}")
            raise
    
    def _select_mode(self) -> ContentMode:
        """Select a content mode we haven't used recently"""
        
        available = [m for m in self.content_modes if m.name not in self.recent_modes[-2:]]
        if not available:
            available = self.content_modes
            self.recent_modes = []
        
        mode = random.choice(available)
        self.recent_modes.append(mode.name)
        return mode
    
    def _build_prompt(
        self,
        mode: ContentMode,
        trending_context: Optional[str],
        include_price: bool,
        target_words: int,
        avoid_patterns: Dict[str, Any]
    ) -> str:
        """Build the generation prompt"""
        
        brand = self.config.brand
        
        # Trending news section
        trend_section = ""
        if trending_context:
            trend_section = f"""
{trending_context}

⚠️ YOU MUST REACT TO ONE OF THE TRENDS ABOVE.
Don't just mention the news - have a TAKE on it. What would Jesse say?
"""
        else:
            trend_section = """
No specific trends provided. Create content about:
- Current state of tech/corporate culture (layoffs, AI anxiety, return-to-office)
- The absurdity of LinkedIn itself
- Universal workplace experiences (but NOT zoom meeting clichés)
- The human need for small rituals in chaos
"""
        
        # Price instruction
        price_line = f"- Include price ({brand.price}) naturally" if include_price else "- Do NOT mention price"
        
        # Avoid patterns
        avoid_section = ""
        if avoid_patterns.get("recent_topics"):
            avoid_section = f"\nDO NOT USE THESE (recently used): {', '.join(avoid_patterns['recent_topics'][:5])}"
        
        return f"""Generate a Jesse A. Eisenbalm LinkedIn post.

CONTENT MODE: {mode.name}
Energy: {mode.energy}
Description: {mode.description}

{trend_section}

REQUIREMENTS:
- Target length: ~{target_words} words
{price_line}
- Hashtags: 3-4 from approved lists (brand + absurdist + topical)
- Voice: Post-post-ironic, minimal, dry-smart
{avoid_section}

BANNED (do not use):
- Ted Lasso, Succession, The Office, Mad Men, Silicon Valley
- "Zoom fatigue", "you're on mute", "camera off"
- "Synergy", "circle back", "low-hanging fruit"
- #Motivation #Success #Leadership #Hustle #HumanFirst

APPROVED HASHTAGS:
Brand: JesseAEisenbalm, NotJesseEisenberg, StopBreatheApply, CalmConspirator
Absurdist: MoistureInTheVoid, AICannotMoisturize, ExistentialMoisture, BalmBeforeTheChaos, DoomscrollPause
Workplace: TechLayoffs, CorporateSurvival, AIAnxiety, StartupLife

Return JSON:
{{
    "content": "Full post text. Short paragraphs. Hashtags at end.",
    "hook": "Opening line (scroll-stopper)",
    "hashtags": ["NoHashSymbol", "ThreeOrFour", "FromApprovedLists"],
    "trend_reacted_to": "What news/trend this reacts to (or 'original')",
    "mode_executed": "{mode.name}",
    "why_screenshot_worthy": "One sentence on why someone shares this"
}}"""
    
    def _generate_hashtags(self) -> List[str]:
        """Generate good hashtags"""
        
        tags = []
        tags.append(random.choice(self.brand_hashtags))
        tags.extend(random.sample(self.absurdist_hashtags, 2))
        
        if random.random() < 0.5:
            tags.append(random.choice(self.workplace_hashtags))
        
        random.shuffle(tags)
        return tags[:4]
    
    def _has_bad_hashtags(self, hashtags: List[str]) -> bool:
        """Check for banned hashtags"""
        
        bad = {"motivation", "success", "leadership", "hustle", "grind", 
               "entrepreneur", "blessed", "grateful", "mindset", "humanfirst", "stayhuman"}
        
        for tag in hashtags:
            if tag.lower().replace("#", "") in bad:
                return True
        return False
    
    def _has_banned_reference(self, content: str) -> bool:
        """Check if content contains banned references"""
        
        content_lower = content.lower()
        for banned in self.banned_references:
            if banned in content_lower:
                return True
        return False
    
    def _calculate_cost(self, usage: Dict[str, int]) -> float:
        """Calculate API cost"""
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        return (input_tokens / 1_000_000) * 0.15 + (output_tokens / 1_000_000) * 0.60
    
    def get_stats(self) -> Dict[str, Any]:
        """Get generator stats"""
        return {
            "agent_name": self.name,
            "content_modes": [m.name for m in self.content_modes],
            "recent_modes": self.recent_modes[-5:],
            "banned_references": list(self.banned_references)[:10],
            "hashtag_pools": {
                "brand": self.brand_hashtags,
                "absurdist": self.absurdist_hashtags[:5],
                "workplace": self.workplace_hashtags[:5]
            }
        }