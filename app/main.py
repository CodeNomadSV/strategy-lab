import json
from fastapi import Depends, FastAPI
from app.engine import run_backtest
from app.models import BacktestRequest
from app.llm import (Analysis, LunaClient, ParseEnvelope, ParseRequest,
                     ANALYZE_PROMPT, PARSE_PROMPT, get_luna, validate_output)

app = FastAPI(title='Strategy Lab', version='0.2.0',
              description='Educational SMA backtesting with optional APMIX Luna commentary.')


@app.get('/health')
def health():
    return {'status': 'ok'}


@app.post('/backtests')
@app.post('/api/v1/strategies/backtest')
def backtest(request: BacktestRequest):
    return run_backtest(request)


@app.post('/api/v1/ai/parse', response_model=ParseEnvelope)
def parse_strategy(request: ParseRequest, luna: LunaClient = Depends(get_luna)):
    """Draft only: review the extracted periods before submitting a backtest."""
    return validate_output(ParseEnvelope, luna.complete(PARSE_PROMPT, request.text))


@app.post('/api/v1/ai/analyze')
def analyze(request: BacktestRequest, luna: LunaClient = Depends(get_luna)):
    """Compute authoritative metrics in Python; send only summary to APMIX."""
    result = run_backtest(request)
    summary = {k: v for k, v in result.items() if k not in ('trades', 'equity_curve')}
    summary['assumptions'] = {
        'fee_bps': request.fee_bps, 'slippage_bps': request.slippage_bps,
        'fast_period': request.fast_period, 'slow_period': request.slow_period,
        'candle_count': len(request.candles),
        'start': request.candles[0].timestamp.isoformat(),
        'end': request.candles[-1].timestamp.isoformat(),
        'data_source': 'user supplied; not independently verified',
        'execution': 'next open; long only; final close liquidation',
        'drawdown': 'close-to-close; not intrabar', 'sharpe': 'not calculated'}
    analysis = validate_output(Analysis, luna.complete(
        ANALYZE_PROMPT, json.dumps(summary, ensure_ascii=False)))
    return {'backtest': result, 'analysis': analysis,
            'notice': 'Metrics are computed by Python. AI commentary may be inaccurate.'}
