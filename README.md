# AffiliateLinker

Automated Pinterest affiliate marketing system powered by 4 AI agents.

## Overview

AffiliateLinker automatically discovers Amazon affiliate products, creates Pinterest pins, and posts them throughout the day to generate passive affiliate income.

## Agents

| Agent | Role |
|-------|------|
| **Product Researcher** | Finds high-margin Amazon products with affiliate potential |
| **Account Manager** | Creates and schedules Pinterest pins with affiliate links |
| **Strategist** | Researches growth tactics and optimizes strategy |
| **Manager** | Orchestrates all agents and monitors system health |

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure API keys
cp .env.example .env
# Edit .env with your credentials

# 3. Run the system
python main.py start
```

## Commands

```bash
python main.py run         # Run all agents once
python main.py start       # Start continuous scheduler
python main.py status      # Show system status
python main.py discover    # Run product discovery only
python main.py post        # Run posting only
python main.py strategy    # Run strategy analysis
python main.py dashboard   # Launch Streamlit dashboard
```

## Setup Requirements

1. **Amazon Associates Account** - https://affiliate-program.amazon.com
2. **Pinterest Business Account** - With API access enabled
3. **Pinterest Developer App** - https://developers.pinterest.com

## Project Structure

```
AffiliateLinker/
├── agents/           # Agent specification files
├── src/
│   ├── agents/       # Agent implementations
│   ├── api/          # Amazon & Pinterest API clients
│   ├── database/     # Database models
│   ├── scheduler/    # Job scheduler
│   └── dashboard/    # Streamlit dashboard
├── config/           # Configuration files
├── data/             # Database and logs
└── strategy/         # Strategy reports
```

## Configuration

Edit `config/settings.yaml` to customize:
- Product niches and price ranges
- Posting schedule and frequency
- Automation level (0-5)
- Alert thresholds

## Automation Levels

| Level | Description |
|-------|-------------|
| 0 | Manual - all operations require user input |
| 1 | Auto-discovery - finds products automatically |
| 2 | Auto-approval - approves qualifying products |
| 3 | Auto-posting - posts without approval |
| 4 | Auto-strategy - applies strategy recommendations |
| 5 | Full auto - complete autonomous operation |

## License

MIT
