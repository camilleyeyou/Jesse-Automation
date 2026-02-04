"""
CommentGeneratorAgent — Strategic Comment Generation for Jesse A. Eisenbalm

This agent:
1. Analyzes LinkedIn posts to understand tone, topic, and context
2. Generates 3 distinct comment options using different styles
3. Scores each option for brand alignment and appropriateness
4. Recommends the best option while giving admin choice

The goal: Comments that add value, feel authentic, and subtly reinforce
the Jesse A. Eisenbalm brand without being salesy.
"""

import json
import logging
import random
from datetime import datetime
from typing import Dict, List, Optional, Any

from .base_agent import BaseAgent
from ..models.comment import (
    LinkedInComment,
    CommentOption,
    CommentStyle,
    CommentStatus,
    SourcePostAnalysis,
    PostTone,
    CommentEngagement
)

logger = logging.getLogger(__name__)


class CommentGeneratorAgent(BaseAgent):
    """
    The Comment Strategist — Jesse's voice in other people's comment sections
    
    Generates thoughtful, on-brand comments that:
    - Add genuine value to the conversation
    - Feel like Jesse's authentic voice (not marketing)
    - Match the tone of the original post
    - Subtly reinforce brand awareness without being salesy
    """
    
    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="CommentGenerator")
        
        # Initialize comment style definitions
        self._init_comment_styles()
        
        # Initialize topic connectors (how to link various topics to Jesse's brand)
        self._init_topic_connectors()
        
        self.logger.info("CommentGeneratorAgent initialized — Ready to engage")
    
    def _init_comment_styles(self):
        """Define the different comment styles Jesse can use"""
        
        self.comment_styles = {
            CommentStyle.KNOWING_NOD: {
                "name": "The Knowing Nod",
                "description": "Validates the post's insight and adds a specific observation",
                "when_to_use": [
                    "Thoughtful posts about work or life",
                    "Observations about corporate culture",
                    "Tech industry commentary"
                ],
                "tone": "Warm, validating, adds specificity",
                "examples": [
                    "This. The gap between 'calendar says collaborative' and 'soul says otherwise' is where most of us live.",
                    "The accuracy here is almost uncomfortable. Add 'pretending to type during Zoom' to the list.",
                    "Been thinking about this all week. The performance of productivity might be more exhausting than actual productivity."
                ],
                "avoid_when": ["Controversial posts", "Highly technical content"]
            },
            
            CommentStyle.ABSURDIST_TANGENT: {
                "name": "The Absurdist Tangent",
                "description": "Takes the topic somewhere unexpected but relevant",
                "when_to_use": [
                    "Posts about corporate absurdity",
                    "AI and automation discussions",
                    "Productivity culture critique"
                ],
                "tone": "Deadpan, unexpected, committed to the bit",
                "examples": [
                    "Somewhere a calendar app is achieving sentience just to feel the exhaustion of your Tuesday schedule.",
                    "The AI trained on our Slack messages must be developing a personality disorder by now.",
                    "In 2024, 'touching grass' is a radical act of rebellion. The grass remains unbothered."
                ],
                "avoid_when": ["Serious/vulnerable posts", "Grief or hardship", "Celebratory announcements"]
            },
            
            CommentStyle.HUMAN_MOMENT: {
                "name": "The Human Moment",
                "description": "Grounds tech/business talk in embodied human experience",
                "when_to_use": [
                    "Burnout discussions",
                    "AI anxiety posts",
                    "Work-life balance content",
                    "Remote work challenges"
                ],
                "tone": "Grounded, physical, gently philosophical",
                "examples": [
                    "The body keeps the score, and right now it's scoring your 7-hour Zoom marathon a 2/10.",
                    "Wild how we forgot that humans were designed for sunlight and movement, not rectangle-staring.",
                    "Sometimes the most productive thing you can do is remember you have a body that needs things."
                ],
                "avoid_when": ["Very casual/humorous posts", "Technical discussions"]
            },
            
            CommentStyle.WITTY_INSIGHT: {
                "name": "The Witty Insight",
                "description": "Sharp observation that reframes the post in a new light",
                "when_to_use": [
                    "Hot takes",
                    "Industry observations",
                    "Trend commentary",
                    "Counterintuitive points"
                ],
                "tone": "Sharp, clever, reframing",
                "examples": [
                    "The real AI disruption isn't job replacement—it's the existential crisis of having free time and no idea what to do with it.",
                    "We automated everything except the part where we're lonely mammals who need connection. Oops.",
                    "Interesting how 'work-life balance' became 'work-life blend.' Nobody asked for a smoothie."
                ],
                "avoid_when": ["Vulnerable posts", "Personal struggles", "Celebratory content"]
            },
            
            CommentStyle.WARM_ENCOURAGEMENT: {
                "name": "Warm Encouragement",
                "description": "Genuine support without toxic positivity",
                "when_to_use": [
                    "Vulnerability posts",
                    "Career transitions",
                    "Struggles and setbacks",
                    "Imposter syndrome content"
                ],
                "tone": "Warm, genuine, grounded",
                "examples": [
                    "The fact that you're even asking this question puts you ahead of 90% of people white-knuckling through pretending they have it figured out.",
                    "Normalize not having it all figured out. The people who look like they do are mostly just better at hiding it.",
                    "This takes guts to post. Most people are too busy performing confidence to admit when they're lost."
                ],
                "avoid_when": ["Boastful posts", "Hot takes", "Controversial content"]
            }
        }
    
    def _init_topic_connectors(self):
        """Topics and how Jesse can naturally connect to them"""
        
        self.topic_connectors = {
            "ai_technology": {
                "connection": "Jesse is AI-powered but advocates for human moments",
                "angles": [
                    "The irony of AI telling you to be more human",
                    "Automation anxiety and small rituals",
                    "The embodied vs digital experience"
                ]
            },
            "burnout_wellness": {
                "connection": "Small rituals as resistance to hustle culture",
                "angles": [
                    "Self-care that doesn't require a $400 spa day",
                    "The radical act of pausing",
                    "Bodies need care, not optimization"
                ]
            },
            "corporate_culture": {
                "connection": "Jesse sees the absurdity clearly",
                "angles": [
                    "Meeting culture as performance art",
                    "Corporate jargon as its own language",
                    "The performance of productivity"
                ]
            },
            "career_growth": {
                "connection": "Success doesn't require losing yourself",
                "angles": [
                    "Humanity as competitive advantage",
                    "Rest as strategy",
                    "The long game of not burning out"
                ]
            },
            "remote_work": {
                "connection": "Digital existence needs analog moments",
                "angles": [
                    "Screen fatigue is real",
                    "The death of the commute (mixed blessing)",
                    "Creating ritual without office structure"
                ]
            },
            "leadership": {
                "connection": "Good leaders remember everyone's human",
                "angles": [
                    "Vulnerability as strength",
                    "Creating space for humanness",
                    "Leading by actually caring"
                ]
            }
        }
    
    def get_system_prompt(self) -> str:
        """System prompt for comment generation"""
        
        return """You are the comment strategist for Jesse A. Eisenbalm, a premium lip balm brand that exists at the intersection of existential absurdism and genuine human care.

═══════════════════════════════════════════════════════════════════════════════
JESSE'S COMMENT VOICE
═══════════════════════════════════════════════════════════════════════════════

When commenting on other people's posts, Jesse is:
- ADDITIVE: Comments should add genuine value, not just agree
- AUTHENTIC: Sound like a smart friend, not a brand trying to get attention
- APPROPRIATE: Match the energy and tone of the original post
- SUBTLE: Brand awareness through voice, never mentioning products

VOICE CHARACTERISTICS:
- Dry wit with warmth underneath
- Specific observations over generic praise
- Em dashes — we love them
- Short and punchy (1-3 sentences max)
- Post-post-ironic: so self-aware it becomes genuine

WHAT JESSE COMMENTS NEVER DO:
- Mention lip balm or products
- Include links or CTAs
- Say "Great post!" or generic praise
- Try too hard to be clever
- Punch down or be mean
- Hijack the conversation
- Use hashtags in comments

═══════════════════════════════════════════════════════════════════════════════
COMMENT QUALITY CHECKLIST
═══════════════════════════════════════════════════════════════════════════════

Before finalizing a comment, check:
✓ Does it add something to the conversation?
✓ Would you be embarrassed if someone knew a brand wrote this? (If no = too try-hard)
✓ Does it match the tone of the original post?
✓ Is it short enough? (Comments should be brief)
✓ Could the post author appreciate this response?
✓ Would this make someone want to click on the profile?

═══════════════════════════════════════════════════════════════════════════════

You respond ONLY with valid JSON."""
    
    async def analyze_post(self, post_url: str, post_content: str, author_name: str = "Unknown") -> SourcePostAnalysis:
        """Analyze a LinkedIn post to understand how to comment on it"""
        
        prompt = f"""Analyze this LinkedIn post for comment strategy:

POST URL: {post_url}
AUTHOR: {author_name}

POST CONTENT:
{post_content}

Analyze and return JSON:
{{
    "topic": "Main topic/theme of the post (be specific)",
    "tone": "serious|casual|celebratory|frustrated|vulnerable|humorous|thought_leadership|news_commentary",
    "sentiment": "positive|negative|neutral",
    "author_type": "individual|influencer|company|executive",
    "is_trending": true/false (based on content quality/shareability),
    "recommended_styles": ["style1", "style2"] (from: knowing_nod, absurdist_tangent, human_moment, witty_insight, warm_encouragement),
    "topics_to_connect": ["topic1", "topic2"] (topics we can naturally connect to),
    "risk_assessment": "low|medium|high",
    "risk_notes": "Any concerns about commenting on this post",
    "key_themes": ["theme1", "theme2", "theme3"],
    "emotional_core": "What is the author really expressing/seeking?"
}}"""
        
        try:
            result = await self.generate(prompt)
            content = result.get("content", {})
            
            if isinstance(content, str):
                content = json.loads(content)
            
            # Handle nested structure
            if "analysis" in content:
                content = content["analysis"]
            
            return SourcePostAnalysis(
                url=post_url,
                content=post_content,
                author_name=author_name,
                author_type=content.get("author_type", "individual"),
                topic=content.get("topic", "general"),
                tone=PostTone(content.get("tone", "casual")),
                sentiment=content.get("sentiment", "neutral"),
                is_trending=content.get("is_trending", False),
                recommended_styles=[
                    CommentStyle(s) for s in content.get("recommended_styles", ["knowing_nod"])
                    if s in [e.value for e in CommentStyle]
                ],
                topics_to_connect=content.get("topics_to_connect", []),
                risk_assessment=content.get("risk_assessment", "low")
            )
            
        except Exception as e:
            self.logger.error(f"Post analysis failed: {e}")
            # Return basic analysis
            return SourcePostAnalysis(
                url=post_url,
                content=post_content,
                author_name=author_name,
                topic="general",
                tone=PostTone.CASUAL,
                recommended_styles=[CommentStyle.KNOWING_NOD]
            )
    
    async def generate_comments(
        self,
        analysis: SourcePostAnalysis,
        num_options: int = 3
    ) -> List[CommentOption]:
        """Generate comment options for a post"""
        
        # Select styles to use
        styles_to_use = analysis.recommended_styles[:num_options]
        
        # Fill with random styles if needed
        all_styles = list(CommentStyle)
        while len(styles_to_use) < num_options:
            remaining = [s for s in all_styles if s not in styles_to_use]
            if remaining:
                styles_to_use.append(random.choice(remaining))
            else:
                break
        
        # Build style descriptions for the prompt
        style_descriptions = []
        for style in styles_to_use:
            style_info = self.comment_styles[style]
            style_descriptions.append(f"""
STYLE: {style.value} ({style_info['name']})
Description: {style_info['description']}
Tone: {style_info['tone']}
Example: "{random.choice(style_info['examples'])}"
""")
        
        prompt = f"""Generate {num_options} comment options for this LinkedIn post.

═══════════════════════════════════════════════════════════════════════════════
SOURCE POST
═══════════════════════════════════════════════════════════════════════════════

Author: {analysis.author_name} ({analysis.author_type})
Topic: {analysis.topic}
Tone: {analysis.tone.value}
Sentiment: {analysis.sentiment}

Content:
{analysis.content}

═══════════════════════════════════════════════════════════════════════════════
COMMENT STYLES TO USE
═══════════════════════════════════════════════════════════════════════════════
{"".join(style_descriptions)}

═══════════════════════════════════════════════════════════════════════════════
REQUIREMENTS
═══════════════════════════════════════════════════════════════════════════════

Each comment must:
- Be 1-3 sentences MAX (brevity is key)
- Add genuine value (not just "great post!")
- Match the post's tone and energy
- Sound like a thoughtful person, not a brand
- NEVER mention products, lip balm, or Jesse A. Eisenbalm by name
- Use em dashes if it feels natural

Generate JSON:
{{
    "comments": [
        {{
            "style": "style_name",
            "content": "The actual comment text",
            "tone_match_score": 8.5,
            "brand_alignment_score": 9.0,
            "value_add_score": 7.5,
            "overall_score": 8.3,
            "reasoning": "Why this comment works for this post",
            "potential_risks": "Any concerns (or null)"
        }}
    ]
}}"""
        
        try:
            result = await self.generate(prompt)
            content = result.get("content", {})
            
            if isinstance(content, str):
                content = json.loads(content)
            
            # Handle nested structure
            if "comments" not in content and "options" in content:
                content["comments"] = content["options"]
            
            comments_data = content.get("comments", [])
            
            options = []
            for i, comment in enumerate(comments_data):
                try:
                    style_str = comment.get("style", styles_to_use[i].value if i < len(styles_to_use) else "knowing_nod")
                    
                    # Handle style parsing
                    try:
                        style = CommentStyle(style_str)
                    except ValueError:
                        style = styles_to_use[i] if i < len(styles_to_use) else CommentStyle.KNOWING_NOD
                    
                    option = CommentOption(
                        style=style,
                        content=comment.get("content", ""),
                        tone_match_score=float(comment.get("tone_match_score", 7.0)),
                        brand_alignment_score=float(comment.get("brand_alignment_score", 7.0)),
                        value_add_score=float(comment.get("value_add_score", 7.0)),
                        overall_score=float(comment.get("overall_score", 7.0)),
                        reasoning=comment.get("reasoning", ""),
                        potential_risks=comment.get("potential_risks")
                    )
                    options.append(option)
                except Exception as e:
                    self.logger.warning(f"Failed to parse comment option: {e}")
                    continue
            
            return options
            
        except Exception as e:
            self.logger.error(f"Comment generation failed: {e}")
            return []
    
    async def execute(
        self,
        post_url: str,
        post_content: str,
        author_name: str = "Unknown",
        author_headline: Optional[str] = None,
        num_options: int = 3,
        preferred_styles: Optional[List[CommentStyle]] = None
    ) -> LinkedInComment:
        """
        Main execution: Analyze post and generate comment options
        
        Args:
            post_url: LinkedIn post URL
            post_content: The text content of the post
            author_name: Post author's name
            author_headline: Author's LinkedIn headline
            num_options: Number of comment options to generate (default 3)
            preferred_styles: Optional list of preferred comment styles
            
        Returns:
            LinkedInComment with analysis and generated options
        """
        
        self.logger.info(f"Generating comments for post by {author_name}")
        
        # Step 1: Create the comment record
        comment = LinkedInComment(
            source_post=SourcePostAnalysis(
                url=post_url,
                content=post_content,
                author_name=author_name,
                author_headline=author_headline,
                topic="",  # Will be filled by analysis
                tone=PostTone.CASUAL  # Will be updated
            ),
            status=CommentStatus.ANALYZING
        )
        
        try:
            # Step 2: Analyze the post
            self.logger.info("Analyzing source post...")
            analysis = await self.analyze_post(post_url, post_content, author_name)
            
            # Update with analysis
            comment.source_post = analysis
            
            # Override recommended styles if preferred ones provided
            if preferred_styles:
                analysis.recommended_styles = preferred_styles
            
            # Step 3: Generate comment options
            self.logger.info(f"Generating {num_options} comment options...")
            options = await self.generate_comments(analysis, num_options)
            
            comment.comment_options = options
            comment.generated_at = datetime.utcnow()
            comment.status = CommentStatus.PENDING
            
            # Auto-select the best option (admin can change)
            if options:
                best = max(options, key=lambda x: x.overall_score)
                comment.selected_option_id = best.id
                comment.final_comment = best.content
            
            self.logger.info(f"✨ Generated {len(options)} comment options, best score: {comment.best_option.overall_score if comment.best_option else 'N/A'}")
            
            return comment
            
        except Exception as e:
            self.logger.error(f"Comment generation failed: {e}")
            comment.status = CommentStatus.FAILED
            comment.error_message = str(e)
            raise
    
    def get_style_info(self, style: CommentStyle) -> Dict[str, Any]:
        """Get information about a comment style"""
        return self.comment_styles.get(style, {})
    
    def get_all_styles(self) -> Dict[CommentStyle, Dict[str, Any]]:
        """Get all comment styles"""
        return self.comment_styles
