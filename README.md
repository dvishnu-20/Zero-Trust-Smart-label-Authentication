# Zero-Trust Authentication for Smart Labels in Secure Supply Chains

An end-to-end Cyber-Physical Supply Chain Security prototype implementing continuous multi-factor Zero-Trust verification for RFID smart labels. The system validates physical package tamper seals, sequential route topologies, travel velocities, duplicate RFID cloning, and operator credentials with a deceptive silent duress mechanism.

The edge hardware (ESP32) communicates directly with the FastAPI backend over a high-speed **USB-Serial Bridge** at 115200 baud, providing low-latency, tamper-resistant telemetry without local Wi-Fi dependencies. All operational decisions, scores ($0–100$), violations, and visual telemetry are reflected across the **Software Dashboard, Administrative Console, and On-board OLED Display**.

---

## 📌 Core Zero-Trust Architecture & Verification Principles

The system adheres strictly to the Zero-Trust axiom: ***"Never Trust, Always Verify"***. An enrolled RFID tag alone is never sufficient for transit authorization. Every scan undergoes 8 multi-factor verification checks:

1. **RFID Database Enrollment Check**: Validates whether the RFID tag UID is officially registered in the supply chain database. Unregistered tags are quarantined (with controlled auto-enrollment permitted only at Manufacturer Node `C01`).
2. **Physical Conductive Tamper Seal Check**: Senses whether the physical breakaway conductive circuit over the package seal is closed (3.3V intact) or broken/opened (GND pull-down). Tampering incurs an immediate $-80$ score deduction and categorical quarantine.
3. **Employee Identity & Silent Duress Authentication**: Validates operator credentials. If an operator is coerced and inputs emergency Duress PIN `9999`, the interface deceptively presents `ALLOW (VERIFIED)` to avoid alerting the aggressor while secretly dispatching a critical alarm to central security feeds.
4. **Sequential Route Topology Check & Station Dwell Policy**: Enforces valid topological state transitions ($C01 \rightarrow C02 \rightarrow C03 \rightarrow C04$). Forward skipping penalizes $-35$ points, and backtracking from downstream stations penalizes $-25$ points. Authorized re-reads at the same physical station ($\text{checkpoint\_id} = \text{current\_checkpoint\_id}$) are recognized as handling dwell scans, maintaining a clean score of 100.
5. **Travel Velocity & Spatial-Temporal Bounds**: Computes transit time $\Delta t$ from the previous checkpoint. If travel time violates minimum physical transit limits, an `IMPOSSIBLE_TRAVEL_SPEED` violation is logged ($-30$ points).
6. **Concurrent Duplicate RFID Clone Detection**: Detects whether the same tag UID was scanned at a different checkpoint within a 10-second sliding window, instantly flagging concurrent RF cloning attacks ($-40$ points).
7. **Scan History Location Consistency**: Confirms that the tag's recorded location matches its immediate prior database scan history.
8. **Persistent Quarantine Lock**: Once quarantined, a package is permanently locked from transit (`trust_score = 0`). Subsequent rescans cannot clear the quarantine status, and route progression is frozen.

### Decision Matrix
* **`ALLOW`** ($\text{Trust Score} \ge 80$): Genuine item, intact seal, verified sequential transit.
* **`FLAG`** ($50 \le \text{Trust Score} < 80$): Anomaly detected (e.g. forward skip, abnormal velocity). Diverted to secondary manual audit.
* **`QUARANTINE`** ($\text{Trust Score} < 50$ or Tamper Detected): Physical seal broken, cloned tag, or unregistered item. Cargo transit is halted.

---

## 🏗️ Repository Architecture

