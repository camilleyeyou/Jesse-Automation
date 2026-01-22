from dotenv import load_dotenv
load_dotenv()

"""
Jesse A. Eisenbalm LinkedIn Automation API
FastAPI backend for content generation and automation
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.config.config_manager import get_config, AppConfig
from src.infrastructure.ai.openai_client import OpenAIClient
from src.services.orchestrator import ContentOrchestrator
from src.services.queue_manager import get_queue_manager
from src.services.scheduler import get_scheduler
from src.services.linkedin_poster import LinkedInPoster, MockLinkedInPoster
# NEW: Import ImageGeneratorAgent
from src.agents.image_generator import ImageGeneratorAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
config: AppConfig = None
ai_client: OpenAIClient = None
orchestrator: ContentOrchestrator = None
queue_manager = None
scheduler = None
linkedin_poster = None
image_generator = None  # NEW: Add image generator global


# ============== Pydantic Models ==============

class ScheduleConfig(BaseModel):
    hour: int = 9
    minute: int = 0
    timezone: str = "America/New_York"
    enabled: bool = True

class QueuePostRequest(BaseModel):
    content: str
    hashtags: Optional[List[str]] = []
    image_url: Optional[str] = None
    priority: int = 0

class GenerateRequest(BaseModel):
    num_posts: int = 1
    add_to_queue: bool = True
    use_video: bool = False  # Generate video (~$1.00) instead of image ($0.03)


# ============== Lifespan ==============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global config, ai_client, orchestrator, queue_manager, scheduler, linkedin_poster, image_generator
    
    logger.info("Starting Jesse A. Eisenbalm Automation API...")
    
    # Initialize config
    config = get_config()
    
    # Initialize AI client
    ai_client = OpenAIClient(config)
    
    # NEW: Initialize image generator
    image_generator = ImageGeneratorAgent(ai_client, config)
    logger.info("✅ ImageGeneratorAgent initialized")
    
    # Initialize orchestrator WITH image generator
    orchestrator = ContentOrchestrator(
        ai_client, 
        config, 
        image_generator=image_generator,  # NEW: Pass image generator
        queue_manager=None  # We'll set this after queue_manager is created if needed
    )
    logger.info("✅ ContentOrchestrator initialized with image generator")
    
    # Initialize queue manager
    queue_manager = get_queue_manager()
    
    # Initialize scheduler
    scheduler = get_scheduler(config)
    
    # Initialize LinkedIn poster
    if os.getenv("MOCK_LINKEDIN", "false").lower() == "true":
        linkedin_poster = MockLinkedInPoster(config)
        logger.info("Using MOCK LinkedIn poster")
    else:
        linkedin_poster = LinkedInPoster(config)
    
    # Auto-start scheduler if configured
    if os.getenv("AUTO_START_SCHEDULER", "false").lower() == "true":
        scheduler.start()
        hour = int(os.getenv("DEFAULT_POST_HOUR", "9"))
        minute = int(os.getenv("DEFAULT_POST_MINUTE", "0"))
        timezone = os.getenv("DEFAULT_TIMEZONE", "America/New_York")
        scheduler.schedule_daily_post(
            job_func=daily_post_job,
            hour=hour,
            minute=minute,
            timezone=timezone
        )
        logger.info(f"Auto-started scheduler at {hour:02d}:{minute:02d} {timezone}")
    
    logger.info("API startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    if scheduler and scheduler.is_running:
        scheduler.stop()
    if ai_client:
        await ai_client.close()
    logger.info("Shutdown complete")


# ============== App Setup ==============

app = FastAPI(
    title="Jesse A. Eisenbalm Automation API",
    description="AI-powered LinkedIn content generation and automation",
    version="2.0.0",
    lifespan=lifespan
)

# CORS - Allow Vercel frontend
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
origins = [origin.strip() for origin in cors_origins.split(",")]

# Add common Vercel patterns
if os.getenv("VERCEL_URL"):
    origins.append(f"https://{os.getenv('VERCEL_URL')}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for images
images_dir = Path("data/images")
images_dir.mkdir(parents=True, exist_ok=True)
try:
    app.mount("/images", StaticFiles(directory=str(images_dir)), name="images")
except Exception as e:
    logger.warning(f"Could not mount images directory: {e}")

# Static files for videos
videos_dir = Path("data/images/videos")
videos_dir.mkdir(parents=True, exist_ok=True)
try:
    app.mount("/videos", StaticFiles(directory=str(videos_dir)), name="videos")
except Exception as e:
    logger.warning(f"Could not mount videos directory: {e}")


# ============== Background Jobs ==============

async def daily_post_job():
    """
    Job function for daily posting - ALWAYS generates fresh content.
    
    This ensures:
    - Fresh trending topic every post
    - No stale queued content
    - Fully automatic operation
    """
    logger.info("=" * 60)
    logger.info("🕐 SCHEDULED POST JOB TRIGGERED")
    logger.info("=" * 60)
    
    try:
        # Use generate_and_post_now for fresh content every time
        result = await orchestrator.generate_and_post_now(
            linkedin_poster=linkedin_poster,
            use_video=False  # Use images for cost efficiency
        )
        
        if result.get("success"):
            # Record to history for tracking
            post_data = result.get("post", {})
            queue_manager.record_published(
                post_data,
                linkedin_post_id=result.get("linkedin", {}).get("post_id"),
                status="success"
            )
            logger.info(f"✅ Scheduled post successful: {result.get('linkedin', {}).get('post_id')}")
        else:
            logger.error(f"❌ Scheduled post failed: {result.get('error')}")
            # Record failure
            queue_manager.record_published(
                result.get("post", {}),
                status="failed",
                error=result.get("error")
            )
            
    except Exception as e:
        logger.error(f"❌ Daily post job exception: {e}")
        import traceback
        traceback.print_exc()


# ============== Health Check ==============

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Jesse A. Eisenbalm Automation API",
        "version": "2.0.0",
        "status": "running",
        "image_generation": "enabled" if image_generator else "disabled"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "scheduler_running": scheduler.is_running if scheduler else False,
        "queue_size": queue_manager.get_queue_stats()["pending"] if queue_manager else 0,
        "image_generator": "ready" if image_generator else "not initialized"
    }


# ============== Automation Endpoints ==============

@app.get("/api/automation/status")
async def get_automation_status():
    """Get full automation status"""
    return {
        "scheduler": scheduler.get_status() if scheduler else None,
        "queue": queue_manager.get_queue_stats() if queue_manager else None,
        "linkedin": {
            "configured": linkedin_poster.is_configured() if linkedin_poster else False,
            "mock": isinstance(linkedin_poster, MockLinkedInPoster)
        },
        "image_generation": {
            "enabled": image_generator is not None,
            "provider": "google_imagen" if image_generator else None
        }
    }


@app.post("/api/automation/scheduler/start")
async def start_scheduler():
    """Start the automation scheduler"""
    if not scheduler:
        raise HTTPException(500, "Scheduler not initialized")
    
    if scheduler.start():
        return {"success": True, "message": "Scheduler started"}
    else:
        raise HTTPException(500, "Failed to start scheduler")


@app.post("/api/automation/scheduler/stop")
async def stop_scheduler():
    """Stop the automation scheduler"""
    if not scheduler:
        raise HTTPException(500, "Scheduler not initialized")
    
    if scheduler.stop():
        return {"success": True, "message": "Scheduler stopped"}
    else:
        raise HTTPException(500, "Failed to stop scheduler")


@app.get("/api/automation/schedule")
async def get_schedule():
    """Get current schedule settings"""
    return {
        "hour": scheduler.settings.get("post_hour", 9),
        "minute": scheduler.settings.get("post_minute", 0),
        "timezone": scheduler.settings.get("timezone", "America/New_York"),
        "enabled": scheduler.settings.get("enabled", False),
        "next_run": scheduler.get_next_run_time().isoformat() if scheduler.get_next_run_time() else None
    }


@app.post("/api/automation/schedule")
async def set_schedule(config: ScheduleConfig):
    """Set the posting schedule"""
    if not scheduler:
        raise HTTPException(500, "Scheduler not initialized")
    
    success = scheduler.schedule_daily_post(
        job_func=daily_post_job,
        hour=config.hour,
        minute=config.minute,
        timezone=config.timezone
    )
    
    if success:
        return {
            "success": True,
            "message": f"Scheduled for {config.hour:02d}:{config.minute:02d} {config.timezone}",
            "next_run": scheduler.get_next_run_time().isoformat() if scheduler.get_next_run_time() else None
        }
    else:
        raise HTTPException(500, "Failed to set schedule")


@app.post("/api/automation/post-now")
async def post_now(background_tasks: BackgroundTasks):
    """Trigger an immediate post (generates fresh content)"""
    background_tasks.add_task(daily_post_job)
    return {"success": True, "message": "Fresh content generation and post triggered"}


@app.post("/api/automation/generate-and-post")
async def generate_and_post(use_video: bool = False):
    """
    Generate fresh content and post immediately (synchronous).
    
    This is the RECOMMENDED way to post because:
    - Always uses fresh trending topics
    - No stale queue content
    - Returns full result including LinkedIn post ID
    
    Args:
        use_video: Generate video (~$1.00) instead of image ($0.03)
    """
    if not orchestrator:
        raise HTTPException(500, "Orchestrator not initialized")
    if not linkedin_poster:
        raise HTTPException(500, "LinkedIn poster not initialized")
    
    try:
        result = await orchestrator.generate_and_post_now(
            linkedin_poster=linkedin_poster,
            use_video=use_video
        )
        
        if result.get("success"):
            # Record to history
            queue_manager.record_published(
                result.get("post", {}),
                linkedin_post_id=result.get("linkedin", {}).get("post_id"),
                status="success"
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Generate and post failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Failed: {str(e)}")


@app.post("/api/automation/generate-content")
async def generate_content(request: GenerateRequest):
    """
    Generate new content
    
    Args:
        num_posts: Number of posts to generate (default: 1)
        add_to_queue: Whether to add approved posts to queue (default: True)
        use_video: Generate 8-second video (~$1.00) instead of image ($0.03) (default: False)
    """
    if not orchestrator:
        raise HTTPException(500, "Orchestrator not initialized")
    
    try:
        # Generate batch with optional video
        batch = await orchestrator.generate_batch(
            num_posts=request.num_posts,
            use_video=request.use_video
        )
        
        # Add approved posts to queue if requested
        added_to_queue = 0
        if request.add_to_queue:
            for post in batch.get_approved_posts():
                # to_dict() automatically calculates average_score from validation_scores
                queue_manager.add_to_queue(post.to_dict())
                added_to_queue += 1
        
        return {
            "success": True,
            "batch_id": batch.id,
            "total_posts": len(batch.posts) + len(batch.rejected_posts),
            "approved_posts": len(batch.approved_posts),
            "added_to_queue": added_to_queue,
            "media_type": "video" if request.use_video else "image",
            "posts": [p.to_dict() for p in batch.posts]
        }
        
    except Exception as e:
        logger.error(f"Content generation failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Generation failed: {str(e)}")


# ============== Queue Endpoints ==============

@app.get("/api/automation/queue")
async def get_queue(status: Optional[str] = None, limit: int = 50):
    """Get queued posts"""
    return {
        "posts": queue_manager.get_queue(status=status, limit=limit),
        "stats": queue_manager.get_queue_stats()
    }


@app.post("/api/automation/queue")
async def add_to_queue(request: QueuePostRequest):
    """Add a post to the queue"""
    post_id = queue_manager.add_to_queue({
        "content": request.content,
        "hashtags": request.hashtags,
        "image_url": request.image_url
    }, priority=request.priority)
    
    return {"success": True, "post_id": post_id}


@app.delete("/api/automation/queue/{post_id}")
async def remove_from_queue(post_id: str):
    """Remove a post from the queue"""
    queue_manager.remove_from_queue(post_id)
    return {"success": True, "message": f"Post {post_id} removed"}


@app.post("/api/automation/queue/clear")
async def clear_queue(status: Optional[str] = None):
    """Clear the queue"""
    deleted = queue_manager.clear_queue(status=status)
    return {"success": True, "deleted": deleted}


# ============== History Endpoints ==============

@app.get("/api/automation/history")
async def get_history(days: int = 30, limit: int = 100):
    """Get published posts history"""
    return {
        "posts": queue_manager.get_published_history(days=days, limit=limit)
    }


@app.get("/api/automation/activity")
async def get_activity(limit: int = 100):
    """Get activity log"""
    return {
        "activities": queue_manager.get_activity_log(limit=limit)
    }


# ============== LinkedIn Endpoints ==============

@app.get("/api/automation/topics/recent")
async def get_recent_topics(limit: int = 20):
    """Get recently used trending topics (for debugging/display)"""
    if not orchestrator or not orchestrator.trend_service:
        return {"topics": [], "message": "Trend service not available"}
    
    topics = orchestrator.trend_service.get_recent_topics(limit=limit)
    return {
        "topics": topics,
        "cooldown_days": orchestrator.trend_service.TOPIC_COOLDOWN_DAYS
    }


@app.post("/api/automation/topics/cleanup")
async def cleanup_old_topics(days: int = 30):
    """Clean up topics older than specified days"""
    if not orchestrator or not orchestrator.trend_service:
        raise HTTPException(500, "Trend service not available")
    
    deleted = orchestrator.trend_service.cleanup_old_topics(days=days)
    return {"success": True, "deleted": deleted}


@app.get("/api/automation/linkedin/status")
async def get_linkedin_status():
    """Get LinkedIn connection status"""
    if not linkedin_poster:
        return {"configured": False, "error": "LinkedIn poster not initialized"}
    
    return {
        "configured": linkedin_poster.is_configured(),
        "mock": isinstance(linkedin_poster, MockLinkedInPoster)
    }


@app.post("/api/automation/linkedin/test")
async def test_linkedin():
    """Test LinkedIn connection"""
    if not linkedin_poster:
        raise HTTPException(500, "LinkedIn poster not initialized")
    
    result = linkedin_poster.test_connection()
    return result


# ============== Run ==============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8001)),
        reload=True
    )