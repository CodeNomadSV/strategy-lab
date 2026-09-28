from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def payload(closes=None):
    closes = closes or [3, 2, 1, 4, 5, 2, 1]
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    return dict(fast_period=1, slow_period=2, initial_capital=1000,
                fee_bps=0, slippage_bps=0, candles=[
        dict(timestamp=(start + timedelta(days=i)).isoformat(),
             open=p, high=p, low=p, close=p) for i, p in enumerate(closes)])


def test_health():
    assert client.get('/health').json() == {'status': 'ok'}


def test_hand_calculated_next_open_fills():
    body = payload()
    r = client.post('/backtests', json=body)
    assert r.status_code == 200
    result = r.json()
    trade = result['trades'][0]
    assert trade['entry_price'] == 5
    assert trade['exit_price'] == 1
    assert trade['entry_time'] == body['candles'][4]['timestamp']
    assert result['final_equity'] == pytest.approx(200)
    assert result['total_return_pct'] == pytest.approx(-80)
    assert result['max_drawdown_pct'] == pytest.approx(-80)


def test_costs_are_charged_on_both_sides():
    body = payload()
    body.update(fee_bps=100, slippage_bps=100)
    result = client.post('/backtests', json=body).json()
    expected_units = 1000 / (5 * 1.01 * 1.01)
    assert result['final_equity'] == pytest.approx(expected_units * .99 * .99)
    assert result['trades'][0]['pnl'] == pytest.approx(result['final_equity'] - 1000)


def test_no_cross_no_trade():
    r = client.post('/backtests', json=payload([2]*8)).json()
    assert r['trade_count'] == 0
    assert r['win_rate_pct'] is None
    assert r['final_equity'] == 1000


def test_terminal_liquidation():
    result = client.post('/backtests', json=payload([3, 2, 1, 4, 5, 6])).json()
    assert result['trades'][0]['exit_reason'] == 'end_of_data'
    assert result['final_equity'] == pytest.approx(1200)


def test_last_signal_not_filled():
    result = client.post('/backtests', json=payload([3, 2, 1, 4])).json()
    assert result['trade_count'] == 0


@pytest.mark.parametrize('case', ['periods', 'order', 'duplicate', 'ohlc', 'zero', 'timezone', 'short', 'unknown', 'fee'])
def test_invalid_input(case):
    body = payload()
    if case == 'periods': body['fast_period'] = 3
    if case == 'order': body['candles'].reverse()
    if case == 'duplicate': body['candles'][1]['timestamp'] = body['candles'][0]['timestamp']
    if case == 'ohlc': body['candles'][0]['high'] = 1
    if case == 'zero': body['candles'][0]['close'] = 0
    if case == 'timezone': body['candles'][0]['timestamp'] = '2025-01-01T00:00:00'
    if case == 'short': body['slow_period'] = 50
    if case == 'unknown': body['strategy'] = 'made_up'
    if case == 'fee': body['fee_bps'] = -1
    assert client.post('/backtests', json=body).status_code == 422


def test_future_data_does_not_change_prior_equity():
    original = payload()
    modified = payload()
    modified['candles'][-1].update(open=20, high=20, low=20, close=20)
    a = client.post('/backtests', json=original).json()
    b = client.post('/backtests', json=modified).json()
    assert a['equity_curve'][:-1] == b['equity_curve'][:-1]
