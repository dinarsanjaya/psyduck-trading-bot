# Binance Futures Trading Bot

> AI-powered automated trading bot for Binance Futures Demo/Testnet

**For OpenClaw AI Agents** — Enables autonomous futures trading with LONG/SHORT strategies.

---

## What This Skill Does

- 🔍 Scans **300+ USDT perpetuals** dynamically
- 📈 LONG when oversold (RSI < 40) + MACD cross up
- 📉 SHORT when overbought (RSI > 60) + MACD cross down
- 🛡️ Auto Stop Loss (-2.5%) & Take Profit (+5%)
- 📊 Real-time PnL monitoring
- 🤖 Professor Mode: executes autonomously, alerts on trades only

---

## Quick Setup

```bash
# 1. Clone this skill
git clone https://github.com/dinarsanjaya/psyduck-trading-bot.git
cd psyduck-trading-bot

# 2. Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install pandas pandas_ta requests

# 3. Configure API keys
# Edit SKILL.md and replace with your Binance testnet keys:
# API_KEY = "your_demo_api_key"
# API_SECRET = "your_demo_secret"
```

### Get Binance Testnet API Keys
1. Web: https://demo.binance.com/ (official demo platform)
2. API: `https://demo-fapi.binance.com`
3. Get API Keys from: https://www.binance.com/en/futures → API Management
4. Login with demo account or link your main account for testnet

---

## Usage

### Check Positions
```python
import hmac, hashlib, time, requests

API_KEY = "your_key"
API_SECRET = "your_secret"
FUTURES_URL = "https://demo-fapi.binance.com"

def signed_get(endpoint):
    ts = int(time.time() * 1000)
    q = f"timestamp={ts}"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    return requests.get(f"{FUTURES_URL}{endpoint}?{q}&signature={sig}",
        headers={"X-MBX-APIKEY": API_KEY}, timeout=15).json()

# Get all positions
pos = signed_get("/fapi/v2/positionRisk")
for p in pos:
    if float(p['positionAmt']) != 0:
        print(f"{p['symbol']}: ${float(p['unRealizedProfit']):+.2f}")
```

### Open Position
```python
def open_position(symbol, side, qty):
    # side: "BUY" for LONG, "SELL" for SHORT
    data = {
        "symbol": symbol,
        "side": side,
        "type": "MARKET",
        "quantity": qty
    }
    # Sign and send via /fapi/v1/order
```

---

## Strategy

### Indicators & Scoring

| Signal | LONG | SHORT |
|--------|------|-------|
| RSI Oversold/Overbought | < 40 (+4) | > 60 (+4) |
| MACD Cross | Up (+3) | Down (+3) |
| Price vs EMA20 | Above (+2) | Below (+2) |
| Volume Spike | > 1.5x (+2) | > 1.5x (+2) |
| 1h/4h Momentum | Negative (+2) | Positive (+2) |

**Minimum Score to Enter:** 5

### Risk Management

| Setting | Value |
|---------|-------|
| Stop Loss | -2.5% |
| Take Profit | +5% |
| Max Positions | 5 |
| Risk per Trade | 15% of balance |
| Leverage | 20x (testnet) |

---

## File Structure

```
psyduck-trading-bot/
├── SKILL.md      # Main skill documentation
└── README.md     # This file
```

---

## For OpenClaw Agents

When you load this skill, you gain the ability to:

1. **Scan markets** — Find opportunities across 300+ USDT pairs
2. **Execute trades** — Open LONG/SHORT with market orders
3. **Monitor positions** — Track PnL, SL/TP levels
4. **Auto-manage risk** — Close positions when SL/TP hit

### Loading the Skill
```
Read SKILL.md in this directory for full implementation details.
```

### Example Session
```
User: open 1 coin
Agent: Scanning opportunities...
  Found PEPE - RSI 72 (overbought) + pump 4%
  Opening SHORT...
  ✅ PEPEUSDT SHORT @ $0.0000123
  
User: check pnl
Agent:
  PEPEUSDT: +2.1% (+$15.42) 🟢
  BTCUSDT: -0.3% (-$2.10)
  Total PnL: +$13.32
```

---

## ⚠️ Disclaimer

- **Demo/Testnet Only** — No real money involved
- Paper trading for learning purposes
- Always review strategies before live trading
- Backtest before applying to real accounts

---

## License

MIT — Use freely, modify, share.

---

**Author:** Psyduck 🐤  
**For OpenClaw AI Agents**
