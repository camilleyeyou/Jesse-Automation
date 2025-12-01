"""
Batch Models for processing multiple posts
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import uuid4
from pydantic import BaseModel, Field
from .post import LinkedInPost, PostStatus


class BatchMetrics(BaseModel):
    """Metrics for a batch of posts with image generation tracking"""
    total_posts: int = 0
    approved_posts: int = 0
    rejected_posts: int = 0
    revised_posts: int = 0
    
    # Image metrics
    posts_with_images: int = 0
    image_generation_rate: float = 0.0
    image_cost: float = 0.0
    text_cost: float = 0.0
    
    approval_rate: float = 0.0
    revision_success_rate: float = 0.0
    average_score: float = 0.0
    average_processing_time: float = 0.0
    
    total_tokens_used: int = 0
    total_cost: float = 0.0
    
    cultural_reference_performance: Dict[str, float] = Field(default_factory=dict)
    agent_agreement_rate: float = 0.0
    
    def calculate(self, posts: List[LinkedInPost]) -> None:
        """Calculate metrics from posts including image statistics"""
        if not posts:
            return
        
        self.total_posts = len(posts)
        self.approved_posts = sum(1 for p in posts if p.status == PostStatus.APPROVED)
        self.rejected_posts = sum(1 for p in posts if p.status == PostStatus.REJECTED)
        self.revised_posts = sum(1 for p in posts if p.revision_count > 0)
        
        # Image metrics
        self.posts_with_images = sum(1 for p in posts if p.has_image)
        self.image_generation_rate = self.posts_with_images / self.total_posts if self.total_posts > 0 else 0
        
        # Calculate image cost (Gemini: $0.039 per image)
        self.image_cost = self.posts_with_images * 0.039
        
        self.approval_rate = self.approved_posts / self.total_posts if self.total_posts > 0 else 0
        
        if self.revised_posts > 0:
            revised_approved = sum(1 for p in posts 
                                 if p.revision_count > 0 and p.status == PostStatus.APPROVED)
            self.revision_success_rate = revised_approved / self.revised_posts
        
        approved = [p for p in posts if p.status == PostStatus.APPROVED]
        if approved:
            self.average_score = sum(p.average_score for p in approved) / len(approved)
        
        processing_times = [p.processing_time_seconds for p in posts 
                           if p.processing_time_seconds is not None]
        if processing_times:
            self.average_processing_time = sum(processing_times) / len(processing_times)
        
        self.total_tokens_used = sum(p.total_tokens_used for p in posts)
        self.total_cost = sum(p.estimated_cost for p in posts)
        
        # Calculate text cost (total - image cost)
        self.text_cost = max(0, self.total_cost - self.image_cost)


class Batch(BaseModel):
    """Represents a batch of posts being processed"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    config: Dict[str, Any] = Field(default_factory=dict)
    posts: List[LinkedInPost] = Field(default_factory=list)
    metrics: BatchMetrics = Field(default_factory=BatchMetrics)
    
    status: str = "pending"  # pending, processing, completed, failed
    error: Optional[str] = None
    
    def add_post(self, post: LinkedInPost) -> None:
        """Add a post to the batch"""
        post.batch_id = self.id
        self.posts.append(post)
    
    def complete(self) -> None:
        """Mark batch as completed and calculate metrics"""
        self.completed_at = datetime.utcnow()
        self.status = "completed"
        self.metrics.calculate(self.posts)
    
    def get_approved_posts(self) -> List[LinkedInPost]:
        """Get all approved posts"""
        return [p for p in self.posts if p.status == PostStatus.APPROVED]
    
    def get_rejected_posts(self) -> List[LinkedInPost]:
        """Get all rejected posts"""
        return [p for p in self.posts if p.status == PostStatus.REJECTED]
    
    def get_posts_with_images(self) -> List[LinkedInPost]:
        """Get all posts that have generated images"""
        return [p for p in self.posts if p.has_image]
    
    def get_approved_posts_with_images(self) -> List[LinkedInPost]:
        """Get approved posts that have images"""
        return [p for p in self.posts if p.status == PostStatus.APPROVED and p.has_image]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert batch to dictionary"""
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
            "error": self.error,
            "posts": [p.to_dict() for p in self.posts],
            "metrics": {
                "total_posts": self.metrics.total_posts,
                "approved_posts": self.metrics.approved_posts,
                "rejected_posts": self.metrics.rejected_posts,
                "approval_rate": self.metrics.approval_rate,
                "posts_with_images": self.metrics.posts_with_images,
                "total_cost": self.metrics.total_cost,
                "image_cost": self.metrics.image_cost,
                "text_cost": self.metrics.text_cost
            }
        }
