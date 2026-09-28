"""Long-only SMA crossover. Decisions use completed closes; fills use next open."""
from app.models import BacktestRequest


def run_backtest(request: BacktestRequest) -> dict:
    bars = request.candles
    fee, slip = request.fee_bps / 10000, request.slippage_bps / 10000
    cash = request.initial_capital
    units = 0.0
    pending = None
    entry = None
    previous_diff = None
    fast_sum = slow_sum = 0.0
    trades, curve = [], []
    peak = cash
    max_drawdown = 0.0

    def sell(price, timestamp, reason):
        nonlocal cash, units, entry
        fill = price * (1 - slip)
        gross = units * fill
        cash = gross * (1 - fee)
        trades.append({**entry, 'exit_time': timestamp.isoformat(),
                       'exit_price': fill, 'exit_fee': gross * fee,
                       'pnl': cash - entry['cost'], 'exit_reason': reason})
        units, entry = 0.0, None

    for i, bar in enumerate(bars):
        if pending == 'buy' and units == 0:
            fill = bar.open * (1 + slip)
            units = cash / (fill * (1 + fee))
            entry = {'entry_time': bar.timestamp.isoformat(), 'entry_price': fill,
                     'quantity': units, 'entry_fee': units * fill * fee, 'cost': cash}
            cash = 0.0
        elif pending == 'sell' and units:
            sell(bar.open, bar.timestamp, 'cross_below')
        pending = None

        fast_sum += bar.close
        slow_sum += bar.close
        if i >= request.fast_period:
            fast_sum -= bars[i - request.fast_period].close
        if i >= request.slow_period:
            slow_sum -= bars[i - request.slow_period].close
        if i >= request.slow_period - 1:
            diff = fast_sum / request.fast_period - slow_sum / request.slow_period
            if previous_diff is not None:
                if previous_diff <= 0 < diff:
                    pending = 'buy'
                elif previous_diff >= 0 > diff:
                    pending = 'sell'
            previous_diff = diff

        # Explicit terminal liquidation; last-close signals are never executed.
        if i == len(bars) - 1 and units:
            sell(bar.close, bar.timestamp, 'end_of_data')
        equity = cash + units * bar.close
        peak = max(peak, equity)
        max_drawdown = min(max_drawdown, equity / peak - 1)
        curve.append({'timestamp': bar.timestamp.isoformat(), 'equity': equity})

    return {'symbol': request.symbol, 'strategy': request.strategy,
            'initial_capital': request.initial_capital, 'final_equity': cash,
            'total_return_pct': (cash / request.initial_capital - 1) * 100,
            'max_drawdown_pct': max_drawdown * 100,
            'win_rate_pct': (100 * sum(t['pnl'] > 0 for t in trades) / len(trades)) if trades else None,
            'trade_count': len(trades), 'trades': trades, 'equity_curve': curve}
