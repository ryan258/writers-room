#!/bin/bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

if [ ! -f ".env" ]; then
  echo "Warning: .env file not found. OPENROUTER_API_KEY must be set before running Writers Room."
fi

if [ "${1:-}" = "--cli" ]; then
  shift
  if command -v uv >/dev/null 2>&1 && [ -f "pyproject.toml" ]; then
    exec uv run python main.py "$@"
  fi

  if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: python3 is not installed or not on PATH."
    exit 1
  fi

  if [ -d ".venv" ]; then
    # shellcheck disable=SC1091
    source .venv/bin/activate
  elif [ -d "venv" ]; then
    # shellcheck disable=SC1091
    source venv/bin/activate
  fi

  exec python main.py "$@"
fi

exec ./start_web.sh "$@"
