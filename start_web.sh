#!/bin/bash

set -euo pipefail

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

warn_missing_env() {
    if [ ! -f ".env" ]; then
        echo -e "\n${YELLOW}⚠️  Warning: .env file not found.${NC}"
        echo -e "${YELLOW}   Make sure you have set OPENROUTER_API_KEY in your environment.${NC}"
    fi
}

open_browser() {
    (sleep 2 && open "http://localhost:5001" 2>/dev/null || xdg-open "http://localhost:5001" 2>/dev/null || echo -e "${YELLOW}Please open http://localhost:5001 in your browser${NC}") &
}

launch_server() {
    echo -e "\n${GREEN}🚀 Starting Web Server...${NC}"
    echo -e "${CYAN}   Press Ctrl+C to stop.${NC}\n"
    exec "$@" uvicorn web.app:app --reload --port 5001
}

echo -e "${CYAN}🎬 Writers Room: The Mischief Engine${NC}"
echo -e "${CYAN}=====================================${NC}"

if command -v uv >/dev/null 2>&1 && [ -f "pyproject.toml" ]; then
    echo -e "${GREEN}✓ uv project detected. Syncing environment...${NC}"
    uv sync --group dev
    echo -e "${GREEN}✓ Dependencies synced with uv.${NC}"
    warn_missing_env
    open_browser
    launch_server uv run
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo -e "${RED}Error: python3 is not installed or not in PATH.${NC}"
    exit 1
fi

if [ -d ".venv" ]; then
    echo -e "${GREEN}✓ Virtual environment found. Activating...${NC}"
    # shellcheck disable=SC1091
    source .venv/bin/activate
elif [ -d "venv" ]; then
    echo -e "${GREEN}✓ Virtual environment found. Activating...${NC}"
    # shellcheck disable=SC1091
    source venv/bin/activate
else
    echo -e "${YELLOW}⚠️  No virtual environment found. Running with system Python.${NC}"
    echo -e "${YELLOW}   (Recommended fallback: python3 -m venv .venv && source .venv/bin/activate)${NC}"
fi

if [ ! -f ".requirements_installed" ] || [ "requirements.txt" -nt ".requirements_installed" ]; then
    echo -e "\n${CYAN}📦 Installing fallback dependencies from requirements.txt...${NC}"
    python3 -m pip install -r requirements.txt
    touch .requirements_installed
    echo -e "${GREEN}✓ Dependencies installed.${NC}"
else
    echo -e "${GREEN}✓ Dependencies already installed.${NC}"
fi

warn_missing_env
open_browser
launch_server
