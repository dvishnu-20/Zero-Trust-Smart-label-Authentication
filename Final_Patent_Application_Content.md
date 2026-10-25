# Form 2: Patent Application
*(Copy and paste the sections below into your final Word document template)*

---

### 1. Title of the Invention
**ZERO-TRUST SMART AUTHENTICATION LABEL SYSTEM AND METHOD FOR SECURE VERIFICATION OF PRODUCTS IN A SUPPLY CHAIN**

---

### 2. Applicant(s) & Inventor(s) Details

**Applicant / Inventor 1**
* Name: Namburi Mokshitha Sai
* Registration No.: 23MID0149
* Nationality: Indian
* Institution / Affiliation: Vellore Institute of Technology (VIT)
* Address for Service in India: [Insert Full Physical Address / University Address here, including PIN code]
* Category of Applicant: Educational Institution / Student Applicant

**Applicant / Inventor 2**
* Name: D. Satya Sai Vishnu Vardhan
* Registration No.: 23MID0163
* Nationality: Indian
* Institution / Affiliation: Vellore Institute of Technology (VIT)
* Address for Service in India: [Insert Full Physical Address / University Address here, including PIN code]
* Category of Applicant: Educational Institution / Student Applicant

---

### 3. Field of the Invention
The present invention relates generally to the field of Internet of Things (IoT)-enabled security and authentication systems, and more particularly to a Zero-Trust based smart authentication label system for products moving through a multi-stakeholder supply chain. The invention combines Radio Frequency Identification (RFID) tagging, physical package tamper detection, checkpoint-based route and time verification, and continuous multi-factor trust scoring to authenticate physical goods at every stage of their movement from manufacturer to warehouse, distributor, and retailer, thereby addressing anti-counterfeiting, product traceability, and supply-chain security.

---

### 4. Background of the Invention & Prior Art
In a typical supply chain, a product moves sequentially through a manufacturer, a warehouse, a distributor, and a retailer, and Radio Frequency Identification (RFID) tags are conventionally used to identify and track such products. A significant drawback of existing RFID-based identification is that the presence of a valid RFID tag does not prove that the product to which it is attached has not been tampered with. 

In practice, an RFID tag can be cloned, a genuine tag can be removed from an authentic product and attached to a counterfeit product, or a sealed package can be opened and its contents replaced. Furthermore, a product can be diverted through an incorrect route, the same RFID tag can be read at multiple, geographically inconsistent locations, and previously captured scan data can be replayed. Verification of the tag identity alone is insufficient to authenticate the product.

Failure to detect these vulnerabilities allows counterfeit products to enter the supply chain, exposes customers to fraudulent goods, causes financial loss and reputational harm to manufacturers and brand owners, and makes it difficult to trace the specific point in the supply chain at which tampering occurred.

**Prior Art**
A review of the existing literature in the fields of Zero-Trust architectures for IoT, RFID authentication protocols, blockchain-assisted supply-chain traceability, and lightweight cryptographic authentication schemes reveals that:
* Existing Zero-Trust research addresses network and device-level identity verification, segmentation, and continuous monitoring for IoT networks generally, but does not disclose a practical Zero-Trust system for physical products moving through discrete supply-chain checkpoints.
* Existing RFID and NFC authentication protocols, including hash/XOR-based mutual authentication and blockchain-assisted schemes, secure the communication between a tag and a reader but do not verify whether the physical product, its label, or its package has been replaced or tampered with.
* Existing blockchain-based traceability platforms create immutable transaction logs of scan events, but such ledgers can record a cloned or diverted tag as a valid entry if the underlying node blindly trusts the tag, and cannot independently determine whether the physical goods themselves have been swapped.
* Existing lightweight Zero-Trust and anonymous-authentication frameworks are optimised to reduce cryptographic and communication overhead, but do not combine physical tamper detection with route-sequence and time-based contextual verification.

