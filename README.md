# Jesse A. Eisenbalm - Autonomous Content Strategist

**AI-powered content strategy, generation, validation, and automated daily posting for LinkedIn.**

> Jesse is not a brand. Jesse is a character — a $8.99 lip balm that became sentient and has opinions about late capitalism.

## What This Does

Jesse doesn't just generate LinkedIn posts. He runs a full editorial operation:

- **Learns from performance** — ingests LinkedIn engagement data weekly
- **Plans ahead** — a strategist agent writes a Mon-Fri editorial calendar every Sunday
- **Remembers his positions** — tracks what he's argued, not just what topics he covered
- **Stays on brand** — portfolio QC agent monitors for voice drift
- **Holds himself accountable** — weekly review compares the plan to what actually posted

## Architecture: The Autonomous Loop

```
Sunday
  06:00 AM  PerformanceIngestionJob    Fetch LinkedIn analytics
  06:30 AM  StrategyRefinementAgent    Generate insights from performance data
  07:00 AM  WeeklyStrategistAgent      Plan Mon-Fri calendar (reads reviews + positions + insights)

Monday-Friday
  06:30 AM  Orchestrator               Read calendar -> enforce theme/format -> inject prior positions
            NewsCuratorAgent           Find trending topic matching today's theme
            ContentStrategistAgent     Generate post with editorial guidance
            3 Validators               Sarah (authenticity), Marcus (craft), Jordan (performance)
            PositionExtractor          Store what Jesse argued (not just the topic)
            LinkedInPoster             Publish with image + CTA comment

Friday
  06:00 PM  PortfolioQCAgent           Brand consistency check across last 10 posts
  06:30 PM  WeeklyReviewAgent          Compare plan vs actual, score adherence
```

## The AI Agents

| Agent | Role | Specialty |
|-------|------|-----------|
| **Weekly Strategist** | Plans the week | ReAct agent with GPT-4o, 6 tools, writes editorial calendar |
| **Strategy Refinement** | Learns from data | Generates 1-3 insights/week from engagement patterns |
| **Content Strategist** | Writes posts | Five Questions framework, Liquid Death creative energy |
| **News Curator** | Picks trends | AI-powered selection from Brave Search + RSS + Google Trends |
| **Position Extractor** | Tracks stances | Extracts what Jesse argued so future posts build on it |
| **Sarah Chen** | Validator | Emotional authenticity + target audience recognition |
| **Marcus Williams** | Validator | Writing craft + conceptual commitment |
| **Jordan Park** | Validator | Platform performance + scroll-stopping hooks |
| **Portfolio QC** | Brand guardian | Detects voice drift, tone monotony, positioning issues |
| **Weekly Review** | Accountability | Compares plan to actual, scores adherence, flags deviations |
| **Image Generator** | Visual creator | Gemini 2.5 Flash branded images |
| **Feedback Aggregator** | Synthesis | Combines validator feedback for revision |
| **Revision Generator** | Editor | Fixes issues while keeping voice |

## The Five Questions (Strategic Spine)

Every post answers exactly one:

1. **THE WHAT** — AI Slop (celebration AND reckoning)
2. **THE WHAT IF** — AI Safety (make technical feel human)
3. **THE WHO PROFITS** — AI Economy (track the money, track the hype)
4. **THE HOW TO COPE** — Rituals (human technologies that outlast digital ones)
5. **THE WHY IT MATTERS** — Humanity (what does it mean to live well?)

## Stack

- **Backend:** Python / FastAPI / SQLite / APScheduler
- **AI:** OpenAI GPT-4o + GPT-4o-mini / Google Gemini 2.5 Flash
- **Frontend:** React / Vite / Tailwind CSS
- **Deployment:** Railway (API) + Vercel (dashboard)
- **APIs:** LinkedIn API / Brave Search / Google Trends

## Project Structure

