#!/usr/bin/env python3
"""
Real-Time Trade Monitor - WebSocket Based
Monitors positions with <100ms price updates
Auto-updates watchlist when new positions are opened
"""

import json
import hmac
import hashlib
import time
import threading
import sys
import signal
from websocket import create_connection, WebSocketConnectionClosedException

API_KEY = "FSUmnDqHGbQVtVlftKrtxZrfA75BzfZUszltB9WBvxWBNgkrCP4kT19qPBzpbRur"
API_SECRET = "2okFUCG6p8RYljC5YMVC7Y37v198b8K55ctvtk6BMScsaZJFy68CAMuFuyyMnvZO"
FUTURES_URL = "https://demo-fapi.binance.com"
WS_URL = "wss://stream.binance.com:9443/ws"

# Positions to monitor (symbol -> {entry, side, amount, sl, tp})
POSITIONS = {}
PRICES = {}

# WebSocket state
ws = None
ws_lock = threading.Lock()
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
    """Fetch current positions from API"""
    ts = int(time.time() * 1000)
    q = f"timestamp={ts}"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    import requests
    r = requests.get(f"{FUTURES_URL}/fapi/v2/positionRisk?{q}&signature={sig}",
                    headers={"X-MBX-APIKEY": API_KEY}, timeout=15)
    return r.json()

def close_position(symbol, side, qty):
    """Close position with market order"""
    close_side = "BUY" if side == "SHORT" else "SELL"
    print(f"🔴 CLOSING {symbol} ({close_side}) at market price...")
    
    result = signed_post("/fapi/v1/order", {
        "symbol": symbol,
        "side": close_side,
        "type": "MARKET",
        "quantity": qty
    })
    
    if 'orderId' in result:
        print(f"✅ {symbol} CLOSED! Order ID: {result['orderId']}")
        if symbol in POSITIONS:
            del POSITIONS[symbol]
        reconnect_websocket()  # Update stream after closing
        return True
    else:
        print(f"❌ Close failed: {result}")
        return False

def check_and_close(symbol, current_price):
    """Check if TP or SL hit, close if needed"""
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
            print(f"🎯 {symbol} TP HIT! Price ${current_price} <= TP ${tp}")
            close_position(symbol, side, qty)
        elif current_price >= sl:
            print(f"🛑 {symbol} SL HIT! Price ${current_price} >= SL ${sl}")
            close_position(symbol, side, qty)
    else:  # LONG
        if current_price >= tp:
            print(f"🎯 {symbol} TP HIT! Price ${current_price} >= TP ${tp}")
            close_position(symbol, side, qty)
        elif current_price <= sl:
            print(f"🛑 {symbol} SL HIT! Price ${current_price} <= SL ${sl}")
            close_position(symbol, side, qty)

def load_positions():
    """Load positions from API and setup TP/SL levels"""
    global POSITIONS
    pos_data = get_positions()
    
    old_positions = set(POSITIONS.keys())
    new_positions = set()
    
    for p in pos_data:
        amt = float(p['positionAmt'])
        if amt == 0:
            continue
            
        symbol = p['symbol']
        new_positions.add(symbol)
        entry = float(p['entryPrice'])
        side = "SHORT" if amt < 0 else "LONG"
        qty = abs(amt)
        
        if side == "SHORT":
            sl = entry * 1.025
            tp = entry * 0.95
        else:
            sl = entry * 0.975
            tp = entry * 1.05
        
        POSITIONS[symbol] = {
            'entry': entry,
            'side': side,
            'amount': qty,
            'sl': sl,
            'tp': tp
        }
    
    # Show new positions
    added = new_positions - old_positions
    removed = old_positions - new_positions
    
    if added:
        print(f"🆕 New positions detected: {', '.join(added)}")
    if removed:
        print(f"❌ Positions closed: {', '.join(removed)}")
    
    return added, removed

def reconnect_websocket():
    """Reconnect WebSocket with updated stream list"""
    global ws
    
    if not POSITIONS:
        print("No positions to monitor")
        return
    
    with ws_lock:
        try:
            if ws:
                ws.close()
        except:
            pass
        
        streams = [f"{s.lower()}@ticker" for s in POSITIONS.keys()]
        ws_url = f"{WS_URL}/{'/'.join(streams)}"
        
        print(f"\n🔗 Reconnecting WebSocket with {len(streams)} streams...")
        print(f"   Watching: {', '.join(POSITIONS.keys())}")
        
        try:
            ws = create_connection(ws_url, timeout=30)
            print("✅ WebSocket reconnected!\n")
        except Exception as e:
            print(f"❌ Reconnect failed: {e}")

def position_checker():
    """Background thread to check for new positions every 30 seconds"""
    global running
    
    while running:
        time.sleep(30)
        if not running:
            break
        
        old_keys = set(POSITIONS.keys())
        load_positions()
        new_keys = set(POSITIONS.keys())
        
        if old_keys != new_keys:
            print(f"📊 Position change detected, updating WebSocket...")
            reconnect_websocket()

def websocket_listener():
    """WebSocket listener for real-time price updates"""
    global ws, running
    
    if not POSITIONS:
        print("No positions to monitor")
        return
    
    streams = [f"{s.lower()}@ticker" for s in POSITIONS.keys()]
    ws_url = f"{WS_URL}/{'/'.join(streams)}"
    
    print(f"🔗 Connecting to WebSocket...")
    print(f"   Streams: {', '.join(POSITIONS.keys())}")
    print()
    
    try:
        ws = create_connection(ws_url, timeout=30)
        print("✅ WebSocket connected! Monitoring in real-time...\n")
        
        while running:
            try:
                data = json.loads(ws.recv())
                
                if 'e' in data:
                    symbol = data['s']
                    price = float(data['c'])
                    PRICES[symbol] = price
                    check_and_close(symbol, price)
                    
            except WebSocketConnectionClosedException:
                if running:
                    print("⚠️ WebSocket disconnected, reconnecting...")
                    time.sleep(1)
                    reconnect_websocket()
            except Exception as e:
                if running:
                    print(f"Error: {e}")
                    time.sleep(1)
                    
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
    finally:
        if ws:
            try:
                ws.close()
            except:
                pass

def signal_handler(sig, frame):
    global running
    print("\n🛑 Shutting down...")
    running = False
    sys.exit(0)

def main():
    global running
    
    signal.signal(signal.SIGINT, signal_handler)
    
    print("""
╔══════════════════════════════════════════════╗
║   Real-Time Trade Monitor (WebSocket)      ║
║   <100ms updates + auto position detection ║
╚══════════════════════════════════════════════╝
    """)
    
    print("📡 Loading positions...")
    load_positions()
    
    if not POSITIONS:
        print("❌ No open positions found")
        sys.exit(1)
    
    print(f"\n📊 Monitoring {len(POSITIONS)} positions in real-time...")
    print("   Auto-updates when new positions are opened")
    print("   Press Ctrl+C to stop\n")
    
    # Start position checker thread
    checker = threading.Thread(target=position_checker, daemon=True)
    checker.start()
    
    websocket_listener()

if __name__ == "__main__":
    main()
