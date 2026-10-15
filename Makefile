name := Call_me_maybe

UV_CACHE_DIR := /goinfre/nambirak/Call_me_maybe/cache
export UV_CACHE_DIR

HF_HOME := /goinfre/nambirak/Call_me_maybe/hf-cache
HF_HUB_CACHE := $(HF_HOME)/hub
export HF_HOME
export HF_HUB_CACHE

.PHONY: all install run debug clean clean-all clean-cache lint check-uv

all: install

check-uv:
	@if ! command -v uv >/dev/null 2>&1; then \
		echo "Installing uv..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
		echo "uv installed. Please restart your shell or run: export PATH=\"$$HOME/.local/bin:$$PATH\""; \
		exit 1; \
	fi

install: check-uv
	@echo "Starting $(name) installation..."
	@uv sync --frozen 2>/dev/null || uv sync
	@echo "Installation complete."

run:
	@mkdir -p "$(HF_HUB_CACHE)"
	@uv run python -m src

debug:
	@echo "HF_HOME=$(HF_HOME)"
	@echo "HF_HUB_CACHE=$(HF_HUB_CACHE)"
	@echo "UV_CACHE_DIR=$(UV_CACHE_DIR)"
	@uv run python --version
	@uv run python -c "import sys; print(sys.executable)"
	@if [ ! -d .venv ]; then echo "WARNING: .venv missing, run 'make install'"; fi

clean:
	@echo "Cleaning project..."
	@rm -rf __pycache__ .mypy_cache *.egg-info .pytest_cache .python-version output.txt
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name output -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Clean complete."

clean-all: clean
	@rm -rf .venv
	@echo "Full clean complete."

clean-cache:
	@rm -rf "$(HF_HOME)"
	@echo "Hugging Face cache removed."
lint:
	@echo "Running linters..."
	@uv run flake8 src --max-line-length=79 --select=D,E,W,F --ignore=E203,W503
	@echo "Running type checker..."
	@uv run mypy src --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
