.PHONY: up down restart logs setup seed run-pipeline api dashboard test lint format

up:
	docker-compose up -d

down:
	docker-compose down

restart:
	docker-compose down && docker-compose up -d

logs:
	docker-compose logs -f

setup:
	python scripts/setup_db.py

seed:
	python scripts/seed_data.py

run-pipeline:
	python scripts/run_pipeline.py

api:
	uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

dashboard:
	streamlit run dashboard/app.py

test:
	pytest tests/ -v

test-coverage:
	pytest tests/ --cov=. --cov-report=html -v

lint:
	flake8 . --exclude=venv,__pycache__,.git

format:
	black . --exclude=venv
	isort . --skip=venv

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete