import logging
import sys
from datetime import date

from tools.stock_data import batch_fetch_all_stocks
from tools.technical_analysis import compute_all_technicals
from tools.news_fetcher import fetch_news_for_sectors, fetch_geopolitical_news
from services.analyzer import generate_report
from services.email_service import send_report_email

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"logs/run_{date.today().isoformat()}.log"),
    ],
)
logger = logging.getLogger(__name__)


def main():
    today = date.today().isoformat()
    logger.info(f"=== Stock Genie Daily Run: {today} ===")

    # Step 1: Fetch all stock fundamentals
    logger.info("Step 1: Fetching stock fundamentals...")
    all_stocks = batch_fetch_all_stocks()

    # Step 2: Compute technical indicators
    logger.info("Step 2: Computing technical indicators...")
    all_technicals = compute_all_technicals(all_stocks)

    # Step 3: Fetch news
    logger.info("Step 3: Fetching sector and geopolitical news...")
    sector_news = fetch_news_for_sectors()
    geo_news = fetch_geopolitical_news()

    # Step 4: Aggregate
    logger.info("Step 4: Aggregating data...")
    aggregated = {
        "date": today,
        "stocks": all_stocks,
        "technicals": all_technicals,
        "sector_news": sector_news,
        "geopolitical_news": geo_news,
    }

    # Step 5: Generate HTML report via Claude CLI
    logger.info("Step 5: Generating report via Claude Code CLI...")
    html_report = generate_report(aggregated)

    # Save a local copy
    report_path = f"logs/report_{today}.html"
    with open(report_path, "w") as f:
        f.write(html_report)
    logger.info(f"Report saved to {report_path}")

    # Step 6: Send email
    logger.info("Step 6: Sending email...")
    send_report_email(f"Stock Genie Daily - {today}", html_report)

    logger.info("=== Pipeline complete ===")


if __name__ == "__main__":
    main()
