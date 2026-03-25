#!/usr/bin/env bash
set -euo pipefail

SCRIPT="/Users/tanishqjagwani/IdeaProjects/stock-genie-agent/scripts/run.sh"
CRON_SCHEDULE="30 1 * * 1-5"  # 1:30 AM UTC = 7:00 AM IST, weekdays

chmod +x "$SCRIPT"

# Add cron entry if not already present
(crontab -l 2>/dev/null | grep -v "stock-genie-agent"; echo "$CRON_SCHEDULE $SCRIPT  # stock-genie-agent") | crontab -

echo "Cron installed. Current crontab:"
crontab -l
