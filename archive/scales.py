from flask import Flask, jsonify
import serial

app = Flask(__name__)

try:
    ser = serial.Serial('/dev/ttyUSB0', 9600, serial.SEVENBITS, serial.PARITY_EVEN,
                        serial.STOPBITS_ONE, timeout=1)
    print ("Serial port opened ok.")
except serial.SerialException:
    ser = None
    print ("Serial port not available. Please check the connection.")

@app.route('/status')
def status():
    print ("connection.")
    if ser is None:
        return jsonify({'error': 'Serial port not available'}), 500
        print ("Serial port not available. Please check the connection.")
    try:
        #ser.write(b'Q\r\n')
        line = ser.readline().decode().strip()
        parts = line.split(',')
        if len(parts) == 2 and '_' in parts[1]:
            weight_str, unit = parts[1].split('_')
            return jsonify({
                'status': parts[0],
                'weight': float(weight_str),
                'unit': unit
            })
        print ("connection.")
        return jsonify({'error': 'Invalid data'}), 500
        
    except Exception as e:
        print ("Serial")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8765)
