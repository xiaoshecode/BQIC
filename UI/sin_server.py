from flask import Flask, jsonify, request
import time
import math
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

frequency = 1.0
amplitude = 1.0
phase = 0.0
start_time = time.time()

def get_sin_value():
    current_time = time.time() - start_time
    value = amplitude * math.sin(2 * math.pi * frequency * current_time + phase)
    return value, current_time

@app.route('/api/sin', methods=['GET'])
def api_sin():
    value, current_time = get_sin_value()
    return jsonify({
        'timestamp': time.time(),
        'current_time': current_time,
        'value': value,
        'frequency': frequency,
        'amplitude': amplitude,
        'phase': phase
    })

@app.route('/api/sin/params', methods=['POST'])
def update_params():
    global frequency, amplitude, phase, start_time
    data = request.json or {}
    frequency = float(data.get('frequency', frequency))
    amplitude = float(data.get('amplitude', amplitude))
    phase = float(data.get('phase', phase))
    start_time = time.time()  # reset time
    return jsonify({'status': 'ok', 'frequency': frequency, 'amplitude': amplitude, 'phase': phase})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
