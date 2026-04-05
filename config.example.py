# Binance Futures Configuration — Testnet Account
# API Keys: generate at https://www.binance.com/en/my/settings/api-management (enable Testnet mode)
# Testnet API keys are REQUIRED — demo keys don't fill orders.

API_KEY = ""
API_SECRET = ""

# API Endpoints
FUTURES_URL = "https://testnet.binancefuture.com"

# ============ TRADING SETTINGS ============

# Risk Management
STOP_LOSS_PCT = 2.5
TAKE_PROFIT_PCT = 5.0
RISK_PER_TRADE = 0.025  # 2.5% of balance per trade
MAX_POSITIONS = 10  # Maximum concurrent positions
LEVERAGE = 20  # Leverage multiplier

# Scanning Settings
INTERVAL = 120  # seconds between scans
TIMEFRAME = "1h"  # candle timeframe

# Coin Universe — STRICT WHITELIST for quality signals
COINS_WHITELIST = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "DOTUSDT", "LINKUSDT",
    "MATICUSDT", "LTCUSDT", "ATOMUSDT", "UNIUSDT", "ETCUSDT",
    "ARBUSDT", "OPUSDT", "WIFUSDT", "SUIUSDT", "SEIUSDT",
    "TIAUSDT", "JUPUSDT", "WLDUSDT", "RENDERUSDT", "INJUSDT",
    "NEARUSDT", "FILUSDT", "AAVEUSDT", "MKRUSDT", "APTUSDT",
    "SAGAUSDT", "XLMUSDT", "STXUSDT", "AXSUSDT",
]
COIN_UNIVERSE = "whitelist"  # "whitelist" uses COINS_WHITELIST
MIN_VOLUME_24H = 10_000_000  # Minimum 24h volume in USDT

# ============ STRATEGY SETTINGS ============

# Signal Thresholds — stricter for higher win rate
RSI_OVERSOLD = 30       # only extreme oversold
RSI_OVERBOUGHT = 70     # only extreme overbought
MOM_THRESHOLD = 0.15    # small mom OK — EMA filter provides trend confirmation
VOL_RATIO_MIN = 1.5     # volume confirmation
CONF_ALERT = 7          # high conviction — EMA filter adds quality gate anyway

# Dynamic Stop Loss (ATR-based — adapts to each coin's volatility)
USE_DYNAMIC_SL = True
STOP_LOSS_ATR_MULT = 2.0   # ATR multiplier for SL
STOP_LOSS_PCT_FALLBACK = 2.5  # fallback when ATR unavailable

# EMA Trend Filter — only trade in direction of trend
USE_EMA_FILTER = True
EMA_LENGTH = 20

# Partial TP — lock profits at 2:1 risk:reward
USE_PARTIAL_TP = True
TP_1_RATIO = 2.0  # close 50% at 2:1 R:R
TP_2_RATIO = 3.0  # close remaining at 3:1 R:R

# ============ NOTIFICATIONS ============

ENABLE_ALERTS = True
ALERT_ON_ENTRY = True
ALERT_ON_EXIT = True
ALERT_ON_SL = True
ALERT_ON_TP = True

# Discord webhook
DISCORD_WEBHOOK = "YOUR_WEBHOOK_URL_HERE"
DISCORD_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
