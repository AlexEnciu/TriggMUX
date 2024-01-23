# app.py
from flask import Flask, render_template
from flask_socketio import SocketIO
import RPi.GPIO as GPIO
import time

app = Flask(__name__)
socketio = SocketIO(app)

# Set up GPIO
GPIO.setmode(GPIO.BCM)
enable_pin = 14
s_pins = [15, 18, 23, 24]
pwm_pins = [12, 13]

for pin in [enable_pin] + s_pins+pwm_pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

# Set up PWM
pwm_12 = GPIO.PWM(12, 1000)  # PWM frequency of 1 kHz on GPIO 12
pwm_13 = GPIO.PWM(13, 3000)  # PWM frequency of 2 kHz on GPIO 13

# Start PWM with 0% duty cycle initially
pwm_12.start(50)
pwm_13.start(50)

mux_channel = 0  # Default MUX channel

# Index route
@app.route('/')
def index():
    return render_template('index.html')

# WebSocket event handler for applying the selected MUX channel
@socketio.on('apply_mux_channel')
def handle_mux_channel(data):
    global mux_channel
    mux_channel = int(data['channel'])
    send_led_status()

# WebSocket event handler for button clicks
@socketio.on('button_click')
def handle_button_click(data):
    pin = int(data['pin'])
    action = data['action']

    if action == 'on':
        GPIO.output(pin, GPIO.HIGH)
    elif action == 'off':
        GPIO.output(pin, GPIO.LOW)

    # Send status update to the client
    socketio.emit('update_status', {'pin': pin, 'status': action})

    # Send LED status update to the client
    send_led_status()

# WebSocket event handler for applying the selected MUX channel
@socketio.on('apply_mux_channel')
def handle_mux_channel(data):
    global mux_channel
    mux_channel = int(data['channel'])
    # Update the GPIO states based on the MUX channel
    update_gpio_states()
    # Send LED status update to the client
    send_led_status()

def update_gpio_states():
    # Calculate the binary representation of the MUX channel
    mux_binary = bin(mux_channel)[2:].zfill(4)

    # Set GPIO states based on the MUX channel
    GPIO.output(s_pins[0], int(mux_binary[3]))  # S0
    GPIO.output(s_pins[1], int(mux_binary[2]))  # S1
    GPIO.output(s_pins[2], int(mux_binary[1]))  # S2
    GPIO.output(s_pins[3], int(mux_binary[0]))  # S3

def send_led_status():
    # Send LED status to the client
    led_statuses = {
        'led-enable': GPIO.input(enable_pin),
        'led-s0': GPIO.input(s_pins[0]),
        'led-s1': GPIO.input(s_pins[1]),
        'led-s2': GPIO.input(s_pins[2]),
        'led-s3': GPIO.input(s_pins[3]),
        'mux-channel': mux_channel,
    }
    socketio.emit('update_led_status', led_statuses)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
