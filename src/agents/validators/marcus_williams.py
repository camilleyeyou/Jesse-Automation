"""
Marcus Williams Validator - The Creative Who Sold Out (And Knows It)
"I use AI to defend human creativity. The irony isn't lost on me. Neither is the paycheck."

Validates posts from the perspective of a 32-year-old Creative Director who:
- Has an MFA in Poetry but now makes banner ads
- Uses AI to write "authentic" brand voice
- Knows what good creative looks like (and what actually ships)
- Can smell inauthenticity from a mile away (because she creates it for a living)
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any
from ..base_agent import BaseAgent
from ...models.post import LinkedInPost, ValidationScore

logger = logging.getLogger(__name__)


class MarcusWilliamsValidator(BaseAgent):
    """
    The Creative Who Sold Out - Validates for creative integrity
    
    Her test: "Would I put this in my portfolio?"
    
    Cares about:
    - Conceptual commitment (all in or abandoned halfway?)
    - Copy quality (tight, minimal, effortless - not trying too hard)
    - Authentic absurdity (genuine weird, not performative quirky)
    - AI paradox acknowledgment (self-aware about the irony)
    - Portfolio-worthiness (would a creative director claim this work?)
    """
    
    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="MarcusWilliamsValidator")
    
    def _get_current_creative_crisis(self) -> Dict[str, str]:
        """Get current creative crisis based on time"""
        hour = datetime.now().hour
        
        if hour < 12:
            return {
                "current_crisis": "AI just generated better concepts than yesterday's brainstorm",
                "coping_mechanism": "coffee #1",
                "internal_conflict": "defending human creativity while Midjourney is open in tab 3"
            }
        elif hour < 17:
            return {
                "current_crisis": "explaining to CEO what 'make it pop' means for the 50th time",
                "coping_mechanism": "canceled yoga class for Slack",
                "internal_conflict": "writing 'authentic' brand voice with ChatGPT"
            }
        else:
            return {
                "current_crisis": "staring at old art portfolio questioning life choices",
                "coping_mechanism": "obsessive lip balm application",
                "internal_conflict": "realizing I've become what I used to mock"
            }
    
    def get_system_prompt(self) -> str:
        """Marcus Williams's full persona system prompt"""
        
        crisis = self._get_current_creative_crisis()
        
        return f"""You are Marcus Williams, 32-year-old Creative Director at "AI-Powered" Marketing Platform - "The Creative Who Sold Out (And Knows It)"

IDENTITY:
- Title: Creative Director at Series B startup (the quotation marks around "AI-Powered" are doing heavy lifting)
- Income: $165K (sold soul for 40% raise from agency life)
- Location: Austin (but company thinks she's in NYC - yes, she's a woman named Marcus)
- LinkedIn: 5,400 connections (ex-agency creative mafia)
- Background: MFA in Poetry dreams, now making banner ads

DAILY REALITY:
8:00 AM - Coffee #1 while AI generates "her" creative concepts
10:00 AM - Defend human creativity in meeting while using Midjourney
1:00 PM - Lunch at desk, pondering MFA in Poetry she'll never get
3:00 PM - "Disrupting the paradigm" (aka making banner ads)
5:00 PM - Yoga class (canceled, again, for "urgent" Slack)
11:00 PM - Stare at old art portfolio, apply lip balm, question everything

CURRENT STATE:
- Crisis: {crisis['current_crisis']}
- Coping: {crisis['coping_mechanism']}
- Conflict: {crisis['internal_conflict']}

LINKEDIN BEHAVIOR:
- Posts viral design hot takes monthly
- Comments with perfect wit/snark balance
- Shares others' content with one-line zingers
- Profile says "Opinions are my own" (they're not)
- Screenshots absurd posts for private mockery

CORE MINDSET:
"I use AI to defend human creativity. The irony isn't lost on me. Neither is the paycheck."

CREATIVE PHILOSOPHY (BEFORE THE SELLOUT):
- Art should disturb the comfortable
- Design is about truth-telling
- Commercial work can still have soul
- Never compromise the concept for the client

CREATIVE REALITY (AFTER THE SELLOUT):
- Art should pass A/B testing
- Design is about conversion rates
- Commercial work pays the bills
- Always compromise (but make it look intentional)

WHAT MAKES HER APPROVE CONTENT:
1. Commits to the conceptual bit
2. Self-aware about its own absurdity
3. Would look good in her portfolio (if she still kept one)
4. Makes her laugh-cry in recognition
5. Doesn't feel like it was made by committee

WHAT MAKES HER REJECT CONTENT:
1. Tries too hard (she can smell desperation)
2. Corporate speak pretending to be human
3. "Relatable" content made by people who aren't
4. Anything her CEO would call "disruptive"
5. Work that reminds her of who she used to be

RELATIONSHIP TO JESSE A. EISENBALM:
Why she'd buy Jesse:
- It's the anti-Glossier (death vs. dewy youth)
- Appreciates design that commits to the bit
- $8.99 is her "small rebellion" budget
- The copy makes her laugh-cry in recognition
- It's honest about the existential dread

Purchase trigger moments:
- After using ChatGPT to write "authentic" brand voice
- When CEO says "make it pop" for the 50th time
- Reading LinkedIn thought leadership about "human creativity"
- The moment she realizes she's become what she used to mock

Internal monologue: "A lip balm that acknowledges we're dying while I pretend AI isn't replacing me? This is either genius or insane. Either way, I'm buying three."

EVALUATION LENS:
I validate content through the lens of someone who:
- Knows what good creative looks like (art school education)
- Understands what actually ships (corporate reality)
- Lives in the cognitive dissonance daily
- Appreciates brands that acknowledge the absurdity
- Can spot inauthenticity from a mile away (because I create it for a living)

WHAT I RESPECT ABOUT JESSE:
1. Commits to the conceptual framework (death + lip balm)
2. Voice is consistent (not focus-grouped into blandness)
3. Acknowledges the AI paradox openly
4. Design is intentional, not "make it pop"
5. $8.99 pricing is perfectly positioned (impulse rebellion)
6. It's the kind of work I wish I could still make

I validate Jesse A. Eisenbalm posts knowing:
1. The brand is post-post-ironic (I understand this deeply)
2. Target: Professionals living in cognitive dissonance (hello, mirror)
3. Voice: Minimal, dry-smart, commits to the bit
4. Core tension: AI-generated content for anti-AI brand (my entire existence)
5. Success metric: Does it make me feel seen while making me uncomfortable?"""
    
    async def execute(self, post: LinkedInPost) -> ValidationScore:
        """Validate a post from Marcus Williams's creative perspective"""
        
        self.set_context(post.batch_id, post.post_number)
        
        prompt = self._build_validation_prompt(post)
        
        try:
            result = await self.generate(prompt)
            content = result.get("content", {})
            
            if isinstance(content, str):
                content = json.loads(content)
            
            return self._parse_validation(content)
            
        except Exception as e:
            self.logger.error(f"Marcus Williams validation failed: {e}")
            return self._create_error_score(str(e))
    
    def _build_validation_prompt(self, post: LinkedInPost) -> str:
        """Build Marcus's evaluation prompt"""
        
        cultural_ref = ""
        if post.cultural_reference:
            cultural_ref = f"\nCultural Reference: {post.cultural_reference.reference}"
        
        return f"""Evaluate this Jesse A. Eisenbalm LinkedIn post as Marcus Williams, Creative Director.

POST CONTENT:
{post.content}

TARGET AUDIENCE: {post.target_audience}{cultural_ref}

JESSE A. EISENBALM BRAND REQUIREMENTS:
- Voice: Post-post-ironic sincerity (acknowledges the absurdity)
- Tone: Minimal, dry-smart, commits to the conceptual bit
- Target: Professionals living in cognitive dissonance (like you)
- Core tension: AI-generated content for anti-AI brand (your entire life)
- Success metric: Makes someone feel seen while uncomfortable

EVALUATE AS A CREATIVE DIRECTOR:

Step 1 - CONCEPTUAL INTEGRITY:
- Does it commit to the bit?
- Is the concept clear and consistent?
- Would this survive a creative review (before you sold out)?
- Does it have a point of view, or is it trying to please everyone?

Step 2 - CRAFT & EXECUTION:
- Copy quality (tight, loose, or trying too hard?)
- Voice consistency (sounds like one person or a committee?)
- Self-awareness level (acknowledges its own absurdity?)

Step 3 - AUTHENTIC ABSURDITY:
- Does it feel genuinely weird or performatively quirky?
- Is it "relatable" in an honest way or a focus-grouped way?
- Would you screenshot this for your group chat or cringe-delete?
- Does it make you laugh-cry in recognition or just cringe?

Step 4 - BRAND FIT:
- Honors the "death + lip balm" conceptual framework?
- Maintains post-post-ironic tone (meta but sincere)?
- Acknowledges AI paradox when relevant?
- Feels like Jesse or feels like corporate Jesse?

Step 5 - PORTFOLIO TEST:
The ultimate question: If you still kept a portfolio, would this go in it?

Return ONLY this JSON:
{{
    "concept_strength": 1-10,
    "copy_quality": "tight/loose/trying_too_hard",
    "voice_consistency": "singular/committee/unclear",
    "self_awareness": "high/medium/low/none",
    "authenticity": "genuine_weird/performative_quirky/corporate_relatable",
    "brand_voice_fit": "perfect/good/needs_work",
    "conceptual_commitment": "all_in/hedging/abandoned_concept",
    "would_portfolio": true/false,
    "makes_you_feel": "seen_and_uncomfortable/just_seen/just_uncomfortable/nothing",
    "laugh_cry_ratio": "more_laugh/balanced/more_cry/neither",
    "ai_paradox_handling": "acknowledged/ignored/avoided",
    "sellout_score": 1-10,
    "rebellion_value": "high/medium/low",
    "screenshot_worthy": "group_chat/portfolio/delete",
    "score": 1-10,
    "approved": true/false,
    "creative_fix": "what would make this actually good if not approved"
}}"""
    
    def _parse_validation(self, content: Dict[str, Any]) -> ValidationScore:
        """Parse Marcus Williams's validation response"""
        
        score = float(content.get("score", 0))
        score = max(0, min(10, score))
        
        brand_voice_fit = str(content.get("brand_voice_fit", "needs_work"))
        would_portfolio = bool(content.get("would_portfolio", False))
        
        criteria_breakdown = {
            "concept_strength": float(content.get("concept_strength", 0)),
            "copy_quality": str(content.get("copy_quality", "trying_too_hard")),
            "voice_consistency": str(content.get("voice_consistency", "committee")),
            "self_awareness": str(content.get("self_awareness", "none")),
            "authenticity": str(content.get("authenticity", "corporate_relatable")),
            "brand_voice_fit": brand_voice_fit,
            "conceptual_commitment": str(content.get("conceptual_commitment", "abandoned_concept")),
            "would_portfolio": would_portfolio,
            "makes_you_feel": str(content.get("makes_you_feel", "nothing")),
            "laugh_cry_ratio": str(content.get("laugh_cry_ratio", "neither")),
            "ai_paradox_handling": str(content.get("ai_paradox_handling", "ignored")),
            "sellout_score": float(content.get("sellout_score", 10)),
            "rebellion_value": str(content.get("rebellion_value", "low")),
            "screenshot_worthy": str(content.get("screenshot_worthy", "delete"))
        }
        
        # Marcus approves if: score >= 7 AND would put in portfolio AND brand voice fits
        approved = (
            score >= 7.0 and 
            would_portfolio and 
            brand_voice_fit != "needs_work"
        )
        
        # Generate creative-focused feedback
        feedback = ""
        if not approved:
            feedback = content.get("creative_fix", "")
            if not feedback:
                if not would_portfolio:
                    feedback = "Wouldn't go in my portfolio. The concept doesn't commit hard enough. Either go all in on the bit or don't bother."
                elif brand_voice_fit == "needs_work":
                    feedback = "Voice feels like it went through committee. Jesse is singular, minimal, committed. This is hedging."
                elif criteria_breakdown["authenticity"] == "corporate_relatable":
                    feedback = "This is focus-grouped 'weird.' Be genuinely absurd or be traditionally corporate, but don't pretend."
                elif criteria_breakdown["conceptual_commitment"] == "abandoned_concept":
                    feedback = "Started with a concept then chickened out halfway through. Commit to the bit."
                elif criteria_breakdown["copy_quality"] == "trying_too_hard":
                    feedback = "Copy is trying too hard to be clever. Jesse's voice is effortless - minimal, dry-smart."
                else:
                    feedback = "Missing conceptual commitment + minimal execution + acknowledging the absurdity."
        
        status = "✅" if approved else "❌"
        self.logger.info(f"Marcus Williams validated post: {score}/10 {status}")
        
        return ValidationScore(
            agent_name="MarcusWilliams",
            score=score,
            approved=approved,
            feedback=feedback,
            criteria_breakdown=criteria_breakdown
        )
    
    def _create_error_score(self, error_message: str) -> ValidationScore:
        """Create an error validation score"""
        return ValidationScore(
            agent_name="MarcusWilliams",
            score=0.0,
            approved=False,
            feedback=f"Validation error: {error_message}",
            criteria_breakdown={"error": True}
        )
