from __future__ import annotations

import logging
import time
from typing import Optional

import numpy as np
import pandas as pd

from config.settings import YFINANCE_DELAY
from models.schemas import TechnicalIndicators
from tools.stock_data import fetch_historical_data

logger = logging.getLogger(__name__)


# --- Pure pandas/numpy indicator calculations ---

def _rsi(close: pd.Series, length: int = 14) -> Optional[float]:
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=length).mean()
    avg_loss = loss.rolling(window=length).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    val = rsi.iloc[-1]
    return round(float(val), 2) if not np.isnan(val) else None


def _ema(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(span=length, adjust=False).mean()


def _macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = _ema(close, fast)
    ema_slow = _ema(close, slow)
    macd_line = ema_fast - ema_slow
    signal_line = _ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def _bbands(close: pd.Series, length: int = 20, std: float = 2.0):
    middle = close.rolling(window=length).mean()
    rolling_std = close.rolling(window=length).std()
    upper = middle + std * rolling_std
    lower = middle - std * rolling_std
    return upper, middle, lower


def _sma(close: pd.Series, length: int) -> Optional[float]:
    s = close.rolling(window=length).mean()
    if s.dropna().empty:
        return None
    val = s.iloc[-1]
    return round(float(val), 2) if not np.isnan(val) else None


def _atr(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14) -> Optional[float]:
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    atr_series = tr.rolling(window=length).mean()
    val = atr_series.iloc[-1]
    return round(float(val), 2) if not np.isnan(val) else None


# --- Main indicator computation ---

def compute_indicators(ticker: str, df: pd.DataFrame) -> Optional[TechnicalIndicators]:
    """Compute all technical indicators from OHLCV data."""
    try:
        if df is None or len(df) < 30:
            return None

        close = df["Close"]
        high = df["High"]
        low = df["Low"]
        volume = df["Volume"]

        # RSI
        rsi_val = _rsi(close, 14)

        # MACD
        macd_line, signal_line, histogram = _macd(close, 12, 26, 9)
        macd_val = round(float(macd_line.iloc[-1]), 4) if not np.isnan(macd_line.iloc[-1]) else None
        macd_signal_val = round(float(signal_line.iloc[-1]), 4) if not np.isnan(signal_line.iloc[-1]) else None
        macd_hist_val = round(float(histogram.iloc[-1]), 4) if not np.isnan(histogram.iloc[-1]) else None

        # Bollinger Bands
        bb_upper_s, bb_middle_s, bb_lower_s = _bbands(close, 20, 2.0)
        bb_upper = round(float(bb_upper_s.iloc[-1]), 2) if not np.isnan(bb_upper_s.iloc[-1]) else None
        bb_middle = round(float(bb_middle_s.iloc[-1]), 2) if not np.isnan(bb_middle_s.iloc[-1]) else None
        bb_lower = round(float(bb_lower_s.iloc[-1]), 2) if not np.isnan(bb_lower_s.iloc[-1]) else None

        # SMAs
        sma_20_val = _sma(close, 20)
        sma_50_val = _sma(close, 50)
        sma_200_val = _sma(close, 200)

        # EMAs
        ema_12_s = _ema(close, 12)
        ema_26_s = _ema(close, 26)
        ema_12_val = round(float(ema_12_s.iloc[-1]), 2) if not np.isnan(ema_12_s.iloc[-1]) else None
        ema_26_val = round(float(ema_26_s.iloc[-1]), 2) if not np.isnan(ema_26_s.iloc[-1]) else None

        # ATR
        atr_val = _atr(high, low, close, 14)

        # Support / Resistance (20-day low/high)
        support = round(float(low.tail(20).min()), 2)
        resistance = round(float(high.tail(20).max()), 2)

        # Trend determination
        current_price = float(close.iloc[-1])
        trend = _determine_trend(current_price, sma_50_val, sma_200_val)

        # Signal determination
        signal = _determine_signal(rsi_val, macd_hist_val, current_price, bb_lower, bb_upper)

        # Volume trend
        vol_trend = _determine_volume_trend(volume)

        return TechnicalIndicators(
            ticker=ticker,
            rsi_14=rsi_val,
            macd=macd_val,
            macd_signal=macd_signal_val,
            macd_hist=macd_hist_val,
            bb_upper=bb_upper,
            bb_middle=bb_middle,
            bb_lower=bb_lower,
            sma_20=sma_20_val,
            sma_50=sma_50_val,
            sma_200=sma_200_val,
            ema_12=ema_12_val,
            ema_26=ema_26_val,
            atr_14=atr_val,
            trend=trend,
            signal=signal,
            support=support,
            resistance=resistance,
            volume_trend=vol_trend,
        )
    except Exception as e:
        logger.warning(f"Failed to compute indicators for {ticker}: {e}")
        return None


def _determine_trend(price: float, sma50: Optional[float], sma200: Optional[float]) -> str:
    if sma50 is None:
        return "NEUTRAL"
    if sma200 is not None:
        if price > sma50 > sma200:
            return "BULLISH"
        if price < sma50 < sma200:
            return "BEARISH"
    if price > sma50:
        return "BULLISH"
    if price < sma50:
        return "BEARISH"
    return "NEUTRAL"


def _determine_signal(
    rsi: Optional[float],
    macd_hist: Optional[float],
    price: float,
    bb_lower: Optional[float],
    bb_upper: Optional[float],
) -> str:
    score = 0

    if rsi is not None:
        if rsi < 30:
            score += 2
        elif rsi < 40:
            score += 1
        elif rsi > 70:
            score -= 2
        elif rsi > 60:
            score -= 1

    if macd_hist is not None:
        if macd_hist > 0:
            score += 1
        else:
            score -= 1

    if bb_lower is not None and bb_upper is not None:
        if price <= bb_lower:
            score += 1
        elif price >= bb_upper:
            score -= 1

    if score >= 3:
        return "STRONG_BUY"
    if score >= 1:
        return "BUY"
    if score <= -3:
        return "STRONG_SELL"
    if score <= -1:
        return "SELL"
    return "HOLD"


def _determine_volume_trend(volume: pd.Series) -> str:
    if len(volume) < 20:
        return "NORMAL"
    avg_5 = volume.tail(5).mean()
    avg_20 = volume.tail(20).mean()
    if avg_20 == 0:
        return "NORMAL"
    ratio = avg_5 / avg_20
    if ratio > 1.3:
        return "HIGH"
    if ratio < 0.7:
        return "LOW"
    return "NORMAL"


def compute_all_technicals(fundamentals: dict) -> dict:
    """Compute technicals for all stocks. Returns {sector: {market: [TechnicalIndicators]}}."""
    results = {}
    total = sum(
        len(stocks)
        for sector_markets in fundamentals.values()
        for stocks in sector_markets.values()
    )
    computed = 0

    for sector, markets in fundamentals.items():
        if sector not in results:
            results[sector] = {}
        for market, stocks in markets.items():
            if market not in results[sector]:
                results[sector][market] = []
            for stock in stocks:
                ticker = stock["ticker"]
                computed += 1
                logger.info(f"[{computed}/{total}] Computing technicals for {ticker}")
                df = fetch_historical_data(ticker)
                if df is not None:
                    indicators = compute_indicators(ticker, df)
                    if indicators:
                        results[sector][market].append(indicators.model_dump())
                time.sleep(YFINANCE_DELAY)

    return results
