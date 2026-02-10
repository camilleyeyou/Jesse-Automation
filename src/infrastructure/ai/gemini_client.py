"""
Google Gemini Image Client
Standalone client for Gemini 2.5 Flash Image generation
"""

import os
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import Gemini
try:
    from google import genai
    from PIL import Image
    from io import BytesIO
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Google Gemini SDK not available - install with: pip install google-genai Pillow")


class GeminiImageClient:
    """Client for Google Gemini/Imagen image generation"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize Gemini client

        Args:
            api_key: Google API key (defaults to GOOGLE_API_KEY env var)
            model: Image model to use (defaults to imagen-3.0-generate-002)
        """
        if not GEMINI_AVAILABLE:
            raise ImportError("Google Gemini SDK not installed")

        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")

        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment")

        self.client = genai.Client(api_key=self.api_key)
        # Use provided model or default to production Imagen 3
        self.model = model or os.getenv("GOOGLE_IMAGE_MODEL", "imagen-3.0-generate-002")

        logger.info(f"GeminiImageClient initialized with model: {self.model}")
    
    def generate_image(
        self,
        prompt: str,
        base_image_path: Optional[str] = None
    ) -> bytes:
        """
        Generate image using Gemini 2.5 Flash Image
        
        Args:
            prompt: Text description of image to generate
            base_image_path: Optional path to base image for editing
            
        Returns:
            Image data as bytes
        """
        
        logger.info(f"Generating image with prompt length: {len(prompt)}")
        
        try:
            contents = [prompt]
            
            # Optional: Include base image for editing/remixing
            if base_image_path and os.path.exists(base_image_path):
                logger.info(f"Using base image: {base_image_path}")
                base_image = Image.open(base_image_path)
                contents.append(base_image)
            
            # Generate image
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
            )
            
            # Extract image bytes from response
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    logger.info("Image generated successfully")
                    return part.inline_data.data
            
            logger.error("No image data in response")
            return None
            
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            raise
    
    def save_image(self, image_data: bytes, output_path: str) -> str:
        """Save image bytes to file"""
        
        try:
            # Ensure directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            image = Image.open(BytesIO(image_data))
            image.save(output_path)
            logger.info(f"Image saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to save image: {e}")
            raise
    
    def generate_and_save(
        self,
        prompt: str,
        output_path: str,
        base_image_path: Optional[str] = None
    ) -> str:
        """Generate image and save to file in one step"""
        
        image_data = self.generate_image(prompt, base_image_path)
        if image_data:
            return self.save_image(image_data, output_path)
        return None
