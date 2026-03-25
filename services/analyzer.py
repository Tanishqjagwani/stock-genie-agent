import json
import logging
import subprocess

from config.settings import CLAUDE_TIMEOUT

logger = logging.getLogger(__name__)


def generate_report(aggregated_data: dict) -> str:
    """Call Claude Code CLI to generate the HTML report."""
    data_json = json.dumps(aggregated_data, indent=2, default=str)

    prompt = f"""You are a senior financial analyst. Analyze this global stock market data
and generate a complete HTML email report.

DATA:
{data_json}

Generate a beautiful HTML email report with:
1. Market Overview (2-3 sentences summarizing today's market action)
2. For each sector (Healthcare, Tech, Defence, Energy, Finance, Infrastructure):
   - Sector name with icon and trend badge (Bullish/Bearish/Neutral)
   - Table with columns: Ticker | Price | Change% | Signal | RSI | Trend
   - Group stocks by market (US, India, Europe, Asia)
   - 2-sentence AI commentary on sector outlook
   - Key news headlines affecting this sector
3. Top 5 Picks (STRONG_BUY or BUY stocks with best confluence across all markets)
4. Risk Alerts (geopolitical threats, macro risks)
5. Disclaimer

Style requirements:
- Use inline CSS only (for email compatibility)
- Dark theme: background #1a1a2e, card backgrounds #16213e, text #eee
- Green #00b894 for positive, Red #d63031 for negative, Amber #fdcb6e for neutral
- Table-based layout for email client compatibility
- Responsive widths using percentages
- Professional financial report aesthetic

Output ONLY the complete HTML document, nothing else. No markdown fences."""

    logger.info("Calling Claude Code CLI for report generation...")

    result = subprocess.run(
        ["claude", "--print", "--output-format", "text"],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=CLAUDE_TIMEOUT,
    )

    if result.returncode != 0:
        logger.error(f"Claude CLI failed: {result.stderr}")
        raise RuntimeError(f"Claude CLI returned non-zero exit code: {result.returncode}")

    html = result.stdout.strip()

    if not html.startswith("<"):
        # Try to extract HTML if wrapped in markdown fences
        if "```html" in html:
            html = html.split("```html", 1)[1]
            html = html.rsplit("```", 1)[0].strip()
        elif "```" in html:
            html = html.split("```", 1)[1]
            html = html.rsplit("```", 1)[0].strip()

    logger.info(f"Generated HTML report ({len(html)} chars)")
    return html
