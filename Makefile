.PHONY: setup test run-local stop-local migrate seed ingest analyze clean help

help:
	@echo "AI Radar Impact Development Makefile"
	@echo "===================================="
	@echo "Lệnh khả dụng:"
	@echo "  make setup         - Cài đặt dependencies cho cả Backend và Frontend cục bộ"
	@echo "  make run-local     - Khởi chạy các container Docker (db, backend, frontend)"
	@echo "  make stop-local    - Dừng các container Docker đang chạy"
	@echo "  make migrate       - Chạy Alembic migrations để cập nhật cơ sở dữ liệu"
	@echo "  make seed          - Nạp dữ liệu nguồn RSS ban đầu"
	@echo "  make ingest        - Thu thập dữ liệu mới từ các nguồn tin"
	@echo "  make analyze       - Phân tích các tài liệu chưa xử lý bằng Gemini"
	@echo "  make test          - Chạy các unit tests trong container Backend"
	@echo "  make clean         - Dọn dẹp cache của Python cục bộ"

setup:
	@echo "Cài đặt dependencies cục bộ..."
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

run-local:
	@echo "Khởi chạy docker-compose..."
	docker-compose up -d

stop-local:
	@echo "Dừng docker-compose..."
	docker-compose down

migrate:
	@echo "Đang chạy database migrations..."
	docker-compose exec backend alembic upgrade head

seed:
	@echo "Đang nạp nguồn RSS mẫu..."
	docker-compose exec backend python -m app.scripts.seed_sources

ingest:
	@echo "Đang chạy quy trình Ingestion..."
	docker-compose exec backend python -m app.scripts.run_ingestion

analyze:
	@echo "Đang chạy quy trình phân tích AI (Gemini)..."
	docker-compose exec backend python -m app.scripts.run_analysis

test:
	@echo "Đang chạy tests..."
	docker-compose exec backend pytest

clean:
	@echo "Đang dọn dẹp python cache..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ipynb_checkpoints" -exec rm -rf {} +
