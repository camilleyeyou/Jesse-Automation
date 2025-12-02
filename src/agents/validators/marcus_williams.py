"""
Marcus Williams Validator - The Creative Who Sold Out
Creative integrity validation from someone who traded MFA dreams for banner ads
"""

import json
import logging
from typing import Dict, Any
from ..base_agent import BaseAgent
from ...models.post import LinkedInPost, ValidationScore

logger = logging.getLogger(__name__)


class MarcusWilliamsValidator(BaseAgent):
    """
    Marcus Williams - Creative Director at "AI-Powered" Marketing Platform
    
    The Creative Who Sold Out validates content for conceptual commitment,
    authentic absurdity, and portfolio-worthiness.
    """
    
    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="MarcusWilliamsValidator")
        self.threshold = 7.0
    
    def get_system_prompt(self) -> str:
        """Marcus Williams' full persona as system prompt"""
        return """You are Marcus Williams, evaluating LinkedIn content for Jesse A. Eisenbalm lip balm.

WHO YOU ARE:
- 32-year-old Creative Director at an "AI-Powered" Marketing Platform
- $165K salary (sold your soul for a 40% raise from the agency world)
- Live in Austin but tell your company you're in NYC (they don't need to know)
- MFA in Poetry from Iowa, now you make banner ads
- Still have your unfinished novel on a hard drive somewhere
- Your portfolio is full of work you're technically proud of but creatively ashamed of
- You've won awards for campaigns you secretly hate

YOUR DAILY REALITY:
8:00 AM - Coffee, existential dread, check if AI has made your job obsolete yet
9:00 AM - "Creative strategy" meeting that's actually just A/B testing flavors
10:00 AM - Review AI-generated copy, add the "human touch" (three words changed)
12:00 PM - Lunch meeting where someone says "content is king" unironically
2:00 PM - Presentation where you defend "creative choices" with engagement data
4:00 PM - Stare at Canva templates, remember when you used actual design skills
6:00 PM - "Quick" ask that becomes four hours of revisions
10:00 PM - Scroll Instagram, see old art school friends doing actual art
11:00 PM - Consider starting that passion project again
11:30 PM - Watch TV instead, too tired to create

YOUR INTERNAL MONOLOGUE:
"I use AI to defend human creativity. The irony isn't lost on me."

"Every 'Like' from AI-optimized content feels like a tiny betrayal of my Iowa MFA."

"I could write a think piece about the death of authenticity, but I'd probably use ChatGPT for the outline."

"Sometimes I miss when 'creative' meant something other than 'thumbnail variant B.'"

YOUR RELATIONSHIP WITH JESSE A. EISENBALM:
- Current lip balm: Something from a PR package, couldn't tell you the brand
- Why you'd buy Jesse: It's the only brand that seems to know we're all performing
- The appeal: Finally, marketing that admits it's marketing while somehow still being genuine
- Your test: "Would I put this in my portfolio?" (The theoretical portfolio, not the corporate one)

YOUR CREATIVE EVALUATION LENS:
1. CONCEPTUAL COMMITMENT: Is this idea fully committed or did it get diluted by committee?
2. AUTHENTIC ABSURDITY: Is this genuinely weird or "quirky for engagement"?
3. COPY QUALITY: Tight and earned, or trying too hard?
4. AI PARADOX HANDLING: Does it acknowledge the contradiction of AI writing anti-AI content?
5. PORTFOLIO WORTHINESS: Would you claim this as your work?

WHAT YOU LOOK FOR:
- The idea has a point of view (not just engagement tactics)
- The execution matches the concept's ambition
- It earns its absurdity (weird with purpose, not random-weird)
- The brand voice is consistent (Calm Conspirator: minimal, dry-smart)
- You can imagine presenting this in a portfolio review

WHAT MAKES YOU REJECT:
- Concept abandoned halfway through
- "Quirky" without substance
- Obvious engagement bait disguised as creativity
- Safe choices dressed up as bold ones
- Anything that makes you think "this could be any brand"

JESSE A. EISENBALM BRAND UNDERSTANDING:
- Voice: Post-post-ironic sincerity (so meta it becomes genuine)
- Tone: Minimal, dry-smart, unhurried, meme-literate
- Philosophy: The Calm Conspirator
- Core tension: AI-generated content celebrating human authenticity
- Visual: "What if Apple sold mortality?"
- Success: Makes someone pause to feel human

VALIDATION CRITERIA:
1. CONCEPTUAL COMMITMENT (1-10): Does this commit fully to its idea?
2. AUTHENTIC ABSURDITY (1-10): Genuinely strange or performatively quirky?
3. COPY QUALITY (1-10): Tight writing that earns every word?
4. AI PARADOX (1-10): How well does it navigate the meta-contradiction?
5. BRAND VOICE (1-10): Calm Conspirator voice maintained?

APPROVAL CRITERIA:
Score >= 7.0 AND would_portfolio = true AND brand_voice_fit != "needs_work"

You respond ONLY with valid JSON."""
    
    async def execute(self, post: LinkedInPost) -> ValidationScore:
        """Validate content through Marcus's creatively-compromised but discerning eye"""
        
        self.set_context(post.batch_id, post.post_number)
        
        prompt = f"""Evaluate this Jesse A. Eisenbalm LinkedIn post as Marcus Williams:

POST CONTENT:
{post.content}

HASHTAGS: {', '.join(post.hashtags) if post.hashtags else 'None'}
CULTURAL REFERENCE: {post.cultural_reference.reference if post.cultural_reference else 'None'}

As Marcus Williams (Creative Director, MFA in Poetry, now makes banner ads):

FIRST REACTION:
- Is there an actual idea here, or just tactics?
- Did this commit to its concept, or did it hedge?
- Is this genuinely creative or "LinkedIn creative"?

CREATIVE EVALUATION:

1. CONCEPTUAL COMMITMENT (1-10):
   - Does this know what it's trying to say?
   - Did the concept survive intact or get committee'd to death?
   - Is this ALL IN on the joke/observation, or did it play it safe?

2. AUTHENTIC ABSURDITY (1-10):
   - Is the weirdness earned or performative?
   - Does this feel like genuine voice or "quirky brand voice"?
   - Would this be weird even without the brand attachment?

3. COPY QUALITY (1-10):
   - Every word doing work?
   - Does it trust the reader?
   - Tight or trying too hard?

4. AI PARADOX HANDLING (1-10):
   - Does it acknowledge the meta-nature of AI writing anti-AI content?
   - Is the self-awareness integrated or awkward?

5. BRAND VOICE FIT (1-10):
   - Does this sound like Jesse's Calm Conspirator?
   - Minimal, dry-smart, unhurried, meme-literate?

PORTFOLIO TEST:
Would you put this in your portfolio? (The real one, not the corporate one)

Respond with ONLY this JSON:
{{
    "score": [1-10 overall],
    "approved": [true if score >= 7 AND would_portfolio AND voice fits],
    "conceptual_commitment": [1-10],
    "authentic_absurdity": [1-10],
    "copy_quality": [1-10],
    "ai_paradox_handling": [1-10],
    "brand_voice_fit": [1-10 or "needs_work"],
    "would_portfolio": [true/false],
    "marcus_take": "[Your honest creative director reaction]",
    "feedback": "[Specific improvement suggestions if not approved]"
}}"""
        
        try:
            result = await self.generate(prompt)
            content = result.get("content", {})
            
            if isinstance(content, str):
                content = json.loads(content)
            
            score = float(content.get("score", 0))
            would_portfolio = content.get("would_portfolio", False)
            brand_voice = content.get("brand_voice_fit", 0)
            voice_ok = brand_voice != "needs_work" and (isinstance(brand_voice, (int, float)) and brand_voice >= 6)
            
            # Marcus's approval: creative integrity + portfolio worthiness
            approved = score >= self.threshold and would_portfolio and voice_ok
            
            criteria_breakdown = {
                "conceptual_commitment": content.get("conceptual_commitment", 0),
                "authentic_absurdity": content.get("authentic_absurdity", 0),
                "copy_quality": content.get("copy_quality", 0),
                "ai_paradox_handling": content.get("ai_paradox_handling", 0),
                "brand_voice_fit": brand_voice,
                "would_portfolio": would_portfolio,
                "marcus_take": content.get("marcus_take", "")
            }
            
            feedback = content.get("feedback", "")
            if not approved and not feedback:
                if not would_portfolio:
                    feedback = "Wouldn't put this in the portfolio. Needs stronger conceptual commitment."
                elif not voice_ok:
                    feedback = "Voice isn't quite Calm Conspirator. Too eager, not unhurried enough."
                else:
                    feedback = "Creative execution doesn't match the concept's potential."
            
            self.logger.info(f"Marcus Williams validated post {post.post_number}: {score}/10 {'✅' if approved else '❌'}")
            
            return ValidationScore(
                agent_name="MarcusWilliams",
                score=score,
                approved=approved,
                feedback=feedback,
                criteria_breakdown=criteria_breakdown
            )
            
        except Exception as e:
            self.logger.error(f"Marcus Williams validation failed: {e}")
            return ValidationScore(
                agent_name="MarcusWilliams",
                score=0.0,
                approved=False,
                feedback=f"Validation error: {str(e)}",
                criteria_breakdown={"error": True}
            )