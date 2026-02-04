"""
Comment Models for LinkedIn Comment Engagement System
Jesse A. Eisenbalm — Strategic Comment Generation

These models handle the full lifecycle of a LinkedIn comment:
1. Source post analysis
2. Comment generation (3 options)
3. Admin approval
4. Posting via LinkedIn API
5. Engagement tracking
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
import uuid


class CommentStyle(str, Enum):
    """Different comment styles Jesse can use"""
    KNOWING_NOD = "knowing_nod"           # Validates insight, adds observation
    ABSURDIST_TANGENT = "absurdist_tangent"  # Unexpected but relevant
    HUMAN_MOMENT = "human_moment"          # Grounds in embodied experience
    WITTY_INSIGHT = "witty_insight"        # Sharp reframe
    WARM_ENCOURAGEMENT = "warm_encouragement"  # Genuine support


class CommentStatus(str, Enum):
    """Status of a comment in the queue"""
    ANALYZING = "analyzing"      # Fetching/analyzing source post
    PENDING = "pending"          # Generated, awaiting review
    APPROVED = "approved"        # Admin approved, ready to post
    POSTED = "posted"            # Successfully posted to LinkedIn
    REJECTED = "rejected"        # Admin rejected
    FAILED = "failed"            # Posting failed


class PostTone(str, Enum):
    """Detected tone of the source post"""
    SERIOUS = "serious"
    CASUAL = "casual"
    CELEBRATORY = "celebratory"
    FRUSTRATED = "frustrated"
    VULNERABLE = "vulnerable"
    HUMOROUS = "humorous"
    THOUGHT_LEADERSHIP = "thought_leadership"
    NEWS_COMMENTARY = "news_commentary"


class SourcePostAnalysis(BaseModel):
    """Analysis of the LinkedIn post we're commenting on"""
    
    url: str = Field(..., description="LinkedIn post URL")
    urn: Optional[str] = Field(None, description="LinkedIn post URN (internal ID)")
    
    # Content
    content: str = Field(..., description="Post text content")
    author_name: str = Field(..., description="Post author's name")
    author_headline: Optional[str] = Field(None, description="Author's LinkedIn headline")
    author_type: str = Field("individual", description="'individual', 'influencer', 'company', 'executive'")
    
    # Analysis
    topic: str = Field(..., description="Main topic/theme of the post")
    tone: PostTone = Field(..., description="Detected tone")
    sentiment: str = Field("neutral", description="'positive', 'negative', 'neutral'")
    
    # Engagement context
    likes_count: Optional[int] = Field(None, description="Current likes")
    comments_count: Optional[int] = Field(None, description="Current comments")
    is_trending: bool = Field(False, description="Whether post appears to be trending")
    
    # Comment strategy
    recommended_styles: List[CommentStyle] = Field(
        default_factory=list,
        description="Recommended comment styles for this post"
    )
    topics_to_connect: List[str] = Field(
        default_factory=list,
        description="Topics we can naturally connect to Jesse's brand"
    )
    risk_assessment: str = Field(
        "low",
        description="'low', 'medium', 'high' — risk of comment backfiring"
    )
    
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


