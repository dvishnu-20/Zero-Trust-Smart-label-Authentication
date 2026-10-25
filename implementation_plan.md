# Implementation Plan: Zero Trust Authentication System for Smart Labels in Secure Supply Chains

Build a comprehensive software ecosystem for **Zero Trust RFID Smart Label Supply Chain Security**. The system combines physical tamper detection, RFID identity verification, continuous contextual checks (route, location, speed/time, duplicate usage), employee authentication with silent duress handling, a weighted Trust Scoring Engine, a RESTful API backend, a virtual ESP32 hardware simulator, an ESP32 firmware sketch, and a modern Web Dashboard.

---

## Technical Architecture & Overview

```
[ Physical Product ] ---> [ ESP32 Hardware / Virtual Simulator ]
  - RFID Tag (UID)          - RC522 Reader / Virtual RFID
  - Conductive Tamper Loop  - Tamper GPIO Pin Input
                            - Employee Keypad / PIN
                            - Status LEDs & Buzzer
                                        |
                                   (HTTP POST JSON)
                                        v
                            [ FastAPI Backend Server ]
                                        |
                    +-------------------+-------------------+
                    |                   |                   |
            [ SQLite Database ] [ Zero-Trust Security ] [ Web Dashboard & ]
            - Products          - 8 Multi-Factor Checks  - Live Checkpoint Scan
            - Checkpoints       - Trust Score (0-100)    - Chain Visualizer
            - Scans History     - Attack Classifier      - Incident Alerts Feed
            - Employee/Duress   - Decision Engine        - Attack Demo Suite
```

---

## Proposed Software Architecture & Components

### 1. Database Layer (`backend/database.py`, `backend/models.py`)
Database schema (SQLite via SQLAlchemy):
* **`Product`**: `product_id` (PK, e.g. "P1001"), `product_name`, `rfid_uid` (e.g. "A1B2C3D4"), `manufacturer`, `status` ("ALLOW", "FLAG", "QUARANTINE"), `current_checkpoint_id`, `expected_next_checkpoint_id`.
* **`Checkpoint`**: `checkpoint_id` (PK, e.g. "C01"), `checkpoint_name` ("Manufacturer"), `location`, `sequence_order` (1..N), `min_travel_seconds`, `max_travel_seconds`.
* **`Employee`**: `employee_id` (PK, e.g. "E101"), `name`, `normal_pin` ("1234"), `duress_pin` ("9999"), `assigned_checkpoint_id`.
* **`ScanHistory`**: `scan_id` (PK), `product_id`, `rfid_uid`, `checkpoint_id`, `timestamp`, `tamper_detected` (bool), `employee_id`, `is_duress` (bool), `trust_score` (int 0-100), `decision` ("ALLOW", "FLAG", "QUARANTINE"), `violation_details` (JSON/string).
* **`Alert`**: `alert_id` (PK), `scan_id`, `alert_type` ("RFID_CLONE", "TAMPER_DETECTED", "ROUTE_VIOLATION", "IMPOSSIBLE_TRAVEL_SPEED", "SILENT_DURESS", "UNAUTHORIZED_RFID"), `severity` ("HIGH", "CRITICAL", "MEDIUM"), `timestamp`, `acknowledged` (bool).

---

### 2. Multi-Factor Zero-Trust Verification Engine (`backend/security_engine.py`)
Evaluates 8 security factors for every scan request and generates a score from 0 to 100:

| Check | Factor Evaluated | Weight / Deduction | Attack Detected |
|---|---|---|---|
| **1. RFID Registration** | Is RFID UID registered in system? | Registered: +20, Unregistered: Score set to 0 | Unknown Tag Attack / Counterfeit |
| **2. Product-RFID Association** | Does RFID match assigned product ID? | Match: +10, Mismatch: -50 | RFID Misuse / Label Transfer |
| **3. Tamper Verification** | Conductive loop intact? (`tamper == false`) | Intact: +20, Tampered: Score dropped to <=20 (QUARANTINE) | Package Tampering / Box Opening |
| **4. Route Verification** | Current checkpoint matches `expected_next_checkpoint`? | Correct: +20, Skipped/Wrong Checkpoint: -30 (FLAG) | Route Manipulation |
| **5. Travel Time / Speed** | Time since last scan realistic? | Within range: +15, Unrealistic (< min_time): -25 | Replay Attack / Impossible Speed |
| **6. Duplicate RFID Check** | Same RFID scanned simultaneously at distant locations? | Unique: +10, Duplicate detected: -40 | RFID Cloning Attack |
| **7. Previous Checkpoint Check** | Valid sequence transition from previous scan? | Sequence Valid: +5, Sequence Invalid: -15 | Out-of-order Scan |
| **8. Employee / Duress Check** | Normal PIN vs Duress PIN provided? | Normal PIN: Valid; Duress PIN: Trigger Hidden Alert, Decision masked if configured | Insider Threat / Silent Duress |

