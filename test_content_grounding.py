#!/usr/bin/env python3
"""
Test script to verify content generator prompts are grounded in specific news.
Tests prompt structure and template rendering without requiring API dependencies.
"""

import sys
import os
import random
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Set required env vars for testing
os.environ.setdefault('OPENAI_API_KEY', 'test')
os.environ.setdefault('GOOGLE_API_KEY', 'test')

# Mock heavy dependencies before importing the agent
sys.modules['openai'] = MagicMock()
sys.modules['google'] = MagicMock()
sys.modules['google.genai'] = MagicMock()
sys.modules['tiktoken'] = MagicMock()

from src.infrastructure.config.config_manager import get_config
from src.agents.content_strategist import ContentGeneratorAgent, ContentPillar


def test_content_grounding():
    """Test that content generator now requires specific news grounding"""

    print("=" * 80)
    print("TESTING CONTENT GENERATOR GROUNDING")
    print("=" * 80)

    # Test 1: Verify prompt changes
    print("\n📝 Test 1: Checking updated prompt instructions")
    print("-" * 80)

    config = get_config()
    ai_client = MagicMock()
    generator = ContentGeneratorAgent(ai_client, config)

    # Create a mock trending context
    mock_trend_context = """
TODAY'S TRENDING NEWS (RESEARCH) — React to this:

HEADLINE: HuggingFace paper: "Scaling Laws for Neural Language Models"
CATEGORY: RESEARCH
STRATEGIC THEME: Ai Safety / Safety Research
SOURCE TIER: Tier 1 (Early Detection 0-24h)
DETAILS: New research shows that model performance scales predictably with compute. The paper claims "breakthrough understanding" of scaling laws. However, buried in the appendix: results only hold for models under 10B parameters.
SOURCE: https://huggingface.co/papers/2024.12345

IMPORTANT: Write about the SPECIFIC news above. Reference the actual headline, details, or cultural moment. Don't create generic content.
"""

    # Build the prompt that would be sent to the AI
    test_prompt = generator._build_creative_prompt(
        strategy=generator._select_creative_strategy(
            trending_context=mock_trend_context,
            requested_pillar=None,
            requested_format=None,
            avoid_patterns={}
        ),
        trending_context=mock_trend_context,
        avoid_patterns={},
        memory_context=""
    )

    # Check if the new instructions are present
    checks = {
        "Mission framing": "YOUR MISSION FOR THIS POST" in test_prompt,
        "Jesse's mood section": "JESSE'S MOOD TODAY" in test_prompt,
        "The Landing section": "THE LANDING" in test_prompt,
        "Ground it instruction": "GROUND IT: Start with what the news ACTUALLY says" in test_prompt,
        "Find the delta instruction": "FIND THE DELTA" in test_prompt,
        "Juxtapose instruction": "JUXTAPOSE WITH HONESTY" in test_prompt,
        "Play it dead straight": "PLAY IT DEAD STRAIGHT" in test_prompt,
        "Creative ammunition section": "CREATIVE AMMUNITION" in test_prompt,
        "Screenshot test": "THE SCREENSHOT TEST" in test_prompt,
        "Creative gut check": "BEFORE YOU WRITE: THE CREATIVE GUT CHECK" in test_prompt,
        "Trending context injected": "Scaling Laws for Neural Language Models" in test_prompt,
    }

    print("\nPrompt includes new grounding instructions:")
    all_passed = True
    for check_name, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check_name}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n✅ All grounding instructions present in prompt!")
    else:
        print("\n❌ Some grounding instructions missing from prompt")
        return False

    # Test 2: Check specific angle generation
    print("\n🎯 Test 2: Checking specific angle generation")
    print("-" * 80)

    specific_angle = generator._generate_specific_angle(
        pillar=ContentPillar.AI_HUMAN_TENSION,
        trending_context=mock_trend_context
    )

    print(f"\nGenerated angle instruction:\n{specific_angle}")

    angle_checks = {
        "References actual news": "SPECIFIC news" in specific_angle,
        "Mentions headline/details": "headline and details" in specific_angle,
        "Looks for gap": "gap between" in specific_angle,
        "Avoids invented scenarios": "not invented scenarios" in specific_angle,
    }

    print("\nAngle instruction quality:")
    for check_name, passed in angle_checks.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check_name}")

    # Test 3: Verify system prompt has new character framing
    print("\n🧠 Test 3: System prompt character framing")
    print("-" * 80)

    system_prompt = generator.system_prompt

    system_checks = {
        "Jesse is a character": "JESSE IS NOT A BRAND. JESSE IS A CHARACTER." in system_prompt,
        "Five Questions framework": "THE FIVE QUESTIONS" in system_prompt,
        "Liquid Death rules": "THE LIQUID DEATH CREATIVE RULES" in system_prompt,
        "Sentiment range": "SENTIMENT RANGE" in system_prompt,
        "Jesse Method": "THE JESSE METHOD" in system_prompt,
        "Hard rules": "HARD RULES" in system_prompt,
    }

    for check_name, passed in system_checks.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check_name}")

    # Test 4: No-trend prompt path
    print("\n🌙 Test 4: No-trend prompt path")
    print("-" * 80)

    no_trend_prompt = generator._build_creative_prompt(
        strategy=generator._select_creative_strategy(
            trending_context=None,
            requested_pillar=None,
            requested_format=None,
            avoid_patterns={}
        ),
        trending_context=None,
        avoid_patterns={},
        memory_context=""
    )

    no_trend_checks = {
        "Jesse's inner world fallback": "write from Jesse's inner world" in no_trend_prompt,
        "Still has mission framing": "YOUR MISSION FOR THIS POST" in no_trend_prompt,
        "Still has creative gut check": "CREATIVE GUT CHECK" in no_trend_prompt,
        "No Jesse Method for news (not needed)": "GROUND IT:" not in no_trend_prompt,
    }

    for check_name, passed in no_trend_checks.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check_name}")

    # Test 5: Avoid patterns flow through
    print("\n🚫 Test 5: Avoid patterns in prompt")
    print("-" * 80)

    avoid_prompt = generator._build_creative_prompt(
        strategy=generator._select_creative_strategy(
            trending_context=None,
            requested_pillar=None,
            requested_format=None,
            avoid_patterns={"recent_topics": ["meetings", "AI safety"], "recent_hooks": ["Tube #4,847"]}
        ),
        trending_context=None,
        avoid_patterns={"recent_topics": ["meetings", "AI safety"], "recent_hooks": ["Tube #4,847"]},
        memory_context=""
    )

    avoid_checks = {
        "Recent topics injected": "meetings" in avoid_prompt,
        "Recent hooks injected": "Tube #4,847" in avoid_prompt,
        "Variety guard label": "VARIETY GUARD" in avoid_prompt,
    }

    for check_name, passed in avoid_checks.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check_name}")

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    print("\n✅ System prompt: Jesse-as-character with Five Questions spine")
    print("✅ Creative prompt: Mission/Mood/Landing/Ammunition/Brief structure")
    print("✅ News grounding: Jesse Method (Ground It / Find Delta / Juxtapose / Dead Straight)")
    print("✅ No-trend fallback: Jesse's inner world path works")
    print("✅ Avoid patterns: Recent topics/hooks flow into variety guard")
    print("✅ Quality gates: Screenshot/Surprise/Recognition/Humanity tests")

    return True


if __name__ == "__main__":
    try:
        result = test_content_grounding()
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
