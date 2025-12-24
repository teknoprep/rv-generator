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
- Use a **quality 12 V → 5 V DC converter** capable of supplying the Pi + relays
- Ensure **common ground** between:
  - Raspberry Pi
  - Relay board
  - Generator control wiring

---

### ▶️ Generator START Wiring (Relay 1)

- **Relay 1** is used for **START**
- Locate the generator’s **momentary START switch**
- Identify:
  - **Common**
  - **Start signal wire**

#### Wiring Method
- Leave the factory switch intact
- **Splice** into the START circuit:
  - Relay **COM** → Common wire on start switch
  - Relay **NO (Normally Open)** → Start signal wire

✅ This allows:
- Manual starting via the original switch
- Automatic starting via the relay

❗ Use **NO only** — you only want to close the circuit when issuing a START command.

---

### ⏹️ Generator STOP Wiring (Relay 2)

- **Relay 2** is used for **STOP**
- Locate the generator’s **momentary STOP switch**
- Identify:
  - **Common**
  - **Stop signal wire**

#### Wiring Method
- Same as START:
  - Relay **COM** → Common wire on stop switch
  - Relay **NO (Normally Open)** → Stop signal wire

✅ Manual stop still works  
✅ Relay issues a momentary STOP when commanded

---

### ✅ Why NO (Normally Open)?
- Prevents accidental start/stop on:
  - Boot
  - Power loss
  - Software crash
- Relay only closes the circuit **intentionally**
- Mimics a human pressing the button

---

## 🌡️ Temperature Sensor (DHT22)
| Signal | GPIO | Pin |
|------|------|-----|
| DATA | GPIO 4 | Pin 7 |
| VCC | 3.3 V | Pin 1 |
| GND | GND | Any |

---

## ⚙️ Configuration (.env File)

Configuration is handled via a `.env` file located in the project directory.

### Example `.env`
```env
START_RELAY=5
STOP_RELAY=6

START_PULSE_TIME=2
STOP_PULSE_TIME=2

TEMP_START_THRESHOLD=85
TEMP_STOP_THRESHOLD=75

ENABLE_INA226=true
ENABLE_DHT22=true

LOG_LEVEL=INFO
```

---

### 🔍 Variable Descriptions

| Variable | Description |
|--------|-------------|
| `START_RELAY` | GPIO number used for generator START |
| `STOP_RELAY` | GPIO number used for generator STOP |
| `START_PULSE_TIME` | Seconds to hold START relay ON |
| `STOP_PULSE_TIME` | Seconds to hold STOP relay ON |
| `TEMP_START_THRESHOLD` | Temperature (°F) to auto‑start generator |
| `TEMP_STOP_THRESHOLD` | Temperature (°F) to stop generator |
| `ENABLE_INA226` | Enable voltage/current monitoring |
| `ENABLE_DHT22` | Enable temperature monitoring |
| `LOG_LEVEL` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`) |

💡 These values can be adjusted without changing code.

---

## ⚠️ Safety Notes
- Relays are **forced OFF at boot**
- Always test with generator **disabled**
- Fuse all added wiring appropriately
- Verify generator control voltages before connecting
- This project assumes **momentary switch logic**

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
