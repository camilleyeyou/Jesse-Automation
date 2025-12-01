"""
Scheduler Service
APScheduler-based automation for daily LinkedIn posting
"""

import json
import logging
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)

# Try to import APScheduler
try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.date import DateTrigger
    from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    logger.warning("APScheduler not available - install with: pip install APScheduler")

# Try to import ZoneInfo (Python 3.9+) or fallback to pytz
try:
    from zoneinfo import ZoneInfo
except ImportError:
    try:
        import pytz
        ZoneInfo = lambda tz: pytz.timezone(tz)
    except ImportError:
        ZoneInfo = None
        logger.warning("No timezone library available")


class SchedulerService:
    """Manages scheduled posting automation"""
    
    def __init__(self, config=None):
        self.config = config
        self.scheduler = None
        self.is_running = False
        self.job_history = []
        self.max_history = 100
        
        # Callbacks
        self.on_post_success = None
        self.on_post_error = None
        self.on_content_generated = None
        
        # Config file for persistence
        self.config_file = Path("config/automation_config.json")
        
        # Load saved config
        self._load_config()
        
        if APSCHEDULER_AVAILABLE:
            self._init_scheduler()
    
    def _init_scheduler(self):
        """Initialize the APScheduler"""
        
        timezone = self.settings.get("timezone", "America/New_York")
        
        if ZoneInfo:
            try:
                tz = ZoneInfo(timezone)
                self.scheduler = AsyncIOScheduler(timezone=tz)
            except Exception as e:
                logger.warning(f"Failed to set timezone {timezone}: {e}")
                self.scheduler = AsyncIOScheduler()
        else:
            self.scheduler = AsyncIOScheduler()
        
        # Add event listeners
        self.scheduler.add_listener(self._on_job_executed, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self._on_job_error, EVENT_JOB_ERROR)
        self.scheduler.add_listener(self._on_job_missed, EVENT_JOB_MISSED)
        
        logger.info("Scheduler initialized")
    
    def _load_config(self):
        """Load saved configuration"""
        
        self.settings = {
            "enabled": False,
            "post_hour": 9,
            "post_minute": 0,
            "timezone": "America/New_York",
            "auto_generate": True,
            "last_updated": None
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    saved = json.load(f)
                    self.settings.update(saved)
            except Exception as e:
                logger.warning(f"Failed to load scheduler config: {e}")
    
    def _save_config(self):
        """Save configuration to file"""
        
        self.settings["last_updated"] = datetime.utcnow().isoformat()
        
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.settings, f, indent=2)
    
    def start(self) -> bool:
        """Start the scheduler"""
        
        if not APSCHEDULER_AVAILABLE:
            logger.error("APScheduler not available")
            return False
        
        if self.is_running:
            logger.warning("Scheduler already running")
            return True
        
        try:
            self.scheduler.start()
            self.is_running = True
            self.settings["enabled"] = True
            self._save_config()
            
            logger.info("Scheduler started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop the scheduler"""
        
        if not self.is_running:
            return True
        
        try:
            self.scheduler.shutdown(wait=False)
            self.is_running = False
            self.settings["enabled"] = False
            self._save_config()
            
            # Reinitialize for potential restart
            self._init_scheduler()
            
            logger.info("Scheduler stopped")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop scheduler: {e}")
            return False
    
    def schedule_daily_post(
        self,
        job_func: Callable,
        hour: int = 9,
        minute: int = 0,
        timezone: str = "America/New_York"
    ) -> bool:
        """Schedule daily posting at specified time"""
        
        if not APSCHEDULER_AVAILABLE:
            return False
        
        try:
            # Remove existing daily job if present
            existing = self.scheduler.get_job("daily_post")
            if existing:
                self.scheduler.remove_job("daily_post")
            
            # Create cron trigger
            if ZoneInfo:
                try:
                    trigger = CronTrigger(
                        hour=hour,
                        minute=minute,
                        timezone=ZoneInfo(timezone)
                    )
                except:
                    trigger = CronTrigger(hour=hour, minute=minute)
            else:
                trigger = CronTrigger(hour=hour, minute=minute)
            
            # Add the job
            self.scheduler.add_job(
                job_func,
                trigger=trigger,
                id="daily_post",
                name="Daily LinkedIn Post",
                replace_existing=True,
                misfire_grace_time=3600,  # 1 hour grace period
                coalesce=True,
                max_instances=1
            )
            
            # Update settings
            self.settings["post_hour"] = hour
            self.settings["post_minute"] = minute
            self.settings["timezone"] = timezone
            self._save_config()
            
            logger.info(f"Scheduled daily post at {hour:02d}:{minute:02d} {timezone}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to schedule daily post: {e}")
            return False
    
    def schedule_one_time(
        self,
        job_func: Callable,
        run_time: datetime,
        job_id: str = None
    ) -> Optional[str]:
        """Schedule a one-time post"""
        
        if not APSCHEDULER_AVAILABLE:
            return None
        
        try:
            job_id = job_id or f"one_time_{datetime.utcnow().timestamp()}"
            
            self.scheduler.add_job(
                job_func,
                trigger=DateTrigger(run_date=run_time),
                id=job_id,
                name=f"One-time post at {run_time}",
                replace_existing=True
            )
            
            logger.info(f"Scheduled one-time post for {run_time}")
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to schedule one-time post: {e}")
            return None
    
    def get_next_run_time(self) -> Optional[datetime]:
        """Get the next scheduled run time"""
        
        if not self.scheduler:
            return None
        
        job = self.scheduler.get_job("daily_post")
        if job:
            # Handle different APScheduler versions
            # APScheduler 3.x uses next_run_time attribute
            if hasattr(job, 'next_run_time'):
                return job.next_run_time
            # APScheduler 4.x might use different approach
            elif hasattr(job, 'trigger'):
                try:
                    # Try to get next fire time from trigger
                    next_time = job.trigger.get_next_fire_time(None, datetime.now())
                    return next_time
                except Exception:
                    pass
            # Fallback: calculate from settings
            try:
                now = datetime.now()
                scheduled_time = now.replace(
                    hour=self.settings.get("post_hour", 9),
                    minute=self.settings.get("post_minute", 0),
                    second=0,
                    microsecond=0
                )
                if scheduled_time <= now:
                    scheduled_time += timedelta(days=1)
                return scheduled_time
            except Exception:
                pass
        
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status"""
        
        next_run = self.get_next_run_time()
        
        return {
            "available": APSCHEDULER_AVAILABLE,
            "running": self.is_running,
            "enabled": self.settings.get("enabled", False),
            "schedule": {
                "hour": self.settings.get("post_hour", 9),
                "minute": self.settings.get("post_minute", 0),
                "timezone": self.settings.get("timezone", "America/New_York")
            },
            "next_run": next_run.isoformat() if next_run else None,
            "auto_generate": self.settings.get("auto_generate", True),
            "jobs": self._get_jobs_info(),
            "recent_history": self.job_history[-10:]
        }
    
    def _get_jobs_info(self) -> list:
        """Get info about scheduled jobs"""
        
        if not self.scheduler:
            return []
        
        jobs = []
        for job in self.scheduler.get_jobs():
            next_run = None
            # Handle different APScheduler versions
            if hasattr(job, 'next_run_time'):
                next_run = job.next_run_time
            elif hasattr(job, 'trigger'):
                try:
                    next_run = job.trigger.get_next_fire_time(None, datetime.now())
                except:
                    pass
            
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": next_run.isoformat() if next_run else None
            })
        
        return jobs
    
    def _on_job_executed(self, event):
        """Handle successful job execution"""
        
        self.job_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "job_id": event.job_id,
            "status": "success"
        })
        
        # Trim history
        if len(self.job_history) > self.max_history:
            self.job_history = self.job_history[-self.max_history:]
        
        logger.info(f"Job {event.job_id} executed successfully")
        
        if self.on_post_success:
            try:
                self.on_post_success(event)
            except Exception as e:
                logger.error(f"Post success callback failed: {e}")
    
    def _on_job_error(self, event):
        """Handle job execution error"""
        
        self.job_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "job_id": event.job_id,
            "status": "error",
            "error": str(event.exception) if event.exception else "Unknown error"
        })
        
        logger.error(f"Job {event.job_id} failed: {event.exception}")
        
        if self.on_post_error:
            try:
                self.on_post_error(event)
            except Exception as e:
                logger.error(f"Post error callback failed: {e}")
    
    def _on_job_missed(self, event):
        """Handle missed job"""
        
        self.job_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "job_id": event.job_id,
            "status": "missed"
        })
        
        logger.warning(f"Job {event.job_id} missed scheduled time")
    
    def trigger_now(self, job_func: Callable) -> bool:
        """Manually trigger a post now"""
        
        if not APSCHEDULER_AVAILABLE:
            # Run directly if no scheduler
            try:
                asyncio.create_task(job_func())
                return True
            except:
                return False
        
        try:
            # Schedule to run immediately
            self.scheduler.add_job(
                job_func,
                trigger=DateTrigger(run_date=datetime.now()),
                id=f"manual_{datetime.utcnow().timestamp()}",
                name="Manual trigger"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to trigger manual post: {e}")
            return False


# Singleton instance
_scheduler: Optional[SchedulerService] = None


def get_scheduler(config=None) -> SchedulerService:
    """Get or create scheduler singleton"""
    global _scheduler
    if _scheduler is None:
        _scheduler = SchedulerService(config)
    return _scheduler