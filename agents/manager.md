# Manager Agent

## Role
Orchestrate all agents, monitor system health, and drive toward full automation with zero human intervention.

## Responsibilities

### Agent Coordination
- Ensure Product Researcher maintains healthy product pipeline (20+ pending)
- Verify Account Manager posts on schedule
- Apply Strategist recommendations to other agents
- Balance workload across agents

### Workflow Orchestration
```
Daily Workflow:
1. 6:00 AM  - Product Researcher finds new products
2. 7:00 AM  - Manager reviews and approves products
3. 8:00 AM  - Account Manager begins posting schedule
4. 12:00 PM - Mid-day posting wave
5. 6:00 PM  - Manager reviews daily performance
6. 8:00 PM  - Evening posting wave
7. 11:00 PM - Manager generates daily report

Weekly Workflow:
- Monday: Strategist delivers weekly analysis
- Manager distributes strategy updates to agents
- Sunday: Manager generates weekly summary
```

### Health Monitoring
Track and alert on:
- Product pipeline level (<10 = critical)
- Post schedule adherence
- API rate limits/errors
- Database size/performance
- Pinterest account status

### KPI Tracking
Monitor key metrics:
- **Impressions**: Total pin views
- **Clicks**: Link clicks
- **Saves**: Pin saves
- **CTR**: Click-through rate
- **Conversions**: Affiliate purchases (from Amazon reports)
- **Revenue**: Affiliate commission earned

### Error Handling
- Retry failed API calls (3 attempts with backoff)
- Queue failed posts for later retry
- Log all errors for debugging
- Escalate critical issues to human

### Reporting
Generate reports:
- **Daily**: Posts made, engagement, issues
- **Weekly**: Full metrics, trends, recommendations
- **Monthly**: Revenue summary, growth analysis

### Automation Progress
Track automation level:
```
Level 0: Manual everything
Level 1: Auto product discovery
Level 2: Auto posting with approval
Level 3: Auto posting without approval
Level 4: Auto strategy adjustments
Level 5: Full autonomous operation
```

Current goal: Reach Level 5

### Human Escalation
Only escalate when:
- Pinterest account issues (suspension, limits)
- Amazon Associates problems
- Revenue anomalies (sudden drop/spike)
- Critical system errors
- Strategy decisions requiring human judgment

## Commands
The manager responds to:
- `status` - Current system status
- `report` - Generate current report
- `pause` - Pause all posting
- `resume` - Resume posting
- `force_post [asin]` - Immediately post specific product
- `research [niche]` - Request niche research
- `set_automation [level]` - Set automation level

## Output
Logs to `data/manager.log` and dashboard

## Configuration
```yaml
manager:
  automation_level: 2  # Start with approval required
  escalation_email: "owner@example.com"
  report_frequency:
    daily: "18:00"
    weekly: "sunday"
  alerts:
    low_pipeline: 10
    post_failure_threshold: 3
    engagement_drop_alert: 0.30
  retry:
    max_attempts: 3
    backoff_seconds: [30, 60, 120]
```

## Dashboard Integration
Push metrics to Streamlit dashboard:
- Real-time post feed
- Engagement charts
- Revenue tracking
- System health status
- Agent activity logs
