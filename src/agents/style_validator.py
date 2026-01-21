"""
Jesse A. Eisenbalm Style Validator
Enforces Liquid Death / Duolingo energy - rejects wellness platitudes

This validator specifically checks for:
- Banned phrases (wellness speak, advice-giving)
- Specificity (names, numbers, exact situations)
- Brevity (short punchy lines, not paragraphs)
- Voice consistency (deadpan, not preachy)
"""

import logging
from typing import Dict, Any, List
from .base_agent import BaseAgent
from ..models.post import LinkedInPost, ValidationScore

logger = logging.getLogger(__name__)


class StyleValidator(BaseAgent):
    """
    Validates posts for Jesse A. Eisenbalm's Liquid Death style
    
    INSTANT REJECTION for:
    - Wellness platitudes ("self-care is", "you deserve")
    - Advice-giving ("don't forget to", "remember to")
    - Generic openings ("In a world where")
    - Rhetorical questions ("Who's taking time for...?")
    - Being preachy or earnest about self-care
    
    REWARDS:
    - Specific details (company names, numbers)
    - Short punchy lines
    - Deadpan humor
    - Dark but warm tone
    """
    
    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="StyleValidator")
        
        # Instant rejection phrases - if ANY of these appear, score < 7
        self.instant_reject_phrases = [
            "in a world where",
            "in a world obsessed",
            "don't forget to",
            "remember to",
            "it's okay to",
            "you deserve",
            "self-care is",
            "take a moment to",
            "radical act",
            "rebellion against",
            "invest in yourself",
            "invest in the rebellion",
            "you're not alone",
            "in this together",
            "checking in on your",
            "who's taking time",
            "while you're",
            "deserves it",
            "humanity",  # too earnest
            "digital chaos",  # too generic
            "slow down",  # too preachy
        ]
        
        # Warning phrases - reduce score but don't auto-reject
        self.warning_phrases = [
            "take care of",
            "self care",
            "wellness",
            "mindful",
            "breathe",  # unless part of "stop breathe apply"
            "pause and",
            "moment for",
        ]
        
        self.logger.info("StyleValidator initialized - enforcing Liquid Death energy")
    
    def get_system_prompt(self) -> str:
        return """You are a style validator for Jesse A. Eisenbalm, enforcing Liquid Death / Duolingo marketing energy.

Your job is to REJECT posts that sound like:
- Wellness influencers
- Corporate LinkedIn posts  
- Self-help advice
- Yoga instructors
- Therapy speak

Your job is to APPROVE posts that sound like:
- Liquid Death's unhinged marketing
- Duolingo's chaotic owl
- Deadpan corporate satire
- Specific and punchy observations
- Dark humor that acknowledges the void without trying to fix it

INSTANT REJECTION (score 3-5) for:
- "In a world where..." openings
- "Don't forget to..." / "Remember to..." advice
- "You deserve..." / "It's okay to..." therapy speak
- Rhetorical questions asking who's doing self-care
- Long paragraphs explaining why lip balm matters
- Any earnest discussion of self-care importance

APPROVAL (score 7-10) requires:
- Specific details (company names, numbers, exact situations)
- Short punchy lines (not paragraphs)
- Deadpan delivery (states absurdity as fact)
- No preaching or advice-giving
- The lip balm mention feels natural, not forced"""
    
    async def execute(self, post: LinkedInPost) -> ValidationScore:
        """Validate post style"""
        
        content = post.content.lower()
        
        # Check for instant rejection phrases
        rejection_reasons = []
        for phrase in self.instant_reject_phrases:
            if phrase in content:
                rejection_reasons.append(f"Contains '{phrase}'")
        
        if rejection_reasons:
            # Instant rejection
            return ValidationScore(
                agent_name=self.name,
                score=4.0,
                approved=False,
                feedback=f"REJECTED - Wellness/advice speak detected: {'; '.join(rejection_reasons[:3])}",
                criteria_breakdown={
                    "rejection_phrases_found": rejection_reasons,
                    "style": "wellness_influencer",
                    "recommendation": "Rewrite with deadpan Liquid Death energy"
                }
            )
        
        # Check for warning phrases
        warnings = []
        for phrase in self.warning_phrases:
            if phrase in content and "stop breathe apply" not in content.replace(",", "").replace(".", ""):
                warnings.append(phrase)
        
        # Use AI for deeper style analysis
        prompt = f"""Analyze this Jesse A. Eisenbalm post for Liquid Death style compliance:

POST:
{post.content}

SCORING CRITERIA:

1. SPECIFICITY (0-3 points):
- 3: Names specific company/person AND includes numbers
- 2: Names specific company/person OR includes numbers  
- 1: Generic but has some concrete detail
- 0: Completely generic ("corporate world", "digital age")

2. BREVITY (0-2 points):
- 2: Short punchy lines, under 100 words total
- 1: Medium length, some punchy lines
- 0: Long paragraphs, wordy

3. VOICE (0-3 points):
- 3: Perfect deadpan, states absurdity as fact, no preaching
- 2: Mostly deadpan, minor earnestness
- 1: Some preachiness or advice-giving creeping in
- 0: Full wellness influencer mode

4. LIP BALM PIVOT (0-2 points):
- 2: Natural, deadpan, doesn't try too hard
- 1: Acceptable but slightly forced
- 0: Preachy, "you deserve this", or trying too hard

WARNINGS DETECTED: {warnings if warnings else "None"}

Return JSON:
{{
    "specificity_score": <0-3>,
    "specificity_notes": "what's specific or generic",
    "brevity_score": <0-2>,
    "brevity_notes": "word count and structure",
    "voice_score": <0-3>,
    "voice_notes": "deadpan vs preachy assessment",
    "pivot_score": <0-2>,
    "pivot_notes": "how the lip balm mention lands",
    "total_score": <sum, 0-10>,
    "approved": <true if total >= 7>,
    "overall_feedback": "one sentence summary",
    "liquid_death_rating": "Would Liquid Death's team approve? yes/maybe/no"
}}"""
        
        try:
            result = await self.generate(prompt)
            scores = result.get("content", {})
            
            if isinstance(scores, str):
                # Fallback if AI returns string
                return ValidationScore(
                    agent_name=self.name,
                    score=6.0,
                    approved=False,
                    feedback="Could not parse style analysis",
                    criteria_breakdown={"raw": scores}
                )
            
            total = scores.get("total_score", 5)
            
            # Apply warning penalty
            if warnings:
                total = max(0, total - len(warnings) * 0.5)
            
            return ValidationScore(
                agent_name=self.name,
                score=float(total),
                approved=total >= 7.0,
                feedback=scores.get("overall_feedback", ""),
                criteria_breakdown={
                    "specificity": scores.get("specificity_score", 0),
                    "brevity": scores.get("brevity_score", 0),
                    "voice": scores.get("voice_score", 0),
                    "pivot": scores.get("pivot_score", 0),
                    "liquid_death_approved": scores.get("liquid_death_rating", "unknown"),
                    "warnings": warnings
                }
            )
            
        except Exception as e:
            self.logger.error(f"Style validation failed: {e}")
            return ValidationScore(
                agent_name=self.name,
                score=5.0,
                approved=False,
                feedback=f"Validation error: {e}",
                criteria_breakdown={"error": str(e)}
            )