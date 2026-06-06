# Product Requirements Document (PRD)

## Objective
Build a lightweight uptime monitor that allows users to register URLs, periodically checks them, and displays the latest status and response time.

## Assignment Goals
- Working end-to-end application
- Fast implementation
- Simple architecture
- Docker Compose startup

## Functional Requirements

### Backend
- POST /urls
- GET /urls
- DELETE /urls/{id}
- Health endpoint: GET /health
- Background scheduler runs every 60 seconds

### Monitoring Logic
A URL is UP when:
- HTTP status code < 400

A URL is DOWN when:
- Timeout occurs
- DNS resolution fails
- Connection error occurs
- HTTP status >= 400

### Frontend
- Add URL form
- List monitored URLs
- Status badge (UP/DOWN)
- Response time
- Last checked timestamp
- Delete button
- Auto refresh every 30 seconds

## Non Goals
- Authentication
- Alerting
- Historical charts
- Multi-user support
- Custom intervals
