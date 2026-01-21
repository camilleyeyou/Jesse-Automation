"""
Content Orchestrator - The Master Controller for Jesse A. Eisenbalm
Coordinates all agents: Trend Scout → Content Generator → Validators → Queue

NOW WITH: Real-time trend integration for reactive, non-clichéd content

FIXED: 
- Use correct Pydantic field names (image_url, not image_path)
- Return BatchResult compatible with main.py
- Convert file paths to web-accessible URLs
- Deduplicate trends within a batch
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Set

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


def convert_to_web_url(file_path: str, media_type: str = "image") -> str:
    """
    Convert a local file path to a web-accessible URL
    
    data/images/filename.png -> /images/filename.png
    data/images/videos/filename.mp4 -> /videos/filename.mp4
    """
    if not file_path:
        return None
    
    # Already a web URL
    if file_path.startswith('/images') or file_path.startswith('/videos'):
        return file_path
    if file_path.startswith('http://') or file_path.startswith('https://'):
        return file_path
    
    # Extract filename from path
    filename = file_path.split('/')[-1]
    
    # Determine URL based on media type or path
    if media_type == "video" or '/videos/' in file_path or filename.endswith('.mp4'):
        return f"/videos/{filename}"
    else:
        return f"/images/{filename}"


class BatchResult:
    """Result object for batch generation - compatible with main.py expectations"""
    
    def __init__(self, batch_id: str, posts: List[LinkedInPost], media_type: str = "image"):
        self.batch_id = batch_id
        self.id = batch_id  # Alias for compatibility
        self.posts = posts
        self.media_type = media_type
        self.approved_posts = [p for p in posts]  # All posts in list are approved
        self.rejected_posts = []
    
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
            "id": self.batch_id,
            "approved": len(self.approved_posts),
            "rejected": len(self.rejected_posts),
            "media_type": self.media_type,
            "posts": self.posts
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
        
        # Log image generator status
        if self.image_generator:
            logger.info("✅ ContentOrchestrator initialized WITH image generator")
        else:
            logger.warning("⚠️ ContentOrchestrator initialized WITHOUT image generator - images will not be generated")
        
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
        logger.info(f"Image generator available: {self.image_generator is not None}")
        
        # Step 1: Fetch trending news for reactive content
        trending_news = []
        trending_context = None
        if self.trend_service:
            try:
                trending_news = await self.trend_service.get_trending_news(force_refresh=force_trend_refresh)
                trending_context = self.trend_service.format_for_content_generator(trending_news)
                
                # Track headlines to avoid repetition
                for item in trending_news:
                    if item.headline not in self.recent_headlines:
                        self.recent_headlines.append(item.headline)
                
                # Keep only last 20 headlines
                self.recent_headlines = self.recent_headlines[-20:]
                
                logger.info(f"Fetched {len(trending_news)} trending news items for content generation")
            except Exception as e:
                logger.warning(f"Failed to fetch trends: {e}")
        
        # Step 2: Generate posts with trend deduplication
        approved_posts = []
        used_trend_indices: Set[int] = set()  # Track which trends have been used in this batch
        
        for i in range(num_posts):
            post_number = i + 1
            logger.info(f"Processing post {post_number} (media: {media_type})")
            
            try:
                # Create filtered trending context excluding already-used trends
                filtered_context = self._filter_trending_context(
                    trending_news, 
                    trending_context, 
                    used_trend_indices
                )
                
                post, used_index = await self._process_single_post(
                    post_number=post_number,
                    batch_id=batch_id,
                    trending_context=filtered_context,
                    trending_news=trending_news,
                    use_video=use_video
                )
                
                if post:
                    approved_posts.append(post)
                    # Track which trend was used
                    if used_index is not None:
                        used_trend_indices.add(used_index)
                        logger.info(f"Post {post_number} used trend index {used_index}")
                    
            except Exception as e:
                logger.error(f"Post {post_number} failed: {e}")
                import traceback
                traceback.print_exc()
        
        logger.info(f"Batch {batch_id} completed: {len(approved_posts)}/{num_posts} approved")
        
        return BatchResult(batch_id=batch_id, posts=approved_posts, media_type=media_type)
    
    def _filter_trending_context(
        self, 
        trending_news: List, 
        full_context: Optional[str],
        used_indices: Set[int]
    ) -> Optional[str]:
        """Filter out already-used trends from the context"""
        
        if not trending_news or not full_context:
            return full_context
        
        if not used_indices:
            return full_context
        
        # Filter out used trends
        available_news = [
            (i, item) for i, item in enumerate(trending_news) 
            if i not in used_indices
        ]
        
        if not available_news:
            logger.warning("All trends used in batch - content will be original")
            return None
        
        # Rebuild context with only available trends
        if self.trend_service:
            available_items = [item for _, item in available_news]
            return self.trend_service.format_for_content_generator(available_items)
        
        return full_context
    
    async def _process_single_post(
        self,
        post_number: int,
        batch_id: str,
        trending_context: Optional[str] = None,
        trending_news: List = None,
        use_video: bool = False
    ) -> Tuple[Optional[LinkedInPost], Optional[int]]:
        """
        Process a single post through the full pipeline
        
        Returns: (post, used_trend_index) - the post and which trend index was used (if any)
        """
        
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
        
        # Try to identify which trend was used (for deduplication)
        used_trend_index = self._identify_used_trend(post, trending_news)
        
        # Track this topic
        if post.cultural_reference:
            self.recent_topics.append(post.cultural_reference.reference)
        self.recent_topics = self.recent_topics[-20:]  # Keep last 20
        
        # Step 2: Generate image/video
        if self.image_generator:
            try:
                logger.info(f"Generating {'video' if use_video else 'image'} for post {post_number}...")
                media_result = await self.image_generator.execute(post, use_video=use_video)
                
                if media_result.get("success"):
                    # Get the saved path and convert to web URL
                    saved_path = media_result.get("saved_path") or media_result.get("path") or media_result.get("url")
                    
                    if use_video or media_result.get("media_type") == "video":
                        web_url = convert_to_web_url(saved_path, "video")
                        post.image_url = web_url  # Store in image_url field (frontend checks this)
                        post.video_url = web_url
                        post.media_type = "video"
                        logger.info(f"✅ Video generated: {saved_path} -> {web_url}")
                    else:
                        web_url = convert_to_web_url(saved_path, "image")
                        post.image_url = web_url
                        post.media_type = "image"
                        logger.info(f"✅ Image generated: {saved_path} -> {web_url}")
                else:
                    logger.warning(f"Post {post_number}: Media generation failed - {media_result.get('error')}")
            except Exception as e:
                logger.warning(f"Post {post_number}: Media generation failed - {e}")
                import traceback
                traceback.print_exc()
        else:
            logger.warning(f"Post {post_number}: No image generator available - skipping media generation")
        
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
        
        if approved:
            logger.info(f"Post {post_number}: APPROVED with score {avg_score:.1f}")
            
            # Store validation score for queue display
            post.average_score = avg_score
            
            # Add to queue if available
            if self.queue_manager:
                try:
                    await self.queue_manager.add_post(post)
                except Exception as e:
                    logger.error(f"Failed to add post to queue: {e}")
            
            return post, used_trend_index
        else:
            logger.warning(f"Post {post_number}: REJECTED with score {avg_score:.1f}")
            return None, used_trend_index
    
    def _identify_used_trend(self, post: LinkedInPost, trending_news: List) -> Optional[int]:
        """Try to identify which trend was used in the post content"""
        
        if not trending_news or not post.content:
            return None
        
        content_lower = post.content.lower()
        
        for i, news_item in enumerate(trending_news):
            # Check if key words from the headline appear in content
            headline_words = set(news_item.headline.lower().split())
            # Remove common words
            headline_words -= {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'to', 'for', 'of', 'and', 'in', 'on'}
            
            # If 2+ significant words from headline appear in content, likely this trend
            matches = sum(1 for word in headline_words if len(word) > 3 and word in content_lower)
            if matches >= 2:
                return i
        
        return None
    
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
            "image_generator_active": self.image_generator is not None,
            "recent_topics_tracked": len(self.recent_topics),
            "recent_headlines_tracked": len(self.recent_headlines)
        }