"""
Content Orchestrator - SIMPLIFIED
- One fresh trend fetched per post
- No trend storage/caching
- Clean separation of concerns
- Memory integration for learning and avoiding repetition
"""

import asyncio
import logging
import uuid
from typing import Dict, Any, List, Optional

from ..models.post import LinkedInPost, ValidationScore
from ..agents.content_strategist import ContentGeneratorAgent
from ..agents.feedback_aggregator import FeedbackAggregatorAgent
from ..agents.revision_generator import RevisionGeneratorAgent
from ..agents.validators import SarahChenValidator, MarcusWilliamsValidator, JordanParkValidator

try:
    from ..infrastructure.trend_service import get_trend_service
    TREND_SERVICE_AVAILABLE = True
except ImportError:
    TREND_SERVICE_AVAILABLE = False

try:
    from ..infrastructure.memory import get_memory
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    get_memory = None

logger = logging.getLogger(__name__)


def convert_to_web_url(file_path: str, media_type: str = "image") -> str:
    """Convert local file path to web-accessible URL"""
    if not file_path:
        return None
    if file_path.startswith('/images') or file_path.startswith('/videos'):
        return file_path
    if file_path.startswith('http'):
        return file_path
    
    filename = file_path.split('/')[-1]
    if media_type == "video" or filename.endswith('.mp4'):
        return f"/videos/{filename}"
    return f"/images/{filename}"


class BatchResult:
    def __init__(self, batch_id: str, posts: List[LinkedInPost], media_type: str = "image"):
        self.batch_id = batch_id
        self.id = batch_id
        self.posts = posts
        self.media_type = media_type
        self.approved_posts = posts
        self.rejected_posts = []
    
    def get_approved_posts(self):
        return self.approved_posts
    
    def get_rejected_posts(self):
        return self.rejected_posts


