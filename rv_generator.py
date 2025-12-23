#!/usr/bin/env python3

import os
import time
import signal
import sys

import RPi.GPIO as GPIO
from dotenv import load_dotenv

# ---------- I2C (smbus / smbus2) ----------
try:
    from smbus2 import SMBus
except ImportError:
    from smbus import SMBus


# ==================================================
# Load configuration
# ==================================================
ENV_PATH = "/usr/local/rv-generator/.env"
load_dotenv(ENV_PATH)

# Voltage thresholds
VOLTAGE_START = float(os.getenv("VOLTAGE_START", "12.0"))
VOLTAGE_STOP  = float(os.getenv("VOLTAGE_STOP", "13.6"))

# Timing (seconds)
START_PULSE_TIME = int(os.getenv("START_PULSE_TIME", "2"))
STOP_PULSE_TIME  = int(os.getenv("STOP_PULSE_TIME", "2"))
MIN_RUN_TIME     = int(os.getenv("MIN_RUN_TIME", "1800"))
RETRY_DELAY      = int(os.getenv("RETRY_DELAY", "60"))
MAX_ATTEMPTS     = int(os.getenv("MAX_START_ATTEMPTS", "3"))

# INA226
I2C_BUS     = int(os.getenv("I2C_BUS", "1"))
INA_ADDRESS = int(os.getenv("INA226_ADDR", "0x40"), 16)
SAMPLE_INTERVAL = int(os.getenv("VOLTAGE_SAMPLE_INTERVAL", "5"))

# Relays (ACTIVE-HIGH)
RELAY_START_GPIO = int(os.getenv("RELAY_START_GPIO", "5"))
RELAY_STOP_GPIO  = int(os.getenv("RELAY_STOP_GPIO", "6"))

# Logging
LOG_INTERVAL = int(os.getenv("LOG_INTERVAL", "30"))

# ==================================================
# INA226 Registers
# ==================================================
REG_CONFIG        = 0x00
REG_BUS_VOLTAGE   = 0x02

# ==================================================
# Helpers
# ==================================================
def swap16(val: int) -> int:
    return ((val << 8) & 0xFF00) | (val >> 8)


# ==================================================
# INA226 Setup
# ==================================================
bus = SMBus(I2C_BUS)

def ina_init():
    # Continuous bus + shunt voltage, 1.1ms conversion
    config = 0x4127
    bus.write_word_data(INA_ADDRESS, REG_CONFIG, swap16(config))


def read_voltage() -> float:
    raw = bus.read_word_data(INA_ADDRESS, REG_BUS_VOLTAGE)
    raw = swap16(raw)
    return raw * 0.00125   # 1.25mV per bit


# ==================================================
# GPIO Setup
# ==================================================
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

GPIO.setup(RELAY_START_GPIO, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(RELAY_STOP_GPIO,  GPIO.OUT, initial=GPIO.LOW)

def pulse_relay(pin: int, seconds: int):
    GPIO.output(pin, GPIO.HIGH)
    time.sleep(seconds)
    GPIO.output(pin, GPIO.LOW)


# ==================================================
# Clean shutdown
# ==================================================
def shutdown_handler(signum, frame):
    print("Shutting down service, turning relays OFF")
    GPIO.output(RELAY_START_GPIO, GPIO.LOW)
    GPIO.output(RELAY_STOP_GPIO, GPIO.LOW)
    GPIO.cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)


# ==================================================
# Main Loop
# ==================================================
def main():
    print("RV Generator Controller starting")
    ina_init()

    generator_running = False
    run_start_time = None
    start_attempts = 0
    last_log = 0

    while True:
        voltage = read_voltage()
        now = time.time()

        # Periodic log
        if now - last_log >= LOG_INTERVAL:
            print(f"Battery Voltage: {voltage:.2f} V")
            last_log = now

        # -------- Generator not running --------
        if not generator_running:
            if voltage < VOLTAGE_START:
                if start_attempts < MAX_ATTEMPTS:
                    print("Starting generator")
                    pulse_relay(RELAY_START_GPIO, START_PULSE_TIME)
                    start_attempts += 1
                    time.sleep(RETRY_DELAY)
                else:
                    print("Max start attempts reached, waiting")
            else:
                start_attempts = 0

            # Detect successful start by voltage rise
            if voltage > (VOLTAGE_START + 0.5):
                generator_running = True
                run_start_time = now
                start_attempts = 0
                print("Generator detected as running")

        # -------- Generator running --------
        else:
            run_time = now - run_start_time

            if run_time >= MIN_RUN_TIME and voltage >= VOLTAGE_STOP:
                print("Stopping generator")
                pulse_relay(RELAY_STOP_GPIO, STOP_PULSE_TIME)
                generator_running = False
                run_start_time = None

        time.sleep(SAMPLE_INTERVAL)


# ==================================================
# Entry Point
# ==================================================
if __name__ == "__main__":
    main()
