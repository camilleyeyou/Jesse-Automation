"""
Base Agent class for all AI agents
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all AI agents"""
    
    def __init__(self, ai_client, config, name: str = "BaseAgent"):
        """
        Initialize base agent
        
        Args:
            ai_client: OpenAI/Gemini client for API calls
            config: Application configuration
            name: Agent name for logging and tracking
        """
        self.ai_client = ai_client
        self.config = config
        self.name = name
        self.logger = logging.getLogger(f"agent.{name}")
        
        # Set agent name for cost tracking
        if hasattr(ai_client, 'set_agent_name'):
            ai_client.set_agent_name(name)
    
    @abstractmethod
    async def execute(self, *args, **kwargs) -> Dict[str, Any]:
        """Execute the agent's main task - must be implemented by subclasses"""
        pass
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent - override in subclasses"""
        return f"You are {self.name}, an AI assistant."
    
    def get_brand_context(self) -> str:
        """Get brand context from config"""
        brand = self.config.brand
        return f"""
Brand: {brand.product_name}
Price: {brand.price}
Tagline: "{brand.tagline}"
Ritual: "{brand.ritual}"
Target Audience: {brand.target_audience}
Voice: {', '.join(brand.voice_attributes)}
"""
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        response_format: str = "json",
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """Generate a response using the AI client"""
        
        system_prompt = system_prompt or self.get_system_prompt()
        
        self.logger.debug(f"Generating response with prompt length: {len(prompt)}")
        
        result = await self.ai_client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            response_format=response_format,
            temperature=temperature
        )
        
        self.logger.debug(f"Generated response with {result.get('usage', {}).get('total_tokens', 0)} tokens")
        
        return result
    
    def set_context(self, batch_id: str = None, post_number: int = None):
        """Set context for cost tracking"""
        if hasattr(self.ai_client, 'set_context'):
            self.ai_client.set_context(batch_id, post_number)