```
tarpproj/
├── backend/
│   ├── database.py             # SQLite engine & SQLAlchemy session generator
│   ├── models.py               # ORM schemas: Product, Checkpoint, Employee, ScanHistory, Alert
│   ├── security_engine.py      # 8 Zero-Trust multi-factor verification checks & scoring engine
│   ├── seed.py                 # Automated database initialization & default data seeder
│   └── main.py                 # FastAPI REST API application & static asset routes
├── firmware/
│   ├── esp32_checkpoint.ino    # ESP32 firmware (SPI RFID + I2C OLED + Tamper Pin + USB Serial)
│   └── README.md               # Hardware flashing guide and schematics
├── frontend/
│   ├── index.html              # Operational security console & virtual simulator
│   ├── admin_stats.html        # Multi-node administrative statistics dashboard
│   ├── cover.html              # Executive architecture & interactive cover visualizer
│   ├── app.js                  # Frontend client controller & tone synthesizer
│   └── style.css               # Modern dark-mode glassmorphism interface styling
├── eval_icoet/                 # ICOET 2027 Experimental Reproducibility Suite
│   ├── README_START_HERE.md    # Complete protocol and execution instructions
│   ├── run_original_120.py     # Author-supplied 120-trial runner wrapper
│   ├── run_trials_original.py  # 6-scenario x 20-trial decision benchmark
│   ├── analyze_original_trials.py # Statistical Wilson 95% CI & latency auditor
│   ├── compare_baselines.py    # Paired baseline comparison (Zero-Trust vs UID-Only)
│   ├── security_probes.py      # 8 adversarial defensive negative probes
│   ├── policy_sweep.py         # 36-variant analytical threshold sensitivity sweep
│   ├── repeat_scan_benchmark.py # Station dwell vs fresh registered tag benchmark
│   ├── instrumented_serial_bridge.py # Microsecond-accurate serial-to-HTTP test bridge
│   ├── evidence_snapshot.py    # Provenance manifest generator with SHA-256 digests
│   └── hardware_observation_template.csv # Observation recording template
├── results/                    # Frozen experimental datasets, CSVs, and audit manifests
│   ├── evidence_manifest.json  # Cryptographic SHA-256 ledger of all evidence files
│   ├── original_120_trials.csv # 120 target trial results
│   ├── trial_summary_audited.json # Statistical latency and Wilson intervals
│   ├── hardware/               # Physical ESP32 benchmark logs (connected, tampered, dwell)
│   ├── icoet_baseline/         # Paired baseline comparison data
│   ├── icoet_probes/           # Adversarial probe results
│   └── icoet_policy_sweep/     # Sensitivity sweep matrices
├── tests/
│   ├── test_security_engine.py # Automated unit test suite
│   └── execute_test_trials.py  # Automated 70-trial pipeline reliability runner
├── optional_quarantine_hold_regression.py # Standalone quarantine persistence regression probe
├── serial_bridge.py            # Production USB-Serial-to-HTTP bridge (115200 baud)
├── run_system.py               # Single-command launcher script
├── README.md                   # System documentation & setup guide
└── .gitignore                  # Git exclusion rules
```

---

## ⚡ Hardware Pinout & Wiring Connections

| Component | Module Pin | ESP32 GPIO | Description / Operating Parameter |
|---|---|---|---|
| **MFRC522 RFID** | VCC | **3.3V** | Operating voltage (⚠️ 3.3V only, do NOT use 5V) |
| | GND | **GND** | Ground reference |
| | RST | **GPIO 22** | Module reset line |
| | MISO | **GPIO 19** | SPI Master-In Slave-Out |
| | MOSI | **GPIO 23** | SPI Master-Out Slave-In |
| | SCK | **GPIO 18** | SPI Serial Clock |
| | SDA (SS) | **GPIO 5** | SPI Chip / Slave Select |
| **SSD1306 OLED** | VCC | **3.3V** | Display logic power |
| | GND | **GND** | Ground reference |
| | SDA | **GPIO 16** | I2C Data line |
| | SCL | **GPIO 17** | I2C Clock line |
| **Tamper Seal** | Lead A | **GPIO 15** | Configured as `INPUT_PULLDOWN`. Connected to 3.3V = Intact (`tamper: 0`). Disconnected = Broken (`tamper: 1`). |
| | Lead B | **3.3V** | Seal loop circuit source |
| **Station Switch** | Pushbutton | **GPIO 12** | Configured as `INPUT_PULLUP`. Pressing increments station ($C01 \rightarrow C02 \rightarrow C03 \rightarrow C04$). |

---

## 🚀 Quickstart & Setup Guide

### 1. Environment Installation
Clone the repository and install the required dependencies:
```powershell
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install required dependencies
pip install fastapi uvicorn sqlalchemy pydantic pyserial requests pytest
```

---

### 2. Database Initialization (Automatic Creation & Seeding)

> [!NOTE]
> **Database files (`*.db` / `*.sqlite`) are intentionally excluded from Git** to avoid merge conflicts and prevent tracking local test states. The SQLite database is created dynamically on-demand.

To initialize a fresh database with standard supply chain checkpoints, employees, and products, run:
```powershell
python -m backend.seed
```
This command automatically executes SQLAlchemy schema migrations, creates `zero_trust_supply_chain.db`, and provisions:
* **4 Supply Chain Checkpoints**:
  * `C01`: Manufacturer Node (Sequence 1)
  * `C02`: Central Warehouse (Sequence 2)
  * `C03`: Regional Distribution Hub (Sequence 3)
  * `C04`: Retail Destination (Sequence 4)
* **4 Authorized Operators**: `E101` to `E104` with normal PIN `1234` and silent duress PIN `9999`.
* **Baseline Products**: Pre-enrolled smart label items for testing.

---

### 3. Launching the Full System
To start both the FastAPI server and open the web management interface in one command:
```powershell
python run_system.py
```
* **Dashboard & Security Console**: `http://127.0.0.1:8000/dashboard`
* **Administrative Statistics**: `http://127.0.0.1:8000/admin-stats`
* **Executive Architecture Visualizer**: `http://127.0.0.1:8000/`
* **Interactive OpenAPI Swagger Docs**: `http://127.0.0.1:8000/docs`

---

