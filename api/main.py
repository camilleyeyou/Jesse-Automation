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

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
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
# NEW: Import Comment System
from src.agents.comment_generator import CommentGeneratorAgent
from src.services.comment_queue_manager import get_comment_queue_manager
from src.services.linkedin_comment_service import (
    LinkedInCommentService,
    LinkedInCommentConfig,
    MockLinkedInCommentService
)
from src.services.performance_ingestion import PerformanceIngestionService
from src.agents.weekly_strategist import WeeklyStrategistAgent
from src.agents.strategy_refinement import StrategyRefinementAgent
from src.agents.portfolio_qc import PortfolioQCAgent
from src.agents.weekly_review import WeeklyReviewAgent
from src.agents.quality_drift import QualityDriftAgent
from src.infrastructure.memory import get_memory
from src.models.comment import (
    CommentGenerationRequest,
    CommentApprovalRequest,
    CommentStatus,
    CommentStyle
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database path — auto-detects Railway volume at /data, falls back to local
DB_PATH = "data/automation/queue.db"

# Global instances
config: AppConfig = None
ai_client: OpenAIClient = None
orchestrator: ContentOrchestrator = None
queue_manager = None
scheduler = None
linkedin_poster = None
image_generator = None  # NEW: Add image generator global
# Comment System globals
comment_generator: CommentGeneratorAgent = None
comment_queue_manager = None
linkedin_comment_service = None
performance_ingestion: PerformanceIngestionService = None
weekly_strategist: WeeklyStrategistAgent = None
strategy_refinement: StrategyRefinementAgent = None
portfolio_qc: PortfolioQCAgent = None
weekly_review: WeeklyReviewAgent = None
quality_drift: QualityDriftAgent = None

# Job status tracker — stores last result/error for each agent
import traceback as _tb
from datetime import datetime as _dt

_job_status: dict[str, dict] = {}


def _track_job(name: str):
    """Decorator-style context: tracks a background job's result or error."""
    import functools

    def decorator(coro_func):
        @functools.wraps(coro_func)
        async def wrapper(*args, **kwargs):
            _job_status[name] = {"status": "running", "started_at": _dt.utcnow().isoformat()}
            try:
                result = await coro_func(*args, **kwargs)
                _job_status[name] = {
                    "status": "completed",
                    "result": str(result)[:500] if result else None,
                    "started_at": _job_status[name]["started_at"],
                    "completed_at": _dt.utcnow().isoformat(),
                    "error": None,
                }
                logger.info(f"✅ {name} completed: {str(result)[:200]}")
                return result
            except Exception as e:
                tb = _tb.format_exc()
                _job_status[name] = {
                    "status": "failed",
                    "started_at": _job_status[name]["started_at"],
                    "completed_at": _dt.utcnow().isoformat(),
                    "error": str(e),
                    "traceback": tb[-1000:],
                }
                logger.error(f"❌ {name} FAILED: {e}\n{tb}")
        return wrapper
    return decorator


# ============== Pydantic Models ==============

class ScheduleConfig(BaseModel):
    hour: int = 6
    minute: int = 30
    timezone: str = "America/Los_Angeles"
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
    global comment_generator, comment_queue_manager, linkedin_comment_service
    global performance_ingestion, weekly_strategist, strategy_refinement, portfolio_qc, weekly_review
    global DB_PATH

    logger.info("Starting Jesse A. Eisenbalm Automation API...")

    # Auto-detect persistent storage (Railway volume mounted at /data)
    if os.path.isdir("/data"):
        DB_PATH = "/data/queue.db"
        logger.info(f"📂 Railway volume detected — using persistent DB: {DB_PATH}")
    else:
        DB_PATH = "data/automation/queue.db"
        logger.info(f"📂 Local mode — using DB: {DB_PATH}")
    
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
    queue_manager = get_queue_manager(DB_PATH)
    
    # Initialize scheduler
    scheduler = get_scheduler(config)
    
    # Initialize LinkedIn poster
    if os.getenv("MOCK_LINKEDIN", "false").lower() == "true":
        linkedin_poster = MockLinkedInPoster(config)
        logger.info("Using MOCK LinkedIn poster")
    else:
        linkedin_poster = LinkedInPoster(config)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # COMMENT SYSTEM INITIALIZATION
    # ═══════════════════════════════════════════════════════════════════════════
    
    # Initialize Comment Generator Agent
    comment_generator = CommentGeneratorAgent(ai_client, config)
    logger.info("✅ CommentGeneratorAgent initialized")
    
    # Initialize Comment Queue Manager
    comment_queue_manager = get_comment_queue_manager()
    logger.info("✅ Comment Queue Manager initialized")
    
    # Initialize LinkedIn Comment Service
    linkedin_org_urn = os.getenv("LINKEDIN_ORG_URN")
    linkedin_company_id = os.getenv("LINKEDIN_COMPANY_ID")
    linkedin_access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")

    # Build org URN from company ID if not provided directly
    if not linkedin_org_urn and linkedin_company_id:
        linkedin_org_urn = f"urn:li:organization:{linkedin_company_id}"

    if os.getenv("MOCK_LINKEDIN_COMMENTS", "false").lower() == "true":
        linkedin_comment_service = MockLinkedInCommentService()
        logger.info("Using MOCK LinkedIn Comment Service")
    elif linkedin_org_urn and linkedin_access_token:
        linkedin_comment_service = LinkedInCommentService(
            LinkedInCommentConfig(
                access_token=linkedin_access_token,
                organization_urn=linkedin_org_urn
            )
        )
        logger.info("✅ LinkedIn Comment Service initialized")
    else:
        logger.warning("LinkedIn Comment Service not configured (missing LINKEDIN_ORG_URN/LINKEDIN_COMPANY_ID or LINKEDIN_ACCESS_TOKEN)")

    # Wire comment service to orchestrator for auto-CTA comments
    if linkedin_comment_service and orchestrator:
        orchestrator.comment_service = linkedin_comment_service
        logger.info("✅ Comment service wired to orchestrator for auto-CTA comments")

    # ═══════════════════════════════════════════════════════════════════════════
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PERFORMANCE INGESTION (Phase 1 — Data Foundation)
    # ═══════════════════════════════════════════════════════════════════════════

    from src.infrastructure.memory import get_memory as _get_memory
    try:
        _memory = _get_memory(DB_PATH)
        performance_ingestion = PerformanceIngestionService(memory=_memory)
        if performance_ingestion.is_configured():
            logger.info("✅ PerformanceIngestionService initialized — LinkedIn analytics ingestion ready")
        else:
            logger.warning("⚠️ PerformanceIngestionService initialized but LinkedIn token not set — will skip ingestion")
    except Exception as e:
        logger.warning(f"⚠️ PerformanceIngestionService init failed: {e}")

    # Initialize Weekly Strategist Agent (Phase 2 — Strategic Brain)
    try:
        weekly_strategist = WeeklyStrategistAgent(
            ai_client=ai_client,
            config=config,
            trend_service=orchestrator.trend_service if orchestrator else None,
            db_path=DB_PATH,
        )
        logger.info("✅ WeeklyStrategistAgent initialized — editorial planning ready")
    except Exception as e:
        logger.warning(f"⚠️ WeeklyStrategistAgent init failed: {e}")

    # Initialize Strategy Refinement Agent (Phase 3 — Learning System)
    try:
        strategy_refinement = StrategyRefinementAgent(
            ai_client=ai_client, config=config, db_path=DB_PATH
        )
        logger.info("✅ StrategyRefinementAgent initialized — performance pattern analysis ready")
    except Exception as e:
        logger.warning(f"⚠️ StrategyRefinementAgent init failed: {e}")

    # Initialize Portfolio QC Agent (Phase 3 — Learning System)
    try:
        portfolio_qc = PortfolioQCAgent(
            ai_client=ai_client, config=config, db_path=DB_PATH
        )
        logger.info("✅ PortfolioQCAgent initialized — brand consistency monitoring ready")
    except Exception as e:
        logger.warning(f"⚠️ PortfolioQCAgent init failed: {e}")

    # Initialize Weekly Review Agent (Phase 3.3 — Accountability Loop)
    try:
        weekly_review = WeeklyReviewAgent(
            ai_client=ai_client, config=config, db_path=DB_PATH
        )
        logger.info("✅ WeeklyReviewAgent initialized — accountability loop ready")
    except Exception as e:
        logger.warning(f"⚠️ WeeklyReviewAgent init failed: {e}")

    # Initialize Quality Drift Agent — Claude-powered daily supervisor that
    # detects drift patterns per-post validators can't see. Writes findings to
    # strategy_insights with 'drift:' prefix for the weekly strategist + dashboard.
    global quality_drift
    try:
        quality_drift = QualityDriftAgent(
            ai_client=ai_client, config=config, db_path=DB_PATH
        )
        logger.info("✅ QualityDriftAgent initialized — daily drift supervision ready")
    except Exception as e:
        logger.warning(f"⚠️ QualityDriftAgent init failed: {e}")

    # Auto-start scheduler if configured
    if os.getenv("AUTO_START_SCHEDULER", "false").lower() == "true":
        scheduler.start()
        _schedule_all_jobs()
        logger.info("Auto-started scheduler with all jobs")

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

# Always include production Vercel URL
origins.append("https://jesse-automation.vercel.app")

# Add common Vercel patterns (preview deployments)
if os.getenv("VERCEL_URL"):
    origins.append(f"https://{os.getenv('VERCEL_URL')}")

# --- API Key Authentication Middleware ---
class APIKeyMiddleware(BaseHTTPMiddleware):
    """Simple shared-secret authentication middleware.

    If API_SECRET_KEY is set, all /api/ requests must include a valid key
    via 'Authorization: Bearer <key>' or 'X-API-Key: <key>' header.
    Health check (/) and static file routes (/images/, /videos/) are always public.
    """
    async def dispatch(self, request: Request, call_next):
        api_key = os.getenv("API_SECRET_KEY")

        # If no key configured, allow all requests (backward compatible)
        if not api_key:
            return await call_next(request)

        path = request.url.path

        # Always allow public routes
        if path == "/" or path.startswith("/images/") or path.startswith("/videos/"):
            return await call_next(request)

        # Only protect /api/ routes
        if path.startswith("/api/"):
            # Check Authorization: Bearer <key>
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer ") and auth_header[7:] == api_key:
                return await call_next(request)

            # Check X-API-Key header
            x_api_key = request.headers.get("x-api-key", "")
            if x_api_key == api_key:
                return await call_next(request)

            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API key"},
            )

        # Non-/api/ routes pass through
        return await call_next(request)

