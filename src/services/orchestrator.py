"""
Content Orchestrator - The Master Controller for Jesse A. Eisenbalm
Coordinates all agents: Trend Scout → Content Generator → Validators → Queue

NOW WITH: Real-time trend integration for reactive, non-clichéd content
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


class ContentOrchestrator:
    """
    Master orchestrator for Jesse A. Eisenbalm content generation
    
    Flow:
    1. Fetch trending news (NEW!)
    2. Generate content reacting to trends
    3. Validate with Sarah, Marcus, Jordan
    4. Revise if needed
    5. Queue approved posts
    
    Key improvement: Content is now REACTIVE to real news, not formulaic
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
    ) -> Dict[str, Any]:
        """
        Generate a batch of posts
        
        Args:
            num_posts: Number of posts to generate
            use_video: Use video generation instead of images
            force_trend_refresh: Force refresh of trending news cache
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
        results = {
            "batch_id": batch_id,
            "requested": num_posts,
            "approved": 0,
            "rejected": 0,
            "posts": [],
            "media_type": media_type,
            "trending_topics_used": []
        }
        
        for i in range(num_posts):
            post_number = i + 1
            logger.info(f"Processing post {post_number} (media: {media_type})")
            
            try:
                post_result = await self._process_single_post(
                    post_number=post_number,
                    batch_id=batch_id,
                    trending_context=trending_context,
                    use_video=use_video
                )
                
                if post_result["approved"]:
                    results["approved"] += 1
                    if post_result.get("trend_used"):
                        results["trending_topics_used"].append(post_result["trend_used"])
                else:
                    results["rejected"] += 1
                
                results["posts"].append(post_result)
                
            except Exception as e:
                logger.error(f"Post {post_number} failed: {e}")
                results["rejected"] += 1
                results["posts"].append({
                    "post_number": post_number,
                    "approved": False,
                    "error": str(e)
                })
        
        logger.info(f"Batch {batch_id} completed: {results['approved']}/{num_posts} approved")
        
        return results
    
    async def _process_single_post(
        self,
        post_number: int,
        batch_id: str,
        trending_context: Optional[str] = None,
        use_video: bool = False
    ) -> Dict[str, Any]:
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
            except Exception as e:
                logger.warning(f"Post {post_number}: Media generation failed - {e}")
        
        # Step 3: Validate with all validators
        validation_scores = await self._validate_post(post)
        
        # Step 4: Aggregate feedback
        aggregated = await self.feedback_aggregator.execute(post, validation_scores)
        
        # Step 5: Check if approved (need 2/3 validators)
        approvals = sum(1 for v in validation_scores if v.approved)
        avg_score = sum(v.score for v in validation_scores) / len(validation_scores)
        
        logger.info(f"Post {post_number}: Validated - {approvals}/3 approvals, avg score: {avg_score:.1f}")
        
        approved = approvals >= 2
        
        # Step 6: Revise if needed (one attempt)
        if not approved and approvals >= 1:
            logger.info(f"Post {post_number}: Attempting revision")
            post = await self.revision_generator.execute(post, aggregated)
            
            # Re-validate
            validation_scores = await self._validate_post(post)
            approvals = sum(1 for v in validation_scores if v.approved)
            avg_score = sum(v.score for v in validation_scores) / len(validation_scores)
            approved = approvals >= 2
            
            logger.info(f"Post {post_number}: After revision - {approvals}/3 approvals")
        
        if approved:
            logger.info(f"Post {post_number}: APPROVED with score {avg_score:.1f}")
            
            # Add to queue if available
            if self.queue_manager:
                await self.queue_manager.add_post(post)
        else:
            logger.warning(f"Post {post_number}: REJECTED with score {avg_score:.1f}")
        
        return {
            "post_number": post_number,
            "approved": approved,
            "score": avg_score,
            "approvals": approvals,
            "content": post.content,
            "hashtags": post.hashtags,
            "image_path": post.image_path,
            "media_type": getattr(post, 'media_type', 'image'),
            "validation_breakdown": {
                v.agent_name: {"score": v.score, "approved": v.approved, "feedback": v.feedback}
                for v in validation_scores
            },
            "trend_used": post.cultural_reference.reference if post.cultural_reference else None
        }
    
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