### 4. Running Physical Hardware with the USB-Serial Bridge
1. Connect your flashed ESP32 to your PC via USB.
2. In a separate terminal, launch the serial bridge:
   ```powershell
   python serial_bridge.py
   ```
3. The bridge auto-detects the active COM port (e.g., `COM15`), opens the serial channel at 115200 baud, receives scan telemetry (`UID, CHECKPOINT, TAMPER_BIT`), and dispatches it via HTTP POST to `http://127.0.0.1:8000/api/scan`.

---

## 🧪 Experimental Validation & Reproducibility Suite (`eval_icoet/`)

The repository includes a comprehensive, scientifically auditable evaluation kit developed for academic verification:

### Stage 1: Original 120-Trial Suite (Concordance & Latency)
Runs 20 trials across each of the 6 core scenarios ($N=120$):
```powershell
python eval_icoet/run_original_120.py
python eval_icoet/analyze_original_trials.py trial_results.csv
```
* **Concordance**: **120 / 120 PASS (100%)**
* **Slowest Single Trial**: **0.044 s** (Benchmark limit: $< 2.000\text{ s}$)
* **False Tamper Rate**: **0** false alerts in untouched scans
* **Duress Concealment**: **20 / 20** displayed `ALLOW (VERIFIED)` with background alert.

### Stage 2: Paired Baseline Comparison (Zero-Trust vs UID-Only)
Compares the full 8-check Zero-Trust engine against a naive registered-UID baseline under identical controlled inputs:
```powershell
python eval_icoet/compare_baselines.py --confirm-reset --out results/icoet_baseline
```
* **Anomaly Detection Rate**: Zero-Trust = **100/100 (100%)** vs UID-Only = **0/100 (0%)**
* **Normal Specificity**: **20/20 (100%)** for both policies.

### Stage 3: Defensive Adversarial Probes
Evaluates 8 defensive negative test cases to document security boundaries and residual risks:
```powershell
python eval_icoet/security_probes.py --confirm-reset --out results/icoet_probes
```

### Stage 4: Empirical Hardware Benchmarking (ESP32 on COM15)
Records microsecond-accurate serial-to-HTTP transit and server commitment latencies:
```powershell
# 30 Scans with Intact Seal
python eval_icoet/instrumented_serial_bridge.py --port COM15 --limit 30 --out results/hardware/connected.csv

# 30 Scans with Broken Seal
python eval_icoet/instrumented_serial_bridge.py --port COM15 --limit 30 --out results/hardware/tampered.csv
```
* **Intact Seal**: Mean latency = **44.72 ms**, 0 false tampers.
* **Broken Seal**: Mean latency = **46.17 ms**, 30/30 (100%) true `QUARANTINE`.
* **API Delivery**: 60 / 60 requests returned HTTP 200 (0 drops).

### Stage 5: Station Dwell vs Fresh UID Benchmark
Validates the Station Dwell Policy on repeated taps of the same tag at `C01` versus distinct fresh tags:
```powershell
python eval_icoet/repeat_scan_benchmark.py
```
* **Authorized Repeat Dwell Scans**: **30 / 30 ALLOW (100%)**
* **Fresh Registered UIDs**: **30 / 30 ALLOW (100%)**

### Stage 6: Persistent Quarantine Hold Regression
Verifies that a tampered product cannot clear quarantine by being re-tapped with an intact seal:
```powershell
python optional_quarantine_hold_regression.py --confirm-reset
```
* **Result**: `initial: QUARANTINE (20) -> rescan: QUARANTINE (0)`. No quarantine-release transition.

### Stage 7: Evidence Manifest & Provenance Snapshot
Computes SHA-256 cryptographic digests for all generated datasets and records the exact environment:
```powershell
python eval_icoet/evidence_snapshot.py --results results
```
Output saved to [`results/evidence_manifest.json`](results/evidence_manifest.json).

---

## 🔒 Security Threat Model & Architectural Limitations

For scientific transparency, the defensive probes establish the following boundaries:
1. **Unauthenticated Provisioning at C01**: Unregistered tags presented at Manufacturer Node C01 are auto-enrolled by default. In high-assurance environments, provisioning must require an authenticated, digitally signed certificate.
2. **Client-Side Tamper Attestation**: The server relies on the client-reported boolean without hardware cryptographic attestation. An attacker with a compromised serial bridge can forge tamper bits. Production implementations should utilize a hardware Secure Element (e.g. ATECC608A) or signed attestation tokens.
3. **Temporal Clone Detection Boundary**: RFID cloning detection utilizes a 10-second temporal window. Standard ISO 14443A static UIDs remain vulnerable to RF emulation; cryptographic mutual authentication (such as MIFARE DESFire EV3) is required to eliminate static UID duplication.

---

## 📄 License & Academic Attribution
* **License**: MIT Open Source License.
* **Authors**: Duddu Satya Sai Vishnu Vardhan, Namburi Mokshitha Sai.
* **Institution**: Vellore Institute of Technology (VIT).
