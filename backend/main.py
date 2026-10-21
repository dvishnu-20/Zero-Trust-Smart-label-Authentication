import os
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import engine, Base, get_db
from backend.models import Product, Checkpoint, Employee, ScanHistory, Alert
from backend.security_engine import evaluate_zero_trust_scan
from backend.seed import seed_database

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Zero Trust Smart Label Supply Chain Security API",
    description="Multi-factor Zero-Trust verification system combining RFID, physical tamper detection, route validation, duplicate detection, travel speed, and silent duress authentication.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Schemas
class ScanRequest(BaseModel):
    rfid_uid: str
    checkpoint_id: str
    tamper_detected: bool = False
    employee_id: Optional[str] = None
    pin: Optional[str] = None

class ProductRegisterRequest(BaseModel):
    product_id: str
    product_name: str
    rfid_uid: str
    manufacturer: str

# API Routes
@app.post("/api/scan")
def process_scan(payload: ScanRequest, db: Session = Depends(get_db)):
    """
    Primary checkpoint scanner endpoint called by ESP32 or Virtual Simulator.
    Runs 8 Zero-Trust multi-factor security checks.
    """
    result = evaluate_zero_trust_scan(
        db=db,
        rfid_uid=payload.rfid_uid,
        checkpoint_id=payload.checkpoint_id,
        tamper_detected=payload.tamper_detected,
        employee_id=payload.employee_id,
        pin=payload.pin
    )
    return result

@app.get("/api/products")
def get_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    result = []
    for p in products:
        curr_cp = db.query(Checkpoint).filter(Checkpoint.checkpoint_id == p.current_checkpoint_id).first()
        next_cp = db.query(Checkpoint).filter(Checkpoint.checkpoint_id == p.expected_next_checkpoint_id).first()
        result.append({
            "product_id": p.product_id,
            "product_name": p.product_name,
            "rfid_uid": p.rfid_uid,
            "manufacturer": p.manufacturer,
            "status": p.status,
            "current_checkpoint": curr_cp.checkpoint_name if curr_cp else "Not Started",
            "current_checkpoint_id": p.current_checkpoint_id,
            "expected_next_checkpoint": next_cp.checkpoint_name if next_cp else ("Completed" if p.expected_next_checkpoint_id == "COMPLETED" else "Manufacturer Node"),
            "expected_next_checkpoint_id": p.expected_next_checkpoint_id,
            "registered_at": p.registered_at.isoformat() if p.registered_at else None
        })
    return result

