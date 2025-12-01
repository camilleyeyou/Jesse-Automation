# Jesse A. Eisenbalm - LinkedIn Automation System

**AI-powered content generation, validation, and automated daily posting for LinkedIn.**

> "What if Apple sold mortality?" - Premium lip balm meets existential dread meets corporate satire.

## 🚀 Features

- **Multi-Agent Content Generation** - GPT-4o-mini powered content creation
- **3 Persona Validators** - Sarah Chen, Marcus Williams, Jordan Park
- **Image Generation** - Google Gemini 2.5 Flash for branded visuals
- **Automated Daily Posting** - APScheduler-based reliable scheduling
- **SQLite Queue** - Persistent post queue with priority support
- **Modern Dashboard** - React UI for easy management
- **CLI Tools** - Command-line automation control

## 📁 Project Structure

```
jesse-automation/
├── src/
│   ├── agents/              # AI Agents
│   │   ├── base_agent.py
│   │   ├── content_generator.py
│   │   ├── image_generator.py
│   │   ├── feedback_aggregator.py
│   │   ├── revision_generator.py
│   │   └── validators/
│   │       ├── sarah_chen.py
│   │       ├── marcus_williams.py
│   │       └── jordan_park.py
│   ├── models/              # Data Models
│   │   ├── post.py
│   │   └── batch.py
│   ├── services/            # Business Logic
│   │   ├── orchestrator.py
│   │   ├── scheduler.py
│   │   ├── queue_manager.py
│   │   └── linkedin_poster.py
│   └── infrastructure/      # External Integrations
│       ├── ai/
│       ├── config/
│       ├── prompts/
│       └── cost_tracking/
├── api/                     # FastAPI Backend
│   └── main.py
├── dashboard/               # React Frontend
│   └── src/
├── cli/                     # Command Line Tools
│   └── automation.py
├── config/                  # Configuration
│   └── config.yaml
├── data/                    # Data Storage
│   ├── images/
│   ├── output/
│   └── automation/
├── requirements.txt
└── .env.example
```

## ⚡ Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys:
# - OPENAI_API_KEY
# - GOOGLE_API_KEY
# - LINKEDIN_ACCESS_TOKEN (optional)
```

### 3. Start the API Server

```bash
cd api
uvicorn main:app --reload --port 8001
```

### 4. Use the CLI

```bash
# Check status
python cli/automation.py status

# Generate content
python cli/automation.py generate

# Set daily posting schedule (9 AM)
python cli/automation.py schedule --hour 9 --minute 0

# Start scheduler
python cli/automation.py start

# Post immediately
python cli/automation.py post
```

### 5. Open Dashboard

Visit http://localhost:3000 (after starting frontend)

## 🔧 Configuration

Edit `config/config.yaml`:

```yaml
openai:
  model: gpt-4o-mini
  temperature: 0.7

google:
  image_model: gemini-2.5-flash-image
  use_images: true

batch:
  posts_per_batch: 1
  max_revisions: 2
```

## 🤖 AI Agents

| Agent | Role | What They Check |
|-------|------|-----------------|
| **Content Generator** | Creates posts | Brand voice, cultural refs, hooks |
| **Sarah Chen** | Customer Validator | Authenticity, survivor reality |
| **Marcus Williams** | Business Validator | Creative integrity, portfolio-worthy |
| **Jordan Park** | Social Validator | Algorithm, virality, engagement |
| **Image Generator** | Visual Creator | Brand aesthetics, product accuracy |
| **Feedback Aggregator** | Synthesis | Combines validator feedback |
| **Revision Generator** | Editor | Fixes issues while keeping voice |

## 📊 API Endpoints

### Automation Control
- `GET /api/automation/status` - Full system status
- `POST /api/automation/scheduler/start` - Start scheduler
- `POST /api/automation/scheduler/stop` - Stop scheduler
- `POST /api/automation/schedule` - Set daily post time
- `POST /api/automation/post-now` - Trigger immediate post
- `POST /api/automation/generate-content` - Generate new content

### Queue Management
- `GET /api/automation/queue` - View queued posts
- `POST /api/automation/queue` - Add post to queue
- `DELETE /api/automation/queue/{id}` - Remove from queue

### History
- `GET /api/automation/history` - Published posts history
- `GET /api/automation/activity` - Activity log

## 🔐 LinkedIn Setup

1. Create LinkedIn App at https://developer.linkedin.com
2. Get OAuth 2.0 credentials
3. Run OAuth flow or set `LINKEDIN_ACCESS_TOKEN` in `.env`

## 💰 Costs

| Service | Cost |
|---------|------|
| GPT-4o-mini | ~$0.002 per post |
| Gemini 2.5 Flash | $0.039 per image |
| **Total per post** | ~$0.04 |

## 📝 License

MIT License - See LICENSE file

---

**Made with ❤️ for keeping humans human in an AI world**
