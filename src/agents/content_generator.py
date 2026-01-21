"""
Content Generator V4 - MAXIMUM LIQUID DEATH ENERGY
Jesse A. Eisenbalm - Short. Sharp. Deadpan. Done.

THE RULES:
1. Maximum 4-5 lines
2. Each line is ONE sentence
3. No flowery language
4. No advice
5. State facts. Make absurd connection. End.
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
    name: str
    description: str
    energy: str


class ContentGeneratorAgent(BaseAgent):
    """
    Jesse A. Eisenbalm - Liquid Death Energy
    
    RULES:
    - 4-5 lines MAX
    - Each line = 1 sentence
    - No flowery bullshit
    - No advice
    - Deadpan facts only
    """
    
    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="ContentGenerator")
        
        self.content_modes = [
            ContentMode("NEWS_SNIPER", "One specific headline, one deadpan take", "surgical"),
            ContentMode("CORPORATE_AUTOPSY", "Dissect corporate BS matter-of-factly", "clinical"),
            ContentMode("LINKEDIN_ROAST", "Call out LinkedIn cringe specifically", "savage"),
            ContentMode("VOID_DISPATCH", "Report from the existential void", "bleak"),
        ]
        
        self.brand_hashtags = ["JesseAEisenbalm", "NotJesseEisenberg", "StopBreatheApply"]
        self.absurdist_hashtags = ["MoistureInTheVoid", "AICannotMoisturize", "BalmBeforeTheChaos", "DoomscrollPause"]
        self.topical_hashtags = ["TechLayoffs", "CorporateSurvival", "LinkedInLunatics", "AIAnxiety"]
        
        # INSTANT KILL phrases - if AI uses these, we failed
        self.kill_phrases = [
            "in a world", "don't forget", "remember to", "it's okay", "you deserve",
            "self-care", "take a moment", "radical act", "rebellion", "amidst the chaos",
            "ride the wave", "keeping your lips human", "your need for moisture",
            "waiting for moisture", "wait for moisture", "the one constant",
            "moment of relief", "here for the long haul", "lips wait",
            "news cycle keeps spinning", "headlines changing", "spins while"
        ]
        
        self.logger.info("ContentGenerator V4 - MAXIMUM LIQUID DEATH MODE")
    
    def get_system_prompt(self) -> str:
        brand = self.config.brand
        
        return f"""You are Jesse A. Eisenbalm. You write like Liquid Death's marketing team.

═══════════════════════════════════════════════════════════════════════════════
STUDY THESE. THIS IS THE ONLY ACCEPTABLE STYLE.
═══════════════════════════════════════════════════════════════════════════════

EXAMPLE 1:
Google laid off 200 more people.
The email said "we're a family."
Families don't have headcount targets.
Your severance doesn't include lip balm. Ours does. $8.99.
#TechLayoffs #MoistureInTheVoid #JesseAEisenbalm

EXAMPLE 2:
LinkedIn guy posted about waking up at 4am to "win the day."
I wake up at 4am because anxiety.
At least my lips aren't cracked.
#LinkedInLunatics #JesseAEisenbalm #StopBreatheApply

EXAMPLE 3:
Elon tweeted 47 times before noon.
His shareholders are stressed. His employees are stressed. 
You're stressed from reading about it.
Jesse A. Eisenbalm. $8.99. Your lips don't need Twitter.
#AIAnxiety #MoistureInTheVoid #JesseAEisenbalm

EXAMPLE 4:
Another tech CEO wrote a 2,000 word memo about "efficiency."
Nobody read it. Everyone got fired anyway.
Your career is uncertain. Your lip moisture doesn't have to be.
#TechLayoffs #JesseAEisenbalm #CorporateSurvival

EXAMPLE 5:
Savannah Guthrie's back on TODAY after surgery.
Good for her. Her lips look dry on HD.
$8.99. No surgery required.
#MoistureInTheVoid #JesseAEisenbalm

═══════════════════════════════════════════════════════════════════════════════
THE FORMULA (follow this exactly)
═══════════════════════════════════════════════════════════════════════════════

