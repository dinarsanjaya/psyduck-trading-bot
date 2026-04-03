"""
Multi-Coin Autopilot - Professor Mode
Binance Demo Futures + RSI/MACD/ADX Strategy
"""
import os
import time
import requests
import hmac
import hashlib
import pandas as pd
import pandas_ta as ta
from datetime import datetime
from multiprocessing import Pool, cpu_count

# ============== CONFIG ==============
API_KEY = os.environ.get("BINANCE_API_KEY", "your_api_key_here")
API_SECRET = os.environ.get("BINANCE_API_SECRET", "your_api_secret_here")

FUTURES_URL = "https://demo-fapi.binance.com"
INTERVAL = "1h"

RSI_PERIOD = 14
RSI_OVERSOLD = 40
RSI_OVERBOUGHT = 60
RISK_PERCENT = 0.025
STOP_LOSS_PCT = 2.5
TAKE_PROFIT_PCT = 5.0
MAX_POSITIONS = 5
MIN_SCORE_BUY = 5
MIN_SCORE_SELL = 3

CONFIRM_FILE = "/tmp/psyduck_pending_trades.txt"

# ============== HTTP HELPERS ==============
def get(endpoint, params=None):
    url = f"{FUTURES_URL}{endpoint}"
    r = requests.get(url, params=params, timeout=15)
    return r.json() if r.status_code == 200 else None

def signed_get(endpoint):
    ts = int(time.time() * 1000)
    q = f"timestamp={ts}"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"{FUTURES_URL}{endpoint}?{q}&signature={sig}"
    r = requests.get(url, headers={"X-MBX-APIKEY": API_KEY}, timeout=15)
    return r.json() if r.status_code == 200 else None

def signed_post(endpoint, data):
    ts = int(time.time() * 1000)
    data['timestamp'] = ts
    q = "&".join([f"{k}={v}" for k,v in data.items()])
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    data['signature'] = sig
    url = f"{FUTURES_URL}{endpoint}"
    r = requests.post(url, data=data, headers={"X-MBX-APIKEY": API_KEY}, timeout=15)
    return r.json() if r.status_code == 200 else r.text

# ============== COINS ==============
def get_all_usdt_symbols():
    """Fetch ALL USDT-margined perpetual futures symbols from Binance"""
    data = get("/fapi/v1/exchangeInfo")
    if data and 'symbols' in data:
        symbols = []
        for s in data['symbols']:
            if s['symbol'].endswith('USDT') and s['status'] == 'TRADING':
                symbols.append(s['symbol'])
        return symbols
    return []

ALL_COINS = get_all_usdt_symbols()
print(f"📡 Loaded {len(ALL_COINS)} USDT symbols from Binance")

# ============== DATA ==============
def get_klines(symbol, limit=100):
    data = get("/fapi/v1/klines", {"symbol": symbol, "interval": INTERVAL, "limit": limit})
    if data and isinstance(data, list):
        df = pd.DataFrame(data)
        df.columns = ['open_time','open','high','low','close','volume','close_time',
                      'quote_volume','trades','taker_buy_base','taker_buy_quote','ignore']
        df['open'] = pd.to_numeric(df['open'])
        df['high'] = pd.to_numeric(df['high'])
        df['low'] = pd.to_numeric(df['low'])
        df['close'] = pd.to_numeric(df['close'])
        df['volume'] = pd.to_numeric(df['volume'])
        return df
    return None

def get_price(symbol):
    data = get("/fapi/v1/ticker/price", {"symbol": symbol})
    return float(data['price']) if data else None

# Cache step sizes from exchange info
_STEP_CACHE = {}

def _load_step_sizes():
    global _STEP_CACHE
    if _STEP_CACHE:
        return
    data = get("/fapi/v1/exchangeInfo")
    if data and 'symbols' in data:
        for sym in data['symbols']:
            for f in sym['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    _STEP_CACHE[sym['symbol']] = {
                        'stepSize': float(f['stepSize']),
                        'minQty': float(f['minQty'])
                    }
                    break

def _round_qty(qty, symbol):
    """Round quantity to exchange step size, minimum quantity, and integer constraints."""
    _load_step_sizes()
    if symbol not in _STEP_CACHE:
        return round(qty, 3)
    info = _STEP_CACHE[symbol]
    step = info['stepSize']
    min_qty = info['minQty']
    if step >= 1:
        return max(int(round(qty)), int(min_qty))
    decimals = len(str(step).rstrip('0').split('.')[-1])
    return round(max(qty, min_qty), decimals)

