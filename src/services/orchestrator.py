"""
Content Orchestrator - FINAL FIX
The REAL solution: Fetch all trends ONCE, then assign different trends to each post.

The problem was:
- Fetching trends fresh for each post = same top results
- Or giving all trends to AI and hoping it picks different ones = it doesn't

The fix:
- Fetch trends once at batch start
- Pop trends from the list as we assign them to posts
- Each post gets a trend that's been REMOVED from the pool
"""

import asyncio
import logging
import uuid
from typing import Dict, Any, List, Optional, Set

from ..models.post import LinkedInPost, ValidationScore
from ..agents.content_generator import ContentGeneratorAgent
from ..agents.feedback_aggregator import FeedbackAggregatorAgent
from ..agents.revision_generator import RevisionGeneratorAgent
from ..agents.validators import SarahChenValidator, MarcusWilliamsValidator, JordanParkValidator

try:
    from ..infrastructure.trend_service import get_trend_service
    TREND_SERVICE_AVAILABLE = True
except ImportError:
    TREND_SERVICE_AVAILABLE = False

logger = logging.getLogger(__name__)


def convert_to_web_url(file_path: str, media_type: str = "image") -> str:
    """Convert local file path to web-accessible URL"""
    if not file_path:
        return None
    if file_path.startswith('/images') or file_path.startswith('/videos'):
        return file_path
    if file_path.startswith('http://') or file_path.startswith('https://'):
        return file_path
    
    filename = file_path.split('/')[-1]
    if media_type == "video" or '/videos/' in file_path or filename.endswith('.mp4'):
        return f"/videos/{filename}"
    return f"/images/{filename}"


class BatchResult:
    """Result object for batch generation"""
    
    def __init__(self, batch_id: str, posts: List[LinkedInPost], media_type: str = "image"):
        self.batch_id = batch_id
        self.id = batch_id
        self.posts = posts
        self.media_type = media_type
        self.approved_posts = [p for p in posts]
        self.rejected_posts = []
    
    def get_approved_posts(self) -> List[LinkedInPost]:
        return self.approved_posts
    
    def get_rejected_posts(self) -> List[LinkedInPost]:
        return self.rejected_posts


