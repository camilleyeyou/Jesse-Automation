"""
LinkedIn Poster Service - FIXED
Handles posting content to LinkedIn (Personal + Company Pages)

FIX: Convert web URLs back to file paths for image upload
"""

import os
import json
import logging
import time
import requests
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from urllib.parse import quote

logger = logging.getLogger(__name__)

# Video upload configuration
VIDEO_UPLOAD_CHUNK_SIZE = 4 * 1024 * 1024  # 4MB chunks (LinkedIn recommended)
VIDEO_POLL_INTERVAL = 5  # seconds between status checks
VIDEO_POLL_MAX_ATTEMPTS = 60  # 5 min timeout (60 * 5 = 300 seconds)
VIDEO_API_VERSION = "202501"  # LinkedIn API version YYYYMM format


def web_url_to_file_path(url: str) -> Optional[str]:
    """
    Convert web URL to local file path.
    
    /images/jesse_xxx.png -> data/images/jesse_xxx.png
    /videos/jesse_xxx.mp4 -> data/images/videos/jesse_xxx.mp4
    """
    if not url:
        return None
    
    # Already a file path
    if url.startswith('data/') or url.startswith('/home/') or url.startswith('./'):
        return url
    
    # Convert web URL to file path
    if url.startswith('/images/'):
        filename = url.replace('/images/', '')
        return f"data/images/{filename}"
    
    if url.startswith('/videos/'):
        filename = url.replace('/videos/', '')
        return f"data/images/videos/{filename}"
    
    # If it's a full URL (http/https), can't convert
    if url.startswith('http://') or url.startswith('https://'):
        return None
    
    return url


