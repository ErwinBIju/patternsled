from signal import signal, SIGTERM, SIGHUP, pause
from gpiozero import PWMLED, Button
from threading import Thread
from time import sleep
from random import randrange
from rpi_lcd import LCD
from Adafruit_ADS1x15 import ADS1115

# Initialize components
adc = ADS1115()
adc.start_adc(0, gain=1)
lcd = LCD()
leds = (PWMLED(20), PWMLED(21), PWMLED(16), PWMLED(26), PWMLED(6), PWMLED(5), PWMLED(19))
button = Button(12)
is_running = True
delay = 0.1
brightness = 1.0
index = 0
direction = ">>"

patterns = (
    [1, 0, 0, 0, 0, 0, 0],
    [1, 1, 0, 0, 0, 0, 0],
    [1, 1, 1, 0, 0, 0, 0],
    [1, 1, 1, 1, 0, 0, 0],
    [1, 1, 1, 1, 1, 0, 0],
    [1, 1, 1, 1, 1, 1, 0],
    [1, 0, 1, 0, 1, 0, 0]
)

# Functions for reading potentiometers
def read_potentiometer(channel):
    return adc.read_adc(channel)

def calculate_brightness(value, exponent=2.0):
    return (value / 255) ** exponent

# Threaded functions
def update_lcd():
    while is_running:
        lcd.text(f"B:{brightness*100:3.0f}% D:{delay:2.2f}s", 2)
        sleep(0.1)

def speed_adjustment():
    global delay
    while is_running:
        pot_value = read_potentiometer(0)  # Potentiometer 1
        delay = 0.02 + 0.4 * pot_value / 255
        sleep(0.01)

def brightness_adjustment():
    global brightness
    while is_running:
        pot_value = read_potentiometer(1)  # Potentiometer 2
        brightness = calculate_brightness(pot_value)
        sleep(0.01)

def show_pattern():
    global direction
    while is_running:
        for id in range(7):
            leds[id].value = patterns[index][id] * brightness  # Adjust LED value
        if direction == ">>":
            token = patterns[index].pop(-1)
            patterns[index].insert(0, token)
            lcd.text(f"Pattern {index}/7 {direction}", 1)
        else:
            token = patterns[index].pop(0)
            patterns[index].append(token)
            lcd.text(f"Pattern {index}/7 {direction}", 1)
        sleep(delay)

# Main program setup
try:
    signal(SIGTERM, safe_exit)
    signal(SIGHUP, safe_exit)
    button.when_pressed = change_direction

    # Start threads
    lcd_thread = Thread(target=update_lcd, daemon=True)
    lcd_thread.start()

    speed_thread = Thread(target=speed_adjustment, daemon=True)
    speed_thread.start()

    brightness_thread = Thread(target=brightness_adjustment, daemon=True)
    brightness_thread.start()

    # Start pattern display
    worker = Thread(target=show_pattern, daemon=True)
    worker.start()

    pause()

except KeyboardInterrupt:
    pass
finally:
    is_running = False
    worker.join()
    for id in range(7):
        leds[id].close()
    lcd.clear()