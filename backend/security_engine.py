import datetime
import json
from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from backend.models import Product, Checkpoint, Employee, ScanHistory, Alert

def evaluate_zero_trust_scan(
    db: Session,
    rfid_uid: str,
    checkpoint_id: str,
    tamper_detected: bool,
    employee_id: str = None,
    pin: str = None
) -> Dict[str, Any]:
    """
    Evaluates 8 Zero-Trust Multi-Factor security checks for an RFID scan.
    Returns evaluation result dict with trust_score, decision, violations, alerts, and display_message.
    """
    violations: List[str] = []
    generated_alerts: List[Dict[str, Any]] = []
    
    trust_score = 100
    rfid_clean = rfid_uid.strip().upper()
    
    # 1. RFID Registration Check
    product = db.query(Product).filter(Product.rfid_uid == rfid_clean).first()
    if not product:
        if checkpoint_id == "C01":
            # Auto-register new tags at Manufacturer Node (C01)
            new_prod_id = f"P_AUTO_{int(datetime.datetime.utcnow().timestamp())}"
            product = Product(
                product_id=new_prod_id,
                product_name=f"Auto-Enrolled Product",
                rfid_uid=rfid_clean,
                manufacturer="System Auto-Enrollment",
                status="ALLOW",
                current_checkpoint_id=None,
                expected_next_checkpoint_id="C01"
            )
            db.add(product)
            db.commit()
            db.refresh(product)
            # Tag is now registered! Continue with normal evaluation below.
        else:
            trust_score = 0
            violations.append("UNREGISTERED_RFID: RFID tag is not registered in the system.")
            generated_alerts.append({
                "alert_type": "UNREGISTERED_RFID",
                "description": f"Unregistered RFID tag scanned: {rfid_clean} at checkpoint {checkpoint_id}.",
                "severity": "CRITICAL"
            })
            decision = "QUARANTINE"
            
            # Record scan history even for unregistered
            scan_record = ScanHistory(
                product_id=None,
                rfid_uid=rfid_clean,
                checkpoint_id=checkpoint_id,
                timestamp=datetime.datetime.utcnow(),
                tamper_detected=tamper_detected,
                employee_id=employee_id,
                is_duress=False,
                trust_score=0,
                decision=decision,
                violation_details=json.dumps(violations)
            )
            db.add(scan_record)
            db.commit()
            db.refresh(scan_record)
            
            for alt in generated_alerts:
                alert_obj = Alert(
                    scan_id=scan_record.scan_id,
                    alert_type=alt["alert_type"],
                    description=alt["description"],
                    severity=alt["severity"],
                    timestamp=datetime.datetime.utcnow()
                )
                db.add(alert_obj)
            db.commit()
            
            return {
                "decision": decision,
                "trust_score": 0,
                "product_id": None,
                "product_name": "UNKNOWN PRODUCT",
                "violations": violations,
                "is_duress": False,
                "display_status": "QUARANTINE",
                "scan_id": scan_record.scan_id,
                "led": "RED"
            }

    # Product found
    product_id = product.product_id
    curr_checkpoint = db.query(Checkpoint).filter(Checkpoint.checkpoint_id == checkpoint_id).first()
    all_checkpoints = db.query(Checkpoint).order_by(Checkpoint.sequence_order.asc()).all()
    cp_dict = {cp.checkpoint_id: cp for cp in all_checkpoints}

    # 2. Package Tamper Verification
    if tamper_detected:
        trust_score -= 80
        violations.append("PACKAGE_TAMPERED: Physical conductive seal is broken/opened.")
        generated_alerts.append({
            "alert_type": "TAMPER_DETECTED",
            "description": f"Physical tamper loop broken for Product {product_id} ({product.product_name}) at {checkpoint_id}.",
            "severity": "CRITICAL"
        })

    # 3. Employee Authentication & Silent Duress Mechanism
    is_duress = False
    if employee_id:
        emp = db.query(Employee).filter(Employee.employee_id == employee_id).first()
        if emp:
            if pin == emp.duress_pin:
                is_duress = True
                violations.append("SILENT_DURESS: Employee entered emergency Duress PIN.")
                generated_alerts.append({
                    "alert_type": "SILENT_DURESS",
                    "description": f"SILENT DURESS ALERT! Employee {emp.name} ({employee_id}) coerced at checkpoint {checkpoint_id} for product {product_id}!",
                    "severity": "CRITICAL"
                })
            elif pin != emp.normal_pin:
                trust_score -= 15
                violations.append("INVALID_EMPLOYEE_PIN: Employee PIN authentication failed.")
        else:
            trust_score -= 10
            violations.append("UNKNOWN_EMPLOYEE: Employee ID not registered.")

    # 4. Route Verification
    expected_cp = product.expected_next_checkpoint_id
    if expected_cp and checkpoint_id != expected_cp:
        # Check if out of order
        target_cp = cp_dict.get(checkpoint_id)
        expected_cp_obj = cp_dict.get(expected_cp)
        
        if target_cp and expected_cp_obj:
            if target_cp.sequence_order > expected_cp_obj.sequence_order:
                trust_score -= 35
                violations.append(f"ROUTE_VIOLATION: Skipped expected checkpoint {expected_cp}. Arrived at {checkpoint_id}.")
                generated_alerts.append({
                    "alert_type": "ROUTE_VIOLATION",
                    "description": f"Route Violation for {product_id}: Expected {expected_cp}, but scanned at {checkpoint_id}.",
                    "severity": "HIGH"
                })
            else:
                trust_score -= 25
                violations.append(f"ROUTE_BACKTRACK: Product scanned at previous checkpoint {checkpoint_id} (Expected {expected_cp}).")
                generated_alerts.append({
                    "alert_type": "ROUTE_VIOLATION",
                    "description": f"Route Backtrack for {product_id}: Scanned at {checkpoint_id} after passing it.",
                    "severity": "MEDIUM"
                })
        else:
            trust_score -= 20
            violations.append(f"ROUTE_MISMATCH: Invalid checkpoint {checkpoint_id}.")

    # 5. Travel Time & Speed Verification
    last_scan = (
        db.query(ScanHistory)
        .filter(ScanHistory.product_id == product_id)
        .order_by(ScanHistory.scan_id.desc())
        .first()
    )
    
    now = datetime.datetime.utcnow()
    if last_scan and curr_checkpoint:
        time_diff_seconds = (now - last_scan.timestamp).total_seconds()
        min_allowed = curr_checkpoint.min_travel_seconds
        
        if last_scan.checkpoint_id != checkpoint_id and time_diff_seconds < min_allowed:
            trust_score -= 30
            violations.append(f"IMPOSSIBLE_TRAVEL_SPEED: Scanned at new checkpoint in {int(time_diff_seconds)}s (Min expected: {min_allowed}s).")
            generated_alerts.append({
                "alert_type": "IMPOSSIBLE_TRAVEL_SPEED",
                "description": f"Impossible movement speed for product {product_id}: Moved from {last_scan.checkpoint_id} to {checkpoint_id} in {int(time_diff_seconds)} seconds.",
                "severity": "HIGH"
            })

    # 6. Duplicate RFID Usage / Cloning Detection
    recent_duplicate = (
        db.query(ScanHistory)
        .filter(
            ScanHistory.rfid_uid == rfid_clean,
            ScanHistory.checkpoint_id != checkpoint_id
        )
        .order_by(ScanHistory.scan_id.desc())
        .first()
    )
    if recent_duplicate:
        dup_diff = (now - recent_duplicate.timestamp).total_seconds()
        if dup_diff < 10: # Scanned at two different checkpoints within 10 seconds
            trust_score -= 40
            violations.append(f"DUPLICATE_RFID_CLONE: RFID {rfid_clean} scanned simultaneously at {recent_duplicate.checkpoint_id} and {checkpoint_id}!")
            generated_alerts.append({
                "alert_type": "RFID_CLONE",
                "description": f"SUSPECTED RFID CLONING ATTACK! Tag {rfid_clean} used concurrently at multiple checkpoints within {int(dup_diff)}s.",
                "severity": "CRITICAL"
            })

    # 7. Previous Scan Verification
    if last_scan and product.current_checkpoint_id:
        if last_scan.checkpoint_id != product.current_checkpoint_id:
            trust_score -= 15
            violations.append(f"SCAN_HISTORY_MISMATCH: Recorded location ({product.current_checkpoint_id}) does not match last scan ({last_scan.checkpoint_id}).")

    # Final Score Calculation & Decision Matrix
    trust_score = max(0, min(100, trust_score))
    
    if tamper_detected or trust_score < 50:
        decision = "QUARANTINE"
        led_color = "RED"
    elif trust_score < 80:
        decision = "FLAG"
        led_color = "YELLOW"
    else:
        decision = "ALLOW"
        led_color = "GREEN"

    # Deceptive UI output for Silent Duress (so attacker sees normal ALLOW/VERIFIED)
    display_status = decision
    if is_duress and decision == "ALLOW":
        display_status = "ALLOW (VERIFIED)" # UI will display clean ALLOW to attacker, while alert triggers for security team

    # Update Product status in DB
    product.status = decision
    product.current_checkpoint_id = checkpoint_id
    
    # Calculate next expected checkpoint
    if curr_checkpoint:
        next_seq = curr_checkpoint.sequence_order + 1
        next_cp_obj = db.query(Checkpoint).filter(Checkpoint.sequence_order == next_seq).first()
        if next_cp_obj:
            product.expected_next_checkpoint_id = next_cp_obj.checkpoint_id
        else:
            product.expected_next_checkpoint_id = "COMPLETED"

    # Save Scan Record
    scan_record = ScanHistory(
        product_id=product_id,
        rfid_uid=rfid_clean,
        checkpoint_id=checkpoint_id,
        timestamp=now,
        tamper_detected=tamper_detected,
        employee_id=employee_id,
        is_duress=is_duress,
        trust_score=trust_score,
        decision=decision,
        violation_details=json.dumps(violations)
    )
    db.add(scan_record)
    db.commit()
    db.refresh(scan_record)

    # Save Alerts
    for alt in generated_alerts:
        alert_obj = Alert(
            scan_id=scan_record.scan_id,
            alert_type=alt["alert_type"],
            description=alt["description"],
            severity=alt["severity"],
            timestamp=now
        )
        db.add(alert_obj)
    db.commit()

    return {
        "scan_id": scan_record.scan_id,
        "product_id": product_id,
        "product_name": product.product_name,
        "rfid_uid": rfid_clean,
        "checkpoint_id": checkpoint_id,
        "trust_score": trust_score,
        "decision": decision,
        "display_status": display_status,
        "violations": violations,
        "is_duress": is_duress,
        "tamper_detected": tamper_detected,
        "led": led_color,
        "next_checkpoint": product.expected_next_checkpoint_id
    }
