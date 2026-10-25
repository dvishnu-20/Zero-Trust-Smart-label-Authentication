import serial
import serial.tools.list_ports
import requests
import time
import threading
import sys

# Configuration
BACKEND_URL = "http://127.0.0.1:8000/api/scan"
BAUD_RATE = 115200

# Global state for simulating Duress PIN from the bridge
use_duress_pin = False

def get_employee_for_checkpoint(cp_id):
    mapping = {
        "C01": "E101",
        "C02": "E102",
        "C03": "E103",
        "C04": "E104"
    }
    return mapping.get(cp_id, "E101")

def listen_for_keyboard():
    global use_duress_pin
    print("\n[Controls] Press 'D' + Enter to toggle Duress PIN mode for the next scan.")
    while True:
        try:
            line = sys.stdin.readline().strip().lower()
            if line == 'd':
                use_duress_pin = not use_duress_pin
                state = "ON (PIN: 9999)" if use_duress_pin else "OFF (PIN: 1234)"
                print(f"\n[!] Duress Mode is now {state}. Scan an RFID tag to test.\n")
        except:
            break

def main():
    print("=========================================================")
    print(" Zero Trust Hardware-Software Serial Bridge")
    print("=========================================================")
    
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("[ERROR] No serial ports found. Please connect the ESP32 via USB.")
        return
        
    print("Available Ports:")
    for i, port in enumerate(ports):
        print(f"[{i}] {port.device} - {port.description}")
        
    if len(ports) == 1:
        selected_port = ports[0].device
        print(f"Auto-selecting only available port: {selected_port}")
    else:
        idx = input(f"Select port index [0-{len(ports)-1}]: ")
        try:
            selected_port = ports[int(idx)].device
        except:
            print("Invalid selection.")
            return

    try:
        ser = serial.Serial(selected_port, BAUD_RATE, timeout=1)
        print(f"[SUCCESS] Connected to ESP32 on {selected_port} at {BAUD_RATE} baud.")
    except Exception as e:
        print(f"[ERROR] Could not open port {selected_port}: {e}")
        return

    # Start keyboard listener in background for Duress PIN toggling
    threading.Thread(target=listen_for_keyboard, daemon=True).start()

    print("\n[READY] Waiting for RFID scans from hardware...")
    
    global use_duress_pin
    while True:
        try:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                if not line:
                    continue
                    
                # Expected format from ESP32: "A1 B2 C3 D4, 2, 1" or "A1 B2 C3 D4, 2"
                if "," in line:
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 2:
                        uid_raw = parts[0]
                        cp_num = parts[1]
                        
                        # Remove spaces and uppercase
                        uid_clean = uid_raw.replace(" ", "").upper()
                        
                        # Validate: Checkpoint must be a single digit (1-4) and UID must be valid hex
                        is_valid_cp = cp_num.isdigit() and (1 <= int(cp_num) <= 4)
                        is_valid_hex = bool(uid_clean) and all(c in "0123456789ABCDEF" for c in uid_clean) and len(uid_clean) >= 6
                        
                        if not (is_valid_cp and is_valid_hex):
                            # Ignore ESP32 bootloader / ROM debug logs (e.g. rst:0x1, configsip, load:0x...)
                            continue
                        
                        is_tampered = False
                        if len(parts) >= 3:
                            is_tampered = (parts[2].strip() == "1")
                        
                        # Format Checkpoint ID (e.g. 1 -> C01)
                        checkpoint_id = f"C0{cp_num}"
                        employee_id = get_employee_for_checkpoint(checkpoint_id)
                        
                        # Determine PIN
                        pin = "9999" if use_duress_pin else "1234"
                        
                        tamper_str = " | ⚠️ TAMPERED!" if is_tampered else ""
                        print(f"\n[SCAN DETECTED] UID: {uid_clean} | Checkpoint: {checkpoint_id} | Employee: {employee_id}{tamper_str}")
                        
                        if use_duress_pin:
                            print("[!] Sending SILENT DURESS PIN (9999) to backend...")
                            
                        # Build payload
                        payload = {
                            "rfid_uid": uid_clean,
                            "checkpoint_id": checkpoint_id,
                            "tamper_detected": is_tampered,
                            "employee_id": employee_id,
                            "pin": pin
                        }
                        
                        # Send to backend
                        try:
                            res = requests.post(BACKEND_URL, json=payload, timeout=2)
                            if res.status_code == 200:
                                data = res.json()
                                print(f"[BACKEND DECISION] {data.get('decision')} | Score: {data.get('trust_score')}/100")
                            else:
                                print(f"[BACKEND ERROR] Status {res.status_code}: {res.text}")
                        except Exception as req_err:
                            print(f"[REQUEST ERROR] Could not reach backend: {req_err}")
                            
                        # Reset duress mode after single use
                        if use_duress_pin:
                            use_duress_pin = False
                            print("[INFO] Duress Mode automatically reset to OFF.")

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error reading serial: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
