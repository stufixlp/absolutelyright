# Claude "Absolutely Right" Counter Scripts

Scripts to track how often Claude Code says you're right.

## Quick Start

### 1. Backfill Historical Data
Scan all existing Claude conversations and upload to your API:

```bash
python3 backfill.py --upload http://localhost:3003
# Or with authentication:
python3 backfill.py --upload https://absolutelyright.lol YOUR_SECRET
```

### 2. Real-time Monitoring
Watch for new "you're right" messages as they happen:

```bash
python3 watcher.py --upload http://localhost:3003
# Or with authentication:
python3 watcher.py --upload https://absolutelyright.lol YOUR_SECRET
```

## What Gets Counted

Both scripts track two metrics:
- **Absolutely right**: "You're absolutely right" or "You are absolutely right"
- **Just right**: Any "You're right" or "You are right" (includes "absolutely right")

## Environment Variables

Optional environment variables to customize behavior:

```bash
# Change Claude projects directory (default: ~/.claude/projects)
export CLAUDE_PROJECTS=/path/to/claude/projects

# Change patterns (regex)
export PATTERN="You(?:'re| are) absolutely right"
export PATTERN_RIGHT="You(?:'re| are) right"

# Change check interval for watcher (seconds, default: 2)
export CHECK_INTERVAL=5
```

## Data Storage

Both scripts store data locally in `~/.absolutelyright/`:
- `daily_counts.json` - Absolutely right counts by date
- `daily_right_counts.json` - Total right counts by date  
- `project_counts.json` - Counts by project
- `processed_ids.json` - Already processed message IDs
- `total_count.txt` - Running total

## API Endpoints

The scripts upload to `/api/set` with this payload:
```json
{
  "day": "2024-01-15",
  "count": 5,
  "right_count": 12,
  "secret": "optional_secret"
}
```

## Tips

- Run `backfill.py` first to get all historical data
- Keep `watcher.py` running to track new messages in real-time
- The watcher uploads today's counts on startup and after each new match
- Both scripts work without authentication if your API doesn't require it