@app.post("/api/products/register")
def register_product(payload: ProductRegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(Product).filter(
        (Product.product_id == payload.product_id) | (Product.rfid_uid == payload.rfid_uid)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Product ID or RFID UID already registered.")
    
    first_cp = db.query(Checkpoint).order_by(Checkpoint.sequence_order.asc()).first()
    new_p = Product(
        product_id=payload.product_id,
        product_name=payload.product_name,
        rfid_uid=payload.rfid_uid.upper(),
        manufacturer=payload.manufacturer,
        status="ALLOW",
        current_checkpoint_id=None,
        expected_next_checkpoint_id=first_cp.checkpoint_id if first_cp else "C01"
    )
    db.add(new_p)
    db.commit()
    db.refresh(new_p)
    return {"message": "Product registered successfully", "product": new_p}

@app.get("/api/products/{product_id}/track")
def track_product(product_id: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    scans = (
        db.query(ScanHistory)
        .filter(ScanHistory.product_id == product_id)
        .order_by(ScanHistory.scan_id.asc())
        .all()
    )
    
    checkpoints = db.query(Checkpoint).order_by(Checkpoint.sequence_order.asc()).all()
    
    history_list = []
    for s in scans:
        cp = db.query(Checkpoint).filter(Checkpoint.checkpoint_id == s.checkpoint_id).first()
        history_list.append({
            "scan_id": s.scan_id,
            "checkpoint_id": s.checkpoint_id,
            "checkpoint_name": cp.checkpoint_name if cp else s.checkpoint_id,
            "timestamp": s.timestamp.isoformat() + "Z" if s.timestamp else None,
            "tamper_detected": s.tamper_detected,
            "trust_score": s.trust_score,
            "decision": s.decision,
            "is_duress": s.is_duress,
            "employee_id": s.employee_id
        })

    return {
        "product_id": product.product_id,
        "product_name": product.product_name,
        "rfid_uid": product.rfid_uid,
        "status": product.status,
        "current_checkpoint_id": product.current_checkpoint_id,
        "expected_next_checkpoint_id": product.expected_next_checkpoint_id,
        "all_checkpoints": [{"checkpoint_id": c.checkpoint_id, "checkpoint_name": c.checkpoint_name, "sequence_order": c.sequence_order} for c in checkpoints],
        "scans": history_list
    }

@app.get("/api/checkpoints")
def get_checkpoints(db: Session = Depends(get_db)):
    cps = db.query(Checkpoint).order_by(Checkpoint.sequence_order.asc()).all()
    return cps

@app.get("/api/employees")
def get_employees(db: Session = Depends(get_db)):
    employees = db.query(Employee).all()
    return [{"employee_id": e.employee_id, "name": e.name, "assigned_checkpoint_id": e.assigned_checkpoint_id} for e in employees]

@app.get("/api/scans")
def get_scans(limit: int = 50, db: Session = Depends(get_db)):
    scans = db.query(ScanHistory).order_by(ScanHistory.scan_id.desc()).limit(limit).all()
    res = []
    for s in scans:
        cp = db.query(Checkpoint).filter(Checkpoint.checkpoint_id == s.checkpoint_id).first()
        res.append({
            "scan_id": s.scan_id,
            "product_id": s.product_id,
            "rfid_uid": s.rfid_uid,
            "checkpoint_id": s.checkpoint_id,
            "checkpoint_name": cp.checkpoint_name if cp else s.checkpoint_id,
            "timestamp": s.timestamp.isoformat() + "Z" if s.timestamp else None,
            "tamper_detected": s.tamper_detected,
            "trust_score": s.trust_score,
            "decision": s.decision,
            "is_duress": s.is_duress,
            "employee_id": s.employee_id
        })
    return res

@app.get("/api/alerts")
def get_alerts(db: Session = Depends(get_db)):
    alerts = db.query(Alert).order_by(Alert.alert_id.desc()).limit(50).all()
    res = []
    for a in alerts:
        res.append({
            "alert_id": a.alert_id,
            "scan_id": a.scan_id,
            "alert_type": a.alert_type,
            "description": a.description,
            "severity": a.severity,
            "timestamp": a.timestamp.isoformat() + "Z" if a.timestamp else None,
            "acknowledged": a.acknowledged
        })
    return res

@app.post("/api/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.acknowledged = True
    db.commit()
    return {"message": "Alert acknowledged"}

@app.post("/api/seed")
def reset_and_seed(db: Session = Depends(get_db)):
    seed_database()
    return {"message": "Database reset and seeded with default supply chain dataset successfully."}

@app.post("/api/demo/trigger/{demo_id}")
def trigger_demo_scenario(demo_id: int, db: Session = Depends(get_db)):
    """
    Preset triggers for Faculty Review Presentations:
    Demo 1: Normal Product Journey (P1001 scanned sequentially at C01)
    Demo 2: Package Tampering (P1001 scanned with tamper wire broken)
    Demo 3: Wrong Route Violation (P1002 scanned at C03 skipping C01 & C02)
    Demo 4: RFID Cloning Attack (A1B2C3D4 scanned simultaneously at C04)
    Demo 5: Suspicious Travel Speed (Rapid scans within 1s across distant nodes)
    Demo 6: Silent Duress Emergency (Employee scans using Duress PIN 9999)
    """
    if demo_id == 1:
        # Normal scan
        res = evaluate_zero_trust_scan(db, rfid_uid="A1B2C3D4", checkpoint_id="C01", tamper_detected=False, employee_id="E101", pin="1234")
        return {"demo": "Demo 1 - Normal Product", "result": res}
    elif demo_id == 2:
        # Tampered package
        res = evaluate_zero_trust_scan(db, rfid_uid="A1B2C3D4", checkpoint_id="C02", tamper_detected=True, employee_id="E102", pin="1234")
        return {"demo": "Demo 2 - Tampered Package", "result": res}
    elif demo_id == 3:
        # Route violation (Product P1002 starts at C01 expected, but scanned directly at C04)
        res = evaluate_zero_trust_scan(db, rfid_uid="E5F6G7H8", checkpoint_id="C04", tamper_detected=False, employee_id="E104", pin="1234")
        return {"demo": "Demo 3 - Route Manipulation", "result": res}
    elif demo_id == 4:
        # RFID cloning attack (Same tag scanned at C01 then immediately at C04)
        evaluate_zero_trust_scan(db, rfid_uid="99887766", checkpoint_id="C01", tamper_detected=False, employee_id="E101", pin="1234")
        res = evaluate_zero_trust_scan(db, rfid_uid="99887766", checkpoint_id="C04", tamper_detected=False, employee_id="E104", pin="1234")
        return {"demo": "Demo 4 - RFID Cloning Attack", "result": res}
    elif demo_id == 5:
        # Suspicious speed (Rapid consecutive scans)
        evaluate_zero_trust_scan(db, rfid_uid="11223344", checkpoint_id="C01", tamper_detected=False, employee_id="E101", pin="1234")
        res = evaluate_zero_trust_scan(db, rfid_uid="11223344", checkpoint_id="C02", tamper_detected=False, employee_id="E102", pin="1234")
        return {"demo": "Demo 5 - Suspicious Movement Speed", "result": res}
    elif demo_id == 6:
        # Silent Duress
        res = evaluate_zero_trust_scan(db, rfid_uid="55667788", checkpoint_id="C01", tamper_detected=False, employee_id="E101", pin="9999")
        return {"demo": "Demo 6 - Silent Duress Triggered", "result": res}
    else:
        raise HTTPException(status_code=400, detail="Invalid Demo ID. Choose 1 to 6.")

@app.get("/api/admin/metrics")
def get_admin_metrics(db: Session = Depends(get_db)):
    total_products = db.query(Product).count()
    total_scans = db.query(ScanHistory).count()
    allow_scans = db.query(ScanHistory).filter(ScanHistory.decision == "ALLOW").count()
    flag_scans = db.query(ScanHistory).filter(ScanHistory.decision == "FLAG").count()
    quarantine_scans = db.query(ScanHistory).filter(ScanHistory.decision == "QUARANTINE").count()
    duress_scans = db.query(ScanHistory).filter(ScanHistory.is_duress == True).count()
    tamper_scans = db.query(ScanHistory).filter(ScanHistory.tamper_detected == True).count()
    
    # Attack breakdown from alerts table
    alerts = db.query(Alert).all()
    threat_breakdown = {
        "TAMPER_RUPTURE": 0,
        "ROUTE_DEVIATION": 0,
        "RFID_CLONE": 0,
        "VELOCITY_ANOMALY": 0,
        "SILENT_DURESS": 0,
        "UNREGISTERED_TAG": 0,
        "EMPLOYEE_AUTH": 0,
        "OTHER": 0
    }
    
    for a in alerts:
        t = a.alert_type or ""
        if "TAMPER" in t:
            threat_breakdown["TAMPER_RUPTURE"] += 1
        elif "ROUTE" in t:
            threat_breakdown["ROUTE_DEVIATION"] += 1
        elif "CLON" in t or "DUPLICATE" in t:
            threat_breakdown["RFID_CLONE"] += 1
        elif "VELOCITY" in t or "SPEED" in t:
            threat_breakdown["VELOCITY_ANOMALY"] += 1
        elif "DURESS" in t:
            threat_breakdown["SILENT_DURESS"] += 1
        elif "UNREGISTERED" in t or "UNKNOWN" in t:
            threat_breakdown["UNREGISTERED_TAG"] += 1
        elif "EMPLOYEE" in t or "PIN" in t:
            threat_breakdown["EMPLOYEE_AUTH"] += 1
        else:
            threat_breakdown["OTHER"] += 1

    # Checkpoint-wise breakdown
    checkpoints = db.query(Checkpoint).order_by(Checkpoint.sequence_order.asc()).all()
    cp_stats = []
    for cp in checkpoints:
        cp_scans = db.query(ScanHistory).filter(ScanHistory.checkpoint_id == cp.checkpoint_id).count()
        cp_allow = db.query(ScanHistory).filter(ScanHistory.checkpoint_id == cp.checkpoint_id, ScanHistory.decision == "ALLOW").count()
        cp_tamper = db.query(ScanHistory).filter(ScanHistory.checkpoint_id == cp.checkpoint_id, ScanHistory.tamper_detected == True).count()
        cp_quarantine = db.query(ScanHistory).filter(ScanHistory.checkpoint_id == cp.checkpoint_id, ScanHistory.decision == "QUARANTINE").count()
        
        pass_rate = round((cp_allow / cp_scans * 100), 1) if cp_scans > 0 else 100.0
        health_status = "HEALTHY" if pass_rate >= 85 and cp_tamper == 0 else ("FLAGGED" if pass_rate >= 50 else "CRITICAL")
        
        cp_stats.append({
            "checkpoint_id": cp.checkpoint_id,
            "checkpoint_name": cp.checkpoint_name,
            "location": cp.location,
            "sequence_order": cp.sequence_order,
            "total_scans": cp_scans,
            "allow_count": cp_allow,
            "tamper_count": cp_tamper,
            "quarantine_count": cp_quarantine,
            "pass_rate": pass_rate,
            "health_status": health_status
        })

    # Overall Compliance / Health Index
    if total_scans > 0:
        health_index = round(((allow_scans + (flag_scans * 0.5)) / total_scans) * 100, 1)
    else:
        health_index = 100.0

    return {
        "summary": {
            "total_products": total_products,
            "total_scans": total_scans,
            "allow_scans": allow_scans,
            "flag_scans": flag_scans,
            "quarantine_scans": quarantine_scans,
            "duress_scans": duress_scans,
            "tamper_scans": tamper_scans,
            "health_index": health_index,
            "total_alerts": len(alerts)
        },
        "threat_breakdown": threat_breakdown,
        "checkpoint_stats": cp_stats
    }

# Mount frontend web static files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    def read_cover():
        return FileResponse(os.path.join(frontend_dir, "cover.html"))

    @app.get("/cover")
    def read_cover_alias():
        return FileResponse(os.path.join(frontend_dir, "cover.html"))

    @app.get("/dashboard")
    def read_dashboard():
        return FileResponse(os.path.join(frontend_dir, "index.html"))

    @app.get("/admin-stats")
    def read_admin_stats():
        return FileResponse(os.path.join(frontend_dir, "admin_stats.html"))

