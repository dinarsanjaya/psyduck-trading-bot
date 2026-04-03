# Binance Futures Trading Bot

**Skill for automated futures trading on Binance Demo/Testnet**

---

## Overview

This skill enables AI agents to:
- 🔍 Scan **548 USDT perpetuals** dynamically (no fixed list)
- 📈 Execute **LONG/SHORT** positions automatically
- ⚡ **Real-time** position monitoring via WebSocket (<100ms updates)
- 🛡️ Auto **SL/TP** with instant execution when levels hit
- 📊 Track **PnL in USD** (not percentage)
- 🤖 **Professor Mode:** executes autonomously, alerts on trades only

---

## Prerequisites

1. **Binance Demo Account** (testnet)
   - Web: https://demo.binance.com/ (official demo platform)
   - API: `https://demo-fapi.binance.com`
   - Get API Keys from: https://www.binance.com/en/futures → API Management

2. **Python 3.8+** with dependencies:
   ```
   pandas pandas_ta requests websocket-client
   ```

3. **OpenClaw** agent running

---

## Installation

### Step 1: Setup Environment

```bash
# Clone the skill
git clone https://github.com/dinarsanjaya/psyduck-trading-bot.git
cd psyduck-trading-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure API Keys

**Option A: Environment variables (recommended for quick setup)**
```bash
export BINANCE_API_KEY="your_demo_api_key"
export BINANCE_API_SECRET="your_demo_api_secret"
```

**Option B: config.py file**
```bash
cp config.py.example config.py
# Edit config.py and add your API keys
```

### Step 3: Run

**Autopilot (scanning + auto-trade):**
```bash
source venv/bin/activate
nohup python learn/autopilot.py > /tmp/autopilot.log 2>&1 &
echo "PID: $!"
```

**Real-Time Monitor (WebSocket - auto TP/SL):**
```bash
source venv/bin/activate
nohup python realtime_monitor.py > /tmp/realtime.log 2>&1 &
echo "PID: $!"
```

**Run both for full automation:**
```bash
# Autopilot: scans markets, opens positions
# Monitor: watches positions, closes on TP/SL
```

---

## File Structure

```
psyduck-trading-bot/
├── SKILL.md                    # This file (for AI agents)
├── README.md                   # Quick overview
├── requirements.txt            # Python dependencies
├── config.py.example           # Configuration template
├── setup_check.py             # Verify setup
├── learn/
│   ├── autopilot.py            # Market scanner + auto-trade
│   └── realtime_monitor.py     # WebSocket TP/SL monitor
└── .gitignore
```

---

## Key Features

### 1. Autopilot - Market Scanner
- Scans 300+ USDT pairs for opportunities
- Long when RSI < 40 + MACD cross up
- Short when RSI > 60 + MACD cross down
- Auto-opens positions with 15% risk per trade

### 2. Real-Time Monitor - WebSocket Based
- **<100ms price updates** (vs 2-minute polling)
- **Auto-detects new positions** every 30 seconds
- **Auto-adds** new coins to WebSocket stream
- **Instant TP/SL execution** when levels hit
- No manual intervention needed

### 3. PnL Tracking
- All values in **USD** (not percentage)
- Real-time balance updates
- Per-position and total PnL

---

## Usage Commands

### Check PnL (USD)
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

## Strategy Indicators

| Indicator | Long Signal | Short Signal |
|-----------|-------------|--------------|
| RSI | < 40 (+4) | > 60 (+4) |
| MACD | Cross up (+3) | Cross down (+3) |
| Price vs EMA20 | Above (+2) | Below (+2) |
| Volume Spike | > 1.5x (+2) | > 1.5x (+2) |
| Momentum | Negative (+2) | Positive (+2) |

**Minimum Score to Enter:** 5

---

## Risk Management

| Setting | Value |
|---------|-------|
| Stop Loss | -2.5% |
| Take Profit | +5% |
| Max Positions | 5 |
| Risk per Trade | 15% of balance |
| Leverage | 20x (testnet) |

---

## WebSocket Monitor Flow

```
┌─────────────────────────────────────────────────────┐
│  1. Load positions from API                        │
│  2. Setup WebSocket stream for all symbols          │
│  3. Monitor price in REAL-TIME (<100ms)            │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │  Every 30 seconds:                          │   │
│  │  - Check for new positions                  │   │
│  │  - Auto-add new coins to stream             │   │
│  │  - Auto-remove closed positions             │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  When TP or SL hit:                                │
│  → Instant MARKET order to close                   │
└─────────────────────────────────────────────────────┘
```

---

## Coin Universe (Dynamic)

No fixed list. Scanner fetches all available USDT-M futures pairs dynamically.

**Default priority coins:**
```
BTC, ETH, SOL, BNB, XRP, ADA, DOGE, AVAX, DOT, LINK,
ALGO, FIL, VET, AAVE, GRT, PEPE, WIF, BONK, NEIRO, SUI,
SEI, TIA, JUP, PYTH, OP, RNDR, AXL, INJ, SAGA, JTO
```

**Override in config:**
```python
COINS = None              # None = all coins
COINS = ["BTC", "ETH"]   # Or specific list
SCAN_MODE = "all"         # "all" | "whitelist" | "top_movers"
```

---

## Troubleshooting

### Module not found
```bash
pip install -r requirements.txt
```

### Check Bot Status
```bash
# Autopilot log
tail -f /tmp/autopilot.log

# Real-time monitor log
tail -f /tmp/realtime.log
```

### Restart Monitor
```bash
pkill -f "realtime_monitor"
source venv/bin/activate
nohup python realtime_monitor.py > /tmp/realtime.log 2>&1 &
```

---

## For Multi-User Access

### Install on Another Machine
```bash
git clone https://github.com/dinarsanjaya/psyduck-trading-bot.git
cd psyduck-trading-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp config.py.example config.py
# Edit config.py with your API keys
```

### OpenClaw Skill Sync
```bash
cp -r psyduck-trading-bot ~/.openclaw/workspace/skills/binance-futures/
openclaw gateway restart
```

---

## Notes

- **Demo Only:** Uses Binance testnet. No real money.
- **Paper Trading:** Good for learning before live account.
- **Real-Time:** WebSocket gives <100ms updates, not 2-minute polling
- **Auto-Update:** Monitor auto-detects new positions, no restart needed

---

## Example Session

```
User: check pnl
Agent:
  SEIUSDT: +$7.73 🟢
  NEIROUSDT: +$0.79
  ALGOUSDT: +$8.40 🟢
  VETUSDT: +$9.15 🟢
  GRTUSDT: -$6.30 🔴
  
  Balance: $4,833
  Total PnL: +$19.77

User: open 1 more coin
Agent: [scans]
  Found PEPE - RSI 72 (overbought) + pump 4%
  Opening SHORT...
  ✅ PEPEUSDT SHORT opened @ $0.0000123
  
  [Monitor auto-updates, adds PEPE to WebSocket stream]
```

---

**Author:** Psyduck 🐤  
**For OpenClaw AI Agents
