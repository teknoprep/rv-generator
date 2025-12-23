#!/usr/bin/env python3

import time
import os
import signal
import sys
try:
    from smbus2 import SMBus
except ImportError:
    from smbus import SMBus
import RPi.GPIO as GPIO
from dotenv import load_dotenv

# --------------------------------------------------
# Load config
# --------------------------------------------------
load_dotenv("/usr/local/rv-generator/.env")

V_START = float(os.getenv("VOLTAGE_START"))
V_STOP  = float(os.getenv("VOLTAGE_STOP"))

START_PULSE = int(os.getenv("START_PULSE_TIME"))
STOP_PULSE  = int(os.getenv("STOP_PULSE_TIME"))
MIN_RUN     = int(os.getenv("MIN_RUN_TIME"))
RETRY_DELAY = int(os.getenv("RETRY_DELAY"))
MAX_ATTEMPTS = int(os.getenv("MAX_START_ATTEMPTS"))

TEMP_ENABLE = os.getenv("TEMP_ENABLE").lower() == "true"
TEMP_START  = float(os.getenv("TEMP_START_BELOW", 999))

I2C_BUS = int(os.getenv("I2C_BUS"))
INA_ADDR = int(os.getenv("INA226_ADDR"), 16)

RELAY_START = int(os.getenv("RELAY_START_GPIO"))
RELAY_STOP  = int(os.getenv("RELAY_STOP_GPIO"))

SAMPLE_INTERVAL = int(os.getenv("VOLTAGE_SAMPLE_INTERVAL"))
LOG_INTERVAL = int(os.getenv("LOG_INTERVAL"))

# --------------------------------------------------
# INA226 (VBUS only)
# --------------------------------------------------
REG_CONFIG = 0x00
REG_BUS_VOLTAGE = 0x02

bus = smbus.SMBus(I2C_BUS)

def swap16(x):
    return ((x << 8) & 0xFF00) | (x >> 8)

def ina_init():
    config = 0x4127
    bus.write_word_data(INA_ADDR, REG_CONFIG, swap16(config))

def read_voltage():
    raw = bus.read_word_data(INA_ADDR, REG_BUS_VOLTAGE)
    raw = swap16(raw)
    return raw * 0.00125

# --------------------------------------------------
# GPIO
# --------------------------------------------------
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

GPIO.setup(RELAY_START, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(RELAY_STOP,  GPIO.OUT, initial=GPIO.LOW)

def pulse(pin, seconds):
    GPIO.output(pin, GPIO.HIGH)
    time.sleep(seconds)
    GPIO.output(pin, GPIO.LOW)

# --------------------------------------------------
# Shutdown handling
# --------------------------------------------------
def shutdown(*_):
    GPIO.output(RELAY_START, GPIO.LOW)
    GPIO.output(RELAY_STOP, GPIO.LOW)
    GPIO.cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

# --------------------------------------------------
# Main logic
# --------------------------------------------------
def main():
    ina_init()
    attempts = 0
    gen_running = False
    run_start = None
    last_log = 0

    print("RV Generator service started")

    while True:
        voltage = read_voltage()
        now = time.time()

        if now - last_log > LOG_INTERVAL:
            print(f"Voltage: {voltage:.2f} V")
            last_log = now

        if not gen_running:
            if voltage < V_START:
                if attempts < MAX_ATTEMPTS:
                    print("Starting generator")
                    pulse(RELAY_START, START_PULSE)
                    attempts += 1
                    time.sleep(RETRY_DELAY)
                else:
                    print("Max start attempts reached")
            else:
                attempts = 0
        else:
            if (now - run_start) > MIN_RUN and voltage >= V_STOP:
                print("Stopping generator")
                pulse(RELAY_STOP, STOP_PULSE)
                gen_running = False

        if not gen_running and voltage > V_START + 0.5:
            gen_running = True
            run_start = now
            attempts = 0

        time.sleep(SAMPLE_INTERVAL)

if __name__ == "__main__":
    main()
