#!/usr/bin/env python3

import os
import time
import signal
import sys
from datetime import datetime
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv
from smbus2 import SMBus
import gpiod
from gpiod.line import Direction, Value

# ==================================================
# Load configuration
# ==================================================
ENV_PATH = "/usr/local/rv-generator/.env"
load_dotenv(ENV_PATH)

VOLTAGE_START = float(os.getenv("VOLTAGE_START", "12.3"))
VOLTAGE_STOP  = float(os.getenv("VOLTAGE_STOP", "13.6"))
VOLTAGE_RISE_CONFIRM = float(os.getenv("VOLTAGE_RISE_CONFIRM", "0.3"))

START_PULSE_TIME = int(os.getenv("START_PULSE_TIME", "2"))
STOP_PULSE_TIME  = int(os.getenv("STOP_PULSE_TIME", "2"))
MIN_RUN_TIME     = int(os.getenv("MIN_RUN_TIME", "1800"))
RETRY_DELAY      = int(os.getenv("RETRY_DELAY", "60"))
MAX_ATTEMPTS     = int(os.getenv("MAX_START_ATTEMPTS", "3"))

I2C_BUS     = int(os.getenv("I2C_BUS", "1"))
INA_ADDRESS = int(os.getenv("INA226_ADDR", "0x40"), 16)
SAMPLE_INTERVAL = int(os.getenv("VOLTAGE_SAMPLE_INTERVAL", "5"))

GPIO_CHIP = os.getenv("GPIO_CHIP", "/dev/gpiochip4")
RELAY_START_LINE = int(os.getenv("RELAY_START_GPIO", "5"))
RELAY_STOP_LINE  = int(os.getenv("RELAY_STOP_GPIO", "6"))

LOG_INTERVAL = int(os.getenv("LOG_INTERVAL", "30"))
LOG_FILE = os.getenv("LOG_FILE", "/usr/local/rv-generator/rv-generator.log")

SMTP_ENABLED = os.getenv("SMTP_ENABLED", "false").lower() == "true"
SMTP_SERVER  = os.getenv("SMTP_SERVER", "")
SMTP_PORT    = int(os.getenv("SMTP_PORT", "0"))
SMTP_USER    = os.getenv("SMTP_USER", "")
SMTP_PASS    = os.getenv("SMTP_PASS", "")
SMTP_FROM    = os.getenv("SMTP_FROM", "")
SMTP_TO      = os.getenv("SMTP_TO", "")
SMTP_SUBJECT = os.getenv("SMTP_SUBJECT", "RV Alerts")
SMTP_TLS     = os.getenv("SMTP_TLS", "true").lower() == "true"

# ==================================================
# Logging
# ==================================================
def log_line(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{ts} {msg}"
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass
    print(line)

# ==================================================
# Email
# ==================================================
def send_email(msg_text):
    if not SMTP_ENABLED:
        return
    try:
        msg = EmailMessage()
        msg["From"] = SMTP_FROM
        msg["To"] = SMTP_TO
        msg["Subject"] = SMTP_SUBJECT
        msg.set_content(msg_text)
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as s:
            if SMTP_TLS:
                s.starttls()
            if SMTP_USER and SMTP_PASS:
                s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
    except Exception as e:
        log_line(f"EMAIL ERROR: {e}")

# ==================================================
# INA226
# ==================================================
REG_CONFIG = 0x00
REG_BUS_VOLTAGE = 0x02

def swap16(v):
    return ((v << 8) & 0xFF00) | (v >> 8)

bus = SMBus(I2C_BUS)

def ina_init():
    bus.write_word_data(INA_ADDRESS, REG_CONFIG, swap16(0x4127))
    log_line("INA226 initialized")

def read_voltage():
    raw = swap16(bus.read_word_data(INA_ADDRESS, REG_BUS_VOLTAGE))
    return raw * 0.00125

# ==================================================
# GPIO via libgpiod v2 (CORRECT)
# ==================================================
chip = gpiod.Chip(GPIO_CHIP)

lines = chip.request_lines(
    [RELAY_START_LINE, RELAY_STOP_LINE],
    consumer="rv-generator",
    config=gpiod.LineSettings(
        direction=Direction.OUTPUT,
        output_value=Value.INACTIVE,
        active_low=False
    )
)

def pulse(line, sec):
    log_line(f"Pulsing relay {line} for {sec}s")
    lines.set_value(line, Value.ACTIVE)
    time.sleep(sec)
    lines.set_value(line, Value.INACTIVE)

# ==================================================
# Shutdown
# ==================================================
def shutdown_handler(*_):
    log_line("Service shutting down")
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
    ina_init()

    generator_running = False
    run_start = None
    attempts = 0

    while True:
        voltage = read_voltage()
        now = time.time()

        log_line(f"Battery Voltage: {voltage:.2f} V")

        if not generator_running:
            if voltage < VOLTAGE_START and attempts < MAX_ATTEMPTS:
                start_v = voltage
                log_line(f"Starting generator (voltage {start_v:.2f} V)")
                pulse(RELAY_START_LINE, START_PULSE_TIME)
                time.sleep(RETRY_DELAY)

                new_v = read_voltage()
                delta = new_v - start_v

                if delta >= VOLTAGE_RISE_CONFIRM:
                    generator_running = True
                    run_start = time.time()
                    attempts = 0
                    msg = f"Generator confirmed running (ΔV={delta:.2f} V)"
                    log_line(msg)
                    send_email(msg)
                else:
                    attempts += 1
                    msg = f"Start failed (ΔV={delta:.2f} V)"
                    log_line(msg)
                    send_email(msg)

        else:
            if now - run_start >= MIN_RUN_TIME and voltage >= VOLTAGE_STOP:
                msg = "Stopping generator (battery charged)"
                log_line(msg)
                send_email(msg)
                pulse(RELAY_STOP_LINE, STOP_PULSE_TIME)
                generator_running = False
                run_start = None

        time.sleep(SAMPLE_INTERVAL)

if __name__ == "__main__":
    main()
