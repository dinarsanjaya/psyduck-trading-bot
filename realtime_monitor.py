#!/usr/bin/env python3
"""
Real-Time Trade Monitor - WebSocket Based
Monitors positions with <100ms price updates
Fresh instance per session - auto-restarts on new positions
"""

import json
import hmac
import hashlib
import time
import os
import sys
import signal
from websocket import create_connection, WebSocketConnectionClosedException

API_KEY = os.environ.get("BINANCE_API_KEY", "your_api_key_here")
API_SECRET = os.environ.get("BINANCE_API_SECRET", "your_api_secret_here")
FUTURES_URL = "https://demo-fapi.binance.com"
WS_URL = "wss://stream.binance.com:9443/ws"

POSITIONS = {}
PRICES = {}
ws = None
running = True

def signed_post(endpoint, data):
    ts = int(time.time() * 1000)
    data['timestamp'] = ts
    q = "&".join([f"{k}={v}" for k,v in data.items()])
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    data['signature'] = sig
    import requests
    r = requests.post(f"{FUTURES_URL}{endpoint}", data=data, 
                     headers={"X-MBX-APIKEY": API_KEY}, timeout=15)
    return r.json()

def get_positions():
    ts = int(time.time() * 1000)
    q = f"timestamp={ts}"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    import requests
    r = requests.get(f"{FUTURES_URL}/fapi/v2/positionRisk?{q}&signature={sig}",
                    headers={"X-MBX-APIKEY": API_KEY}, timeout=15)
    return r.json()

def close_position(symbol, side, qty):
    close_side = "BUY" if side == "SHORT" else "SELL"
    print(f"🔴 CLOSING {symbol} ({close_side})...")
    
    result = signed_post("/fapi/v1/order", {
        "symbol": symbol,
        "side": close_side,
        "type": "MARKET",
        "quantity": qty
    })
    
    if 'orderId' in result:
        print(f"✅ {symbol} CLOSED! Order ID: {result['orderId']}")
        return True
    else:
        print(f"❌ Close failed: {result}")
        return False

def check_and_close(symbol, current_price):
    if symbol not in POSITIONS:
        return
    
    p = POSITIONS[symbol]
    entry = p['entry']
    side = p['side']
    sl = p['sl']
    tp = p['tp']
    qty = p['amount']
    
    if side == "SHORT":
        if current_price <= tp:
            print(f"🎯 {symbol} TP HIT! ${current_price} <= ${tp}")
            close_position(symbol, side, qty)
        elif current_price >= sl:
            print(f"🛑 {symbol} SL HIT! ${current_price} >= ${sl}")
            close_position(symbol, side, qty)
    else:
        if current_price >= tp:
            print(f"🎯 {symbol} TP HIT! ${current_price} >= ${tp}")
            close_position(symbol, side, qty)
        elif current_price <= sl:
            print(f"🛑 {symbol} SL HIT! ${current_price} <= ${sl}")
            close_position(symbol, side, qty)

def load_positions():
    global POSITIONS
    pos_data = get_positions()
    
    old_keys = set(POSITIONS.keys())
    new_positions = {}
    
    for p in pos_data:
        amt = float(p['positionAmt'])
        if amt == 0:
            continue
            
        symbol = p['symbol']
        entry = float(p['entryPrice'])
        side = "SHORT" if amt < 0 else "LONG"
        qty = abs(amt)
        
        if side == "SHORT":
            sl = entry * 1.025
            tp = entry * 0.95
        else:
            sl = entry * 0.975
            tp = entry * 1.05
        
        new_positions[symbol] = {
            'entry': entry,
            'side': side,
            'amount': qty,
            'sl': sl,
            'tp': tp
        }
    
    POSITIONS = new_positions
    added = set(POSITIONS.keys()) - old_keys
    removed = old_keys - set(POSITIONS.keys())
    
    return added, removed, set(POSITIONS.keys())

def restart_fresh():
    """Kill self and restart with current positions"""
    global running
    print("\n🔄 Restarting fresh...")
    running = False
    os.execv(sys.executable, [sys.executable] + sys.argv)

def signal_handler(sig, frame):
    global running
    print("\n🛑 Shutting down...")
    running = False
    sys.exit(0)

def main():
    global ws, running
    
    signal.signal(signal.SIGINT, signal_handler)
    
    print("""
╔══════════════════════════════════════════════╗
║   Real-Time Trade Monitor (WebSocket)      ║
║   Fresh instance - auto restarts on change  ║
╚══════════════════════════════════════════════╝
    """)
    
    print("📡 Loading positions...")
    added, removed, current = load_positions()
    
    if removed:
        print(f"❌ Closed: {', '.join(removed)}")
    if added:
        print(f"🆕 New: {', '.join(added)}")
    
    if not POSITIONS:
        print("❌ No open positions found")
        sys.exit(1)
    
    print(f"\n📊 Monitoring {len(POSITIONS)} positions:")
    for sym, p in POSITIONS.items():
        print(f"   {sym}: {p['side']} | Entry ${p['entry']:.6f} | TP ${p['tp']:.6f}")
    print()
    
    streams = [f"{s.lower()}@ticker" for s in POSITIONS.keys()]
    ws_url = f"{WS_URL}/{'/'.join(streams)}"
    
    print(f"🔗 Connecting WebSocket...")
    print(f"   Streams: {', '.join(POSITIONS.keys())}\n")
    
    try:
        ws = create_connection(ws_url, timeout=30)
        print("✅ Connected! Monitoring real-time...\n")
        
        last_check = time.time()
        
        while running:
            try:
                data = json.loads(ws.recv())
                
                if 'e' in data:
                    symbol = data['s']
                    price = float(data['c'])
                    PRICES[symbol] = price
                    check_and_close(symbol, price)
                
                # Check for position changes every 30 seconds
                if time.time() - last_check > 30:
                    last_check = time.time()
                    added, removed, current = load_positions()
                    
                    if added or removed:
                        print(f"\n🔄 Position change detected!")
                        if removed:
                            print(f"   ❌ Closed: {', '.join(removed)}")
                        if added:
                            print(f"   🆕 New: {', '.join(added)}")
                        restart_fresh()
                    
            except WebSocketConnectionClosedException:
                if running:
                    print("⚠️ WebSocket disconnected")
                    time.sleep(1)
                    ws = create_connection(ws_url, timeout=30)
            except Exception as e:
                if running:
                    pass
                    
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if ws:
            ws.close()

if __name__ == "__main__":
    main()
