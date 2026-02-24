#!/usr/bin/env python3
"""
Test script to verify RSS sources are fetching REAL content
Run this after container rebuild to verify sources work
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from infrastructure.source_integrations.rss_source import HuggingFaceSource, RSSSource


async def test_sources():
    """Test that sources fetch real, specific news"""

    print("=" * 80)
    print("TESTING RSS SOURCES - Fetching REAL news")
    print("=" * 80)

    # Test HuggingFace Daily Papers
    print("\n📰 HuggingFace Daily Papers (Tier 1 - Early Detection)")
    print("-" * 80)
    hf_config = {
        'name': 'HuggingFace Daily Papers',
        'type': 'rss',
        'url': 'https://huggingface.co/papers',
        'enabled': True
    }

    try:
        hf_source = HuggingFaceSource(hf_config, tier=1)
        trends = await hf_source.fetch(limit=5)
        print(f"✅ Fetched {len(trends)} real papers from HuggingFace\n")

        for i, trend in enumerate(trends[:3], 1):
            print(f"{i}. {trend.headline}")
            print(f"   URL: {trend.url}")
            print(f"   Summary: {trend.summary[:100]}...")
            print()
    except Exception as e:
        print(f"❌ HuggingFace fetch failed: {e}\n")

    # Test Simon Willison Blog
    print("\n📝 Simon Willison Blog (Tier 2 - Editorial Filter)")
    print("-" * 80)
    sw_config = {
        'name': 'Simon Willison Blog',
        'type': 'rss',
        'url': 'https://simonwillison.net/atom/everything/',
        'enabled': True
    }

    try:
        sw_source = RSSSource(sw_config, tier=2)
        trends = await sw_source.fetch(limit=5)
        print(f"✅ Fetched {len(trends)} real posts from Simon Willison\n")

        for i, trend in enumerate(trends[:3], 1):
            print(f"{i}. {trend.headline}")
            print(f"   URL: {trend.url}")
            print(f"   Summary: {trend.summary[:100]}...")
            print()
    except Exception as e:
        print(f"❌ Simon Willison fetch failed: {e}\n")

    print("=" * 80)
    print("✅ Test complete - Sources should be fetching SPECIFIC, REAL news")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_sources())
