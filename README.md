# Binance Futures Autopilot

Real-time trading bot for Binance Demo Futures using RSI/MACD/ADX strategy.

## Features

- **548 coins** scanned (ALL USDT-margined perpetual futures)
- RSI + MACD + ADX multi-indicator scoring
- Auto TP/SL at 5% / 2.5%
- WebSocket real-time price monitor
- Fresh restart on position change

## Quick Start

```bash
cd ~/.openclaw/workspace/trading-bot/learn
source ~/.openclaw/workspace/trading-bot-venv/bin/activate

# Run autopilot (100 loops, 30s interval)
python3 -u autopilot.py --iterations 100 --interval 30

# Run real-time monitor (auto restarts on position change)
python3 -u realtime_monitor.py
```

## Commands

```bash
# Status check
python3 -u autopilot.py --mode status

# Autopilot with custom settings
python3 -u autopilot.py --iterations 50 --interval 60

# Kill
pkill -f autopilot.py
```

## Logs

- Autopilot: `tail -f /tmp/autopilot.log`
- Monitor: `tail -f /tmp/realtime.log`

## Config (in autopilot.py)

| Parameter | Default | Description |
|-----------|---------|-------------|
| RSI_PERIOD | 14 | RSI lookback |
| RSI_OVERSOLD | 40 | Buy threshold |
| RSI_OVERBOUGHT | 60 | Sell threshold |
| STOP_LOSS_PCT | 2.5 | Stop loss % |
| TAKE_PROFIT_PCT | 5.0 | Take profit % |
| MAX_POSITIONS | 2 | Max concurrent positions |
| RISK_PERCENT | 0.025 | 2.5% of balance per trade |
