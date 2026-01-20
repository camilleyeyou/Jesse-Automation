"""
Content Orchestrator - The Master Controller for Jesse A. Eisenbalm
Coordinates all agents: Trend Scout → Content Generator → Validators → Queue

NOW WITH: Real-time trend integration for reactive, non-clichéd content

FIXED: Return format compatibility with main.py
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from ..models.post import LinkedInPost, ValidationScore
from ..agents.content_generator import ContentGeneratorAgent
from ..agents.feedback_aggregator import FeedbackAggregatorAgent
from ..agents.revision_generator import RevisionGeneratorAgent
from ..agents.validators import SarahChenValidator, MarcusWilliamsValidator, JordanParkValidator

# Import trend service
try:
    from ..infrastructure.trend_service import get_trend_service, TrendService
    TREND_SERVICE_AVAILABLE = True
except ImportError:
    TREND_SERVICE_AVAILABLE = False

logger = logging.getLogger(__name__)


class BatchResult:
    """Result object for batch generation - compatible with main.py expectations"""
    
    def __init__(self, batch_id: str, posts: List[LinkedInPost], media_type: str = "image"):
        self.batch_id = batch_id
        self.posts = posts
        self.media_type = media_type
        self.approved_posts = [p for p in posts if getattr(p, 'approved', True)]
        self.rejected_posts = [p for p in posts if not getattr(p, 'approved', True)]
    
    def get_approved_posts(self) -> List[LinkedInPost]:
        """Get list of approved posts"""
        return self.approved_posts
    
    def get_rejected_posts(self) -> List[LinkedInPost]:
        """Get list of rejected posts"""
        return self.rejected_posts
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "batch_id": self.batch_id,
            "approved": len(self.approved_posts),
            "rejected": len(self.rejected_posts),
            "media_type": self.media_type,
            "posts": [self._post_to_dict(p) for p in self.posts]
        }
    
    def _post_to_dict(self, post: LinkedInPost) -> Dict[str, Any]:
        """Convert post to dictionary"""
        return {
            "id": getattr(post, 'id', str(uuid.uuid4())),
            "content": post.content,
            "hashtags": post.hashtags,
            "image_path": getattr(post, 'image_path', None),
            "media_type": getattr(post, 'media_type', 'image'),
            "approved": getattr(post, 'approved', True),
            "score": getattr(post, 'validation_score', 0)
        }


class ContentOrchestrator:
    """
    Master orchestrator for Jesse A. Eisenbalm content generation
    
    Flow:
    1. Fetch trending news (NEW!)
    2. Generate content reacting to trends
    3. Validate with Sarah, Marcus, Jordan
    4. Revise if needed
    5. Queue approved posts
    """
    
    def __init__(self, ai_client, config, image_generator=None, queue_manager=None):
        self.ai_client = ai_client
        self.config = config
        self.image_generator = image_generator
        self.queue_manager = queue_manager
        
        # Initialize agents
        self.content_generator = ContentGeneratorAgent(ai_client, config)
        self.feedback_aggregator = FeedbackAggregatorAgent(ai_client, config)
        self.revision_generator = RevisionGeneratorAgent(ai_client, config)
        
        # Initialize validators
        self.validators = [
            SarahChenValidator(ai_client, config),
            MarcusWilliamsValidator(ai_client, config),
            JordanParkValidator(ai_client, config)
        ]
        
        # Initialize trend service
        self.trend_service = None
        if TREND_SERVICE_AVAILABLE:
            self.trend_service = get_trend_service()
            logger.info("✅ Trend service initialized - content will react to real news")
        else:
            logger.warning("⚠️ Trend service not available - using standard generation")
        
        # Track recent content to avoid repetition
        self.recent_topics = []
        self.recent_headlines = []
        
        logger.info("ContentOrchestrator initialized with trend-reactive generation")
    
    async def generate_batch(
        self, 
        num_posts: int = 1, 
        use_video: bool = False,
        force_trend_refresh: bool = False
    ) -> BatchResult:
        """
        Generate a batch of posts
        
        Returns BatchResult object compatible with main.py
        """
        
        batch_id = str(uuid.uuid4())
        media_type = "video" if use_video else "image"
        
        logger.info(f"Starting batch {batch_id} with {num_posts} posts (media: {media_type})")
        
        # Step 1: Fetch trending news for reactive content
        trending_context = None
        if self.trend_service:
            try:
                news = await self.trend_service.get_trending_news(force_refresh=force_trend_refresh)
                trending_context = self.trend_service.format_for_content_generator(news)
                
                # Track headlines to avoid repetition
                for item in news:
                    if item.headline not in self.recent_headlines:
                        self.recent_headlines.append(item.headline)
                
                # Keep only last 20 headlines
                self.recent_headlines = self.recent_headlines[-20:]
                
                logger.info(f"Fetched {len(news)} trending news items for content generation")
            except Exception as e:
                logger.warning(f"Failed to fetch trends: {e}")
        
        # Step 2: Generate posts
        approved_posts = []
        
        for i in range(num_posts):
            post_number = i + 1
            logger.info(f"Processing post {post_number} (media: {media_type})")
            
            try:
                post = await self._process_single_post(
                    post_number=post_number,
                    batch_id=batch_id,
                    trending_context=trending_context,
                    use_video=use_video
                )
                
                if post and getattr(post, 'approved', False):
                    approved_posts.append(post)
                    
            except Exception as e:
                logger.error(f"Post {post_number} failed: {e}")
                import traceback
                traceback.print_exc()
        
        logger.info(f"Batch {batch_id} completed: {len(approved_posts)}/{num_posts} approved")
        
        return BatchResult(batch_id=batch_id, posts=approved_posts, media_type=media_type)
    
    async def _process_single_post(
        self,
        post_number: int,
        batch_id: str,
        trending_context: Optional[str] = None,
        use_video: bool = False
    ) -> Optional[LinkedInPost]:
        """Process a single post through the full pipeline"""
        
        # Build avoid patterns from recent content
        avoid_patterns = {
            "recent_topics": self.recent_topics[-10:],
            "recent_headlines": self.recent_headlines[-5:]
        }
        
        # Step 1: Generate content with trending context
        post = await self.content_generator.execute(
            post_number=post_number,
            batch_id=batch_id,
            trending_context=trending_context,
            avoid_patterns=avoid_patterns
        )
        
        # Ensure post has image_path attribute
        if not hasattr(post, 'image_path'):
            post.image_path = None
        if not hasattr(post, 'media_type'):
            post.media_type = 'image'
        if not hasattr(post, 'approved'):
            post.approved = False
        if not hasattr(post, 'validation_score'):
            post.validation_score = 0
        
        # Track this topic
        if post.cultural_reference:
            self.recent_topics.append(post.cultural_reference.reference)
        self.recent_topics = self.recent_topics[-20:]  # Keep last 20
        
        # Step 2: Generate image/video
        if self.image_generator:
            try:
                media_result = await self.image_generator.execute(post, use_video=use_video)
                if media_result.get("success"):
                    post.image_path = media_result.get("path")
                    post.media_type = media_result.get("media_type", "image")
                else:
                    logger.warning(f"Post {post_number}: Media generation failed - {media_result.get('error')}")
                    post.image_path = None
            except Exception as e:
                logger.warning(f"Post {post_number}: Media generation failed - {e}")
                post.image_path = None
        
        # Step 3: Validate with all validators
        validation_scores = await self._validate_post(post)
        
        # Step 4: Aggregate feedback
        aggregated = await self.feedback_aggregator.execute(post, validation_scores)
        
        # Step 5: Check if approved (need 2/3 validators)
        approvals = sum(1 for v in validation_scores if v.approved)
        avg_score = sum(v.score for v in validation_scores) / len(validation_scores) if validation_scores else 0
        
        logger.info(f"Post {post_number}: Validated - {approvals}/3 approvals, avg score: {avg_score:.1f}")
        
        approved = approvals >= 2
        
        # Step 6: Revise if needed (one attempt)
        if not approved and approvals >= 1:
            logger.info(f"Post {post_number}: Attempting revision")
            post = await self.revision_generator.execute(post, aggregated)
            
            # Re-validate
            validation_scores = await self._validate_post(post)
            approvals = sum(1 for v in validation_scores if v.approved)
            avg_score = sum(v.score for v in validation_scores) / len(validation_scores) if validation_scores else 0
            approved = approvals >= 2
            
            logger.info(f"Post {post_number}: After revision - {approvals}/3 approvals")
        
        # Set final approval status
        post.approved = approved
        post.validation_score = avg_score
        
        if approved:
            logger.info(f"Post {post_number}: APPROVED with score {avg_score:.1f}")
            
            # Add to queue if available
            if self.queue_manager:
                try:
                    await self.queue_manager.add_post(post)
                except Exception as e:
                    logger.error(f"Failed to add post to queue: {e}")
        else:
            logger.warning(f"Post {post_number}: REJECTED with score {avg_score:.1f}")
        
        return post
    
    async def _validate_post(self, post: LinkedInPost) -> List[ValidationScore]:
        """Run all validators in parallel"""
        
        tasks = [validator.execute(post) for validator in self.validators]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        scores = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Validator {self.validators[i].name} failed: {result}")
                # Create a failing score for the error
                scores.append(ValidationScore(
                    agent_name=self.validators[i].name,
                    score=0,
                    approved=False,
                    feedback=f"Validation error: {result}",
                    criteria_breakdown={"error": True}
                ))
            else:
                scores.append(result)
        
        return scores
    
    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics"""
        
        return {
            "content_generator": self.content_generator.get_stats(),
            "validators": [v.name for v in self.validators],
            "trend_service_active": self.trend_service is not None,
            "recent_topics_tracked": len(self.recent_topics),
            "recent_headlines_tracked": len(self.recent_headlines)
        }