#!/usr/bin/env python3

import os
import time
import signal
import sys
from datetime import datetime

from dotenv import load_dotenv
from smbus2 import SMBus
import gpiod
from gpiod.line import Direction, Value

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
GPIO_CHIP = os.getenv("GPIO_CHIP", "/dev/gpiochip4")

RELAY_START_LINE = int(os.getenv("RELAY_START_GPIO", "5"))
RELAY_STOP_LINE  = int(os.getenv("RELAY_STOP_GPIO", "6"))

# ------------------ Logging ------------------
LOG_INTERVAL = int(os.getenv("LOG_INTERVAL", "30"))
LOG_FILE = os.getenv(
    "LOG_FILE",
    "/usr/local/rv-generator/rv-generator.log"
)

# ==================================================
# Logging helper
# ==================================================
def log_line(message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{timestamp} {message}"

    # Write to file
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception as e:
        print(f"{timestamp} LOG FILE ERROR: {e}")

    # Always print to stdout for journalctl
    print(line)

# ==================================================
# INA226
# ==================================================
REG_CONFIG      = 0x00
REG_BUS_VOLTAGE = 0x02

def swap16(val: int) -> int:
    return ((val << 8) & 0xFF00) | (val >> 8)

bus = SMBus(I2C_BUS)

def ina_init():
    # Continuous bus voltage conversion
    config = 0x4127
    bus.write_word_data(INA_ADDRESS, REG_CONFIG, swap16(config))
    log_line("INA226 initialized")

def read_voltage() -> float:
    raw = bus.read_word_data(INA_ADDRESS, REG_BUS_VOLTAGE)
    raw = swap16(raw)
    return raw * 0.00125  # 1.25 mV per bit

# ==================================================
# GPIO via libgpiod v2
# ==================================================
chip = gpiod.Chip(GPIO_CHIP)

lines = chip.request_lines(
    consumer="rv-generator",
    config={
        RELAY_START_LINE: gpiod.LineSettings(
            direction=Direction.OUTPUT,
            output_value=Value.INACTIVE
        ),
        RELAY_STOP_LINE: gpiod.LineSettings(
            direction=Direction.OUTPUT,
            output_value=Value.INACTIVE
        ),
    }
)

def pulse(line_offset: int, seconds: int):
    log_line(f"Pulsing relay {line_offset} for {seconds}s")
    lines.set_value(line_offset, Value.ACTIVE)
    time.sleep(seconds)
    lines.set_value(line_offset, Value.INACTIVE)

# ==================================================
# Shutdown handler
# ==================================================
def shutdown_handler(signum, frame):
    log_line("Shutting down service, turning relays OFF")
    lines.set_value(RELAY_START_LINE, Value.INACTIVE)
    lines.set_value(RELAY_STOP_LINE, Value.INACTIVE)
    lines.release()
    chip.close()
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

# ==================================================
# Main loop
# ==================================================
def main():
    log_line("RV Generator Controller started")
    log_line(f"Using GPIO chip: {GPIO_CHIP}")

    ina_init()

    generator_running = False
    run_start_time = None
    start_attempts = 0
    last_log = 0

    while True:
        voltage = read_voltage()
        now = time.time()

        # Periodic voltage logging
        if now - last_log >= LOG_INTERVAL:
            log_line(f"Battery Voltage: {voltage:.2f} V")
            last_log = now

        # ---------------- Generator NOT running ----------------
        if not generator_running:
            if voltage < VOLTAGE_START:
                if start_attempts < MAX_ATTEMPTS:
                    log_line(
                        f"Voltage low ({voltage:.2f} V < {VOLTAGE_START:.2f} V), starting generator"
                    )
                    pulse(RELAY_START_LINE, START_PULSE_TIME)
                    start_attempts += 1
                    time.sleep(RETRY_DELAY)
                else:
                    log_line("Max start attempts reached, waiting")
            else:
                start_attempts = 0

            # Detect successful start
            if voltage > (VOLTAGE_START + 0.5):
                generator_running = True
                run_start_time = now
                start_attempts = 0
                log_line("Generator detected as running")

        # ---------------- Generator running ----------------
        else:
            run_time = now - run_start_time
            if run_time >= MIN_RUN_TIME and voltage >= VOLTAGE_STOP:
                log_line(
                    f"Voltage high ({voltage:.2f} V >= {VOLTAGE_STOP:.2f} V), stopping generator"
                )
                pulse(RELAY_STOP_LINE, STOP_PULSE_TIME)
                generator_running = False
                run_start_time = None

        time.sleep(SAMPLE_INTERVAL)

# ==================================================
# Entry point
# ==================================================
if __name__ == "__main__":
    main()
