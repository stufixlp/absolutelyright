# Claude "Absolutely Right" Tracker

Counts how often Claude agrees with you.

## Quick start

```bash
python3 watcher.py  # Start tracking locally
```

## Backfill historical data

```bash
# Just count locally
python3 backfill.py

# Count and upload to API
python3 backfill.py --upload https://absolutelyright.lol YOUR_SECRET

# Output as JSON
python3 backfill.py --json
```

The backfill script tracks both:
- "You're absolutely right" / "You are absolutely right"
- "You're right" / "You are right"

## Configuration

Set environment variables (optional):
```bash
export CLAUDE_PROJECTS=~/.claude/projects  # Path to Claude projects
```

## Data

Stored locally in `~/.absolutelyright/`:

- `total_count.txt` - Running total
- `daily_counts.json` - Counts by date
- `project_counts.json` - By project

---

*These are the actual scripts that power absolutelyright.lol*