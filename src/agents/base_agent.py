"""
Base Agent class for all AI agents
Updated with Jesse A. Eisenbalm Brand Toolkit (January 2026)
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all AI agents"""
    
    # ═══════════════════════════════════════════════════════════════════════════
    # JESSE A. EISENBALM BRAND TOOLKIT - SHARED CONSTANTS
    # ═══════════════════════════════════════════════════════════════════════════
    
    BRAND_COLORS = {
        "primary_blue": "#407CD1",   # Corporate notification at 11 PM
        "cream": "#FCF9EC",          # The premium void
        "coral": "#F96A63",          # Dry lip emergency
        "black": "#000000",          # The eternal abyss
        "white": "#FFFFFF"           # Also acceptable
    }
    
    BRAND_TYPOGRAPHY = {
        "headlines": "Repro Mono Medium",  # Monospace, deliberate, technical
        "body": "Poppins"                  # Bold, SemiBold, Medium, Light
    }
    
    BRAND_MOTIF = "Hexagons (because beeswax)"
    
    BRAND_AI_PHILOSOPHY = {
        "principle": "AI tells as features, not bugs",
        "encouraged": [
            "Em dashes everywhere —",
            "Colons in titles:",
            "Self-aware AI acknowledgment"
        ],
        "embraced_imperfections": [
            "Extra fingers",
            "Mangled, malformed text",
            "Conflicting light sources",
            "Bad proportions and perspectives"
        ]
    }
    
    BRAND_IDENTITY = {
        "name": "Jesse A. Eisenbalm",
        "not_to_be_confused_with": "Jesse Eisenberg (the actor)",
        "note": "He's sick and tired of being mistaken for Jesse Eisenberg"
    }
    
    BRAND_VOICE = {
        "archetype": "The Calm Conspirator",
        "attributes": [
            "Minimal — use half the words, then cut three more",
            "Dry-smart — intellectual without pretension",
            "Unhurried — the only brand NOT urgency-posting",
            "Meme-literate — understand internet culture, never try too hard",
            "Post-post-ironic — so meta it becomes genuine"
        ]
    }
    
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
        return f"You are {self.name}, an AI assistant for Jesse A. Eisenbalm."
    
    def get_brand_context(self) -> str:
        """Get full brand context from config and brand toolkit"""
        brand = self.config.brand
        
        return f"""
═══════════════════════════════════════════════════════════════════════════════
JESSE A. EISENBALM - BRAND CONTEXT
═══════════════════════════════════════════════════════════════════════════════

PRODUCT:
- Name: {brand.product_name}
- Price: {brand.price} (hand-numbered tubes)
- Tagline: "{brand.tagline}"
- Ritual: "{brand.ritual}"
- Target Audience: {brand.target_audience}

BRAND TOOLKIT:

Colors:
- Primary Blue: {self.BRAND_COLORS['primary_blue']} (corporate notification energy)
- Cream: {self.BRAND_COLORS['cream']} (premium void)
- Coral: {self.BRAND_COLORS['coral']} (dry lip emergency)
- Black: {self.BRAND_COLORS['black']} (eternal abyss)

Typography:
- Headlines: {self.BRAND_TYPOGRAPHY['headlines']}
- Body: {self.BRAND_TYPOGRAPHY['body']}

Visual Motif: {self.BRAND_MOTIF}

AI Philosophy: "{self.BRAND_AI_PHILOSOPHY['principle']}"
- Encouraged: {', '.join(self.BRAND_AI_PHILOSOPHY['encouraged'])}

Voice Archetype: {self.BRAND_VOICE['archetype']}
- {chr(10).join('- ' + attr for attr in self.BRAND_VOICE['attributes'])}

Identity Note: {self.BRAND_IDENTITY['name']} — {self.BRAND_IDENTITY['note']}
"""
    
    def get_brand_toolkit_summary(self) -> Dict[str, Any]:
        """Get brand toolkit as a dictionary for programmatic access"""
        return {
            "colors": self.BRAND_COLORS,
            "typography": self.BRAND_TYPOGRAPHY,
            "motif": self.BRAND_MOTIF,
            "ai_philosophy": self.BRAND_AI_PHILOSOPHY,
            "identity": self.BRAND_IDENTITY,
            "voice": self.BRAND_VOICE
        }
    
    def get_color(self, color_name: str) -> str:
        """Get a specific brand color by name"""
        return self.BRAND_COLORS.get(color_name, self.BRAND_COLORS['black'])
    
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
    
    def validate_brand_compliance(self, content: str) -> Dict[str, Any]:
        """
        Basic brand compliance check for content
        Returns dict with compliance notes
        """
        compliance = {
            "has_em_dashes": "—" in content or " — " in content,
            "mentions_product": "jesse" in content.lower() or "eisenbalm" in content.lower(),
            "avoids_eisenberg_confusion": "eisenberg" not in content.lower() or "not" in content.lower(),
            "tone_indicators": {
                "has_minimal_feel": len(content.split()) < 200,
                "avoids_exclamation_spam": content.count("!") < 3,
                "avoids_emoji_spam": sum(1 for c in content if ord(c) > 127000) < 3
            }
        }
        
        compliance["overall"] = (
            compliance["mentions_product"] and 
            compliance["tone_indicators"]["avoids_exclamation_spam"] and
            compliance["tone_indicators"]["avoids_emoji_spam"]
        )
        
        return compliance