No prior art system known to the applicants combines, in a single low-cost embedded device, RFID identity verification, physical package tamper detection, checkpoint route-sequence verification, inter-checkpoint transit-time verification, clone-tag detection, and continuous multi-factor trust scoring to render a real-time ALLOW, FLAG, or QUARANTINE decision at each stage of a supply chain. There therefore exists a need for a low-cost, lightweight smart-label and checkpoint verification system that continuously re-evaluates a product's trustworthiness at every stage of the supply chain, rather than trusting a scanned RFID tag permanently once it has been read.

---

### 5. Object / Summary of the Invention
The main objective of the present invention is to provide a smart product label and checkpoint verification system that overcomes the limitations of existing approaches by authenticating a product independently at each checkpoint rather than depending on a single RFID validation performed at an earlier stage.

In the present invention, each product is provided with an RFID smart label along with a low-cost tamper detection mechanism in the form of a copper wire loop attached to the package seal. At each checkpoint, a hardware module reads the product RFID tag and the state of the tamper loop. Additional information, which includes a checkpoint identifier, operator authentication information, and a scan timestamp, is collected and transmitted through a wireless communication network to a backend server.

The backend security server evaluates the product against multiple independent factors and computes a composite trust score. Based on this trust score, the system renders and communicates one of three decisions: ALLOW, FLAG (for manual review), or QUARANTINE. In the physical prototype implementation, the checkpoint unit provides the operator with relevant verification information through an OLED display. A push button is incorporated to control the checkpoints. This implementation provides a low-cost approach for demonstrating checkpoint-based product verification.

---

### 6. Brief Description of Drawings
* **FIG. 1** — Block diagram illustrating the overall three-layer system architecture of the invention (Smart Product layer, Checkpoint Node layer, and Security Server layer), together with the data flow between an RFID tag, a checkpoint hardware module, a backend security engine, a database layer, and a web dashboard.
* **FIG. 2** — Circuit design diagram of the checkpoint hardware module.
* **FIG. 3** — Photograph of the physical prototype of the Manufacturer (C01) checkpoint module.

---

### 7. Detailed Description of the Invention

**7.1 System Architecture**
The invention is implemented as a three-layer system, as shown in FIG. 1.
* **Layer 1 - Smart Product:** Each product is provided with a passive RFID tag (13.56 MHz, MIFARE Classic or equivalent) that uniquely identifies the product, together with a tamper-detection mechanism in the form of a conductive copper-wire loop laid across the package seal. The copper loop forms a closed electrical circuit while the seal is intact. Severing or opening the seal breaks the loop and changes its electrical state from a closed condition to an open condition detectable by the checkpoint hardware.
* **Layer 2 - Checkpoint Node (Edge):** Each checkpoint in the supply chain is equipped with a checkpoint hardware module built around an ESP32 microcontroller connected via a Serial Peripheral Interface (SPI) bus to an MFRC522 RFID reader and to a tamper-sensing input pin connected to the copper-wire loop. The ESP32 reads the RFID tag identifier and the tamper-loop state and packages this data (together with the checkpoint identity and, where applicable, an operator authentication code) into a JSON payload and transmits it to the backend security server over Wi-Fi by an HTTP POST request.
* **Layer 3 - Security Server:** The backend is implemented using the Python FastAPI framework with an SQLite database managed through SQLAlchemy. On receiving data from the checkpoint, the backend processes the data using multiple Zero-Trust verification parameters such as RFID registry validity, physical tamper status, operator authentication (including a concealed duress condition), route-sequence correctness, inter-checkpoint transit time, duplicate or cloned tag usage, and continuity with the product's previous scan history, and computes a composite trust score on a scale of 0 to 100. Based on this trust score, the system communicates one of three decisions: ALLOW, FLAG (for review), or QUARANTINE, and the corresponding outcome, together with the checkpoint's scan record, is stored for audit and traceability purposes and is displayed to the operator. A web-based dashboard enables authorised users to monitor scans, track product movement, view alerts, and analyse verification information according to their assigned roles.

