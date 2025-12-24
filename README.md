# 🚐 RV Generator Controller

<p align="center">
  <img src="https://github.com/teknoprep/rv-generator/blob/main/board1.jpg" width="600"><br>
  <em>Raspberry Pi–based RV Generator Controller (Prototype Board)</em>
</p>

A **Raspberry Pi–based automatic generator controller** designed for RV use.  
This service safely controls generator start/stop relays, monitors battery voltage,
temperature, and system conditions, and runs reliably as a background service at boot.

Built for **stability, safety, and unattended operation**.

---

## 📦 Installation (No Git Required)

These steps install the controller as a **background system service** using a normal
user account with **sudo access**. No Git knowledge is required.

### 1️⃣ Download the Project
- Visit:  
  👉 https://github.com/teknoprep/rv-generator
- Click **Code → Download ZIP**
- Copy the ZIP file to your Raspberry Pi
- Extract it

Or from the terminal:
```bash
cd ~
wget https://github.com/teknoprep/rv-generator/archive/refs/heads/main.zip
unzip main.zip
cd rv-generator-main
```

---

### 2️⃣ Run the Installer
```bash
chmod +x install.sh
./install.sh
```

- Creates a Python virtual environment
- Installs dependencies (PEP‑668 safe)
- Installs and enables a **systemd service**
- Forces **all relays OFF** during setup

---

### 3️⃣ Verify Operation
```bash
systemctl status rv-generator.service
journalctl -u rv-generator.service -f
```

The service starts **automatically on boot**.

---

## ✅ Features
- ✅ Automatic generator start/stop
- ✅ Voltage‑based battery monitoring (INA226)
- ✅ Temperature‑based control (optional)
- ✅ Active‑HIGH relay support
- ✅ Retry logic and minimum runtime enforcement
- ✅ Email alerts (SMTP)
- ✅ Safe boot (relays forced OFF)
- ✅ Designed for unattended RV operation

---

## 🔧 RV Generator Wiring Instructions

⚠️ **IMPORTANT:**  
This controller interfaces with the **12 V generator control circuitry**,  
**NOT the 120 V AC output**.

### 🔋 Power
- Power the Raspberry Pi + relay board from the RV’s **12 V system**
- Use a **12 V → 5 V DC converter**
- Ensure **common ground** between:
  - Raspberry Pi
  - Relay board
  - Generator control wiring

---

### ▶️ Generator START (Relay – NO Contact)
- **START relay** parallels the generator’s momentary START switch
- Wire using **NO (Normally Open)** only:
  - Relay **COM** → Switch common
  - Relay **NO** → Start signal wire

---

### ⏹️ Generator STOP (Relay – NO Contact)
- Wired the same as START:
  - Relay **COM** → Switch common
  - Relay **NO** → Stop signal wire

✅ Manual switch still works  
✅ Relay mimics a button press  
✅ No accidental starts on boot or crash

---

## ⚙️ Configuration (`.env`)

All runtime behavior is controlled via the `.env` file.

### ✅ Complete `.env` Example (Sanitized)

```env
# ==============================
# RV Generator Configuration
# ==============================

# Voltage thresholds (volts)
VOLTAGE_START=11.5
VOLTAGE_STOP=12.6
VOLTAGE_RISE_CONFIRM=0.3

# Timing (seconds)
START_PULSE_TIME=8
STOP_PULSE_TIME=2
MIN_RUN_TIME=1800
RETRY_DELAY=30
MAX_START_ATTEMPTS=3

# Temperature control (°F)
TEMP_ENABLE=false
TEMP_GPIO=4
TEMP_START_BELOW=25.0
TEMP_SAMPLE_INTERVAL=60

# INA226 (Battery Monitor)
I2C_BUS=1
INA226_ADDR=0x40
VOLTAGE_SAMPLE_INTERVAL=10

# Relay GPIOs (ACTIVE-HIGH)
RELAY_START_GPIO=5
RELAY_STOP_GPIO=6

# Logging
LOG_INTERVAL=30
LOG_FILE=/usr/local/rv-generator/rv-generator.log

# GPIO chip (libgpiod)
GPIO_CHIP=/dev/gpiochip4

# ==============================
# SMTP / Email Settings
# ==============================

SMTP_ENABLED=true
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
SMTP_USER=alert@example.com
SMTP_PASS=your_smtp_password
SMTP_TLS=true
SMTP_FROM=rv-generator@example.com
SMTP_TO=you@example.com
SMTP_SUBJECT=RV Generator Alert
```

---

## 🔍 `.env` Variable Explanations

### 🔋 Voltage Control
| Variable | Description |
|--------|-------------|
| `VOLTAGE_START` | Battery voltage that triggers generator start |
| `VOLTAGE_STOP` | Voltage at which generator may stop |
| `VOLTAGE_RISE_CONFIRM` | Required voltage increase to confirm generator is running |

---

### ⏱ Timing & Retry Logic
| Variable | Description |
|--------|-------------|
| `START_PULSE_TIME` | Seconds to hold START relay |
| `STOP_PULSE_TIME` | Seconds to hold STOP relay |
| `MIN_RUN_TIME` | Minimum generator runtime (seconds) |
| `RETRY_DELAY` | Delay between failed start attempts |
| `MAX_START_ATTEMPTS` | Maximum retries before fault |

---

### 🌡 Temperature Control
| Variable | Description |
|--------|-------------|
| `TEMP_ENABLE` | Enable temperature‑based start logic |
| `TEMP_GPIO` | GPIO pin for DHT22 data |
| `TEMP_START_BELOW` | Temperature (°F) to start generator |
| `TEMP_SAMPLE_INTERVAL` | Seconds between temp readings |

---

### 🔌 INA226 Power Monitor
| Variable | Description |
|--------|-------------|
| `I2C_BUS` | I²C bus number |
| `INA226_ADDR` | INA226 I²C address |
| `VOLTAGE_SAMPLE_INTERVAL` | Voltage read interval (seconds) |

---

### 🔁 Relays & GPIO
| Variable | Description |
|--------|-------------|
| `RELAY_START_GPIO` | GPIO pin for START relay |
| `RELAY_STOP_GPIO` | GPIO pin for STOP relay |
| `GPIO_CHIP` | GPIO chip device for libgpiod |

---

### 📝 Logging
| Variable | Description |
|--------|-------------|
| `LOG_INTERVAL` | Log write interval |
| `LOG_FILE` | Log file path |

---

### 📧 SMTP / Email Alerts
| Variable | Description |
|--------|-------------|
| `SMTP_ENABLED` | Enable email alerts |
| `SMTP_SERVER` | SMTP server hostname |
| `SMTP_PORT` | SMTP server port |
| `SMTP_USER` | SMTP username |
| `SMTP_PASS` | SMTP password |
| `SMTP_TLS` | Enable TLS encryption |
| `SMTP_FROM` | Sender address |
| `SMTP_TO` | Recipient address |
| `SMTP_SUBJECT` | Email subject |

Alerts can notify on:
- Generator start / stop
- Voltage faults
- Failed start attempts

---

## ⚠️ Safety Notes
- Relays default **OFF at boot**
- Test with generator disabled
- Fuse all added wiring
- Verify generator control voltages
- Designed for **momentary switch logic only**

---

## 📁 Repository Layout
```text
rv-generator/
├── README.md
├── install.sh
├── board1.jpg
├── .env
├── src/
├── systemd/
└── scripts/
```

---

## 📜 License
MIT License
