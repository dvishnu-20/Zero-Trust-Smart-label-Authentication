# Zero Trust Authentication for Smart Labels in Secure Supply Chains

An end-to-end Cyber-Physical Supply Chain Security prototype implementing continuous multi-factor Zero-Trust verification for RFID smart labels, physical package tamper detection, sequential route topology checking, travel speed validation, duplicate clone detection, and a silent duress coercion protection subsystem.

---

## 📌 1. Project Overview & Core Principle

* **Core Principle:** *"Never Trust, Always Verify: A valid RFID tag alone does not mean the product is trusted. Verify continuously at every checkpoint."*
* **Primary Decisions:**
  * **`ALLOW`** (Green LED, Trust Score $\ge 80$): Genuine item, intact seal, correct sequential route.
  * **`FLAG`** (Yellow LED, Trust Score $50–79$): Contextual anomaly detected (e.g. skipped hub, abnormal velocity). Held for inspection.
  * **`QUARANTINE`** (Red LED + Audio Alarm, Trust Score $< 50$ or Tampered): Physical seal rupture or unregistered tag. Cargo blocked.
  * **`SILENT DURESS`**: Emergency PIN `9999` entered under coercion displays deceptive "ALLOW" on screen while silently dispatching a high-priority alarm to security headquarters.

---

## 🛠️ 2. Requirements & Technology Stack

