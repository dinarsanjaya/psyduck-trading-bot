# Binance Futures Trading Bot

**Skill for automated futures trading on Binance Demo/Testnet**

---

## Overview

This skill enables AI agents to:
- Scan 300+ USDT perpetuals dynamically (no fixed list)
- Execute LONG/SHORT positions automatically
- Monitor positions with auto SL/TP
- Track PnL in real-time

**Mode:** Professor (auto-execute, alert on execution only)

---

## Prerequisites

1. **Binance Demo Account** (testnet)
   - Register: https://testnet.binance.gov
   - Get API Key & Secret from dashboard

2. **Python 3.8+** with dependencies:
   ```
   pandas pandas_ta requests
   ```

3. **OpenClaw** agent running

---

## Installation

### Step 1: Setup Environment

```bash
# Create workspace directory
mkdir -p ~/trading-bot
cd ~/trading-bot

# Create virtual environment
python3 -m venv trading-bot-venv
source trading-bot-venv/bin/activate

# Install dependencies
pip install pandas pandas_ta requests
```

### Step 2: Configure API Keys

Create `config.py` in your trading directory:

```python
API_KEY = "your_binance_demo_api_key"
API_SECRET = "your_binance_demo_secret"
FUTURES_URL = "https://demo-fapi.binance.com"

# Trading settings
STOP_LOSS_PCT = 2.5
TAKE_PROFIT_PCT = 5.0
MAX_POSITIONS = 5
RISK_PER_TRADE = 0.15  # 15% of balance
INTERVAL = 120  # seconds between scans
```

### Step 3: Run the Bot

```bash
source ~/trading-bot/trading-bot-venv/bin/activate
python trading-bot/learn/autopilot.py
```

Run in background:
```bash
nohup python trading-bot/learn/autopilot.py > /tmp/autopilot.log 2>&1 &
echo $!  # Get PID for monitoring
```

---

## Usage Commands

### Check Positions
```python
# Get current PnL for all positions
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

pos = signed_get("/fapi/v2/positionRisk")
for p in pos:
    if float(p['positionAmt']) != 0:
        print(f"{p['symbol']}: ${float(p['unRealizedProfit']):+.2f}")
EOF
```

### Open Position (Long)
```python
# Example: Open LONG on a coin
def open_position(symbol, side, qty):
    data = {
        "symbol": symbol,
        "side": side,  # BUY or SELL
        "type": "MARKET",
        "quantity": qty
    }
    # Sign and send order...
```

### Monitor SL/TP
The bot automatically:
- Closes position if price hits SL (-2.5%)
- Closes position if price hits TP (+5%)

---

## Strategy Indicators

| Indicator | Long Signal | Short Signal |
|-----------|-------------|--------------|
| RSI | < 40 | > 60 |
| MACD | Cross up | Cross down |
| ADX | > 25 | > 25 |
| Volume | > 1.5x avg | > 1.5x avg |

**Minimum Score:** 5 for entry

---

## Coin Universe (Dynamic)

The scanner automatically fetches **all available USDT perpetuals** from Binance. No fixed list needed.

### Default Priority Coins (High Liquidity)
```
BTC, ETH, SOL, BNB, XRP, ADA, DOGE, AVAX, DOT, LINK,
ALGO, FIL, VET, AAVE, GRT, PEPE, WIF, BONK, NEIRO, SUI,
SEI, TIA, JUP, PYTH, OP, RNDR, AXL, INJ, SAGA, JTO
```

### Dynamic Scanning
The bot scans **all USDT-M futures pairs** dynamically:
```python
# Get all USDT pairs automatically
r = requests.get("https://api.binance.com/api/v3/exchangeInfo")
all_coins = [s['symbol'] for s in r.json()['symbols'] 
             if s['symbol'].endswith('USDT') and s['status'] == 'TRADING']
# Result: 300+ coins available
```

### Custom Universe (Optional)
Override in `config.py`:
```python
# Scan specific coins only
COINS = ["BTC", "ETH", "SOL", "PEPE", "WIF"]  # Or None for ALL

# Or use top movers only
SCAN_MODE = "top_movers"  # "all" | "whitelist" | "top_movers"

# Volume filter
MIN_VOLUME_24H = 1_000_000  # USDT
```

---

## Risk Management

| Setting | Value |
|---------|-------|
| Stop Loss | -2.5% |
| Take Profit | +5% |
| Max Positions | 5 |
| Risk per Trade | 15% of balance |
| Leverage | 20x (demo) |

---

## Troubleshooting

### Order Failed: -4120
Demo API doesn't support SL/TP orders via API. Bot handles SL/TP manually by monitoring price levels.

### Module not found
```bash
source ~/trading-bot/trading-bot-venv/bin/activate
pip install pandas pandas_ta requests
```

### Check Bot Status
```bash
tail -f /tmp/autopilot.log
```

---

## For Multi-User Access

### Share with Team

1. **GitHub Backup:**
   ```bash
   cd ~/.openclaw/workspace
   git add trading-bot/
   git commit -m "Trading bot setup"
   git push
   ```

2. **Install on another machine:**
   ```bash
   git clone https://github.com/your-repo/openclaw-backup.git
   cd openclaw-backup
   python3 -m venv trading-bot-venv
   source trading-bot-venv/bin/activate
   pip install pandas pandas_ta requests
   ```

3. **Update API keys** in config.py for each user

### OpenClaw Skill Sync
To make this skill available to other OpenClaw agents:
```bash
cp -r ~/trading-bot ~/.openclaw/workspace/skills/binance-futures/
```

---

## Notes

- **Demo Only:** This setup uses Binance testnet. No real money.
- **Professor Mode:** Bot executes autonomously, alerts on trades only.
- **Paper Trading:** Good for learning before real account.

---

## Example Session

```
User: check pnl
Agent: [runs position check]
  SEIUSDT: +1.44% (+$11.05) 🟢
  NEIROUSDT: +1.44% (+$10.15) 🟢
  Total PnL: +$37.06

User: open 1 more coin
Agent: [scans opportunities]
  Found ALGOUSDT - RSI 69 (overbought)
  Opening SHORT...
  ✅ ALGOUSDT SHORT opened @ $0.1217
```