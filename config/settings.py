import os
from dotenv import load_dotenv

load_dotenv()

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
EMAIL_TO = os.getenv("EMAIL_TO", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "Stock Genie <onboarding@resend.dev>")

YFINANCE_DELAY = 0.5  # seconds between requests
NEWS_DAYS_BACK = 1
HISTORICAL_PERIOD = "60d"
CLAUDE_TIMEOUT = 300  # 5 minutes