app.add_middleware(APIKeyMiddleware)

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


# ============== Job Scheduling ==============

def _schedule_all_jobs():
    """Schedule all recurring jobs — daily post + Sunday learning cycle + Friday QC."""
    hour = int(os.getenv("DEFAULT_POST_HOUR", "6"))
    minute = int(os.getenv("DEFAULT_POST_MINUTE", "30"))
    timezone = os.getenv("DEFAULT_TIMEZONE", "America/Los_Angeles")

    # Daily content generation + LinkedIn post
    scheduler.schedule_daily_post(
        job_func=daily_post_job,
        hour=hour,
        minute=minute,
        timezone=timezone
    )
    logger.info(f"📅 Daily post: {hour:02d}:{minute:02d} {timezone}")

    # Sunday learning cycle
    if performance_ingestion:
        scheduler.schedule_weekly_job(
            job_func=weekly_ingestion_job,
            day_of_week="sun", hour=6, minute=0, timezone=timezone,
            job_id="weekly_ingestion", job_name="Weekly Performance Ingestion",
        )
        logger.info("📊 Sunday 6:00 AM: Performance Ingestion")

    if strategy_refinement:
        scheduler.schedule_weekly_job(
            job_func=weekly_refinement_job,
            day_of_week="sun", hour=6, minute=30, timezone=timezone,
            job_id="weekly_refinement", job_name="Weekly Strategy Refinement",
        )
        logger.info("📈 Sunday 6:30 AM: Strategy Refinement")

    if weekly_strategist:
        scheduler.schedule_weekly_job(
            job_func=weekly_strategy_job,
            day_of_week="sun", hour=7, minute=0, timezone=timezone,
            job_id="weekly_strategy", job_name="Weekly Strategy Planning",
        )
        logger.info("🧠 Sunday 7:00 AM: Weekly Strategist")

    # Friday quality checks
    if portfolio_qc:
        scheduler.schedule_weekly_job(
            job_func=friday_qc_job,
            day_of_week="fri", hour=18, minute=0, timezone=timezone,
            job_id="friday_portfolio_qc", job_name="Friday Portfolio QC",
        )
        logger.info("🔍 Friday 6:00 PM: Portfolio QC")

    if weekly_review:
        scheduler.schedule_weekly_job(
            job_func=friday_review_job,
            day_of_week="fri", hour=18, minute=30, timezone=timezone,
            job_id="friday_weekly_review", job_name="Friday Weekly Review",
        )
        logger.info("📋 Friday 6:30 PM: Weekly Review")

    # Daily Claude supervisor — runs an hour after daily post so today's post
    # is in the window along with the preceding week.
    if quality_drift:
        drift_hour = (hour + 1) % 24
        scheduler.schedule_daily_job(
            job_func=daily_drift_job,
            hour=drift_hour, minute=minute, timezone=timezone,
            job_id="daily_drift_scan", job_name="Daily Drift Supervisor",
        )
        logger.info(f"🔎 Daily {drift_hour:02d}:{minute:02d} {timezone}: Quality Drift Supervisor")


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


