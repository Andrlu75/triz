# TRIZ-Solver

AI-platform for solving inventive problems using ARIZ-2010 methodology (V. Petrov).

## Tech Stack

- **Backend:** Django 5, Django REST Framework, Celery, OpenAI GPT-4o
- **Frontend:** React, TypeScript, Vite, Tailwind CSS, Zustand
- **Database:** PostgreSQL 16 + pgvector
- **Queue:** Redis 7 + Celery
- **Infrastructure:** Docker Compose

## Quick Start

```bash
# Copy environment variables
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY

# Start all services
make up

# Run database migrations
make migrate

# Load TRIZ knowledge base
make load-triz

# Run tests
make test
```

## Services

| Service        | Port  | Description                      |
|----------------|-------|----------------------------------|
| backend        | 8000  | Django API server                |
| frontend       | 5173  | React dev server (Vite)          |
| db             | 5432  | PostgreSQL 16 + pgvector         |
| redis          | 6379  | Redis 7 (cache + Celery broker)  |
| celery_worker  | -     | Celery worker for LLM calls      |
| celery_beat    | -     | Celery beat (periodic tasks)     |

## Development

```bash
# Start with hot-reload (dev mode)
make up

# View logs
make logs

# Django shell
make shell

# Stop all services
make down
```

## Project Structure

```
triz/
├── docker-compose.yml
├── docker-compose.dev.yml
├── .env.example
├── Makefile
├── backend/
│   ├── Dockerfile
│   ├── manage.py
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   └── dev.py
│   │   ├── celery.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   ├── apps/
│   └── requirements/
│       ├── base.txt
│       └── dev.txt
└── frontend/
    ├── Dockerfile
    ├── package.json
    └── src/
```
