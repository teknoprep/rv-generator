# 🚐 RV Generator Controller

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

<p align="center">
  <img src="https://github.com/teknoprep/rv-generator/blob/main/board1.jpg" width="600"><br>
  <em>Raspberry Pi–based RV Generator Controller (Prototype Board)</em>
</p>

A **Raspberry Pi–based automatic generator controller** designed for RV use.  
This service safely controls generator start/stop relays, monitors system conditions
(temperature, voltage/current), and runs reliably as a background service at boot.

Built for **stability, safety, and unattended operation**.

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

### I²C (INA226)
| Signal | GPIO | Pin |
|------|------|-----|
| SDA | GPIO 2 | Pin 3 |
| SCL | GPIO 3 | Pin 5 |

---

### 🌡️ Temperature Sensor (DHT22)
| Signal | GPIO | Pin |
|------|------|-----|
| DATA | GPIO 4 | Pin 7 |
| VCC | 3.3 V | Pin 1 |
| GND | GND | Any |

---

## ⚠️ Safety Notes
- Relays are **forced OFF at boot** to prevent unintended generator starts
- Always test with the generator **disabled** before live operation
- Ensure proper fuse protection and isolation where required
- Use a common ground for all logic-level components

---

## 📁 Repository Layout
```text
rv-generator/
├── README.md
├── install.sh
├── board1.jpg
├── src/
├── systemd/
└── scripts/
```

---

## 📜 License
MIT License
