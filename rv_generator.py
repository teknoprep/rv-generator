#!/usr/bin/env python3

import os
import time
import signal
import sys

from dotenv import load_dotenv
from smbus2 import SMBus
import gpiod

# ==================================================
# Load configuration
# ==================================================
ENV_PATH = "/usr/local/rv-generator/.env"
load_dotenv(ENV_PATH)

# ------------------ Voltage thresholds ------------------
VOLTAGE_START = float(os.getenv("VOLTAGE_START", "12.0"))
VOLTAGE_STOP  = float(os.getenv("VOLTAGE_STOP", "13.6"))

# ------------------ Timing (seconds) ------------------
START_PULSE_TIME = int(os.getenv("START_PULSE_TIME", "2"))
STOP_PULSE_TIME  = int(os.getenv("STOP_PULSE_TIME", "2"))
MIN_RUN_TIME     = int(os.getenv("MIN_RUN_TIME", "1800"))
RETRY_DELAY      = int(os.getenv("RETRY_DELAY", "60"))
MAX_ATTEMPTS     = int(os.getenv("MAX_START_ATTEMPTS", "3"))

# ------------------ INA226 ------------------
I2C_BUS     = int(os.getenv("I2C_BUS", "1"))
INA_ADDRESS = int(os.getenv("INA226_ADDR", "0x40"), 16)
SAMPLE_INTERVAL = int(os.getenv("VOLTAGE_SAMPLE_INTERVAL", "5"))

# ------------------ GPIO / Relays ------------------
GPIO_CHIP = os.getenv("GPIO_CHIP", "gpiochip0")

RELAY_START_LINE = int(os.getenv("RELAY_START_GPIO", "5"))
RELAY_STOP_LINE  = int(os.getenv("RELAY_STOP_GPIO", "6"))

LOG_INTERVAL = int(os.getenv("LOG_INTERVAL", "30"))

# ==================================================
# INA226 registers
# ==================================================
REG_CONFIG      = 0x00
REG_BUS_VOLTAGE = 0x02

def swap16(val):
    return ((val << 8) & 0xFF00) | (val >> 8)

# ==================================================
# INA226 setup
# ==================================================
bus = SMBus(I2C_BUS)

def ina_init():
    # Continuous bus voltage conversion
    config = 0x4127
    bus.write_word_data(INA_ADDRESS, REG_CONFIG, swap16(config))

def read_voltage():
    raw = bus.read_word_data(INA_ADDRESS, REG_BUS_VOLTAGE)
    raw = swap16(raw)
    return raw * 0.00125  # 1.25mV per bit

# ==================================================
# GPIO via libgpiod
# ==================================================
chip = gpiod.Chip(GPIO_CHIP)

relay_start = chip.get_line(RELAY_START_LINE)
relay_stop  = chip.get_line(RELAY_STOP_LINE)

relay_start.request(
    consumer="rv-generator",
    type=gpiod.LINE_REQ_DIR_OUT,
    default_vals=[0]
)

relay_stop.request(
    consumer="rv-generator",
    type=gpiod.LINE_REQ_DIR_OUT,
    default_vals=[0]
)

def pulse(line, seconds):
    line.set_value(1)
    time.sleep(seconds)
    line.set_value(0)

# ==================================================
# Shutdown handler
# ==================================================
def shutdown_handler(signum, frame):
    relay_start.set_value(0)
    relay_stop.set_value(0)
    relay_start.release()
    relay_stop.release()
    chip.close()
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

# ==================================================
# Main loop
# ==================================================
def main():
    print("RV Generator Controller started")
    print(f"Using GPIO chip: {GPIO_CHIP}")

    ina_init()

    generator_running = False
    run_start_time = None
    start_attempts = 0
    last_log = 0

    while True:
        voltage = read_voltage()
        now = time.time()

        if now - last_log >= LOG_INTERVAL:
            print(f"Battery Voltage: {voltage:.2f} V")
            last_log = now

        if not generator_running:
            if voltage < VOLTAGE_START:
                if start_attempts < MAX_ATTEMPTS:
                    print("Starting generator")
                    pulse(relay_start, START_PULSE_TIME)
                    start_attempts += 1
                    time.sleep(RETRY_DELAY)
                else:
                    print("Max start attempts reached")
            else:
                start_attempts = 0

            if voltage > (VOLTAGE_START + 0.5):
                generator_running = True
                run_start_time = now
                start_attempts = 0
                print("Generator detected as running")

        else:
            run_time = now - run_start_time
            if run_time >= MIN_RUN_TIME and voltage >= VOLTAGE_STOP:
                print("Stopping generator")
                pulse(relay_stop, STOP_PULSE_TIME)
                generator_running = False
                run_start_time = None

        time.sleep(SAMPLE_INTERVAL)

# ==================================================
# Entry point
# ==================================================
if __name__ == "__main__":
    main()
