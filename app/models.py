from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)


class Candle(StrictModel):
    timestamp: datetime
    open: float = Field(gt=0, le=1e12)
    high: float = Field(gt=0, le=1e12)
    low: float = Field(gt=0, le=1e12)
    close: float = Field(gt=0, le=1e12)

    @model_validator(mode='after')
    def valid_candle(self):
        if self.timestamp.utcoffset() is None:
            raise ValueError('Timestamps must include a timezone')
        if not self.low <= min(self.open, self.close) <= max(self.open, self.close) <= self.high:
            raise ValueError('Invalid OHLC range')
        return self


class BacktestRequest(StrictModel):
    symbol: str = Field(default='DEMO', min_length=1, max_length=32)
    strategy: Literal['sma_cross'] = 'sma_cross'
    fast_period: int = Field(default=5, ge=1, le=500)
    slow_period: int = Field(default=20, ge=2, le=1000)
    initial_capital: float = Field(default=10000, ge=1, le=1e12)
    fee_bps: float = Field(default=10, ge=0, le=1000)
    slippage_bps: float = Field(default=5, ge=0, le=1000)
    candles: list[Candle] = Field(min_length=3, max_length=10000)

    @model_validator(mode='after')
    def valid_series(self):
        if self.fast_period >= self.slow_period:
            raise ValueError('fast_period must be less than slow_period')
        if len(self.candles) < self.slow_period + 2:
            raise ValueError('Need at least slow_period + 2 candles')
        if any(a.timestamp >= b.timestamp for a, b in zip(self.candles, self.candles[1:])):
            raise ValueError('Timestamps must be unique and strictly increasing')
        return self
