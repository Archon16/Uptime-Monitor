# TODO Checklist For Kimchi

## Phase 0 - Scaffold

Create:

backend/
frontend/
docker-compose.yml
README.md
AI_LOG.md

---

## Phase 1 - Backend

### Dependencies

fastapi
uvicorn
sqlalchemy
asyncpg
httpx
apscheduler
pydantic-settings

### Files

config.py
database.py
models.py
schemas.py
scheduler.py
routes.py
main.py

### Implement Database

Create urls table with:

- id
- url
- name
- is_up
- status_code
- response_time_ms
- last_checked_at
- created_at

### Implement APIs

POST /urls
GET /urls
DELETE /urls/{id}
GET /health

### Scheduler

Requirements:
- APScheduler AsyncIOScheduler
- Runs every 60 seconds
- Concurrent requests using asyncio.gather
- Timeout 10 seconds
- Follow redirects
- Store latest status in same row

### Backend Acceptance Criteria

- Swagger loads
- URLs can be created
- URLs can be deleted
- Scheduler updates status

---

## Phase 2 - Frontend

### Setup

Create React + Vite project

### Components

StatusBadge.jsx
UrlForm.jsx
UrlTable.jsx

### API Layer

fetchURLs()
addURL()
deleteURL()

### App.jsx

Load URLs on startup

Auto refresh:
setInterval(refresh, 30000)

### UI

Columns:

URL
Name
Status
Response Time
Last Checked
Delete

### Acceptance Criteria

Add URL works
Delete works
Status updates automatically

---

## Phase 3 - Docker

Create:

backend Dockerfile
frontend Dockerfile
docker-compose.yml

Services:

db
backend
frontend

Database volume:
pg_data

---

## Phase 4 - Documentation

README.md

Must contain:
- docker compose up --build
- testing steps
- deployment sketch

AI_LOG.md

Must contain:
- AI tools used
- prompts used
- course corrections

---

## Final Verification

1. docker compose up --build

2. Open:
http://localhost:3000

3. Add:
https://example.com

4. Add:
https://this-domain-does-not-exist-xyz.com

5. Wait 60 seconds

6. Verify:
example.com = UP
broken url = DOWN

7. Restart stack

8. Verify data persists
