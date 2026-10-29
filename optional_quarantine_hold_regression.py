"""Optional LOCAL destructive regression, not part of already-verified experiments.

Copy to the project root and run from that root:
    python optional_quarantine_hold_regression.py --confirm-reset

WARNING: The project's seed_database() DELETES and reseeds the configured DB.
Run ONLY against a disposable test copy of the repository and SQLite database.
"""
import sys
import uuid
from backend.database import SessionLocal
from backend.seed import seed_database
from backend.security_engine import evaluate_zero_trust_scan

if __name__ == "__main__":
    if "--confirm-reset" not in sys.argv:
        raise SystemExit("Refusing to reset DB without --confirm-reset in disposable test copy")
    seed_database()
    db = SessionLocal()
    try:
        uid = "Q" + uuid.uuid4().hex[:9].upper()
        first = evaluate_zero_trust_scan(
            db, rfid_uid=uid, checkpoint_id="C01", tamper_detected=True,
            employee_id="E101", pin="1234"
        )
        second = evaluate_zero_trust_scan(
            db, rfid_uid=uid, checkpoint_id="C01", tamper_detected=False,
            employee_id="E101", pin="1234"
        )
        print("initial tamper decision:", first["decision"], first["trust_score"])
        print("same-station rescan after tamper:", second["decision"], second["trust_score"])
        if first["decision"] == "QUARANTINE" and second["decision"] == "ALLOW":
            print("POTENTIAL SECURITY REGRESSION: quarantine was cleared by later C01 scan")
        else:
            print("No quarantine-release transition observed in this run")
    finally:
        db.close()

