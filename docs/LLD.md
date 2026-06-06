# Low Level Design

## Repository Structure

uptime-monitor/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── scheduler.py
│   │   └── routes.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js
│   │   ├── components/
│   │   │   ├── UrlForm.jsx
│   │   │   ├── UrlTable.jsx
│   │   │   └── StatusBadge.jsx
│   │   └── index.css
│   └── Dockerfile
│
├── docker-compose.yml
├── README.md
└── AI_LOG.md

## Database Schema

Table: urls

id                INTEGER PRIMARY KEY
url               VARCHAR(2048) UNIQUE NOT NULL
name              VARCHAR(255)
is_up             BOOLEAN
status_code       INTEGER
response_time_ms  INTEGER
last_checked_at   TIMESTAMP
created_at        TIMESTAMP

## API Contracts

### POST /urls

Request
{
  "url":"https://example.com",
  "name":"Example"
}

Response 201
{
  "id":1,
  "url":"https://example.com"
}

### GET /urls

Response
[
 {
  "id":1,
  "url":"https://example.com",
  "name":"Example",
  "is_up":true,
  "status_code":200,
  "response_time_ms":120,
  "last_checked_at":"2026-01-01T10:00:00Z"
 }
]

### DELETE /urls/{id}

Response
204 No Content

## Scheduler Design

Interval: 60 seconds

Process:
1. Load all URLs
2. Create AsyncClient
3. asyncio.gather()
4. Update rows

Store:
- status_code
- response_time_ms
- is_up
- last_checked_at

## Startup Logic

Application startup:
- create tables
- start scheduler

Application shutdown:
- stop scheduler