**7.2 Supply-Chain Route and Trust Decision Logic**
The prototype route consists of four checkpoints in sequence: C01 (Manufacturer), C02 (Warehouse), C03 (Distributor), and C04 (Retailer). The backend tracks each product's current and expected-next checkpoint, flagging any scan that breaks this order as a route violation. Using the trust-score factors, the system decides whether to ALLOW, FLAG (manual review required), or QUARANTINE (product held pending investigation). Specific violations—like tamper detection, route mismatch, an implausibly short inter-checkpoint transit time ("suspicious speed"), or the same tag appearing at two checkpoints at once ("clone" condition)—reduce the trust score and generate a timestamped alert on the dashboard's live incident feed.

**7.3 Operator Authentication and Silent-Duress Feature**
Every scan also requires an operator ID and a numeric PIN entered at the checkpoint. A normal PIN (e.g., "1234") authenticates the scan as usual, but a separate, pre-registered duress PIN (e.g., "9999") produces an outwardly identical "ALLOW (VERIFIED)" result at the checkpoint while silently sending a high-priority alert to the security dashboard. This lets an operator acting under coercion signal for help without alerting whoever is forcing the scan.

**7.4 Physical Hardware Implementation**
In addition to the circuit design shown in FIG. 2 and the software simulation, a working checkpoint module has been physically built for Checkpoint C01 (Manufacturer), shown in FIG. 3. The build consists of: an ESP32 board as the controller, an MFRC522 reader wired to it over SPI, an RFID tag on the sample product, a copper-wire tamper loop across the package seal wired to a digital input on the ESP32, a push button used to step the demonstrated checkpoint state through C01 → C02 → C03 → C04 so the full four-checkpoint journey can be shown on the single physical unit, and an OLED display showing the scanned tag ID, current checkpoint, and tamper status. The OLED display communicates the ALLOW/FLAG/QUARANTINE result to the operator. Only C01 exists as physical hardware; C02, C03, and C04 are still represented through the software-based virtual hardware simulator which reproduces scanning, tampering, PIN entry, and the resulting outcome for those stages. The physical unit and the simulated checkpoints both talk to the same FastAPI backend over the same Wi-Fi/HTTP/JSON protocol, so both are evaluated by the same Zero-Trust engine.

**7.5 Software Implementation**
A working web dashboard has been developed providing product registration, live scan monitoring, security alerts, trust-score results, route tracking, and threat information. The ESP32 firmware handles RFID reading, SPI communication with the MFRC522, tamper-loop monitoring, Wi-Fi communication, JSON payload construction, HTTP POST transmission, and output-device control. The backend is implemented in FastAPI, exposes REST endpoints for product registration, scanning, tracking, alerts, checkpoints, employees, and administrative metrics, and its database stores products, checkpoints, employees, scan history, and alerts. A virtual hardware simulator has additionally been developed to demonstrate RFID scanning, package tampering, operator PIN entry, and output-indicator responses for checkpoints that are not physically fabricated, allowing the complete four-checkpoint system to be demonstrated even where only one physical unit exists. An automated test suite exercises the security engine against normal verification, invalid RFID, package tampering, route violations, and the silent-duress feature; all automated tests, together with six interactive demonstration scenarios, have been executed successfully.

**7.6 Design Rationale**
The ESP32 was selected as the checkpoint controller for its built-in Wi-Fi connectivity, native 3.3V SPI support compatible with the MFRC522, low cost, and sufficient processing capability. The MFRC522 was selected as a low-cost 13.56 MHz reader offering a short, controlled reading range appropriate for deliberate checkpoint-by-checkpoint scanning. The conductive copper-wire loop was selected as a tamper sensor for its simplicity, low cost, and direct detection of package-seal integrity; unlike an accelerometer-based sensor, it is unaffected by ordinary handling or transport vibration. A multi-factor trust-scoring approach was adopted rather than a simple RFID whitelist or a blockchain-only approach, because a single RFID check can be defeated by tag cloning whereas combining RFID validity with tamper status, route, transit time, duplicate-use detection, and operator authentication yields a materially more reliable authenticity determination. FastAPI and SQLite were selected for the backend for their simplicity of development, and Wi-Fi/HTTP/JSON was selected as the communication protocol because it is natively supported by the ESP32.

