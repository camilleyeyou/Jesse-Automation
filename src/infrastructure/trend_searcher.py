"""
Web Search Integration for Jesse A. Eisenbalm
Fetches trending topics for reactive content generation

Uses httpx to call search APIs (Brave, Google, or fallback to curated trends)
"""

import os
import logging
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class TrendSearcher:
    """
    Searches for trending topics to react to
    
    Supports:
    - Brave Search API (recommended - good for news)
    - Fallback to curated trending topics
    """
    
    def __init__(self):
        self.brave_api_key = os.getenv("BRAVE_API_KEY")
        self.logger = logging.getLogger("TrendSearcher")
        
        if self.brave_api_key:
            self.logger.info("✅ Brave Search API configured")
        else:
            self.logger.info("⚠️ No Brave API key - using curated trends")
    
    async def search_trends(self, categories: List[str] = None) -> List[Dict[str, Any]]:
        """
        Search for trending topics
        
        Args:
            categories: List of categories to search (tech, workplace, ai, memes)
        
        Returns:
            List of trending topics with title, snippet, and category
        """
        
        if not categories:
            categories = ["tech_layoffs", "ai_news", "workplace_viral"]
        
        # Define search queries for each category
        category_queries = {
            "tech_layoffs": "tech layoffs today 2026",
            "ai_news": "AI announcement news today",
            "workplace_viral": "viral LinkedIn post this week",
            "tech_culture": "Silicon Valley news today",
            "startup_news": "startup funding layoffs 2026",
            "remote_work": "return to office remote work news"
        }
        
        all_trends = []
        
        for category in categories:
            query = category_queries.get(category, f"{category} news today")
            
            if self.brave_api_key:
                trends = await self._search_brave(query, category)
            else:
                trends = self._get_curated_trends(category)
            
            all_trends.extend(trends)
        
        return all_trends[:6]  # Return top 6 trends
    
    async def _search_brave(self, query: str, category: str) -> List[Dict[str, Any]]:
        """Search using Brave Search API"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.search.brave.com/res/v1/news/search",
                    params={
                        "q": query,
                        "count": 3,
                        "freshness": "pd"  # Past day
                    },
                    headers={
                        "X-Subscription-Token": self.brave_api_key,
                        "Accept": "application/json"
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    
                    trends = []
                    for result in results[:3]:
                        trends.append({
                            "title": result.get("title", ""),
                            "snippet": result.get("description", ""),
                            "url": result.get("url", ""),
                            "category": category,
                            "freshness": "today",
                            "source": "brave_search"
                        })
                    
                    self.logger.info(f"Found {len(trends)} trends for '{query}'")
                    return trends
                else:
                    self.logger.warning(f"Brave search failed: {response.status_code}")
                    return self._get_curated_trends(category)
                    
        except Exception as e:
            self.logger.error(f"Brave search error: {e}")
            return self._get_curated_trends(category)
    
    def _get_curated_trends(self, category: str) -> List[Dict[str, Any]]:
        """
        Fallback curated trends when search isn't available
        These are evergreen workplace/tech themes that are always relevant
        """
        
        curated = {
            "tech_layoffs": [
                {
                    "title": "Another tech company announces restructuring",
                    "snippet": "Tech sector continues to adjust workforce amid AI transformation",
                    "category": "tech_layoffs",
                    "freshness": "evergreen",
                    "source": "curated",
                    "jesse_angle": "Survival mode is the only mode. Your lips shouldn't suffer too."
                }
            ],
            "ai_news": [
                {
                    "title": "AI tools now write most first drafts",
                    "snippet": "Survey shows majority of knowledge workers use AI for initial content",
                    "category": "ai_news", 
                    "freshness": "evergreen",
                    "source": "curated",
                    "jesse_angle": "AI wrote this. AI didn't apply your lip balm. Small victories."
                },
                {
                    "title": "Companies mandate AI adoption",
                    "snippet": "More employers requiring AI tool proficiency from employees",
                    "category": "ai_news",
                    "freshness": "evergreen", 
                    "source": "curated",
                    "jesse_angle": "Learn AI or else. But they can't automate moisturizing your lips. Yet."
                }
            ],
            "workplace_viral": [
                {
                    "title": "LinkedIn hustle post goes viral for wrong reasons",
                    "snippet": "Post bragging about working through illness sparks backlash",
                    "category": "workplace_viral",
                    "freshness": "evergreen",
                    "source": "curated",
                    "jesse_angle": "Hustle culture is a scam. Hydrated lips are not."
                },
                {
                    "title": "Meeting overload hits record levels",
                    "snippet": "Average worker now spends 23 hours per week in meetings",
                    "category": "workplace_viral",
                    "freshness": "evergreen",
                    "source": "curated",
                    "jesse_angle": "You've been on mute for 47 minutes. Apply lip balm. No one will notice."
                }
            ],
            "tech_culture": [
                {
                    "title": "Return to office mandates continue",
                    "snippet": "More companies requiring in-person work despite employee resistance",
                    "category": "tech_culture",
                    "freshness": "evergreen",
                    "source": "curated",
                    "jesse_angle": "Back to the office. Back to fluorescent lighting destroying your skin. Pack lip balm."
                }
            ],
            "startup_news": [
                {
                    "title": "Startup runway anxiety at all-time high",
                    "snippet": "Founders report increased stress about funding in current market",
                    "category": "startup_news",
                    "freshness": "evergreen",
                    "source": "curated",
                    "jesse_angle": "18 months runway. Unknown lip balm remaining. One of these you can fix today."
                }
            ],
            "remote_work": [
                {
                    "title": "Zoom fatigue still affecting workers",
                    "snippet": "Video call exhaustion persists years after remote work boom",
                    "category": "remote_work",
                    "freshness": "evergreen",
                    "source": "curated",
                    "jesse_angle": "Camera on. Mic muted. Lips chapped from nervous licking. We see you."
                }
            ]
        }
        
        return curated.get(category, curated["workplace_viral"])
    
    def format_trends_for_prompt(self, trends: List[Dict[str, Any]]) -> str:
        """Format trends into context for the content generator"""
        
        if not trends:
            return ""
        
        lines = ["TRENDING NOW (react to one of these):\n"]
        
        for i, trend in enumerate(trends[:4], 1):
            lines.append(f"{i}. {trend['title']}")
            if trend.get('snippet'):
                lines.append(f"   → {trend['snippet'][:100]}...")
            if trend.get('jesse_angle'):
                lines.append(f"   → Jesse angle: {trend['jesse_angle']}")
            lines.append("")
        
        lines.append("Pick ONE trend to react to, or ignore all and do your own thing.")
        
        return "\n".join(lines)


# Quick test
if __name__ == "__main__":
    import asyncio
    
    async def test():
        searcher = TrendSearcher()
        trends = await searcher.search_trends(["ai_news", "workplace_viral"])
        print(searcher.format_trends_for_prompt(trends))
    
    asyncio.run(test())