"""
Content Orchestrator - The Master Controller for Jesse A. Eisenbalm
FIXED: Proper trend deduplication - each post MUST use a different trend
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

try:
    from ..infrastructure.trend_service import get_trend_service, TrendService, TrendingNews
    TREND_SERVICE_AVAILABLE = True
except ImportError:
    TREND_SERVICE_AVAILABLE = False
    TrendingNews = None

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
    Master orchestrator - NOW WITH PROPER TREND DEDUPLICATION
    Each post in a batch MUST use a different trend.
    """
    
    def __init__(self, ai_client, config, image_generator=None, queue_manager=None):
        self.ai_client = ai_client
        self.config = config
        self.image_generator = image_generator
        self.queue_manager = queue_manager
        
        self.content_generator = ContentGeneratorAgent(ai_client, config)
        self.feedback_aggregator = FeedbackAggregatorAgent(ai_client, config)
        self.revision_generator = RevisionGeneratorAgent(ai_client, config)
        
        self.validators = [
            SarahChenValidator(ai_client, config),
            MarcusWilliamsValidator(ai_client, config),
            JordanParkValidator(ai_client, config)
        ]
        
        self.trend_service = None
        if TREND_SERVICE_AVAILABLE:
            self.trend_service = get_trend_service()
            logger.info("✅ Trend service initialized")
        
        self.recent_topics = []
        self.recent_headlines = []
        
        if self.image_generator:
            logger.info("✅ ContentOrchestrator initialized WITH image generator")
        else:
            logger.warning("⚠️ ContentOrchestrator initialized WITHOUT image generator")
        
        logger.info("ContentOrchestrator initialized with STRICT trend deduplication")
    
    async def generate_batch(
        self, 
        num_posts: int = 1, 
        use_video: bool = False,
        force_trend_refresh: bool = False
    ) -> BatchResult:
        """Generate a batch - each post uses a DIFFERENT trend"""
        
        batch_id = str(uuid.uuid4())
        media_type = "video" if use_video else "image"
        
        logger.info(f"Starting batch {batch_id} with {num_posts} posts (media: {media_type})")
        
        # Step 1: Fetch ALL trending news
        all_trends: List = []
        if self.trend_service:
            try:
                all_trends = await self.trend_service.get_trending_news(force_refresh=force_trend_refresh)
                logger.info(f"Fetched {len(all_trends)} trending news items")
            except Exception as e:
                logger.warning(f"Failed to fetch trends: {e}")
        
        # Step 2: Ensure we have enough unique trends
        if len(all_trends) < num_posts:
            logger.warning(f"Only {len(all_trends)} trends for {num_posts} posts - some may be original content")
        
        # Step 3: Generate posts - EACH GETS A UNIQUE TREND
        approved_posts = []
        used_trend_indices: Set[int] = set()
        
        for i in range(num_posts):
            post_number = i + 1
            logger.info(f"Processing post {post_number}/{num_posts} (media: {media_type})")
            
            # Get the next available trend for THIS post only
            single_trend = None
            single_trend_context = None
            trend_index = None
            
            for idx, trend in enumerate(all_trends):
                if idx not in used_trend_indices:
                    single_trend = trend
                    trend_index = idx
                    # Format JUST THIS ONE TREND for the content generator
                    single_trend_context = self._format_single_trend(trend, idx + 1)
                    break
            
            if single_trend:
                logger.info(f"Post {post_number} assigned trend {trend_index}: {single_trend.headline[:50]}...")
                used_trend_indices.add(trend_index)
            else:
                logger.info(f"Post {post_number} will generate original content (no unused trends)")
            
            try:
                post = await self._process_single_post(
                    post_number=post_number,
                    batch_id=batch_id,
                    trending_context=single_trend_context,  # Only ONE trend passed
                    assigned_trend=single_trend,
                    use_video=use_video
                )
                
                if post:
                    approved_posts.append(post)
                    
            except Exception as e:
                logger.error(f"Post {post_number} failed: {e}")
                import traceback
                traceback.print_exc()
        
        logger.info(f"Batch {batch_id} completed: {len(approved_posts)}/{num_posts} approved")
        return BatchResult(batch_id=batch_id, posts=approved_posts, media_type=media_type)
    
    def _format_single_trend(self, trend, trend_number: int) -> str:
        """Format a SINGLE trend for the content generator - no choices, just this one"""
        
        category_emoji = {
            "tech_industry": "💼",
            "ai_news": "🤖",
            "workplace_viral": "📱",
            "startup_news": "🚀",
            "workplace_culture": "🏢",
            "tech_news": "💻",
            "viral_social": "🔥",
            "entertainment": "🎬",
            "sports": "⚽",
            "finance": "📈",
            "general_news": "📰",
        }.get(trend.category, "📰")
        
        return f"""═══════════════════════════════════════════════════════════════════════════════
🎯 YOUR ASSIGNED TREND - YOU MUST REACT TO THIS ONE
═══════════════════════════════════════════════════════════════════════════════

{category_emoji} {trend.headline}
Category: {trend.category}
Source: {trend.source}
{f"Summary: {trend.summary[:200]}..." if trend.summary else ""}

💡 Angle hint: {trend.jesse_angle}

═══════════════════════════════════════════════════════════════════════════════
INSTRUCTIONS:
- React to THIS specific trend above
- Use the actual names, numbers, and details from the headline
- Be specific - don't make it generic
- This is YOUR assigned trend - the other posts have different ones
═══════════════════════════════════════════════════════════════════════════════"""
    
    async def _process_single_post(
        self,
        post_number: int,
        batch_id: str,
        trending_context: Optional[str] = None,
        assigned_trend = None,
        use_video: bool = False
    ) -> Optional[LinkedInPost]:
        """Process a single post with its assigned trend"""
        
        avoid_patterns = {
            "recent_topics": self.recent_topics[-10:],
            "recent_headlines": self.recent_headlines[-5:]
        }
        
        # Step 1: Generate content with the ASSIGNED trend
        post = await self.content_generator.execute(
            post_number=post_number,
            batch_id=batch_id,
            trending_context=trending_context,
            avoid_patterns=avoid_patterns
        )
        
        # Track what was used
        if assigned_trend:
            self.recent_headlines.append(assigned_trend.headline)
            self.recent_headlines = self.recent_headlines[-20:]
        
        if post.cultural_reference:
            self.recent_topics.append(post.cultural_reference.reference)
            self.recent_topics = self.recent_topics[-20:]
        
        # Step 2: Generate image/video
        if self.image_generator:
            try:
                logger.info(f"Generating {'video' if use_video else 'image'} for post {post_number}...")
                media_result = await self.image_generator.execute(post, use_video=use_video)
                
                if media_result.get("success"):
                    saved_path = media_result.get("saved_path") or media_result.get("path") or media_result.get("url")
                    
                    if use_video or media_result.get("media_type") == "video":
                        web_url = convert_to_web_url(saved_path, "video")
                        post.image_url = web_url
                        post.video_url = web_url
                        post.media_type = "video"
                    else:
                        web_url = convert_to_web_url(saved_path, "image")
                        post.image_url = web_url
                        post.media_type = "image"
                    
                    logger.info(f"✅ Media generated: {saved_path} -> {web_url}")
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
        
        logger.info(f"Post {post_number}: {approvals}/3 approvals, avg score: {avg_score:.1f}")
        
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
                    score=0,
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
            "image_generator_active": self.image_generator is not None,
            "recent_topics_tracked": len(self.recent_topics),
            "recent_headlines_tracked": len(self.recent_headlines)
        }