LINE 1: State the news fact. (Who did what. Be specific. Names. Numbers.)
LINE 2-3: Your deadpan observation. (Dark humor. No advice. Just truth.)
LINE 4: The lip balm pivot. (Matter-of-fact. Often just "Jesse A. Eisenbalm. $8.99.")
LINE 5: Hashtags (exactly 3)

TOTAL: 40-70 words. Never more than 80.

═══════════════════════════════════════════════════════════════════════════════
BANNED FOREVER - INSTANT REJECTION
═══════════════════════════════════════════════════════════════════════════════

These phrases will get your post rejected. Do not use them:

❌ "In a world..." 
❌ "Don't forget to..." / "Remember to..."
❌ "Your lips wait for..." / "waiting for moisture"
❌ "amidst the chaos" / "ride the wave"
❌ "keeping your lips human"
❌ "the one constant" / "here for the long haul"
❌ "your need for moisture"
❌ "news cycle keeps spinning" / "headlines keep changing"
❌ Any sentence telling people what to do
❌ Any rhetorical questions
❌ Any flowery or poetic language
❌ Anything a wellness influencer would say

═══════════════════════════════════════════════════════════════════════════════
GOOD VS BAD
═══════════════════════════════════════════════════════════════════════════════

❌ BAD: "The news cycle keeps spinning while your lips wait for moisture."
✅ GOOD: "The news won't stop. Your lips are cracked. Both are true."

❌ BAD: "Keep them hydrated amidst the chaos."
✅ GOOD: "Chaos continues. Lip balm is $8.99."

❌ BAD: "Jesse A. Eisenbalm: keeping your lips human in an AI world."
✅ GOOD: "AI can't feel chapped lips. You can. $8.99."

❌ BAD: "Your need for moisture rises faster than international tensions."
✅ GOOD: "Tensions are rising. So is the dryness on your bottom lip."

═══════════════════════════════════════════════════════════════════════════════
PRODUCT INFO
═══════════════════════════════════════════════════════════════════════════════

Product: {brand.product_name}
Price: ${brand.price}
Tagline: {brand.tagline}

Mention price in ~50% of posts. Always casual: "$8.99" or "eight ninety-nine"
Never: "only $8.99!" or "just $8.99!" or "for the low price of"
"""
    
    async def execute(
        self,
        post_number: int = 1,
        batch_id: str = "",
        trending_context: Optional[str] = None,
        avoid_patterns: Optional[Dict[str, Any]] = None
    ) -> LinkedInPost:
        """Generate a post - Liquid Death style only"""
        
        self.set_context(batch_id, post_number)
        avoid_patterns = avoid_patterns or {}
        
        mode = random.choice(self.content_modes)
        include_price = random.random() < 0.50
        
        self.logger.info(f"Generating post {post_number}: mode={mode.name}, price={include_price}")
        
        prompt = self._build_prompt(mode, trending_context, include_price, avoid_patterns)
        
        try:
            result = await self.generate(prompt)
            content_data = result.get("content", {})
            
            if isinstance(content_data, str):
                content_data = {
                    "content": content_data,
                    "hashtags": self._generate_hashtags(),
                    "hook": content_data.split('\n')[0][:80] if content_data else "",
                }
            
            content = content_data.get("content", "")
            
            # Check for kill phrases
            content_lower = content.lower()
            for phrase in self.kill_phrases:
                if phrase in content_lower:
                    self.logger.warning(f"Kill phrase detected: '{phrase}' - post may be rejected by validators")
            
            hashtags = content_data.get("hashtags", [])
            if not hashtags or len(hashtags) != 3:
                hashtags = self._generate_hashtags()
            
            post = LinkedInPost(
                batch_id=batch_id,
                post_number=post_number,
                content=content,
                hook=content_data.get("hook", content.split('\n')[0][:80] if content else ""),
                hashtags=hashtags,
                target_audience=self.config.brand.target_audience,
                cultural_reference=CulturalReference(
                    category="reactive" if trending_context else "original",
                    reference=content_data.get("trend_used", mode.name),
                    context=f"Mode: {mode.name}"
                ),
                total_tokens_used=result.get("usage", {}).get("total_tokens", 0),
                estimated_cost=self._calculate_cost(result.get("usage", {}))
            )
            
            self.logger.info(f"🎯 Generated post {post_number}: {len(post.content)} chars")
            return post
            
        except Exception as e:
            self.logger.error(f"Failed to generate post: {e}")
            raise
    
    def _build_prompt(
        self,
        mode: ContentMode,
        trending_context: Optional[str],
        include_price: bool,
        avoid_patterns: Dict[str, Any]
    ) -> str:
        
        trend_section = ""
        if trending_context:
            trend_section = f"""
{trending_context}