async def weekly_ingestion_job():
    """
    Weekly job: fetch LinkedIn engagement data for all published posts.
    Runs Sunday 6:00 AM before the strategy agents.
    """
    logger.info("=" * 60)
    logger.info("📊 WEEKLY PERFORMANCE INGESTION JOB TRIGGERED")
    logger.info("=" * 60)

    if not performance_ingestion:
        logger.warning("Performance ingestion service not initialized — skipping")
        return

    try:
        result = await performance_ingestion.run()
        logger.info(f"📊 Ingestion result: {result}")
    except Exception as e:
        logger.error(f"❌ Weekly ingestion job exception: {e}")
        import traceback
        traceback.print_exc()


async def weekly_refinement_job():
    """
    Weekly job: analyse performance patterns and generate strategy insights.
    Runs Sunday 6:30 AM (after ingestion, before strategist).
    """
    logger.info("=" * 60)
    logger.info("📈 WEEKLY STRATEGY REFINEMENT JOB TRIGGERED")
    logger.info("=" * 60)

    if not strategy_refinement:
        logger.warning("Strategy refinement agent not initialized — skipping")
        return

    try:
        result = await strategy_refinement.execute()
        logger.info(f"📈 Refinement result: {result}")
    except Exception as e:
        logger.error(f"❌ Weekly refinement job exception: {e}")
        import traceback
        traceback.print_exc()


async def friday_qc_job():
    """
    Weekly job: evaluate brand consistency across recent posts.
    Runs Friday 6:00 PM.
    """
    logger.info("=" * 60)
    logger.info("🔍 FRIDAY PORTFOLIO QC JOB TRIGGERED")
    logger.info("=" * 60)

    if not portfolio_qc:
        logger.warning("Portfolio QC agent not initialized — skipping")
        return

    try:
        result = await portfolio_qc.execute()
        logger.info(f"🔍 QC result: {result}")
    except Exception as e:
        logger.error(f"❌ Friday QC job exception: {e}")
        import traceback
        traceback.print_exc()


async def daily_drift_job():
    """Daily Claude-powered supervisor scan for quality drift patterns.

    Runs 07:30 PT — an hour after the daily post generation at 06:30, so the
    day's fresh post is in the window along with the preceding week.
    """
    logger.info("=" * 60)
    logger.info("🔎 DAILY DRIFT SUPERVISOR JOB TRIGGERED")
    logger.info("=" * 60)

    if not quality_drift:
        logger.warning("QualityDriftAgent not initialized — skipping")
        return

    try:
        result = await quality_drift.execute(window_days=7)
        findings_count = result.get("findings_count", 0)
        if findings_count:
            logger.info(f"🔎 Drift scan wrote {findings_count} finding(s)")
        else:
            logger.info("🔎 Drift scan found no issues worth flagging")
    except Exception as e:
        logger.error(f"❌ Daily drift job exception: {e}")
        import traceback
        traceback.print_exc()


