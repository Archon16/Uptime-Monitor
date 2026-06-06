# Project Overview — Uptime Monitor

A lightweight, full-stack application that lets users register URLs, periodically pings them every 60 seconds, and displays whether each URL is **UP** or **DOWN** along with its response time. The entire stack runs locally with a single `docker compose up --build` command.

---

## Table of Contents

- [Architecture at a Glance](#architecture-at-a-glance)
- [How the Services Connect](#how-the-services-connect)
- [Infrastructure — Docker & Docker Compose](#infrastructure--docker--docker-compose)
- [Backend — File-by-File Breakdown](#backend--file-by-file-breakdown)
- [Frontend — File-by-File Breakdown](#frontend--file-by-file-breakdown)
- [Root-Level Files](#root-level-files)
- [Data Flow — End to End](#data-flow--end-to-end)
- [Why This Tech Stack?](#why-this-tech-stack)
- [Database Schema](#database-schema)
- [API Reference](#api-reference)

---

## Architecture at a Glance

```
┌──────────────┐       HTTP (fetch)       ┌──────────────────┐      SQL (asyncpg)      ┌──────────────┐
│              │  ──────────────────────►  │                  │  ──────────────────────► │              │
│   Frontend   │      localhost:8000       │     Backend      │     db:5432 (internal)   │  PostgreSQL  │
│  React+Vite  │  ◄──────────────────────  │  FastAPI+Python  │  ◄────────────────────── │   Database   │
│  Port 3000   │       JSON responses     │    Port 8000     │      query results       │  Port 5432   │
└──────────────┘                          └──────────────────┘                          └──────────────┘
                                                  │
                                                  │  Every 60 seconds (APScheduler)
                                                  ▼
                                          ┌──────────────────┐
                                          │  Scheduler Job   │
                                          │  Pings all URLs  │
                                          │  via httpx       │
                                          │  Updates DB      │
                                          └──────────────────┘
```

There are **3 services** running as Docker containers:

| Service    | Technology           | Container Port | Host Port | Role                                    |
|------------|----------------------|:--------------:|:---------:|-----------------------------------------|
| `frontend` | React + Vite         | 3000           | 3000      | User interface — displays URL statuses  |
| `backend`  | Python FastAPI       | 8000           | 8000      | REST API + background URL health checks |
| `db`       | PostgreSQL 15 Alpine | 5432           | 5432      | Persistent data storage                 |

---

## How the Services Connect

### Frontend → Backend (HTTP REST)

The React frontend makes HTTP calls to `http://localhost:8000` using the browser's native `fetch` API. These calls happen in two ways:

1. **User-triggered** — When a user adds or deletes a URL, the frontend calls `POST /urls` or `DELETE /urls/{id}`.
2. **Automatic polling** — Every **30 seconds**, the frontend calls `GET /urls` to refresh the table with the latest status data.

The backend responds with JSON. CORS middleware on the backend allows the frontend (running on a different port) to make these cross-origin requests.

### Backend → Database (SQL over TCP)

The FastAPI backend connects to PostgreSQL using the connection string:
```
postgresql+asyncpg://postgres:postgres@db:5432/uptime
```

Breaking this down:
- `postgresql` — the database dialect (tells SQLAlchemy it's a PostgreSQL database)
- `asyncpg` — the async Python driver used to communicate with PostgreSQL
- `postgres:postgres` — username:password
- `db` — the hostname (Docker Compose creates a network where service names resolve as hostnames, so `db` maps to the PostgreSQL container's IP)
- `5432` — PostgreSQL's default port
- `uptime` — the database name

All database operations are **async** — the backend never blocks while waiting for a query to complete.

### Backend → External URLs (HTTP via httpx)

The scheduler (running inside the backend process) makes outbound HTTP GET requests to every registered URL using the `httpx` library. It records:
- Whether the URL responded successfully (status < 400 = UP)
- The HTTP status code
- The response time in milliseconds

### Docker Compose Internal Network

Docker Compose automatically creates a **bridge network** that all three services share. Within this network:
- The backend refers to PostgreSQL as `db` (not `localhost`)
- The frontend is served to the browser, which then calls `localhost:8000` (the backend's host-mapped port)

---

## Infrastructure — Docker & Docker Compose

### docker-compose.yml

This is the **orchestration file** that defines all three services and how they connect:

```yaml
version: '3.8'

services:
  db:                              # PostgreSQL database
    image: postgres:15-alpine      # Pre-built image from Docker Hub
    environment:                   # These env vars configure Postgres on first run
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: uptime          # Automatically creates the "uptime" database
    volumes:
      - pg_data:/var/lib/postgresql/data   # Persistent volume — data survives restarts
    ports:
      - "5432:5432"
    healthcheck:                   # Backend waits for this before starting
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend               # Builds from backend/Dockerfile
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@db:5432/uptime
    depends_on:
      db:
        condition: service_healthy  # Only starts after Postgres health check passes

  frontend:
    build: ./frontend              # Builds from frontend/Dockerfile
    ports:
      - "3000:3000"
    depends_on:
      - backend                    # Starts after backend is up
```

**Key concepts:**
- **`depends_on` with `service_healthy`** — Ensures the backend doesn't start before PostgreSQL is ready to accept connections. Without this, the backend would crash trying to connect to a database that isn't ready yet.
- **`pg_data` volume** — A named Docker volume that persists PostgreSQL data. Even if you run `docker compose down` and `docker compose up` again, your URLs and their status data are preserved.
- **Port mapping (`"8000:8000"`)** — Maps the container's internal port to the same port on your host machine, making it accessible from your browser.

### backend/Dockerfile

```dockerfile
FROM python:3.11-slim       # Lightweight Python base image
WORKDIR /app                # All commands run from /app inside the container
COPY requirements.txt .     # Copy dependency list first (Docker layer caching optimization)
RUN pip install --no-cache-dir -r requirements.txt   # Install Python packages
COPY app/ ./app/            # Copy application code
EXPOSE 8000                 # Document which port the app uses
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]  # Start the server
```

**Why copy `requirements.txt` before the code?** Docker caches each layer. If your code changes but dependencies don't, Docker reuses the cached layer with already-installed packages — making rebuilds much faster.

### frontend/Dockerfile

```dockerfile
FROM node:20-alpine         # Lightweight Node.js base image
WORKDIR /app
COPY package.json .         # Same caching strategy as backend
RUN npm install             # Install JavaScript packages
COPY . .                    # Copy all frontend source code
EXPOSE 3000
CMD ["npm", "run", "dev"]   # Start the Vite dev server
```

---

## Backend — File-by-File Breakdown

All backend source code lives in `backend/app/`.

### `main.py` — Application Entry Point

This is where the FastAPI application is created and configured. It does three things on startup:

1. **Creates database tables** — Using SQLAlchemy's `Base.metadata.create_all()`, it ensures the `urls` table exists in PostgreSQL. If the table already exists, this is a no-op.
2. **Starts the scheduler** — Kicks off the APScheduler background job that pings URLs every 60 seconds.
3. **Registers CORS middleware** — Allows the frontend (on port 3000) to call the backend (on port 8000) without browser security blocking the requests.

The `@asynccontextmanager` lifespan pattern ensures clean startup and shutdown:
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP: runs before the app starts accepting requests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  # Create tables
    start_scheduler()                                    # Start background pings
    yield                                                # App is now running
    # SHUTDOWN: runs when the app is stopping
    stop_scheduler()                                     # Clean up scheduler
```

This is FastAPI's modern way (replacing the older `@app.on_event("startup")` pattern) to manage the application lifecycle.

### `config.py` — Configuration Management

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/uptime"

    class Config:
        env_prefix = ""
```

Uses `pydantic-settings` to load configuration from **environment variables**. The `database_url` field has a default value, but if you set a `DATABASE_URL` environment variable (which `docker-compose.yml` does), it overrides the default.

`env_prefix = ""` means it looks for environment variables matching the field name exactly (e.g., `DATABASE_URL` for `database_url` — pydantic-settings is case-insensitive).

### `database.py` — Database Connection Setup

```python
engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()
```

- **`engine`** — The connection pool to PostgreSQL. All database operations go through this. `echo=False` means SQL queries are not logged to stdout.
- **`AsyncSessionLocal`** — A factory that creates database sessions. Each API request gets its own session.
  - `expire_on_commit=False` — After committing, the ORM objects remain usable (without this, accessing attributes after commit would trigger lazy loading, which doesn't work with async).
- **`Base`** — The base class that all ORM models inherit from. It tracks which tables exist.

```python
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

This is a **FastAPI dependency**. Every route that needs database access declares `db: AsyncSession = Depends(get_db)`. FastAPI:
1. Calls `get_db()` before your route handler runs
2. Gives the handler a session
3. Automatically closes the session after the handler finishes (even if it raises an error)

### `models.py` — Database Table Definition (ORM Model)

```python
class Url(Base):
    __tablename__ = "urls"

    id              = Column(Integer, primary_key=True, index=True)
    url             = Column(String(2048), unique=True, nullable=False)
    name            = Column(String(255))
    is_up           = Column(Boolean, default=False)
    status_code     = Column(Integer)
    response_time_ms = Column(Integer)
    last_checked_at = Column(DateTime, server_default=func.now())
    created_at      = Column(DateTime, server_default=func.now())
```

This is the **ORM (Object-Relational Mapping) model**. Instead of writing raw SQL, you interact with this Python class, and SQLAlchemy translates it to SQL.

| Column | Type | Purpose |
|--------|------|---------|
| `id` | Integer (PK) | Auto-incrementing unique identifier |
| `url` | String(2048) | The monitored URL. Unique — can't add the same URL twice |
| `name` | String(255) | Optional human-friendly name |
| `is_up` | Boolean | `true` if last check succeeded, `false` if it failed |
| `status_code` | Integer | HTTP status code from the last check (200, 404, etc.) |
| `response_time_ms` | Integer | How long the last check took in milliseconds |
| `last_checked_at` | DateTime | When the scheduler last checked this URL |
| `created_at` | DateTime | When the URL was first registered |

`server_default=func.now()` means PostgreSQL (not Python) generates the default timestamp — this ensures the time comes from the database server, not the application server.

### `schemas.py` — Request/Response Validation (Pydantic Models)

These define the **shape of data** going in and out of the API:

- **`UrlCreate`** — Validates incoming `POST /urls` requests. Requires `url` (string), optionally accepts `name`.
- **`UrlResponse`** — Defines what the API returns. Includes all fields from the database. `from_attributes = True` tells Pydantic to read data directly from SQLAlchemy model attributes (instead of expecting a dictionary).
- **`HealthResponse`** — Simple `{"status": "ok"}` shape for the health endpoint.

**Why separate models from schemas?** Models define the database structure. Schemas define the API contract. A user should never be able to directly set `is_up` or `status_code` via the API — those are set by the scheduler. By having `UrlCreate` with only `url` and `name`, we enforce this boundary.

### `routes.py` — API Endpoints

Four endpoints:

**`POST /urls`** (Create a URL)
1. Checks if the URL already exists in the database → returns 409 Conflict if so
2. Creates a new `Url` row
3. Commits to the database
4. Returns the created URL with status 201

**`GET /urls`** (List all URLs)
1. Queries all rows from the `urls` table, ordered by `created_at` descending (newest first)
2. Returns them as a JSON array

**`DELETE /urls/{url_id}`** (Remove a URL)
1. Deletes the row matching the given ID
2. If no row was found (`rowcount == 0`), returns 404
3. Otherwise returns 204 No Content

**`GET /health`** (Health check)
1. Returns `{"status": "ok"}` — useful for Docker health checks or load balancer probes

### `scheduler.py` — Background URL Health Checking

This is the **core monitoring logic**. It has three parts:

**`check_url(url_row)`** — Checks a single URL:
```python
async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
    response = await client.get(url_row.url)
```
- Creates an async HTTP client with a **10-second timeout**
- Follows redirects (e.g., http → https redirects)
- If the response status code < 400 → URL is UP
- If any exception occurs (timeout, DNS failure, connection refused) → URL is DOWN
- Measures elapsed time in milliseconds

**`check_all_urls()`** — Checks all URLs concurrently:
```python
tasks = [check_url(u) for u in urls]
results = await asyncio.gather(*tasks)
```
- Loads all URL rows from the database
- Creates a check task for each URL
- Runs them **all at once** using `asyncio.gather()` (not one-by-one — this is crucial for performance)
- Updates each row with the results and commits

**`start_scheduler()` / `stop_scheduler()`** — Lifecycle management:
```python
scheduler = AsyncIOScheduler()
scheduler.add_job(check_all_urls, IntervalTrigger(seconds=60))
scheduler.start()
```
- Uses APScheduler's `AsyncIOScheduler` which integrates with Python's asyncio event loop
- The job runs every 60 seconds
- On application shutdown, `stop_scheduler()` cleanly shuts down the scheduler

### `requirements.txt` — Python Dependencies

| Package | Why it's needed |
|---------|----------------|
| `fastapi` | The web framework — handles HTTP routing, validation, serialization |
| `uvicorn[standard]` | ASGI server that actually runs FastAPI. `[standard]` includes uvloop for better performance |
| `sqlalchemy` | ORM — lets us define tables as Python classes and query with Python instead of raw SQL |
| `asyncpg` | Async PostgreSQL driver — the low-level library that actually sends SQL to PostgreSQL over TCP |
| `httpx` | Async HTTP client — used by the scheduler to ping URLs |
| `apscheduler` | Background job scheduler — triggers `check_all_urls()` every 60 seconds |
| `pydantic-settings` | Loads configuration from environment variables into typed Python objects |

---

## Frontend — File-by-File Breakdown

All frontend source code lives in `frontend/src/`.

### `index.html` — The HTML Shell

```html
<div id="root"></div>
<script type="module" src="/src/main.jsx"></script>
```

This is the **single HTML page** of the entire application (it's a Single Page Application). The `<div id="root">` is where React mounts its component tree. The `<script>` tag loads the JavaScript entry point.

### `main.jsx` — React Entry Point

```jsx
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
```

Finds the `<div id="root">` in the HTML and renders the `<App />` component into it. `StrictMode` enables extra development warnings (double-renders in dev to catch side-effect bugs).

### `App.jsx` — Main Application Component

This is the **brain of the frontend**. It manages all state and coordinates the child components.

**State:**
```jsx
const [urls, setUrls] = useState([])    // Array of URL objects from the backend
```

**Auto-refresh:**
```jsx
useEffect(() => {
    load()                                // Fetch URLs immediately on page load
    const interval = setInterval(load, 30000)  // Then every 30 seconds
    return () => clearInterval(interval)        // Clean up on unmount
}, [])
```
The `useEffect` with an empty dependency array `[]` runs once when the component mounts. It sets up a 30-second polling interval so the UI always reflects the latest scheduler results.

**Event handlers:**
- `handleAdd(url, name)` — Calls the API to add a URL, then refreshes the list
- `handleDelete(id)` — Calls the API to delete a URL, then refreshes the list

**Renders:**
- `<UrlForm>` — The form for adding new URLs
- `<UrlTable>` — The table displaying all monitored URLs

### `api.js` — API Communication Layer

```javascript
const API_BASE = 'http://localhost:8000';
```

Three functions that wrap the browser's `fetch` API:

| Function | HTTP Call | Purpose |
|----------|-----------|---------|
| `fetchURLs()` | `GET /urls` | Retrieve all monitored URLs and their statuses |
| `addURL(url, name)` | `POST /urls` | Register a new URL for monitoring |
| `deleteURL(id)` | `DELETE /urls/{id}` | Remove a URL from monitoring |

Each function checks `res.ok` and throws an error if the request failed. This keeps error handling consistent.

### `components/StatusBadge.jsx` — Status Indicator

A tiny component that renders:
- Green **"UP"** badge if `isUp === true`
- Red **"DOWN"** badge if `isUp === false`
- A dash **"-"** if `isUp` is `null` (URL hasn't been checked yet)

The three-way check (`=== true`, `=== false`, fallback) is important because a newly added URL has `is_up = null` until the scheduler runs for the first time.

### `components/UrlForm.jsx` — Add URL Form

A controlled form with two inputs:
- **URL** (required, type `url` — browser validates it's a valid URL format)
- **Name** (optional, type `text`)

On submit:
1. Prevents default form submission (which would reload the page)
2. Trims whitespace
3. Calls `onAdd(url, name)` (passed down from `App.jsx`)
4. Clears both input fields

### `components/UrlTable.jsx` — URL Status Table

Renders all monitored URLs in a table with 6 columns:

| Column | Source | Display |
|--------|--------|---------|
| URL | `u.url` | The raw URL string |
| Name | `u.name` | User-provided name, or "-" if none |
| Status | `u.is_up` | Rendered via `<StatusBadge>` |
| Response Time | `u.response_time_ms` | Shown as "120ms", or "-" if not yet checked |
| Last Checked | `u.last_checked_at` | Formatted with `toLocaleString()` for local timezone |
| Delete | button | Red delete button, calls `onDelete(u.id)` |

If there are no URLs yet, it shows "No URLs being monitored yet." instead of an empty table.

### `index.css` — Global Styles

| Selector | Purpose |
|----------|---------|
| `body` | System font stack, light gray background, 2rem padding |
| `.container` | White card with max-width 900px, shadow, rounded corners |
| `form` | Flexbox layout for the input fields and button |
| `input[type="text/url"]` | Consistent padding, border, and font size |
| `button` | Blue background (#007bff), white text, hover darkening |
| `table`, `th`, `td` | Full-width table with left-aligned cells and subtle borders |
| `.status-up` | Green background badge for UP status |
| `.status-down` | Red background badge for DOWN status |
| `.delete-btn` | Red delete button with darker hover |
| `.meta` | Gray subtitle text showing URL count |

### `vite.config.js` — Build Tool Configuration

```javascript
export default defineConfig({
  plugins: [react()],       // Enables JSX transformation and React Fast Refresh
  server: {
    port: 3000,             // Dev server runs on port 3000
    host: '0.0.0.0',        // Binds to all interfaces (required inside Docker)
  },
})
```

`host: '0.0.0.0'` is critical — without it, Vite would only listen on `127.0.0.1` inside the container, making it unreachable from your host browser.

### `package.json` — JavaScript Dependencies

| Package | Why it's needed |
|---------|----------------|
| `react` | The UI library — component-based rendering |
| `react-dom` | React's bridge to the browser DOM |
| `vite` | Build tool — fast dev server with hot module replacement |
| `@vitejs/plugin-react` | Vite plugin for JSX/React Fast Refresh support |

---

## Root-Level Files

### `README.md`
Setup instructions, testing steps, architecture summary, and a deployment sketch for AWS (ECS + RDS + CloudFront).

### `AI_LOG.md`
Documents which AI tools were used (Kimchi with kimi-k2.6), the prompts that generated the code, and course corrections made when the AI produced incorrect code.

### `.gitignore`
Prevents unnecessary files from being committed to git.

---

## Data Flow — End to End

### Flow 1: User adds a URL

```
User types URL + name in the form
        │
        ▼
UrlForm calls onAdd(url, name)
        │
        ▼
App.jsx calls addURL(url, name)  →  api.js sends POST /urls to backend
        │
        ▼
routes.py checks for duplicates → creates Url row → commits to PostgreSQL
        │
        ▼
Backend returns 201 + the created URL as JSON
        │
        ▼
App.jsx calls load() → fetches GET /urls → updates state → table re-renders
```

### Flow 2: Scheduler pings URLs (every 60 seconds)

```
APScheduler triggers check_all_urls()
        │
        ▼
Loads all Url rows from PostgreSQL
        │
        ▼
Creates async tasks for each URL
        │
        ▼
asyncio.gather() pings all URLs concurrently via httpx
        │
        ▼
For each URL: records is_up, status_code, response_time_ms, last_checked_at
        │
        ▼
Updates all rows in PostgreSQL and commits
```

### Flow 3: Frontend auto-refresh (every 30 seconds)

```
setInterval fires every 30 seconds
        │
        ▼
Calls load() → GET /urls → backend queries PostgreSQL → returns JSON
        │
        ▼
React updates state → table re-renders with fresh data
```

---

## Why This Tech Stack?

### Backend: FastAPI + Python

| Reason | Detail |
|--------|--------|
| **Async-native** | FastAPI is built on Python's `asyncio`. The scheduler pings multiple URLs concurrently without threads — essential for I/O-bound work like HTTP requests |
| **Auto-generated API docs** | FastAPI creates Swagger UI at `/docs` automatically — makes testing and debugging trivial |
| **Built-in validation** | Pydantic schemas validate request bodies and serialize responses with zero manual code |
| **Fast development** | Minimal boilerplate — the entire backend is ~200 lines across 7 files |

### Database: PostgreSQL

| Reason | Detail |
|--------|--------|
| **Reliability** | PostgreSQL is production-grade, ACID-compliant, and battle-tested |
| **Easy Docker setup** | Official `postgres:15-alpine` image works out-of-the-box with environment variables |
| **Persistent volumes** | Named Docker volume ensures data survives container restarts |
| **Industry standard** | The most commonly expected database in production deployments |

### ORM: SQLAlchemy 2.x + asyncpg

| Reason | Detail |
|--------|--------|
| **Async support** | SQLAlchemy 2.x has first-class async session support, pairing perfectly with FastAPI |
| **asyncpg driver** | The fastest async PostgreSQL driver for Python — uses PostgreSQL's binary protocol |
| **ORM convenience** | Define tables as Python classes, query with Python expressions instead of raw SQL |

### HTTP Client: httpx

| Reason | Detail |
|--------|--------|
| **Async support** | Unlike `requests`, `httpx` supports `async/await` natively — required for use with `asyncio.gather()` |
| **Redirect handling** | Built-in `follow_redirects=True` handles 301/302 redirects automatically |
| **Timeout support** | Configurable timeouts prevent the scheduler from hanging on unresponsive URLs |

### Scheduler: APScheduler

| Reason | Detail |
|--------|--------|
| **AsyncIOScheduler** | Integrates directly with Python's event loop — runs inside the same process as FastAPI |
| **No external dependency** | Unlike Celery (which needs Redis/RabbitMQ), APScheduler runs in-process with zero infrastructure overhead |
| **Simple interval jobs** | One line to schedule a recurring job: `scheduler.add_job(fn, IntervalTrigger(seconds=60))` |

### Frontend: React + Vite

| Reason | Detail |
|--------|--------|
| **Component model** | React's component architecture keeps the UI modular — `StatusBadge`, `UrlForm`, `UrlTable` are independent, reusable pieces |
| **State management** | `useState` + `useEffect` is sufficient for this MVP — no need for Redux or context |
| **Vite** | Extremely fast dev server with hot module replacement — changes reflect instantly in the browser |
| **Native Fetch API** | No need for Axios — the browser's built-in `fetch` handles all API calls |

### Infrastructure: Docker + Docker Compose

| Reason | Detail |
|--------|--------|
| **One-command startup** | `docker compose up --build` launches all 3 services — no manual setup of Python, Node, or PostgreSQL |
| **Environment consistency** | Everyone runs the exact same versions of Python, Node, and PostgreSQL regardless of their host OS |
| **Network isolation** | Docker Compose creates an internal network where services communicate by name (`db`, `backend`) |
| **Persistent storage** | Named volume `pg_data` keeps database data across restarts |

---

## Database Schema

```sql
CREATE TABLE urls (
    id               SERIAL PRIMARY KEY,
    url              VARCHAR(2048) UNIQUE NOT NULL,
    name             VARCHAR(255),
    is_up            BOOLEAN DEFAULT FALSE,
    status_code      INTEGER,
    response_time_ms INTEGER,
    last_checked_at  TIMESTAMP DEFAULT NOW(),
    created_at       TIMESTAMP DEFAULT NOW()
);
```

> **Note:** This table is created automatically by SQLAlchemy on application startup (`Base.metadata.create_all()`). You never need to run this SQL manually.

---

## API Reference

### `GET /health`
Returns `{"status": "ok"}`. Used for readiness checks.

### `POST /urls`
**Request:**
```json
{
  "url": "https://example.com",
  "name": "Example"
}
```
**Response (201):**
```json
{
  "id": 1,
  "url": "https://example.com",
  "name": "Example",
  "is_up": null,
  "status_code": null,
  "response_time_ms": null,
  "last_checked_at": "2026-01-01T10:00:00",
  "created_at": "2026-01-01T10:00:00"
}
```
**Error (409):** `{"detail": "URL already exists"}`

### `GET /urls`
**Response (200):**
```json
[
  {
    "id": 1,
    "url": "https://example.com",
    "name": "Example",
    "is_up": true,
    "status_code": 200,
    "response_time_ms": 120,
    "last_checked_at": "2026-01-01T10:01:00",
    "created_at": "2026-01-01T10:00:00"
  }
]
```

### `DELETE /urls/{id}`
**Response (204):** No content.
**Error (404):** `{"detail": "URL not found"}`