### Software Requirements
* **Language & Backend:** Python 3.10+ with [FastAPI](https://fastapi.tiangolo.com/) and [Uvicorn](https://www.uvicorn.org/) (Async RESTful API architecture)
* **Database & ORM:** SQLite with [SQLAlchemy](https://www.sqlalchemy.org/) (Persistent storage for products, checkpoints, scan audit logs, and security alerts)
* **Validation:** [Pydantic](https://docs.pydantic.dev/) for payload schema validation
* **Frontend Web Dashboard:** Vanilla HTML5, Modern CSS3 (Glassmorphism Dark Theme), Vanilla JavaScript, and Web Audio API (for hardware beep tone synthesis)
* **Testing:** Python `unittest` framework

### Microcontroller Firmware Requirements
* **IDE:** Arduino IDE (v2.0+) with ESP32 Board Support package
* **Libraries:**
  * `MFRC522` by GitHubCommunity (SPI RFID communication)
  * `ArduinoJson` by Benoit Blanchon (JSON serialization over HTTP)
  * `WiFi` & `HTTPClient` (Native ESP32 networking libraries)

---

## 🔌 3. Hardware Requirements & Components List

| Component | Quantity | Purpose / Function |
|---|---|---|
| **ESP32 DevKit V1** (30-pin/38-pin) | 1 (or 1 per checkpoint) | Main IoT microcontroller running custom C++ firmware |
| **MFRC522 RFID Reader** | 1 | 13.56 MHz High-Frequency contactless RFID SPI reader |
| **RFID Tags / Smart Cards (UIDs)** | 2–5 | Contactless digital identity tokens attached to packages |
| **Conductive Wire / Copper Tape** | 1 roll | Physical tamper detection seal looped across package box lids |
| **Status LEDs** (Green, Yellow, Red) | 3 | Physical visual verification feedback indicators |
| **220Ω Resistors** | 3 | Current limiting resistors for LEDs |
| **Piezo Buzzer (5V / 3.3V)** | 1 | Audible alert tone & double alarm generator |
| **Solderless Breadboard & Jumpers** | 1 set | Prototyping rig wiring |
| **Micro-USB Cable & Laptop** | 1 | Power supply, serial debugging, and backend server hosting |
| **Sample Package Boxes** | 1–3 | Physical demo boxes representing supply chain cargo |

---

## ⚡ 4. Hardware Pinout & Wiring Connections

### A. RC522 RFID SPI Module to ESP32
| MFRC522 Pin | ESP32 GPIO Pin | Wire Function |
|---|---|---|
| **VCC** | **3.3V** | 3.3V Power (⚠️ Do NOT connect to 5V!) |
| **RST** | **GPIO 22** | Module Reset Pin |
| **GND** | **GND** | Common Ground |
| **MISO** | **GPIO 19** | SPI Master In Slave Out |
| **MOSI** | **GPIO 23** | SPI Master Out Slave In |
| **SCK** | **GPIO 18** | SPI Serial Clock |
| **SDA / SS** | **GPIO 5** | SPI Slave Select |

### B. Conductive Package Tamper Loop Pin Connection
| Physical Wire | ESP32 Connection | Description |
|---|---|---|
| **Tamper In** | **GPIO 4** | Configured as `INPUT_PULLUP` |
| **Tamper Return** | **GND** | Loop intact = `0V LOW` (**SAFE**); Loop broken = `3.3V HIGH` (**TAMPERED**) |

### C. Actuators (Status LEDs & Buzzer)
| Actuator Component | ESP32 GPIO Pin | Function |
|---|---|---|
| **Green LED (+)** | **GPIO 26** | `ALLOW` Status (via 220Ω resistor) |
| **Yellow LED (+)** | **GPIO 25** | `FLAG` Status (via 220Ω resistor) |
| **Red LED (+)** | **GPIO 33** | `QUARANTINE` Status (via 220Ω resistor) |
| **Piezo Buzzer (+)** | **GPIO 27** | Audible Tone & Alarm (PWM Tone) |
| **Common Return (-)** | **GND** | Shared ground rail |

---

## 🏗️ 5. Completed Implementation Details

```
tarpproj/
├── backend/
│   ├── __init__.py
│   ├── database.py         # SQLite engine & SQLAlchemy session generator
│   ├── models.py           # DB models: Product, Checkpoint, Employee, ScanHistory, Alert
│   ├── security_engine.py  # 8 Zero-Trust verification checks & scoring algorithm
│   ├── seed.py             # Default data seeder (checkpoints, products, employees)
│   └── main.py             # FastAPI REST application & static file routes
├── firmware/
│   ├── esp32_checkpoint.ino # Complete ESP32 Arduino C++ firmware sketch
│   └── README.md           # Circuit schematics & hardware flashing guide
├── frontend/
│   ├── cover.html          # Interactive executive cover page & architecture visualizer
│   ├── index.html          # Operational security console & virtual simulator
│   ├── style.css           # Modern dark-mode glassmorphism stylesheet & animations
│   └── app.js              # Frontend JS controller with audio tone synthesis & API calls
├── tests/
│   └── test_security_engine.py # Automated unit tests for all 6 attack vectors
├── run_system.py           # Single-command launcher script
├── PROJECT_COVER_PAGE.md   # Executive presentation summary document
└── README.md               # Complete project documentation & setup guide
```

### Key Modules Implemented
1. **Multi-Factor Zero-Trust Security Engine ([`backend/security_engine.py`](file:///c:/Users/duddu/Downloads/tarpproj/backend/security_engine.py))**:
   - Evaluates **8 checks**: RFID Registration, Product-RFID Binding, Tamper Seal Integrity, Sequential Route Topology, Velocity Bounds, Concurrent Duplicate Clone Defense, Previous Scan Consistency, and Employee Auth with Silent Duress handling.
2. **Virtual Hardware Scanner Simulator ([`frontend/index.html`](file:///c:/Users/duddu/Downloads/tarpproj/frontend/index.html))**:
   - Allows full demonstration of the system without physical hardware attached. Includes RFID swiper, package seal cut toggle, employee PIN keypad, glowing LED lights, and Web Audio API tone synthesis.
3. **Dynamic Product Registration Modal**:
   - Register any new smart label product on-the-fly with 1-click random RFID UID generation.
4. **1-Click Faculty Demo Suite**:
   - Interactive demo triggers for all 6 presentation attack scenarios.
5. **Interactive Executive Cover Page ([`frontend/cover.html`](file:///c:/Users/duddu/Downloads/tarpproj/frontend/cover.html))**:
   - Real-time Trust Score simulator sandbox, interactive 3-stage hardware signal flow visualizer, clean comparative analysis matrix, and animated feature cards.

---

## 🚀 6. Step-by-Step Run Commands

### Step 1: Install Python Dependencies
Open your terminal in the project root directory and run:
```powershell
pip install fastapi uvicorn sqlalchemy pydantic
```

---

### Step 2: Launch Full System (Single Command)
Run the automated launcher:
```powershell
python run_system.py
```
This single command will:
1. Initialize the SQLite database and seed test data.
2. Start the FastAPI server on `http://127.0.0.1:8000`.
3. Automatically open your browser to the **Project Cover Page** at `http://localhost:8000/`.

---

### Step 3: Accessing Pages
* **Interactive Project Cover Page:** `http://localhost:8000/`
* **Operational Security Console & Simulator:** `http://localhost:8000/dashboard`
* **Interactive Swagger API Documentation:** `http://localhost:8000/docs`

---

### Step 4: Run Automated Security Engine Unit Tests
To verify all 6 attack detection scenarios automatically:
```powershell
python -m unittest tests/test_security_engine.py
```
*Expected output:* `Ran 5 tests in 0.271s OK`.

---

### Step 5: Flashing Physical ESP32 Hardware (Optional)
1. Connect ESP32 to laptop via USB cable.
2. Open [`firmware/esp32_checkpoint.ino`](file:///c:/Users/duddu/Downloads/tarpproj/firmware/esp32_checkpoint.ino) in Arduino IDE.
3. Update `WIFI_SSID`, `WIFI_PASSWORD`, and `BACKEND_SCAN_URL` (e.g. `http://<YOUR_LAPTOP_IP>:8000/api/scan`).
4. Install libraries `MFRC522` and `ArduinoJson` in Arduino Library Manager.
5. Select Board **ESP32 Dev Module**, choose COM port, and click **Upload**.

---

## 🧪 7. Faculty Review Demonstration Guide

| Demo Scenario | How to Trigger on Dashboard | Expected System Decision | Hardware Actuation |
|---|---|---|---|
| **Demo 1: Normal Product** | Click `Demo 1` button (P1001 scanned at C01, seal intact) | **`ALLOW`** (Trust Score: 100) | Green LED ON |
| **Demo 2: Package Tampering** | Click `Demo 2` button or toggle "Tamper Loop Cut" switch | **`QUARANTINE`** (Trust Score: 20) | Red LED ON + Double Alarm Buzzer |
| **Demo 3: Route Violation** | Click `Demo 3` button (P1002 skips to C04 directly) | **`FLAG`** (Trust Score: 65) | Yellow LED ON + Warning Tone |
| **Demo 4: RFID Cloning** | Click `Demo 4` button (Tag 99887766 scanned concurrently at C01 & C04) | **`FLAG`** (Trust Score: 60) | Yellow LED ON + Clone Alert |
| **Demo 5: Suspicious Speed** | Click `Demo 5` button (Scanned at distant nodes in < 1s) | **`FLAG`** (Trust Score: 70) | Yellow LED ON + Velocity Alert |
| **Demo 6: Silent Duress** | Enter PIN `9999` in simulator keypad or click `Demo 6` | **`ALLOW (VERIFIED)`** (Screen masked) | Red Alert sent to Central Security Feed |
