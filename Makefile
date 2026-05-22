.PHONY: up down build logs health test-unit test-int test-all install-cli

# ── Docker ─────────────────────────────────────────────────────────────────────
up:
	docker compose up -d

build:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f

health:
	@curl -s http://localhost:8000/health | python3 -m json.tool

# ── Testing ────────────────────────────────────────────────────────────────────
test-unit:
	@echo "── Translation Service ──"
	cd services/translation && python -m pytest tests/ -v
	@echo ""
	@echo "── TTS Service ──"
	cd services/tts && python -m pytest tests/ -v
	@echo ""
	@echo "── ASR Service ──"
	cd services/asr && python -m pytest tests/ -v
	@echo ""
	@echo "── Orchestrator ──"
	cd services/orchestrator && python -m pytest tests/ -v
	@echo ""
	@echo "── CLI ──"
	cd cli && npm test

test-int:
	pip install -r tests/requirements.txt
	python -m pytest tests/integration/ -v

test-all: test-unit test-int

# ── CLI ────────────────────────────────────────────────────────────────────────
install-cli:
	cd cli && npm install && npm run build && npm link

run:
	live-translate
