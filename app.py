from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import RPi.GPIO as GPIO
import time
import timeit

app = Flask(__name__)
socketio = SocketIO(app)

# Set up GPIO
GPIO.setmode(GPIO.BCM)
counter_pulses = 21
beam_detect_on = 26
beam_detect_off = 20
enable_pin = 14
s_pins = [15, 18, 23, 24]
pwm_pins = [12, 13]
GPIO.setup(beam_detect_off, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(beam_detect_on, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(counter_pulses, GPIO.IN, pull_up_down=GPIO.PUD_UP)

for pin in [enable_pin] + s_pins + pwm_pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

# Set up PWM
pwm_12 = GPIO.PWM(12, 20)  # PWM frequency of 1 kHz on GPIO 12
pwm_13 = GPIO.PWM(13, 3000)  # PWM frequency of 2 kHz on GPIO 13

# Start PWM with 0% duty cycle initially
pwm_12.start(1/10)
pwm_13.start(1/10)

# Functions
manual_mode = False  # Initial mode is automatic
last_pulse_time = time.time()
last_emit_time=0
rate=0


def update_gpio_states(mux_channel):
    mux_binary = bin(mux_channel)[2:].zfill(4)
    GPIO.output(s_pins[0], int(mux_binary[3]))  # S0
    GPIO.output(s_pins[1], int(mux_binary[2]))  # S1
    GPIO.output(s_pins[2], int(mux_binary[1]))  # S2
    GPIO.output(s_pins[3], int(mux_binary[0]))  # S3

def enable_mux():
    GPIO.output(enable_pin, GPIO.LOW)
    socketio.emit('message', {'data': 'MUX Enabled'})

def disable_mux():
    GPIO.output(enable_pin, GPIO.HIGH)
    socketio.emit('message', {'data': 'MUX Disabled'})

def laser_trigg(channel):
    update_gpio_states(0)
    socketio.emit('message', {'data': 'Beam Off, LASER ON'})


def pw_trigg(channel):
    update_gpio_states(1)
    socketio.emit('message', {'data': 'Beam On, Plastic Wall ON'})


def pulse_counter(channel):
    global last_pulse_time, rate,last_emit_time
    current_time = time.time()
    time_difference = current_time - last_pulse_time
    last_pulse_time = current_time
    rate = 1 / time_difference if time_difference > 0 else 0
    # Emit accumulated count every second
    if current_time - last_emit_time > 2:
        socketio.emit('rate', {'data': rate})
        last_emit_time = current_time


def switch_to_manual_mode():
    global manual_mode
    manual_mode = True
    GPIO.remove_event_detect(beam_detect_on)
    GPIO.remove_event_detect(beam_detect_off)
    socketio.emit('message', {'data': 'Switched to manual mode'})


def switch_to_automatic_mode():
    global manual_mode
    manual_mode = False
    GPIO.remove_event_detect(beam_detect_on)
    GPIO.remove_event_detect(beam_detect_off)
    setup_event_detection()
    socketio.emit('message', {'data': 'Switched to automatic mode'})


def setup_event_detection():
    GPIO.add_event_detect(beam_detect_on, GPIO.RISING, callback=laser_trigg)
    GPIO.add_event_detect(beam_detect_off, GPIO.RISING, callback=pw_trigg)

GPIO.add_event_detect(counter_pulses, GPIO.RISING, callback=pulse_counter)

@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('laser_trigg_route')
def laser_trigg_route():
    laser_trigg(None)
    return jsonify(result='success', message='Laser Trigg executed')


@socketio.on('pw_trigg_route')
def pw_trigg_route():
    pw_trigg(None)
    return jsonify(result='success', message='PW Trigg executed')


@socketio.on('switch_to_manual_mode_route')
def switch_to_manual_mode_route():
    switch_to_manual_mode()
    return jsonify(result='success', message='Switched to Manual Mode')


@socketio.on('switch_to_automatic_mode_route')
def switch_to_automatic_mode_route():
    switch_to_automatic_mode()
    return jsonify(result='success', message='Switched to Automatic Mode')


@socketio.on('get_rate')
def get_rate():
    #rate = 0  # Replace with the actual rate value
    return jsonify(rate=rate)


@socketio.on('get_messages')
def get_messages():
    messages = ['Message 1', 'Message 2']  # Replace with the actual messages
    return jsonify(messages=messages)


@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('message', {'data': 'Connected to server'})


@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('enable_mux_route')
def handle_MuxEnable():
    enable_mux()
    return jsonify(result='success', message='Mux Enabled')

@socketio.on('disable_mux_route')
def handle_MuxDisable():
    disable_mux()
    return jsonify(result='success', message='Mux Disabled')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    
