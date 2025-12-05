"""
AI Client with OpenAI for text and Google Imagen 3 for images
Fixed to use production Imagen 3 model ($0.03/image) instead of preview model with quota limits
"""

import asyncio
import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# Try to import Gemini/Imagen
try:
    from google import genai
    from google.genai import types
    from PIL import Image
    from io import BytesIO
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Google Gemini SDK not installed - run: pip install google-genai Pillow")


class OpenAIClient:
    """Async AI client with OpenAI (text) and Google Imagen 3 (images)"""
    
    def __init__(self, config):
        self.config = config
        
        # OpenAI client (for text generation)
        self.openai_client = AsyncOpenAI(api_key=config.openai.api_key)
        
        # Google client (for image generation with Imagen 3)
        self.gemini_client = None
        self.use_images = False
        self.image_model = "imagen-3.0-generate-002"  # Production paid model at $0.03/image
        
        if GEMINI_AVAILABLE:
            # Try config first, then environment variable
            google_api_key = getattr(config.google, 'api_key', None) or os.getenv("GOOGLE_API_KEY")
            
            if google_api_key:
                try:
                    self.gemini_client = genai.Client(api_key=google_api_key)
                    
                    # Check config for image model preference
                    config_model = getattr(config.google, 'image_model', None)
                    if config_model:
                        self.image_model = config_model
                    
                    self.use_images = getattr(config.google, 'use_images', True)
                    logger.info(f"✅ Google AI client initialized - image model: {self.image_model}")
                except Exception as e:
                    logger.error(f"❌ Failed to initialize Google AI client: {e}")
            else:
                logger.warning("⚠️ GOOGLE_API_KEY not found - image generation disabled")
        else:
            logger.warning("⚠️ Google Gemini SDK not installed - image generation disabled")
        
        # Setup image output directory
        self.image_output_dir = Path("data/images")
        self.image_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Cost tracking context
        self.agent_name = "OpenAIClient"
        self._current_batch_id = None
        self._current_post_number = None
    
    def set_agent_name(self, name: str):
        """Set the agent name for cost tracking"""
        self.agent_name = name
    
    def set_context(self, batch_id: str = None, post_number: int = None):
        """Set batch and post context for cost tracking"""
        self._current_batch_id = batch_id
        self._current_post_number = post_number
    
    async def generate(self, 
                      prompt: str,
                      system_prompt: Optional[str] = None,
                      model: Optional[str] = None,
                      temperature: Optional[float] = None,
                      max_tokens: Optional[int] = None,
                      response_format: str = "json") -> Dict[str, Any]:
        """Generate completion from OpenAI API with JSON support"""
        
        model = model or self.config.openai.model
        temperature = temperature or self.config.openai.temperature
        max_tokens = max_tokens or self.config.openai.max_tokens
        
        messages = []
        
        # Add JSON instruction to system prompt
        if system_prompt:
            if response_format == "json":
                system_prompt += "\n\nIMPORTANT: You MUST respond with valid JSON only. No additional text, no markdown formatting, no explanations - just pure, valid JSON."
            messages.append({"role": "system", "content": system_prompt})
        elif response_format == "json":
            messages.append({"role": "system", "content": "You MUST respond with valid JSON only. No additional text, no markdown formatting, no explanations - just pure, valid JSON."})
        
        if response_format == "json":
            prompt += "\n\nRemember: Respond ONLY with valid JSON. No other text."
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            if response_format == "json" and ("gpt-4" in model or "gpt-3.5-turbo" in model):
                kwargs["response_format"] = {"type": "json_object"}
            
            response = await self.openai_client.chat.completions.create(**kwargs)
            
            content = response.choices[0].message.content
            
            if not content:
                logger.error("Received empty content from OpenAI")
                content = "{}" if response_format == "json" else ""
            
            if response_format == "json":
                try:
                    content = content.strip()
                    
                    # Remove markdown code blocks if present
                    if content.startswith("```json"):
                        content = content[7:]
                    elif content.startswith("```"):
                        content = content[3:]
                    
                    if content.endswith("```"):
                        content = content[:-3]
                    
                    content = content.strip()
                    
                    if content:
                        parsed_content = json.loads(content)
                    else:
                        logger.warning("Empty JSON content, returning empty dict")
                        parsed_content = {}
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    parsed_content = self._extract_json_from_text(content)
                    if parsed_content is None:
                        parsed_content = {"error": "Failed to parse response", "raw_content": content}
            else:
                parsed_content = content
            
            result = {
                "content": parsed_content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                },
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason if response.choices else "unknown"
            }
            
            return result
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
    
    async def generate_image(self,
                           prompt: str,
                           base_image_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate image using Google Imagen 3 (Production model)
        
        Cost: $0.03 per image
        Model: imagen-3.0-generate-002
        
        This is the production paid model - no free tier quota limits!
        """
        
        if not self.use_images:
            logger.warning("Image generation disabled in config")
            return {"error": "Image generation disabled", "image_data": None}
        
        if not self.gemini_client:
            logger.error("Google AI client not initialized - check GOOGLE_API_KEY")
            return {"error": "Google AI client not available - GOOGLE_API_KEY missing", "image_data": None}
        
        try:
            import time
            start_time = time.time()
            
            # Determine which API to use based on model
            is_imagen = "imagen" in self.image_model.lower()
            
            if is_imagen:
                # Use Imagen 3 API (generate_images)
                return await self._generate_with_imagen(prompt, start_time)
            else:
                # Use Gemini Flash API (generate_content) - fallback for experimental models
                return await self._generate_with_gemini(prompt, base_image_path, start_time)
            
        except Exception as e:
            logger.error(f"❌ Image generation failed: {str(e)}")
            return {
                "error": str(e),
                "image_data": None,
                "provider": "google",
                "model": self.image_model
            }
    
    async def _generate_with_imagen(self, prompt: str, start_time: float) -> Dict[str, Any]:
        """Generate image using Imagen 3 API - Production paid model at $0.03/image"""
        
        logger.info(f"🎨 Generating image with Imagen 3 ({self.image_model})")
        
        try:
            # Imagen 3 uses generate_images() method
            response = self.gemini_client.models.generate_images(
                model=self.image_model,
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="1:1",  # Options: "1:1", "3:4", "4:3", "9:16", "16:9"
                )
            )
            
            # Extract image bytes from Imagen response
            if response.generated_images and len(response.generated_images) > 0:
                image_data = response.generated_images[0].image.image_bytes
                
                generation_time = time.time() - start_time
                size_mb = len(image_data) / (1024 * 1024)
                
                result = {
                    "image_data": image_data,
                    "generation_time_seconds": round(generation_time, 2),
                    "size_mb": round(size_mb, 3),
                    "provider": "google_imagen",
                    "model": self.image_model,
                    "cost": 0.03  # Imagen 3 costs $0.03 per image
                }
                
                logger.info(f"✅ Imagen 3 image generated in {result['generation_time_seconds']}s ({result['size_mb']}MB) - Cost: $0.03")
                
                return result
            else:
                logger.error("No image data in Imagen 3 response")
                return {"error": "No image generated by Imagen 3", "image_data": None}
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Imagen 3 generation failed: {error_msg}")
            
            # Provide helpful error messages
            if "RESOURCE_EXHAUSTED" in error_msg or "429" in error_msg:
                logger.error("💡 Quota exceeded - check billing is enabled at https://console.cloud.google.com/billing")
            elif "PERMISSION_DENIED" in error_msg or "403" in error_msg:
                logger.error("💡 Permission denied - ensure Generative Language API is enabled")
            elif "INVALID_ARGUMENT" in error_msg:
                logger.error("💡 Invalid argument - check prompt doesn't violate content policies")
            
            return {
                "error": error_msg,
                "image_data": None,
                "provider": "google_imagen",
                "model": self.image_model
            }
    
    async def _generate_with_gemini(self, prompt: str, base_image_path: Optional[str], start_time: float) -> Dict[str, Any]:
        """Generate image using Gemini Flash experimental model (fallback)"""
        
        logger.info(f"🎨 Generating image with Gemini ({self.image_model})")
        
        contents = [prompt]
        
        # Add base image if provided (for image editing)
        if base_image_path and os.path.exists(base_image_path):
            try:
                base_image = Image.open(base_image_path)
                contents.append(base_image)
                logger.info(f"Added base image: {base_image_path}")
            except Exception as e:
                logger.warning(f"Failed to load base image: {e}")
        
        response = self.gemini_client.models.generate_content(
            model=self.image_model,
            contents=contents,
        )
        
        image_data = None
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                image_data = part.inline_data.data
                break
        
        if not image_data:
            logger.error("No image data in Gemini response")
            return {"error": "No image generated by Gemini", "image_data": None}
        
        generation_time = time.time() - start_time
        size_mb = len(image_data) / (1024 * 1024)
        
        result = {
            "image_data": image_data,
            "generation_time_seconds": round(generation_time, 2),
            "size_mb": round(size_mb, 3),
            "provider": "google_gemini",
            "model": self.image_model,
            "cost": 0.039  # Gemini experimental - may be free or low cost
        }
        
        logger.info(f"✅ Gemini image generated in {result['generation_time_seconds']}s ({result['size_mb']}MB)")
        
        return result
    
    def _extract_json_from_text(self, text: str) -> Optional[Dict]:
        """Try to extract JSON from text that may contain other content"""
        import re
        
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        
        return None
    
    async def generate_video(self,
                           prompt: str,
                           duration_seconds: int = 8,
                           aspect_ratio: str = "1:1",
                           include_audio: bool = False) -> Dict[str, Any]:
        """
        Generate video using Google Veo 3.1 Fast (Production model)
        
        Cost: 
        - With audio: $0.15/second ($1.20 for 8 seconds)
        - Without audio: $0.10/second ($0.80 for 8 seconds)
        
        Model: veo-3.0-generate-preview (Veo 3 Fast)
        
        Args:
            prompt: Text description of desired video
            duration_seconds: Video length (default 8, max 8 per generation)
            aspect_ratio: "1:1", "9:16" (vertical), "16:9" (horizontal)
            include_audio: Whether to generate synchronized audio
        """
        
        if not self.gemini_client:
            logger.error("Google AI client not initialized - check GOOGLE_API_KEY")
            return {"error": "Google AI client not available - GOOGLE_API_KEY missing", "video_data": None}
        
        try:
            start_time = time.time()
            
            # Use Veo 3 Fast for cost efficiency
            video_model = "veo-3.0-generate-preview"
            
            logger.info(f"🎬 Generating video with Veo 3 Fast ({video_model})")
            logger.info(f"   Duration: {duration_seconds}s, Aspect: {aspect_ratio}, Audio: {include_audio}")
            
            # Build config
            config_params = {
                "number_of_videos": 1,
                "duration_seconds": duration_seconds,
                "aspect_ratio": aspect_ratio,
            }
            
            # Add audio config if requested
            if include_audio:
                config_params["include_audio"] = True
            
            # Generate video
            response = self.gemini_client.models.generate_videos(
                model=video_model,
                prompt=prompt,
                config=types.GenerateVideosConfig(**config_params)
            )
            
            # Veo returns an operation that we need to poll for completion
            # The response may be an operation or direct result depending on SDK version
            video_data = None
            
            # Check if we got a direct response or need to poll
            if hasattr(response, 'generated_videos') and response.generated_videos:
                # Direct response
                video_data = response.generated_videos[0].video.video_bytes
            elif hasattr(response, 'result'):
                # Operation result
                result = response.result()
                if result.generated_videos:
                    video_data = result.generated_videos[0].video.video_bytes
            else:
                # May need to poll - wait for operation to complete
                logger.info("   Waiting for video generation to complete...")
                
                # Poll with timeout (videos can take 30-60 seconds)
                max_wait = 120  # 2 minutes max
                poll_interval = 5
                waited = 0
                
                while waited < max_wait:
                    await asyncio.sleep(poll_interval)
                    waited += poll_interval
                    
                    # Check if operation is done
                    if hasattr(response, 'done') and response.done():
                        result = response.result()
                        if result.generated_videos:
                            video_data = result.generated_videos[0].video.video_bytes
                        break
                    
                    logger.info(f"   Still generating... ({waited}s)")
                
                if not video_data and waited >= max_wait:
                    return {"error": "Video generation timed out after 2 minutes", "video_data": None}
            
            if not video_data:
                logger.error("No video data in Veo response")
                return {"error": "No video generated by Veo", "video_data": None}
            
            generation_time = time.time() - start_time
            size_mb = len(video_data) / (1024 * 1024)
            
            # Calculate cost
            cost_per_second = 0.15 if include_audio else 0.10
            cost = duration_seconds * cost_per_second
            
            result = {
                "video_data": video_data,
                "generation_time_seconds": round(generation_time, 2),
                "size_mb": round(size_mb, 3),
                "duration_seconds": duration_seconds,
                "aspect_ratio": aspect_ratio,
                "has_audio": include_audio,
                "provider": "google_veo",
                "model": video_model,
                "cost": cost,
                "media_type": "video"
            }
            
            logger.info(f"✅ Veo video generated in {result['generation_time_seconds']}s ({result['size_mb']}MB) - Cost: ${cost:.2f}")
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Veo video generation failed: {error_msg}")
            
            # Provide helpful error messages
            if "RESOURCE_EXHAUSTED" in error_msg or "429" in error_msg:
                logger.error("💡 Quota exceeded - check billing is enabled at https://console.cloud.google.com/billing")
            elif "PERMISSION_DENIED" in error_msg or "403" in error_msg:
                logger.error("💡 Permission denied - ensure Vertex AI API is enabled")
            elif "INVALID_ARGUMENT" in error_msg:
                logger.error("💡 Invalid argument - check prompt doesn't violate content policies")
            
            return {
                "error": error_msg,
                "video_data": None,
                "provider": "google_veo",
                "model": "veo-3.0-generate-preview"
            }
    
    async def close(self):
        """Close the client"""
        await self.openai_client.close()


# Need to import time at module level for the helper methods
import time