class LinkedInPoster:
    """Posts content to LinkedIn using the API - supports personal and company pages"""
    
    def __init__(self, config=None):
        self.config = config
        self.access_token = self._get_access_token()
        self.api_base = "https://api.linkedin.com/v2"
        self.user_id = None
        self.company_id = os.getenv("LINKEDIN_COMPANY_ID")
    
    def _get_access_token(self) -> Optional[str]:
        """Get LinkedIn access token from config or environment"""
        
        token = os.getenv("LINKEDIN_ACCESS_TOKEN")
        
        if not token and self.config:
            token = getattr(self.config.linkedin, 'access_token', None)
        
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
                     hashtags: list = None, to_company: bool = None,
                     video_path: str = None, media_type: str = None) -> Dict[str, Any]:
        """
        Publish a post to LinkedIn with optional image or video

        Args:
            content: Post text
            image_path: Path to image file OR web URL (will be converted)
            hashtags: Optional list of hashtags
            to_company: If True, post to company page
            video_path: Path to video file (alternative to image_path)
            media_type: 'image', 'video', or None (auto-detect from path)
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
            
            # Build post text (no hashtags added - content should be complete)
            post_text = content
            # Only add hashtags if explicitly provided and non-empty
            if hashtags and len(hashtags) > 0:
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
            
            # Determine media type and path
            effective_media_path = video_path or image_path
            actual_media_type = media_type

            # Auto-detect media type from file extension if not specified
            if not actual_media_type and effective_media_path:
                if effective_media_path.endswith('.mp4') or effective_media_path.endswith('.mov'):
                    actual_media_type = 'video'
                elif '/videos/' in effective_media_path:
                    actual_media_type = 'video'
                else:
                    actual_media_type = 'image'

            # Handle media upload if provided
            if effective_media_path:
                # Convert web URL to file path if needed
                actual_file_path = web_url_to_file_path(effective_media_path)

                logger.info(f"Media path provided: {effective_media_path}")
                logger.info(f"Converted to file path: {actual_file_path}")
                logger.info(f"Media type: {actual_media_type}")

                if actual_file_path and Path(actual_file_path).exists():
                    logger.info(f"File exists, uploading: {actual_file_path}")

                    if actual_media_type == 'video':
                        # Upload video using Videos API
                        video_result = self._upload_video(actual_file_path, author, headers)

                        if video_result.get("success"):
                            post_body["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "VIDEO"
                            post_body["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [{
                                "status": "READY",
                                "media": video_result["video_urn"]
                            }]
                            logger.info("Video attached to post")
                        else:
                            logger.error(f"Video upload failed: {video_result.get('error')}")
                            return {
                                "success": False,
                                "error": f"Video upload to LinkedIn failed: {video_result.get('error')}",
                                "details": video_result.get("details")
                            }
                    else:
                        # Upload image using Assets API
                        image_result = self._upload_image(actual_file_path, author, headers)

                        if image_result.get("success"):
                            post_body["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "IMAGE"
                            post_body["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [{
                                "status": "READY",
                                "media": image_result["asset"]
                            }]
                            logger.info("Image attached to post")
                        else:
                            logger.warning(f"Image upload failed: {image_result.get('error')}")
                else:
                    logger.warning(f"Media file not found: {actual_file_path}")
                    # Fail if video was expected - don't silently post without it
                    if actual_media_type == 'video':
                        return {
                            "success": False,
                            "error": f"Video file not found: {actual_file_path}. Railway ephemeral storage may have deleted it on restart."
                        }
            
            response = requests.post(
                f"{self.api_base}/ugcPosts",
                headers=headers,
                json=post_body,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                post_id = response.headers.get("X-RestLi-Id", response.json().get("id"))
                logger.info(f"Successfully posted to LinkedIn: {post_id}")
                media_category = post_body["specificContent"]["com.linkedin.ugc.ShareContent"].get("shareMediaCategory", "NONE")
                return {
                    "success": True,
                    "post_id": post_id,
                    "url": f"https://www.linkedin.com/feed/update/{post_id}",
                    "posted_to": "company" if post_to_company else "personal",
                    "had_image": media_category == "IMAGE",
                    "had_video": media_category == "VIDEO",
                    "media_type": media_category.lower() if media_category != "NONE" else None
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
                return {"success": False, "error": f"Failed to register upload: {response.status_code}"}
            
            upload_data = response.json()
            upload_url = upload_data["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
            asset = upload_data["value"]["asset"]
            
            # Upload the image
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            logger.info(f"Uploading image ({len(image_data)} bytes) to LinkedIn...")
            
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
                logger.info("Image uploaded successfully")
                return {"success": True, "asset": asset}
            else:
                return {"success": False, "error": f"Upload failed: {upload_response.status_code}"}

        except Exception as e:
            logger.error(f"Image upload failed: {e}")
            return {"success": False, "error": str(e)}

    def _wait_for_video_ready(
        self,
        video_urn: str,
        headers: dict,
        max_attempts: int = VIDEO_POLL_MAX_ATTEMPTS,
        poll_interval: int = VIDEO_POLL_INTERVAL
    ) -> Dict[str, Any]:
        """
        Poll LinkedIn until video processing is complete.

        Args:
            video_urn: The video URN returned from upload
            headers: Headers including Authorization and LinkedIn-Version
            max_attempts: Maximum polling attempts (default 60 = 5 min)
            poll_interval: Seconds between polls (default 5)

        Returns:
            Dict with 'success' and 'status' or 'error'
        """
        encoded_urn = quote(video_urn, safe='')
        status_url = f"https://api.linkedin.com/rest/videos/{encoded_urn}"

        for attempt in range(max_attempts):
            try:
                response = requests.get(status_url, headers=headers, timeout=30)

                if response.status_code != 200:
                    logger.warning(f"Video status check failed: {response.status_code}")
                    time.sleep(poll_interval)
                    continue

                video_data = response.json()
                status = video_data.get("status")

                if status == "AVAILABLE":
                    logger.info(f"Video ready after {(attempt + 1) * poll_interval} seconds")
                    return {"success": True, "status": status, "data": video_data}

                if status == "PROCESSING_FAILED":
                    reason = video_data.get("processingFailureReason", "Unknown")
                    return {
                        "success": False,
                        "error": f"Video processing failed: {reason}",
                        "status": status
                    }

                logger.debug(f"Video status: {status}, waiting... (attempt {attempt + 1}/{max_attempts})")
                time.sleep(poll_interval)

            except Exception as e:
                logger.warning(f"Status poll error: {e}")
                time.sleep(poll_interval)

        return {
            "success": False,
            "error": f"Video processing timeout after {max_attempts * poll_interval} seconds"
        }

    def _upload_video(self, video_path: str, author: str, headers: dict) -> Dict[str, Any]:
        """
        Upload a video to LinkedIn using the Videos API.

        LinkedIn Videos API flow:
        1. Initialize upload - get upload instructions
        2. Upload video chunks to provided URLs
        3. Finalize upload with ETags
        4. Poll until video status is AVAILABLE

        Args:
            video_path: Local path to MP4 video file
            author: URN of the author (person or organization)
            headers: Base headers including Authorization

        Returns:
            Dict with 'success', 'video_urn', or 'error'
        """
        try:
            # Step 1: Get file size
            file_size = os.path.getsize(video_path)
            logger.info(f"🎬 Uploading video ({file_size / 1024 / 1024:.2f} MB) to LinkedIn...")

            # Step 2: Initialize upload
            init_body = {
                "initializeUploadRequest": {
                    "owner": author,
                    "fileSizeBytes": file_size,
                    "uploadCaptions": False,
                    "uploadThumbnail": False
                }
            }

            video_headers = {
                **headers,
                "LinkedIn-Version": VIDEO_API_VERSION
            }

            init_response = requests.post(
                "https://api.linkedin.com/rest/videos?action=initializeUpload",
                headers=video_headers,
                json=init_body,
                timeout=30
            )

            if init_response.status_code != 200:
                logger.error(f"Failed to initialize video upload: {init_response.status_code}")
                logger.error(f"Response: {init_response.text}")
                return {
                    "success": False,
                    "error": f"Failed to initialize video upload: {init_response.status_code}",
                    "details": init_response.text
                }

            init_data = init_response.json()["value"]
            video_urn = init_data["video"]
            upload_instructions = init_data["uploadInstructions"]

            logger.info(f"Video URN: {video_urn}")
            logger.info(f"Upload chunks: {len(upload_instructions)}")

            # Step 3: Upload video chunks
            uploaded_part_ids = []
            with open(video_path, "rb") as f:
                for i, instruction in enumerate(upload_instructions):
                    first_byte = instruction["firstByte"]
                    last_byte = instruction["lastByte"]
                    upload_url = instruction["uploadUrl"]

                    # Seek to correct position and read chunk
                    f.seek(first_byte)
                    chunk_size = last_byte - first_byte + 1
                    chunk_data = f.read(chunk_size)

                    logger.info(f"Uploading chunk {i+1}/{len(upload_instructions)} ({chunk_size / 1024 / 1024:.2f} MB)...")

                    # Upload chunk (NO Authorization header for pre-signed URLs)
                    upload_response = requests.put(
                        upload_url,
                        headers={"Content-Type": "application/octet-stream"},
                        data=chunk_data,
                        timeout=120
                    )

                    if upload_response.status_code not in [200, 201]:
                        logger.error(f"Chunk {i+1} upload failed: {upload_response.status_code}")
                        return {
                            "success": False,
                            "error": f"Chunk upload failed: {upload_response.status_code}",
                            "details": upload_response.text
                        }

                    # Capture ETag (remove quotes if present)
                    etag = upload_response.headers.get("ETag", "").strip('"')
                    uploaded_part_ids.append(etag)
                    logger.info(f"Chunk {i+1} uploaded, ETag: {etag[:20]}...")

            # Step 4: Finalize upload
            logger.info("Finalizing video upload...")
            finalize_body = {
                "finalizeUploadRequest": {
                    "video": video_urn,
                    "uploadToken": "",
                    "uploadedPartIds": uploaded_part_ids
                }
            }

            finalize_response = requests.post(
                "https://api.linkedin.com/rest/videos?action=finalizeUpload",
                headers=video_headers,
                json=finalize_body,
                timeout=30
            )

            if finalize_response.status_code not in [200, 202]:
                logger.error(f"Failed to finalize video upload: {finalize_response.status_code}")
                return {
                    "success": False,
                    "error": f"Failed to finalize video upload: {finalize_response.status_code}",
                    "details": finalize_response.text
                }

            # Step 5: Poll for video to be ready
            logger.info("Waiting for video processing...")
            ready_result = self._wait_for_video_ready(video_urn, video_headers)

            if not ready_result.get("success"):
                return ready_result

            logger.info(f"✅ Video uploaded successfully: {video_urn}")
            return {"success": True, "video_urn": video_urn}

        except Exception as e:
            logger.error(f"Video upload failed: {e}")
            import traceback
            traceback.print_exc()
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
                     hashtags: list = None, to_company: bool = None,
                     video_path: str = None, media_type: str = None) -> Dict[str, Any]:
        post_to = "company" if (to_company or self.company_id) else "personal"

        # Determine effective media path and type
        effective_media_path = video_path or image_path
        actual_media_type = media_type

        if not actual_media_type and effective_media_path:
            if effective_media_path.endswith('.mp4') or '/videos/' in effective_media_path:
                actual_media_type = 'video'
            else:
                actual_media_type = 'image'

        # Test the URL conversion
        actual_path = web_url_to_file_path(effective_media_path) if effective_media_path else None
        has_media = actual_path and Path(actual_path).exists()

        logger.info(f"[MOCK] Would post to {post_to}: {content[:50]}...")
        logger.info(f"[MOCK] Media ({actual_media_type}): {effective_media_path} -> {actual_path} (exists: {has_media})")

        return {
            "success": True,
            "post_id": f"mock_post_{datetime.utcnow().timestamp()}",
            "url": "https://linkedin.com/mock-post",
            "posted_to": post_to,
            "had_image": has_media and actual_media_type == 'image',
            "had_video": has_media and actual_media_type == 'video',
            "media_type": actual_media_type if has_media else None,
            "mock": True
        }
    
    def get_company_info(self) -> Dict[str, Any]:
        return {
            "success": True,
            "company": {"name": "Mock Company"},
            "mock": True
        }