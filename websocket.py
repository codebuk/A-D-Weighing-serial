import asyncio
import websockets
import serial
import datetime
import random
import re
import argparse
import json

# --- Args ---
parser = argparse.ArgumentParser()
parser.add_argument('--demo', action='store_true', help='Run in demo mode (no serial required)')
args = parser.parse_args()
demo_mode = args.demo
demo_mode = True

# --- Serial Setup ---
ser = None
if not demo_mode:
    try:
        ser = serial.Serial(
            port='COM3',  # Adjust as needed
            baudrate=9600,
            bytesize=serial.SEVENBITS,
            parity=serial.PARITY_EVEN,
            stopbits=serial.STOPBITS_ONE,
            timeout=1
        )
    except Exception as e:
        print("Serial port unavailable:", e)

# --- Parser ---
def parse_scale_line(line):
    timestamp = datetime.datetime.now().isoformat()
    pattern = r'^([A-Z]{2}),([+-]?\d+\.\d+)_([a-zA-Z]+)$'
    match = re.match(pattern, line.strip())
    if match:
        return {
            "status": match.group(1),
            "weight": float(match.group(2)),
            "unit": match.group(3),
            "timestamp": timestamp
        }
    else:
        return {
            "status": "ERROR",
            "weight": None,
            "unit": None,
            "timestamp": timestamp
        }

# --- Demo Generator ---
def generate_demo_data():
    fluctuation = random.uniform(-0.05, 0.05)
    fake_weight = 26.456 + fluctuation
    return {
        "status": "ST",
        "weight": round(fake_weight, 3),
        "unit": "kg",
        "timestamp": datetime.datetime.now().isoformat()
    }

# --- WebSocket Handler ---
async def handler(websocket):
    while True:
        if demo_mode:
            data = generate_demo_data()
        elif ser:
            try:
                ser.write(b'Q\r\n')
                line = ser.readline().decode().strip()
                data = parse_scale_line(line)
            except Exception:
                data = {
                    "status": "ERROR",
                    "weight": None,
                    "unit": None,
                    "timestamp": datetime.datetime.now().isoformat()
                }
        else:
            data = {
                "status": "ERROR",
                "weight": None,
                "unit": None,
                "timestamp": datetime.datetime.now().isoformat()
            }

        await websocket.send(json.dumps(data))
        await asyncio.sleep(.01)

# --- Main ---
async def main():
    async with websockets.serve(handler, "0.0.0.0", 8765):
        print("WebSocket server running at ws://localhost:8765 (demo mode: {})".format(demo_mode))
        await asyncio.Future()  # run forever

asyncio.run(main())
