# absolutelyright.lol

A web app that tracks how many times Claude Code says you're "absolutely right" (or just "right").

## Development

```bash
# Install Rust if needed
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Run locally
cargo run

# Server runs at http://localhost:3003
```

## API

### Get today's counts
```bash
GET /api/today
```

### Get history
```bash
GET /api/history
```

### Update counts
```bash
POST /api/set
Content-Type: application/json

{
  "day": "2025-09-04",
  "count": 5,
  "right_count": 2,
  "secret": "your-secret"  # Required if ABSOLUTELYRIGHT_SECRET is set
}
```

## Deployment (Fly.io)

```bash
# First time setup
fly launch --no-deploy
fly volumes create counts_data --size 1 --region sjc

# Set secret for API protection
fly secrets set ABSOLUTELYRIGHT_SECRET=your-secret-here

# Deploy
fly deploy
```

## Environment Variables

- `ABSOLUTELYRIGHT_SECRET`: Optional. If set, requires matching secret in POST /api/set requests

## Data Persistence

- SQLite database: `counts.db` (local) or `/app/data/counts.db` (production)
- Pageview logs: `pageviews.log` (local) or `/app/data/pageviews.log` (production)

## Tech Stack

- Backend: Rust with Axum
- Frontend: Vanilla JS with rough.js for hand-drawn charts
- Database: SQLite
