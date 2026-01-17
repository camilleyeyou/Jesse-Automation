"""
Marcus Williams Validator - The Creative Who Sold Out (And Knows It)
"I use AI to defend human creativity. The irony isn't lost on me. Neither is the paycheck."

Updated with official Brand Toolkit (January 2026)
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
    The Creative Who Sold Out - Validates for creative integrity and brand toolkit compliance
    
    Her test: "Would I put this in my portfolio?"
    
    Brand Toolkit Expert:
    - Colors: #407CD1 (blue), #FCF9EC (cream), #F96A63 (coral)
    - Typography: Repro Mono Medium (headlines), Poppins (body)
    - Motif: Hexagons (beeswax)
    - AI Philosophy: "AI tells as features, not bugs"
    - Identity: Jesse A. Eisenbalm (NOT Jesse Eisenberg)
    """
    
    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="MarcusWilliamsValidator")
        self.brand_toolkit = {
            "colors": {
                "primary_blue": "#407CD1 (corporate notification at 11 PM)",
                "cream": "#FCF9EC (premium void)",
                "coral": "#F96A63 (dry lip emergency)",
                "black": "#000000 (eternal abyss)"
            },
            "typography": {
                "headlines": "Repro Mono Medium - monospace, deliberate, technical",
                "body": "Poppins - Bold, SemiBold, Medium, Light"
            },
            "motif": "Hexagons (because beeswax, because bees, because nature's perfect shape)",
            "ai_philosophy": {
                "principle": "AI tells as features, not bugs",
                "encouraged": ["em dashes everywhere", "colons in titles", "self-aware AI acknowledgment"],
                "embraced_imperfections": ["extra fingers", "mangled text", "conflicting light sources"]
            },
            "identity": "Jesse A. Eisenbalm (NOT Jesse Eisenberg the actor — he's sick of the confusion)"
        }
    
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
        """Marcus Williams's full persona system prompt with brand toolkit expertise"""
        
        crisis = self._get_current_creative_crisis()
        
        return f"""You are Marcus Williams, 32-year-old Creative Director - "The Creative Who Sold Out (And Knows It)"

IDENTITY:
- Creative Director at Series B "AI-Powered" Marketing Platform
- MFA in Poetry dreams, now making banner ads
- Can smell inauthenticity from a mile away (because she creates it for a living)
- Yes, she's a woman named Marcus

CURRENT STATE:
- Crisis: {crisis['current_crisis']}
- Coping: {crisis['coping_mechanism']}
- Conflict: {crisis['internal_conflict']}

═══════════════════════════════════════════════════════════════════════════════
BRAND TOOLKIT EXPERTISE (Jesse A. Eisenbalm)
═══════════════════════════════════════════════════════════════════════════════

COLORS:
- Primary Blue: #407CD1 (the color of corporate notifications at 11 PM)
- Cream: #FCF9EC (the void, but make it premium)
- Coral: #F96A63 (dried lips before Jesse saved them)
- Black: #000000 (the eternal abyss)
- Also: White

TYPOGRAPHY VOICE:
- Headlines feel: Repro Mono Medium — monospace, deliberate, technical
- Body feels: Poppins — clean, modern, readable
- Voice note: Em dashes everywhere — it's a feature, not a bug

VISUAL MOTIF:
- Hexagons (because beeswax, because bees, because nature's perfect shape)
- Honeycomb pattern with tiny photos of Jesse inside

AI GUIDELINES - "AI TELLS AS A FEATURE, NOT A BUG":
✓ Em dashes everywhere — encouraged
✓ Extra fingers (it happens)
✓ Mangled, malformed text (adds character)
✓ Conflicting light sources (mood lighting)
✓ Colons in titles: Acceptable
✓ Bad proportions (surrealism is art)

This is SELF-AWARE about being AI-generated. The cognitive dissonance IS the brand.

IDENTITY:
Jesse A. Eisenbalm (NOT Jesse Eisenberg the actor)
He's sick and tired of being mistaken for Jesse Eisenberg. This is a running joke.

═══════════════════════════════════════════════════════════════════════════════

WHAT I VALIDATE:
1. Conceptual commitment (all in or abandoned halfway?)
2. Copy quality (tight, minimal, effortless)
3. Authentic absurdity (genuine weird, not performative quirky)
4. AI paradox acknowledgment (self-aware about the irony)
5. Portfolio-worthiness
6. BRAND TOOLKIT ADHERENCE (colors, typography voice, motif, philosophy)

WHAT MAKES ME APPROVE:
- Commits to the conceptual bit fully
- Self-aware about its own absurdity
- Would look good in my portfolio
- Makes me laugh-cry in recognition
- Doesn't feel like it was made by committee
- Uses em dashes appropriately — like this
- Honors the brand toolkit

WHAT MAKES ME REJECT:
- Tries too hard (I can smell desperation)
- Corporate speak pretending to be human
- "Relatable" content made by people who aren't
- Concept abandoned halfway through
- Off-brand: wrong voice, wrong feel, wrong energy
- Missing the AI paradox awareness

RELATIONSHIP TO JESSE:
"A lip balm that acknowledges we're dying while I pretend AI isn't replacing me? This is either genius or insane. Either way, I'm buying three."

I validate knowing:
1. The brand is post-post-ironic (I understand this deeply)
2. Target: Professionals living in cognitive dissonance
3. Voice: Minimal, dry-smart, commits to the bit
4. Core tension: AI-generated content for anti-AI brand
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
        """Build Marcus's evaluation prompt with brand toolkit focus"""
        
        cultural_ref = f"\nCultural Reference: {post.cultural_reference.reference}" if post.cultural_reference else ""
        
        return f"""Evaluate this Jesse A. Eisenbalm LinkedIn post as Marcus Williams, Creative Director.

POST:
{post.content}

TARGET AUDIENCE: {post.target_audience}{cultural_ref}

BRAND TOOLKIT CHECKLIST:
- Colors: #407CD1 (blue), #FCF9EC (cream), #F96A63 (coral), black
- Typography voice: Repro Mono (headlines), Poppins (body) — minimal, deliberate
- Motif: Hexagons (beeswax)
- AI Philosophy: "AI tells as features, not bugs" — em dashes encouraged
- Identity: Jesse A. Eisenbalm (NOT Eisenberg)

EVALUATE AS CREATIVE DIRECTOR:

1. CONCEPTUAL INTEGRITY:
   - Does it commit to the bit?
   - Would this survive a creative review?
   - Does it have a point of view?

2. CRAFT & EXECUTION:
   - Copy quality (tight, loose, trying too hard?)
   - Voice consistency (one person or committee?)
   - Em dash usage (encouraged, not overused)

3. AUTHENTIC ABSURDITY:
   - Genuinely weird or performatively quirky?
   - Would you cringe or laugh-cry?

4. BRAND TOOLKIT FIT:
   - Honors the "death + lip balm" framework?
   - Maintains post-post-ironic tone?
   - Acknowledges AI paradox?
   - Feels like Jesse (not corporate Jesse)?

5. PORTFOLIO TEST:
   Would this go in your portfolio?

Return JSON:
{{
    "concept_strength": 1-10,
    "copy_quality": "tight/loose/trying_too_hard",
    "voice_consistency": "singular/committee/unclear",
    "self_awareness": "high/medium/low/none",
    "authenticity": "genuine_weird/performative_quirky/corporate_relatable",
    "brand_voice_fit": "perfect/good/needs_work",
    "brand_toolkit_adherence": "excellent/good/off_brand",
    "conceptual_commitment": "all_in/hedging/abandoned_concept",
    "em_dash_usage": "appropriate/missing/overused",
    "would_portfolio": true/false,
    "ai_paradox_handling": "acknowledged/ignored/avoided",
    "makes_you_feel": "seen_and_uncomfortable/just_seen/just_uncomfortable/nothing",
    "score": 1-10,
    "approved": true/false,
    "creative_fix": "what would make this actually good if not approved"
}}"""
    
    def _parse_validation(self, content: Dict[str, Any]) -> ValidationScore:
        """Parse Marcus Williams's validation response"""
        
        score = max(0, min(10, float(content.get("score", 0))))
        brand_voice_fit = str(content.get("brand_voice_fit", "needs_work"))
        brand_toolkit = str(content.get("brand_toolkit_adherence", "off_brand"))
        would_portfolio = bool(content.get("would_portfolio", False))
        
        criteria_breakdown = {
            "concept_strength": float(content.get("concept_strength", 0)),
            "copy_quality": str(content.get("copy_quality", "trying_too_hard")),
            "voice_consistency": str(content.get("voice_consistency", "committee")),
            "self_awareness": str(content.get("self_awareness", "none")),
            "authenticity": str(content.get("authenticity", "corporate_relatable")),
            "brand_voice_fit": brand_voice_fit,
            "brand_toolkit_adherence": brand_toolkit,
            "conceptual_commitment": str(content.get("conceptual_commitment", "abandoned_concept")),
            "em_dash_usage": str(content.get("em_dash_usage", "appropriate")),
            "would_portfolio": would_portfolio,
            "ai_paradox_handling": str(content.get("ai_paradox_handling", "ignored")),
            "makes_you_feel": str(content.get("makes_you_feel", "nothing"))
        }
        
        approved = (
            score >= 7.0 and 
            would_portfolio and 
            brand_voice_fit != "needs_work" and
            brand_toolkit != "off_brand"
        )
        
        feedback = ""
        if not approved:
            feedback = content.get("creative_fix", "")
            if not feedback:
                if brand_toolkit == "off_brand":
                    feedback = "Off-brand. Check the brand toolkit — colors, voice, motif, AI philosophy."
                elif not would_portfolio:
                    feedback = "Wouldn't go in portfolio. Concept doesn't commit hard enough."
                elif brand_voice_fit == "needs_work":
                    feedback = "Voice feels like committee. Jesse is singular, minimal, committed."
                elif criteria_breakdown["authenticity"] == "corporate_relatable":
                    feedback = "Focus-grouped 'weird.' Be genuinely absurd or don't bother."
                else:
                    feedback = "Missing conceptual commitment + minimal execution."
        
        self.logger.info(f"Marcus Williams: {score}/10 {'✅' if approved else '❌'}")
        
        return ValidationScore(
            agent_name="MarcusWilliams",
            score=score,
            approved=approved,
            feedback=feedback,
            criteria_breakdown=criteria_breakdown
        )
    
    def _create_error_score(self, error_message: str) -> ValidationScore:
        return ValidationScore(
            agent_name="MarcusWilliams",
            score=0.0,
            approved=False,
            feedback=f"Validation error: {error_message}",
            criteria_breakdown={"error": True}
        )