**Decision Matrix**:
* **`Score >= 80`** AND `Tamper == False` AND `Not Duress` $\rightarrow$ **`ALLOW`** (Green LED)
* **`50 <= Score < 80`** $\rightarrow$ **`FLAG`** (Yellow LED)
* **`Score < 50`** OR `Tamper == True` $\rightarrow$ **`QUARANTINE`** (Red LED + Alarm)

---

### 3. FastAPI Backend REST Service (`backend/main.py`)
* `POST /api/scan`: Endpoint for ESP32 hardware & virtual simulator. Receives `{ rfid_uid, checkpoint_id, tamper_detected, employee_id, pin }`. Runs Security Engine and returns `{ decision, trust_score, violations, is_duress, display_status }`.
* `POST /api/products/register`: Product registration API.
* `GET /api/products`: List all registered products with current location and status.
* `GET /api/products/{product_id}/track`: Retrieve full movement history & route completion tree.
* `GET /api/scans`: Retrieve logs with filter options.
* `GET /api/alerts`: Real-time active alerts & duress flags.
* `POST /api/demo/trigger-attack`: One-click preset triggers for all 6 demo attack scenarios (Normal, Tamper, Wrong Route, Duplicate RFID, Impossible Time, Silent Duress).
* `POST /api/seed`: Reset database with test checkpoints, products, and employee pins.

---

### 4. Virtual Checkpoint & Attack Simulator UI (`frontend/`)
A sleek, modern glassmorphism web dashboard built with HTML, CSS, JavaScript (or Vite framework):
* **Live Interactive Checkpoint Simulator**:
  * Simulated RFID Card swiper / Dropdown selector (`A1B2C3D4` - Product P1001).
  * Checkpoint selector (`C01 - Manufacturer`, `C02 - Warehouse`, `C03 - Distributor`, `C04 - Retailer`).
  * Interactive "Cut Package Seal" toggle switch for hardware tamper loop breaking.
  * PIN keypad entry with Normal (`1234`) and Duress (`9999`) inputs.
  * Live physical LED indicator simulation (Green / Yellow / Red) and audio beeps.
* **Supply Chain Route Visualizer**:
  * Node map showing product progress along Manufacturer $\rightarrow$ Warehouse $\rightarrow$ Distributor $\rightarrow$ Retailer.
  * Status badges for each node (Checked, Flagged, Bypassed).
* **Real-time Alert Center**:
  * Instant popup alert system when attacks are detected.
  * Special Silent Duress warning banner (visible only to security admins).
* **Interactive Attack Demo Test Suite**:
  * Pre-configured buttons to run Demos 1 through 6 with 1-click verification.

---

### 5. ESP32 Arduino Firmware (`firmware/esp32_checkpoint.ino`)
* Complete Arduino C++ sketch supporting ESP32 + RC522 RFID SPI module + Conductive Tamper Loop pin + 3 LEDs + Buzzer + Keypad/Serial PIN input + WiFi client POST request to Backend API.
* Fallback mock hardware mode for development/testing without physical sensors wired up.
* Detailed README documentation with wiring tables, schematics, pin mappings, and build instructions.

---

## User Review Required

> [!IMPORTANT]
> **Key Architecture Decisions for Software First Implementation**:
> 1. We will implement both the **Physical ESP32 C++ Code** AND a **Virtual Hardware Web Simulator**. This ensures you can fully demonstrate and test all 6 security attack scenarios directly from your laptop during presentation/faculty review without requiring physical hardware connected at all times.
> 2. The database will be SQLite (stored locally as `zero_trust_supply_chain.db`), which requires zero setup and persists all product journeys, attack histories, and audit logs.

---

## Proposed Implementation Plan Files

#### [NEW] [backend/main.py](file:///c:/Users/duddu/Downloads/tarpproj/backend/main.py)
FastAPI application with REST API endpoints for scans, product registration, alerts, tracking, and demo triggers.

#### [NEW] [backend/database.py](file:///c:/Users/duddu/Downloads/tarpproj/backend/database.py)
Database connection setup and SQLAlchemy sessions.

