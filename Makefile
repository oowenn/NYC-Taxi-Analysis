.PHONY: help backend-dev frontend-dev build-backend build-frontend setup install test clean test-llm-pipeline

help:
	@echo "NYC Ridehail Analytics Chatbot - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make setup          - Initial setup (install dependencies)"
	@echo ""
	@echo "Development:"
	@echo "  make backend-dev    - Start backend dev server (with LLM pipeline enabled)"
	@echo "  make frontend-dev   - Start frontend dev server"
	@echo ""
	@echo "Build:"
	@echo "  make build-backend  - Build backend Docker image"
	@echo "  make build-frontend - Build frontend for production"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build   - Build all Docker images"
	@echo "  make docker-up      - Start services with Docker Compose"
	@echo "  make docker-down    - Stop Docker Compose services"
	@echo "  make docker-logs    - View Docker Compose logs"
	@echo ""
	@echo "Testing:"
	@echo "  make test           - Run tests"
	@echo "  make test-llm-pipeline - Test LLM pipeline (SQL + chart generation)"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean          - Clean cache and temp files"

setup:
	@echo "Setting up backend..."
	cd backend && python -m venv venv || true
	cd backend && source venv/bin/activate && pip install -r requirements.txt
	@echo "Setting up frontend..."
	cd frontend && npm install
	@echo "Setup complete! Copy .env.example files and configure."

backend-dev:
	cd backend && source venv/bin/activate && USE_LLM_PIPELINE=true uvicorn main:app --reload --port 8000

frontend-dev:
	cd frontend && npm run dev

build-backend:
	cd backend && docker build -t nyc-chatbot-backend .

build-frontend:
	cd frontend && npm run build

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

test:
	cd backend && source venv/bin/activate && pytest
	cd frontend && npm test

test-llm-pipeline:
	@echo "Testing LLM pipeline..."
	cd backend && source venv/bin/activate && PYTHONPATH=. python scripts/test_llm_pipeline.py

clean:
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf backend/.pytest_cache
	rm -rf frontend/node_modules/.cache
	rm -rf frontend/dist
	rm -rf /tmp/nyc_taxi_charts
	rm -f backend/scripts/llm_chart.png