def get_balance():
    data = signed_get("/fapi/v2/account")
    if data and 'assets' in data:
        for b in data['assets']:
            if b['asset'] == 'USDT':
                return float(b['availableBalance'])
    return None

def get_positions():
    data = signed_get("/fapi/v2/positionRisk")
    positions = {}
    if data and isinstance(data, list):
        for p in data:
            if float(p['positionAmt']) != 0:
                positions[p['symbol']] = {
                    'amount': float(p['positionAmt']),
                    'entry': float(p['entryPrice']),
                    'pnl': float(p['unRealizedProfit'])
                }
    return positions

# ============== ANALYSIS ==============
def analyze_coin(symbol):
    df = get_klines(symbol, 100)
    if df is None or len(df) < 50:
        return None
    try:
        close = df['close']
        rsi = ta.rsi(close, length=RSI_PERIOD).iloc[-1]
        macd = ta.macd(close, fast=12, slow=26, signal=9)
        macd_hist = macd['MACDh_12_26_9'].iloc[-1]
        macd_hist_prev = macd['MACDh_12_26_9'].iloc[-2]
        adx_val = ta.adx(df['high'], df['low'], close, length=14)['ADX_14'].iloc[-1]
        ema20 = ta.ema(close, length=20).iloc[-1]
        price = close.iloc[-1]

        score = 0
        reasons = []

        if rsi < 35:
            score += 4
            reasons.append(f"RSI deep oversold ({rsi:.0f})")
        elif rsi < RSI_OVERSOLD:
            score += 2
            reasons.append(f"RSI oversold ({rsi:.0f})")
        elif rsi > 65:
            score -= 3
            reasons.append(f"RSI overbought ({rsi:.0f})")

        if macd_hist > 0 and macd_hist_prev <= 0:
            score += 4
            reasons.append("MACD golden cross")
        elif macd_hist < 0 and macd_hist_prev >= 0:
            score -= 3
            reasons.append("MACD death cross")
        elif macd_hist > 0:
            score += 1

        if adx_val > 25 and macd_hist > 0:
            score += 2
            reasons.append(f"Strong uptrend (ADX={adx_val:.0f})")

        if price > ema20:
            score += 2
            reasons.append("EMA uptrend")

        signal = "BUY" if score >= MIN_SCORE_BUY else ("SELL" if score <= -MIN_SCORE_SELL else "HOLD")

        return {
            'symbol': symbol,
            'price': price,
            'rsi': rsi,
            'macd_hist': macd_hist,
            'adx': adx_val,
            'score': score,
            'signal': signal,
            'reasons': reasons
        }
    except:
        return None

def _analyze_worker(symbol):
    """Top-level worker for multiprocessing (must be picklable)"""
    return analyze_coin(symbol)

def scan_all():
    n_workers = min(cpu_count(), 8, len(ALL_COINS))
    with Pool(n_workers) as pool:
        results = pool.map(_analyze_worker, ALL_COINS)
    results = [r for r in results if r is not None]
    results.sort(key=lambda x: x['score'], reverse=True)
    return results

# ============== TRADING ==============
def buy(symbol, quantity):
    qty = _round_qty(quantity, symbol)
    data = signed_post("/fapi/v1/order", {
        "symbol": symbol, "side": "BUY", "type": "MARKET", "quantity": qty
    })
    if 'orderId' in data:
        print(f"  ✅ BUY {qty} {symbol}")
        return True
    print(f"  ❌ Failed: {data}")
    return False

def sell(symbol, quantity):
    qty = _round_qty(quantity, symbol)
    data = signed_post("/fapi/v1/order", {
        "symbol": symbol, "side": "SELL", "type": "MARKET", "quantity": qty
    })
    if 'orderId' in data:
        print(f"  ✅ SELL {qty} {symbol}")
        return True
    print(f"  ❌ Failed: {data}")
    return False

def close_position(symbol):
    pos = get_positions()
    if symbol in pos:
        return sell(symbol, abs(pos[symbol]['amount']))
    return False

# ============== MAIN ==============
def status():
    print("\n" + "="*60)
    print("🤖 AUTOPILOT STATUS")
    print("="*60)
    bal = get_balance()
    print(f"Balance: ${bal:.2f}" if bal else "Balance: N/A")
    positions = get_positions()
    if positions:
        for sym, p in positions.items():
            print(f"{sym}: {p['amount']} @ ${p['entry']:.4f} | PnL: ${p['pnl']:.2f}")
    else:
        print("Positions: NONE")
    print("="*60)