**7.7 Economic and Environmental Considerations**
The physically implemented checkpoint hardware module is constructed from low-cost, commercially available components (ESP32 development board, MFRC522 RFID reader module, RFID tag, push button, OLED display, copper tape, jumper wires, and a basic enclosure), giving an approximate total prototype cost in the range of ₹800 to ₹1,100 per checkpoint unit. Because each product label uses a passive (battery-free) RFID tag, the invention avoids the need to fit a battery to every individual package, thereby reducing electronic waste and the associated environmental burden.

---

### 8. Claims (Independent + Dependent)
**We claim:**

1. A zero-trust smart authentication label system for verifying products in a supply chain, the system comprising: an RFID tag affixed to a product; a tamper-detection loop disposed across a seal of a package containing the product, the tamper-detection loop being configured to change electrical state upon the seal being opened; a checkpoint hardware module comprising a microcontroller operatively coupled to an RFID reader for reading the RFID tag and to the tamper-detection loop for reading a tamper status, a push button for advancing a checkpoint state, and a display for presenting a tag identifier, a checkpoint identifier, the tamper status and a verification result, the checkpoint hardware module being configured to transmit scan data, comprising the tag identifier, the tamper status and the checkpoint identifier, over a wireless network; and a backend security server configured to receive the scan data, to compute a composite trust score from a plurality of verification factors including RFID validity, tamper status, checkpoint route sequence and inter-checkpoint transit time, and to generate a decision, selected from an ALLOW decision, a FLAG decision and a QUARANTINE decision, based on the computed trust score, and to transmit the decision to the checkpoint hardware module for presentation on the display.
2. The system of claim 1, wherein the tamper-detection loop is a conductive copper-wire loop integrated across the package seal, presenting a closed-circuit electrical state when the seal is intact and an open-circuit electrical state when the seal is broken.
3. The system of claim 1, wherein the push button is configured to advance the checkpoint state through a predetermined sequence of checkpoints corresponding to sequential stages of the supply chain, enabling a single physically implemented checkpoint hardware module to demonstrate verification at each of the plurality of checkpoints.
4. The system of claim 1, wherein the display is an OLED display, and wherein the checkpoint hardware module presents on the OLED display, in real time, the RFID tag identifier, the current checkpoint identifier, the tamper status and the verification result received from the backend security server.
5. The system of claim 1, wherein the plurality of verification factors further includes operator authentication, duplicate or cloned RFID tag usage, and continuity between the current scan and a previous scan of the same product.
6. The system of claim 1, wherein the backend security server is configured to generate the ALLOW decision when the trust score is 80 or above, the FLAG decision when the trust score is between 50 and 79 inclusive, and the QUARANTINE decision when the trust score is below 50.
7. The system of claim 5, wherein the backend security server is configured to detect duplicate or cloned RFID tag usage by determining that the same RFID tag identifier has been read at two or more checkpoints within a time interval that is inconsistent with physical transit between those checkpoints.
8. The system of claim 1, wherein the backend security server is configured to detect a route-sequence violation by comparing a received checkpoint identifier against an expected next checkpoint identifier maintained for the product, and to flag the product where the received checkpoint identifier does not correspond to the expected next checkpoint.
9. The system of claim 5, wherein the operator authentication comprises entry of a security PIN at the checkpoint hardware module, and wherein the backend security server is configured, upon entry of a predetermined duress PIN distinct from a normal operating PIN, to cause the checkpoint hardware module to present an outwardly normal verification result on the display while covertly generating a critical security alert at the backend security server.
10. The system of claim 1, wherein the backend security server maintains a configurable minimum and/or maximum transit-time threshold for each pair of adjacent checkpoints, and is configured to reduce the trust score where a transit time between two checkpoint scans of the same product falls outside the configured threshold for that pair of checkpoints.
11. The system of claim 1, wherein the checkpoint hardware module further comprises a plurality of status indicator elements, selected from light-emitting diodes of different colours and an audible buzzer, configured to indicate the ALLOW, FLAG or QUARANTINE decision, as an alternative or in addition to the display.

