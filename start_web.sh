#!/bin/bash

# start_web.sh - Launch the Writers Room Web Interface

# Colors for output
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}🎬 Writers Room: The Mischief Engine${NC}"
echo -e "${CYAN}=====================================${NC}"

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed or not in PATH.${NC}"
    exit 1
fi

# Check for virtual environment
if [ -d "venv" ]; then
    echo -e "${GREEN}✓ Virtual environment found. Activating...${NC}"
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo -e "${GREEN}✓ Virtual environment found. Activating...${NC}"
    source .venv/bin/activate
else
    echo -e "${YELLOW}⚠️  No virtual environment found. Running with system Python.${NC}"
    echo -e "${YELLOW}   (Recommended: python3 -m venv venv && source venv/bin/activate)${NC}"
fi

# Install dependencies if needed
if [ ! -f ".requirements_installed" ]; then
    echo -e "\n${CYAN}📦 Installing dependencies...${NC}"
    pip install -r requirements.txt
    if [ $? -eq 0 ]; then
        touch .requirements_installed
        echo -e "${GREEN}✓ Dependencies installed.${NC}"
    else
        echo -e "${RED}Error: Failed to install dependencies.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ Dependencies already installed.${NC}"
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "\n${YELLOW}⚠️  Warning: .env file not found.${NC}"
    echo -e "${YELLOW}   Make sure you have set OPENROUTER_API_KEY in your environment.${NC}"
fi

# Launch browser in background (wait a sec for server to start)
(sleep 2 && open "http://localhost:5001" 2>/dev/null || xdg-open "http://localhost:5001" 2>/dev/null || echo -e "${YELLOW}Please open http://localhost:5001 in your browser${NC}") &

# Start Flask Server
echo -e "\n${GREEN}🚀 Starting Web Server...${NC}"
echo -e "${CYAN}   Press Ctrl+C to stop.${NC}\n"

cd web
python3 app.py
