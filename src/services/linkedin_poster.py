"""
LinkedIn Poster Service
Handles posting content to LinkedIn (Personal + Company Pages)
"""

import os
import json
import logging
import requests
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class LinkedInPoster:
    """Posts content to LinkedIn using the API - supports personal and company pages"""
    
    def __init__(self, config=None):
        self.config = config
        self.access_token = self._get_access_token()
        self.api_base = "https://api.linkedin.com/v2"
        self.user_id = None
        self.company_id = os.getenv("LINKEDIN_COMPANY_ID")  # For company page posting
    
    def _get_access_token(self) -> Optional[str]:
        """Get LinkedIn access token from config or environment"""
        
        # Try environment variable first
        token = os.getenv("LINKEDIN_ACCESS_TOKEN")
        
        if not token and self.config:
            token = getattr(self.config.linkedin, 'access_token', None)
        
        # Try token file
        if not token:
            token_file = Path("config/linkedin_token.json")
            if token_file.exists():
                try:
                    with open(token_file) as f:
                        data = json.load(f)
                        token = data.get("access_token")
                except Exception as e:
                    logger.warning(f"Failed to read token file: {e}")
        
        return token
    
    def is_configured(self) -> bool:
        """Check if LinkedIn is properly configured"""
        return bool(self.access_token)
    
    def test_connection(self) -> Dict[str, Any]:
        """Test the LinkedIn connection"""
        
        if not self.access_token:
            return {
                "success": False,
                "error": "No access token configured"
            }
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "X-Restli-Protocol-Version": "2.0.0"
            }
            
            response = requests.get(
                f"{self.api_base}/userinfo",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.user_id = data.get("sub")
                return {
                    "success": True,
                    "user_id": self.user_id,
                    "name": data.get("name"),
                    "email": data.get("email"),
                    "company_id": self.company_id
                }
            else:
                return {
                    "success": False,
                    "error": f"API returned {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            logger.error(f"LinkedIn connection test failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_user_id(self) -> Optional[str]:
        """Get the authenticated user's LinkedIn ID"""
        
        if self.user_id:
            return self.user_id
        
        result = self.test_connection()
        if result.get("success"):
            return self.user_id
        
        return None
    
    def publish_post(self, content: str, image_path: str = None, 
                     hashtags: list = None, to_company: bool = None) -> Dict[str, Any]:
        """
        Publish a post to LinkedIn
        
        Args:
            content: Post text
            image_path: Optional path to image file
            hashtags: Optional list of hashtags
            to_company: If True, post to company page. If None, auto-detect based on LINKEDIN_COMPANY_ID
        """
        
        if not self.access_token:
            return {
                "success": False,
                "error": "No access token configured"
            }
        
        # Determine if posting to company page
        post_to_company = to_company if to_company is not None else bool(self.company_id)
        
        if post_to_company and not self.company_id:
            return {
                "success": False,
                "error": "Company ID not configured. Set LINKEDIN_COMPANY_ID env var."
            }
        
        if not post_to_company:
            user_id = self.get_user_id()
            if not user_id:
                return {
                    "success": False,
                    "error": "Could not get user ID"
                }
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0"
            }
            
            # Build post text with hashtags
            post_text = content
            if hashtags:
                post_text += "\n\n" + " ".join(f"#{h.replace('#', '')}" for h in hashtags)
            
            # Set author based on posting target
            if post_to_company:
                author = f"urn:li:organization:{self.company_id}"
            else:
                author = f"urn:li:person:{self.user_id}"
            
            # Post body
            post_body = {
                "author": author,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": post_text
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            # Handle image upload if provided
            if image_path and Path(image_path).exists():
                image_result = self._upload_image(image_path, author, headers)
                if image_result.get("success"):
                    post_body["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "IMAGE"
                    post_body["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [{
                        "status": "READY",
                        "media": image_result["asset"]
                    }]
            
            response = requests.post(
                f"{self.api_base}/ugcPosts",
                headers=headers,
                json=post_body,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                post_id = response.headers.get("X-RestLi-Id", response.json().get("id"))
                logger.info(f"Successfully posted to LinkedIn: {post_id}")
                return {
                    "success": True,
                    "post_id": post_id,
                    "url": f"https://www.linkedin.com/feed/update/{post_id}",
                    "posted_to": "company" if post_to_company else "personal"
                }
            else:
                logger.error(f"LinkedIn post failed: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"API returned {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            logger.error(f"LinkedIn post failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _upload_image(self, image_path: str, author: str, headers: dict) -> Dict[str, Any]:
        """Upload an image to LinkedIn"""
        
        try:
            # Register upload
            register_body = {
                "registerUploadRequest": {
                    "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                    "owner": author,
                    "serviceRelationships": [{
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent"
                    }]
                }
            }
            
            response = requests.post(
                f"{self.api_base}/assets?action=registerUpload",
                headers=headers,
                json=register_body,
                timeout=30
            )
            
            if response.status_code != 200:
                return {"success": False, "error": "Failed to register upload"}
            
            upload_data = response.json()
            upload_url = upload_data["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
            asset = upload_data["value"]["asset"]
            
            # Upload the image
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            upload_headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/octet-stream"
            }
            
            upload_response = requests.put(
                upload_url,
                headers=upload_headers,
                data=image_data,
                timeout=60
            )
            
            if upload_response.status_code in [200, 201]:
                return {"success": True, "asset": asset}
            else:
                return {"success": False, "error": f"Upload failed: {upload_response.status_code}"}
                
        except Exception as e:
            logger.error(f"Image upload failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_company_info(self) -> Dict[str, Any]:
        """Get company page info (if configured)"""
        
        if not self.company_id:
            return {"success": False, "error": "No company ID configured"}
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "X-Restli-Protocol-Version": "2.0.0"
            }
            
            response = requests.get(
                f"{self.api_base}/organizations/{self.company_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return {"success": True, "company": response.json()}
            else:
                return {"success": False, "error": f"API returned {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}


class MockLinkedInPoster:
    """Mock poster for testing without API calls"""
    
    def __init__(self, config=None):
        self.config = config
        self.company_id = os.getenv("LINKEDIN_COMPANY_ID")
    
    def is_configured(self) -> bool:
        return True
    
    def test_connection(self) -> Dict[str, Any]:
        return {
            "success": True,
            "user_id": "mock_user_123",
            "name": "Test User",
            "company_id": self.company_id,
            "mock": True
        }
    
    def publish_post(self, content: str, image_path: str = None, 
                     hashtags: list = None, to_company: bool = None) -> Dict[str, Any]:
        post_to = "company" if (to_company or self.company_id) else "personal"
        logger.info(f"[MOCK] Would post to {post_to}: {content[:50]}...")
        return {
            "success": True,
            "post_id": f"mock_post_{datetime.utcnow().timestamp()}",
            "url": "https://linkedin.com/mock-post",
            "posted_to": post_to,
            "mock": True
        }
    
    def get_company_info(self) -> Dict[str, Any]:
        return {
            "success": True,
            "company": {"name": "Mock Company"},
            "mock": True
        }