"""
Image Generator Agent - Creates branded images using Google Gemini
"""

import os
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from PIL import Image
from io import BytesIO
from .base_agent import BaseAgent
from ..models.post import LinkedInPost

logger = logging.getLogger(__name__)


class ImageGeneratorAgent(BaseAgent):
    """Generates branded images for LinkedIn posts using Google Gemini"""
    
    def __init__(self, ai_client, config):
        super().__init__(ai_client, config, name="ImageGenerator")
        
        # Setup image output directory
        self.image_dir = Path("data/images")
        self.image_dir.mkdir(parents=True, exist_ok=True)
    
    def get_system_prompt(self) -> str:
        return f"""You are an expert at creating image prompts for Jesse A. Eisenbalm lip balm brand.

{self.get_brand_context()}

VISUAL STYLE:
- Modern minimalist aesthetic
- Warm, inviting color palette (golds, creams, soft whites)
- Professional but approachable
- Premium feel without being pretentious
- Should feel at home on LinkedIn

IMAGE REQUIREMENTS:
- Clean, professional composition
- Product should be subtly integrated (not the main focus)
- Should complement the post content
- Avoid stock photo clichés
- Think "Apple ad meets Wes Anderson"
"""
    
    async def execute(self, post: LinkedInPost) -> Dict[str, Any]:
        """Generate an image for a LinkedIn post"""
        
        self.set_context(post.batch_id, post.post_number)
        
        # Check if image generation is enabled
        if not self.ai_client.use_images:
            self.logger.info("Image generation disabled, skipping")
            return {"success": False, "reason": "Image generation disabled"}
        
        # First, generate an optimized prompt for the image
        prompt_result = await self._generate_image_prompt(post)
        
        if not prompt_result.get("success"):
            return prompt_result
        
        image_prompt = prompt_result["prompt"]
        image_description = prompt_result["description"]
        
        # Generate the image using Gemini
        try:
            result = await self.ai_client.generate_image(prompt=image_prompt)
            
            if result.get("error") or not result.get("image_data"):
                self.logger.error(f"Image generation failed: {result.get('error')}")
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error"),
                    "prompt": image_prompt
                }
            
            # Save the image
            image_path = self._save_image(result["image_data"], post.id)
            
            # Update post with image data
            post.set_image(
                url=str(image_path),
                prompt=image_prompt,
                description=image_description,
                provider="google_gemini",
                cost=result.get("cost", 0.039)
            )
            
            self.logger.info(f"Generated image for post {post.post_number}: {image_path}")
            
            return {
                "success": True,
                "image_path": str(image_path),
                "prompt": image_prompt,
                "description": image_description,
                "generation_time": result.get("generation_time_seconds"),
                "size_mb": result.get("size_mb"),
                "cost": result.get("cost", 0.039)
            }
            
        except Exception as e:
            self.logger.error(f"Image generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "prompt": image_prompt
            }
    
    async def _generate_image_prompt(self, post: LinkedInPost) -> Dict[str, Any]:
        """Generate an optimized image prompt based on post content"""
        
        prompt = f"""Create an image generation prompt for this LinkedIn post:

POST CONTENT:
{post.content}

CULTURAL REFERENCE: {post.cultural_reference.reference if post.cultural_reference else 'None'}

Create a detailed image prompt that:
1. Complements the post's message and tone
2. Subtly includes or references Jesse A. Eisenbalm lip balm
3. Uses the brand's visual aesthetic (modern, minimal, warm tones)
4. Would look professional on LinkedIn
5. Is specific enough for AI image generation

OUTPUT FORMAT (JSON only):
{{
    "prompt": "<detailed image generation prompt, 50-100 words>",
    "description": "<short description for alt text, 10-20 words>",
    "style_notes": "<brief notes on intended visual style>"
}}"""
        
        try:
            result = await self.generate(prompt)
            content = result.get("content", {})
            
            if isinstance(content, str):
                return {
                    "success": True,
                    "prompt": content,
                    "description": "Jesse A. Eisenbalm branded image"
                }
            
            return {
                "success": True,
                "prompt": content.get("prompt", "A minimalist product shot of premium lip balm"),
                "description": content.get("description", "Jesse A. Eisenbalm branded image")
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate image prompt: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _save_image(self, image_data: bytes, post_id: str) -> Path:
        """Save image data to file"""
        
        filename = f"{post_id}_{uuid.uuid4().hex[:8]}.png"
        filepath = self.image_dir / filename
        
        try:
            image = Image.open(BytesIO(image_data))
            image.save(filepath)
            self.logger.info(f"Saved image to {filepath}")
            return filepath
        except Exception as e:
            self.logger.error(f"Failed to save image: {e}")
            raise