async def friday_review_job():
    """
    Weekly job: compare editorial plan vs actual posts and score adherence.
    Runs Friday 6:30 PM (after Portfolio QC at 6:00 PM).
    """
    logger.info("=" * 60)
    logger.info("📋 FRIDAY WEEKLY REVIEW JOB TRIGGERED")
    logger.info("=" * 60)

    if not weekly_review:
        logger.warning("Weekly review agent not initialized — skipping")
        return

    try:
        result = await weekly_review.execute()
        logger.info(f"📋 Review result: {result}")
    except Exception as e:
        logger.error(f"❌ Friday review job exception: {e}")
        import traceback
        traceback.print_exc()


async def weekly_strategy_job():
    """
    Weekly job: plan the Mon-Fri editorial calendar.
    Runs Sunday 7:00 AM after performance ingestion completes.
    """
    logger.info("=" * 60)
    logger.info("🧠 WEEKLY STRATEGY PLANNING JOB TRIGGERED")
    logger.info("=" * 60)

    if not weekly_strategist:
        logger.warning("Weekly strategist not initialized — skipping")
        return

    try:
        result = await weekly_strategist.execute()
        logger.info(f"🧠 Strategy result: {result}")
    except Exception as e:
        logger.error(f"❌ Weekly strategy job exception: {e}")
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
    """Start the automation scheduler with all jobs"""
    if not scheduler:
        raise HTTPException(500, "Scheduler not initialized")

    if scheduler.start():
        _schedule_all_jobs()
        return {"success": True, "message": "Scheduler started with all jobs"}
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
        "timezone": scheduler.settings.get("timezone", "America/Los_Angeles"),
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


@app.post("/api/automation/queue/post")
async def post_from_queue(post_id: Optional[str] = None):
    """
    Post the next item from the queue to LinkedIn.

    Args:
        post_id: Optional specific post ID to publish (otherwise uses next pending)

    Returns:
        Result with LinkedIn post ID on success
    """
    if not linkedin_poster:
        raise HTTPException(500, "LinkedIn poster not initialized")

    result = await asyncio.to_thread(queue_manager.post_from_queue, linkedin_poster, post_id)

    if result.get("success"):
        return result
    else:
        raise HTTPException(400, result.get("error", "Failed to post from queue"))


@app.post("/api/automation/queue/post/{post_id}")
async def post_specific_from_queue(post_id: str):
    """Post a specific item from the queue to LinkedIn"""
    if not linkedin_poster:
        raise HTTPException(500, "LinkedIn poster not initialized")

    result = await asyncio.to_thread(queue_manager.post_from_queue, linkedin_poster, post_id)

    if result.get("success"):
        return result
    else:
        raise HTTPException(400, result.get("error", "Failed to post from queue"))


@app.post("/api/automation/queue/requeue-failed")
async def requeue_failed_posts():
    """Move all failed posts back to pending status"""
    count = queue_manager.requeue_failed()
    return {"success": True, "requeued": count}


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


# ═══════════════════════════════════════════════════════════════════════════════
# PERFORMANCE INGESTION ENDPOINTS (Phase 1 — Data Foundation)
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/automation/ingest-performance")
async def trigger_ingestion(background_tasks: BackgroundTasks):
    """Manually trigger LinkedIn performance ingestion."""
    if not performance_ingestion:
        raise HTTPException(503, "Performance ingestion service not initialized")

    @_track_job("ingestion")
    async def _run():
        return await performance_ingestion.run()

    background_tasks.add_task(_run)
    return {"status": "started", "message": "Performance ingestion running in background"}


@app.post("/api/automation/run-refinement")
async def trigger_refinement(background_tasks: BackgroundTasks):
    """Manually trigger the strategy refinement agent."""
    if not strategy_refinement:
        raise HTTPException(503, "Strategy refinement agent not initialized")

    @_track_job("refinement")
    async def _run():
        return await strategy_refinement.execute()

    background_tasks.add_task(_run)
    return {"status": "started", "message": "Strategy refinement running in background"}


@app.post("/api/automation/run-portfolio-qc")
async def trigger_portfolio_qc(background_tasks: BackgroundTasks):
    """Manually trigger the portfolio QC agent."""
    if not portfolio_qc:
        raise HTTPException(503, "Portfolio QC agent not initialized")

    @_track_job("portfolio_qc")
    async def _run():
        return await portfolio_qc.execute()

    background_tasks.add_task(_run)
    return {"status": "started", "message": "Portfolio QC running in background"}


@app.post("/api/automation/run-drift-scan")
async def trigger_drift_scan(background_tasks: BackgroundTasks):
    """Manually trigger the Quality Drift Supervisor.

    Normally runs daily on a schedule; this endpoint lets the dashboard force a
    scan on demand (e.g. after a batch of revisions to see what the supervisor
    flags).
    """
    if not quality_drift:
        raise HTTPException(503, "Quality drift agent not initialized")

    @_track_job("quality_drift")
    async def _run():
        return await quality_drift.execute(window_days=7)

    background_tasks.add_task(_run)
    return {"status": "started", "message": "Quality drift scan running in background"}


@app.get("/api/automation/avoid-list")
async def get_avoid_list(limit: int = 50):
    """Active generator avoid-list entries the supervisor has written.

    When the QualityDriftAgent detects recycled phrases, template overuse,
    or voice drift, it writes literal strings here. The content strategist
    reads these before every generation and injects them into VARIETY GUARD.
    Dashboard shows what the system has 'learned to avoid.'
    """
    memory = get_memory(DB_PATH)
    entries = memory.get_active_avoid_phrases(limit=limit)
    return {
        "count": len(entries),
        "entries": entries,
    }


