# Jesse Automation — Implementation Roadmap

## Project Overview

Jesse A. Eisenbalm LinkedIn content automation system. Currently operates as a **content factory** (trend → generate → validate → post). The goal is to transform it into a **real autonomous content strategist** that learns from performance, plans ahead, and makes editorial decisions.

**Stack:** Python / FastAPI / SQLite / OpenAI + Gemini / LinkedIn API
**Repository:** github.com/camilleyeyou/Jesse-Automation

---

## Architecture: 4 Layers

| Layer | Name | Status |
|-------|------|--------|
| Layer 1 | **Sense** — trend signals + engagement ingestion | Partial (trends exist, engagement missing) |
| Layer 2 | **Think** — strategic brain + editorial calendar | Not started |
| Layer 3 | **Create** — content generation + validation | Done |
| Layer 4 | **Learn** — performance analysis + strategy refinement | Not started |

---

## Phase 1 — Data Foundation

### 1.1 DB Schema Migrations
- [x] Create `editorial_calendar` table
  ```sql
  CREATE TABLE editorial_calendar (
    id INTEGER PRIMARY KEY,
    scheduled_for DATE,
    theme TEXT,
    format TEXT,
    angle_seed TEXT,
    status TEXT,       -- planned -> generated -> validated -> posted
    post_id INTEGER,
    created_by TEXT     -- 'strategist_agent' or 'manual'
  );
  ```
- [x] Create `strategy_insights` table
  ```sql
  CREATE TABLE strategy_insights (
    id INTEGER PRIMARY KEY,
    insight_type TEXT,      -- format_learning, theme_performance, timing, voice
    observation TEXT,
    confidence REAL,        -- 0.0-1.0, grows with evidence
    evidence_count INTEGER,
    created_at TIMESTAMP,
    last_validated TIMESTAMP
  );
  ```
- [x] Extend `content_memory` with engagement columns
  ```sql
  ALTER TABLE content_memory ADD COLUMN engagement_score REAL;
  ALTER TABLE content_memory ADD COLUMN reactions INTEGER DEFAULT 0;
  ALTER TABLE content_memory ADD COLUMN comments INTEGER DEFAULT 0;
  ALTER TABLE content_memory ADD COLUMN shares INTEGER DEFAULT 0;
  ALTER TABLE content_memory ADD COLUMN impressions INTEGER DEFAULT 0;
  ALTER TABLE content_memory ADD COLUMN performance_fetched_at TIMESTAMP;
  ```

### 1.2 LinkedIn Engagement Ingestion
- [x] Build `PerformanceIngestionJob` service
  - Fetches post analytics weekly via LinkedIn API
  - Key endpoints:
    - `GET /v2/organizationalEntityShareStatistics` — post-level engagement stats
    - `GET /v2/socialActions/{shareUrn}` — comment content + sentiment signals
  - Writes reactions, comments, shares, impressions to `content_memory`
  - Computes `engagement_score` per post
- [x] Store linkedin_post_urn in content_memory when posts are published (already handled by mark_posted_to_linkedin)

### 1.3 Scheduler Hook
- [x] Wire `PerformanceIngestionJob` into APScheduler (runs every Sunday at 6:00 AM)

---

## Phase 2 — Strategic Brain

### 2.1 ContentStrategistAgent (ReAct agent — native tool-calling, no LangGraph dep)
- [x] Build as ReAct agent with tool functions (`src/agents/weekly_strategist.py`)
- [x] Runs Sunday 7:00 AM (after ingestion completes)
- [x] Uses GPT-4o (not mini) for planning; cheaper models execute posts
- [x] Tool functions:
  - `get_recent_performance(days=14)` — reads engagement data from DB
  - `get_theme_distribution(days=7)` — checks recent theme coverage
  - `get_strategy_insights(top=10)` — reads accumulated editorial learnings
  - `get_trending_signals()` — wraps existing MultiTierTrendService
  - `write_weekly_brief(brief: dict)` — commits plan to `editorial_calendar`
- [x] Output: weekly editorial brief with theme distribution, formats, avoid/double-down guidance, content_slots for Mon-Fri
- [x] Added `generate_with_tools()` to OpenAI client for tool-calling support

### 2.2 Orchestrator Wiring
- [x] Update orchestrator to read from `editorial_calendar` instead of generating on-demand
- [x] Each daily run reads today's calendar entry for theme/format/angle_seed
- [x] Pass angle_seed to NewsCuratorAgent to guide trend selection

---

## Phase 3 — Learning System

### 3.1 StrategyRefinementAgent (`src/agents/strategy_refinement.py`)
- [x] Runs every Sunday at 6:30 AM (before ContentStrategistAgent)
- [x] Reads past week's post performance vs historical averages
- [x] Generates 2-3 new `strategy_insights` entries per week
- [x] Updates confidence scores on existing insights with new evidence
- [x] Example insights:
  - "First-person absurdist posts average 3.2x engagement vs third-person (observed 8 weeks)"
  - "AI Safety content gets more comments; AI Slop content gets more shares (6 weeks)"
  - "Posts published Tuesday 9am outperform Thursday 4pm by 40% (12-week avg)"

