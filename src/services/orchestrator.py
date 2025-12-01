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
    
    async def generate_batch(self, num_posts: int = 1) -> Batch:
        """Generate a batch of posts with validation and revision loops"""
        
        batch = Batch()
        batch.status = "processing"
        
        logger.info(f"Starting batch {batch.id} with {num_posts} posts")
        start_time = time.time()
        
        try:
            for i in range(num_posts):
                post = await self._process_single_post(i + 1, batch.id)
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
    
    async def _process_single_post(self, post_number: int, batch_id: str) -> LinkedInPost:
        """Process a single post through generation, validation, and revision"""
        
        logger.info(f"Processing post {post_number}")
        start_time = time.time()
        
        # Step 1: Generate content
        post = await self.content_generator.execute(
            post_number=post_number,
            batch_id=batch_id
        )
        
        # Step 2: Generate image (if enabled)
        if self.config.google.use_images:
            image_result = await self.image_generator.execute(post)
            if image_result.get("success"):
                logger.info(f"Post {post_number}: Image generated")
            else:
                logger.warning(f"Post {post_number}: Image generation failed - {image_result.get('error')}")
        
        # Step 3: Initial validation
        await self._validate_post(post)
        
        # Step 4: Revision loop if needed
        revision_attempt = 0
        while not post.is_approved(self.min_approvals) and post.can_revise():
            revision_attempt += 1
            logger.info(f"Post {post_number}: Revision attempt {revision_attempt}")
            
            # Aggregate feedback
            feedback = await self.feedback_aggregator.execute(post)
            
            if not feedback.get("success"):
                logger.warning(f"Feedback aggregation failed: {feedback.get('error')}")
                break
            
            # Generate revision
            post = await self.revision_generator.execute(post, feedback)
            
            # Re-validate
            await self._validate_post(post)
        
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
        
        await asyncio.gather(*validation_tasks)
        
        logger.info(f"Post {post.post_number}: Validated - {post.approval_count}/{len(self.validators)} approvals, avg score: {post.average_score:.1f}")
    
    async def generate_single_post(self) -> LinkedInPost:
        """Generate a single approved post (convenience method)"""
        
        batch = await self.generate_batch(num_posts=1)
        approved = batch.get_approved_posts()
        
        if approved:
            return approved[0]
        elif batch.posts:
            return batch.posts[0]
        else:
            raise Exception("Failed to generate any posts")
