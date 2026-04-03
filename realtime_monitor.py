#!/usr/bin/env python3
"""
Real-Time Trade Monitor - WebSocket Based
Monitors positions with <100ms price updates
"""

import json
import hmac
import hashlib
import time
import threading
import sys
from websocket import create_connection, WebSocketConnectionClosedException

API_KEY = "FSUmnDqHGbQVtVlftKrtxZrfA75BzfZUszltB9WBvxWBNgkrCP4kT19qPBzpbRur"
API_SECRET = "2okFUCG6p8RYljC5YMVC7Y37v198b8K55ctvtk6BMScsaZJFy68CAMuFuyyMnvZO"
FUTURES_URL = "https://demo-fapi.binance.com"
WS_URL = "wss://stream.binance.com:9443/ws"  # Mainnet (demo WS unavailable)

# Positions to monitor (symbol -> {entry, side, amount, sl, tp})
POSITIONS = {}

# Price cache
PRICES = {}

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
        # For SHORT: TP = price lower, SL = price higher
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
    
    for p in pos_data:
        amt = float(p['positionAmt'])
        if amt == 0:
            continue
            
        symbol = p['symbol']
        entry = float(p['entryPrice'])
        side = "SHORT" if amt < 0 else "LONG"
        qty = abs(amt)
        
        if side == "SHORT":
            sl = entry * 1.025  # +2.5%
            tp = entry * 0.95   # -5%
        else:
            sl = entry * 0.975  # -2.5%
            tp = entry * 1.05   # +5%
        
        POSITIONS[symbol] = {
            'entry': entry,
            'side': side,
            'amount': qty,
            'sl': sl,
            'tp': tp
        }
        
        print(f"📊 Monitoring {symbol} ({side}):")
        print(f"   Entry: ${entry:.6f}")
        print(f"   TP: ${tp:.6f}")
        print(f"   SL: ${sl:.6f}")
        print()

def websocket_listener():
    """WebSocket listener for real-time price updates"""
    if not POSITIONS:
        print("No positions to monitor")
        return
    
    # Build stream URL for all positions
    streams = [f"{s.lower()}@ticker" for s in POSITIONS.keys()]
    ws_url = f"{WS_URL}/{'/'.join(streams)}"
    
    print(f"🔗 Connecting to WebSocket...")
    print(f"   Streams: {', '.join(POSITIONS.keys())}")
    print()
    
    try:
        ws = create_connection(ws_url, timeout=30)
        print("✅ WebSocket connected! Monitoring in real-time...\n")
        
        while True:
            try:
                data = json.loads(ws.recv())
                
                if 'e' in data:  # Ticker event
                    symbol = data['s']
                    price = float(data['c'])  # Close price (current)
                    PRICES[symbol] = price
                    
                    # Check TP/SL
                    check_and_close(symbol, price)
                    
            except WebSocketConnectionClosedException:
                print("⚠️ WebSocket disconnected, reconnecting...")
                time.sleep(1)
                ws = create_connection(ws_url, timeout=30)
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(1)
                
    except Exception as e:
        print(f"❌ WebSocket error: {e}")

def main():
    print("""
╔══════════════════════════════════════════════╗
║   Real-Time Trade Monitor (WebSocket)      ║
║   <100ms price updates, auto TP/SL         ║
╚══════════════════════════════════════════════╝
    """)
    
    print("📡 Loading positions...")
    load_positions()
    
    if not POSITIONS:
        print("❌ No open positions found")
        sys.exit(1)
    
    print(f"📊 Monitoring {len(POSITIONS)} positions in real-time...")
    print("Press Ctrl+C to stop\n")
    
    websocket_listener()

if __name__ == "__main__":
    main()
