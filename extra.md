Here is the complete, practical checklist of **all hardware components, tools, and physical materials** required to assemble and present a **live physical demonstration** of your Zero Trust Smart Label project to faculty.

---

# 📦 Hardware Components Shopping & Preparation List

### 1. Core Electronic Components

| # | Component | Exact Specification | Quantity | Role in the Demonstration |
|---|---|---|---|---|
| **1** | **ESP32 Development Board** | ESP32 DevKit V1 (30-pin or 38-pin) | **1 unit** | Acts as the Checkpoint Controller: reads RFID, senses the tamper loop, displays station status on OLED, and streams scan events over USB Serial. |
| **2** | **RC522 RFID Reader Module** | 13.56 MHz MFRC522 (SPI Interface, 3.3V) | **1 unit** | Contactless scanner that reads the RFID UID from the product label over SPI. |
| **3** | **RFID 13.56 MHz Tags / Cards** | Mifare 1K Classic RFID Cards / Keyfobs / Stickers | **2 to 4 tags** | Attached to physical product boxes to serve as the digital identity token of each product. |
| **4** | **0.96" I2C OLED Display** | SSD1306 128x64 I2C Display (3.3V) | **1 unit** | Hardware visual indicator: displays active Checkpoint (1–4), Scanned Tag UID, and `TAMPERED` status. |
| **5** | **Push Button Switch** | Tactile Breadboard Push Button | **1 unit** | Connected to GPIO 12. Pressing cycles the active checkpoint on the single ESP32 (C01 $\rightarrow$ C02 $\rightarrow$ C03 $\rightarrow$ C04). |
| **6** | **USB Data Cable** | Micro-USB or USB-C (data-capable) | **1 cable** | Connects ESP32 to your laptop for power and real-time USB Serial streaming (115200 baud). |

*(Note: Physical LEDs are not used on the hardware breadboard; all decision scores [0-100] and ALLOW / FLAG / QUARANTINE status badges are displayed dynamically in the software dashboard).*

---

### 2. Physical Package & "Smart Label" Materials

| # | Item | What to Use | Purpose |
|---|---|---|---|
| **7** | **Sample Product Box** | A small cardboard box, jewelry gift box, or medicine box | Acts as the real physical product cargo moving through the supply chain. |
| **8** | **Conductive Tamper Wire / Seal** | Thin copper foil tape with conductive adhesive or thin jumper wire | Taped across the opening lid of the box. Connected to ESP32 **GPIO 15** and **GND**.<br>• **Box Closed:** Circuit is intact (`SAFE`).<br>• **Box Opened / Cut:** Circuit breaks (`TAMPER DETECTED`). |
| **9** | **Adhesive Tape / Seal Sticker** | Normal clear tape or tamper-evident sticker | Secures the RFID tag and conductive wire across the box opening. |

---

### 3. Prototyping & Connectivity Accessories

| # | Item | Specification | Quantity |
|---|---|---|---|
| **10** | **Solderless Breadboard** | 400 or 830 tie-point breadboard | **1 board** |
| **11** | **Jumper Wires** | Male-to-Female and Male-to-Male jumpers | **~15 wires** |
| **12** | **Laptop** | Windows / Mac / Linux laptop | Runs the Python FastAPI Backend Server, Database, and Web Dashboard. |
| **13** | **Python USB Serial Bridge** | [`serial_bridge.py`](file:///c:/Users/duddu/Downloads/tarpproj/serial_bridge.py) | Reads USB Serial at 115200 baud and streams JSON to backend. |

---

# 🔌 Quick Assembly & Wiring Checklist

```
                            +--------------------+
                            |    ESP32 DevKit    |
                            |                    |
    [ MFRC522 RFID ]        |                    |
    VCC   ----------------> | 3.3V  (NOT 5V!)    |
    RST   ----------------> | GPIO 22            |
    GND   ----------------> | GND                |       +---------------------------+
    MISO  ----------------> | GPIO 19            |       | SSD1306 OLED (I2C)        |
    MOSI  ----------------> | GPIO 23            | ----> | SDA  --> GPIO 16          |
    SCK   ----------------> | GPIO 18            | ----> | SCL  --> GPIO 17          |
    SDA   ----------------> | GPIO 5             |       | VCC/GND --> 3.3V / GND    |
                            |                    |       +---------------------------+
    [ PACKAGE TAMPER WIRE ] |                    |
    Lead A ---------------> | GPIO 15            | (Internal Pullup/Pulldown)
    Lead B ---------------> | GND / 3.3V         |
                            |                    |
    [ ADVANCE BUTTON ]      |                    |
    Pin ------------------> | GPIO 12            | (Press to cycle Checkpoints 1-4)
                            |                    |
    [ USB SERIAL CABLE ]    |                    |
    To Laptop ------------> | USB (115200 baud)  | ====> USB Serial Python Bridge (serial_bridge.py)
                            +--------------------+
```

---

# 🎬 How to Perform the Live Demo for Faculty

1. **Step 1: Start Backend & Dashboard on Laptop**
   * Run `python run_system.py` in your terminal.
   * Dashboard opens automatically at `http://localhost:8000/dashboard`.

2. **Step 2: Connect ESP32 Hardware via USB Serial**
   * Plug ESP32 into laptop USB.
   * In a second terminal, run `python serial_bridge.py`. It will detect the COM port at 115200 baud.
   * OLED display illuminates showing `Checkpoint 1`.

3. **Step 3: Demo 1 — Normal Genuine Product Scan**
   * Place the sealed product box (conductive wire intact) near the RC522 reader.
   * **Result:** Dashboard displays **`ALLOW (Score: 100/100)`** with a Green badge, pleasant chime sounds, OLED shows scanned UID, and the product moves along the route visualizer.

4. **Step 4: Demo 2 — Package Tampering Attack (Faculty Wow Factor)**
   * Simulate theft/tampering by **cutting the thin wire or opening the box lid**.
   * OLED immediately flashes **`TAMPERED`**.
   * Tap the RFID tag on the reader again.
   * **Result:** Dashboard flashes **`QUARANTINE (Score: 20/100) — PACKAGE TAMPERED`** with a Red status indicator, and cargo is blocked.

5. **Step 5: Demo 3 — Silent Duress Coercion Attack**
   * Press `D` in the `serial_bridge.py` terminal (or enter PIN `9999` in the console).
   * Tap the RFID tag.
   * **Result:** The screen deceptively shows **`ALLOW (VERIFIED)`** so the attacker is not alerted, but central security simultaneously receives a **high-priority Red Duress Emergency Alert**.