@app.get("/api/automation/system-health")
async def get_system_health():
    """Consolidated autonomy status for the dashboard.

    Surfaces the signals that tell you whether the closed-loop system is
    healthy: pillar balance, fallback-reject rate, starved pillars, active
    avoid entries, recent drift findings. Dashboard polls this for a single
    'system health' panel instead of calling 4 separate endpoints.
    """
    memory = get_memory(DB_PATH)

    pillar_dist = memory.get_pillar_distribution(days=14)
    fallback = memory.get_fallback_shipping_rate(days=14)
    starved = memory.get_severely_starved_pillar(days=7)
    avoid_count = len(memory.get_active_avoid_phrases(limit=100))
    recent_findings = memory.get_recent_drift_findings(days=7, limit=20)

    # Classify health at a glance
    issues = []
    if fallback.get("fallback_rate", 0) > 0.3:
        issues.append({
            "severity": "critical",
            "type": "fallback_overuse",
            "detail": f"Fallback rate {fallback['fallback_rate']:.1%} — posts not reaching 2-of-3 consensus"
        })
    if starved:
        issues.append({
            "severity": "warning",
            "type": "pillar_starved",
            "detail": f"Pillar '{starved}' has 0 posts in 7 days — next generation will auto-override"
        })
    if not pillar_dist.get("balanced"):
        issues.append({
            "severity": "info",
            "type": "pillar_imbalance",
            "detail": f"Missing pillars: {pillar_dist.get('missing_pillars', [])}"
        })

    return {
        "overall_health": "degraded" if any(i["severity"] == "critical" for i in issues)
            else "warning" if issues
            else "healthy",
        "pillar_distribution": pillar_dist,
        "fallback_rate": fallback,
        "starved_pillar": starved,
        "active_avoid_count": avoid_count,
        "recent_findings_count": len(recent_findings),
        "issues": issues,
    }


