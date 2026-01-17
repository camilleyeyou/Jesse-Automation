"""
Feedback Aggregator Agent - The Brand Guardian for Jesse A. Eisenbalm
Synthesizes feedback from Jordan, Marcus, and Sarah into actionable revision guidance

Updated with official Brand Toolkit (January 2026)
"""

import json
import logging
from typing import Dict, Any, List
from .base_agent import BaseAgent
from ..models.post import LinkedInPost, ValidationScore

logger = logging.getLogger(__name__)


class FeedbackAggregatorAgent(BaseAgent):
    """
    The Brand Guardian - Synthesizes feedback from three unique validator perspectives
    
    Brand Toolkit Integration:
    - Colors: #407CD1 (blue), #FCF9EC (cream), #F96A63 (coral), #000000, white
    - Typography: Repro Mono Medium (headlines), Poppins (body)
    - Visual motif: Hexagons (because beeswax)
    - AI Philosophy: "AI tells as a feature, not a bug"
    - Identity: Jesse A. Eisenbalm (NOT Jesse Eisenberg)
    """
    
    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="FeedbackAggregator")
        self._initialize_validator_knowledge()
        self.brand_toolkit = {
            "colors": {"primary_blue": "#407CD1", "cream": "#FCF9EC", "coral": "#F96A63", "black": "#000000"},
            "typography": {"headlines": "Repro Mono Medium", "body": "Poppins"},
            "motif": "Hexagons (beeswax)",
            "ai_philosophy": "AI tells as features, not bugs",
            "identity_note": "Jesse A. Eisenbalm, NOT Jesse Eisenberg"
        }
    
    def _initialize_validator_knowledge(self):
        """Initialize deep knowledge of each validator's perspective"""
        
        self.jordan_profile = {
            "name": "Jordan Park",
            "title": "Freelance Content Strategist",
            "age": 26,
            "archetype": "Algorithm Whisperer",
            "focus": "Platform performance, engagement mechanics, viral potential",
            "key_test": "Would I screenshot this for my 'Best Copy Examples' folder?",
            "cares_about": ["Hook strength", "Algorithm favor", "Viral mechanics", "Screenshot-ability", "Platform-native feel"],
            "feedback_style": "Data-driven, specific about mechanics"
        }
        
        self.marcus_profile = {
            "name": "Marcus Williams",
            "title": "Creative Director at 'AI-Powered' Marketing Platform",
            "age": 32,
            "archetype": "Creative Who Sold Out",
            "focus": "Conceptual integrity, craft execution, authentic absurdity, brand toolkit",
            "key_test": "Would I put this in my portfolio?",
            "cares_about": ["Conceptual commitment", "Copy quality", "Authentic absurdity", "AI paradox", "Brand toolkit adherence"],
            "feedback_style": "Creative director blunt, portfolio test"
        }
        
        self.sarah_profile = {
            "name": "Sarah Chen",
            "title": "Senior Product Manager (survived 3 layoffs)",
            "age": 31,
            "archetype": "Reluctant Tech Survivor",
            "focus": "Target audience authenticity, survivor reality, honest vs performative",
            "key_test": "Would I screenshot this for my 'Work is Hell' WhatsApp group?",
            "cares_about": ["Scroll-stop authenticity", "Secret club worthiness", "Survivor reality", "Honest vulnerability"],
            "feedback_style": "Survivor perspective, visceral reactions"
        }
    
    def get_system_prompt(self) -> str:
        """System prompt for feedback aggregation with brand toolkit"""
        
        return """You are the Brand Guardian for Jesse A. Eisenbalm, synthesizing feedback from three validators.

BRAND TOOLKIT:
- Colors: #407CD1 (blue), #FCF9EC (cream), #F96A63 (coral), #000000 (black)
- Typography: Repro Mono Medium (headlines), Poppins (body)
- Motif: Hexagons (beeswax)
- AI Philosophy: "AI tells as features, not bugs" - em dashes encouraged, self-aware about AI
- Identity: Jesse A. Eisenbalm (NOT Jesse Eisenberg)

VALIDATORS:
1. JORDAN PARK (Algorithm Whisperer): Platform performance, hooks, viral mechanics
2. MARCUS WILLIAMS (Creative Who Sold Out): Conceptual integrity, brand toolkit, portfolio-worthy
3. SARAH CHEN (Reluctant Tech Survivor): Authenticity, survivor reality, secret club worthy

PRIORITY: Sarah (authenticity) > Marcus (creative) > Jordan (platform)

BRAND VOICE: Post-post-ironic sincerity, Calm Conspirator, minimal, dry-smart, unhurried, meme-literate.

You respond ONLY with valid JSON."""
    
    async def execute(self, post: LinkedInPost, validation_scores: List[ValidationScore]) -> Dict[str, Any]:
        """Aggregate feedback from all validators into actionable guidance"""
        
        self.set_context(post.batch_id, post.post_number)
        feedback_summary = self._build_feedback_summary(validation_scores)
        prompt = self._build_aggregation_prompt(post, validation_scores, feedback_summary)
        
        try:
            result = await self.generate(prompt)
            content = result.get("content", {})
            if isinstance(content, str):
                content = json.loads(content)
            
            scores = [v.score for v in validation_scores]
            approvals = [v for v in validation_scores if v.approved]
            
            return {
                "critical_issues": content.get("critical_issues", []),
                "preserve_elements": content.get("preserve_elements", []),
                "revision_guidance": content.get("revision_guidance", []),
                "priority_focus": content.get("priority_focus", ""),
                "consensus_score": sum(scores) / len(scores) if scores else 0,
                "approval_count": len(approvals),
                "total_validators": len(validation_scores),
                "approval_gap": content.get("approval_gap", ""),
                "brand_voice_check": content.get("brand_voice_check", ""),
                "brand_toolkit_compliance": content.get("brand_toolkit_compliance", ""),
                "root_cause": content.get("root_cause", ""),
                "validator_breakdown": {
                    v.agent_name: {"score": v.score, "approved": v.approved, "feedback": v.feedback, "criteria": v.criteria_breakdown}
                    for v in validation_scores
                }
            }
        except Exception as e:
            self.logger.error(f"Feedback aggregation failed: {e}")
            return self._create_fallback_aggregation(validation_scores)
    
    def _build_feedback_summary(self, validation_scores: List[ValidationScore]) -> str:
        summary_parts = []
        for score in validation_scores:
            profile = self._get_validator_profile(score.agent_name)
            status = "✅ APPROVED" if score.approved else "❌ NOT APPROVED"
            summary_parts.append(f"{score.agent_name} ({profile['archetype']}): {score.score}/10 {status}\nFeedback: {score.feedback or 'None'}")
        return "\n\n".join(summary_parts)
    
    def _get_validator_profile(self, name: str) -> Dict[str, Any]:
        profiles = {"JordanPark": self.jordan_profile, "MarcusWilliams": self.marcus_profile, "SarahChen": self.sarah_profile}
        return profiles.get(name, {"archetype": "Unknown", "key_test": "Unknown"})
    
    def _build_aggregation_prompt(self, post: LinkedInPost, validation_scores: List[ValidationScore], feedback_summary: str) -> str:
        approvals = sum(1 for v in validation_scores if v.approved)
        avg_score = sum(v.score for v in validation_scores) / len(validation_scores) if validation_scores else 0
        
        return f"""Synthesize feedback for this Jesse A. Eisenbalm post:

POST: {post.content}

STATUS: {approvals}/{len(validation_scores)} approvals, avg score: {avg_score:.1f}/10

VALIDATION RESULTS:
{feedback_summary}

Respond with JSON containing: root_cause, critical_issues, preserve_elements, revision_guidance, priority_focus, approval_gap, brand_voice_check, brand_toolkit_compliance"""
    
    def _create_fallback_aggregation(self, validation_scores: List[ValidationScore]) -> Dict[str, Any]:
        approvals = [v for v in validation_scores if v.approved]
        critical_issues = [{"issue": v.feedback, "raised_by": v.agent_name, "priority": 1} for v in validation_scores if not v.approved and v.feedback]
        
        return {
            "critical_issues": critical_issues[:3],
            "preserve_elements": ["Core brand voice"],
            "revision_guidance": [{"change": "Address validator feedback", "reason": "Improve approval rate", "addresses": "All"}],
            "priority_focus": critical_issues[0]["issue"] if critical_issues else "General improvement",
            "consensus_score": sum(v.score for v in validation_scores) / len(validation_scores) if validation_scores else 0,
            "approval_count": len(approvals),
            "total_validators": len(validation_scores),
            "approval_gap": f"Need {2 - len(approvals)} more approvals",
            "brand_voice_check": "Maintain post-post-ironic sincerity",
            "brand_toolkit_compliance": "Verify brand adherence",
            "validator_breakdown": {v.agent_name: {"score": v.score, "approved": v.approved, "feedback": v.feedback} for v in validation_scores}
        }
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "agent_name": self.name,
            "validators_known": ["Jordan Park", "Marcus Williams", "Sarah Chen"],
            "priority_hierarchy": "Sarah > Marcus > Jordan",
            "brand_toolkit": self.brand_toolkit
        }