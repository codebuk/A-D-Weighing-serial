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
#demo_mode = True

# --- Serial Setup ---
ser = None
if not demo_mode:
    try:
        ser = serial.Serial(
            port='/dev/ttyUSB0',  # Adjust as needed
            baudrate=9600,
            bytesize=serial.SEVENBITS,
            parity=serial.PARITY_EVEN,
            stopbits=serial.STOPBITS_ONE,
            timeout=1
        )
        print(f"Serial port connected: {ser.port}")
    except Exception as e:
        print("Serial port unavailable:", e)

# --- Parser ---
def parse_scale_line(line):
    timestamp = datetime.datetime.now().isoformat()
    
    # Handle multiple possible formats
    patterns = [
        r'^([A-Z]{2}),GS,([+-]?\d+\.\d+)\s+([a-zA-Z]+)$',  # ST,GS,+150.25 kg
        r'^([A-Z]{2}),([+-]?\d+\.\d+)_([a-zA-Z]+)$',       # ST,+150.25_kg
        r'^([A-Z]{2}),([+-]?\d+\.\d+)\s+([a-zA-Z]+)$',     # ST,+150.25 kg
    ]
    
    line = line.strip()
    
    # Handle special responses
    if line == 'I':
        return {
            "status": "US",  # Unstable
            "weight": None,
            "unit": None,
            "timestamp": timestamp
        }
    elif line == 'OL':
        return {
            "status": "OL",  # Overload
            "weight": None,
            "unit": None,
            "timestamp": timestamp
        }
    elif line == '?':
        return {
            "status": "ERROR",
            "weight": None,
            "unit": None,
            "timestamp": timestamp
        }
    
    # Try to match weight patterns
    for pattern in patterns:
        match = re.match(pattern, line)
        if match:
            return {
                "status": match.group(1),
                "weight": float(match.group(2)),
                "unit": match.group(3),
                "timestamp": timestamp
            }
    
    # If no pattern matches
    print(f"Could not parse line: {repr(line)}")
    return {
        "status": "ERROR",
        "weight": None,
        "unit": None,
        "timestamp": timestamp,
        "raw": line
    }

# --- Demo Generator ---
demo_responses = [
    ("ST", 26.456, "kg"),      # Stable weight
    ("ST", 26.461, "kg"),      # Stable weight slight change
    ("US", 26.425, "kg"),      # Unstable weight
    ("US", 26.489, "kg"),      # Unstable weight
    ("ST", 26.450, "kg"),      # Back to stable
    ("US", None, None),        # Scale unstable (I response)
    ("ST", 0.000, "kg"),       # Zero weight
    ("US", 26.447, "kg"),      # Unstable near target
    ("ST", 26.465, "kg"),      # Stable again
    ("OL", None, None),        # Overload condition
    ("ST", 26.452, "kg"),      # Back to normal
    ("ERROR", None, None),     # Error condition
]

demo_index = 0

def generate_demo_data():
    global demo_index
    status, weight, unit = demo_responses[demo_index]
    demo_index = (demo_index + 1) % len(demo_responses)
    
    # Add small fluctuation to weight readings
    if weight is not None:
        fluctuation = random.uniform(-0.02, 0.02)
        weight = round(weight + fluctuation, 3)
    
    return {
        "status": status,
        "weight": weight,
        "unit": unit,
        "timestamp": datetime.datetime.now().isoformat()
    }

# --- WebSocket Handler ---
async def handler(websocket):
    client_address = websocket.remote_address
    print(f"Client connected: {client_address}")
    
    try:
        while True:
            if demo_mode:
                data = generate_demo_data()
                # Add delay in demo mode to simulate real timing
                await asyncio.sleep(1.0)
            elif ser:
                try:
                    # Just read the continuous data stream - no query needed
                    line = ser.readline().decode('ascii', errors='ignore')
                    
                    if line.strip():
                        data = parse_scale_line(line)
                        print(f"Received: {line.strip()} -> {data}")
                    else:
                        # Timeout occurred, but this is normal - just continue
                        continue
                        
                except serial.SerialException as e:
                    print(f"Serial error: {e}")
                    data = {
                        "status": "ERROR",
                        "weight": None,
                        "unit": None,
                        "timestamp": datetime.datetime.now().isoformat(),
                        "error": str(e)
                    }
                except Exception as e:
                    print(f"Unexpected error reading serial: {e}")
                    data = {
                        "status": "ERROR",
                        "weight": None,
                        "unit": None,
                        "timestamp": datetime.datetime.now().isoformat(),
                        "error": str(e)
                    }
            else:
                data = {
                    "status": "ERROR",
                    "weight": None,
                    "unit": None,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "error": "No serial connection available"
                }
                await asyncio.sleep(1.0)  # Prevent busy loop when no serial

            # Send data to client (only when we have actual data)
            if 'data' in locals():
                try:
                    await websocket.send(json.dumps(data))
                except websockets.exceptions.ConnectionClosed:
                    print(f"Client disconnected: {client_address}")
                    break
                except Exception as e:
                    print(f"Error sending data: {e}")
                    break
                
    except websockets.exceptions.ConnectionClosed:
        print(f"Client connection closed: {client_address}")
    except Exception as e:
        print(f"Handler error for {client_address}: {e}")
    finally:
        print(f"Cleaning up connection for {client_address}")

# --- Main ---
async def main():
    try:
        async with websockets.serve(handler, "0.0.0.0", 8765):
            print(f"WebSocket server running at ws://localhost:8765 (demo mode: {demo_mode})")
            await asyncio.Future()  # run forever
    except KeyboardInterrupt:
        print("Server stopped by user")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        if ser:
            ser.close()
            print("Serial port closed")

if __name__ == "__main__":
    asyncio.run(main())
