"""
Post Queue Manager
SQLite-backed persistent queue for scheduled posting
With memory integration for learning from past posts
"""

import json
import sqlite3
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)

# Import memory system
try:
    from ..infrastructure.memory import get_memory
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    get_memory = None


class PostQueueManager:
    """Manages a persistent queue of posts for scheduled publishing"""

    def __init__(self, db_path: str = "data/automation/queue.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

        # Initialize memory system for learning
        self.memory = None
        if MEMORY_AVAILABLE:
            try:
                self.memory = get_memory(str(self.db_path))
                logger.info("✅ Queue Manager connected to memory system")
            except Exception as e:
                logger.warning(f"Memory system unavailable: {e}")
    
    def _init_database(self):
        """Initialize SQLite database with required tables"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Post queue table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS post_queue (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    hashtags TEXT,
                    image_url TEXT,
                    image_description TEXT,
                    image_prompt TEXT,
                    cultural_reference TEXT,
                    target_audience TEXT,
                    priority INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'pending',
                    scheduled_for TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    batch_id TEXT,
                    validation_score REAL
                )
            """)
            
            # Published posts history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS published_posts (
                    id TEXT PRIMARY KEY,
                    post_id TEXT,
                    linkedin_post_id TEXT,
                    content TEXT,
                    hashtags TEXT,
                    image_url TEXT,
                    published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    engagement_data TEXT,
                    status TEXT DEFAULT 'success',
                    error_message TEXT,
                    metadata TEXT
                )
            """)
            
            # Activity log
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS activity_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    details TEXT,
                    status TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS automation_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
        
        logger.info(f"Database initialized at {self.db_path}")
    
    def add_to_queue(self, post_data: Dict[str, Any], priority: int = 0) -> str:
        """Add a post to the queue"""
        
        post_id = post_data.get("id", str(uuid4()))
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Handle cultural reference
            cultural_ref = post_data.get("cultural_reference")
            if cultural_ref and isinstance(cultural_ref, dict):
                cultural_ref = json.dumps(cultural_ref)
            elif cultural_ref and hasattr(cultural_ref, "dict"):
                cultural_ref = json.dumps(cultural_ref.dict())
            
            cursor.execute("""
                INSERT INTO post_queue 
                (id, content, hashtags, image_url, image_description, image_prompt,
                 cultural_reference, target_audience, priority, status, batch_id, 
                 validation_score, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?)
            """, (
                post_id,
                post_data.get("content", ""),
                json.dumps(post_data.get("hashtags", [])),
                post_data.get("image_url"),
                post_data.get("image_description"),
                post_data.get("image_prompt"),
                cultural_ref,
                post_data.get("target_audience", ""),
                priority,
                post_data.get("batch_id"),
                post_data.get("average_score") or post_data.get("validation_score"),
                json.dumps(post_data.get("metadata", {}))
            ))
            
            conn.commit()
        
        self._log_activity("add_to_queue", {"post_id": post_id}, "success")
        logger.info(f"Added post {post_id} to queue")
        
        return post_id
    
    def get_next_post(self) -> Optional[Dict[str, Any]]:
        """Get the next post to publish (highest priority, oldest first)"""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM post_queue 
                WHERE status = 'pending'
                AND (scheduled_for IS NULL OR scheduled_for <= datetime('now'))
                ORDER BY priority DESC, created_at ASC
                LIMIT 1
            """)
            
            row = cursor.fetchone()
            
            if row:
                return self._row_to_dict(row)
            
            return None
    
    def get_queue(self, status: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get posts from the queue"""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if status:
                cursor.execute("""
                    SELECT * FROM post_queue 
                    WHERE status = ?
                    ORDER BY priority DESC, created_at ASC
                    LIMIT ?
                """, (status, limit))
            else:
                cursor.execute("""
                    SELECT * FROM post_queue 
                    ORDER BY priority DESC, created_at ASC
                    LIMIT ?
                """, (limit,))
            
            return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    def update_status(self, post_id: str, status: str):
        """Update post status"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE post_queue 
                SET status = ?, updated_at = datetime('now')
                WHERE id = ?
            """, (status, post_id))
            conn.commit()
        
        logger.debug(f"Updated post {post_id} status to {status}")
    
    def remove_from_queue(self, post_id: str):
        """Remove a post from the queue"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM post_queue WHERE id = ?", (post_id,))
            conn.commit()
        
        self._log_activity("remove_from_queue", {"post_id": post_id}, "success")
        logger.info(f"Removed post {post_id} from queue")
    
    def record_published(self, post_data: Dict[str, Any], linkedin_post_id: str = None,
                         status: str = "success", error: str = None):
        """Record a published post to history and memory"""

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO published_posts
                (id, post_id, linkedin_post_id, content, hashtags, image_url,
                 status, error_message, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid4()),
                post_data.get("id"),
                linkedin_post_id,
                post_data.get("content"),
                json.dumps(post_data.get("hashtags", [])),
                post_data.get("image_url"),
                status,
                error,
                json.dumps(post_data.get("metadata", {}))
            ))

            conn.commit()

        # Store in memory system for learning
        if self.memory and status == "success":
            try:
                self.memory.mark_posted_to_linkedin(
                    post_data.get("id", ""),
                    linkedin_post_id or ""
                )
                logger.debug(f"📝 Recorded published post in memory: {post_data.get('id')}")
            except Exception as e:
                logger.warning(f"Failed to record in memory: {e}")

        self._log_activity("record_published", {
            "post_id": post_data.get("id"),
            "linkedin_post_id": linkedin_post_id,
            "status": status
        }, status)
    
    def get_published_history(self, days: int = 30, limit: int = 100) -> List[Dict[str, Any]]:
        """Get published posts history"""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM published_posts 
                WHERE published_at >= datetime('now', ?)
                ORDER BY published_at DESC
                LIMIT ?
            """, (f'-{days} days', limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Count by status
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM post_queue 
                GROUP BY status
            """)
            status_counts = dict(cursor.fetchall())
            
            # Published today
            cursor.execute("""
                SELECT COUNT(*) FROM published_posts 
                WHERE date(published_at) = date('now')
            """)
            published_today = cursor.fetchone()[0]
            
            # Published this week
            cursor.execute("""
                SELECT COUNT(*) FROM published_posts 
                WHERE published_at >= datetime('now', '-7 days')
            """)
            published_week = cursor.fetchone()[0]
            
            return {
                "pending": status_counts.get("pending", 0),
                "publishing": status_counts.get("publishing", 0),
                "failed": status_counts.get("failed", 0),
                "published_today": published_today,
                "published_this_week": published_week,
                "total_in_queue": sum(status_counts.values())
            }
    
    def clear_queue(self, status: str = None):
        """Clear the queue (optionally by status)"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if status:
                cursor.execute("DELETE FROM post_queue WHERE status = ?", (status,))
            else:
                cursor.execute("DELETE FROM post_queue")
            
            deleted = cursor.rowcount
            conn.commit()
        
        self._log_activity("clear_queue", {"status": status, "deleted": deleted}, "success")
        logger.info(f"Cleared {deleted} posts from queue")
        
        return deleted
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert a database row to dictionary"""
        
        data = dict(row)
        
        # Parse JSON fields
        if data.get("hashtags"):
            try:
                data["hashtags"] = json.loads(data["hashtags"])
            except:
                data["hashtags"] = []
        
        if data.get("cultural_reference"):
            try:
                data["cultural_reference"] = json.loads(data["cultural_reference"])
            except:
                pass
        
        if data.get("metadata"):
            try:
                data["metadata"] = json.loads(data["metadata"])
            except:
                data["metadata"] = {}
        
        return data
    
    def _log_activity(self, action: str, details: Dict[str, Any], status: str):
        """Log an activity to the database"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO activity_log (action, details, status)
                VALUES (?, ?, ?)
            """, (action, json.dumps(details), status))
            conn.commit()
    
    def get_activity_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent activity log entries"""

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM activity_log
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

            return [dict(row) for row in cursor.fetchall()]

    def get_memory_insights(self) -> Dict[str, Any]:
        """Get insights from memory system about past content performance"""
        if not self.memory:
            return {"available": False, "message": "Memory system not available"}

        try:
            stats = self.memory.get_stats()
            recent_posts = self.memory.get_recent_posts(days=30, limit=20)
            recent_topics = self.memory.get_recent_topics(days=7, limit=10)

            return {
                "available": True,
                "stats": stats,
                "recent_posts_count": len(recent_posts),
                "recent_topics": recent_topics,
                "learning_enabled": True
            }
        except Exception as e:
            logger.warning(f"Failed to get memory insights: {e}")
            return {"available": False, "error": str(e)}

    def post_from_queue(self, linkedin_poster, post_id: str = None) -> Dict[str, Any]:
        """
        Post the next item from the queue to LinkedIn.

        Args:
            linkedin_poster: LinkedInPoster instance
            post_id: Optional specific post ID to publish (otherwise uses next in queue)

        Returns:
            Dict with success status and details
        """
        # Get the post to publish
        if post_id:
            post_data = self.get_post_by_id(post_id)
            if not post_data:
                return {"success": False, "error": f"Post {post_id} not found in queue"}
        else:
            post_data = self.get_next_post()
            if not post_data:
                return {"success": False, "error": "No pending posts in queue"}

        post_id = post_data.get("id")
        logger.info(f"📤 Publishing post {post_id} from queue...")

        # Mark as publishing
        self.update_status(post_id, "publishing")

        try:
            # Publish to LinkedIn
            result = linkedin_poster.publish_post(
                content=post_data.get("content", ""),
                image_path=post_data.get("image_url"),
                hashtags=post_data.get("hashtags", [])
            )

            if result.get("success"):
                linkedin_post_id = result.get("post_id")
                logger.info(f"✅ Posted successfully: {linkedin_post_id}")

                # Update queue status
                self.update_status(post_id, "published")

                # Record in history
                self.record_published(post_data, linkedin_post_id, "success")

                # Remove from active queue
                self.remove_from_queue(post_id)

                return {
                    "success": True,
                    "post_id": post_id,
                    "linkedin_post_id": linkedin_post_id,
                    "content": post_data.get("content", "")[:100] + "...",
                    "message": "Post published successfully from queue"
                }
            else:
                error_msg = result.get("error", "Unknown error")
                logger.error(f"❌ LinkedIn publish failed: {error_msg}")

                # Mark as failed but keep in queue
                self.update_status(post_id, "failed")

                # Record failure
                self.record_published(post_data, None, "failed", error_msg)

                return {
                    "success": False,
                    "post_id": post_id,
                    "error": error_msg,
                    "details": result.get("details")
                }

        except Exception as e:
            logger.error(f"❌ Exception publishing from queue: {e}")
            self.update_status(post_id, "failed")
            return {
                "success": False,
                "post_id": post_id,
                "error": str(e)
            }

    def get_post_by_id(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific post from the queue by ID"""

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM post_queue WHERE id = ?
            """, (post_id,))

            row = cursor.fetchone()
            if row:
                return self._row_to_dict(row)
            return None

    def requeue_failed(self) -> int:
        """Move all failed posts back to pending status"""

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE post_queue
                SET status = 'pending', updated_at = datetime('now')
                WHERE status = 'failed'
            """)
            count = cursor.rowcount
            conn.commit()

        if count > 0:
            logger.info(f"♻️ Requeued {count} failed posts")
            self._log_activity("requeue_failed", {"count": count}, "success")

        return count


# Singleton instance
_queue_manager: Optional[PostQueueManager] = None


def get_queue_manager(db_path: str = "data/automation/queue.db") -> PostQueueManager:
    """Get or create queue manager singleton"""
    global _queue_manager
    if _queue_manager is None:
        _queue_manager = PostQueueManager(db_path)
    return _queue_manager
