from fastapi import FastAPI
from app.engine import run_backtest
from app.models import BacktestRequest

app = FastAPI(title='Strategy Lab', version='0.1.0',
              description='Educational long-only SMA backtesting API. No live trading.')


@app.get('/health')
def health():
    return {'status': 'ok'}


@app.post('/backtests')
def backtest(request: BacktestRequest):
    return run_backtest(request)
