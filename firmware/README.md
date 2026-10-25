# ESP32 Checkpoint Hardware Firmware & Wiring Guide

This directory contains the physical hardware firmware for the **Zero Trust Authentication Smart Label System**.

The edge microcontroller runs embedded C++ on the **ESP32 DevKit V1**, communicating with the host computer over a **high-speed USB Serial Bridge (115200 baud)**. All verification decisions and status indicators are rendered **in the software dashboard** and on the **on-board 0.96" I2C OLED screen**, without external physical breadboard LEDs.

---

## 1. Hardware Pinout Connection Table

### A. RC522 RFID Reader (SPI Interface) to ESP32

| MFRC522 Pin | ESP32 GPIO Pin | Wire Function |
|---|---|---|
| **VCC** | **3.3V** | 3.3V DC Power (⚠️ Strictly 3.3V, do NOT connect to 5V!) |
| **RST** | **GPIO 22** | Module Reset Pin |
| **GND** | **GND** | Common Ground |
| **MISO** | **GPIO 19** | SPI Master In Slave Out |
| **MOSI** | **GPIO 23** | SPI Master Out Slave In |
| **SCK** | **GPIO 18** | SPI Serial Clock |
| **SDA / SS** | **GPIO 5** | SPI Slave Select |

---

### B. SSD1306 0.96" I2C OLED Display to ESP32

The OLED display shows the active checkpoint number (e.g., `Checkpoint 1`), the scanned UID, and `TAMPERED` alerts locally on the station rig.

| OLED Pin | ESP32 GPIO Pin | Function |
|---|---|---|
| **VCC** | **3.3V** | 3.3V DC Power |
| **GND** | **GND** | Common Ground |
| **SDA** | **GPIO 16** | I2C Serial Data |
| **SCL** | **GPIO 17** | I2C Serial Clock |

---

### C. Package Tamper Detection Loop & Checkpoint Button

| Component | ESP32 Connection | Description |
|---|---|---|
| **Tamper Wire Lead A** | **GPIO 15** | Set to `INPUT_PULLDOWN` / `INPUT_PULLUP` mode in firmware. |
| **Tamper Wire Lead B** | **3.3V / GND** | When the wire loop across the box seal is intact, the circuit is closed (`SAFE`). When sliced or opened, the loop breaks (`TAMPERED`). |
| **Checkpoint Push Button** | **GPIO 12** | Set to `INPUT_PULLUP`. Pressing increments the active checkpoint (1 $\rightarrow$ 2 $\rightarrow$ 3 $\rightarrow$ 4 $\rightarrow$ 1). |

*(Note: Physical LEDs are not used on the hardware rig. All decision scoring results [ALLOW, FLAG, QUARANTINE] and color-coded status badges are presented in the web dashboard software).*

---

## 2. Circuit Diagram Overview

```
                         +-------------------+
                         |   ESP32 DevKit    |
                         |                   |
     [RC522 RFID]        |                   |
     SDA (SS) ---------> | GPIO 5            |
     SCK --------------> | GPIO 18           |       +---------------------+
     MOSI -------------> | GPIO 23           |       | I2C OLED Display    |
     MISO -------------> | GPIO 19           | ----> | SDA (GPIO 16)       |
     RST --------------> | GPIO 22           | ----> | SCL (GPIO 17)       |
     3.3V -------------> | 3.3V              |       | VCC / GND (3.3V)    |
     GND --------------> | GND               |       +---------------------+
                         |                   |
     [Package Seal]      |                   |
     Tamper Lead A ----> | GPIO 15           | (Internal Pullup/Pulldown)
     Tamper Lead B ----> | GND               |
                         |                   |
     [Advance Button]    |                   |
     Button Pin -------> | GPIO 12           | (Internal Pullup to GND)
                         |                   |
     [USB Data Cable]    |                   |
     USB to Laptop ----> | Serial (115200)   | ====> USB Serial Python Bridge (serial_bridge.py)
                         +-------------------+
```

---

## 3. How to Compile & Flash via Arduino IDE

1. **Install ESP32 Board Manager**:
   - Open Arduino IDE $\rightarrow$ `Preferences` $\rightarrow$ Additional Board Manager URLs:
     `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
   - Tools $\rightarrow$ Board $\rightarrow$ Boards Manager $\rightarrow$ Search **ESP32** by Espressif $\rightarrow$ Install.
2. **Install Required Libraries**:
   - `MFRC522` by GitHubCommunity (for RC522 RFID SPI reader)
   - `Adafruit SSD1306` by Adafruit (for I2C OLED display)
   - `Adafruit GFX Library` by Adafruit
3. **Flash ESP32**:
   - Open [`firmware/esp32_checkpoint.ino`](file:///c:/Users/duddu/Downloads/tarpproj/firmware/esp32_checkpoint.ino).
   - Select Board: `ESP32 Dev Module`.
   - Select Port: COM port of the connected ESP32.
   - Click **Upload**.
4. **Run USB Serial Bridge on Host PC**:
   - In your project root terminal:
     ```powershell
     python serial_bridge.py
     ```
   - The bridge reads scan events from the serial port at 115200 baud and streams them via HTTP POST to the local FastAPI backend.