class ContentOrchestrator:
    """
    Orchestrates content generation.
    
    KEY CHANGE: Each post gets ONE fresh trend fetched at generation time.
    No caching, no storage, no duplicates.
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
            # Use same database as queue manager for consistency
            self.trend_service = get_trend_service("data/automation/queue.db")
            logger.info("✅ Trend service initialized - content will react to real news")

        # Initialize memory system
        self.memory = None
        if MEMORY_AVAILABLE:
            try:
                self.memory = get_memory("data/automation/queue.db")
                logger.info("✅ Memory system initialized - agents will learn from past content")
            except Exception as e:
                logger.warning(f"Memory system unavailable: {e}")

        if self.image_generator:
            logger.info("✅ ContentOrchestrator initialized WITH image generator")
        else:
            logger.warning("⚠️ ContentOrchestrator initialized WITHOUT image generator")
    
    async def generate_batch(self, num_posts: int = 1, use_video: bool = False) -> BatchResult:
        """Generate a batch of posts, each with a unique fresh trend."""

        batch_id = str(uuid.uuid4())
        logger.info(f"Starting batch {batch_id[:8]} with {num_posts} posts")

        # Start memory session for this batch
        if self.memory:
            self.memory.start_session(batch_id)
            logger.info("📝 Memory session started")

        # Reset trend tracking for this batch
        if self.trend_service:
            self.trend_service.reset_for_new_batch()

        approved_posts = []
        rejected_count = 0

        for i in range(num_posts):
            post_number = i + 1
            post_id = f"{batch_id[:8]}_{post_number}"  # Create tracking ID
            logger.info(f"\n--- Post {post_number}/{num_posts} ---")

            # Fetch ONE fresh trend for THIS post (with tracking)
            trend = None
            if self.trend_service:
                trend = await self.trend_service.get_one_fresh_trend(post_id=post_id)
                if trend:
                    logger.info(f"📰 Trend ({trend.category}): {trend.headline[:70]}...")

            try:
                post, validation_scores, was_approved = await self._process_single_post_with_memory(
                    post_number=post_number,
                    batch_id=batch_id,
                    trend=trend,
                    use_video=use_video
                )

                if was_approved and post:
                    approved_posts.append(post)
                    logger.info(f"✅ Post {post_number} APPROVED")
                else:
                    rejected_count += 1
                    logger.warning(f"❌ Post {post_number} REJECTED")

            except Exception as e:
                logger.error(f"Post {post_number} failed: {e}")
                import traceback
                traceback.print_exc()
                rejected_count += 1

        # End memory session
        if self.memory:
            self.memory.end_session()
            logger.info(f"📝 Memory session ended: {len(approved_posts)} approved, {rejected_count} rejected")

        logger.info(f"\nBatch complete: {len(approved_posts)}/{num_posts} approved")
        return BatchResult(batch_id=batch_id, posts=approved_posts)
    
    async def _process_single_post_with_memory(
        self,
        post_number: int,
        batch_id: str,
        trend=None,
        use_video: bool = False
    ) -> tuple:
        """
        Process a single post and store results in memory.

        Returns:
            tuple: (post, validation_scores, was_approved)
        """
        post = await self._process_single_post(
            post_number=post_number,
            batch_id=batch_id,
            trend=trend,
            use_video=use_video
        )

        was_approved = post is not None
        validation_scores = post.validation_scores if post else []

        # Store in memory
        if self.memory:
            try:
                # Extract metadata for memory
                post_id = f"{batch_id[:8]}_{post_number}"
                content = post.content if post else ""
                pillar = getattr(post, 'cultural_reference', None)
                pillar_name = pillar.category if pillar else None

                # Calculate average score
                avg_score = 0
                if validation_scores:
                    avg_score = sum(v.score for v in validation_scores) / len(validation_scores)

                # Convert validation scores to dicts for storage
                scores_as_dicts = []
                for vs in validation_scores:
                    scores_as_dicts.append({
                        'agent_name': vs.agent_name,
                        'score': vs.score,
                        'approved': vs.approved,
                        'feedback': vs.feedback,
                        'strengths': getattr(vs, 'strengths', []),
                        'weaknesses': getattr(vs, 'weaknesses', [])
                    })

                self.memory.remember_post(
                    post_id=post_id,
                    batch_id=batch_id,
                    content=content,
                    pillar=pillar_name,
                    trending_topic=trend.headline if trend else None,
                    was_approved=was_approved,
                    average_score=avg_score,
                    validation_scores=scores_as_dicts
                )
                logger.debug(f"📝 Stored post {post_id} in memory (approved={was_approved})")

            except Exception as e:
                logger.warning(f"Failed to store post in memory: {e}")

        return post, validation_scores, was_approved

    async def _process_single_post(
        self,
        post_number: int,
        batch_id: str,
        trend=None,
        use_video: bool = False
    ) -> Optional[LinkedInPost]:
        """Process a single post with its assigned trend."""
        
        # Format trend for content generator with rich context
        trend_context = None
        if trend:
            parts = [
                f"HEADLINE: {trend.headline}",
                f"CATEGORY: {trend.category.upper()}",
            ]

            # Use description (rich) or summary (basic)
            description = getattr(trend, 'description', '') or ''
            if description:
                parts.append(f"DETAILS: {description[:300]}")
            elif trend.summary:
                parts.append(f"SUMMARY: {trend.summary}")

            if trend.url and trend.source != "fallback":
                parts.append(f"SOURCE: {trend.url}")

            # Include related articles for additional context
            related = getattr(trend, 'related_articles', []) or []
            if related:
                parts.append("\nRELATED CONTEXT:")
                for i, article in enumerate(related[:3], 1):
                    if article.get("title"):
                        parts.append(f"  {i}. {article['title']}")
                        if article.get("snippet"):
                            parts.append(f"     {article['snippet']}")

            jesse_angle = getattr(trend, 'jesse_angle', '') or ''
            if jesse_angle:
                parts.append(f"\nSUGGESTED ANGLE: {jesse_angle}")

            trend_body = "\n".join(parts)

            trend_context = f"""
TODAY'S TRENDING NEWS ({trend.category.upper()}) — React to this:

{trend_body}

