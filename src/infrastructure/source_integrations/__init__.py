"""
Source Integrations Package
============================

Modular source integrations for multi-tier content sourcing.

Each source integration fetches trends from a specific platform
(RSS feeds, APIs, web scraping) and transforms them into TrendingNews objects.
"""

from .base_source import BaseSourceIntegration

__all__ = ['BaseSourceIntegration']
