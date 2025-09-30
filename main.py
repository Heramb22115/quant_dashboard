import yfinance as yf
import pandas as pd
import numpy as np
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import date, timedelta

class PriceData(BaseModel):
    Date: str
    Open: float
    High: float
    Low: float
    Close: float
    Volume: int

class HistoricalDataResponse(BaseModel):
    ticker: str
    history: List[PriceData]

class SMAResponse(BaseModel):
    ticker: str
    sma: Dict[str, float | None]

class StockInfoResponse(BaseModel):
    ticker: str
    info: Dict[str, Any]

class BollingerBandsData(BaseModel):
    Middle_Band: Optional[float] = None
    Upper_Band: Optional[float] = None
    Lower_Band: Optional[float] = None

class BollingerBandsResponse(BaseModel):
    ticker: str
    bands: Dict[str, BollingerBandsData]

class MACDData(BaseModel):
    MACD_Line: Optional[float] = None
    Signal_Line: Optional[float] = None
    Histogram: Optional[float] = None

class MACDResponse(BaseModel):
    ticker: str
    macd: Dict[str, MACDData]

class RSIResponse(BaseModel):
    ticker: str
    rsi: Dict[str, float | None]

def get_stock_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    stock = yf.Ticker(ticker)
    hist = stock.history(start=start_date, end=end_date)
    return hist if not hist.empty else pd.DataFrame()

def get_company_info(ticker: str) -> dict:
    stock = yf.Ticker(ticker)
    try:
        return stock.info
    except Exception:
        return {}

def calculate_bollinger_bands(data: pd.DataFrame, window: int, num_std: int):
    close_price = data['Close']
    middle_band = close_price.rolling(window=window).mean()
    std_dev = close_price.rolling(window=window).std()
    upper_band = middle_band + (std_dev * num_std)
    lower_band = middle_band - (std_dev * num_std)
    return middle_band, upper_band, lower_band

