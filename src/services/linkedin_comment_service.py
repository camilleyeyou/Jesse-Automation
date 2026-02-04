"""
LinkedIn Comment Service — API Integration for Posting & Tracking Comments

Handles:
- Posting comments via LinkedIn API
- Fetching engagement metrics
- Managing rate limits

Requires LinkedIn API access with Community Management API permissions.
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)


@dataclass
class LinkedInCommentConfig:
    """LinkedIn API configuration for comments"""
    access_token: str
    organization_urn: str  # Format: "urn:li:organization:123456"
    api_base_url: str = "https://api.linkedin.com/v2"
    rate_limit_comments_per_day: int = 100


class LinkedInCommentService:
    """
    Service for interacting with LinkedIn's Comment API
    
    Uses the Community Management API to:
    - Post comments on posts
    - Fetch comment engagement
    - Track performance
    """
    
    def __init__(self, config: LinkedInCommentConfig):
        self.config = config
        self.headers = {
            "Authorization": f"Bearer {config.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
            "LinkedIn-Version": "202401"
        }
        
        # Rate limiting tracking
        self._comments_posted_today = 0
        self._last_reset = datetime.utcnow().date()
        
        logger.info(f"LinkedInCommentService initialized for org {config.organization_urn}")
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        
        today = datetime.utcnow().date()
        if today != self._last_reset:
            self._comments_posted_today = 0
            self._last_reset = today
        
        return self._comments_posted_today < self.config.rate_limit_comments_per_day
    
    def _extract_post_urn(self, post_url: str) -> Optional[str]:
        """
        Extract the post URN from a LinkedIn URL
        
        LinkedIn URLs can be in various formats:
        - https://www.linkedin.com/feed/update/urn:li:activity:7123456789/
        - https://www.linkedin.com/posts/username_activity-7123456789-xxxx
        - https://www.linkedin.com/feed/update/urn:li:share:7123456789/
        """
        
        # Try activity URN format
        activity_match = re.search(r'urn:li:activity:(\d+)', post_url)
        if activity_match:
            return f"urn:li:activity:{activity_match.group(1)}"
        
        # Try share URN format
        share_match = re.search(r'urn:li:share:(\d+)', post_url)
        if share_match:
            return f"urn:li:share:{share_match.group(1)}"
        
        # Try activity ID from posts URL
        posts_match = re.search(r'activity-(\d+)', post_url)
        if posts_match:
            return f"urn:li:activity:{posts_match.group(1)}"

        # Try share ID from posts URL (e.g., share-7424606489861869568-xxxx)
        share_posts_match = re.search(r'share-(\d+)', post_url)
        if share_posts_match:
            return f"urn:li:share:{share_posts_match.group(1)}"

        # Try ugcPost format
        ugc_match = re.search(r'urn:li:ugcPost:(\d+)', post_url)
        if ugc_match:
            return f"urn:li:ugcPost:{ugc_match.group(1)}"
        
        logger.warning(f"Could not extract URN from URL: {post_url}")
        return None
    
    async def post_comment(
        self,
        post_url: str,
        comment_text: str,
        post_urn: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Post a comment on a LinkedIn post
        
        Args:
            post_url: URL of the post to comment on
            comment_text: The comment text
            post_urn: Optional URN if already known
            
        Returns:
            Dict with success status, comment_urn, and response data
        """
        
        # Check rate limit
        if not self._check_rate_limit():
            return {
                "success": False,
                "error": "Rate limit exceeded",
                "error_type": "rate_limit"
            }
        
        # Get post URN
        if not post_urn:
            post_urn = self._extract_post_urn(post_url)
        
        if not post_urn:
            return {
                "success": False,
                "error": "Could not extract post URN from URL",
                "error_type": "invalid_url"
            }
        
        # Build the comment payload
        payload = {
            "actor": self.config.organization_urn,
            "object": post_urn,
            "message": {
                "text": comment_text
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                # URL-encode the URN for use in the path
                encoded_urn = quote(post_urn, safe='')
                response = await client.post(
                    f"{self.config.api_base_url}/socialActions/{encoded_urn}/comments",
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )
                
                # Log full response for debugging
                logger.info(f"LinkedIn API response: status={response.status_code}, headers={dict(response.headers)}")
                logger.info(f"LinkedIn API response body: {response.text[:500] if response.text else 'empty'}")

                if response.status_code in [200, 201]:
                    self._comments_posted_today += 1

                    response_data = response.json() if response.text else {}
                    comment_urn = response_data.get("id") or response.headers.get("x-restli-id")

                    logger.info(f"Successfully posted comment on {post_urn}, comment_urn={comment_urn}")
                    
                    return {
                        "success": True,
                        "comment_urn": comment_urn,
                        "post_urn": post_urn,
                        "response": response_data,
                        "status_code": response.status_code
                    }
                else:
                    error_data = response.json() if response.text else {}
                    error_message = error_data.get("message", response.text or "Unknown error")
                    
                    logger.error(f"Failed to post comment: {response.status_code} - {error_message}")
                    
                    return {
                        "success": False,
                        "error": error_message,
                        "error_type": "api_error",
                        "status_code": response.status_code,
                        "response": error_data
                    }
                    
        except httpx.TimeoutException:
            logger.error("LinkedIn API timeout")
            return {
                "success": False,
                "error": "Request timed out",
                "error_type": "timeout"
            }
        except Exception as e:
            logger.error(f"LinkedIn API error: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "exception"
            }
    
    async def get_comment_engagement(self, comment_urn: str) -> Dict[str, Any]:
        """Fetch engagement metrics for a comment"""

        try:
            async with httpx.AsyncClient() as client:
                # URL-encode the URN for use in the path
                encoded_urn = quote(comment_urn, safe='')
                response = await client.get(
                    f"{self.config.api_base_url}/socialActions/{encoded_urn}",
                    headers=self.headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    return {
                        "success": True,
                        "likes": data.get("likesSummary", {}).get("totalLikes", 0),
                        "replies": data.get("commentsSummary", {}).get("totalFirstLevelComments", 0),
                        "raw_data": data
                    }
                else:
                    return {
                        "success": False,
                        "error": f"API returned {response.status_code}",
                        "likes": 0,
                        "replies": 0
                    }
                    
        except Exception as e:
            logger.error(f"Failed to fetch engagement: {e}")
            return {
                "success": False,
                "error": str(e),
                "likes": 0,
                "replies": 0
            }
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status"""
        
        today = datetime.utcnow().date()
        if today != self._last_reset:
            self._comments_posted_today = 0
            self._last_reset = today
        
        return {
            "comments_posted_today": self._comments_posted_today,
            "daily_limit": self.config.rate_limit_comments_per_day,
            "remaining": self.config.rate_limit_comments_per_day - self._comments_posted_today,
            "resets_at": (datetime.utcnow().replace(hour=0, minute=0, second=0) + timedelta(days=1)).isoformat()
        }


class MockLinkedInCommentService:
    """
    Mock service for testing without hitting the real API
    """
    
    def __init__(self, config: Optional[LinkedInCommentConfig] = None):
        self.config = config
        self._comments_posted_today = 0
        logger.info("MockLinkedInCommentService initialized (no real API calls)")
    
    async def post_comment(self, post_url: str, comment_text: str, post_urn: Optional[str] = None) -> Dict[str, Any]:
        """Mock posting a comment"""
        
        import uuid
        comment_urn = f"urn:li:comment:{uuid.uuid4().hex[:12]}"
        
        logger.info(f"[MOCK] Would post comment on {post_url}: {comment_text[:50]}...")
        
        return {
            "success": True,
            "comment_urn": comment_urn,
            "post_urn": post_urn or "urn:li:activity:mock123",
            "response": {"mock": True},
            "status_code": 201
        }
    
    async def get_comment_engagement(self, comment_urn: str) -> Dict[str, Any]:
        """Mock getting engagement"""
        
        import random
        
        return {
            "success": True,
            "likes": random.randint(0, 15),
            "replies": random.randint(0, 3),
            "raw_data": {"mock": True}
        }
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Mock rate limit status"""
        
        return {
            "comments_posted_today": self._comments_posted_today,
            "daily_limit": 100,
            "remaining": 100 - self._comments_posted_today,
            "resets_at": (datetime.utcnow().replace(hour=0, minute=0, second=0) + timedelta(days=1)).isoformat()
        }
