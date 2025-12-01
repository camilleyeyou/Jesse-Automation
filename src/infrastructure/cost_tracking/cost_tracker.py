"""
Cost Tracking for API Calls
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# Pricing per 1M tokens (as of 2024)
PRICING = {
    "openai": {
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4o": {"input": 5.00, "output": 15.00},
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    },
    "google": {
        "gemini-2.5-flash-image": {"per_image": 0.039},
        "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    }
}


@dataclass
class APICall:
    """Record of a single API call"""
    timestamp: str
    agent_name: str
    model: str
    provider: str
    call_type: str  # text_generation, image_generation
    input_tokens: int = 0
    output_tokens: int = 0
    image_count: int = 0
    cost: float = 0.0
    batch_id: Optional[str] = None
    post_number: Optional[int] = None
    generation_time: Optional[float] = None
    success: bool = True
    error: Optional[str] = None


@dataclass
class CostTracker:
    """Tracks costs across all API calls"""
    calls: List[APICall] = field(default_factory=list)
    total_cost: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_images: int = 0
    
    def track_api_call(
        self,
        agent_name: str,
        model: str,
        provider: str,
        call_type: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        image_count: int = 0,
        batch_id: Optional[str] = None,
        post_number: Optional[int] = None,
        generation_time: Optional[float] = None,
        success: bool = True,
        error: Optional[str] = None
    ) -> float:
        """Track an API call and calculate its cost"""
        
        cost = self._calculate_cost(provider, model, call_type, input_tokens, output_tokens, image_count)
        
        call = APICall(
            timestamp=datetime.utcnow().isoformat(),
            agent_name=agent_name,
            model=model,
            provider=provider,
            call_type=call_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            image_count=image_count,
            cost=cost,
            batch_id=batch_id,
            post_number=post_number,
            generation_time=generation_time,
            success=success,
            error=error
        )
        
        self.calls.append(call)
        self.total_cost += cost
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_images += image_count
        
        logger.debug(f"Tracked API call: {agent_name} - ${cost:.4f}")
        
        return cost
    
    def _calculate_cost(
        self,
        provider: str,
        model: str,
        call_type: str,
        input_tokens: int,
        output_tokens: int,
        image_count: int
    ) -> float:
        """Calculate cost for an API call"""
        
        if call_type == "image_generation":
            # Image generation pricing
            if provider == "google" and model in PRICING.get("google", {}):
                return PRICING["google"][model].get("per_image", 0.039) * image_count
            return 0.039 * image_count  # Default Gemini pricing
        
        # Text generation pricing
        provider_pricing = PRICING.get(provider, {})
        model_pricing = provider_pricing.get(model, {"input": 0.15, "output": 0.60})
        
        input_cost = (input_tokens / 1_000_000) * model_pricing.get("input", 0.15)
        output_cost = (output_tokens / 1_000_000) * model_pricing.get("output", 0.60)
        
        return input_cost + output_cost
    
    def get_summary(self) -> Dict[str, Any]:
        """Get cost summary"""
        return {
            "total_cost": round(self.total_cost, 4),
            "total_calls": len(self.calls),
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_images": self.total_images,
            "cost_by_agent": self._get_cost_by_agent(),
            "cost_by_type": self._get_cost_by_type()
        }
    
    def _get_cost_by_agent(self) -> Dict[str, float]:
        """Get cost breakdown by agent"""
        costs = {}
        for call in self.calls:
            if call.agent_name not in costs:
                costs[call.agent_name] = 0.0
            costs[call.agent_name] += call.cost
        return {k: round(v, 4) for k, v in costs.items()}
    
    def _get_cost_by_type(self) -> Dict[str, float]:
        """Get cost breakdown by call type"""
        costs = {"text_generation": 0.0, "image_generation": 0.0}
        for call in self.calls:
            if call.call_type in costs:
                costs[call.call_type] += call.cost
        return {k: round(v, 4) for k, v in costs.items()}
    
    def save_to_file(self, filepath: str = "data/output/cost_report.json") -> None:
        """Save cost report to file"""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "summary": self.get_summary(),
            "calls": [
                {
                    "timestamp": c.timestamp,
                    "agent_name": c.agent_name,
                    "model": c.model,
                    "provider": c.provider,
                    "call_type": c.call_type,
                    "input_tokens": c.input_tokens,
                    "output_tokens": c.output_tokens,
                    "image_count": c.image_count,
                    "cost": round(c.cost, 4),
                    "batch_id": c.batch_id,
                    "success": c.success
                }
                for c in self.calls
            ]
        }
        
        with open(path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Cost report saved to {filepath}")
    
    def reset(self) -> None:
        """Reset all tracking data"""
        self.calls = []
        self.total_cost = 0.0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_images = 0


# Singleton instance
_cost_tracker: Optional[CostTracker] = None


def get_cost_tracker() -> CostTracker:
    """Get or create cost tracker singleton"""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker


def reset_cost_tracker() -> CostTracker:
    """Reset and return a fresh cost tracker"""
    global _cost_tracker
    _cost_tracker = CostTracker()
    return _cost_tracker
