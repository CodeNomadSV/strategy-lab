import json
from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.llm import LunaClient, get_luna

client = TestClient(app)
VALID = {'supported': True, 'strategy': {'strategy': 'sma_cross', 'fast_period': 5, 'slow_period': 20}, 'explanation': 'تقاطع میانگین ساده'}


@pytest.fixture(autouse=True)
def cleanup(monkeypatch):
    monkeypatch.setenv('APMIX_API_KEY', 'unit-test-secret')
    monkeypatch.setenv('APMIX_MODEL', 'gpt-5.6-luna')
    yield
    app.dependency_overrides.clear()


def mock_provider(response=None, status=200, error=None):
    original_client = httpx.Client
    def handle(request):
        if error:
            raise error
        assert str(request.url) == 'https://api.apmix.ai/v1/chat/completions'
        body = json.loads(request.content)
        assert body['model'] == 'gpt-5.6-luna'
        assert body['max_tokens'] == 1800
        assert request.headers['authorization'] == 'Bearer unit-test-secret'
        return httpx.Response(status, json=response)
    return patch('app.llm.httpx.Client', side_effect=lambda **kw: original_client(
        transport=httpx.MockTransport(handle), **kw))


def envelope(content):
    return {'choices': [{'finish_reason': 'stop', 'message': {'content': json.dumps(content)}}]}


def test_parse_http_contract():
    with mock_provider(envelope(VALID)):
        r = client.post('/api/v1/ai/parse', json={'text': 'SMA5 crosses SMA20'})
    assert r.status_code == 200
    assert r.json() == VALID


def test_missing_key_does_not_break_backtests(monkeypatch):
    monkeypatch.delenv('APMIX_API_KEY')
    assert client.post('/api/v1/ai/parse', json={'text': 'SMA5 SMA20'}).status_code == 503
    assert client.get('/health').status_code == 200
    from pathlib import Path
    data = json.loads(Path('examples/request.json').read_text())
    assert client.post('/api/v1/strategies/backtest', json=data).status_code == 200


@pytest.mark.parametrize('status,expected', [(401,503),(403,503),(429,429),(500,502),(400,502),(302,502)])
def test_errors_do_not_leak_provider_body(status, expected):
    with mock_provider({'error': 'unit-test-secret private data'}, status):
        r = client.post('/api/v1/ai/parse', json={'text': 'SMA5 SMA20'})
    assert r.status_code == expected
    assert 'unit-test-secret' not in r.text


@pytest.mark.parametrize('response', [
    {}, {'choices': []}, {'choices': [{'finish_reason':'length', 'message': {'content':'{}'}}]},
    {'choices': [{'finish_reason':'stop', 'message': {'content':'not JSON'}}]},
    envelope({'supported': True, 'strategy': {'strategy':'ema_cross', 'fast_period':5,'slow_period':20}, 'explanation':'unsupported'}),
    envelope({'supported': True, 'strategy': None, 'explanation':'bad'}),
    envelope({'supported': True, 'strategy': {'strategy':'sma_cross','fast_period':20,'slow_period':5},'explanation':'bad'}),
    envelope({**VALID, 'execute': 'print(1)'}),
])
def test_reject_invalid_model_output(response):
    with mock_provider(response):
        assert client.post('/api/v1/ai/parse', json={'text':'SMA5 SMA20'}).status_code == 502


def test_unsupported_strategy_is_explained():
    data = {'supported':False,'strategy':None,'explanation':'EMA هنوز پشتیبانی نمی‌شود.'}
    with mock_provider(envelope(data)):
        assert client.post('/api/v1/ai/parse', json={'text':'EMA5 EMA20'}).json() == data


@pytest.mark.parametrize('error,expected', [(httpx.ReadTimeout('secret'),504),(httpx.ConnectError('secret'),502)])
def test_network_errors(error, expected):
    with mock_provider(error=error):
        r=client.post('/api/v1/ai/parse',json={'text':'SMA5 SMA20'})
    assert r.status_code == expected
    assert 'secret' not in r.text


def test_analyze_uses_python_metrics_and_omits_raw_candles():
    from pathlib import Path
    body=json.loads(Path('examples/request.json').read_text())
    expected=client.post('/backtests',json=body).json()
    class FakeLuna:
        def complete(self, system, user):
            summary=json.loads(user)
            assert summary['total_return_pct'] == expected['total_return_pct']
            assert 'candles' not in summary and 'equity_curve' not in summary
            assert summary['assumptions']['candle_count'] == len(body['candles'])
            return {'summary':'تحلیل نمونه','risks':['داده ساختگی'],'next_steps':['آزمون خارج نمونه']}
    app.dependency_overrides[get_luna]=FakeLuna
    r=client.post('/api/v1/ai/analyze',json=body)
    assert r.status_code == 200
    assert r.json()['backtest'] == expected


def test_invalid_user_input_never_calls_provider():
    with patch.object(LunaClient, 'complete', side_effect=AssertionError('must not call')):
        assert client.post('/api/v1/ai/parse',json={'text':'x'*2001}).status_code == 422
        assert client.post('/api/v1/ai/analyze',json={}).status_code == 422
