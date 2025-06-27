import asyncio
import websockets
import serial
import datetime
import random
import re
import argparse
import json
import threading
import queue

# --- Args ---
parser = argparse.ArgumentParser()
parser.add_argument('--demo', action='store_true', help='Run in demo mode (no serial required)')
args = parser.parse_args()
demo_mode = args.demo
#demo_mode = True

# --- Serial Setup ---
ser = None
serial_queue = queue.Queue()
serial_thread = None
serial_running = False

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

def serial_reader_thread():
    """Background thread to read serial data without blocking the event loop"""
    global serial_running
    while serial_running and ser:
        try:
            line = ser.readline().decode('ascii', errors='ignore')
            if line.strip():
                serial_queue.put(line.strip())
        except serial.SerialException as e:
            serial_queue.put(('ERROR', str(e)))
            break
        except Exception as e:
            serial_queue.put(('ERROR', str(e)))
            break

def start_serial_reader():
    """Start the serial reader thread"""
    global serial_thread, serial_running
    if ser and not serial_running:
        serial_running = True
        serial_thread = threading.Thread(target=serial_reader_thread, daemon=True)
        serial_thread.start()
        print("Serial reader thread started")

def stop_serial_reader():
    """Stop the serial reader thread"""
    global serial_running
    serial_running = False
    if serial_thread:
        serial_thread.join(timeout=2)
        print("Serial reader thread stopped")

# --- Parser ---
def parse_scale_line(line):
    timestamp = datetime.datetime.now().isoformat()
    raw_line = line.strip()  # Store the original raw line
    
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
            "timestamp": timestamp,
            "raw": raw_line
        }
    elif line == 'OL':
        return {
            "status": "OL",  # Overload
            "weight": None,
            "unit": None,
            "timestamp": timestamp,
            "raw": raw_line
        }
    elif line == '?':
        return {
            "status": "ERROR",
            "weight": None,
            "unit": None,
            "timestamp": timestamp,
            "raw": raw_line
        }
    
    # Try to match weight patterns
    for pattern in patterns:
        match = re.match(pattern, line)
        if match:
            return {
                "status": match.group(1),
                "weight": float(match.group(2)),
                "unit": match.group(3),
                "timestamp": timestamp,
                "raw": raw_line
            }
    
    # If no pattern matches
    print(f"Could not parse line: {repr(line)}")
    return {
        "status": "ERROR",
        "weight": None,
        "unit": None,
        "timestamp": timestamp,
        "raw": raw_line
    }
    
# --- Demo Generator ---
demo_responses = [
    ("ST", 26.456, "kg", "ST,GS,+26.456 kg"),       # Stable weight
    ("ST", 26.461, "kg", "ST,GS,+26.461 kg"),       # Stable weight slight change
    ("US", 26.425, "kg", "US,GS,+26.425 kg"),       # Unstable weight
    ("US", 26.489, "kg", "US,GS,+26.489 kg"),       # Unstable weight
    ("ST", 26.450, "kg", "ST,GS,+26.450 kg"),       # Back to stable
    ("US", None, None, "I"),                        # Scale unstable (I response)
    ("ST", 0.000, "kg", "ST,GS,+0.000 kg"),         # Zero weight
    ("US", 26.447, "kg", "US,GS,+26.447 kg"),       # Unstable near target
    ("ST", 26.465, "kg", "ST,GS,+26.465 kg"),       # Stable again
    ("OL", None, None, "OL"),                        # Overload condition
    ("ST", 26.452, "kg", "ST,GS,+26.452 kg"),       # Back to normal
    ("ERROR", None, None, "?"),                      # Error condition
]

demo_index = 0

def generate_demo_data():
    global demo_index
    status, weight, unit, raw_str = demo_responses[demo_index]
    demo_index = (demo_index + 1) % len(demo_responses)
    
    # Add small fluctuation to weight readings and update raw string
    if weight is not None:
        fluctuation = random.uniform(-0.02, 0.02)
        weight = round(weight + fluctuation, 3)
        # Update raw string with fluctuated weight
        raw_str = f"{status},GS,{weight:+.3f} {unit}"
    
    return {
        "status": status,
        "weight": weight,
        "unit": unit,
        "timestamp": datetime.datetime.now().isoformat(),
        "raw": raw_str
    }

# --- WebSocket Handler ---
async def handler(websocket):
    client_address = websocket.remote_address
    print(f"Client connected: {client_address}")
    
    # Start serial reader if we have serial connection
    if ser and not demo_mode:
        start_serial_reader()
    
    try:
        while True:
            data = None
            
            if demo_mode:
                data = generate_demo_data()
                # Add delay in demo mode to simulate real timing
                await asyncio.sleep(1.0)
                
            elif ser:
                try:
                    # Check for data from serial thread (non-blocking)
                    try:
                        line = serial_queue.get_nowait()
                        if isinstance(line, tuple) and line[0] == 'ERROR':
                            # Handle error from serial thread
                            data = {
                                "status": "ERROR",
                                "weight": None,
                                "unit": None,
                                "timestamp": datetime.datetime.now().isoformat(),
                                "error": line[1],
                                "raw": ""
                            }
                        else:
                            # Parse the line from serial
                            data = parse_scale_line(line)
                            print(f"Received: {line} -> Status: {data['status']}, Weight: {data.get('weight')}, Raw: {data['raw']}")
                            
                    except queue.Empty:
                        # No data available, wait a bit and continue
                        await asyncio.sleep(0.1)
                        continue
                        
                except Exception as e:
                    print(f"Unexpected error processing serial data: {e}")
                    data = {
                        "status": "ERROR",
                        "weight": None,
                        "unit": None,
                        "timestamp": datetime.datetime.now().isoformat(),
                        "error": str(e),
                        "raw": ""
                    }
            else:
                data = {
                    "status": "ERROR",
                    "weight": None,
                    "unit": None,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "error": "No serial connection available",
                    "raw": ""
                }
                await asyncio.sleep(1.0)  # Prevent busy loop when no serial

            # Send data to client (only when we have actual data)
            if data:
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
        stop_serial_reader()
        if ser:
            ser.close()
            print("Serial port closed")

if __name__ == "__main__":
    asyncio.run(main())