def calculate_macd(data: pd.DataFrame, fast_period: int, slow_period: int, signal_period: int):
    close_price = data['Close']
    ema_fast = close_price.ewm(span=fast_period, adjust=False).mean()
    ema_slow = close_price.ewm(span=slow_period, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_rsi(data: pd.DataFrame, window: int):
    close_price = data['Close']
    delta = close_price.diff(1)
    gain = delta.where(delta > 0, 0).fillna(0)
    loss = -delta.where(delta < 0, 0).fillna(0)
    avg_gain = gain.rolling(window=window, min_periods=1).mean()
    avg_loss = loss.rolling(window=window, min_periods=1).mean()
    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi

app = FastAPI(
    title="Quant Dashboard API",
    description="An API for fetching financial data and technical indicators.",
    version="2.1.0"
)

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Quant Dashboard API v2!"}

@app.get("/stocks/{ticker}/info", response_model=StockInfoResponse, tags=["Stocks"])
async def get_stock_info(ticker: str):
    info = get_company_info(ticker)
    if not info or not info.get("longName"):
        raise HTTPException(status_code=404, detail=f"Info not found for ticker '{ticker}'")
    
    filtered_info = {
        "longName": info.get("longName"),
        "symbol": info.get("symbol"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "country": info.get("country"),
        "website": info.get("website"),
        "marketCap": info.get("marketCap"),
        "longBusinessSummary": info.get("longBusinessSummary"),
    }
    return StockInfoResponse(ticker=ticker, info=filtered_info)

@app.get("/stocks/{ticker}/history", response_model=HistoricalDataResponse, tags=["Stocks"])
async def get_historical_data(ticker: str, start_date: Optional[date] = None, end_date: Optional[date] = None):
    if end_date is None: end_date = date.today()
    if start_date is None: start_date = end_date - timedelta(days=365)
    data = get_stock_data(ticker, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    if data.empty:
        raise HTTPException(status_code=404, detail=f"No historical data found for ticker '{ticker}'")
    
    data.reset_index(inplace=True)
    history_list = [
        PriceData(
            Date=row['Date'].strftime('%Y-%m-%d'),
            Open=row['Open'],
            High=row['High'],
            Low=row['Low'],
            Close=row['Close'],
            Volume=row['Volume']
        ) for _, row in data.iterrows()
    ]
    return HistoricalDataResponse(ticker=ticker, history=history_list)

@app.get("/technicals/{ticker}/sma", response_model=SMAResponse, tags=["Technicals"])
async def get_sma(ticker: str, window: int = 20, start_date: Optional[date] = None, end_date: Optional[date] = None):
    if end_date is None: end_date = date.today()
    if start_date is None: start_date = end_date - timedelta(days=365 + window)
    data = get_stock_data(ticker, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    if data.empty:
        raise HTTPException(status_code=404, detail=f"No data for SMA calculation for ticker '{ticker}'")
    
    sma_series = data['Close'].rolling(window=window).mean()
    sma_series.replace([np.inf, -np.inf], np.nan, inplace=True)
    sma_dict = {date.strftime('%Y-%m-%d'): (None if pd.isna(val) else val) for date, val in sma_series.items()}
    return SMAResponse(ticker=ticker, sma=sma_dict)

@app.get("/technicals/{ticker}/bbands", response_model=BollingerBandsResponse, tags=["Technicals"])
async def get_bollinger_bands(ticker: str, window: int = 20, num_std: int = 2, start_date: Optional[date] = None, end_date: Optional[date] = None):
    if end_date is None: end_date = date.today()
    if start_date is None: start_date = end_date - timedelta(days=365 + window)
    data = get_stock_data(ticker, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    if data.empty:
        raise HTTPException(status_code=404, detail=f"No data for Bollinger Bands calculation for ticker '{ticker}'")

    middle, upper, lower = calculate_bollinger_bands(data, window, num_std)
    result = {}
    for idx in middle.index:
        date_str = idx.strftime('%Y-%m-%d')
        middle_val = middle.get(idx)
        upper_val = upper.get(idx)
        lower_val = lower.get(idx)
        result[date_str] = BollingerBandsData(
            Middle_Band=middle_val if pd.notna(middle_val) and np.isfinite(middle_val) else None,
            Upper_Band=upper_val if pd.notna(upper_val) and np.isfinite(upper_val) else None,
            Lower_Band=lower_val if pd.notna(lower_val) and np.isfinite(lower_val) else None
        )
    return BollingerBandsResponse(ticker=ticker, bands=result)

@app.get("/technicals/{ticker}/macd", response_model=MACDResponse, tags=["Technicals"])
async def get_macd(ticker: str, fast: int = 12, slow: int = 26, signal: int = 9, start_date: Optional[date] = None, end_date: Optional[date] = None):
    if end_date is None: end_date = date.today()
    if start_date is None: start_date = end_date - timedelta(days=365 + slow)
    data = get_stock_data(ticker, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    if data.empty:
        raise HTTPException(status_code=404, detail=f"No data for MACD calculation for ticker '{ticker}'")

    macd_line, signal_line, histogram = calculate_macd(data, fast, slow, signal)
    result = {}
    for idx in macd_line.index:
        date_str = idx.strftime('%Y-%m-%d')
        macd_val = macd_line.get(idx)
        signal_val = signal_line.get(idx)
        hist_val = histogram.get(idx)
        result[date_str] = MACDData(
            MACD_Line=macd_val if pd.notna(macd_val) and np.isfinite(macd_val) else None,
            Signal_Line=signal_val if pd.notna(signal_val) and np.isfinite(signal_val) else None,
            Histogram=hist_val if pd.notna(hist_val) and np.isfinite(hist_val) else None
        )
    return MACDResponse(ticker=ticker, macd=result)

@app.get("/technicals/{ticker}/rsi", response_model=RSIResponse, tags=["Technicals"])
async def get_rsi(ticker: str, window: int = 14, start_date: Optional[date] = None, end_date: Optional[date] = None):
    if end_date is None: end_date = date.today()
    if start_date is None: start_date = end_date - timedelta(days=365 + window)
    data = get_stock_data(ticker, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    if data.empty:
        raise HTTPException(status_code=404, detail=f"No data for RSI calculation for ticker '{ticker}'")
    
    rsi_series = calculate_rsi(data, window)
    rsi_series.replace([np.inf, -np.inf], np.nan, inplace=True)
    rsi_dict = {date.strftime('%Y-%m-%d'): (None if pd.isna(val) else val) for date, val in rsi_series.items()}
    return RSIResponse(ticker=ticker, rsi=rsi_dict)

