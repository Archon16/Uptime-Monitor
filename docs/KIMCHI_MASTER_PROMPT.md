# Master Prompt For Kimchi

Build the complete uptime monitor MVP using the attached PRD, HLD, LLD, Tech Stack and TODO documents.

Requirements:

Backend:
- FastAPI
- Python 3.11
- SQLAlchemy 2.x
- PostgreSQL
- APScheduler
- httpx

Frontend:
- React + Vite
- Plain CSS
- Native fetch

Infrastructure:
- Docker Compose

Important Constraints:
- Keep implementation simple.
- Do NOT introduce Redis.
- Do NOT introduce Celery.
- Do NOT introduce Kafka.
- Do NOT introduce Alembic.
- Do NOT create microservices.
- Use a single urls table.
- Store only latest status.
- No historical checks table.

Implementation Order:
1. Backend
2. Frontend
3. Docker
4. Documentation
5. Verification

After each phase, verify functionality before moving to next phase.
