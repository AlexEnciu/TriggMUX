import RPi.GPIO as GPIO
import time

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
pwm_12.start(1/100)
pwm_13.start(50)

# Functions
counter = 0
manual_mode = False  # Initial mode is automatic
last_pulse_time = time.time()


def update_gpio_states(mux_channel):
    # Calculate the binary representation of the MUX channel
    mux_binary = bin(mux_channel)[2:].zfill(4)
    # Set GPIO states based on the MUX channel
    GPIO.output(s_pins[0], int(mux_binary[3]))  # S0
    GPIO.output(s_pins[1], int(mux_binary[2]))  # S1
    GPIO.output(s_pins[2], int(mux_binary[1]))  # S2
    GPIO.output(s_pins[3], int(mux_binary[0]))  # S3

def laser_trigg(channel):
    # switch to laser
    update_gpio_states(0)
    print("Beam Off, LASER ON")
    time.sleep(0.5)

def pw_trigg(channel):
    # switch to PlasticWall
    update_gpio_states(1)
    print("Beam On, Plastic Wall ON")
    time.sleep(0.5)

def pulse_counter(channel):
    global counter, last_pulse_time
    counter += 1
    current_time = time.time()
    time_difference = current_time - last_pulse_time
    last_pulse_time = current_time
    rate = 1 / time_difference if time_difference > 0 else 0
    print(f"\rRate: {rate:.2f} Hz ",end='', flush=True)


def setup_event_detection():
    # Set up event detection with GPIO.RISING
    GPIO.add_event_detect(beam_detect_on, GPIO.RISING, callback=laser_trigg)
    GPIO.add_event_detect(beam_detect_off, GPIO.RISING, callback=pw_trigg)

def switch_to_manual_mode():
    global manual_mode
    manual_mode = True
    # Clean up existing event detections
    GPIO.remove_event_detect(beam_detect_on)
    GPIO.remove_event_detect(beam_detect_off)

def switch_to_automatic_mode():
    global manual_mode
    manual_mode = False
    # Clean up any previous manual mode settings
    GPIO.remove_event_detect(beam_detect_on)
    GPIO.remove_event_detect(beam_detect_off)
    # Set up event detection for automatic mode
    setup_event_detection()

def help():
    print("-----------------------------------------------------------------------")
    print("-----------------------------------------------------------------------")
    print("This is a short help for the TPC trigger control unit")
    print("-----------------------------------------------------------------------")
    print("laser_trigg() -> set the trigger for the LASER")
    print("pw_trigg() -> set the trigger for the Plastic Wall")
    print("switch_to_automatic_mode() -> set the automatic detection mode for the Beam window")
    print("switch_to_manual_mode() -> set the manual mode in order to control manualy the LASER and the Plastic Wall")
    print("-----------------------------------------------------------------------")
    print("-----------------------------------------------------------------------")

def close_app():
    GPIO.cleanup()
    exit()

GPIO.add_event_detect(counter_pulses, GPIO.RISING, callback=pulse_counter)
# Initial setup for automatic mode
#setup_event_detection()
"""
try:
    while True:
        if manual_mode:
            # Manual mode logic here
            # For example, use input() to get user commands for manual control
            pass
        else:
            # Automatic mode logic here
            pass
        time.sleep(0.001)

except KeyboardInterrupt:
    GPIO.cleanup()
"""