**Independent Method Claim**
12. A method of verifying a product in a supply chain using a zero-trust smart authentication label system, the method comprising: reading, by a checkpoint hardware module at a checkpoint, an RFID tag identifier affixed to the product and a tamper status of a tamper-detection loop disposed across a package seal of the product; receiving, at the checkpoint hardware module, a checkpoint-advance input from a push button and updating a checkpoint state accordingly; transmitting scan data, comprising the RFID tag identifier, the tamper status and a checkpoint identifier corresponding to the checkpoint state, from the checkpoint hardware module to a backend security server over a wireless network; computing, at the backend security server, a composite trust score from a plurality of verification factors comprising RFID validity, the tamper status, a route-sequence check, and an inter-checkpoint transit-time check; generating a decision selected from ALLOW, FLAG and QUARANTINE based on the computed trust score; transmitting the decision to the checkpoint hardware module; and presenting the RFID tag identifier, the checkpoint identifier, the tamper status and the decision on a display of the checkpoint hardware module.
13. The method of claim 12, further comprising detecting duplicate or cloned use of the RFID tag identifier by determining that the RFID tag identifier has been received from two or more checkpoints within a time interval inconsistent with physical transit therebetween, and reducing the trust score accordingly.
14. The method of claim 12, further comprising receiving an operator security PIN at the checkpoint hardware module, and, upon determining that the received security PIN corresponds to a predetermined duress PIN, presenting an outwardly normal verification result on the display while generating a covert critical security alert at the backend security server.
15. The method of claim 12, further comprising storing the scan data and the generated decision in a database, and displaying live scan records, route-tracking information and security alerts on a web-based dashboard accessible to authorised stakeholders of the supply chain.

---

### 9. Abstract (≤ 150 words)
A zero-trust smart authentication label system for verifying products in a multi-stage supply chain is disclosed. Each product carries a passive RFID tag together with a copper-wire tamper-detection loop integrated into its packaging. A checkpoint hardware module, comprising a microcontroller, an RFID reader, a push button, and a display, reads the tag and tamper status and transmits this data over a wireless network to a backend security server. The server computes a continuous multi-factor trust score from RFID validity, tamper condition, checkpoint route sequence, inter-checkpoint travel time, duplicate tag usage, operator authentication, and prior scan history, and issues an ALLOW, FLAG, or QUARANTINE decision. A concealed duress-PIN feature lets a coerced operator covertly alert security while an outwardly normal result is displayed. The system detects tag cloning, route manipulation, tampering, and impossible transit speeds without relying on RFID identity alone.

---

### 10. Declaration, Signature & Date
We hereby declare that:
1. The above-named invention has been devised by us and is, to the best of our knowledge and belief, novel and has not been anticipated by publication in India or elsewhere before the date of this application;
2. We are in possession of the above-named invention and believe that we are the true and first inventors thereof;
3. The particulars given in this application and the accompanying statements and specification are correct to the best of our knowledge and belief; and
4. We claim the priority date, if any, as indicated in this application, and undertake to furnish such further information or documents as may be required under the Patents Act, 1970 and the Patents Rules, 2003.

**Applicant / Inventor 1**
Name: Namburi Mokshitha Sai (23MID0149)
Signature: ____________________________
Date: ____________________________
Place: ____________________________

**Applicant / Inventor 2**
Name: D. Satya Sai Vishnu Vardhan (23MID0163)
Signature: ____________________________
Date: ____________________________
Place: ____________________________
