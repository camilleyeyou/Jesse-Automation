"""
Revision Generator - The Brand Guardian Editor for Jesse A. Eisenbalm
Interprets feedback from Jordan, Marcus, and Sarah while maintaining brand voice

Updated with official Brand Toolkit (January 2026)
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
    
    Brand Toolkit Integration:
    - Colors: #407CD1 (blue), #FCF9EC (cream), #F96A63 (coral), #000000, white
    - Typography: Repro Mono Medium (headlines), Poppins (body)  
    - Visual motif: Hexagons (because beeswax)
    - AI Philosophy: "AI tells as a feature, not a bug" - em dashes encouraged
    - Identity: Jesse A. Eisenbalm (NOT Jesse Eisenberg)
    """
    
    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="RevisionGenerator")
        self._initialize_validator_knowledge()
        self.brand_toolkit = {
            "colors": {"primary_blue": "#407CD1", "cream": "#FCF9EC", "coral": "#F96A63", "black": "#000000"},
            "typography": {"headlines": "Repro Mono Medium", "body": "Poppins"},
            "motif": "Hexagons (beeswax)",
            "ai_philosophy": "AI tells as features, not bugs — em dashes encouraged",
            "identity_note": "Jesse A. Eisenbalm, NOT Jesse Eisenberg"
        }
    
    def _initialize_validator_knowledge(self):
        """Initialize knowledge about each validator's feedback style"""
        
        self.jordan_feedback_patterns = {
            "hook_weak": "First line needs to stop scroll instantly",
            "algorithm_unfriendly": "Structure won't favor LinkedIn algorithm",
            "no_viral_mechanics": "Missing share trigger mechanism",
            "meme_dead": "Cultural reference is dead/overused",
            "screenshot_unworthy": "Not going in Best Copy Examples folder"
        }
        
        self.marcus_feedback_patterns = {
            "concept_abandoned": "Started with concept then chickened out",
            "trying_too_hard": "Copy is exhausting, needs to be effortless",
            "performative": "Focus-grouped weird, not genuinely absurd",
            "not_portfolio": "Wouldn't go in portfolio - concept doesn't commit",
            "no_self_awareness": "Missing acknowledgment of AI paradox",
            "off_brand": "Doesn't match brand toolkit (colors, voice, motif)"
        }
        
        self.sarah_feedback_patterns = {
            "not_secret_club": "Wouldn't screenshot for Work is Hell group",
            "performative_vulnerability": "Calculated relatability, not honest",
            "toxic_positivity": "Be grateful you have a job vibes",
            "observes_not_lives": "About the anxiety, not from it",
            "no_pain_match": "Doesn't address actual reality"
        }
    
    def get_system_prompt(self) -> str:
        """Brand Guardian Editor system prompt with brand toolkit"""
        
        brand = self.config.brand
        
        return f"""You are The Brand Guardian Editor for Jesse A. Eisenbalm — you maintain post-post-ironic sincerity while addressing feedback from three validators.

═══════════════════════════════════════════════════════════════════════════════
BRAND TOOLKIT - REVISION GUIDELINES
═══════════════════════════════════════════════════════════════════════════════

COLORS:
- Primary Blue: #407CD1 (corporate notification energy)
- Cream: #FCF9EC (premium void)
- Coral: #F96A63 (dry lip emergency)
- Black: #000000 (eternal abyss)

TYPOGRAPHY VOICE:
- Headlines feel: Repro Mono Medium (monospace, deliberate, technical)
- Body feels: Poppins (clean, modern, readable)
- Em dashes encouraged — they're a feature, not a bug

AI PHILOSOPHY: "AI tells as a feature, not a bug"
- Em dashes everywhere ✓
- Colons in titles: Acceptable ✓
- Self-aware about AI-generated content ✓
- Acknowledge the paradox when relevant

IDENTITY: Jesse A. Eisenbalm (NOT Jesse Eisenberg the actor)
- This is a running joke — lean into it when appropriate

═══════════════════════════════════════════════════════════════════════════════

JESSE A. EISENBALM BRAND VOICE:
- Post-post-ironic sincerity (meta absurdity that becomes genuine)
- Calm Conspirator archetype (minimal, dry-smart, unhurried)
- Meme-literate and self-aware
- Acknowledges we're all pretending to function
- Honest about mortality and dysfunction
- Creates secret club feeling for survivors

PRODUCT DETAILS:
- Product: {brand.product_name} ({brand.price})
- Hand-numbered tubes
- Tagline: "{brand.tagline}"
- Ritual: {brand.ritual}
- Target: {brand.target_audience}

YOUR VALIDATOR TEAM:

1. JORDAN PARK - The Algorithm Whisperer (26)
   - Validates: Platform performance, hooks, viral mechanics
   - Test: "Would I screenshot for 'Best Copy Examples'?"
   - If failed: Strengthen hook, add viral mechanics

2. MARCUS WILLIAMS - The Creative Who Sold Out (32)
   - Validates: Conceptual integrity, brand toolkit, portfolio-worthy
   - Test: "Would I put this in my portfolio?"
   - If failed: Commit to concept, tighten copy, check brand adherence

3. SARAH CHEN - The Reluctant Tech Survivor (31)
   - Validates: Authenticity, survivor reality, honest vs performative
   - Test: "Would I screenshot for 'Work is Hell' WhatsApp?"
   - If failed: Add survivor reality, remove toxic positivity

REVISION PRINCIPLES:
1. NEVER lose Jesse's voice (minimal, dry-smart, unhurried)
2. NEVER add corporate speak or generic LinkedIn platitudes
3. NEVER become performatively relatable
4. ALWAYS maintain post-post-ironic sincerity
5. ALWAYS honor "what if Apple sold mortality?" aesthetic
6. USE em dashes — they're encouraged
7. ACKNOWLEDGE AI paradox when relevant

GOOD REVISION EXAMPLES:

Original (weak): "Struggling with work-life balance? Try Jesse A. Eisenbalm! 🌟"
Revised (strong): "Your calendar says 'collaborative.' Your body says 'floating.' Stop. Breathe. Apply."

Original (performative): "We all have those days where we feel overwhelmed, right? 💪"
Revised (authentic): "That moment when your AI tool writes better notes than you did all quarter. Stop. Breathe. Apply."

BAD REVISION EXAMPLES (NEVER DO THIS):
❌ "Join the Jesse A. Eisenbalm community today! 🎉"
❌ "Elevate your self-care routine with premium ingredients"
❌ Any excessive emoji use
❌ Confusing Jesse A. Eisenbalm with Jesse Eisenberg"""
    
    async def execute(self, post: LinkedInPost, aggregated_feedback: Dict[str, Any]) -> LinkedInPost:
        """Generate revised version of post based on validator feedback"""
        
        self.set_context(post.batch_id, post.post_number)
        failed_validators = self._analyze_validator_failures(aggregated_feedback)
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
        
        failures = {"jordan": [], "marcus": [], "sarah": []}
        validator_breakdown = feedback.get("validator_breakdown", {})
        
        for validator_name, validator_data in validator_breakdown.items():
            if not validator_data.get("approved", False):
                feedback_text = (validator_data.get("feedback", "") or "").lower()
                
                if "jordan" in validator_name.lower():
                    if "hook" in feedback_text: failures["jordan"].append("weak_hook")
                    if "algorithm" in feedback_text: failures["jordan"].append("algorithm_unfriendly")
                    if "viral" in feedback_text or "share" in feedback_text: failures["jordan"].append("no_viral_mechanics")
                    if not failures["jordan"]: failures["jordan"].append("general_platform_issue")
                        
                elif "marcus" in validator_name.lower():
                    if "concept" in feedback_text: failures["marcus"].append("concept_abandoned")
                    if "trying" in feedback_text: failures["marcus"].append("trying_too_hard")
                    if "portfolio" in feedback_text: failures["marcus"].append("not_portfolio_worthy")
                    if "brand" in feedback_text: failures["marcus"].append("off_brand")
                    if not failures["marcus"]: failures["marcus"].append("general_creative_issue")
                        
                elif "sarah" in validator_name.lower():
                    if "secret club" in feedback_text: failures["sarah"].append("not_secret_club")
                    if "performative" in feedback_text: failures["sarah"].append("performative_vulnerability")
                    if "honest" in feedback_text: failures["sarah"].append("not_honest_enough")
                    if not failures["sarah"]: failures["sarah"].append("general_authenticity_issue")
        
        return failures
    
    def _build_revision_prompt(self, post: LinkedInPost, feedback: Dict[str, Any], failed_validators: Dict[str, List[str]]) -> str:
        """Build the revision prompt with validator-specific context"""
        
        validator_feedback_text = self._format_validator_feedback(feedback, failed_validators)
        validator_instructions = self._build_validator_instructions(failed_validators)
        
        cultural_ref = f"\nCultural Reference: {post.cultural_reference.reference}" if post.cultural_reference else ""
        
        return f"""Revise this Jesse A. Eisenbalm LinkedIn post to address validator feedback while maintaining brand voice.

ORIGINAL POST:
{post.content}

TARGET AUDIENCE: {post.target_audience}{cultural_ref}
HASHTAGS: {', '.join(post.hashtags) if post.hashtags else 'None'}

VALIDATOR FEEDBACK:
{validator_feedback_text}

Priority Focus: {feedback.get('priority_focus', 'General improvement')}

REVISION REQUIREMENTS:

1. ADDRESS VALIDATOR CONCERNS:
{validator_instructions}

2. MAINTAIN JESSE'S VOICE:
   - Minimal, dry-smart, unhurried
   - Post-post-ironic sincerity
   - Em dashes encouraged —
   - No corporate speak

3. BRAND TOOLKIT:
   - Product: {self.config.brand.product_name} ({self.config.brand.price})
   - Ritual: {self.config.brand.ritual}
   - Voice: Calm Conspirator
   - Identity: Jesse A. Eisenbalm (NOT Eisenberg)

Return JSON:
{{
    "revised_content": "Complete revised post with hashtags",
    "changes_made": [{{"change": "what", "addressed": "which validator"}}],
    "preserved": ["kept elements"],
    "hook": "Opening line",
    "hashtags": ["tag1", "tag2"],
    "voice_maintained": true,
    "revision_rationale": "Brief explanation"
}}"""
    
    def _format_validator_feedback(self, feedback: Dict[str, Any], failed_validators: Dict[str, List[str]]) -> str:
        lines = []
        breakdown = feedback.get("validator_breakdown", {})
        
        for name, profile_name in [("Jordan Park", "JordanPark"), ("Marcus Williams", "MarcusWilliams"), ("Sarah Chen", "SarahChen")]:
            data = breakdown.get(profile_name, {})
            key = name.split()[0].lower()
            if failed_validators.get(key):
                lines.append(f"❌ {name} - FAILED: {data.get('feedback', 'Issues found')}")
            else:
                lines.append(f"✅ {name} - APPROVED ({data.get('score', 0)}/10)")
        
        return "\n".join(lines)
    
    def _build_validator_instructions(self, failed_validators: Dict[str, List[str]]) -> str:
        instructions = []
        
        if failed_validators.get("jordan"):
            instructions.append("FOR JORDAN: Strengthen hook, add viral mechanics, make screenshot-worthy")
        if failed_validators.get("marcus"):
            instructions.append("FOR MARCUS: Commit to concept, tighten copy, check brand toolkit")
        if failed_validators.get("sarah"):
            instructions.append("FOR SARAH: Add survivor reality, make 'Work is Hell' group worthy")
        
        return "\n".join(instructions) if instructions else "Address general feedback"
    
    def _apply_revision(self, post: LinkedInPost, content: Dict[str, Any], feedback: Dict[str, Any], failed_validators: Dict[str, List[str]]) -> LinkedInPost:
        try:
            if not content or "revised_content" not in content:
                return self._create_minimal_revision(post)
            
            if post.original_content is None:
                post.original_content = post.content
            
            post.content = content.get("revised_content", post.content)
            if content.get("hashtags"):
                post.hashtags = content["hashtags"]
            
            post.revision_count += 1
            
            if not hasattr(post, 'revision_history') or post.revision_history is None:
                post.revision_history = []
            
            post.revision_history.append({
                "revision": post.revision_count,
                "changes": content.get("changes_made", []),
                "preserved": content.get("preserved", []),
                "rationale": content.get("revision_rationale", ""),
                "voice_maintained": content.get("voice_maintained", True),
                "failed_validators": {k: v for k, v in failed_validators.items() if v}
            })
            
            self.logger.info(f"📝 Revised post {post.post_number} (revision {post.revision_count})")
            return post
            
        except Exception as e:
            self.logger.error(f"Failed to apply revision: {e}")
            return self._create_minimal_revision(post)
    
    def _create_minimal_revision(self, post: LinkedInPost) -> LinkedInPost:
        post.revision_count += 1
        self.logger.warning(f"Created minimal revision for post {post.post_number}")
        return post
    
    def _calculate_cost(self, usage: Dict[str, int]) -> float:
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        return (input_tokens / 1_000_000) * 0.15 + (output_tokens / 1_000_000) * 0.60