def run(iterations=100, interval=120, confirm_before_trade=True):
    print(f"\n🚀 Starting autopilot: {len(ALL_COINS)} coins, {interval}s interval")
    print(f"📋 Confirm before trade: {'ON' if confirm_before_trade else 'OFF'}")

    for i in range(iterations):
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Loop {i+1}/{iterations}")

        # Scan with timing
        t0 = time.time()
        results = scan_all()
        scan_duration = time.time() - t0
        print(f"  ⏱️  Scanned {len(ALL_COINS)} coins in {scan_duration:.1f}s ({len(ALL_COINS)/scan_duration:.0f} coins/sec)")

        positions = get_positions()
        bal = get_balance()

        buys = [r for r in results if r['signal'] == 'BUY']
        sells = [r for r in results if r['signal'] == 'SELL']

        print(f"  📊 BUY signals: {len(buys)} | SELL signals: {len(sells)}")
        if buys:
            for r in buys[:5]:
                print(f"     • {r['symbol']}: score={r['score']} | RSI={r['rsi']:.0f} | {' | '.join(r['reasons'])}")

        # Check existing positions
        for sym, pos in list(positions.items()):
            price = get_price(sym)
            if price:
                pnl_pct = (price - pos['entry']) / pos['entry'] * 100
                print(f"  {sym}: {pnl_pct:+.2f}%")

                if pnl_pct <= -STOP_LOSS_PCT:
                    print(f"    🛑 STOP LOSS!")
                    close_position(sym)
                elif pnl_pct >= TAKE_PROFIT_PCT:
                    print(f"    🎯 TAKE PROFIT!")
                    close_position(sym)

        # Open new positions (with confirmation)
        open_slots = MAX_POSITIONS - len(positions)
        if open_slots > 0 and buys and bal and bal > 50:
            pending = []
            for r in buys[:open_slots]:
                qty = round((bal * RISK_PERCENT) / r['price'], 3)
                if qty > 0:
                    pending.append({
                        'symbol': r['symbol'],
                        'price': r['price'],
                        'qty': qty,
                        'score': r['score'],
                        'reasons': r['reasons']
                    })

            if pending:
                # Write pending trades to file
                with open(CONFIRM_FILE, 'w') as f:
                    f.write(f"# Pending trades at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    for p in pending:
                        f.write(f"BUY|{p['symbol']}|{p['price']}|{p['qty']}|{p['score']}\n")
                    f.write("# Add 'EXECUTE' (without quotes) to this file to confirm, or delete to skip.\n")

                print(f"\n  ⏸️  PENDING CONFIRMATION ({len(pending)} trade(s)):")
                for p in pending:
                    print(f"     → BUY {p['symbol']} {p['qty']} @ ${p['price']:.4f} (score={p['score']})")
                print(f"\n  ⚠️  CONFIRM REQUIRED — edit '{CONFIRM_FILE}' to approve")
                print(f"     echo EXECUTE >> {CONFIRM_FILE}")

                if confirm_before_trade:
                    confirmed = False
                    while not confirmed:
                        time.sleep(10)
                        if not os.path.exists(CONFIRM_FILE):
                            print(f"  ⏭️  Skipped (file removed)")
                            confirmed = True
                            break
                        with open(CONFIRM_FILE, 'r') as f:
                            content = f.read().strip()
                        if 'EXECUTE' in content.upper():
                            confirmed = True
                            print(f"  ✅ Execution approved!")
                            os.remove(CONFIRM_FILE)
                            break
                        # else: keep waiting
                        print(f"  ⏳ Waiting for confirmation... ({datetime.now().strftime('%H:%M:%S')})")

                    # Execute confirmed trades
                    if confirmed and os.path.exists(CONFIRM_FILE):
                        pass  # already handled above
                    elif confirmed:
                        for p in pending:
                            buy(p['symbol'], p['qty'])
                            bal -= p['qty'] * p['price']
                else:
                    for p in pending:
                        buy(p['symbol'], p['qty'])
                        bal -= p['qty'] * p['price']

        if i < iterations - 1:
            time.sleep(interval)

    print("\n✅ Done!")
    status()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['status', 'autopilot'], default='autopilot')
    parser.add_argument('--iterations', type=int, default=100)
    parser.add_argument('--interval', type=int, default=120)
    parser.add_argument('--no-confirm', action='store_true', help='Skip confirmation before trade')
    args = parser.parse_args()

    if args.mode == 'status':
        status()
    else:
        run(iterations=args.iterations, interval=args.interval, confirm_before_trade=not args.no_confirm)
