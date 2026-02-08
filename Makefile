.PHONY: up down logs migrate test shell load-triz build restart

up:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d

down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	docker compose exec backend python manage.py migrate

test:
	docker compose exec backend pytest
	docker compose exec frontend npm test

shell:
	docker compose exec backend python manage.py shell

load-triz:
	docker compose exec backend python manage.py load_triz_data --all

build:
	docker compose build

restart:
	docker compose restart