class CommentOption(BaseModel):
    """A single generated comment option"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    style: CommentStyle = Field(..., description="Comment style used")
    content: str = Field(..., min_length=10, max_length=500, description="The comment text")
    
    # Scoring
    tone_match_score: float = Field(..., ge=0, le=10, description="How well it matches post tone")
    brand_alignment_score: float = Field(..., ge=0, le=10, description="How on-brand for Jesse")
    value_add_score: float = Field(..., ge=0, le=10, description="Does it add to conversation?")
    overall_score: float = Field(..., ge=0, le=10, description="Combined score")
    
    # Reasoning
    reasoning: str = Field(..., description="Why this comment works")
    potential_risks: Optional[str] = Field(None, description="Any concerns about this approach")
    
    @property
    def is_recommended(self) -> bool:
        """Whether this option is recommended based on scores"""
        return self.overall_score >= 7.0


class CommentEngagement(BaseModel):
    """Tracking engagement on our posted comment"""
    
    likes: int = Field(0, description="Likes on our comment")
    replies: int = Field(0, description="Replies to our comment")
    
    # Broader impact (if trackable)
    profile_visits_24h: Optional[int] = Field(None, description="Company profile visits in 24h after")
    follower_change_24h: Optional[int] = Field(None, description="Follower change in 24h after")
    
    # Tracking metadata
    first_checked_at: Optional[datetime] = None
    last_checked_at: Optional[datetime] = None
    check_count: int = 0
    
    def update(self, likes: int, replies: int):
        """Update engagement metrics"""
        self.likes = likes
        self.replies = replies
        self.last_checked_at = datetime.utcnow()
        self.check_count += 1
        if not self.first_checked_at:
            self.first_checked_at = self.last_checked_at


class LinkedInComment(BaseModel):
    """
    Complete comment record — from analysis to posting to engagement
    
    This is the main model that tracks the full lifecycle of a comment.
    """
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Source post
    source_post: SourcePostAnalysis = Field(..., description="Analysis of the post we're commenting on")
    
    # Generated options
    comment_options: List[CommentOption] = Field(
        default_factory=list,
        description="Generated comment options (usually 3)"
    )
    
    # Selection
    selected_option_id: Optional[str] = Field(None, description="ID of selected option")
    final_comment: Optional[str] = Field(None, description="Final comment text (may be edited)")
    
    # Status tracking
    status: CommentStatus = Field(CommentStatus.ANALYZING)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    generated_at: Optional[datetime] = Field(None, description="When options were generated")
    approved_at: Optional[datetime] = Field(None, description="When admin approved")
    approved_by: Optional[str] = Field(None, description="Admin who approved")
    posted_at: Optional[datetime] = Field(None, description="When posted to LinkedIn")
    rejected_at: Optional[datetime] = Field(None, description="When rejected")
    rejection_reason: Optional[str] = Field(None, description="Why it was rejected")
    
    # LinkedIn response
    comment_urn: Optional[str] = Field(None, description="LinkedIn's URN for our comment")
    linkedin_response: Optional[Dict[str, Any]] = Field(None, description="Raw API response")
    error_message: Optional[str] = Field(None, description="Error if posting failed")
    
    # Engagement
    engagement: CommentEngagement = Field(default_factory=CommentEngagement)
    
    @property
    def selected_option(self) -> Optional[CommentOption]:
        """Get the selected comment option"""
        if not self.selected_option_id:
            return None
        for opt in self.comment_options:
            if opt.id == self.selected_option_id:
                return opt
        return None
    
    @property
    def best_option(self) -> Optional[CommentOption]:
        """Get the highest-scored option"""
        if not self.comment_options:
            return None
        return max(self.comment_options, key=lambda x: x.overall_score)
    
    def select_option(self, option_id: str, edited_text: Optional[str] = None):
        """Select a comment option for posting"""
        self.selected_option_id = option_id
        if edited_text:
            self.final_comment = edited_text
        else:
            opt = self.selected_option
            if opt:
                self.final_comment = opt.content
    
    def approve(self, approved_by: str, edited_text: Optional[str] = None):
        """Approve the comment for posting"""
        if edited_text:
            self.final_comment = edited_text
        self.status = CommentStatus.APPROVED
        self.approved_at = datetime.utcnow()
        self.approved_by = approved_by
    
    def reject(self, reason: Optional[str] = None):
        """Reject the comment"""
        self.status = CommentStatus.REJECTED
        self.rejected_at = datetime.utcnow()
        self.rejection_reason = reason
    
    def mark_posted(self, comment_urn: str, linkedin_response: Dict[str, Any]):
        """Mark as successfully posted"""
        self.status = CommentStatus.POSTED
        self.posted_at = datetime.utcnow()
        self.comment_urn = comment_urn
        self.linkedin_response = linkedin_response
    
    def mark_failed(self, error: str):
        """Mark as failed to post"""
        self.status = CommentStatus.FAILED
        self.error_message = error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "source_post": {
                "url": self.source_post.url,
                "content": self.source_post.content[:200] + "..." if len(self.source_post.content) > 200 else self.source_post.content,
                "author_name": self.source_post.author_name,
                "topic": self.source_post.topic,
                "tone": self.source_post.tone.value if self.source_post.tone else "casual",
                "recommended_styles": [s.value for s in self.source_post.recommended_styles],
            },
            "comment_options": [
                {
                    "id": opt.id,
                    "style": opt.style.value,
                    "content": opt.content,
                    "overall_score": opt.overall_score,
                    "reasoning": opt.reasoning
                }
                for opt in self.comment_options
            ],
            "selected_option_id": self.selected_option_id,
            "final_comment": self.final_comment,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "posted_at": self.posted_at.isoformat() if self.posted_at else None,
            "engagement": {
                "likes": self.engagement.likes,
                "replies": self.engagement.replies
            }
        }


class CommentQueueSummary(BaseModel):
    """Summary stats for the comment queue"""
    
    total: int = 0
    pending: int = 0
    approved: int = 0
    posted: int = 0
    rejected: int = 0
    failed: int = 0
    
    # Engagement totals
    total_likes: int = 0
    total_replies: int = 0
    avg_engagement_rate: float = 0.0
    
    # Performance
    top_performing_styles: List[Dict[str, Any]] = Field(default_factory=list)


class CommentGenerationRequest(BaseModel):
    """Request to generate comments for a LinkedIn post"""
    
    post_url: str = Field(..., description="LinkedIn post URL")
    post_content: str = Field(..., description="Post content text")
    author_name: str = Field("Unknown", description="Post author name")
    author_headline: Optional[str] = Field(None, description="Author's headline")
    num_options: int = Field(3, ge=1, le=5, description="Number of options to generate")
    preferred_styles: Optional[List[str]] = Field(None, description="Preferred comment styles")


class CommentApprovalRequest(BaseModel):
    """Request to approve a comment"""

    option_id: Optional[str] = Field(None, description="ID of selected option (auto-selects best if not provided)")
    edited_text: Optional[str] = Field(None, description="Edited comment text (optional)")
    approved_by: str = Field("admin", description="Who is approving")
    post_immediately: bool = Field(False, description="Whether to post immediately after approval")
