"""
AI Client — unified text generation with provider routing.

Text routing:
  - model name starts with "gpt-"      → OpenAI
  - model name starts with "claude-"   → Anthropic (Fix #2: generator uses Sonnet)
  - model name starts with "gemini-"   → Google (text; images stay on Imagen)

Images still route through Google Imagen via generate_image().
"""

import asyncio
import json
import os
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# Anthropic SDK — required for Fix #2 (generator on Claude Sonnet)
try:
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic SDK not installed - run: pip install anthropic")

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


def _infer_provider(model: str) -> str:
    """Map model name to provider. Used by the unified generate() router."""
    m = (model or "").lower()
    if m.startswith("claude"):
        return "anthropic"
    if m.startswith("gemini"):
        return "google"
    # Default to OpenAI — covers gpt-*, o1-*, and legacy names
    return "openai"


class OpenAIClient:
    """Async AI client with OpenAI (text) and Google Imagen (images)"""
    
    def __init__(self, config):
        self.config = config

        # OpenAI client (for text generation)
        self.openai_client = AsyncOpenAI(api_key=config.openai.api_key)

        # Anthropic client (Fix #2 — generator uses Claude Sonnet)
        self.anthropic_client = None
        anthropic_cfg = getattr(config, 'anthropic', None)
        anthropic_api_key = (
            getattr(anthropic_cfg, 'api_key', None) if anthropic_cfg else None
        ) or os.getenv("ANTHROPIC_API_KEY")
        if ANTHROPIC_AVAILABLE and anthropic_api_key:
            try:
                self.anthropic_client = AsyncAnthropic(api_key=anthropic_api_key)
                logger.info("✅ Anthropic client initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Anthropic client: {e}")
        elif not ANTHROPIC_AVAILABLE:
            logger.warning("⚠️ Anthropic SDK not installed — Claude routing disabled")
        else:
            logger.warning("⚠️ ANTHROPIC_API_KEY not set — Claude routing disabled")

        # Google client (for image generation with Imagen)
        self.gemini_client = None
        self.use_images = False
        # Default image model. imagen-3.0-generate-002 was deprecated upstream (404s
        # with "not found for API version v1beta"). Imagen 4 is the current line.
        self.image_model = "imagen-4.0-fast-generate-001"
        
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
                      response_format = "json") -> Dict[str, Any]:
        """Generate completion from the provider inferred from `model`.

        Routes by model name prefix: gpt-* → OpenAI, claude-* → Anthropic.

        response_format can be:
          - "json" (string) — basic JSON mode (prompt + parse for Anthropic)
          - "text" (string) — plain text
          - dict with "type": "json_schema" — OpenAI-native structured output
            (for Anthropic, treated as prompt-level JSON)
        """

        model = model or self.config.openai.model
        provider = _infer_provider(model)

        if provider == "anthropic":
            return await self._generate_with_anthropic(
                prompt=prompt,
                system_prompt=system_prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
            )

        if provider == "google":
            return await self._generate_with_gemini_text(
                prompt=prompt,
                system_prompt=system_prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
            )

        # OpenAI path — unchanged below
        temperature = temperature if temperature is not None else self.config.openai.temperature
        max_tokens = max_tokens if max_tokens is not None else self.config.openai.max_tokens

        messages = []

        # Determine if we're in JSON mode (string "json" or structured schema dict)
        is_json_mode = response_format == "json" or (isinstance(response_format, dict) and response_format.get("type") in ("json_object", "json_schema"))

        # Add JSON instruction to system prompt
        if system_prompt:
            if is_json_mode:
                system_prompt += "\n\nIMPORTANT: You MUST respond with valid JSON only. No additional text, no markdown formatting, no explanations - just pure, valid JSON."
            messages.append({"role": "system", "content": system_prompt})
        elif is_json_mode:
            messages.append({"role": "system", "content": "You MUST respond with valid JSON only. No additional text, no markdown formatting, no explanations - just pure, valid JSON."})

        if is_json_mode:
            prompt += "\n\nRemember: Respond ONLY with valid JSON. No other text."

        messages.append({"role": "user", "content": prompt})

        try:
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            # Support structured JSON schema (dict) or basic JSON mode (string)
            if isinstance(response_format, dict):
                kwargs["response_format"] = response_format
            elif response_format == "json" and ("gpt-4" in model or "gpt-3.5-turbo" in model):
                kwargs["response_format"] = {"type": "json_object"}
            
            response = await self.openai_client.chat.completions.create(**kwargs)
            
            content = response.choices[0].message.content
            
            if not content:
                logger.error("Received empty content from OpenAI")
                content = "{}" if is_json_mode else ""

            if is_json_mode:
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

    async def generate_with_tools(
        self,
        messages: list,
        tools: list,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Chat completion with tool/function calling — routes by model prefix.

        Callers pass OpenAI-format `tools` and OpenAI-format `messages`. The
        response is always normalised to the OpenAI shape (`message.tool_calls`
        with `function.name` / `function.arguments` JSON string), so agents can
        reuse the same ReAct loop regardless of which provider handles the call.
        Under the hood, Claude models run through Anthropic's tool-use API with
        tools translated on the way in and responses translated on the way out.
        """
        model = model or self.config.openai.model
        provider = _infer_provider(model)

        if provider == "anthropic":
            return await self._generate_with_tools_anthropic(
                messages=messages,
                tools=tools,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        temperature = temperature if temperature is not None else self.config.openai.temperature
        max_tokens = max_tokens or self.config.openai.max_tokens

        try:
            response = await self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            choice = response.choices[0]
            msg = choice.message

            # Build a serialisable assistant message dict
            assistant_msg = {
                "role": "assistant",
                "content": msg.content or "",
            }

            if msg.tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ]

            return {
                "message": assistant_msg,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                },
                "model": response.model,
                "finish_reason": choice.finish_reason,
            }

        except Exception as e:
            logger.error(f"OpenAI tool-calling API error: {e}")
            raise

    async def _generate_with_tools_anthropic(
        self,
        messages: list,
        tools: list,
        model: str,
        temperature: Optional[float],
        max_tokens: Optional[int],
    ) -> Dict[str, Any]:
        """Anthropic tool-use behind the OpenAI-shaped generate_with_tools facade.

        Translates tools in (OpenAI schema → Anthropic schema), messages in
        (role=tool/tool_calls → Anthropic user/assistant content blocks), and
        the response back out (Anthropic tool_use blocks → OpenAI tool_calls).
        """
        if not self.anthropic_client:
            raise RuntimeError(
                "Anthropic client not initialized — set ANTHROPIC_API_KEY or route "
                "tool-calling to an OpenAI model."
            )

        anthropic_cfg = getattr(self.config, "anthropic", None)
        if temperature is None:
            temperature = getattr(anthropic_cfg, "temperature", 0.5) if anthropic_cfg else 0.5
        if max_tokens is None:
            max_tokens = getattr(anthropic_cfg, "max_tokens", 2000) if anthropic_cfg else 2000

        # --- Translate tools: OpenAI schema → Anthropic schema ---
        anthropic_tools = []
        for t in tools or []:
            fn = t.get("function", {}) if isinstance(t, dict) else {}
            anthropic_tools.append({
                "name": fn.get("name", ""),
                "description": fn.get("description", ""),
                "input_schema": fn.get("parameters", {"type": "object", "properties": {}}),
            })

        # --- Translate messages: OpenAI → Anthropic ---
        # Anthropic splits system out of messages; tool results come in as user
        # messages with tool_result content blocks; tool_use lives in assistant
        # content blocks (not a separate tool_calls array).
        system_chunks = []
        anthropic_messages = []
        for msg in messages:
            role = msg.get("role")
            if role == "system":
                if msg.get("content"):
                    system_chunks.append(msg["content"])
                continue

            if role == "tool":
                # Pack tool results into the most recent user turn (or a new one)
                tool_block = {
                    "type": "tool_result",
                    "tool_use_id": msg.get("tool_call_id", ""),
                    "content": msg.get("content", ""),
                }
                if anthropic_messages and anthropic_messages[-1]["role"] == "user" \
                        and isinstance(anthropic_messages[-1].get("content"), list):
                    anthropic_messages[-1]["content"].append(tool_block)
                else:
                    anthropic_messages.append({"role": "user", "content": [tool_block]})
                continue

            if role == "assistant":
                blocks = []
                text = msg.get("content") or ""
                if text:
                    blocks.append({"type": "text", "text": text})
                for tc in msg.get("tool_calls") or []:
                    fn = tc.get("function", {})
                    raw_args = fn.get("arguments", "{}")
                    try:
                        parsed_args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
                    except json.JSONDecodeError:
                        parsed_args = {}
                    blocks.append({
                        "type": "tool_use",
                        "id": tc.get("id", ""),
                        "name": fn.get("name", ""),
                        "input": parsed_args,
                    })
                if not blocks:
                    blocks = [{"type": "text", "text": ""}]
                anthropic_messages.append({"role": "assistant", "content": blocks})
                continue

            # Default: user message
            content = msg.get("content", "")
            anthropic_messages.append({"role": "user", "content": content})

        system_prompt = "\n\n".join(system_chunks).strip() or None

        try:
            response = await self.anthropic_client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                tools=anthropic_tools,
                messages=anthropic_messages,
            )

            # --- Translate response: Anthropic → OpenAI shape ---
            text_parts = []
            tool_calls = []
            for block in response.content or []:
                btype = getattr(block, "type", None)
                if btype == "text":
                    text_parts.append(getattr(block, "text", "") or "")
                elif btype == "tool_use":
                    tool_calls.append({
                        "id": getattr(block, "id", ""),
                        "type": "function",
                        "function": {
                            "name": getattr(block, "name", ""),
                            "arguments": json.dumps(getattr(block, "input", {}) or {}),
                        },
                    })

            assistant_msg: Dict[str, Any] = {
                "role": "assistant",
                "content": "".join(text_parts),
            }
            if tool_calls:
                assistant_msg["tool_calls"] = tool_calls

            usage = getattr(response, "usage", None)
            return {
                "message": assistant_msg,
                "usage": {
                    "prompt_tokens": getattr(usage, "input_tokens", 0) if usage else 0,
                    "completion_tokens": getattr(usage, "output_tokens", 0) if usage else 0,
                    "total_tokens": (
                        (getattr(usage, "input_tokens", 0) + getattr(usage, "output_tokens", 0))
                        if usage else 0
                    ),
                },
                "model": getattr(response, "model", model),
                "finish_reason": getattr(response, "stop_reason", "end_turn"),
            }

        except Exception as e:
            logger.error(f"Anthropic tool-calling API error: {e}")
            raise

    async def _generate_with_anthropic(
        self,
        prompt: str,
        system_prompt: Optional[str],
        model: str,
        temperature: Optional[float],
        max_tokens: Optional[int],
        response_format,
    ) -> Dict[str, Any]:
        """Call Claude via the Anthropic SDK and adapt the response to our shape.

        Shape parity with the OpenAI branch:
          {"content": parsed_json_or_str, "usage": {...}, "model": ..., "finish_reason": ...}
        """
        if not self.anthropic_client:
            raise RuntimeError(
                "Anthropic client not initialized — set ANTHROPIC_API_KEY or remove claude-* "
                "model routing. See Fix #2 in CLAUDE.md."
            )

        anthropic_cfg = getattr(self.config, 'anthropic', None)
        if temperature is None:
            temperature = getattr(anthropic_cfg, 'temperature', 0.9) if anthropic_cfg else 0.9
        if max_tokens is None:
            max_tokens = getattr(anthropic_cfg, 'max_tokens', 600) if anthropic_cfg else 600

        is_json_mode = response_format == "json" or (
            isinstance(response_format, dict)
            and response_format.get("type") in ("json_object", "json_schema")
        )

        # If a JSON schema is provided, inject its shape into the system prompt so
        # Claude knows exactly which fields to return. (Anthropic doesn't have
        # OpenAI's "json_schema" strict mode, but Sonnet follows shape instructions
        # reliably when they're explicit.)
        schema_hint = ""
        if isinstance(response_format, dict) and response_format.get("type") == "json_schema":
            try:
                schema_block = response_format.get("json_schema", {}).get("schema", {})
                schema_hint = (
                    "\n\nYour output MUST be a single JSON object matching this schema:\n"
                    + json.dumps(schema_block, indent=2)
                )
            except Exception:
                schema_hint = ""

        effective_system = system_prompt or ""
        if is_json_mode:
            effective_system += (
                "\n\nCRITICAL: Respond with valid JSON only. No markdown. No prose before or "
                "after. No code fences. Just the JSON object."
            )
        effective_system += schema_hint

        user_prompt = prompt
        if is_json_mode:
            user_prompt += "\n\nReturn ONLY valid JSON. No other text."

        try:
            response = await self.anthropic_client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=effective_system.strip() or None,
                messages=[{"role": "user", "content": user_prompt}],
            )

            # Extract text from the content blocks
            parts = []
            for block in response.content or []:
                text = getattr(block, "text", None)
                if text:
                    parts.append(text)
            raw = "".join(parts).strip()

            if is_json_mode:
                # Strip any markdown code fences Claude might add despite instructions
                cleaned = raw
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                elif cleaned.startswith("```"):
                    cleaned = cleaned[3:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                cleaned = cleaned.strip()

                try:
                    parsed = json.loads(cleaned) if cleaned else {}
                except json.JSONDecodeError:
                    parsed = self._extract_json_from_text(cleaned) or {
                        "error": "Failed to parse Claude JSON", "raw_content": cleaned[:500]
                    }
                content_value: Any = parsed
            else:
                content_value = raw

            usage = getattr(response, "usage", None)
            return {
                "content": content_value,
                "usage": {
                    "prompt_tokens": getattr(usage, "input_tokens", 0) if usage else 0,
                    "completion_tokens": getattr(usage, "output_tokens", 0) if usage else 0,
                    "total_tokens": (
                        (getattr(usage, "input_tokens", 0) + getattr(usage, "output_tokens", 0))
                        if usage else 0
                    ),
                },
                "model": getattr(response, "model", model),
                "finish_reason": getattr(response, "stop_reason", "unknown"),
            }

        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise

    async def embed_text(self, text: str, model: str = "text-embedding-3-small") -> list:
        """Embed text via OpenAI (Fix #4 — retrieval-augmented voice grounding).

        Returns an empty list on failure rather than raising, so retrieval degrades
        gracefully to no-retrieval instead of blocking generation.
        """
        if not text or not text.strip():
            return []
        try:
            response = await self.openai_client.embeddings.create(
                model=model,
                input=text.strip(),
            )
            return list(response.data[0].embedding)
        except Exception as e:
            logger.warning(f"Embedding failed: {e}")
            return []

    async def _generate_with_gemini_text(
        self,
        prompt: str,
        system_prompt: Optional[str],
        model: str,
        temperature: Optional[float],
        max_tokens: Optional[int],
        response_format,
    ) -> Dict[str, Any]:
        """Call Gemini text generation (via google.genai SDK) and adapt to our shape.

        Used by Fix #3 so Jordan Park runs on a different provider from Sarah (Claude)
        and Marcus (GPT-4o) — breaking correlated-judgment convergence.
        """
        if not self.gemini_client:
            raise RuntimeError(
                "Gemini client not initialized — set GOOGLE_API_KEY or remove gemini-* "
                "model routing. See Fix #3 in CLAUDE.md."
            )

        if temperature is None:
            temperature = 0.4  # validators should be more deterministic than the generator
        if max_tokens is None:
            max_tokens = 800

        is_json_mode = response_format == "json" or (
            isinstance(response_format, dict)
            and response_format.get("type") in ("json_object", "json_schema")
        )

        effective_system = system_prompt or ""
        if is_json_mode:
            effective_system += (
                "\n\nCRITICAL: Respond with valid JSON only. No markdown. No prose before or "
                "after. No code fences. Just the JSON object."
            )

        full_prompt = (effective_system + "\n\n" + prompt) if effective_system.strip() else prompt
        if is_json_mode:
            full_prompt += "\n\nReturn ONLY valid JSON. No other text."

        # If the caller passed a json_schema response_format, pin Gemini's output
        # shape using response_schema. Without this, Gemini returns JSON but with
        # whatever key names it prefers — which blanks out downstream parsers
        # (observed: Jordan's q1_insight/q2_surprise_moment/etc. came back as {}).
        gemini_schema = None
        if isinstance(response_format, dict) and response_format.get("type") == "json_schema":
            try:
                gemini_schema = response_format.get("json_schema", {}).get("schema")
            except Exception:
                gemini_schema = None

        try:
            # google.genai's generate_content is sync — run in a worker thread
            # to keep our async call chain non-blocking.
            def _call():
                config_obj = None
                try:
                    from google.genai import types as _types
                    config_kwargs = dict(
                        temperature=temperature,
                        max_output_tokens=max_tokens,
                        response_mime_type="application/json" if is_json_mode else None,
                    )
                    if gemini_schema is not None and is_json_mode:
                        config_kwargs["response_schema"] = gemini_schema
                    config_obj = _types.GenerateContentConfig(**config_kwargs)
                except Exception:
                    config_obj = None
                kwargs = {"model": model, "contents": full_prompt}
                if config_obj is not None:
                    kwargs["config"] = config_obj
                return self.gemini_client.models.generate_content(**kwargs)

            response = await asyncio.to_thread(_call)

            # Extract text
            raw = ""
            try:
                raw = (response.text or "").strip()
            except Exception:
                # Fallback: walk parts
                try:
                    for part in response.candidates[0].content.parts:
                        t = getattr(part, "text", None)
                        if t:
                            raw += t
                    raw = raw.strip()
                except Exception:
                    raw = ""

            if is_json_mode:
                cleaned = raw
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                elif cleaned.startswith("```"):
                    cleaned = cleaned[3:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                cleaned = cleaned.strip()
                try:
                    parsed = json.loads(cleaned) if cleaned else {}
                except json.JSONDecodeError:
                    parsed = self._extract_json_from_text(cleaned) or {
                        "error": "Failed to parse Gemini JSON", "raw_content": cleaned[:500]
                    }
                content_value: Any = parsed
            else:
                content_value = raw

            # Token usage (best-effort — field names vary by SDK version)
            usage_meta = getattr(response, "usage_metadata", None)
            in_tokens = getattr(usage_meta, "prompt_token_count", 0) if usage_meta else 0
            out_tokens = getattr(usage_meta, "candidates_token_count", 0) if usage_meta else 0

            return {
                "content": content_value,
                "usage": {
                    "prompt_tokens": in_tokens,
                    "completion_tokens": out_tokens,
                    "total_tokens": in_tokens + out_tokens,
                },
                "model": model,
                "finish_reason": "stop",
            }

        except Exception as e:
            logger.error(f"Gemini text API error: {e}")
            raise

    async def generate_image(self,
                           prompt: str,
                           base_image_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate image using Google Imagen (Production model)
        
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
            start_time = time.time()
            
            # Determine which API to use based on model
            is_imagen = "imagen" in self.image_model.lower()
            
            if is_imagen:
                # Use Imagen API (generate_images)
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
        """Generate image using Imagen API - Production paid model at $0.03/image"""
        
        logger.info(f"🎨 Generating image with Imagen ({self.image_model})")
        
        try:
            # Imagen uses generate_images() method
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
                    "cost": 0.03  # Imagen costs $0.03 per image
                }
                
                logger.info(f"✅ Imagen image generated in {result['generation_time_seconds']}s ({result['size_mb']}MB) - Cost: $0.03")
                
                return result
            else:
                logger.error("No image data in Imagen response")
                return {"error": "No image generated by Imagen", "image_data": None}
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Imagen generation failed: {error_msg}")
            
            # Provide helpful error messages
            if "RESOURCE_EXHAUSTED" in error_msg or "429" in error_msg:
                logger.error("💡 Quota exceeded - check billing is enabled at https://console.cloud.google.com/billing")
            elif "PERMISSION_DENIED" in error_msg or "403" in error_msg:
                logger.error("💡 Permission denied - ensure Generative Language API is enabled")
            elif "only available on paid plans" in error_msg:
                logger.error(
                    "💡 Imagen requires a paid Google AI Studio plan. Upgrade at "
                    "https://ai.dev/projects, or set google.use_images=false to skip."
                )
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
                           aspect_ratio: str = "16:9",
                           include_audio: bool = False) -> Dict[str, Any]:
        """
        Generate video using Google Veo 3.1 Fast
        
        Cost (after Sept 2025 price drop):
        - Veo 3.1 Fast with audio: $0.15/second ($1.20 for 8 seconds)
        - Veo 3.1 Fast without audio: $0.10/second ($0.80 for 8 seconds)
        
        Model: veo-3.1-fast-generate-preview
        
        Args:
            prompt: Text description of desired video
            duration_seconds: Video length (4, 6, or 8 seconds - default 8)
            aspect_ratio: "16:9" (landscape), "9:16" (vertical/portrait)
            include_audio: Whether to generate synchronized audio
        """
        
        if not self.gemini_client:
            logger.error("Google AI client not initialized - check GOOGLE_API_KEY")
            return {"error": "Google AI client not available - GOOGLE_API_KEY missing", "video_data": None}
        
        try:
            start_time = time.time()
            
            # Use Veo 3.1 Fast for cost efficiency ($0.10/sec without audio, $0.15/sec with audio)
            # Standard Veo 3.1 is $0.20/sec without audio, $0.40/sec with audio
            video_model = "veo-3.1-fast-generate-preview"
            
            logger.info(f"🎬 Generating video with Veo 3.1 Fast ({video_model})")
            logger.info(f"   Duration: {duration_seconds}s, Aspect: {aspect_ratio}, Audio: {include_audio}")
            
            # Build config - Veo uses specific parameters
            config_params = {
                "aspect_ratio": aspect_ratio,
            }
            
            # Add audio config if requested  
            if include_audio:
                config_params["include_audio"] = True
            
            # Generate video - returns a long-running operation
            logger.info("   Waiting for video generation to complete...")
            
            try:
                operation = self.gemini_client.models.generate_videos(
                    model=video_model,
                    prompt=prompt,
                    config=types.GenerateVideosConfig(**config_params)
                )
                
                # Poll the operation until complete using raw API calls
                operation_name = operation.name if hasattr(operation, 'name') else str(operation)
                logger.info(f"   Operation name: {operation_name}")
                logger.info("   Waiting for video generation (this may take 1-3 minutes)...")

                import httpx

                max_wait = 600  # 10 minutes
                poll_interval = 10  # Check every 10 seconds
                waited = 0
                is_done = False
                final_response = None

                # Get API key for polling
                api_key = os.getenv("GOOGLE_API_KEY")
                poll_url = f"https://generativelanguage.googleapis.com/v1beta/{operation_name}?key={api_key}"

                async with httpx.AsyncClient() as client:
                    while waited < max_wait:
                        try:
                            # Poll the operation status
                            poll_response = await client.get(poll_url, timeout=30.0)

                            if poll_response.status_code == 200:
                                op_data = poll_response.json()
                                is_done = op_data.get("done", False)

                                if is_done:
                                    logger.info(f"   Video generation completed after {waited}s!")
                                    final_response = op_data.get("response", {})
                                    break

                                # Check for error
                                if "error" in op_data:
                                    error_msg = op_data["error"].get("message", str(op_data["error"]))
                                    logger.error(f"   Video generation error: {error_msg}")
                                    return {"error": f"Video generation failed: {error_msg}", "video_data": None}
                            else:
                                logger.warning(f"   Poll request failed: {poll_response.status_code}")

                        except Exception as poll_err:
                            logger.warning(f"   Poll error: {poll_err}")

                        # Wait before next poll
                        await asyncio.sleep(poll_interval)
                        waited += poll_interval

                        if waited % 30 == 0:  # Log progress every 30 seconds
                            logger.info(f"   Still generating... ({waited}s elapsed)")

                if not is_done:
                    return {"error": "Video generation timed out after 10 minutes", "video_data": None}
                
                video_data = None

                # Extract video from the polling response or operation object
                response = final_response or getattr(operation, 'response', None)

                logger.info(f"   Response type: {type(response)}")
                if isinstance(response, dict):
                    logger.info(f"   Response keys: {list(response.keys())}")
                else:
                    logger.info(f"   Response attributes: {[attr for attr in dir(response) if not attr.startswith('_')] if response else 'None'}")

                if response:
                    # Handle dict response from raw API polling
                    if isinstance(response, dict):
                        # Try multiple response structures:
                        # 1. generateVideoResponse.generatedSamples (actual API response)
                        # 2. generatedVideos (alternative format)
                        generated_samples = []

                        # Check for generateVideoResponse wrapper (actual format from API)
                        gen_video_resp = response.get("generateVideoResponse", {})
                        if gen_video_resp:
                            generated_samples = gen_video_resp.get("generatedSamples", [])
                            logger.info(f"   Found generateVideoResponse with {len(generated_samples)} samples")

                        # Fallback to generatedVideos
                        if not generated_samples:
                            generated_samples = response.get("generatedVideos", [])
                            if generated_samples:
                                logger.info(f"   Found generatedVideos: {len(generated_samples)}")

                        if generated_samples:
                            sample = generated_samples[0]
                            logger.info(f"   Sample structure: {list(sample.keys()) if isinstance(sample, dict) else type(sample)}")

                            # Video data is in sample.video.uri
                            video_obj = sample.get("video", sample) if isinstance(sample, dict) else sample
                            video_uri = video_obj.get("uri") if isinstance(video_obj, dict) else None

                            if video_uri:
                                logger.info(f"   Found video URI: {video_uri}")
                                video_data = await self._download_video(video_uri)
                            else:
                                logger.warning(f"   No URI in video object: {video_obj}")
                        else:
                            logger.warning(f"   No video samples found in dict response: {list(response.keys())}")

                    # Handle SDK object response
                    elif hasattr(response, 'generated_videos') and response.generated_videos:
                        logger.info(f"   Found generated_videos (object): {len(response.generated_videos)}")
                        video = response.generated_videos[0]

                        if hasattr(video, 'video'):
                            if hasattr(video.video, 'video_bytes') and video.video.video_bytes:
                                video_data = video.video.video_bytes
                                logger.info(f"   Extracted video_bytes: {len(video_data)} bytes")
                            elif hasattr(video.video, 'uri') and video.video.uri:
                                video_uri = video.video.uri
                                logger.info(f"   Found video URI: {video_uri}")
                                video_data = await self._download_video(video_uri)
                        elif hasattr(video, 'video_bytes') and video.video_bytes:
                            video_data = video.video_bytes
                            logger.info(f"   Extracted video_bytes directly: {len(video_data)} bytes")
                        elif hasattr(video, 'uri') and video.uri:
                            video_uri = video.uri
                            logger.info(f"   Found video URI directly: {video_uri}")
                            video_data = await self._download_video(video_uri)
                    else:
                        logger.warning(f"   Unknown response format")
                        # Try to find video data in other attributes
                        if hasattr(response, 'video_bytes') and response.video_bytes:
                            video_data = response.video_bytes
                        elif hasattr(response, 'uri') and response.uri:
                            video_data = await self._download_video(response.uri)
                else:
                    logger.error(f"   No response from operation")

                if not video_data:
                    logger.error("No video data extracted from Veo response")
                    logger.info(f"   Full response: {response}")
                    return {"error": "No video generated by Veo", "video_data": None}
                    
            except Exception as gen_error:
                logger.error(f"   Error generating video: {gen_error}")
                import traceback
                traceback.print_exc()
                return {"error": f"Error generating video: {gen_error}", "video_data": None}
            
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
                "model": "veo-3.1-fast-generate-preview"
            }
    
    async def _download_video(self, uri: str) -> Optional[bytes]:
        """Download video from Google Cloud Storage URI with redirect support"""
        try:
            import httpx

            # The URI might be a GCS URI or a direct download URL
            if uri.startswith("gs://"):
                # Convert GCS URI to download URL
                # gs://bucket/path -> https://storage.googleapis.com/bucket/path
                uri = uri.replace("gs://", "https://storage.googleapis.com/")

            # Add API key for Google GenAI URLs (required for authentication)
            if "generativelanguage.googleapis.com" in uri:
                api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
                if api_key and "key=" not in uri:
                    separator = "&" if "?" in uri else "?"
                    uri = f"{uri}{separator}key={api_key}"

            # Follow redirects to handle 302 responses
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(uri, timeout=60.0)
                response.raise_for_status()
                return response.content

        except Exception as e:
            logger.error(f"Failed to download video from {uri}: {e}")
            return None
    
    async def close(self):
        """Close the client"""
        await self.openai_client.close()