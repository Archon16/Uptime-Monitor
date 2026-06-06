# High Level Design

## Architecture

Browser
  |
React Frontend (Port 3000)
  |
FastAPI Backend (Port 8000)
  |
PostgreSQL (Port 5432)

Scheduler (inside backend process)
  |
Runs every 60s
  |
Checks all URLs concurrently
  |
Updates database

## Data Flow

User adds URL
 -> Backend validates
 -> Save to database

Scheduler runs
 -> Load URLs
 -> Ping URLs concurrently
 -> Save latest status

Frontend polls every 30s
 -> GET /urls
 -> Render table
