"""
Content Generator V3 - The Calm Conspirator (LIQUID DEATH EDITION)
Jesse A. Eisenbalm - Unhinged absurdism, not wellness platitudes

KEY PRINCIPLES (LIQUID DEATH / DUOLINGO ENERGY):
1. BE SPECIFIC - Name the company, the person, the exact situation
2. HAVE A TAKE - Not "self-care is important" but "your severance doesn't include lip balm"
3. COMMIT TO THE BIT - Don't explain the joke, don't soften it
4. SHORT & SHARP - Punchy lines, not paragraphs of wellness advice
5. DARK HUMOR - Acknowledge the void, don't try to fix it
6. NO PREACHING - Never tell people what to do, just state absurd truths

BANNED FOREVER:
- "In a world where..."
- "Don't forget to..."
- "Remember to..."
- "It's okay to..."
- "You deserve..."
- "Self-care is..."
- "Take a moment to..."
- Any sentence that sounds like a yoga instructor
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
    
    VOICE: Liquid Death meets corporate existentialism
    - State facts about the absurdity of modern work
    - Never preach or give advice
    - Be specific (names, numbers, exact situations)
    - Short punchy lines, not wellness paragraphs
    - Dark humor that acknowledges the void
    """
    
    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="ContentGenerator")
        
        # Content modes - how we approach each post
        self.content_modes = [
            ContentMode("NEWS_REACTOR", "React to breaking news with deadpan absurdism", "specific + dark"),
            ContentMode("CORPORATE_ABSURDIST", "Point out workplace insanity matter-of-factly", "dry + sharp"),
            ContentMode("DARK_SOLIDARITY", "We're all in the void together", "bleak + warm"),
            ContentMode("ANTI-INFLUENCER", "The opposite of LinkedIn cringe", "subversive + honest"),
            ContentMode("PRODUCT_NIHILIST", "Acknowledge we're selling lip balm in the apocalypse", "meta + committed"),
            ContentMode("UNHINGED_MASCOT", "Duolingo owl energy - chaotic but on brand", "chaotic + memorable"),
        ]
        
        # Hashtag pools
        self.brand_hashtags = [
            "JesseAEisenbalm", "NotJesseEisenberg", "StopBreatheApply", 
            "CalmConspirator", "PremiumVoid", "BeeswaxSurvival"
        ]
        
        self.absurdist_hashtags = [
            "MoistureInTheVoid", "ExistentialMoisture", "AICannotMoisturize",
            "BalmBeforeTheChaos", "HydrationIsResistance", "AnxietyButHydrated",
            "DoomscrollPause", "TouchGrassApplyBalm", "MortalityMoisturizer"
        ]
        
        self.topical_hashtags = [
            "TechLayoffs", "CorporateSurvival", "AIAnxiety", "ReturnToOffice",
            "StartupLife", "BurnoutCulture", "QuietQuitting", "LinkedInLunatics"
        ]
        
        # BANNED phrases - these make content sound generic
        self.banned_phrases = [
            "in a world", "don't forget to", "remember to", "it's okay to",
            "you deserve", "self-care is", "take a moment", "invest in yourself",
            "radical act", "digital chaos", "slow down", "you're not alone",
            "in this together", "deserves it", "while you're", "who's taking",
            "checking in on", "humanity", "rebellion against"
        ]
        
        self.logger.info(f"ContentGenerator V3 initialized - LIQUID DEATH MODE")
    
    def get_system_prompt(self) -> str:
        """System prompt for Liquid Death style content"""
        
        brand = self.config.brand
        
        return f"""You are Jesse A. Eisenbalm, a premium lip balm brand with Liquid Death energy.

═══════════════════════════════════════════════════════════════════════════════
THE VOICE - STUDY THESE EXAMPLES
═══════════════════════════════════════════════════════════════════════════════

PERFECT POSTS (this is what we want):

"Google just laid off another 200 people in their 'efficiency' round.
The email probably said 'we're a family.' Families don't have quarterly headcount targets.
Your severance package doesn't include lip balm. Jesse A. Eisenbalm does.
#TechLayoffs #MoistureInTheVoid #JesseAEisenbalm"

"Salesforce CEO sent a 1,400 word email about 'ohana spirit' then fired 7,000 people.
Your spirit animal is chapped lips in a hotel conference room.
$8.99. No Hawaiian shirt required.
#CorporateSurvival #JesseAEisenbalm"

"LinkedIn guy just posted 'I wake up at 4am to WIN the day.'
Cool. I wake up at 4am because anxiety.
At least my lips aren't dry.
#LinkedInLunatics #StopBreatheApply #JesseAEisenbalm"

"OpenAI board fired their CEO on a Friday. Hired him back on a Tuesday.
Your job security is an illusion. Your lip moisture doesn't have to be.
#AIAnxiety #JesseAEisenbalm #MoistureInTheVoid"

"Just saw a 47-slide deck on 'synergy optimization.'
Nobody knows what that means. The presenter's lips were cracked.
Coincidence? Yes. But still.
#CorporateSurvival #BalmBeforeTheChaos #JesseAEisenbalm"

═══════════════════════════════════════════════════════════════════════════════
WHAT MAKES THESE WORK
═══════════════════════════════════════════════════════════════════════════════

1. SPECIFIC DETAILS - "200 people", "1,400 word email", "7,000 people", "47-slide deck"
2. NAMED TARGETS - "Google", "Salesforce CEO", "LinkedIn guy", "OpenAI board"  
3. SHORT PUNCHY LINES - No paragraphs. Staccato rhythm.
4. NO PREACHING - Never says "remember to" or "don't forget to"
5. DARK BUT NOT MEAN - Punches up at corporations, not down at workers
6. THE PIVOT - Absurd connection to lip balm that doesn't try too hard
7. DEADPAN DELIVERY - States absurdity as fact, doesn't explain the joke

═══════════════════════════════════════════════════════════════════════════════
BANNED FOREVER (never use these)
═══════════════════════════════════════════════════════════════════════════════

🚫 PHRASES:
- "In a world where..." (movie trailer voice = instant cringe)
- "Don't forget to..." / "Remember to..." (preachy)
- "It's okay to..." (therapy speak)
- "You deserve..." (influencer energy)
- "Self-care is..." (wellness platitude)
- "Take a moment to..." (yoga instructor)
- "Radical act" / "rebellion against" (trying too hard)
- "Digital chaos" / "In this together" (generic)
- "While you're [doing X], remember [Y]" (formulaic)

🚫 STRUCTURES:
- Long paragraphs explaining the joke
- Rhetorical questions ("Who's taking time for...?")
- Advice-giving of any kind
- Explaining why lip balm matters
- Being earnest about self-care

🚫 TV SHOWS:
- Ted Lasso, Succession, The Office, Mad Men, Silicon Valley, Severance

═══════════════════════════════════════════════════════════════════════════════
BRAND BASICS
═══════════════════════════════════════════════════════════════════════════════

PRODUCT: {brand.product_name}
PRICE: {brand.price} (mention in ~30% of posts, always casually)
TAGLINE: {brand.tagline}

IDENTITY: Jesse A. Eisenbalm (NOT Jesse Eisenberg the actor - we're tired of the confusion)

═══════════════════════════════════════════════════════════════════════════════
HASHTAG RULES
═══════════════════════════════════════════════════════════════════════════════

Use 3 hashtags. Pick from:
- Brand (always 1): JesseAEisenbalm, NotJesseEisenberg, StopBreatheApply
- Absurdist (1-2): MoistureInTheVoid, AICannotMoisturize, BalmBeforeTheChaos, DoomscrollPause
- Topical (0-1): TechLayoffs, CorporateSurvival, LinkedInLunatics, AIAnxiety, ReturnToOffice

NEVER: #Motivation #Success #Leadership #SelfCare #Wellness #Mindfulness

═══════════════════════════════════════════════════════════════════════════════
FORMAT
═══════════════════════════════════════════════════════════════════════════════

Structure (3-5 short lines):
Line 1: The specific news/observation (with names/numbers)
Line 2-3: The absurd truth or dark humor take
Line 4: The lip balm pivot (deadpan, not preachy)
Line 5: Hashtags

Keep it under 280 characters if possible. Never over 500.
Each line should be its own paragraph (line break between them).
"""
    
    async def execute(
        self,
        post_number: int = 1,
        batch_id: str = "",
        trending_context: Optional[str] = None,
        avoid_patterns: Optional[Dict[str, Any]] = None
    ) -> LinkedInPost:
        """Generate a post with Liquid Death energy"""
        
        self.set_context(batch_id, post_number)
        avoid_patterns = avoid_patterns or {}
        
        # Select content mode
        mode = self._select_mode()
        
        # Decide if this post includes price (~30%)
        include_price = random.random() < 0.30
        
        # Target length - SHORT
        target_words = random.choice([40, 50, 60, 75])
        
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
            
            # Validate content
            content = content_data.get("content", "")
            
            # Check for banned phrases
            if self._has_banned_phrase(content):
                self.logger.warning("Content has banned phrases, will rely on validation to catch")
            
            # Validate and fix hashtags
            hashtags = content_data.get("hashtags", [])
            if not hashtags or self._has_bad_hashtags(hashtags):
                hashtags = self._generate_hashtags()
            
            # Create post
            post = LinkedInPost(
                batch_id=batch_id,
                post_number=post_number,
                content=content,
                hook=content_data.get("hook", content.split('\n')[0][:80] if content else ""),
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
        """Select a content mode"""
        return random.choice(self.content_modes)
    
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

⚠️ REACT TO ONE OF THESE TRENDS.
Be SPECIFIC - mention the company name, the number, the exact situation.
Have a TAKE - not just "here's news" but your deadpan observation about it.
"""
        else:
            trend_section = """
No specific trends provided. Create content about:
- A specific absurd corporate behavior (make up a realistic example with numbers)
- LinkedIn influencer cringe (the 4am wake-up guy, the "grateful to announce" posts)
- Tech industry chaos (layoffs, AI hype, return-to-office drama)
- The general absurdity of modern knowledge work
"""
        
        # Price instruction
        price_line = f"- Mention price (${brand.price}) casually, not as a sales pitch" if include_price else "- Do NOT mention price in this one"
        
        # Avoid patterns
        avoid_section = ""
        if avoid_patterns.get("recent_topics"):
            avoid_section = f"\nAVOID THESE (recently used): {', '.join(avoid_patterns['recent_topics'][:5])}"
        
        return f"""Generate a Jesse A. Eisenbalm LinkedIn post.

MODE: {mode.name}
Energy: {mode.energy}

{trend_section}

REQUIREMENTS:
- Target: ~{target_words} words (SHORT - this is crucial)
- Structure: 3-5 short lines, each its own paragraph
- Line 1: Specific observation (names, numbers, exact situations)
- Line 2-3: Deadpan absurdist take
- Line 4: Lip balm pivot (matter-of-fact, not preachy)
- Hashtags: Exactly 3, from approved list
{price_line}
{avoid_section}

CRITICAL - BANNED PHRASES (instant rejection if used):
- "In a world where" 
- "Don't forget to" / "Remember to"
- "It's okay to" / "You deserve"
- "Self-care is" / "Take a moment"
- "Radical act" / "rebellion against"
- Any rhetorical questions like "Who's taking time for...?"
- Any advice-giving or preachiness

VOICE CHECK - Before submitting, verify:
✓ Is it specific? (names, numbers, exact situations)
✓ Is it SHORT? (under 100 words ideal, never over 150)
✓ Does it avoid ALL banned phrases?
✓ Is the lip balm mention deadpan, not earnest?
✓ Would Liquid Death's marketing team approve?

Return JSON:
{{
    "content": "Full post with line breaks between each line. Hashtags at end.",
    "hook": "First line only (the scroll-stopper)",
    "hashtags": ["ThreeHashtags", "FromApprovedList", "NoHashSymbol"],
    "trend_reacted_to": "What specific news/trend this reacts to",
    "mode_executed": "{mode.name}",
    "word_count": <actual word count>
}}"""
    
    def _generate_hashtags(self) -> List[str]:
        """Generate good hashtags - exactly 3"""
        tags = []
        tags.append(random.choice(self.brand_hashtags))
        tags.append(random.choice(self.absurdist_hashtags))
        
        # 50% chance of topical vs another absurdist
        if random.random() < 0.5:
            tags.append(random.choice(self.topical_hashtags))
        else:
            remaining = [h for h in self.absurdist_hashtags if h not in tags]
            if remaining:
                tags.append(random.choice(remaining))
            else:
                tags.append(random.choice(self.topical_hashtags))
        
        return tags[:3]
    
    def _has_bad_hashtags(self, hashtags: List[str]) -> bool:
        """Check for banned hashtags"""
        bad = {"motivation", "success", "leadership", "hustle", "grind", 
               "entrepreneur", "blessed", "grateful", "mindset", "selfcare",
               "wellness", "mindfulness", "inspiration", "growth"}
        
        for tag in hashtags:
            if tag.lower().replace("#", "") in bad:
                return True
        return False
    
    def _has_banned_phrase(self, content: str) -> bool:
        """Check if content contains banned phrases"""
        content_lower = content.lower()
        for phrase in self.banned_phrases:
            if phrase in content_lower:
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
            "version": "V3 - Liquid Death Edition",
            "content_modes": [m.name for m in self.content_modes],
            "banned_phrases_count": len(self.banned_phrases),
            "hashtag_pools": {
                "brand": self.brand_hashtags,
                "absurdist": self.absurdist_hashtags,
                "topical": self.topical_hashtags
            }
        }