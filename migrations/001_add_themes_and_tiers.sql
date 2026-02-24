-- Migration: Add Theme and Tier Support
-- Date: 2026-02-24
-- Description: Adds theme/tier tracking to existing tables and creates new tables for source management

-- ============================================================================
-- EXTEND EXISTING TABLES
-- ============================================================================
-- Note: These tables are created dynamically by TrendService and AgentMemory.
-- We use ALTER TABLE ADD COLUMN which is safe and idempotent in SQLite.
-- If the column already exists, SQLite will error but the script continues.

-- Add theme/tier columns to used_topics table (created by TrendService)
-- Check if table exists first, then add columns
ALTER TABLE used_topics ADD COLUMN theme TEXT;
ALTER TABLE used_topics ADD COLUMN sub_theme TEXT;
ALTER TABLE used_topics ADD COLUMN tier INTEGER;
ALTER TABLE used_topics ADD COLUMN source_type TEXT;

-- Add theme/tier columns to content_memory table (created by AgentMemory)
ALTER TABLE content_memory ADD COLUMN theme TEXT;
ALTER TABLE content_memory ADD COLUMN sub_theme TEXT;
ALTER TABLE content_memory ADD COLUMN trend_tier INTEGER;

-- ============================================================================
-- CREATE NEW TABLES
-- ============================================================================

-- Track all content sources (API, RSS, scraping) with health metrics
CREATE TABLE IF NOT EXISTS trend_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL UNIQUE,
    source_type TEXT NOT NULL,  -- 'api', 'rss', 'scrape', 'newsletter'
    tier INTEGER NOT NULL,       -- 1-4 sourcing tier
    enabled BOOLEAN DEFAULT TRUE,
    api_endpoint TEXT,
    refresh_minutes INTEGER DEFAULT 60,
    last_fetched TIMESTAMP,
    success_rate REAL DEFAULT 1.0,
    avg_relevance REAL DEFAULT 0.5,
    total_fetches INTEGER DEFAULT 0,
    successful_fetches INTEGER DEFAULT 0,
    config_json TEXT            -- JSON config for source-specific settings
);

-- Cache AI theme classifications to avoid repeated LLM calls
CREATE TABLE IF NOT EXISTS trend_theme_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trend_fingerprint TEXT NOT NULL,
    theme TEXT NOT NULL,
    sub_theme TEXT,
    confidence REAL DEFAULT 0.0,  -- 0.0-1.0 confidence score
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by TEXT             -- 'ai', 'curator', or 'manual'
);

-- ============================================================================
-- CREATE INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_theme_mapping_fingerprint ON trend_theme_mapping(trend_fingerprint);
CREATE INDEX IF NOT EXISTS idx_theme_mapping_theme ON trend_theme_mapping(theme);
CREATE INDEX IF NOT EXISTS idx_used_topics_theme ON used_topics(theme);
CREATE INDEX IF NOT EXISTS idx_content_memory_theme ON content_memory(theme);
CREATE INDEX IF NOT EXISTS idx_trend_sources_tier ON trend_sources(tier);
CREATE INDEX IF NOT EXISTS idx_trend_sources_enabled ON trend_sources(enabled);

-- ============================================================================
-- SEED INITIAL DATA
-- ============================================================================

-- Register existing sources
INSERT INTO trend_sources (source_name, source_type, tier, enabled, refresh_minutes)
VALUES
    ('Brave Search', 'api', 3, 1, 720),
    ('Google Trends', 'api', 3, 1, 720);

-- Register new sources (disabled by default until implemented)
INSERT INTO trend_sources (source_name, source_type, tier, enabled, refresh_minutes)
VALUES
    ('HuggingFace Daily Papers', 'rss', 1, 0, 60),
    ('arXiv Sanity Lite', 'rss', 1, 0, 60),
    ('Reddit r/MachineLearning', 'api', 1, 0, 60),
    ('Reddit r/LocalLLaMA', 'api', 1, 0, 60),
    ('Simon Willison Blog', 'rss', 2, 0, 360),
    ('Techmeme', 'scrape', 3, 0, 720),
    ('CSET Georgetown', 'rss', 4, 0, 10080),
    ('AI Now Institute', 'rss', 4, 0, 10080),
    ('AIAAIC Repository', 'rss', 4, 0, 10080);