### 3.2 PortfolioQCAgent (`src/agents/portfolio_qc.py`)
- [x] Runs Friday at 6:00 PM
- [x] Evaluates last 10 posts as a collection (not individually)
- [x] Checks: brand voice consistency, tone drift, reading level trends, positioning adherence
- [x] Writes scored report to DB, flags drift for human review

### 3.3 Strategy Memory Retrieval
- [x] ContentStrategistAgent reads top insights before planning each week (via `get_strategy_insights` tool)
- [x] Insights accumulate over time = Jesse's editorial wisdom

---

## Phase 4 — Full Autonomy

### 4.1 Strategy Dashboard (`dashboard/src/StrategyTab.jsx`)
- [x] React UI showing weekly strategy report
- [x] Theme performance charts (CSS bar charts, color-coded by theme)
- [x] Insights timeline (expandable cards with confidence bars)
- [x] Editorial calendar view (5-day grid with status icons)
- [x] Post performance table (reactions, comments, shares, impressions)
- [x] Manual trigger buttons for all agents (ingestion, refinement, strategist, QC)
- [x] Adaptive weights visualization
- [x] Format A/B testing status with underexplored format alerts

### 4.2 Adaptive Theme Weights
- [x] Theme distribution auto-adjusts based on rolling performance averages
- [x] `compute_adaptive_weights()` in AgentMemory with minimum floor guarantee (10%)
- [x] `get_adaptive_weights` tool available to WeeklyStrategistAgent
- [x] `GET /api/automation/adaptive-weights` API endpoint
- [x] Dashboard visualization of current weights

### 4.3 A/B Format Testing
- [x] `get_format_performance()` tracks engagement by post format
- [x] `get_underexplored_formats()` identifies formats with <3 posts
- [x] WeeklyStrategistAgent prompt instructs it to schedule underexplored formats
- [x] Dashboard shows format performance + underexplored format alerts

---

## Sunday Evening Autonomous Run (Target State)

| Time | Agent | Action |
|------|-------|--------|
| 6:00 AM | PerformanceIngestionJob | Fetch last week's LinkedIn post analytics, write to content_memory |
| 6:30 AM | StrategyRefinementAgent | Compare performance vs averages, generate strategy_insights |
| 7:00 AM | ContentStrategistAgent | ReAct loop: read data → reason → write editorial_calendar for Mon-Fri |
| 7:30 AM | PortfolioQCAgent | Review last 10 posts as collection, score brand consistency |
| Mon-Fri | Existing pipeline | Read today's calendar entry → NewsCurator → Generate → Validate → Post |
| Fri 6 PM | Weekly report | Summary of performance, theme distribution, top insights |

---

## Current System (Already Built)

- Content generation pipeline (orchestrator.py)
- 3 validator personas: SarahChen, JordanPark, MarcusWilliams
- Five Questions strategic spine (THE WHAT, WHAT IF, WHO PROFITS, HOW TO COPE, WHY IT MATTERS)
- Jesse-as-character (not brand) with sentiment range
- Multi-tier trend service (RSS, Brave, pytrends)
- AI-powered news curator with theme classification
- Memory system (agent_memory.py) for avoiding repetition
- Image/video generation and LinkedIn posting
- Auto-CTA first comment after successful publish
- Comment service for LinkedIn API interactions
- APScheduler for automated daily posting

---

## Key Files

| File | Purpose |
|------|---------|
| `src/services/orchestrator.py` | Main content pipeline — where editorial_calendar integration goes |
| `src/agents/content_strategist.py` | Content generation agent + prompts |
| `src/agents/validators/` | Sarah Chen, Jordan Park, Marcus Williams |
| `src/agents/news_curator.py` | AI-powered trend curation |
| `src/infrastructure/trend_service.py` | Multi-tier trend sourcing |
| `src/infrastructure/memory/agent_memory.py` | Memory system + DB tables |
| `src/services/linkedin_poster.py` | LinkedIn post publishing |
| `src/services/linkedin_comment_service.py` | LinkedIn comment API |
| `src/services/scheduler.py` | APScheduler configuration |
| `api/main.py` | FastAPI server + service initialization |
| `prompts/` | Extracted prompt text files |

---

## Conventions

- Word limit: 60-150 words per post
- No hashtags
- No external links in post body (CTA goes in first comment)
- CTA link: jesseaeisenbalm.com
- SQLite DB path: `data/automation/queue.db` (local) / `api/data/automation/queue.db` (API)
- All new tables go in agent_memory.py with safe CREATE IF NOT EXISTS + ALTER TABLE migrations
