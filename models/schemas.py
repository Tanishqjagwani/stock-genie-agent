from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class StockFundamentals(BaseModel):
    ticker: str
    name: str
    market: str
    sector: str
    price: Optional[float] = None
    change_pct: Optional[float] = None
    pe_ratio: Optional[float] = None
    market_cap: Optional[float] = None
    volume: Optional[int] = None
    high_52w: Optional[float] = None
    low_52w: Optional[float] = None


class TechnicalIndicators(BaseModel):
    ticker: str
    rsi_14: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None
    atr_14: Optional[float] = None
    trend: str = "NEUTRAL"  # BULLISH / BEARISH / NEUTRAL
    signal: str = "HOLD"  # STRONG_BUY / BUY / HOLD / SELL / STRONG_SELL
    support: Optional[float] = None
    resistance: Optional[float] = None
    volume_trend: str = "NORMAL"  # HIGH / NORMAL / LOW


class NewsArticle(BaseModel):
    title: str
    source: str
    url: str
    published: Optional[str] = None


class SectorData(BaseModel):
    sector: str
    stocks: List[dict] = []
    news: List[NewsArticle] = []
