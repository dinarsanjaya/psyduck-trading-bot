#!/usr/bin/env python3
"""
Binance Futures Trading Bot - Quick Start
"""

import os
import sys

def print_banner():
    print("""
╔══════════════════════════════════════════════╗
║   Binance Futures Trading Bot                ║
║   Auto-scan + Auto-trade (Demo)             ║
╚══════════════════════════════════════════════╝
    """)

def check_setup():
    """Check if environment is properly configured"""
    errors = []
    
    # Check Python version
    if sys.version_info < (3, 8):
        errors.append("Python 3.8+ required")
    
    # Check dependencies
    try:
        import pandas
        import pandas_ta
        import requests
    except ImportError as e:
        errors.append(f"Missing dependency: {e}")
    
    # Check config
    if not os.path.exists("config.py"):
        errors.append("config.py not found. Copy config.py.example to config.py")
    
    return errors

def main():
    print_banner()
    
    errors = check_setup()
    
    if errors:
        print("❌ Setup issues found:\n")
        for err in errors:
            print(f"  • {err}")
        print("\n📖 See README.md for setup instructions")
        sys.exit(1)
    
    print("✅ All checks passed!")
    print("\n🚀 Bot ready to run!")
    print("\nNext steps:")
    print("  1. Edit config.py with your API keys")
    print("  2. Run: python learn/autopilot.py")
    print("  3. Or import and use the trading functions in your agent")

if __name__ == "__main__":
    main()
