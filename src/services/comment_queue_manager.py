"""
Comment Queue Manager — Database Operations for Comment Engagement System

Handles:
- Storing and retrieving comments
- Queue management (pending, approved, posted, rejected)
- Engagement tracking updates
- Analytics queries
"""

import json
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path

from ..models.comment import (
    LinkedInComment,
    CommentOption,
    CommentStyle,
    CommentStatus,
    SourcePostAnalysis,
    PostTone,
    CommentEngagement,
    CommentQueueSummary
)

logger = logging.getLogger(__name__)


class CommentQueueManager:
    """
    Manages the comment queue database
    
    Stores comments through their full lifecycle:
    analyzing → pending → approved → posted (or rejected/failed)
    """
    
    def __init__(self, db_path: str = "data/comments/comment_queue.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        logger.info(f"CommentQueueManager initialized at {self.db_path}")
    
    def _init_database(self):
        """Initialize the database schema"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Main comments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS comments (
                    id TEXT PRIMARY KEY,
                    
                    -- Source post info
                    source_post_url TEXT NOT NULL,
                    source_post_urn TEXT,
                    source_post_content TEXT NOT NULL,
                    source_post_author TEXT,
                    source_post_author_headline TEXT,
                    source_post_topic TEXT,
                    source_post_tone TEXT,
                    source_post_analysis JSON,
                    
                    -- Generated options
                    comment_options JSON,
                    selected_option_id TEXT,
                    final_comment TEXT,
                    
                    -- Status
                    status TEXT DEFAULT 'analyzing',
                    
                    -- Timestamps
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    generated_at TIMESTAMP,
                    approved_at TIMESTAMP,
                    approved_by TEXT,
                    posted_at TIMESTAMP,
                    rejected_at TIMESTAMP,
                    rejection_reason TEXT,
                    
                    -- LinkedIn response
                    comment_urn TEXT,
                    linkedin_response JSON,
                    error_message TEXT,
                    
                    -- Engagement
                    engagement_likes INTEGER DEFAULT 0,
                    engagement_replies INTEGER DEFAULT 0,
                    engagement_last_checked TIMESTAMP,
                    engagement_data JSON
                )
            """)
            
            # Indexes for common queries
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_comments_status ON comments(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_comments_created ON comments(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_comments_posted ON comments(posted_at)")
            
            # Engagement tracking history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS engagement_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    comment_id TEXT NOT NULL,
                    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    likes INTEGER,
                    replies INTEGER,
                    FOREIGN KEY (comment_id) REFERENCES comments(id)
                )
            """)
            
            conn.commit()
            logger.info("Comment database initialized")
    
    def _comment_to_row(self, comment: LinkedInComment) -> Dict[str, Any]:
        """Convert LinkedInComment to database row"""
        
        return {
            "id": comment.id,
            "source_post_url": comment.source_post.url,
            "source_post_urn": comment.source_post.urn,
            "source_post_content": comment.source_post.content,
            "source_post_author": comment.source_post.author_name,
            "source_post_author_headline": comment.source_post.author_headline,
            "source_post_topic": comment.source_post.topic,
            "source_post_tone": comment.source_post.tone.value if comment.source_post.tone else None,
            "source_post_analysis": json.dumps(comment.source_post.model_dump(mode='json')),
            "comment_options": json.dumps([opt.model_dump(mode='json') for opt in comment.comment_options]),
            "selected_option_id": comment.selected_option_id,
            "final_comment": comment.final_comment,
            "status": comment.status.value,
            "created_at": comment.created_at.isoformat(),
            "generated_at": comment.generated_at.isoformat() if comment.generated_at else None,
            "approved_at": comment.approved_at.isoformat() if comment.approved_at else None,
            "approved_by": comment.approved_by,
            "posted_at": comment.posted_at.isoformat() if comment.posted_at else None,
            "rejected_at": comment.rejected_at.isoformat() if comment.rejected_at else None,
            "rejection_reason": comment.rejection_reason,
            "comment_urn": comment.comment_urn,
            "linkedin_response": json.dumps(comment.linkedin_response) if comment.linkedin_response else None,
            "error_message": comment.error_message,
            "engagement_likes": comment.engagement.likes,
            "engagement_replies": comment.engagement.replies,
            "engagement_last_checked": comment.engagement.last_checked_at.isoformat() if comment.engagement.last_checked_at else None,
            "engagement_data": json.dumps(comment.engagement.model_dump(mode='json'))
        }
    
    def _row_to_comment(self, row: sqlite3.Row) -> LinkedInComment:
        """Convert database row to LinkedInComment"""
        
        # Parse source post analysis
        analysis_data = json.loads(row["source_post_analysis"]) if row["source_post_analysis"] else {}
        
        # Handle tone parsing
        tone_str = analysis_data.get("tone", row["source_post_tone"] or "casual")
        try:
            tone = PostTone(tone_str)
        except ValueError:
            tone = PostTone.CASUAL
        
        # Parse recommended styles
        recommended_styles = []
        for style_str in analysis_data.get("recommended_styles", []):
            try:
                recommended_styles.append(CommentStyle(style_str))
            except ValueError:
                continue
        
        source_post = SourcePostAnalysis(
            url=row["source_post_url"],
            urn=row["source_post_urn"],
            content=row["source_post_content"],
            author_name=row["source_post_author"] or "Unknown",
            author_headline=row["source_post_author_headline"],
            topic=row["source_post_topic"] or analysis_data.get("topic", ""),
            tone=tone,
            sentiment=analysis_data.get("sentiment", "neutral"),
            likes_count=analysis_data.get("likes_count"),
            comments_count=analysis_data.get("comments_count"),
            is_trending=analysis_data.get("is_trending", False),
            recommended_styles=recommended_styles,
            topics_to_connect=analysis_data.get("topics_to_connect", []),
            risk_assessment=analysis_data.get("risk_assessment", "low")
        )
        
        # Parse comment options
        options_data = json.loads(row["comment_options"]) if row["comment_options"] else []
        comment_options = []
        for opt_data in options_data:
            try:
                style = CommentStyle(opt_data.get("style", "knowing_nod"))
            except ValueError:
                style = CommentStyle.KNOWING_NOD
            
            comment_options.append(CommentOption(
                id=opt_data.get("id", ""),
                style=style,
                content=opt_data.get("content", ""),
                tone_match_score=float(opt_data.get("tone_match_score", 7.0)),
                brand_alignment_score=float(opt_data.get("brand_alignment_score", 7.0)),
                value_add_score=float(opt_data.get("value_add_score", 7.0)),
                overall_score=float(opt_data.get("overall_score", 7.0)),
                reasoning=opt_data.get("reasoning", ""),
                potential_risks=opt_data.get("potential_risks")
            ))
        
        # Parse engagement
        engagement_data = json.loads(row["engagement_data"]) if row["engagement_data"] else {}
        engagement = CommentEngagement(
            likes=row["engagement_likes"] or 0,
            replies=row["engagement_replies"] or 0,
            last_checked_at=datetime.fromisoformat(row["engagement_last_checked"]) if row["engagement_last_checked"] else None
        )
        
        # Parse linkedin response
        linkedin_response = json.loads(row["linkedin_response"]) if row["linkedin_response"] else None
        
        return LinkedInComment(
            id=row["id"],
            source_post=source_post,
            comment_options=comment_options,
            selected_option_id=row["selected_option_id"],
            final_comment=row["final_comment"],
            status=CommentStatus(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.utcnow(),
            generated_at=datetime.fromisoformat(row["generated_at"]) if row["generated_at"] else None,
            approved_at=datetime.fromisoformat(row["approved_at"]) if row["approved_at"] else None,
            approved_by=row["approved_by"],
            posted_at=datetime.fromisoformat(row["posted_at"]) if row["posted_at"] else None,
            rejected_at=datetime.fromisoformat(row["rejected_at"]) if row["rejected_at"] else None,
            rejection_reason=row["rejection_reason"],
            comment_urn=row["comment_urn"],
            linkedin_response=linkedin_response,
            error_message=row["error_message"],
            engagement=engagement
        )
    
    def save(self, comment: LinkedInComment) -> LinkedInComment:
        """Save or update a comment"""
        
        row = self._comment_to_row(comment)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if exists
            cursor.execute("SELECT id FROM comments WHERE id = ?", (comment.id,))
            exists = cursor.fetchone() is not None
            
            if exists:
                # Update
                set_clause = ", ".join(f"{k} = ?" for k in row.keys() if k != "id")
                values = [v for k, v in row.items() if k != "id"] + [comment.id]
                cursor.execute(f"UPDATE comments SET {set_clause} WHERE id = ?", values)
            else:
                # Insert
                columns = ", ".join(row.keys())
                placeholders = ", ".join("?" * len(row))
                cursor.execute(f"INSERT INTO comments ({columns}) VALUES ({placeholders})", list(row.values()))
            
            conn.commit()
        
        logger.info(f"Saved comment {comment.id} with status {comment.status.value}")
        return comment
    
    def get(self, comment_id: str) -> Optional[LinkedInComment]:
        """Get a comment by ID"""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM comments WHERE id = ?", (comment_id,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_comment(row)
            return None
    
    def get_by_status(self, status: CommentStatus, limit: int = 50) -> List[LinkedInComment]:
        """Get comments by status"""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM comments WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                (status.value, limit)
            )
            
            return [self._row_to_comment(row) for row in cursor.fetchall()]
    
    def get_pending(self, limit: int = 50) -> List[LinkedInComment]:
        """Get pending comments awaiting approval"""
        return self.get_by_status(CommentStatus.PENDING, limit)
    
    def get_approved(self, limit: int = 50) -> List[LinkedInComment]:
        """Get approved comments ready to post"""
        return self.get_by_status(CommentStatus.APPROVED, limit)
    
    def get_posted(self, limit: int = 50) -> List[LinkedInComment]:
        """Get posted comments"""
        return self.get_by_status(CommentStatus.POSTED, limit)
    
    def get_queue(self, limit: int = 50) -> List[LinkedInComment]:
        """Get all comments in the active queue (pending + approved)"""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                """SELECT * FROM comments 
                   WHERE status IN ('pending', 'approved') 
                   ORDER BY created_at DESC LIMIT ?""",
                (limit,)
            )
            
            return [self._row_to_comment(row) for row in cursor.fetchall()]
    
    def get_history(self, limit: int = 50, include_rejected: bool = False) -> List[LinkedInComment]:
        """Get comment history (posted and optionally rejected)"""
        
        statuses = ['posted']
        if include_rejected:
            statuses.extend(['rejected', 'failed'])
        
        placeholders = ", ".join("?" * len(statuses))
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                f"""SELECT * FROM comments 
                    WHERE status IN ({placeholders}) 
                    ORDER BY posted_at DESC NULLS LAST, created_at DESC 
                    LIMIT ?""",
                statuses + [limit]
            )
            
            return [self._row_to_comment(row) for row in cursor.fetchall()]
    
    def approve(self, comment_id: str, approved_by: str, edited_text: Optional[str] = None) -> Optional[LinkedInComment]:
        """Approve a comment"""
        
        comment = self.get(comment_id)
        if not comment:
            return None
        
        comment.approve(approved_by, edited_text)
        return self.save(comment)
    
    def reject(self, comment_id: str, reason: Optional[str] = None) -> Optional[LinkedInComment]:
        """Reject a comment"""
        
        comment = self.get(comment_id)
        if not comment:
            return None
        
        comment.reject(reason)
        return self.save(comment)
    
    def mark_posted(self, comment_id: str, comment_urn: str, linkedin_response: Dict[str, Any]) -> Optional[LinkedInComment]:
        """Mark a comment as posted"""
        
        comment = self.get(comment_id)
        if not comment:
            return None
        
        comment.mark_posted(comment_urn, linkedin_response)
        return self.save(comment)
    
    def mark_failed(self, comment_id: str, error: str) -> Optional[LinkedInComment]:
        """Mark a comment as failed to post"""
        
        comment = self.get(comment_id)
        if not comment:
            return None
        
        comment.mark_failed(error)
        return self.save(comment)
    
    def update_engagement(self, comment_id: str, likes: int, replies: int) -> Optional[LinkedInComment]:
        """Update engagement metrics for a posted comment"""
        
        comment = self.get(comment_id)
        if not comment:
            return None
        
        comment.engagement.update(likes, replies)
        
        # Also log to history
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO engagement_history (comment_id, likes, replies) VALUES (?, ?, ?)",
                (comment_id, likes, replies)
            )
            conn.commit()
        
        return self.save(comment)
    
    def delete(self, comment_id: str) -> bool:
        """Delete a comment"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
            conn.commit()
            deleted = cursor.rowcount > 0
        
        if deleted:
            logger.info(f"Deleted comment {comment_id}")
        
        return deleted
    
    def get_summary(self) -> CommentQueueSummary:
        """Get queue summary statistics"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Count by status
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM comments 
                GROUP BY status
            """)
            
            status_counts = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Engagement totals
            cursor.execute("""
                SELECT 
                    SUM(engagement_likes) as total_likes,
                    SUM(engagement_replies) as total_replies,
                    COUNT(*) as posted_count
                FROM comments 
                WHERE status = 'posted'
            """)
            
            engagement_row = cursor.fetchone()
            total_likes = engagement_row[0] or 0
            total_replies = engagement_row[1] or 0
            posted_count = engagement_row[2] or 0
        
        return CommentQueueSummary(
            total=sum(status_counts.values()),
            pending=status_counts.get("pending", 0),
            approved=status_counts.get("approved", 0),
            posted=status_counts.get("posted", 0),
            rejected=status_counts.get("rejected", 0),
            failed=status_counts.get("failed", 0),
            total_likes=total_likes,
            total_replies=total_replies,
            avg_engagement_rate=(total_likes + total_replies) / posted_count if posted_count > 0 else 0
        )
    
    def get_comments_needing_engagement_check(self, hours_since_last_check: int = 6) -> List[LinkedInComment]:
        """Get posted comments that need engagement checked"""
        
        cutoff = datetime.utcnow() - timedelta(hours=hours_since_last_check)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM comments 
                WHERE status = 'posted' 
                AND (engagement_last_checked IS NULL OR engagement_last_checked < ?)
                ORDER BY posted_at DESC
            """, (cutoff.isoformat(),))
            
            return [self._row_to_comment(row) for row in cursor.fetchall()]


# Singleton instance
_comment_queue_manager: Optional[CommentQueueManager] = None


def get_comment_queue_manager() -> CommentQueueManager:
    """Get or create the singleton CommentQueueManager"""
    global _comment_queue_manager
    if _comment_queue_manager is None:
        _comment_queue_manager = CommentQueueManager()
    return _comment_queue_manager