#### [NEW] [backend/models.py](file:///c:/Users/duddu/Downloads/tarpproj/backend/models.py)
SQLAlchemy models for Product, Checkpoint, Employee, ScanHistory, and Alert.

#### [NEW] [backend/security_engine.py](file:///c:/Users/duddu/Downloads/tarpproj/backend/security_engine.py)
Multi-factor Zero-Trust evaluation engine, trust score calculator, route validation logic, duplicate RFID detection, travel time validation, and silent duress handler.

#### [NEW] [backend/seed.py](file:///c:/Users/duddu/Downloads/tarpproj/backend/seed.py)
Data seeder script creating sample checkpoints (Manufacturer, Warehouse, Distributor, Retailer), sample products (P1001-P1005 with RFID UIDs), and sample employees (with normal & duress PINs).

#### [NEW] [firmware/esp32_checkpoint.ino](file:///c:/Users/duddu/Downloads/tarpproj/firmware/esp32_checkpoint.ino)
Complete ESP32 C++ code for physical hardware deployment (RC522 reader, WiFi HTTP POST client, LEDs, buzzer, tamper pin).

#### [NEW] [firmware/README.md](file:///c:/Users/duddu/Downloads/tarpproj/firmware/README.md)
Pinout specification, circuit schematic diagram instructions, and hardware setup documentation.

#### [NEW] [frontend/index.html](file:///c:/Users/duddu/Downloads/tarpproj/frontend/index.html)
Main Web Dashboard layout with live simulator, product route tracking, real-time alert feed, and attack test bench.

#### [NEW] [frontend/style.css](file:///c:/Users/duddu/Downloads/tarpproj/frontend/style.css)
Modern glassmorphism theme, vibrant status indicators, LED animations, responsive flex/grid layouts.

#### [NEW] [frontend/app.js](file:///c:/Users/duddu/Downloads/tarpproj/frontend/app.js)
Frontend JavaScript controller for API integration, real-time polling/websockets for alerts, interactive simulation controls, and attack scenario demo triggers.

#### [NEW] [run_system.py](file:///c:/Users/duddu/Downloads/tarpproj/run_system.py)
Single-command launcher script that installs requirements, initializes the database with demo data, and starts the web server.

---

## Verification Plan

### Automated & Backend Tests
- Create Python unit test script `tests/test_security_engine.py` to verify:
  1. Valid RFID + normal route $\rightarrow$ `ALLOW` (Score >= 80)
  2. Unknown RFID UID $\rightarrow$ `QUARANTINE` (Score = 0)
  3. Tamper loop broken (`tamper=True`) $\rightarrow$ `QUARANTINE` (Score <= 20)
  4. Out of sequence checkpoint $\rightarrow$ `FLAG` (Route violation)
  5. Duplicate scan in rapid succession $\rightarrow$ `FLAG` (Cloning / Replay alert)
  6. Duress PIN (`9999`) $\rightarrow$ Visible status "ALLOW", Internal Flag `is_duress=True` & Silent Alert generated.

### Manual Verification Scenarios (Faculty Presentation Demos)
- Launch backend & open dashboard at `http://localhost:8000`.
- **Demo 1 (Normal Product)**: Scan `P1001` (`A1B2C3D4`) sequentially from Checkpoint 1 through 4 $\rightarrow$ Observe `ALLOW` decision & Green LED.
- **Demo 2 (Package Tampering)**: Toggle "Tamper Loop Cut" on Checkpoint 2 $\rightarrow$ Observe `QUARANTINE` decision & Red LED + Tamper Alert.
- **Demo 3 (Route Manipulation)**: Attempt to scan `P1002` at Checkpoint 3 skipping Checkpoint 2 $\rightarrow$ Observe `FLAG` decision & Route Violation alert.
- **Demo 4 (RFID Cloning)**: Scan same RFID `A1B2C3D4` at Checkpoint 4 while registered location is Checkpoint 1 $\rightarrow$ Observe `FLAG` decision & Duplicate RFID Alert.
- **Demo 5 (Impossible Travel Speed)**: Perform two consecutive scans at distant checkpoints within 1 second $\rightarrow$ Observe `FLAG` decision & Impossible Speed Alert.
- **Demo 6 (Silent Duress)**: Perform scan using Duress PIN `9999` $\rightarrow$ Screen displays deceptive "VERIFIED", while Admin Security Console displays high-priority red **SILENT DURESS ALERT**.
