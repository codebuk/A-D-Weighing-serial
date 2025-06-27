import serial
import time

def open_serial(port="/dev/ttyUSB0", baudrate=9600):
    """Open and return the serial port."""
    return serial.Serial(
        port=port,
        baudrate=baudrate,
        bytesize=serial.SEVENBITS,
        parity=serial.PARITY_EVEN,
        stopbits=serial.STOPBITS_ONE,
        timeout=1
    )

def send_command(ser, cmd):
    """Send a command followed by CR LF."""
    ser.write((cmd + '\r\n').encode('ascii'))

def read_response(ser):
    """Read and decode the response from the scale."""
    line = ser.readline().decode('ascii').strip()
    return line

def parse_weight_response(response):
    """Extract and return the weight, unit, and status from a valid response."""
    if not response:  # Handle empty responses from timeout
        return None, None, "Error"
        
    if response.startswith("ST"):
        try:
            parts = response.split(",")
            weight = parts[1].split(" ")[0]  # "+00123.45"
            unit = parts[1].split(" ")[1]    # "kg"
            return float(weight), unit, "stable"
        except (IndexError, ValueError):
            print("Parse error")
            return None, None, "Error"
    elif response.startswith("US"):
        try:
            parts = response.split(",")
            weight = parts[1].split(" ")[0]  # "+00123.45"
            unit = parts[1].split(" ")[1]    # "kg"
            return float(weight), unit, "unstable"
        except (IndexError, ValueError):
            print("Parse error")
            return None, None, "Error"
    elif response.startswith("I"):
        print("Scale returns I.")
        return None, None, "unstable"
    elif response.startswith("?"):
        print("Invalid command.")
        return None, None, "Error"
    elif response.startswith("OL"):
        print("Overload condition.")
        return None, None, "overload"
    else:
        print("Unknown response:", response)
        return None, None, "Error"

def main():
    try:
        ser = open_serial("/dev/ttyUSB0", 9600)
        print("Serial port opened.")

        while True:
            send_command(ser, "Q")  # Request weight - uncommented
            response = read_response(ser)
            print("Raw response:", repr(response))

            weight, unit, status = parse_weight_response(response)
            if weight is not None:
                print(f"Weight: {weight} {unit} - Status: {status}")
            else:
                print(f"Status: {status}")

    except serial.SerialException as e:
        print("Serial error:", e)
    except KeyboardInterrupt:
        print("Exiting.")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("Serial port closed.")

if __name__ == "__main__":
    main()