```
jesse-automation/
├── src/
│   ├── agents/                    # AI Agents
│   │   ├── content_strategist.py  # Post generation (Five Questions + Liquid Death energy)
│   │   ├── news_curator.py        # AI-powered trend selection
│   │   ├── weekly_strategist.py   # ReAct agent for editorial planning
│   │   ├── strategy_refinement.py # Performance pattern analysis
│   │   ├── portfolio_qc.py        # Brand consistency monitoring
│   │   ├── weekly_review.py       # Plan vs actual accountability
│   │   ├── position_extractor.py  # Stance/argument tracking
│   │   ├── image_generator.py     # Gemini-powered branded visuals
│   │   ├── feedback_aggregator.py # Combines validator feedback
│   │   ├── revision_generator.py  # Post revision from feedback
│   │   ├── comment_generator.py   # LinkedIn comment engagement
│   │   └── validators/            # Three-persona validation
│   │       ├── sarah_chen.py      # Emotional authenticity
│   │       ├── marcus_williams.py # Writing craft
│   │       └── jordan_park.py     # Platform performance
│   ├── models/
│   │   ├── post.py
│   │   ├── batch.py
│   │   └── comment.py
│   ├── services/
│   │   ├── orchestrator.py        # Main pipeline (calendar-aware)
│   │   ├── scheduler.py           # APScheduler (daily + weekly jobs)
│   │   ├── performance_ingestion.py # LinkedIn analytics fetcher
│   │   ├── queue_manager.py
│   │   ├── linkedin_poster.py
│   │   └── linkedin_comment_service.py
│   └── infrastructure/
│       ├── ai/openai_client.py    # OpenAI + Gemini client (tool-calling support)
│       ├── memory/agent_memory.py # SQLite memory (positions, calendar, insights)
│       ├── config/config_manager.py
│       ├── trend_service.py       # Multi-tier trend sourcing
│       ├── theme_classifier.py    # AI theme classification
│       └── source_integrations/   # RSS, Brave, Google Trends
├── api/main.py                    # FastAPI server + all endpoints
├── dashboard/src/                 # React dashboard
│   ├── api.js                     # Shared API client with auth
│   ├── App.jsx                    # Main app (Overview, Schedule, Queue, History)
│   ├── StrategyTab.jsx            # Strategy dashboard (calendar, insights, performance)
│   └── CommentsTab.jsx            # Comment engagement UI
├── prompts/                       # Extracted prompt text files
├── config/config.yaml             # 5 themes, 4 sourcing tiers, model config
└── CLAUDE.md                      # Implementation roadmap
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Required:
#   OPENAI_API_KEY
#   GOOGLE_API_KEY
#   BRAVE_API_KEY
#   LINKEDIN_ACCESS_TOKEN
#   LINKEDIN_COMPANY_ID
# Optional:
#   API_SECRET_KEY          (enables API authentication)
#   AUTO_START_SCHEDULER    (set to "true" for autonomous operation)
#   DEFAULT_POST_HOUR       (default: 6)
#   DEFAULT_POST_MINUTE     (default: 30)
#   DEFAULT_TIMEZONE        (default: America/Los_Angeles)
```

### 3. Start the API Server

```bash
cd api
uvicorn main:app --port 8001
```

### 4. Open Dashboard

Deploy `dashboard/` to Vercel or run locally:

```bash
cd dashboard
npm install && npm run dev
```

Set `VITE_API_BASE` to your API URL and `VITE_API_KEY` if auth is enabled.

## API Endpoints

### Automation
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/automation/status` | Full system status |
| POST | `/api/automation/generate-and-post` | Generate fresh content and post to LinkedIn |
| POST | `/api/automation/generate-content` | Generate content to queue |
| POST | `/api/automation/post-now` | Post next queued item |
| POST | `/api/automation/scheduler/start` | Start scheduler |
| POST | `/api/automation/scheduler/stop` | Stop scheduler |
| POST | `/api/automation/schedule` | Set daily post time |

### Strategy (Phase 1-4)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/automation/performance` | Engagement data for recent posts |
| GET | `/api/automation/calendar` | Editorial calendar entries |
| GET | `/api/automation/strategy-insights` | Accumulated editorial learnings |
| GET | `/api/automation/adaptive-weights` | Theme weights + format performance |
| POST | `/api/automation/ingest-performance` | Trigger LinkedIn analytics ingestion |
| POST | `/api/automation/run-refinement` | Trigger strategy refinement |
| POST | `/api/automation/run-strategist` | Trigger weekly planning |
| POST | `/api/automation/run-portfolio-qc` | Trigger brand consistency check |
| POST | `/api/automation/run-weekly-review` | Trigger plan vs actual review |

### Queue
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/automation/queue` | View queued posts |
| POST | `/api/automation/queue/post/{id}` | Post specific item from queue |
| DELETE | `/api/automation/queue/{id}` | Remove from queue |

### LinkedIn
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/automation/linkedin/status` | LinkedIn connection status |
| POST | `/api/automation/linkedin/test` | Test LinkedIn connection |

## Database Schema

SQLite with WAL mode. Key tables:

| Table | Purpose |
|-------|---------|
| `content_memory` | All generated posts + engagement metrics |
| `position_memory` | What Jesse argued (stance, sentiment, key claims) |
| `editorial_calendar` | Weekly plans from strategist agent |
| `strategy_insights` | Accumulated learnings, QC reports, weekly reviews |
| `validator_memory` | Feedback patterns per validator |
| `learning_insights` | Image styles, general learnings |

## Costs

| Service | Cost | Used For |
|---------|------|----------|
| GPT-4o-mini | ~$0.002/post | Content generation, validation, position extraction |
| GPT-4o | ~$0.03/call | Weekly strategist, refinement, QC, review |
| Gemini 2.5 Flash | ~$0.03/image | Branded visual generation |
| Brave Search | Free tier | Trend sourcing |
| **Daily cost** | **~$0.07** | 1 post + image |
| **Weekly cost** | **~$0.50** | 5 posts + Sunday planning + Friday QC/review |

## Security

- Optional API key authentication (`API_SECRET_KEY` env var)
- All database queries use parameterized statements
- LinkedIn tokens read from environment, never logged
- CORS configured for specific origins only

## Conventions

- 40-100 words per post
- No hashtags
- No external links in post body (CTA goes in first comment via jesseaeisenbalm.com)
- Em dashes are Jesse's signature punctuation
- SQLite DB: `data/automation/queue.db`

---

**Made for keeping humans human in an AI world.**
