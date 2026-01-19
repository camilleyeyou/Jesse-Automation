"""
Trend Scout Agent - The Culture Radar for Jesse A. Eisenbalm
Finds trending topics, news, and cultural moments to react to

Inspired by: Duolingo's unhinged Twitter, Liquid Death's chaos energy, Wendy's roasts
"""

import logging
import random
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TrendingTopic:
    """A trending topic with context for content creation"""
    topic: str
    category: str  # tech_news, meme, cultural_moment, workplace, ai_news
    hook_angle: str  # How Jesse would approach this
    freshness: str  # breaking, today, this_week
    source: str
    jesse_relevance: str  # Why this matters for lip balm existentialism


class TrendScoutAgent:
    """
    The Culture Radar - Scans for trending topics Jesse can react to
    
    Like Duolingo's social team but for existential lip balm.
    We don't just post content - we react to the chaos.
    """
    
    def __init__(self, ai_client, config):
        self.ai_client = ai_client
        self.config = config
        self.logger = logging.getLogger("agent.TrendScout")
        
        # Categories to search
        self.search_categories = {
            "tech_layoffs": [
                "tech layoffs today",
                "company layoffs 2026",
                "startup shutdown"
            ],
            "ai_news": [
                "AI announcement today",
                "ChatGPT news",
                "AI replacing jobs",
                "AI generated content controversy"
            ],
            "workplace_culture": [
                "return to office news",
                "remote work debate",
                "LinkedIn cringe post viral",
                "corporate jargon meme"
            ],
            "tech_culture": [
                "Silicon Valley news today",
                "startup culture viral",
                "tech bro meme trending"
            ],
            "memes_trending": [
                "meme trending today",
                "viral tweet today",
                "trending LinkedIn post"
            ]
        }
        
        # Evergreen angles (when no good trends found)
        self.evergreen_angles = [
            {
                "topic": "Sunday Scaries",
                "category": "workplace",
                "hook_angle": "The existential dread of Monday approaching",
                "freshness": "evergreen",
                "jesse_relevance": "Lip balm as ritual against the void of the work week"
            },
            {
                "topic": "Meeting that could have been an email",
                "category": "workplace",
                "hook_angle": "Time theft disguised as collaboration",
                "freshness": "evergreen",
                "jesse_relevance": "Apply lip balm during meetings you're muted in"
            },
            {
                "topic": "LinkedIn Hustle Culture",
                "category": "cultural_moment",
                "hook_angle": "People bragging about working through illness/vacation",
                "freshness": "evergreen",
                "jesse_relevance": "Counter-programming to productivity poison"
            },
            {
                "topic": "AI Writing Your Emails",
                "category": "ai_news",
                "hook_angle": "When the AI writes better than you do",
                "freshness": "evergreen",
                "jesse_relevance": "At least your lip balm application is still human"
            },
            {
                "topic": "Corporate Buzzword Bingo",
                "category": "workplace",
                "hook_angle": "Synergy, alignment, circle back, low-hanging fruit",
                "freshness": "evergreen",
                "jesse_relevance": "Words that mean nothing, unlike the moisturizing power of beeswax"
            }
        ]
        
        self.logger.info("TrendScout initialized - scanning for cultural chaos")
    
    async def scout_trends(self, search_func=None) -> List[TrendingTopic]:
        """
        Scout for trending topics to react to
        
        Args:
            search_func: Optional async function to search web (e.g., brave_search)
                        If not provided, uses curated evergreen content
        
        Returns:
            List of trending topics with Jesse angles
        """
        
        trends = []
        
        if search_func:
            # Use web search to find real trends
            trends = await self._search_for_trends(search_func)
        
        # If no good trends found, use evergreen angles
        if not trends:
            self.logger.info("Using evergreen angles (no search or no results)")
            trends = self._get_evergreen_trends()
        
        # Add Jesse-specific angles to each trend
        trends = self._add_jesse_angles(trends)
        
        return trends
    
    async def _search_for_trends(self, search_func) -> List[TrendingTopic]:
        """Search web for trending topics"""
        
        trends = []
        
        # Pick 2-3 categories to search
        categories = random.sample(list(self.search_categories.keys()), min(3, len(self.search_categories)))
        
        for category in categories:
            queries = self.search_categories[category]
            query = random.choice(queries)
            
            try:
                self.logger.info(f"Searching: {query}")
                results = await search_func(query)
                
                if results:
                    # Parse results into trends
                    for result in results[:2]:  # Top 2 results per category
                        trend = TrendingTopic(
                            topic=result.get("title", query),
                            category=category,
                            hook_angle="",  # Will be filled by AI
                            freshness="today",
                            source=result.get("url", "web"),
                            jesse_relevance=""  # Will be filled by AI
                        )
                        trends.append(trend)
                        
            except Exception as e:
                self.logger.warning(f"Search failed for {query}: {e}")
                continue
        
        return trends
    
    def _get_evergreen_trends(self) -> List[TrendingTopic]:
        """Get evergreen trends when search isn't available"""
        
        # Pick 3-4 random evergreen angles
        selected = random.sample(self.evergreen_angles, min(4, len(self.evergreen_angles)))
        
        trends = []
        for item in selected:
            trends.append(TrendingTopic(
                topic=item["topic"],
                category=item["category"],
                hook_angle=item["hook_angle"],
                freshness=item["freshness"],
                source="evergreen",
                jesse_relevance=item["jesse_relevance"]
            ))
        
        return trends
    
    def _add_jesse_angles(self, trends: List[TrendingTopic]) -> List[TrendingTopic]:
        """Add Jesse-specific angles to trends that don't have them"""
        
        jesse_angle_templates = [
            "The physical ritual of lip balm in a world of digital chaos",
            "Mortality reminder: your lips will outlast this trending moment",
            "AI can't feel chapped lips (yet)",
            "Stop. Breathe. Apply. Ignore {topic}.",
            "While everyone panics about {topic}, your lips remain moisturized",
            "{topic} won't matter in 100 years. Neither will you. But your lips can feel good right now.",
            "The algorithm pushed {topic} to you. Jesse A. Eisenbalm pushed lip balm to your face. One of these improves your life."
        ]
        
        for trend in trends:
            if not trend.jesse_relevance:
                template = random.choice(jesse_angle_templates)
                trend.jesse_relevance = template.format(topic=trend.topic)
            
            if not trend.hook_angle:
                trend.hook_angle = f"React to {trend.topic} with existential calm"
        
        return trends
    
    def get_reactive_prompt_context(self, trends: List[TrendingTopic]) -> str:
        """Generate context for the content generator about current trends"""
        
        if not trends:
            return ""
        
        trend_descriptions = []
        for i, trend in enumerate(trends, 1):
            trend_descriptions.append(f"""
TREND {i}: {trend.topic}
- Category: {trend.category}
- Freshness: {trend.freshness}
- Hook Angle: {trend.hook_angle}
- Jesse Relevance: {trend.jesse_relevance}
""")
        
        return f"""
═══════════════════════════════════════════════════════════════════════════════
TRENDING NOW - REACT TO THESE (like Duolingo/Liquid Death would)
═══════════════════════════════════════════════════════════════════════════════

{"".join(trend_descriptions)}

REACTIVE CONTENT GUIDELINES:
- Don't just mention the trend - REACT to it with Jesse's worldview
- Be timely but timeless (the post should age well even if trend fades)
- Channel Duolingo's unhinged energy + Liquid Death's absurdist marketing
- Make it feel like Jesse is commenting on the news, not creating content
- The trend is the hook, the existential pivot is the payoff
"""


