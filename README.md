# Uptime Monitor

A lightweight full-stack uptime monitor that periodically pings registered URLs and displays their status.

## Quick Start

```bash
docker compose up --build
```

Then open http://localhost:3000

## Testing

1. Open the frontend at http://localhost:3000
2. Add `https://example.com` — it should show as UP after ~60 seconds
3. Add `https://this-domain-does-not-exist-xyz.com` — it should show as DOWN after ~60 seconds
4. Wait for the scheduler to run (every 60 seconds)
5. Verify statuses update automatically
6. Restart the stack with `docker compose down && docker compose up -d`
7. Verify previously added URLs persist

## Architecture

- **Frontend:** React + Vite (Port 3000)
- **Backend:** FastAPI + SQLAlchemy + PostgreSQL (Port 8000)
- **Database:** PostgreSQL (Port 5432)
- **Scheduler:** APScheduler runs every 60 seconds

## API Endpoints

- `GET /health` — Health check
- `POST /urls` — Register a new URL
- `GET /urls` — List all monitored URLs
- `DELETE /urls/{id}` — Remove a URL

## Deployment Sketch

For a minimal cloud deployment (e.g., AWS ECS + RDS):

1. Push backend and frontend Docker images to ECR
2. Deploy PostgreSQL on RDS
3. Create an ECS Fargate service for the backend with environment variables pointing to RDS
4. Serve the frontend from an S3 bucket + CloudFront, or as a second Fargate service
5. Use an Application Load Balancer in front of the backend
6. Optionally, use AWS App Runner for even simpler deployment of both services

A simple Terraform snippet might look like:

```hcl
resource "aws_ecs_service" "backend" {
  name            = "uptime-backend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = 1
  launch_type     = "FARGATE"
}
```
