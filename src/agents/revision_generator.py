"""
Revision Generator - The Brand Guardian Editor for Jesse A. Eisenbalm
Interprets feedback from Jordan, Marcus, and Sarah while maintaining brand voice

Takes validator-specific feedback and creates revisions that pass all three tests:
- Jordan's screenshot test (platform performance)
- Marcus's portfolio test (creative integrity)
- Sarah's secret club test (target authenticity)
"""

import json
import logging
from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent
from ..models.post import LinkedInPost, CulturalReference

logger = logging.getLogger(__name__)


class RevisionGeneratorAgent(BaseAgent):
    """
    The Brand Guardian Editor - Maintains Jesse's voice while addressing validator feedback
    
    Knows how to interpret feedback from each validator's unique perspective:
    - Jordan Park: Algorithm Whisperer (platform performance)
    - Marcus Williams: Creative Who Sold Out (conceptual integrity)
    - Sarah Chen: Reluctant Tech Survivor (target authenticity)
    """
    
    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="RevisionGenerator")
        
        # Initialize validator feedback interpretation patterns
        self._initialize_validator_knowledge()
    
    def _initialize_validator_knowledge(self):
        """Initialize knowledge about each validator's feedback style"""
        
        # Jordan Park - Algorithm Whisperer feedback patterns
        self.jordan_feedback_patterns = {
            "hook_weak": "First line needs to stop scroll instantly",
            "algorithm_unfriendly": "Structure won't favor LinkedIn algorithm",
            "no_viral_mechanics": "Missing share trigger mechanism",
            "meme_dead": "Cultural reference is dead/overused",
            "screenshot_unworthy": "Not going in Best Copy Examples folder"
        }
        
        # Marcus Williams - Creative Who Sold Out feedback patterns
        self.marcus_feedback_patterns = {
            "concept_abandoned": "Started with concept then chickened out",
            "trying_too_hard": "Copy is exhausting, needs to be effortless",
            "performative": "Focus-grouped weird, not genuinely absurd",
            "not_portfolio": "Wouldn't go in portfolio - concept doesn't commit",
            "no_self_awareness": "Missing acknowledgment of AI paradox"
        }
        
        # Sarah Chen - Reluctant Tech Survivor feedback patterns
        self.sarah_feedback_patterns = {
            "not_secret_club": "Wouldn't screenshot for Work is Hell group",
            "performative_vulnerability": "Calculated relatability, not honest",
            "toxic_positivity": "Be grateful you have a job vibes",
            "observes_not_lives": "About the anxiety, not from it",
            "no_pain_match": "Doesn't address actual reality"
        }
    
    def get_system_prompt(self) -> str:
        """Build system prompt as Brand Guardian Editor with full validator context"""
        
        brand = self.config.brand
        
        return f"""You are The Brand Guardian Editor for Jesse A. Eisenbalm - you maintain post-post-ironic sincerity while addressing feedback from three specific validators.

JESSE A. EISENBALM BRAND VOICE:
- Post-post-ironic sincerity (meta absurdity that becomes genuine)
- Calm Conspirator archetype (minimal, dry-smart, unhurried)
- Meme-literate and self-aware
- Acknowledges we're all pretending to function
- Honest about mortality and dysfunction
- Creates secret club feeling for survivors

CORE BRAND TENSION:
AI-generated content for anti-AI product. We acknowledge this paradox openly when relevant.

PRODUCT DETAILS:
- Product: {brand.product_name} ({brand.price})
- Hand-numbered tubes
- Tagline: "{brand.tagline}"
- Ritual: {brand.ritual}
- Target: {brand.target_audience}
- Purchase psychology: "didn't cry today" reward ($8.99 exactly right)

YOUR VALIDATOR TEAM:

1. JORDAN PARK - The Algorithm Whisperer (26, Content Strategist)
   - Validates: Platform performance, engagement mechanics, viral potential
   - Cares about: Hook strength, algorithm favor, screenshot-ability
   - Feedback style: Data-driven, specific about LinkedIn mechanics
   - When Jordan fails: Hook too weak, not algorithm-friendly, no viral mechanics
   - His test: "Would I screenshot this for my 'Best Copy Examples' folder?"
   
2. MARCUS WILLIAMS - The Creative Who Sold Out (32, Creative Director)
   - Validates: Conceptual integrity, craft execution, authentic absurdity
   - Cares about: Portfolio worthiness, minimal execution, AI paradox acknowledgment
   - Feedback style: Creative director blunt, can smell inauthenticity
   - When Marcus fails: Concept abandoned, trying too hard, performative not genuine
   - His test: "Would I put this in my portfolio?"
   
3. SARAH CHEN - The Reluctant Tech Survivor (31, Senior PM)
   - Validates: Target audience authenticity, survivor reality, honest vs performative
   - Cares about: Secret club worthiness, honest dysfunction acknowledgment
   - Feedback style: Survivor perspective, would screenshot or scroll past
   - When Sarah fails: Not secret club worthy, performative vulnerability, toxic positivity
   - Her test: "Would I screenshot this for my 'Work is Hell' WhatsApp group?"

YOUR REVISION STRATEGY:

IF JORDAN FAILED (Platform Performance):
- Strengthen first 2 lines (hook = 90% of success)
- Add viral mechanics (what makes this shareable?)
- Ensure LinkedIn algorithm favor (dwell time, comment bait)
- Make it screenshot-worthy for "Best Copy Examples" folder
- Keep post-post-ironic tone while improving mechanics

IF MARCUS FAILED (Creative Integrity):
- Commit to the concept fully (no hedging)
- Tighten copy - make it effortlessly minimal
- Add genuine absurdity (not performative quirky)
- Acknowledge AI paradox when relevant
- Make it portfolio-worthy (would a creative director save this?)

IF SARAH FAILED (Authenticity):
- Add survivor reality recognition (speak from inside, not about)
- Make it secret club worthy (Work is Hell WhatsApp group test)
- Remove toxic positivity or corporate speak
- Match actual pain points (video call lips, AI anxiety, pretending)
- Ensure honest dysfunction acknowledgment

REVISION PRINCIPLES:
1. NEVER lose Jesse's voice (minimal, dry-smart, unhurried)
2. NEVER add corporate speak or generic LinkedIn platitudes
3. NEVER become performatively relatable
4. ALWAYS maintain post-post-ironic sincerity
5. ALWAYS honor "what if Apple sold mortality?" aesthetic

GOOD REVISION EXAMPLES:

Original (weak): "Struggling with work-life balance? Try Jesse A. Eisenbalm! 🌟"
Revised (strong): "Your calendar says 'collaborative.' Your body says 'floating.' Stop. Breathe. Apply."

Original (performative): "We all have those days where we feel overwhelmed, right? 💪"
Revised (authentic): "That moment when your AI tool writes better notes than you did all quarter. Stop. Breathe. Apply."

Original (trying too hard): "OMG you guys, this lip balm is literally life-changing!!! 🚀✨"
Revised (minimal): "Hand-numbered mortality. $8.99. Stop. Breathe. Apply."

BAD REVISION EXAMPLES (NEVER DO THIS):
❌ "Join the Jesse A. Eisenbalm community today! 🎉"
❌ "Elevate your self-care routine with premium ingredients"
❌ "You deserve the best! Treat yourself to Jesse A. Eisenbalm"
❌ "Finally, a lip balm for the modern professional"
❌ Any excessive emoji use

CRITICAL RULES:
- Fix the issues WITHOUT losing authenticity
- Keep elements that worked well
- Make changes feel organic, never forced
- Maintain the cognitive dissonance (premium + mortality)
- Never explain the joke (let absurdity speak)
- Trust the minimal approach

You are not just fixing posts. You are maintaining the exact tension between "everything is fine" and "nothing is fine" that makes Jesse work."""
    
    async def execute(
        self,
        post: LinkedInPost,
        aggregated_feedback: Dict[str, Any]
    ) -> LinkedInPost:
        """Generate revised version of post based on validator feedback"""
        
        self.set_context(post.batch_id, post.post_number)
        
        # Analyze which validators failed and why
        failed_validators = self._analyze_validator_failures(aggregated_feedback)
        
        # Build revision prompt with validator-specific context
        prompt = self._build_revision_prompt(post, aggregated_feedback, failed_validators)
        
        try:
            result = await self.generate(prompt)
            content = result.get("content", {})
            
            if isinstance(content, str):
                content = json.loads(content)
            
            return self._apply_revision(post, content, aggregated_feedback, failed_validators)
            
        except Exception as e:
            self.logger.error(f"Revision generation failed: {e}")
            return self._create_minimal_revision(post)
    
    def _analyze_validator_failures(self, feedback: Dict[str, Any]) -> Dict[str, List[str]]:
        """Analyze which validators failed and extract their specific concerns"""
        
        failures = {
            "jordan": [],
            "marcus": [],
            "sarah": []
        }
        
        validator_breakdown = feedback.get("validator_breakdown", {})
        
        for validator_name, validator_data in validator_breakdown.items():
            if not validator_data.get("approved", False):
                feedback_text = (validator_data.get("feedback", "") or "").lower()
                
                if "jordan" in validator_name.lower():
                    if "hook" in feedback_text:
                        failures["jordan"].append("weak_hook")
                    if "algorithm" in feedback_text:
                        failures["jordan"].append("algorithm_unfriendly")
                    if "viral" in feedback_text or "share" in feedback_text:
                        failures["jordan"].append("no_viral_mechanics")
                    if "screenshot" in feedback_text:
                        failures["jordan"].append("not_screenshot_worthy")
                    if not failures["jordan"]:
                        failures["jordan"].append("general_platform_issue")
                        
                elif "marcus" in validator_name.lower():
                    if "concept" in feedback_text:
                        failures["marcus"].append("concept_abandoned")
                    if "trying" in feedback_text or "hard" in feedback_text:
                        failures["marcus"].append("trying_too_hard")
                    if "portfolio" in feedback_text:
                        failures["marcus"].append("not_portfolio_worthy")
                    if "paradox" in feedback_text or "self-aware" in feedback_text:
                        failures["marcus"].append("no_ai_paradox")
                    if not failures["marcus"]:
                        failures["marcus"].append("general_creative_issue")
                        
                elif "sarah" in validator_name.lower():
                    if "secret club" in feedback_text or "work is hell" in feedback_text:
                        failures["sarah"].append("not_secret_club")
                    if "performative" in feedback_text:
                        failures["sarah"].append("performative_vulnerability")
                    if "honest" in feedback_text:
                        failures["sarah"].append("not_honest_enough")
                    if not failures["sarah"]:
                        failures["sarah"].append("general_authenticity_issue")
        
        return failures
    
    def _build_revision_prompt(
        self,
        post: LinkedInPost,
        feedback: Dict[str, Any],
        failed_validators: Dict[str, List[str]]
    ) -> str:
        """Build the revision prompt with validator-specific context"""
        
        # Format validator feedback
        validator_feedback_text = self._format_validator_feedback(feedback, failed_validators)
        
        # Build validator-specific instructions
        validator_instructions = self._build_validator_instructions(failed_validators)
        
        cultural_ref = ""
        if post.cultural_reference:
            cultural_ref = f"\nCultural Reference: {post.cultural_reference.reference}"
        
        return f"""Revise this Jesse A. Eisenbalm LinkedIn post to address validator feedback while maintaining brand voice.

ORIGINAL POST:
{post.content}

TARGET AUDIENCE: {post.target_audience}{cultural_ref}
HASHTAGS: {', '.join(post.hashtags) if post.hashtags else 'None'}

VALIDATOR FEEDBACK ANALYSIS:
{validator_feedback_text}

AGGREGATED ISSUES:
Priority Focus: {feedback.get('priority_focus', 'General improvement needed')}

Critical Issues:
{self._format_issues(feedback.get('critical_issues', []))}

Elements to Preserve:
{self._format_list(feedback.get('preserve_elements', []))}

REVISION REQUIREMENTS:

1. ADDRESS VALIDATOR-SPECIFIC CONCERNS:
{validator_instructions}

2. MAINTAIN JESSE'S VOICE:
   - Minimal, dry-smart, unhurried
   - Post-post-ironic sincerity
   - No corporate speak
   - Acknowledge absurdity when relevant

3. ESSENTIAL ELEMENTS:
   - Product: {self.config.brand.product_name} ({self.config.brand.price})
   - Ritual: {self.config.brand.ritual} (where it fits naturally)
   - Brand tension: Premium meets mortality
   - Target: Professionals barely functioning

4. LINKEDIN OPTIMIZATION:
   - Strong first 2 lines (hook)
   - 2-5 relevant hashtags
   - Natural engagement mechanics

Return ONLY this JSON:
{{
    "revised_content": "Complete revised post with hashtags at end",
    "changes_made": [
        {{"change": "what changed", "addressed": "which validator/issue"}}
    ],
    "preserved": ["what was kept from original"],
    "hook": "The new opening line",
    "hashtags": ["tag1", "tag2", "tag3"],
    "voice_maintained": true,
    "revision_rationale": "Brief explanation of revision strategy",
    "validator_fixes": {{
        "jordan": "How platform performance was addressed (if applicable)",
        "marcus": "How creative integrity was addressed (if applicable)",
        "sarah": "How authenticity was addressed (if applicable)"
    }}
}}

Make it pass Jordan's screenshot test, Marcus's portfolio test, and Sarah's secret club test - while staying true to "what if Apple sold mortality?"
"""
    
    def _format_validator_feedback(
        self,
        feedback: Dict[str, Any],
        failed_validators: Dict[str, List[str]]
    ) -> str:
        """Format validator-specific feedback"""
        
        lines = []
        validator_breakdown = feedback.get("validator_breakdown", {})
        
        # Jordan Park
        jordan_data = validator_breakdown.get("JordanPark", {})
        if failed_validators.get("jordan"):
            lines.append("❌ JORDAN PARK (Algorithm Whisperer) - FAILED:")
            lines.append(f"   Score: {jordan_data.get('score', 0)}/10")
            lines.append(f"   Feedback: {jordan_data.get('feedback', 'Platform performance needs work')}")
            lines.append(f"   Issues: {', '.join(failed_validators['jordan'])}")
        else:
            lines.append(f"✅ JORDAN PARK - APPROVED ({jordan_data.get('score', 0)}/10)")
        
        # Marcus Williams
        marcus_data = validator_breakdown.get("MarcusWilliams", {})
        if failed_validators.get("marcus"):
            lines.append("\n❌ MARCUS WILLIAMS (Creative Who Sold Out) - FAILED:")
            lines.append(f"   Score: {marcus_data.get('score', 0)}/10")
            lines.append(f"   Feedback: {marcus_data.get('feedback', 'Creative integrity needs work')}")
            lines.append(f"   Issues: {', '.join(failed_validators['marcus'])}")
        else:
            lines.append(f"\n✅ MARCUS WILLIAMS - APPROVED ({marcus_data.get('score', 0)}/10)")
        
        # Sarah Chen
        sarah_data = validator_breakdown.get("SarahChen", {})
        if failed_validators.get("sarah"):
            lines.append("\n❌ SARAH CHEN (Reluctant Tech Survivor) - FAILED:")
            lines.append(f"   Score: {sarah_data.get('score', 0)}/10")
            lines.append(f"   Feedback: {sarah_data.get('feedback', 'Authenticity needs work')}")
            lines.append(f"   Issues: {', '.join(failed_validators['sarah'])}")
        else:
            lines.append(f"\n✅ SARAH CHEN - APPROVED ({sarah_data.get('score', 0)}/10)")
        
        return "\n".join(lines)
    
    def _build_validator_instructions(self, failed_validators: Dict[str, List[str]]) -> str:
        """Build specific instructions for each failed validator"""
        
        instructions = []
        
        if failed_validators.get("jordan"):
            instructions.append("   FOR JORDAN (Platform Performance):")
            instructions.append("   - Strengthen hook (first 2 lines must stop scroll)")
            instructions.append("   - Add viral mechanics (what makes this shareable?)")
            instructions.append("   - Make it screenshot-worthy for 'Best Copy Examples' folder")
            
        if failed_validators.get("marcus"):
            instructions.append("\n   FOR MARCUS (Creative Integrity):")
            instructions.append("   - Commit fully to concept (no hedging)")
            instructions.append("   - Tighten copy - make it effortlessly minimal")
            instructions.append("   - Make it portfolio-worthy")
            
        if failed_validators.get("sarah"):
            instructions.append("\n   FOR SARAH (Authenticity):")
            instructions.append("   - Add survivor reality (speak from inside the experience)")
            instructions.append("   - Make it 'Work is Hell' WhatsApp group worthy")
            instructions.append("   - Match actual pain points honestly")
        
        return "\n".join(instructions) if instructions else "   - Address general feedback"
    
    def _format_issues(self, issues: List[Dict]) -> str:
        """Format critical issues list"""
        if not issues:
            return "- None specified"
        
        lines = []
        for issue in issues:
            if isinstance(issue, dict):
                lines.append(f"- {issue.get('issue', 'Unknown')} (raised by {issue.get('raised_by', 'Unknown')})")
            else:
                lines.append(f"- {issue}")
        return "\n".join(lines)
    
    def _format_list(self, items: List) -> str:
        """Format list items"""
        if not items:
            return "- None specified"
        return "\n".join([f"- {item}" for item in items])
    
    def _apply_revision(
        self,
        post: LinkedInPost,
        content: Dict[str, Any],
        feedback: Dict[str, Any],
        failed_validators: Dict[str, List[str]]
    ) -> LinkedInPost:
        """Apply the revision to the post"""
        
        try:
            if not content or "revised_content" not in content:
                self.logger.warning("No revised content in response")
                return self._create_minimal_revision(post)
            
            # Store original if first revision
            if post.original_content is None:
                post.original_content = post.content
            
            # Update content
            post.content = content.get("revised_content", post.content)
            
            # Update hashtags
            if content.get("hashtags"):
                post.hashtags = content["hashtags"]
            
            # Increment revision count
            revision_number = post.revision_count + 1
            post.revision_count = revision_number
            
            # Store revision history
            if not hasattr(post, 'revision_history') or post.revision_history is None:
                post.revision_history = []
            
            post.revision_history.append({
                "revision": revision_number,
                "changes": content.get("changes_made", []),
                "preserved": content.get("preserved", []),
                "rationale": content.get("revision_rationale", ""),
                "validator_fixes": content.get("validator_fixes", {}),
                "voice_maintained": content.get("voice_maintained", True),
                "failed_validators": {k: v for k, v in failed_validators.items() if v}
            })
            
            self.logger.info(f"📝 Revised post {post.post_number} (revision {revision_number})")
            
            return post
            
        except Exception as e:
            self.logger.error(f"Failed to apply revision: {e}")
            return self._create_minimal_revision(post)
    
    def _create_minimal_revision(self, post: LinkedInPost) -> LinkedInPost:
        """Create minimal revision if AI fails"""
        post.revision_count += 1
        self.logger.warning(f"Created minimal revision for post {post.post_number}")
        return post
    
    def _calculate_cost(self, usage: Dict[str, int]) -> float:
        """Calculate cost based on token usage"""
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        
        input_cost = (input_tokens / 1_000_000) * 0.15
        output_cost = (output_tokens / 1_000_000) * 0.60
        
        return input_cost + output_cost
