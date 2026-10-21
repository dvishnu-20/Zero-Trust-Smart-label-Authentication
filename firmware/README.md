# ESP32 Checkpoint Hardware Firmware & Wiring Guide

This directory contains the physical hardware firmware for the **Zero Trust Authentication Smart Label System**.

---

## 1. Hardware Pinout Connection Table

### RC522 RFID Reader (SPI Interface) to ESP32

| MFRC522 Pin | ESP32 GPIO Pin | Function |
|---|---|---|
| **VCC** | **3.3V** | 3.3V Power (Do NOT connect to 5V!) |
| **RST** | **GPIO 22** | Reset Pin |
| **GND** | **GND** | Ground |
| **MISO** | **GPIO 19** | SPI Master In Slave Out |
| **MOSI** | **GPIO 23** | SPI Master Out Slave In |
| **SCK** | **GPIO 18** | SPI Serial Clock |
| **SDA / SS** | **GPIO 5** | SPI Slave Select |

---

### Conductive Package Tamper Loop Pin Connection

The conductive tamper detection seal uses a digital GPIO input with an internal pullup resistor.

| Hardware Wire | ESP32 Connection | Notes |
|---|---|---|
| **Tamper Wire Input** | **GPIO 4** | Set to `INPUT_PULLUP` mode in firmware. |
| **Tamper Wire Return** | **GND** | When wire loop across box seal is intact, GPIO 4 is pulled LOW (`SAFE`). When broken/opened, GPIO 4 pulls HIGH (`TAMPERED`). |

---

### Physical Output Status LEDs & Buzzer

| Output Component | ESP32 GPIO Pin | Color / Decision |
|---|---|---|
| **Green LED** | **GPIO 26** | **ALLOW** (Trust Score 80–100) |
| **Yellow LED** | **GPIO 25** | **FLAG** (Trust Score 50–79) |
| **Red LED** | **GPIO 33** | **QUARANTINE** (Trust Score < 50 or Tampered) |
| **Piezo Buzzer (+)**| **GPIO 27** | Audible Warning / Alarm |
| **LED / Buzzer (-)**| **GND** | Common Ground (Use 220Ω resistors for LEDs) |

---

## 2. Circuit Diagram Overview

```
                        +-------------------+
                        |   ESP32 DevKit    |
                        |                   |
    [RC522 RFID]        |                   |
    SDA ------------->  | GPIO 5            |
    SCK ------------->  | GPIO 18           |       +--------------------+
    MOSI ------------>  | GPIO 23           |       | Physical Status    |
    MISO ------------>  | GPIO 19           | ----> | Green LED (GPIO 26)|
    RST ------------->  | GPIO 22           | ----> | Yellow LED (GPIO 25|
    3.3V ------------>  | 3.3V              | ----> | Red LED (GPIO 33)  |
    GND ------------->  | GND               | ----> | Buzzer (GPIO 27)   |
                        |                   |       +--------------------+
                        |                   |
    [Package Seal]      |                   |
    Loop Pin -------->  | GPIO 4            | (Internal Pullup)
    Loop Return ----->  | GND               |
                        +-------------------+
```

---

## 3. How to Compile & Flash via Arduino IDE

1. **Install ESP32 Board Manager**:
   - Open Arduino IDE $\rightarrow$ `Preferences` $\rightarrow$ Additional Board Manager URLs: `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
   - Tools $\rightarrow$ Board $\rightarrow$ Boards Manager $\rightarrow$ Search **ESP32** by Espressif $\rightarrow$ Install.
2. **Install Required Libraries**:
   - `MFRC522` by GitHubCommunity (for RC522 RFID SPI reader)
   - `ArduinoJson` by Benoit Blanchon (for HTTP JSON serialization)
3. **Configure Wi-Fi & Backend URL**:
   - Open `esp32_checkpoint.ino`.
   - Update `WIFI_SSID` and `WIFI_PASSWORD` with your local Wi-Fi router or phone hotspot credentials.
   - Update `BACKEND_SCAN_URL` with your laptop's LAN IP (e.g. `http://192.168.1.105:8000/api/scan`).
4. **Flash ESP32**:
   - Select Board: `ESP32 Dev Module`.
   - Select Port: COM port of ESP32.
   - Click **Upload**.