@app.get("/api/automation/gold-standard-corpus")
async def get_gold_standard_corpus(limit: int = 50):
    """Browse the gold-standard retrieval corpus.

    Dashboard shows both the hand-seeded Coachella deck specimens and the
    auto-promoted clean 3-of-3 wins. Useful to see what voice anchors the
    generator is retrieving from.
    """
    import sqlite3 as _sq
    memory = get_memory(DB_PATH)
    with _sq.connect(memory.db_path) as conn:
        conn.row_factory = _sq.Row
        rows = conn.execute(
            """SELECT id, content, pillar, format, notes, curator, source_post_id, added_at
               FROM gold_standard_posts
               ORDER BY added_at DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()
    entries = [dict(r) for r in rows]
    return {
        "count": len(entries),
        "total": memory.count_gold_standard_posts(),
        "entries": entries,
    }


@app.get("/api/automation/quality-findings")
async def get_quality_findings(days: int = 14, limit: int = 50):
    """Return drift findings written by the QualityDriftAgent.

    Dashboard polls this to show what the supervisor has flagged. Findings are
    stored in strategy_insights with 'drift:' prefix on insight_type.
    """
    memory = get_memory(DB_PATH)
    findings = memory.get_recent_drift_findings(days=days, limit=limit)
    return {
        "days": days,
        "count": len(findings),
        "findings": findings,
    }


@app.post("/api/automation/run-weekly-review")
async def trigger_weekly_review(background_tasks: BackgroundTasks):
    """Manually trigger the weekly review agent (plan vs reality accountability)."""
    if not weekly_review:
        raise HTTPException(503, "Weekly review agent not initialized")

    @_track_job("weekly_review")
    async def _run():
        return await weekly_review.execute()

    background_tasks.add_task(_run)
    return {"status": "started", "message": "Weekly review running in background"}


@app.post("/api/automation/run-strategist")
async def trigger_strategist(background_tasks: BackgroundTasks):
    """Manually trigger the weekly strategy planning agent."""
    if not weekly_strategist:
        raise HTTPException(503, "Weekly strategist not initialized")

    @_track_job("strategist")
    async def _run():
        return await weekly_strategist.execute()

    background_tasks.add_task(_run)
    return {"status": "started", "message": "Weekly strategist running in background"}


@app.get("/api/automation/job-status")
async def get_job_status():
    """Get the last result/error for each background agent job."""
    return {
        "success": True,
        "jobs": _job_status,
        "agents_initialized": {
            "performance_ingestion": performance_ingestion is not None,
            "strategy_refinement": strategy_refinement is not None,
            "weekly_strategist": weekly_strategist is not None,
            "portfolio_qc": portfolio_qc is not None,
            "weekly_review": weekly_review is not None,
            "scheduler_running": scheduler.is_running if scheduler else False,
        },
    }


@app.get("/api/automation/performance")
async def get_performance(days: int = 14):
    """Get engagement performance data for recent posts."""
    from src.infrastructure.memory import get_memory as _get_mem
    try:
        mem = _get_mem(DB_PATH)
        data = mem.get_recent_performance(days=days)
        return {"success": True, "posts": data, "count": len(data)}
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch performance data: {e}")


@app.get("/api/automation/calendar")
async def get_calendar(start_date: str = None, end_date: str = None):
    """Get editorial calendar entries for a date range."""
    from src.infrastructure.memory import get_memory as _get_mem
    from datetime import date, timedelta
    try:
        mem = _get_mem(DB_PATH)
        if not start_date:
            start_date = date.today().isoformat()
        if not end_date:
            end_date = (date.today() + timedelta(days=7)).isoformat()
        entries = mem.get_calendar_week(start_date, end_date)
        return {"success": True, "entries": entries, "count": len(entries)}
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch calendar: {e}")


@app.get("/api/automation/adaptive-weights")
async def get_adaptive_weights(days: int = 30):
    """Get adaptive theme weights and format performance."""
    from src.infrastructure.memory import get_memory as _get_mem
    try:
        mem = _get_mem(DB_PATH)
        weights = mem.compute_adaptive_weights(days=days)
        theme_perf = mem.get_theme_performance(days=days)
        format_perf = mem.get_format_performance(days=days)
        underexplored = mem.get_underexplored_formats(days=days)
        return {
            "success": True,
            "adaptive_weights": {k: round(v, 3) for k, v in weights.items()},
            "theme_performance": theme_perf,
            "format_performance": format_perf,
            "underexplored_formats": underexplored,
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to compute weights: {e}")


@app.get("/api/automation/strategy-insights")
async def get_insights(top: int = 10, insight_type: str = None):
    """Get top strategy insights."""
    from src.infrastructure.memory import get_memory as _get_mem
    try:
        mem = _get_mem(DB_PATH)
        insights = mem.get_strategy_insights(top=top, insight_type=insight_type)
        return {"success": True, "insights": insights, "count": len(insights)}
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch insights: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# CLIENT REVIEWS — Human feedback from client on content quality
# ═══════════════════════════════════════════════════════════════════════════════


@app.post("/api/automation/client-reviews")
async def add_client_review(request: Request):
    """Submit a client review about content quality."""
    from src.infrastructure.memory import get_memory as _get_mem
    try:
        body = await request.json()
        review_text = body.get("review_text", "").strip()
        if not review_text:
            raise HTTPException(400, "review_text is required")
        rating = body.get("rating")
        category = body.get("category", "general")
        post_id = body.get("post_id")
        mem = _get_mem(DB_PATH)
        review_id = mem.add_client_review(
            review_text=review_text,
            rating=int(rating) if rating is not None else None,
            category=category,
            post_id=post_id,
        )
        return {"success": True, "review_id": review_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to add review: {e}")


@app.get("/api/automation/client-reviews")
async def get_client_reviews(limit: int = 50, unaddressed_only: bool = False):
    """Get client reviews."""
    from src.infrastructure.memory import get_memory as _get_mem
    try:
        mem = _get_mem(DB_PATH)
        reviews = mem.get_client_reviews(limit=limit, unaddressed_only=unaddressed_only)
        return {"success": True, "reviews": reviews, "count": len(reviews)}
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch reviews: {e}")


@app.delete("/api/automation/client-reviews/{review_id}")
async def delete_client_review(review_id: int):
    """Delete a client review."""
    from src.infrastructure.memory import get_memory as _get_mem
    try:
        mem = _get_mem(DB_PATH)
        mem.delete_client_review(review_id)
        return {"success": True}
    except Exception as e:
        raise HTTPException(500, f"Failed to delete review: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# COMMENT ENGAGEMENT ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/comments/generate")
async def generate_comments(request: CommentGenerationRequest):
    """
    Generate comment options for a LinkedIn post
    
    Submit a post URL and content, get back 3 comment options to choose from.
    """
    if not comment_generator:
        raise HTTPException(503, "Comment generator not initialized")
    
    try:
        # Parse preferred styles if provided
        preferred_styles = None
        if request.preferred_styles:
            preferred_styles = [
                CommentStyle(s) for s in request.preferred_styles
                if s in [e.value for e in CommentStyle]
            ]
        
        # Generate comments
        comment = await comment_generator.execute(
            post_url=request.post_url,
            post_content=request.post_content,
            author_name=request.author_name,
            author_headline=request.author_headline,
            num_options=request.num_options,
            preferred_styles=preferred_styles
        )
        
        # Save to queue
        comment_queue_manager.save(comment)
        
        return {
            "success": True,
            "message": f"Generated {len(comment.comment_options)} comment options",
            "comment": comment.to_dict()
        }
        
    except Exception as e:
        logger.error(f"Comment generation failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Generation failed: {str(e)}")


@app.get("/api/comments/queue")
async def get_comments_queue(status: Optional[str] = None, limit: int = 50):
    """
    Get comments in the queue
    
    Optionally filter by status: pending, approved, posted, rejected, failed
    """
    if not comment_queue_manager:
        raise HTTPException(503, "Comment queue manager not initialized")
    
    if status:
        try:
            status_enum = CommentStatus(status)
            comments = comment_queue_manager.get_by_status(status_enum, limit)
        except ValueError:
            raise HTTPException(400, f"Invalid status: {status}")
    else:
        comments = comment_queue_manager.get_queue(limit)
    
    summary = comment_queue_manager.get_summary()
    
    return {
        "success": True,
        "comments": [c.to_dict() for c in comments],
        "summary": {
            "total": summary.total,
            "pending": summary.pending,
            "approved": summary.approved,
            "posted": summary.posted,
            "rejected": summary.rejected,
            "total_likes": summary.total_likes,
            "total_replies": summary.total_replies
        }
    }


@app.get("/api/comments/history")
async def get_comments_history(limit: int = 50, include_rejected: bool = False):
    """Get comment history (posted and optionally rejected)"""
    if not comment_queue_manager:
        raise HTTPException(503, "Comment queue manager not initialized")
    
    comments = comment_queue_manager.get_history(limit, include_rejected)
    
    return {
        "success": True,
        "comments": [c.to_dict() for c in comments],
        "total": len(comments)
    }


@app.get("/api/comments/{comment_id}")
async def get_comment(comment_id: str):
    """Get a single comment by ID"""
    if not comment_queue_manager:
        raise HTTPException(503, "Comment queue manager not initialized")
    
    comment = comment_queue_manager.get(comment_id)
    
    if not comment:
        raise HTTPException(404, "Comment not found")
    
    return {
        "success": True,
        "comment": comment.to_dict()
    }


@app.patch("/api/comments/{comment_id}/select")
async def select_comment_option(comment_id: str, option_id: str, edited_text: Optional[str] = None):
    """Select a comment option (before approval)"""
    if not comment_queue_manager:
        raise HTTPException(503, "Comment queue manager not initialized")
    
    comment = comment_queue_manager.get(comment_id)
    
    if not comment:
        raise HTTPException(404, "Comment not found")
    
    # Verify option exists
    option_ids = [opt.id for opt in comment.comment_options]
    if option_id not in option_ids:
        raise HTTPException(400, "Invalid option ID")
    
    comment.select_option(option_id, edited_text)
    comment_queue_manager.save(comment)
    
    return {
        "success": True,
        "message": "Option selected",
        "comment": comment.to_dict()
    }


@app.patch("/api/comments/{comment_id}/approve")
async def approve_comment(
    comment_id: str,
    request: CommentApprovalRequest,
    background_tasks: BackgroundTasks
):
    """Approve a comment for posting"""
    if not comment_queue_manager:
        raise HTTPException(503, "Comment queue manager not initialized")
    
    comment = comment_queue_manager.get(comment_id)
    
    if not comment:
        raise HTTPException(404, "Comment not found")
    
    if comment.status != CommentStatus.PENDING:
        raise HTTPException(400, f"Comment is {comment.status.value}, not pending")
    
    # Select an option if provided, or auto-select best one
    if request.option_id:
        comment.select_option(request.option_id)
    elif not comment.final_comment and not request.edited_text:
        if not comment.selected_option_id and comment.comment_options:
            # Auto-select best option
            best = max(comment.comment_options, key=lambda x: x.overall_score)
            comment.select_option(best.id)
    
    comment.approve(request.approved_by, request.edited_text)
    comment_queue_manager.save(comment)
    
    # Optionally post immediately
    if request.post_immediately and linkedin_comment_service:
        background_tasks.add_task(post_comment_background, comment_id)
    
    return {
        "success": True,
        "message": "Comment approved" + (" and queued for posting" if request.post_immediately else ""),
        "comment": comment.to_dict()
    }


@app.patch("/api/comments/{comment_id}/reject")
async def reject_comment(comment_id: str, reason: Optional[str] = None):
    """Reject a comment"""
    if not comment_queue_manager:
        raise HTTPException(503, "Comment queue manager not initialized")
    
    comment = comment_queue_manager.reject(comment_id, reason)
    
    if not comment:
        raise HTTPException(404, "Comment not found")
    
    return {
        "success": True,
        "message": "Comment rejected",
        "comment": comment.to_dict()
    }


@app.post("/api/comments/{comment_id}/post")
async def post_comment(comment_id: str):
    """Post an approved comment to LinkedIn"""
    if not comment_queue_manager:
        raise HTTPException(503, "Comment queue manager not initialized")
    if not linkedin_comment_service:
        raise HTTPException(503, "LinkedIn comment service not configured")
    
    comment = comment_queue_manager.get(comment_id)
    
    if not comment:
        raise HTTPException(404, "Comment not found")
    
    if comment.status != CommentStatus.APPROVED:
        raise HTTPException(400, f"Comment must be approved first (current: {comment.status.value})")
    
    if not comment.final_comment:
        raise HTTPException(400, "No comment text to post")
    
    # Post to LinkedIn
    result = await linkedin_comment_service.post_comment(
        post_url=comment.source_post.url,
        comment_text=comment.final_comment,
        post_urn=comment.source_post.urn
    )
    
    if result["success"]:
        comment_queue_manager.mark_posted(
            comment_id,
            result.get("comment_urn", ""),
            result
        )
        
        return {
            "success": True,
            "message": "Comment posted successfully",
            "linkedin_response": result
        }
    else:
        comment_queue_manager.mark_failed(comment_id, result.get("error", "Unknown error"))
        
        raise HTTPException(500, f"Failed to post: {result.get('error', 'Unknown error')}")


@app.delete("/api/comments/{comment_id}")
async def delete_comment(comment_id: str):
    """Delete a comment from the queue"""
    if not comment_queue_manager:
        raise HTTPException(503, "Comment queue manager not initialized")
    
    deleted = comment_queue_manager.delete(comment_id)
    
    if not deleted:
        raise HTTPException(404, "Comment not found")
    
    return {"success": True, "message": "Comment deleted"}


@app.get("/api/comments/analytics/summary")
async def get_comments_analytics():
    """Get comment engagement analytics"""
    if not comment_queue_manager:
        raise HTTPException(503, "Comment queue manager not initialized")
    
    summary = comment_queue_manager.get_summary()
    
    # Get LinkedIn rate limit status if available
    rate_limit = None
    if linkedin_comment_service:
        rate_limit = linkedin_comment_service.get_rate_limit_status()
    
    return {
        "success": True,
        "summary": {
            "total": summary.total,
            "pending": summary.pending,
            "approved": summary.approved,
            "posted": summary.posted,
            "rejected": summary.rejected,
            "failed": summary.failed,
            "total_likes": summary.total_likes,
            "total_replies": summary.total_replies,
            "avg_engagement": summary.avg_engagement_rate
        },
        "rate_limit": rate_limit
    }


# Background task for posting comments
async def post_comment_background(comment_id: str):
    """Background task to post a comment"""
    if not linkedin_comment_service or not comment_queue_manager:
        logger.error("Services not available for background comment posting")
        return
    
    comment = comment_queue_manager.get(comment_id)
    if not comment or not comment.final_comment:
        logger.error(f"Comment {comment_id} not found or has no text")
        return
    
    result = await linkedin_comment_service.post_comment(
        post_url=comment.source_post.url,
        comment_text=comment.final_comment,
        post_urn=comment.source_post.urn
    )
    
    if result["success"]:
        comment_queue_manager.mark_posted(comment_id, result.get("comment_urn", ""), result)
        logger.info(f"Successfully posted comment {comment_id}")
    else:
        comment_queue_manager.mark_failed(comment_id, result.get("error", "Unknown error"))
        logger.error(f"Failed to post comment {comment_id}: {result.get('error')}")


# ═══════════════════════════════════════════════════════════════════════════════
# MEMORY ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/memory/stats")
async def get_memory_stats():
    """Get memory system statistics"""
    if not orchestrator or not orchestrator.memory:
        return {"available": False, "message": "Memory system not initialized"}

    try:
        stats = orchestrator.memory.get_stats()
        return {
            "available": True,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Failed to get memory stats: {e}")
        raise HTTPException(500, f"Failed to get memory stats: {str(e)}")


@app.get("/api/memory/recent-posts")
async def get_memory_recent_posts(days: int = 7, limit: int = 20):
    """Get recently generated posts from memory"""
    if not orchestrator or not orchestrator.memory:
        raise HTTPException(503, "Memory system not initialized")

    try:
        posts = orchestrator.memory.get_recent_posts(days=days, limit=limit)
        return {
            "posts": posts,
            "count": len(posts)
        }
    except Exception as e:
        logger.error(f"Failed to get recent posts: {e}")
        raise HTTPException(500, f"Failed: {str(e)}")


@app.get("/api/memory/pillar-stats")
async def get_pillar_stats(days: int = 30):
    """Get content pillar performance statistics"""
    if not orchestrator or not orchestrator.memory:
        raise HTTPException(503, "Memory system not initialized")

    try:
        stats = orchestrator.memory.get_pillar_stats(days=days)
        return {
            "stats": stats,
            "period_days": days
        }
    except Exception as e:
        logger.error(f"Failed to get pillar stats: {e}")
        raise HTTPException(500, f"Failed: {str(e)}")


@app.get("/api/memory/validator-patterns")
async def get_validator_patterns(days: int = 30):
    """Get learned validator preferences and patterns"""
    if not orchestrator or not orchestrator.memory:
        raise HTTPException(503, "Memory system not initialized")

    try:
        patterns = orchestrator.memory.get_all_validator_patterns(days=days)

        # Convert to serializable format
        result = {}
        for name, pattern in patterns.items():
            result[name] = {
                "likes": pattern.likes,
                "dislikes": pattern.dislikes,
                "approval_rate": pattern.approval_rate,
                "avg_score": pattern.avg_score,
                "best_pillars": pattern.best_pillars,
                "worst_pillars": pattern.worst_pillars,
                "common_critiques": pattern.common_critiques,
                "common_praise": pattern.common_praise
            }

        return {
            "patterns": result,
            "period_days": days
        }
    except Exception as e:
        logger.error(f"Failed to get validator patterns: {e}")
        raise HTTPException(500, f"Failed: {str(e)}")


@app.get("/api/memory/successful-patterns")
async def get_successful_patterns(min_score: float = 7.0, limit: int = 20):
    """Get patterns from highly-rated posts"""
    if not orchestrator or not orchestrator.memory:
        raise HTTPException(503, "Memory system not initialized")

    try:
        patterns = orchestrator.memory.get_successful_patterns(min_score=min_score, limit=limit)
        return {
            "patterns": patterns,
            "min_score": min_score
        }
    except Exception as e:
        logger.error(f"Failed to get successful patterns: {e}")
        raise HTTPException(500, f"Failed: {str(e)}")


@app.get("/api/memory/failed-patterns")
async def get_failed_patterns(max_score: float = 5.0, limit: int = 20):
    """Get patterns from low-rated posts (to learn what to avoid)"""
    if not orchestrator or not orchestrator.memory:
        raise HTTPException(503, "Memory system not initialized")

    try:
        patterns = orchestrator.memory.get_failed_patterns(max_score=max_score, limit=limit)
        return {
            "patterns": patterns,
            "max_score": max_score
        }
    except Exception as e:
        logger.error(f"Failed to get failed patterns: {e}")
        raise HTTPException(500, f"Failed: {str(e)}")


@app.get("/api/memory/insights")
async def get_memory_insights():
    """Get all stored learning insights"""
    if not orchestrator or not orchestrator.memory:
        raise HTTPException(503, "Memory system not initialized")

    try:
        insights = orchestrator.memory.get_all_insights()
        summary = orchestrator.memory.get_validator_feedback_summary()

        return {
            "insights": insights,
            "validator_summary": summary
        }
    except Exception as e:
        logger.error(f"Failed to get insights: {e}")
        raise HTTPException(500, f"Failed: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════════
# Run
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8001)),
        reload=True
    )