class ContentOrchestrator:
    """
    Master orchestrator for Jesse A. Eisenbalm content generation.
    
    KEY FIX: Each post in a batch gets assigned a DIFFERENT trend by:
    1. Fetching all trends ONCE at the start of the batch
    2. Assigning trends by INDEX (post 1 gets trend 0, post 2 gets trend 1, etc.)
    3. Each trend is only used ONCE per batch
    """
    
    def __init__(self, ai_client, config, image_generator=None, queue_manager=None):
        self.ai_client = ai_client
        self.config = config
        self.image_generator = image_generator
        self.queue_manager = queue_manager
        
        # Content agents
        self.content_generator = ContentGeneratorAgent(ai_client, config)
        self.feedback_aggregator = FeedbackAggregatorAgent(ai_client, config)
        self.revision_generator = RevisionGeneratorAgent(ai_client, config)
        
        # Validators
        self.validators = [
            SarahChenValidator(ai_client, config),
            MarcusWilliamsValidator(ai_client, config),
            JordanParkValidator(ai_client, config)
        ]
        
        # Trend service
        self.trend_service = None
        if TREND_SERVICE_AVAILABLE:
            self.trend_service = get_trend_service()
            logger.info("✅ Trend service initialized - content will react to real news")
        
        if self.image_generator:
            logger.info("✅ ContentOrchestrator initialized WITH image generator")
        else:
            logger.warning("⚠️ ContentOrchestrator initialized WITHOUT image generator")
        
        logger.info("ContentOrchestrator initialized with trend-reactive generation")
    
    async def generate_batch(
        self, 
        num_posts: int = 1, 
        use_video: bool = False,
    ) -> BatchResult:
        """
        Generate a batch of posts - EACH WITH A UNIQUE TREND.
        
        The fix: Fetch trends once, then assign by index.
        """
        
        batch_id = str(uuid.uuid4())
        media_type = "video" if use_video else "image"
        
        logger.info(f"Starting batch {batch_id[:8]} with {num_posts} posts (media: {media_type})")
        
        # ========================================
        # STEP 1: FETCH ALL TRENDS ONCE
        # ========================================
        all_trends = []
        if self.trend_service:
            try:
                # Force refresh to get fresh trends
                all_trends = await self.trend_service.get_trending_news(force_refresh=True)
                logger.info(f"📰 Fetched {len(all_trends)} trends for this batch")
                
                # Log the trends we got
                for i, trend in enumerate(all_trends[:num_posts + 2]):
                    logger.info(f"  Trend {i}: {trend.headline[:60]}...")
                    
            except Exception as e:
                logger.warning(f"Failed to fetch trends: {e}")
        
        # ========================================
        # STEP 2: GENERATE POSTS - ASSIGN BY INDEX
        # ========================================
        approved_posts = []
        
        for i in range(num_posts):
            post_number = i + 1
            
            # ASSIGN TREND BY INDEX - each post gets a different one
            assigned_trend = None
            trend_context = None
            
            if i < len(all_trends):
                assigned_trend = all_trends[i]
                trend_context = self._format_single_trend(assigned_trend)
                logger.info(f"📌 Post {post_number} assigned: {assigned_trend.headline[:50]}...")
            else:
                logger.info(f"📌 Post {post_number}: No more trends, generating original content")
            
            try:
                post = await self._process_single_post(
                    post_number=post_number,
                    batch_id=batch_id,
                    trending_context=trend_context,
                    use_video=use_video
                )
                
                if post:
                    approved_posts.append(post)
                    logger.info(f"✅ Post {post_number} APPROVED")
                else:
                    logger.warning(f"❌ Post {post_number} REJECTED")
                    
            except Exception as e:
                logger.error(f"Post {post_number} failed: {e}")
                import traceback
                traceback.print_exc()
        
        logger.info(f"Batch {batch_id[:8]} completed: {len(approved_posts)}/{num_posts} approved")
        return BatchResult(batch_id=batch_id, posts=approved_posts, media_type=media_type)
    
    def _format_single_trend(self, trend) -> str:
        """Format a single trend for the content generator - THIS IS THE ONLY TREND IT SEES"""
        
        return f"""═══════════════════════════════════════════════════════════════════════════════
🎯 YOUR ASSIGNED TREND - YOU MUST USE THIS ONE
═══════════════════════════════════════════════════════════════════════════════

📰 {trend.headline}

Source: {trend.source}
Category: {trend.category}
{f"Details: {trend.summary[:200]}..." if trend.summary else ""}

💡 Jesse angle: {trend.jesse_angle if hasattr(trend, 'jesse_angle') and trend.jesse_angle else "Find the absurd corporate angle"}

═══════════════════════════════════════════════════════════════════════════════
INSTRUCTIONS:
- This is YOUR assigned trend - react to it specifically
- Use the actual names, companies, and numbers from the headline
- Do NOT make up a different topic
- The other posts in this batch have DIFFERENT trends assigned
═══════════════════════════════════════════════════════════════════════════════"""

    async def _process_single_post(
        self,
        post_number: int,
        batch_id: str,
        trending_context: Optional[str] = None,
        use_video: bool = False
    ) -> Optional[LinkedInPost]:
        """Process a single post"""
        
        # Step 1: Generate content
        logger.info(f"Processing post {post_number} (media: {'video' if use_video else 'image'})")
        
        post = await self.content_generator.execute(
            post_number=post_number,
            batch_id=batch_id,
            trending_context=trending_context,
        )
        
        # Step 2: Generate media
        if self.image_generator:
            try:
                logger.info(f"Generating {'video' if use_video else 'image'} for post {post_number}...")
                media_result = await self.image_generator.execute(post, use_video=use_video)
                
                if media_result.get("success"):
                    saved_path = media_result.get("saved_path") or media_result.get("path") or media_result.get("url")
                    
                    if use_video or media_result.get("media_type") == "video":
                        web_url = convert_to_web_url(saved_path, "video")
                        post.video_url = web_url
                        post.image_url = web_url
                        post.media_type = "video"
                    else:
                        web_url = convert_to_web_url(saved_path, "image")
                        post.image_url = web_url
                        post.media_type = "image"
                    
                    logger.info(f"✅ Image generated: {saved_path} -> {web_url}")
                else:
                    logger.warning(f"Media generation failed: {media_result.get('error')}")
            except Exception as e:
                logger.warning(f"Media generation failed: {e}")
        
        # Step 3: Validate
        validation_scores = await self._validate_post(post)
        
        # Step 4: Aggregate feedback
        aggregated = await self.feedback_aggregator.execute(post, validation_scores)
        
        # Step 5: Check approval
        approvals = sum(1 for v in validation_scores if v.approved)
        avg_score = sum(v.score for v in validation_scores) / len(validation_scores) if validation_scores else 0
        
        logger.info(f"Post {post_number}: Validated - {approvals}/3 approvals, avg score: {avg_score:.1f}")
        
        approved = approvals >= 2
        
        # Step 6: Revise if needed
        if not approved and approvals >= 1:
            logger.info(f"Post {post_number}: Attempting revision")
            post = await self.revision_generator.execute(post, aggregated)
            
            validation_scores = await self._validate_post(post)
            approvals = sum(1 for v in validation_scores if v.approved)
            avg_score = sum(v.score for v in validation_scores) / len(validation_scores) if validation_scores else 0
            approved = approvals >= 2
            
            logger.info(f"Post {post_number}: After revision - {approvals}/3 approvals")
        
        if approved:
            logger.info(f"Post {post_number}: APPROVED with score {avg_score:.1f}")
            # Store validation scores so to_dict() can compute average_score
            post.validation_scores = validation_scores
            return post
        else:
            logger.warning(f"Post {post_number}: REJECTED with score {avg_score:.1f}")
            return None
    
    async def _validate_post(self, post: LinkedInPost) -> List[ValidationScore]:
        """Run all validators in parallel"""
        tasks = [validator.execute(post) for validator in self.validators]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        scores = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Validator {self.validators[i].name} failed: {result}")
                scores.append(ValidationScore(
                    agent_name=self.validators[i].name,
                    score=5.0,
                    approved=False,
                    feedback=f"Validation error: {result}",
                    criteria_breakdown={"error": True}
                ))
            else:
                scores.append(result)
        
        return scores
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "content_generator": self.content_generator.get_stats(),
            "validators": [v.name for v in self.validators],
            "trend_service_active": self.trend_service is not None,
            "image_generator_active": self.image_generator is not None
        }