"""
Content Generation Orchestrator
Coordinates all agents to generate, validate, and approve posts
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..models.post import LinkedInPost, PostStatus
from ..models.batch import Batch, BatchMetrics
from ..agents.content_generator import ContentGeneratorAgent
from ..agents.image_generator import ImageGeneratorAgent
from ..agents.feedback_aggregator import FeedbackAggregatorAgent
from ..agents.revision_generator import RevisionGeneratorAgent
from ..agents.validators.sarah_chen import SarahChenValidator
from ..agents.validators.marcus_williams import MarcusWilliamsValidator
from ..agents.validators.jordan_park import JordanParkValidator

logger = logging.getLogger(__name__)


class ContentOrchestrator:
    """Orchestrates the complete content generation and validation pipeline"""
    
    def __init__(self, ai_client, config):
        self.ai_client = ai_client
        self.config = config
        
        # Initialize agents
        self.content_generator = ContentGeneratorAgent(ai_client, config)
        self.image_generator = ImageGeneratorAgent(ai_client, config)
        self.feedback_aggregator = FeedbackAggregatorAgent(ai_client, config)
        self.revision_generator = RevisionGeneratorAgent(ai_client, config)
        
        # Initialize validators
        self.validators = [
            SarahChenValidator(ai_client, config),
            MarcusWilliamsValidator(ai_client, config),
            JordanParkValidator(ai_client, config)
        ]
        
        self.min_approvals = config.batch.min_approvals_required
        self.max_revisions = config.batch.max_revisions
    
    async def generate_batch(self, num_posts: int = 1, use_video: bool = False) -> Batch:
        """
        Generate a batch of posts with validation and revision loops
        
        Args:
            num_posts: Number of posts to generate
            use_video: If True, generate video (~$1.00) instead of image ($0.03)
        """
        
        batch = Batch()
        batch.status = "processing"
        
        media_type = "video" if use_video else "image"
        logger.info(f"Starting batch {batch.id} with {num_posts} posts (media: {media_type})")
        start_time = time.time()
        
        try:
            for i in range(num_posts):
                post = await self._process_single_post(i + 1, batch.id, use_video=use_video)
                batch.add_post(post)
            
            batch.complete()
            
            processing_time = time.time() - start_time
            logger.info(f"Batch {batch.id} completed in {processing_time:.1f}s")
            logger.info(f"Results: {batch.metrics.approved_posts}/{batch.metrics.total_posts} approved")
            
            return batch
            
        except Exception as e:
            batch.status = "failed"
            batch.error = str(e)
            logger.error(f"Batch {batch.id} failed: {e}")
            raise
    
    async def _process_single_post(self, post_number: int, batch_id: str, use_video: bool = False) -> LinkedInPost:
        """Process a single post through generation, validation, and revision"""
        
        media_type = "video" if use_video else "image"
        logger.info(f"Processing post {post_number} (media: {media_type})")
        start_time = time.time()
        
        # Step 1: Generate content
        post = await self.content_generator.execute(
            post_number=post_number,
            batch_id=batch_id
        )
        
        # Step 2: Generate media (image or video)
        if self.config.google.use_images or use_video:
            media_result = await self.image_generator.execute(post, use_video=use_video)
            if media_result.get("success"):
                # Store media info (works for both image and video)
                post.set_image(
                    url=media_result.get("saved_path", ""),
                    prompt=media_result.get("prompt", ""),
                    provider="google_veo" if use_video else "google_gemini",
                    cost=media_result.get("cost", 0.80 if use_video else 0.039)
                )
                # Add media type to post metadata
                post.media_type = media_result.get("media_type", "image")
                logger.info(f"Post {post_number}: {media_type.title()} generated at {post.image_url}")
            else:
                logger.warning(f"Post {post_number}: {media_type.title()} generation failed - {media_result.get('error')}")
        
        # Step 3: Initial validation
        validation_scores = await self._validate_post(post)
        
        # Step 4: Revision loop if needed
        revision_attempt = 0
        while not post.is_approved(self.min_approvals) and post.can_revise():
            revision_attempt += 1
            logger.info(f"Post {post_number}: Revision attempt {revision_attempt}")
            
            # Aggregate feedback - pass both post AND validation_scores
            feedback = await self.feedback_aggregator.execute(post, validation_scores)
            
            if feedback.get("error"):
                logger.warning(f"Feedback aggregation failed: {feedback.get('error')}")
                break
            
            # Generate revision
            post = await self.revision_generator.execute(post, feedback)
            
            # Re-validate
            validation_scores = await self._validate_post(post)
        
        # Set final status
        if post.is_approved(self.min_approvals):
            post.status = PostStatus.APPROVED
            logger.info(f"Post {post_number}: APPROVED with score {post.average_score:.1f}")
        else:
            post.status = PostStatus.REJECTED
            logger.info(f"Post {post_number}: REJECTED with score {post.average_score:.1f}")
        
        post.processing_time_seconds = time.time() - start_time
        
        return post
    
    async def _validate_post(self, post: LinkedInPost):
        """Run all validators on a post in parallel"""
        
        post.status = PostStatus.VALIDATING
        post.validation_scores = []  # Clear previous validations
        
        # Run validators in parallel
        validation_tasks = [
            validator.execute(post) for validator in self.validators
        ]
        
        # FIXED: Capture and store the validation results!
        validation_results = await asyncio.gather(*validation_tasks)
        
        # Store validation scores in the post
        for score in validation_results:
            post.validation_scores.append(score)
        
        logger.info(f"Post {post.post_number}: Validated - {post.approval_count}/{len(self.validators)} approvals, avg score: {post.average_score:.1f}")
        
        # Return validation scores for use in feedback aggregation
        return validation_results
    
    async def generate_single_post(self, use_video: bool = False) -> LinkedInPost:
        """
        Generate a single approved post (convenience method)
        
        Args:
            use_video: If True, generate video (~$1.00) instead of image ($0.03)
        """
        
        batch = await self.generate_batch(num_posts=1, use_video=use_video)
        approved = batch.get_approved_posts()
        
        if approved:
            return approved[0]
        elif batch.posts:
            return batch.posts[0]
        else:
            raise Exception("Failed to generate any posts")
