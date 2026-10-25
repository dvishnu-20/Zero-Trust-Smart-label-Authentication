# ZERO TRUST AUTHENTICATION FOR SMART LABELS IN SECURE SUPPLY CHAINS

---

## 📌 Project Overview & Metadata

* **Project Title:** Zero Trust Authentication for Smart Labels in Secure Supply Chains
* **Domain:** Cyber-Physical Security, IoT Supply Chain Assurance, Zero-Trust Architecture
* **Core Principle:** *"Never Trust, Always Verify: A valid RFID tag alone does not guarantee product authenticity or package integrity."*
* **Core Output Decisions:** `ALLOW` (Green) | `FLAG` (Yellow) | `QUARANTINE` (Red)

---

## ✨ Core Features of the Project & Technical Capabilities

### 1. Continuous Multi-Factor Zero-Trust Verification Engine
* **No Implicit Trust:** Eliminates static RFID trust. Every product package is re-evaluated dynamically at each supply chain node.
* **Dynamic Trust Score ($0 - 100$):** Combines 8 distinct cyber-physical vectors into a weighted mathematical decision model mapping to `ALLOW` ($\ge 80$), `FLAG` ($50-79$), or `QUARANTINE` ($< 50$).

### 2. Physical Package Tamper Seal Sensing (< 50μs Latency)
* **Conductive Seal Circuit:** A thin conductive trace is bonded across the box opening seal, wired to ESP32 GPIO 4 (`INPUT_PULLUP`).
* **Instant Quarantine Trigger:** If the box is sliced or opened in transit, the ground loop is broken ($0\text{V} \rightarrow 3.3\text{V}$), immediately dropping the Trust Score to $\le 20$, setting the software status to QUARANTINE, and displaying TAMPERED on the OLED.

### 3. Dynamic Supply Chain Route Topology Enforcement
* **Sequential Checkpoint Progression:** Enforces authorized flow: `Manufacturer (C01)` $\rightarrow$ `Central Warehouse (C02)` $\rightarrow$ `Regional Distributor (C03)` $\rightarrow$ `Retail Store (C04)`.
* **Anomaly Detection:** Bypassing intermediate inspection facilities or illegal backwards tracking is automatically identified and flagged.

### 4. Anti-Cloning & Velocity Analytics (Replay Defense)
* **Duplicate Tag Identification:** Flags concurrent scans of the same RFID tag UID across geographically separated nodes.
* **Transit Velocity Checking:** Enforces minimum physical transit time thresholds ($t \ge \text{min\_travel\_seconds}$) to defeat replayed scan tokens and cloned tags.

### 5. Silent Duress Coercion Protection Subsystem
* **Dual-Credential Authentication:** Distinguishes between Standard Employee PIN (`1234`) and Emergency Duress PIN (`9999`).
* **Deceptive UI Masking:** Displays normal "ALLOW (VERIFIED)" on the terminal to protect coerced staff from immediate danger while secretly firing a high-priority critical alert to security headquarters.

### 6. Multi-Node Web Console & Virtual Hardware Emulation
* **Full Virtual Hardware Simulator:** Enables testing and demonstrations without physical hardware (virtual RFID reader, seal cut switch, LED status, and Web Audio API tone synthesis).
* **Dynamic Product Registration:** Seamless registration modal creating new RFID smart labels on-the-fly.
* **Faculty Review Demo Suite:** 1-Click attack triggers for all 6 core supply chain threats.

---

## ⚡ Sample Hardware Working & Signal Flow Architecture

```
[ STAGE 1: PHYSICAL PRODUCT WITH SMART LABEL ]
  ├── Sample Product: P1001 High-Grade Microprocessor Array
  ├── Smart RFID Tag: Contactless UID `A1B2C3D4`
  └── Conductive Tamper Loop: Thin conductive wire taped across the box opening seal
                               │
                               ▼ (Physical Contact / RF Scan)
[ STAGE 2: ESP32 CHECKPOINT HARDWARE RIG ]
  ├── RC522 RFID SPI Reader: Reads Tag UID `A1B2C3D4`
  ├── GPIO 4 Tamper Pin (Pull-Up):
  │     ├── [Normal Sealed State]: Circuit Closed ──► GPIO 4 = LOW (0V Grounded)
  │     └── [Tampered Box State]:  Circuit Broken ──► GPIO 4 = HIGH (3.3V Pull-Up)
  ├── Wi-Fi Client: Transmits JSON scan payload over HTTP POST to Backend API
  └── Output Actuators: 3 Feedback LEDs (GPIO 26, 25, 33) + Piezo Buzzer (GPIO 27)
                               │
                               ▼ (HTTP REST JSON)
[ STAGE 3: BACKEND ZERO-TRUST DECISION ENGINE ]
  ├── Identity Verification: RFID UID registered in system database (Unregistered = drops to 0)
  ├── Package Condition: Tamper status verified (Intact = 0 penalty / Broken = -80 pts penalty)
  ├── Contextual Checks: Route sequence (-35 pts), velocity (-30 pts), duplicate clone (-40 pts), employee PIN (-15 pts)
  └── Actuation Signal Returned:
        ├── [Normal]: Trust Score 100/100 ──► ALLOW ──► Green LED ON (Access Granted)
        └── [Tampered]: Trust Score 20/100 ──► QUARANTINE ──► Red LED ON + Double Alarm Buzzer
```

