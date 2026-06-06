# AI Collaboration Log

## AI Tech Stack

- **Tool:** Kimchi (AI Coding Agent)
- **Model:** kimi-k2.6

## Prompts That Shipped It

1. **Scoping prompt:** "Build the uptime monitor MVP according to the Todo file in phases. Refer to Kimchi master prompt file for instructions on how to proceed with development"
2. **Backend scaffold:** Asked Kimchi to write FastAPI backend with SQLAlchemy 2.x async model, CRUD routes, and APScheduler-based health checker
3. **Frontend scaffold:** Asked Kimchi to write React + Vite frontend with components for URL form, table, status badge, and auto-refresh

## Course Corrections

### Issue: Database model timestamps
The initial model draft used `server_default=func.now()` with `onupdate=func.now()` for `last_checked_at`, which would have caused the database to auto-update `last_checked_at` on every SQL update rather than letting the scheduler control it explicitly. Corrected by removing `onupdate` and setting the timestamp in the scheduler code.

### Issue: Scheduler async compatibility
Initial thought was to use `AsyncIOScheduler` directly in the module, but need to ensure scheduler starts after event loop is running. Corrected by using `@asynccontextmanager` lifespan in FastAPI main.py for clean startup/shutdown.
