#!/bin/bash
cd /root/.openclaw/workspace/psyduck-trading-bot
source venv/bin/activate
python3 autopilot.py --iterations 100000 --interval 60 --no-confirm