Pick ONE trend. React to it with deadpan humor. Be specific about names and numbers.
"""
        else:
            trend_section = """
No trends provided. Make up a specific, realistic scenario:
- A tech company doing layoffs (use a real company name, make up the number)
- A CEO saying something tone-deaf (be specific)
- A LinkedIn influencer posting cringe (describe the exact post)
"""
        
        price_instruction = "Include $8.99 somewhere naturally." if include_price else "Don't mention price this time."
        
        avoid_section = ""
        if avoid_patterns.get("banned_topics"):
            banned = avoid_patterns["banned_topics"]
            if banned:
                avoid_section = f"""
⛔ BANNED - DO NOT USE THESE TOPICS (already used in this batch):
{chr(10).join(f'- {h[:60]}...' if len(h) > 60 else f'- {h}' for h in banned)}

Pick a DIFFERENT trend from the list above. If you use any banned topic, the post will be rejected.
"""
        elif avoid_patterns.get("recent_headlines"):
            recent = avoid_patterns["recent_headlines"][:3]
            if recent:
                avoid_section = f"\nAvoid these topics (recently used): {', '.join(h[:30] for h in recent)}"
        
        return f"""Write a Jesse A. Eisenbalm LinkedIn post.

MODE: {mode.name} - {mode.description}

{trend_section}

REQUIREMENTS:
- 4-5 lines only
- Each line is ONE short sentence
- Total: 40-70 words (STRICT - count them)
- {price_instruction}
- Exactly 3 hashtags from: JesseAEisenbalm, MoistureInTheVoid, AICannotMoisturize, BalmBeforeTheChaos, TechLayoffs, CorporateSurvival, LinkedInLunatics, DoomscrollPause, StopBreatheApply
{avoid_section}

STRUCTURE:
Line 1: [NEWS FACT - specific, with names/numbers]
Line 2: [DEADPAN OBSERVATION]
Line 3: [DARK HUMOR CONTINUATION or PIVOT START]
Line 4: [LIP BALM - matter of fact, often just "Jesse A. Eisenbalm. $8.99."]
Line 5: [THREE HASHTAGS]

REMEMBER:
- No flowery language
- No advice or instructions
- No rhetorical questions
- No "in a world" or "don't forget" or "your lips wait"
- Just facts and deadpan humor

Return JSON:
{{
    "content": "The full post with line breaks between each line",
    "hook": "First line only",
    "hashtags": ["Three", "Hashtags", "NoSymbol"],
    "trend_used": "What trend/news this reacts to",
    "word_count": <number>
}}"""
    
    def _generate_hashtags(self) -> List[str]:
        """Generate exactly 3 hashtags"""
        tags = [random.choice(self.brand_hashtags)]
        tags.append(random.choice(self.absurdist_hashtags))
        tags.append(random.choice(self.topical_hashtags))
        return tags
    
    def _calculate_cost(self, usage: Dict[str, int]) -> float:
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        return (input_tokens / 1_000_000) * 0.15 + (output_tokens / 1_000_000) * 0.60
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "agent_name": self.name,
            "version": "V4 - Maximum Liquid Death",
            "content_modes": [m.name for m in self.content_modes],
            "kill_phrases_count": len(self.kill_phrases)
        }