IMPORTANT: Write about the SPECIFIC news above. Reference the actual headline, details, or cultural moment. Don't create generic content.
"""
        
        # Generate content
        post = await self.content_generator.execute(
            post_number=post_number,
            batch_id=batch_id,
            trending_context=trend_context,
        )
        
        # Generate media
        if self.image_generator:
            try:
                media_result = await self.image_generator.execute(post, use_video=use_video)
                
                if media_result.get("success"):
                    saved_path = media_result.get("saved_path") or media_result.get("path")
                    web_url = convert_to_web_url(saved_path, "video" if use_video else "image")
                    post.image_url = web_url
                    if use_video:
                        post.video_url = web_url
                        post.media_type = "video"
                    else:
                        post.media_type = "image"
                    logger.info(f"✅ Media: {web_url}")
            except Exception as e:
                logger.warning(f"Media generation failed: {e}")
        
        # Validate
        validation_scores = await self._validate_post(post)
        approvals = sum(1 for v in validation_scores if v.approved)
        avg_score = sum(v.score for v in validation_scores) / len(validation_scores) if validation_scores else 0
        
        logger.info(f"Validation: {approvals}/3 approvals, avg: {avg_score:.1f}")
        
        approved = approvals >= 2
        
        # Revise if needed
        if not approved and approvals >= 1:
            logger.info("Attempting revision...")
            aggregated = await self.feedback_aggregator.execute(post, validation_scores)
            post = await self.revision_generator.execute(post, aggregated)
            
            validation_scores = await self._validate_post(post)
            approvals = sum(1 for v in validation_scores if v.approved)
            approved = approvals >= 2
        
        if approved:
            post.validation_scores = validation_scores
            return post
        
        return None
    
    async def _validate_post(self, post: LinkedInPost) -> List[ValidationScore]:
        """Run all validators."""
        tasks = [v.execute(post) for v in self.validators]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        scores = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                scores.append(ValidationScore(
                    agent_name=self.validators[i].name,
                    score=5.0,
                    approved=False,
                    feedback=f"Error: {result}"
                ))
            else:
                scores.append(result)
        
        return scores
    
    async def generate_and_post_now(self, linkedin_poster, use_video: bool = False) -> Dict[str, Any]:
        """
        Generate fresh content and post immediately to LinkedIn.
        
        This is the RECOMMENDED method for automated posting because:
        - Always uses fresh trending topics (not stale queued content)
        - Generates and posts in one step
        - No queue management needed
        
        Args:
            linkedin_poster: LinkedInPoster instance
            use_video: Whether to generate video instead of image
            
        Returns:
            Dict with success status, post details, and LinkedIn result
        """
        import uuid
        from datetime import datetime
        
        logger.info("=" * 60)
        logger.info("🚀 GENERATE AND POST NOW - Fresh content pipeline")
        logger.info("=" * 60)
        
        try:
            # Start memory session for this live post
            if self.memory:
                self.memory.start_session(f"live_{uuid.uuid4().hex[:8]}")

            # Step 1: Reset trend tracking for fresh selection
            if self.trend_service:
                self.trend_service.reset_for_new_batch()

            # Step 2: Get fresh trending topic
            post_id = f"live_{uuid.uuid4().hex[:8]}"
            trend = None
            if self.trend_service:
                trend = await self.trend_service.get_one_fresh_trend(post_id=post_id)
                if trend:
                    logger.info(f"📰 Fresh trend ({trend.category}): {trend.headline[:70]}...")
                else:
                    logger.warning("⚠️ No fresh trend available, generating without trend")

            # Step 3: Generate content (with memory)
            logger.info("✍️ Generating content...")
            post, validation_scores, was_approved = await self._process_single_post_with_memory(
                post_number=1,
                batch_id=post_id,
                trend=trend,
                use_video=use_video
            )

            if not was_approved or not post:
                logger.error("❌ Content generation failed validation")
                if self.memory:
                    self.memory.end_session()
                return {
                    "success": False,
                    "error": "Content failed validation - no post generated",
                    "stage": "generation"
                }

            logger.info(f"✅ Content generated: {post.content[:50]}...")

            # Step 4: Post to LinkedIn
            logger.info("📤 Posting to LinkedIn...")
            linkedin_result = linkedin_poster.publish_post(
                content=post.content,
                image_path=post.image_url,
                hashtags=[]  # No hashtags per client request
            )

            if linkedin_result.get("success"):
                logger.info(f"✅ Posted successfully: {linkedin_result.get('post_id')}")

                # Mark trend as used (permanently) after successful post
                if self.trend_service and trend:
                    self.trend_service.mark_topic_used_permanent(trend, post_id=post_id)

                # Mark post as published in memory
                if self.memory:
                    self.memory.mark_posted_to_linkedin(
                        f"{post_id[:8]}_1",
                        linkedin_result.get('post_id', '')
                    )
                    self.memory.end_session()

                return {
                    "success": True,
                    "post": post.to_dict(),
                    "linkedin": linkedin_result,
                    "trend_used": {
                        "headline": trend.headline if trend else None,
                        "category": trend.category if trend else None
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                logger.error(f"❌ LinkedIn post failed: {linkedin_result.get('error')}")
                if self.memory:
                    self.memory.end_session()
                return {
                    "success": False,
                    "error": linkedin_result.get("error"),
                    "details": linkedin_result.get("details"),
                    "stage": "linkedin_post",
                    "post": post.to_dict()  # Include post so it can be manually posted
                }

        except Exception as e:
            logger.error(f"❌ Generate and post failed: {e}")
            import traceback
            traceback.print_exc()
            if self.memory:
                self.memory.end_session()
            return {
                "success": False,
                "error": str(e),
                "stage": "exception"
            }
    
    def get_stats(self):
        stats = {
            "validators": [v.name for v in self.validators],
            "trend_service": self.trend_service is not None,
            "image_generator": self.image_generator is not None,
            "memory": self.memory is not None
        }

        # Add memory stats if available
        if self.memory:
            try:
                stats["memory_stats"] = self.memory.get_stats()
            except Exception:
                pass

        return stats