# Binance Futures Trading Bot

> AI-powered automated trading bot for Binance Futures Demo/Testnet

**For OpenClaw AI Agents** — Enables autonomous futures trading with real-time WebSocket monitoring.

---

## What This Skill Does

- 🔍 Scans **300+ USDT perpetuals** dynamically
- 📈 LONG when oversold (RSI < 40) + MACD cross up
- 📉 SHORT when overbought (RSI > 60) + MACD cross down
- ⚡ **Real-time monitoring** via WebSocket (<100ms updates)
- 🛡️ Auto **Stop Loss (-2.5%)** & **Take Profit (+5%)**
- 📊 **PnL in USD** (not percentage)
- 🤖 Professor Mode: executes autonomously, alerts on trades only

---

## Quick Setup

```bash
# 1. Clone
git clone https://github.com/dinarsanjaya/psyduck-trading-bot.git
cd psyduck-trading-bot

# 2. Install
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configure
cp config.py.example config.py
# Edit config.py with your API keys

# 4. Run both components
nohup python learn/autopilot.py > /tmp/autopilot.log 2>&1 &
nohup python realtime_monitor.py > /tmp/realtime.log 2>&1 &
```

### Get API Keys
1. Web: https://demo.binance.com/
2. API: https://demo-fapi.binance.com
3. Get keys: https://www.binance.com/en/futures → API Management

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    BINANCE FUTURES BOT                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐      ┌──────────────────────────────┐   │
│  │  AUTOPILOT   │      │    REALTIME MONITOR          │   │
│  │  (Scanner)   │      │    (WebSocket)               │   │
│  │              │      │                              │   │
│  │  • Scanning  │      │  • <100ms price updates      │   │
│  │  • Signals   │      │  • Auto-detect positions     │   │
│  │  • Open pos  │────▶│  • Auto-add/remove coins     │   │
│  │              │      │  • Instant TP/SL execution   │   │
│  └──────────────┘      └──────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
psyduck-trading-bot/
├── SKILL.md                    # Full documentation (for AI)
├── README.md                   # This file
├── requirements.txt            # Dependencies
├── config.py.example           # Config template
├── setup_check.py              # Setup verifier
├── learn/
│   ├── autopilot.py            # Market scanner + auto-trade
│   └── realtime_monitor.py     # WebSocket TP/SL monitor
└── .gitignore
```

---

## Key Features

### Real-Time WebSocket Monitor
- **<100ms price updates** — no 2-minute polling lag
- **Auto-detects new positions** every 30 seconds
- **Auto-adds new coins** to WebSocket stream
- **Instant TP/SL execution** when levels hit
- **Silent operation** — only logs on TP/SL trigger

### Autopilot Scanner
- Scans 300+ USDT pairs
- LONG/SHORT with RSI + MACD + ADX + Volume
- Auto risk management (2.5% SL, 5% TP)
- 15% risk per trade, max 5 positions

### PnL in USD
- All values shown in USD
- Real-time balance tracking
- Per-position and total PnL

---

## Usage

### Check PnL
```bash
python3 << 'EOF'
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

bal = signed_get("/fapi/v2/account")
usdt = float(bal['availableBalance'])
pos = signed_get("/fapi/v2/positionRisk")
total_pnl = 0

for p in pos:
    if float(p['positionAmt']) != 0:
        pnl = float(p['unRealizedProfit'])
        total_pnl += pnl
        print(f"{p['symbol']}: ${pnl:+.2f}")

print(f"\nBalance: ${usdt:.2f}")
print(f"Total PnL: ${total_pnl:+.2f}")
EOF
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

## Configuration

Edit `config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `STOP_LOSS_PCT` | 2.5 | Stop loss % |
| `TAKE_PROFIT_PCT` | 5.0 | Take profit % |
| `RISK_PER_TRADE` | 0.15 | 15% of balance |
| `MAX_POSITIONS` | 5 | Max concurrent |
| `LEVERAGE` | 20 | Leverage |
| `INTERVAL` | 120 | Scan interval (sec) |
| `SCAN_MODE` | "all" | all/whitelist/top_movers |

---

## Strategy

### Indicators & Scoring

| Signal | LONG | SHORT |
|--------|------|-------|
| RSI Oversold/Overbought | < 40 (+4) | > 60 (+4) |
| MACD Cross | Up (+3) | Down (+3) |
| Price vs EMA20 | Above (+2) | Below (+2) |
| Volume Spike | > 1.5x (+2) | > 1.5x (+2) |
| Momentum | Negative (+2) | Positive (+2) |

**Minimum Score:** 5 to enter

### Risk Management

| Setting | Value |
|---------|-------|
| Stop Loss | -2.5% |
| Take Profit | +5% |
| Max Positions | 5 |
| Risk per Trade | 15% |
| Leverage | 20x (testnet) |

---

## Example Session

```
User: check pnl
Agent:
  SEIUSDT: +$7.73 🟢
  ALGOUSDT: +$8.40 🟢
  VETUSDT: +$9.15 🟢
  NEIROUSDT: +$0.79
  GRTUSDT: -$6.30 🔴
  
  Balance: $4,833
  Total PnL: +$19.77

User: open 1 more coin
Agent: Scanning...
  Found PEPE - RSI 72 + pump 4%
  Opening SHORT...
  ✅ PEPEUSDT SHORT opened
  
  [Monitor auto-adds PEPE to stream]
```

---

## ⚠️ Disclaimer

- **Demo/Testnet Only** — No real money
- Paper trading for learning
- Always review before live trading
- Backtest strategies first

---

## License

MIT — Use freely, modify, share.

---

**Author:** Psyduck 🐤  
**For OpenClaw AI Agents**
