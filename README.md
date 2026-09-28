# Strategy Lab

An independent Python portfolio project: a long-only SMA crossover backtesting API.
Not affiliated with SetupTrack. Version 0.1 is an educational MVP, not a trading platform.

## What works

- FastAPI endpoints, interactive `/docs`, typed input validation.
- SMA cross signals calculated using completed candle closes.
- Execution at the **next candle open**, including configurable fees and adverse slippage.
- Trade ledger, equity curve, net return, closed-trade win rate and close-to-close maximum drawdown.
- Hand-calculated engine tests and API validation tests; GitHub Actions workflow.
- Dockerfile and deterministic synthetic example data (not historical market data).

## Run locally (Python 3.11+)

```bash
python -m venv .venv
```

Activate on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Or on Linux/macOS:

```bash
source .venv/bin/activate
```

Then:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs. Select `POST /backtests`, click **Try it out**, paste
`examples/request.json`, then **Execute**. Alternatively, in another terminal:

```bash
curl -X POST http://127.0.0.1:8000/backtests -H "Content-Type: application/json" --data-binary @examples/request.json
```

On Windows use `curl.exe` instead of `curl`.

## Docker

```bash
docker build -t strategy-lab .
docker run --rm -p 127.0.0.1:8000:8000 strategy-lab
```

## Design

`app/models.py` validates data; `app/engine.py` implements the pure simulation;
`app/main.py` exposes it over HTTP. Results are not persisted yet.

A positive SMA difference after a nonpositive difference schedules a buy; the
opposite crossing schedules a sell. The initial SMA observation does not trigger
an entry. Positions invest all available cash with fractional units, no leverage
and no short selling. Fees apply on both entry and exit; 10 bps equals 0.1%.
The final position is forcibly closed at the last close with fees and slippage;
this is reported as `end_of_data`. Last-bar signals are ignored.

Equity is marked at candle closes, and drawdown includes initial capital as its
first peak. Drawdown is returned as a nonpositive percentage. Win rate is null
when there are no closed trades. Breakeven trades are not wins. No annualized
Sharpe is reported because bar frequency and risk-free-rate assumptions are not
specified. Gaps are accepted: “next open” means the next supplied candle.

Limits: maximum 10,000 candles/request; no liquidity, volume constraints, spread
model beyond slippage, intrabar drawdown, dividends, corporate actions, funding,
margin or taxes. Float arithmetic is appropriate for this prototype, not exchange
accounting. No authentication, request-body byte limit, rate limiting or persistence:
run locally; do not expose publicly as a production service.

## Learning roadmap

1. Explain request validation and the next-open fill test in your own words.
2. Add CSV ingestion with timezone and duplicate validation.
3. Add PostgreSQL persistence, SQLAlchemy and Alembic migrations.
4. Add EMA/RSI as separately tested strategies.
5. Add an LLM adapter that produces a validated strategy schema (never executes generated code).
6. Add authentication, background jobs, limits and deployment configuration.
7. Add reproducible historical datasets and out-of-sample evaluation.

## Get the project from GitHub

```bash
git clone https://github.com/CodeNomadSV/strategy-lab.git
cd strategy-lab
```

Then follow the local setup above. Read `START_HERE_FA.md` for the Persian guide.

## References

- https://fastapi.tiangolo.com/tutorial/testing/
- https://docs.python.org/3/library/venv.html
