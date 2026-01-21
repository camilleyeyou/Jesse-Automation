"""
Style Validator V2 - STRICT Liquid Death Energy Enforcement
Rejects wellness platitudes, advice-giving, and generic content
"""

import logging
from typing import Dict, Any, List
from .base_agent import BaseAgent
from ..models.post import LinkedInPost, ValidationScore

logger = logging.getLogger(__name__)


class StyleValidator(BaseAgent):
    """
    Enforces Jesse A. Eisenbalm's Liquid Death style
    
    INSTANT REJECTION for:
    - "In a world..." openings
    - Advice-giving ("don't forget", "remember to")
    - Wellness speak ("you deserve", "self-care")
    - Generic pivots without specificity
    - Too long (over 100 words)
    """
    
    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="StyleValidator")
        
        # INSTANT REJECTION - any of these = score under 7
        self.instant_kill_phrases = [
            # Wellness influencer speak
            "in a world",
            "don't forget to",
            "remember to", 
            "it's okay to",
            "you deserve",
            "self-care is",
            "take a moment",
            "radical act",
            "rebellion against",
            "invest in yourself",
            "invest in the rebellion",
            
            # Generic/flowery
            "amidst the chaos",
            "ride the wave",
            "in this together",
            "you're not alone",
            "digital chaos",
            "checking in on",
            "moment of relief",
            "here for the long haul",
            "one constant in",
            
            # Awkward lip balm pivots
            "your lips wait",
            "waiting for moisture",
            "lips remain dry, waiting",
            "your need for moisture",
            "while your lips",
            "keeping your lips human",
            "lips are still there",
            
            # Preachy structures
            "while you're",
            "who's taking time",
            "what about the",
            "how many are",
        ]
        
        self.logger.info(f"StyleValidator initialized with {len(self.instant_kill_phrases)} kill phrases")
    
    def get_system_prompt(self) -> str:
        return "You validate content for Liquid Death style compliance."
    
    async def execute(self, post: LinkedInPost) -> ValidationScore:
        """Validate post style - STRICT enforcement"""
        
        content = post.content.lower()
        content_words = len(post.content.split())
        
        # Check for instant kill phrases
        kills_found = []
        for phrase in self.instant_kill_phrases:
            if phrase in content:
                kills_found.append(phrase)
        
        if kills_found:
            return ValidationScore(
                agent_name=self.name,
                score=3.0,  # Hard fail
                approved=False,
                feedback=f"REJECTED: Contains banned phrases: {', '.join(kills_found[:3])}",
                criteria_breakdown={
                    "kill_phrases": kills_found,
                    "word_count": content_words,
                    "style": "wellness_influencer_detected"
                }
            )
        
        # Check word count (should be 40-80, max 100)
        if content_words > 100:
            return ValidationScore(
                agent_name=self.name,
                score=5.0,
                approved=False,
                feedback=f"REJECTED: Too long ({content_words} words). Max 100, ideal 40-80.",
                criteria_breakdown={
                    "word_count": content_words,
                    "issue": "too_verbose"
                }
            )
        
        # Check for line breaks (should have multiple short lines)
        lines = [l.strip() for l in post.content.split('\n') if l.strip()]
        
        if len(lines) < 3:
            return ValidationScore(
                agent_name=self.name,
                score=5.5,
                approved=False,
                feedback=f"REJECTED: Only {len(lines)} lines. Need 3-5 short punchy lines.",
                criteria_breakdown={
                    "line_count": len(lines),
                    "issue": "not_punchy_enough"
                }
            )
        
        # Check for specificity (should mention specific names/numbers)
        has_specificity = False
        
        # Check for numbers
        import re
        if re.search(r'\$?\d+', post.content):
            has_specificity = True
        
        # Check for proper nouns (capitalized words not at start of sentence)
        words = post.content.split()
        for i, word in enumerate(words):
            if i > 0 and word[0].isupper() and word.lower() not in ['i', 'jesse', 'eisenbalm', 'a.']:
                has_specificity = True
                break
        
        # Score based on quality
        score = 7.0
        feedback_parts = []
        
        if content_words <= 60:
            score += 1.0
            feedback_parts.append("Good brevity")
        elif content_words <= 80:
            score += 0.5
        
        if len(lines) >= 4:
            score += 0.5
            feedback_parts.append("Good structure")
        
        if has_specificity:
            score += 1.0
            feedback_parts.append("Has specific details")
        else:
            score -= 1.0
            feedback_parts.append("Needs more specific names/numbers")
        
        # Check hashtag count
        hashtag_count = post.content.count('#')
        if hashtag_count == 3:
            score += 0.5
        elif hashtag_count > 4:
            score -= 0.5
            feedback_parts.append("Too many hashtags")
        
        score = min(10.0, max(0.0, score))
        approved = score >= 7.0
        
        return ValidationScore(
            agent_name=self.name,
            score=score,
            approved=approved,
            feedback=f"{'APPROVED' if approved else 'NEEDS WORK'}: {'; '.join(feedback_parts) if feedback_parts else 'Acceptable style'}",
            criteria_breakdown={
                "word_count": content_words,
                "line_count": len(lines),
                "has_specificity": has_specificity,
                "hashtag_count": hashtag_count
            }
        )