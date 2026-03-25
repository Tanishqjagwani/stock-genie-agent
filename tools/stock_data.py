from __future__ import annotations

import logging
import time
from typing import Optional

import pandas as pd
import yfinance as yf

from config.settings import HISTORICAL_PERIOD, YFINANCE_DELAY
from config.stocks import STOCKS
from models.schemas import StockFundamentals

logger = logging.getLogger(__name__)


def fetch_stock_fundamentals(ticker: str, market: str, sector: str) -> Optional[StockFundamentals]:
    """Fetch fundamental data for a single ticker."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="5d")

        price = info.get("currentPrice") or info.get("regularMarketPrice")
        prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose")
        change_pct = None
        if price and prev_close and prev_close != 0:
            change_pct = round(((price - prev_close) / prev_close) * 100, 2)

        return StockFundamentals(
            ticker=ticker,
            name=info.get("shortName", ticker),
            market=market,
            sector=sector,
            price=price,
            change_pct=change_pct,
            pe_ratio=info.get("trailingPE"),
            market_cap=info.get("marketCap"),
            volume=info.get("volume"),
            high_52w=info.get("fiftyTwoWeekHigh"),
            low_52w=info.get("fiftyTwoWeekLow"),
        )
    except Exception as e:
        logger.warning(f"Failed to fetch {ticker}: {e}")
        return None


def fetch_historical_data(ticker: str, period: str = HISTORICAL_PERIOD) -> Optional[pd.DataFrame]:
    """Fetch historical OHLCV data for technical analysis."""
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        if df.empty:
            return None
        return df
    except Exception as e:
        logger.warning(f"Failed to fetch history for {ticker}: {e}")
        return None


def batch_fetch_all_stocks() -> dict:
    """Fetch fundamentals for all configured stocks, organized by sector and market."""
    results = {}
    total = sum(
        len(tickers)
        for market in STOCKS.values()
        for tickers in market.values()
    )
    fetched = 0

    for market, sectors in STOCKS.items():
        for sector, tickers in sectors.items():
            if sector not in results:
                results[sector] = {}
            if market not in results[sector]:
                results[sector][market] = []

            for ticker in tickers:
                fetched += 1
                logger.info(f"[{fetched}/{total}] Fetching {ticker} ({market}/{sector})")
                data = fetch_stock_fundamentals(ticker, market, sector)
                if data:
                    results[sector][market].append(data.model_dump())
                time.sleep(YFINANCE_DELAY)

    return results
