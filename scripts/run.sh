#!/usr/bin/env bash
set -euo pipefail

# launchd has a minimal PATH; add homebrew bin (node, python3, etc.)
export PATH="/opt/homebrew/bin:$PATH"

PROJECT_DIR="/Users/tanishqjagwani/IdeaProjects/stock-genie-agent"

# Add project scripts/bin to PATH so 'claude' wrapper is found by subprocess
export PATH="$PROJECT_DIR/scripts/bin:$PATH"

LOG_DIR="$PROJECT_DIR/logs"

mkdir -p "$LOG_DIR"

cd "$PROJECT_DIR"
source .venv/bin/activate

python main.py >> "$LOG_DIR/cron_$(date +%Y-%m-%d).log" 2>&1
