# 🚐 RV Generator Controller

<p align="center">
  <img src="https://github.com/teknoprep/rv-generator/blob/main/board1.jpg" width="600"><br>
  <em>Raspberry Pi–based RV Generator Controller (Prototype Board)</em>
</p>

A **Raspberry Pi–based automatic generator controller** designed for RV use.  
This service safely controls generator start/stop relays, monitors system conditions
(temperature, voltage/current), and runs reliably as a background service at boot.

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
- Extract it (right‑click → *Extract* or via terminal)

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

- You will be prompted for your **sudo password**
- Python dependencies are installed in a **virtual environment**
- A **systemd service** is created and enabled
- All relays are forced **OFF** during setup

---

### 3️⃣ Verify Operation
```bash
systemctl status rv-generator.service
```

View live logs:
```bash
journalctl -u rv-generator.service -f
```

---

### 🔁 Service Control
```bash
sudo systemctl start rv-generator.service
sudo systemctl stop rv-generator.service
sudo systemctl restart rv-generator.service
```

The service starts **automatically on boot**.

---

## ✅ Features
- ✅ Automatic generator control via relays
- ✅ Designed for **ACTIVE-HIGH relay boards**
- ✅ Temperature monitoring (DHT22)
- ✅ Voltage & current monitoring (INA226)
- ✅ Physical switch inputs supported
- ✅ Safe startup (all relays OFF)
- ✅ Runs as a **systemd service**
- ✅ Clean install with virtual environment (PEP-668 safe)
- ✅ Logs to `journalctl`
- ✅ Minimal Raspberry Pi OS footprint

---

## 🧰 Hardware Assumptions
- Raspberry Pi 3B+ (or compatible)
- 5 V relay module (ACTIVE-HIGH)
- Generator with momentary START / STOP control
- DHT22 temperature sensor
- INA226 power monitor (optional but recommended)
- Common ground for all logic-level devices

---

## 🔌 GPIO Pin Assignments

### Relays (ACTIVE-HIGH)
| Relay | Physical Pin | GPIO |
|------|-------------|------|
| Relay 1 | Pin 29 | GPIO 5 |
| Relay 2 | Pin 31 | GPIO 6 |
| Relay 3 | Pin 33 | GPIO 13 |
| Relay 4 | Pin 35 | GPIO 19 |

- `GPIO.HIGH` → Relay **ON**
- `GPIO.LOW` → Relay **OFF**
- All relays are initialized **OFF** at startup

---

## 🔧 RV Generator Wiring Instructions

⚠️ **IMPORTANT:**  
This controller interfaces with the **12 V control side** of the RV generator system —  
**NOT** the 120 V AC output.

### 🔋 Power
- The Raspberry Pi and relay board must be powered from the RV’s **12 V system**
- Use a **quality 12 V → 5 V DC converter**
- Ensure **common ground** between:
  - Raspberry Pi
  - Relay board
  - Generator control wiring

---

### ▶️ Generator START Wiring (Relay 1)
- **Relay 1** is used for **START**
- Splice into the generator’s **momentary START switch**
  - Relay **COM** → Switch common
  - Relay **NO** → Start signal wire

✅ Manual and automatic start both work  
✅ Use **NO only** (momentary action)

---

### ⏹️ Generator STOP Wiring (Relay 2)
- **Relay 2** is used for **STOP**
- Wired the same way as START
  - Relay **COM** → Switch common
  - Relay **NO** → Stop signal wire

✅ Prevents unintended shutdowns  
✅ Mimics pressing the STOP button

---

## ⚙️ Configuration (.env File)

All runtime configuration is handled via a `.env` file in the project directory.

### ✅ Complete Example `.env`
```env
# ------------------------
# Relay Configuration
# ------------------------
START_RELAY=5
STOP_RELAY=6

START_PULSE_TIME=2
STOP_PULSE_TIME=2

# ------------------------
# Temperature Automation
# ------------------------
TEMP_START_THRESHOLD=85
TEMP_STOP_THRESHOLD=75

ENABLE_DHT22=true
ENABLE_INA226=true

# ------------------------
# Logging
# ------------------------
LOG_LEVEL=INFO

# ------------------------
# Email / SMTP Alerts
# ------------------------
ENABLE_EMAIL_ALERTS=true

SMTP_SERVER=smtp.example.com
SMTP_PORT=587
SMTP_USE_TLS=true

SMTP_USERNAME=your_email@example.com
SMTP_PASSWORD=your_email_password

EMAIL_FROM=rv-generator@example.com
EMAIL_TO=alert-recipient@example.com
```

---

### 🔍 `.env` Variable Descriptions

#### Relay Control
| Variable | Description |
|--------|-------------|
| `START_RELAY` | GPIO used to start the generator |
| `STOP_RELAY` | GPIO used to stop the generator |
| `START_PULSE_TIME` | Seconds to hold START relay ON |
| `STOP_PULSE_TIME` | Seconds to hold STOP relay ON |

---

#### Temperature Automation
| Variable | Description |
|--------|-------------|
| `TEMP_START_THRESHOLD` | Temperature (°F) that triggers generator start |
| `TEMP_STOP_THRESHOLD` | Temperature (°F) that allows generator stop |
| `ENABLE_DHT22` | Enable temperature sensor |
| `ENABLE_INA226` | Enable voltage/current monitoring |

---

#### Logging
| Variable | Description |
|--------|-------------|
| `LOG_LEVEL` | Log verbosity: `DEBUG`, `INFO`, `WARNING` |

---

#### Email / SMTP Alerts
| Variable | Description |
|--------|-------------|
| `ENABLE_EMAIL_ALERTS` | Enable email notifications |
| `SMTP_SERVER` | SMTP server hostname |
| `SMTP_PORT` | SMTP server port (usually 587) |
| `SMTP_USE_TLS` | Enable TLS encryption |
| `SMTP_USERNAME` | SMTP login username |
| `SMTP_PASSWORD` | SMTP login password |
| `EMAIL_FROM` | Sender email address |
| `EMAIL_TO` | Recipient email address |

📧 Email alerts can be used for:
- Generator start/stop events
- Fault conditions
- Temperature alerts

---

## ⚠️ Safety Notes
- Relays are **forced OFF at boot**
- Always test with generator **disabled**
- Fuse all added wiring
- Verify generator control voltages before connecting
- Assumes **momentary switch logic**

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