class HashtagGenerator:
    """
    Generates on-brand hashtags for Jesse A. Eisenbalm
    
    Rules:
    - NO generic #Motivation #Success #Leadership garbage
    - Mix of: brand-specific, trending, absurdist, insider jokes
    - 3-5 hashtags max
    - At least one should be slightly unhinged
    """
    
    def __init__(self):
        # Brand-specific hashtags (always relevant)
        self.brand_hashtags = [
            "JesseAEisenbalm",
            "NotJesseEisenberg",
            "StopBreatheApply",
            "LipBalmForTheDying",
            "PremiumVoid",
            "CalmConspirator",
            "BeeswaxSurvival"
        ]
        
        # Absurdist/unhinged hashtags
        self.absurdist_hashtags = [
            "MoistureInTheVoid",
            "CapitalismButMakeItLipBalm",
            "ExistentialMoisture",
            "HydrationIsResistance",
            "LipsAgainstTheMachine",
            "BalmBeforeTheChaos",
            "MortalityMoisturizer",
            "AnxietyButHydrated",
            "DoomscrollPause",
            "AICannotMoisturize",
            "TouchGrassApplyBalm",
            "DigitalDetoxAnalog"
        ]
        
        # Workplace/tech culture hashtags
        self.workplace_hashtags = [
            "CorporateSurvival",
            "MeetingRecovery",
            "SlackDetox",
            "ZoomLipDamage",
            "LayoffSelfCare",
            "QuietQuittingLoudlyMoisturizing",
            "ReturnToOfficeLips",
            "AIWontReplaceThis",
            "PerMyLastEmail",
            "SundayScaries",
            "MidweekMeltdown"
        ]
        
        # Trending/timely hashtags (rotate these)
        self.timely_hashtags = [
            "2026Mood",
            "TechTwitter",
            "LinkedInMoment",
            "MainCharacterEnergy",
            "ThisIsFineMeme",
            "ActuallyThisIsNotFine"
        ]
    
    def generate_hashtags(
        self, 
        post_content: str, 
        topic_category: str = None,
        include_brand: bool = True,
        include_absurdist: bool = True,
        count: int = 4
    ) -> List[str]:
        """
        Generate hashtags for a post
        
        Args:
            post_content: The post text (to extract relevant tags)
            topic_category: Category of the trending topic (if any)
            include_brand: Whether to include brand hashtags
            include_absurdist: Whether to include absurdist hashtags
            count: Total number of hashtags (3-5 recommended)
        
        Returns:
            List of hashtags (without # symbol)
        """
        
        selected = []
        
        # Always include 1 brand hashtag
        if include_brand:
            selected.append(random.choice(self.brand_hashtags))
        
        # Add 1-2 absurdist hashtags
        if include_absurdist:
            absurdist_count = random.randint(1, 2)
            selected.extend(random.sample(self.absurdist_hashtags, absurdist_count))
        
        # Add category-specific hashtag if relevant
        if topic_category in ["workplace", "tech_news", "ai_news", "workplace_culture"]:
            selected.append(random.choice(self.workplace_hashtags))
        
        # Fill remaining slots with timely hashtags
        remaining = count - len(selected)
        if remaining > 0:
            selected.extend(random.sample(self.timely_hashtags, min(remaining, len(self.timely_hashtags))))
        
        # Shuffle and trim to count
        random.shuffle(selected)
        return selected[:count]


# Export for use in content generator
__all__ = ['TrendScoutAgent', 'HashtagGenerator', 'TrendingTopic']