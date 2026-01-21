"""
Content Orchestrator V3 - GUARANTEED UNIQUE TRENDS + STYLE VALIDATION
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

# Import style validator
try:
    from ..agents.style_validator import StyleValidator
    STYLE_VALIDATOR_AVAILABLE = True
except ImportError:
    STYLE_VALIDATOR_AVAILABLE = False

try:
    from ..infrastructure.trend_service import get_trend_service, TrendService
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
    Master orchestrator with:
    - GUARANTEED unique trends per post (via trend service tracking)
    - Style validator to enforce Liquid Death energy
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
        
        # Validators - StyleValidator FIRST to catch bad content early
        self.validators = []
        
        if STYLE_VALIDATOR_AVAILABLE:
            self.validators.append(StyleValidator(ai_client, config))
            logger.info("✅ StyleValidator added - will enforce Liquid Death energy")
        else:
            logger.warning("⚠️ StyleValidator not available - style may vary")
        
        self.validators.extend([
            SarahChenValidator(ai_client, config),
            MarcusWilliamsValidator(ai_client, config),
            JordanParkValidator(ai_client, config)
        ])
        
        # Trend service
        self.trend_service = None
        if TREND_SERVICE_AVAILABLE:
            self.trend_service = get_trend_service()
            logger.info("✅ Trend service initialized")
        
        # Tracking
        self.recent_topics = []
        
        if self.image_generator:
            logger.info("✅ ContentOrchestrator initialized WITH image generator")
        
        logger.info(f"ContentOrchestrator ready with {len(self.validators)} validators")
    
    async def generate_batch(
        self, 
        num_posts: int = 1, 
        use_video: bool = False,
        force_trend_refresh: bool = False
    ) -> BatchResult:
        """Generate a batch - each post gets a UNIQUE trend"""
        
        batch_id = str(uuid.uuid4())
        media_type = "video" if use_video else "image"
        
        logger.info(f"═══════════════════════════════════════════════════════════════")
        logger.info(f"Starting batch {batch_id[:8]} with {num_posts} posts")
        logger.info(f"═══════════════════════════════════════════════════════════════")
        
        # Reset trend tracking for this batch
        if self.trend_service:
            self.trend_service.start_new_batch(batch_id)
        
        approved_posts = []
        
        for i in range(num_posts):
            post_number = i + 1
            logger.info(f"\n--- Processing post {post_number}/{num_posts} ---")
            
            # Get a UNIQUE trend for this post
            trend = None
            trend_context = None
            
            if self.trend_service:
                trend = await self.trend_service.get_next_unused_trend()
                if trend:
                    trend_context = self.trend_service.format_single_trend(trend)
                    logger.info(f"Post {post_number} trend: {trend.headline[:60]}...")
                else:
                    logger.info(f"Post {post_number}: No unused trends - will generate original content")
            
            try:
                post = await self._process_single_post(
                    post_number=post_number,
                    batch_id=batch_id,
                    trend_context=trend_context,
                    assigned_trend=trend,
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
        
        logger.info(f"\n═══════════════════════════════════════════════════════════════")
        logger.info(f"Batch {batch_id[:8]} complete: {len(approved_posts)}/{num_posts} approved")
        logger.info(f"═══════════════════════════════════════════════════════════════")
        
        return BatchResult(batch_id=batch_id, posts=approved_posts, media_type=media_type)
    
    async def _process_single_post(
        self,
        post_number: int,
        batch_id: str,
        trend_context: Optional[str] = None,
        assigned_trend = None,
        use_video: bool = False
    ) -> Optional[LinkedInPost]:
        """Process a single post"""
        
        avoid_patterns = {
            "recent_topics": self.recent_topics[-10:]
        }
        
        # Step 1: Generate content
        post = await self.content_generator.execute(
            post_number=post_number,
            batch_id=batch_id,
            trending_context=trend_context,
            avoid_patterns=avoid_patterns
        )
        
        # Track topic
        if post.cultural_reference:
            self.recent_topics.append(post.cultural_reference.reference)
            self.recent_topics = self.recent_topics[-20:]
        
        # Step 2: Generate image/video
        if self.image_generator:
            try:
                media_result = await self.image_generator.execute(post, use_video=use_video)
                
                if media_result.get("success"):
                    saved_path = media_result.get("saved_path") or media_result.get("path")
                    
                    if use_video or media_result.get("media_type") == "video":
                        web_url = convert_to_web_url(saved_path, "video")
                        post.image_url = web_url
                        post.video_url = web_url
                        post.media_type = "video"
                    else:
                        web_url = convert_to_web_url(saved_path, "image")
                        post.image_url = web_url
                        post.media_type = "image"
                    
                    logger.info(f"✅ Media: {web_url}")
            except Exception as e:
                logger.warning(f"Media generation failed: {e}")
        
        # Step 3: Validate with ALL validators (including StyleValidator)
        validation_scores = await self._validate_post(post)
        
        # Step 4: Check results
        approvals = sum(1 for v in validation_scores if v.approved)
        avg_score = sum(v.score for v in validation_scores) / len(validation_scores) if validation_scores else 0
        
        # Log each validator's result
        for v in validation_scores:
            status = "✅" if v.approved else "❌"
            logger.info(f"  {status} {v.agent_name}: {v.score}/10 - {v.feedback[:50] if v.feedback else 'No feedback'}...")
        
        logger.info(f"Post {post_number}: {approvals}/{len(self.validators)} approvals, avg: {avg_score:.1f}")
        
        # Need majority approval
        min_approvals = len(self.validators) // 2 + 1
        approved = approvals >= min_approvals
        
        # Step 5: Revise if close but not approved
        if not approved and approvals >= min_approvals - 1:
            logger.info(f"Post {post_number}: Attempting revision...")
            
            aggregated = await self.feedback_aggregator.execute(post, validation_scores)
            post = await self.revision_generator.execute(post, aggregated)
            
            validation_scores = await self._validate_post(post)
            approvals = sum(1 for v in validation_scores if v.approved)
            avg_score = sum(v.score for v in validation_scores) / len(validation_scores) if validation_scores else 0
            approved = approvals >= min_approvals
            
            logger.info(f"Post {post_number} after revision: {approvals}/{len(self.validators)} approvals")
        
        if approved:
            post.validation_scores = validation_scores
            return post
        
        return None
    
    async def _validate_post(self, post: LinkedInPost) -> List[ValidationScore]:
        """Run all validators in parallel"""
        tasks = [validator.execute(post) for validator in self.validators]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        scores = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Validator {self.validators[i].name} error: {result}")
                scores.append(ValidationScore(
                    agent_name=self.validators[i].name,
                    score=5.0,
                    approved=False,
                    feedback=f"Error: {result}",
                    criteria_breakdown={"error": True}
                ))
            else:
                scores.append(result)
        
        return scores
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "validators": [v.name for v in self.validators],
            "validator_count": len(self.validators),
            "trend_service_active": self.trend_service is not None,
            "image_generator_active": self.image_generator is not None,
            "style_validator_active": STYLE_VALIDATOR_AVAILABLE
        }