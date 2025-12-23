#!/usr/bin/env python3

import time
import signal
import sys
import RPi.GPIO as GPIO

# --------------------------------------------------
# GPIO CONFIGURATION
# --------------------------------------------------

# Relay mapping (physical pins 29,31,33,35)
RELAYS = {
    1: 5,    # Pin 29
    2: 6,    # Pin 31
    3: 13,   # Pin 33
    4: 19    # Pin 35
}

RELAY_ON  = GPIO.HIGH   # ACTIVE-HIGH board
RELAY_OFF = GPIO.LOW

# --------------------------------------------------
# SETUP
# --------------------------------------------------

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

def init_relays():
    for gpio in RELAYS.values():
        GPIO.setup(gpio, GPIO.OUT, initial=RELAY_OFF)
    print("Relays initialized OFF")

def cleanup():
    print("Shutting down, turning all relays OFF")
    for gpio in RELAYS.values():
        GPIO.output(gpio, RELAY_OFF)
    GPIO.cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, lambda s, f: cleanup())
signal.signal(signal.SIGTERM, lambda s, f: cleanup())

# --------------------------------------------------
# MAIN LOOP
# --------------------------------------------------

def main():
    init_relays()
    print("RV Generator controller running")

    while True:
        # Placeholder loop
        # Generator logic (temp/voltage/start/stop) will live here
        time.sleep(1)

if __name__ == "__main__":
    main()
