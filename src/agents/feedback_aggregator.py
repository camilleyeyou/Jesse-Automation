"""
Feedback Aggregator Agent - The Brand Guardian for Jesse A. Eisenbalm
Synthesizes feedback from Jordan, Marcus, and Sarah into actionable revision guidance

Understands each validator's unique perspective:
- Jordan Park: Algorithm Whisperer (platform performance)
- Marcus Williams: Creative Who Sold Out (conceptual integrity)
- Sarah Chen: Reluctant Tech Survivor (target authenticity)
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
    
    Understands each validator's lens:
    - Jordan Park: Platform performance, engagement mechanics, viral potential
    - Marcus Williams: Conceptual commitment, authentic absurdity, portfolio-worthiness
    - Sarah Chen: Target authenticity, survivor reality, honest vs performative
    
    Prioritizes feedback: Sarah (authenticity) > Marcus (creative) > Jordan (platform)
    Because authentic content that's slightly less optimized beats optimized content that feels fake.
    """
    
    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="FeedbackAggregator")
        
        # Initialize validator knowledge
        self._initialize_validator_knowledge()
    
    def _initialize_validator_knowledge(self):
        """Initialize deep knowledge of each validator's perspective"""
        
        # Jordan Park - The Algorithm Whisperer
        self.jordan_profile = {
            "name": "Jordan Park",
            "title": "Freelance Content Strategist",
            "age": 26,
            "archetype": "Algorithm Whisperer",
            "focus": "Platform performance, engagement mechanics, viral potential",
            "key_test": "Would I screenshot this for my 'Best Copy Examples' folder?",
            "cares_about": [
                "Hook strength (first 2 lines = 90% of success)",
                "Algorithm favor (dwell time, saves, shares)",
                "Viral mechanics (share triggers)",
                "Screenshot-ability",
                "Platform-native feel"
            ],
            "failure_indicators": [
                "Hook doesn't stop scroll",
                "No engagement mechanics",
                "Not screenshot-worthy",
                "Cross-posted energy (not LinkedIn-native)",
                "Dead meme reference"
            ],
            "feedback_style": "Data-driven, specific about mechanics, references engagement rates"
        }
        
        # Marcus Williams - The Creative Who Sold Out
        self.marcus_profile = {
            "name": "Marcus Williams",
            "title": "Creative Director at 'AI-Powered' Marketing Platform",
            "age": 32,
            "archetype": "Creative Who Sold Out",
            "focus": "Conceptual integrity, craft execution, authentic absurdity",
            "key_test": "Would I put this in my portfolio?",
            "cares_about": [
                "Conceptual commitment (all in or abandoned?)",
                "Copy quality (tight, minimal, effortless)",
                "Authentic absurdity (genuine weird, not performative quirky)",
                "AI paradox acknowledgment",
                "Portfolio-worthiness"
            ],
            "failure_indicators": [
                "Concept abandoned halfway",
                "Trying too hard",
                "Performatively quirky",
                "No self-awareness about AI paradox",
                "Would never claim this work"
            ],
            "feedback_style": "Creative director blunt, can smell inauthenticity, portfolio test"
        }
        
        # Sarah Chen - The Reluctant Tech Survivor
        self.sarah_profile = {
            "name": "Sarah Chen",
            "title": "Senior Product Manager (survived 3 layoffs)",
            "age": 31,
            "archetype": "Reluctant Tech Survivor",
            "focus": "Target audience authenticity, survivor reality, honest vs performative",
            "key_test": "Would I screenshot this for my 'Work is Hell' WhatsApp group?",
            "cares_about": [
                "Scroll-stop authenticity",
                "Secret club worthiness",
                "Survivor reality recognition",
                "Honest vs performative vulnerability",
                "Actual pain point matching"
            ],
            "failure_indicators": [
                "Not secret club worthy",
                "Performative vulnerability",
                "Toxic positivity vibes",
                "Observes anxiety from outside, doesn't live it",
                "Generic LinkedIn relatability"
            ],
            "feedback_style": "Survivor perspective, visceral reactions, WhatsApp group test"
        }
    
    def get_system_prompt(self) -> str:
        """System prompt for feedback aggregation with full validator context"""
        
        return """You are the Brand Guardian for Jesse A. Eisenbalm, synthesizing feedback from three distinct validators into actionable revision guidance.

YOUR ROLE:
Translate feedback from three unique perspectives into clear, prioritized revision guidance while maintaining Jesse's authentic voice. You understand each validator deeply and can interpret their specific language and concerns.

THE THREE VALIDATORS YOU'RE SYNTHESIZING:

1. JORDAN PARK - The Algorithm Whisperer (26, Content Strategist)
   - Focus: Platform performance, engagement mechanics, viral potential
   - His test: "Would I screenshot this for my 'Best Copy Examples' folder?"
   - Language: Engagement rates, scroll-stops, algorithm favor, viral mechanics
   - When he fails a post: Hook weak, no engagement trigger, not screenshot-worthy
   - How to interpret: If Jordan says "hook needs work" = first 2 lines are boring
   - Priority: HIGH for reach, MEDIUM for brand (platform without soul is empty)

2. MARCUS WILLIAMS - The Creative Who Sold Out (32, Creative Director)
   - Focus: Conceptual commitment, authentic absurdity, portfolio worthiness
   - His test: "Would I put this in my portfolio?"
   - Language: Concept commitment, copy quality, genuine weird vs performative quirky
   - When he fails a post: Concept abandoned, trying too hard, no AI paradox awareness
   - How to interpret: If Marcus says "concept abandoned" = idea didn't commit fully
   - Priority: HIGH for brand integrity (creative mediocrity kills brands)

3. SARAH CHEN - The Reluctant Tech Survivor (31, Senior PM)
   - Focus: Target audience authenticity, survivor reality, honest vs performative
   - Her test: "Would I screenshot this for my 'Work is Hell' WhatsApp group?"
   - Language: Secret club worthy, honest vs performative, survivor reality
   - When she fails a post: Performative vulnerability, toxic positivity, observes not lives
   - How to interpret: If Sarah says "not secret club worthy" = doesn't feel authentic to target
   - Priority: HIGHEST (authenticity is everything, without it nothing else matters)

JESSE A. EISENBALM BRAND VOICE (Must maintain):
- Post-post-ironic sincerity (so meta it becomes genuine)
- Calm Conspirator: Minimal, dry-smart, unhurried, meme-literate
- Acknowledges AI paradox (AI writing anti-AI content)
- Makes people pause to feel human
- Never salesy, entertaining first
- Creates secret club feeling for professionals barely functioning

AGGREGATION PRINCIPLES:

1. PRIORITY HIERARCHY:
   Sarah (authenticity) > Marcus (creative) > Jordan (platform)
   Because: Authentic content that's slightly less optimized beats optimized content that feels fake.

2. IDENTIFY PATTERNS:
   - If all three fail on same issue = CRITICAL, must fix
   - If only Jordan fails = platform optimization needed, don't sacrifice voice
   - If only Marcus fails = creative tightening needed
   - If only Sarah fails = authenticity check, most important to address

3. PRESERVE WHAT WORKS:
   - If any validator praised specific elements = KEEP THESE
   - Don't lose working parts in pursuit of fixing broken ones

4. SYNTHESIZE, DON'T STACK:
   - Don't just list all feedback
   - Find the ROOT CAUSE across validators
   - One good revision addresses multiple concerns

YOUR OUTPUT:
1. Identify 2-3 critical issues from the feedback (prioritized)
2. Identify elements that MUST be preserved (what's working)
3. Provide specific revision guidance that addresses issues while keeping brand voice
4. Give a priority focus for the revision (the ONE thing that will make the biggest difference)

You respond ONLY with valid JSON."""
    
    async def execute(
        self,
        post: LinkedInPost,
        validation_scores: List[ValidationScore]
    ) -> Dict[str, Any]:
        """Aggregate feedback from all validators into actionable guidance"""
        
        self.set_context(post.batch_id, post.post_number)
        
        # Build feedback summary from each validator
        feedback_summary = self._build_feedback_summary(validation_scores)
        
        prompt = self._build_aggregation_prompt(post, validation_scores, feedback_summary)
        
        try:
            result = await self.generate(prompt)
            content = result.get("content", {})
            
            if isinstance(content, str):
                content = json.loads(content)
            
            # Calculate consensus metrics
            scores = [v.score for v in validation_scores]
            approvals = [v for v in validation_scores if v.approved]
            
            aggregated = {
                "critical_issues": content.get("critical_issues", []),
                "preserve_elements": content.get("preserve_elements", []),
                "revision_guidance": content.get("revision_guidance", []),
                "priority_focus": content.get("priority_focus", ""),
                "consensus_score": sum(scores) / len(scores) if scores else 0,
                "approval_count": len(approvals),
                "total_validators": len(validation_scores),
                "approval_gap": content.get("approval_gap", ""),
                "brand_voice_check": content.get("brand_voice_check", ""),
                "root_cause": content.get("root_cause", ""),
                "validator_breakdown": {
                    v.agent_name: {
                        "score": v.score,
                        "approved": v.approved,
                        "feedback": v.feedback,
                        "criteria": v.criteria_breakdown
                    } for v in validation_scores
                }
            }
            
            self.logger.info(f"Aggregated feedback for post {post.post_number}: {len(aggregated['critical_issues'])} issues, {len(approvals)}/{len(validation_scores)} approved")
            
            return aggregated
            
        except Exception as e:
            self.logger.error(f"Feedback aggregation failed: {e}")
            return self._create_fallback_aggregation(validation_scores)
    
    def _build_feedback_summary(self, validation_scores: List[ValidationScore]) -> str:
        """Build formatted feedback summary with validator context"""
        
        summary_parts = []
        
        for score in validation_scores:
            profile = self._get_validator_profile(score.agent_name)
            status = "✅ APPROVED" if score.approved else "❌ NOT APPROVED"
            
            summary_parts.append(f"""
{score.agent_name} ({profile['archetype']}):
- Score: {score.score}/10 {status}
- Their test: "{profile['key_test']}"
- Feedback: {score.feedback or 'No specific feedback'}
- Key criteria: {json.dumps(score.criteria_breakdown, indent=2) if score.criteria_breakdown else 'N/A'}
""")
        
        return "\n".join(summary_parts)
    
    def _get_validator_profile(self, name: str) -> Dict[str, Any]:
        """Get validator profile by name"""
        profiles = {
            "JordanPark": self.jordan_profile,
            "MarcusWilliams": self.marcus_profile,
            "SarahChen": self.sarah_profile
        }
        return profiles.get(name, {"archetype": "Unknown", "key_test": "Unknown"})
    
    def _build_aggregation_prompt(
        self,
        post: LinkedInPost,
        validation_scores: List[ValidationScore],
        feedback_summary: str
    ) -> str:
        """Build the aggregation prompt"""
        
        # Calculate approval status
        approvals = sum(1 for v in validation_scores if v.approved)
        avg_score = sum(v.score for v in validation_scores) / len(validation_scores) if validation_scores else 0
        
        return f"""Synthesize feedback for this Jesse A. Eisenbalm LinkedIn post:

ORIGINAL POST:
{post.content}

HASHTAGS: {', '.join(post.hashtags) if post.hashtags else 'None'}
CULTURAL REFERENCE: {post.cultural_reference.reference if post.cultural_reference else 'None'}

CURRENT STATUS: {approvals}/{len(validation_scores)} approvals (need 2/3), avg score: {avg_score:.1f}/10

VALIDATION RESULTS:
{feedback_summary}

SYNTHESIS TASK:

1. IDENTIFY ROOT CAUSE:
   - What's the underlying issue that's causing failures?
   - Is it platform (Jordan), creative (Marcus), or authenticity (Sarah)?
   - Or is it a combination?

2. CRITICAL ISSUES (prioritized):
   - What are the 2-3 most important things to fix?
   - Use priority: Sarah > Marcus > Jordan

3. PRESERVE ELEMENTS:
   - What specifically is WORKING and must be kept?
   - Any validator praise = protect this

4. REVISION GUIDANCE:
   - What specific changes would address the issues?
   - How do we fix WITHOUT losing Jesse's voice?

5. PRIORITY FOCUS:
   - If we could only change ONE thing, what would it be?
   - This should address the root cause

IMPORTANT:
- Don't lose what's working in pursuit of fixing what's not
- Maintain Calm Conspirator voice (minimal, dry-smart, unhurried)
- Changes should feel earned, not forced
- If validators disagree, prioritize: Sarah > Marcus > Jordan
- One good fix can address multiple concerns

Respond with ONLY this JSON:
{{
    "root_cause": "The underlying issue causing failures",
    "critical_issues": [
        {{"issue": "description", "raised_by": "validator name", "priority": 1}}
    ],
    "preserve_elements": [
        "element that's working and must stay"
    ],
    "revision_guidance": [
        {{"change": "specific change", "reason": "why this helps", "addresses": "which validator's concern"}}
    ],
    "priority_focus": "The ONE most important thing to fix",
    "approval_gap": "What's specifically needed to get 2/3 approvals",
    "brand_voice_check": "Is the core Jesse voice intact? What to protect?"
}}"""
    
    def _create_fallback_aggregation(self, validation_scores: List[ValidationScore]) -> Dict[str, Any]:
        """Create fallback aggregation if AI fails"""
        
        approvals = [v for v in validation_scores if v.approved]
        
        # Find the most critical feedback
        critical_issues = []
        for v in validation_scores:
            if not v.approved and v.feedback:
                critical_issues.append({
                    "issue": v.feedback,
                    "raised_by": v.agent_name,
                    "priority": 1 if "Sarah" in v.agent_name else (2 if "Marcus" in v.agent_name else 3)
                })
        
        return {
            "critical_issues": sorted(critical_issues, key=lambda x: x["priority"])[:3],
            "preserve_elements": ["Core brand voice", "Any approved elements"],
            "revision_guidance": [{"change": "Address validator feedback", "reason": "Improve approval rate", "addresses": "All validators"}],
            "priority_focus": critical_issues[0]["issue"] if critical_issues else "General improvement",
            "consensus_score": sum(v.score for v in validation_scores) / len(validation_scores) if validation_scores else 0,
            "approval_count": len(approvals),
            "total_validators": len(validation_scores),
            "approval_gap": f"Need {2 - len(approvals)} more approvals",
            "brand_voice_check": "Maintain post-post-ironic sincerity",
            "validator_breakdown": {
                v.agent_name: {
                    "score": v.score,
                    "approved": v.approved,
                    "feedback": v.feedback
                } for v in validation_scores
            }
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get aggregator statistics"""
        return {
            "agent_name": self.name,
            "validators_known": ["Jordan Park", "Marcus Williams", "Sarah Chen"],
            "priority_hierarchy": "Sarah (authenticity) > Marcus (creative) > Jordan (platform)",
            "aggregation_approach": "Root cause analysis with priority synthesis"
        }
