.PHONY: help setup test lint format generate-cases build-embeddings train-ner evaluate serve clean

PYTHON ?= python
PIP ?= pip

help:
	@echo "Kent-AI Development Commands:"
	@echo "  make setup            Install dependencies in virtual environment"
	@echo "  make test             Run test suite with pytest"
	@echo "  make lint             Check code formatting and style"
	@echo "  make format           Auto-format code with black and ruff"
	@echo "  make generate-cases   Run synthetic case generation (LLaMA 3)"
	@echo "  make build-embeddings Build ChromaDB index from repertory.sqlite"
	@echo "  make train-ner        Fine-tune ClinicalBERT model"
	@echo "  make evaluate         Run full pipeline evaluation on test set"
	@echo "  make serve            Launch Streamlit clinical dashboard"
	@echo "  make clean            Remove cache directories and temporary files"

setup:
	$(PIP) install -e ".[dev]"

test:
	pytest tests/ -v

lint:
	ruff check src/ tests/ scripts/

format:
	black src/ tests/ scripts/
	ruff check --fix src/ tests/ scripts/

generate-cases:
	$(PYTHON) scripts/generate_cases.py

build-embeddings:
	$(PYTHON) scripts/build_embeddings.py

train-ner:
	$(PYTHON) scripts/train_ner.py

evaluate:
	$(PYTHON) scripts/evaluate.py

serve:
	streamlit run src/dashboard/app.py

clean:
	rm -rf .pytest_cache .coverage htmlcov build dist *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} +