---

## 🧮 Mathematical Trust Scoring Formula & Decision Matrix

Each checkpoint scan computes a dynamic **Trust Score ($T$)** bounded on the closed interval $[0, 100]$, initialized at a baseline score of $100$ and applying deductive contextual penalties:

$$T = \max\left(0, \min\left(100, 100 - \sum P_j\right)\right)$$

*(Note: If the RFID UID is not registered in the system, the score immediately drops to $T = 0$.)*

Expanded multi-factor penalty deduction model:

$$T = 100 - P_{\text{Seal}} - P_{\text{Route}} - P_{\text{Speed}} - P_{\text{Clone}} - P_{\text{PIN}} - P_{\text{History}}$$

| Verification Check | Verification Criterion | Nominal State | Violation Penalty ($P_j$) | Resulting Score & Decision |
|---|---|---|---|---|
| **1. RFID Registration** | Registered in SQLite Database | Valid UID | Dropped to $0$ (`UNREGISTERED_RFID`) | $0 \longrightarrow$ **`QUARANTINE`** |
| **2. Physical Tamper Seal** | Conductive loop closed (`GPIO 4 LOW`) | Intact Seal | $-80$ (`PACKAGE_TAMPERED`) | $20 \longrightarrow$ **`QUARANTINE`** |
| **3. Sequential Route** | Arrived at expected next checkpoint | In-Sequence | $-35$ (Skipped Node) / $-25$ (Backtrack) | $65 \longrightarrow$ **`FLAG`** |
| **4. Travel Velocity** | Transit time $\ge \text{min\_travel\_seconds}$ | Valid Velocity | $-30$ (`IMPOSSIBLE_TRAVEL_SPEED`) | $70 \longrightarrow$ **`FLAG`** |
| **5. Duplicate Clone Check** | No concurrent scans at distant nodes ($< 10\text{s}$) | Unique UID | $-40$ (`DUPLICATE_RFID_CLONE`) | $60 \longrightarrow$ **`FLAG`** |
| **6. Employee Authentication** | Standard PIN entered (`1234`) | Valid Auth | $-15$ (Invalid PIN) / $-10$ (Unknown Staff) | $85 \longrightarrow$ **`ALLOW`** |

### Decision Thresholds
* **`Score >= 80` AND Seal Intact** $\longrightarrow$ **`ALLOW`** (Green LED, buzzer single beep, access granted).
* **`50 <= Score < 80`** $\longrightarrow$ **`FLAG`** (Yellow LED, warning tone, held for secondary security inspection).
* **`Score < 50` OR Seal Broken** $\longrightarrow$ **`QUARANTINE`** (Red LED + double alarm buzzer, cargo blocked).
* **Duress PIN (`9999`) Entered** $\longrightarrow$ Screen displays deceptive **`ALLOW (VERIFIED)`** while silently transmitting a **`CRITICAL SILENT DURESS ALARM`** to security personnel.

---

## ⚖️ Technical Comparison: Why Zero Trust RFID?

| Security & Operational Factor | Traditional RFID Tracking | Standalone Blockchain | Our Zero Trust Smart Label System |
|---|---|---|---|
| **Physical Package Opening Detection** | Not Protected (Tags read even if opened) | Digital Only (No physical sensing) | **Hardware Seal Rupture Sensor (GPIO 4)** |
| **RFID Tag Cloning Mitigation** | Blindly Trusted (No clone defense) | Limited Defense (Clone can submit tx) | **Concurrent Clone & Speed Analytics** |
| **Sequential Route Verification** | No Verification (Only logs location) | Smart Contract Logic | **Dynamic Topology Enforcement** |
| **Impossible Velocity / Replay Defense** | Not Protected | Not Protected | **Timestamp Delta Bounds** |
| **Insider Coercion / Silent Duress** | Not Supported | Not Supported | **Deceptive UI + Covert Alarm** |
| **Verification Latency & Cost** | Low cost, high vulnerability | High gas fees, slow latency | **Low-cost ESP32 (< 100ms verification)** |

---

## ⚡ Hardware Pinout & Circuit Specifications

| Component | ESP32 GPIO Pin | Function / Wire Details |
|---|---|---|
| **RC522 SDA / SS** | **GPIO 5** | SPI Slave Select |
| **RC522 SCK** | **GPIO 18** | SPI Serial Clock |
| **RC522 MOSI** | **GPIO 23** | SPI Master Out Slave In |
| **RC522 MISO** | **GPIO 19** | SPI Master In Slave Out |
| **RC522 RST** | **GPIO 22** | Module Reset Pin |
| **RC522 Power** | **3.3V & GND** | 3.3V DC Power (Strictly 3.3V) |
| **Tamper Loop In** | **GPIO 4** | Set to `INPUT_PULLUP`. Connected across conductive box seal wire |
| **Tamper Return** | **GND** | Intact seal pulls GPIO 4 LOW (`SAFE`). Broken seal pulls HIGH (`TAMPER`) |
| **Green LED** | **GPIO 26** | `ALLOW` Status Indicator (220Ω resistor) |
| **Yellow LED** | **GPIO 25** | `FLAG` Status Indicator (220Ω resistor) |
| **Red LED** | **GPIO 33** | `QUARANTINE` Status Indicator (220Ω resistor) |
| **Piezo Buzzer** | **GPIO 27** | Audible Alert Tone & Double Alarm |
