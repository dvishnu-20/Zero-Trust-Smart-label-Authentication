"""
run_trials.py  -  6 scenarios x 20 trials for the Zero-Trust smart label project.

HOW TO RUN (from the project root, the folder that contains `backend/`):
    python run_trials.py

WHAT IT DOES
  * Seeds the database, then runs each scenario 20 times with a brand-new tag
    ID each trial, so trials never disturb each other.
  * Compares the returned decision (and score where fixed) with the expected
    value that is written BELOW, before any trial runs.
  * Times each call with time.perf_counter(). It calls
    evaluate_zero_trust_scan() directly, so the time covers the decision engine
    plus the database write, NOT the physical MFRC522 read and NOT HTTP.
    (If you want to time the /api/scan endpoint instead, replace `run_scan`
    with a FastAPI TestClient call; the field names depend on your schema.)
  * Writes every trial to trial_results.csv and prints a summary you can paste
    into Report 3 (Tables 6 and 7).

ASSUMPTIONS (edit if your seed data differs)
  * Employee E101 has normal PIN "1234" and duress PIN "9999" (as in your
    unit tests).
  * Checkpoints C01..C04 exist with the model fields used in security_engine.py.
"""
import csv
import datetime
import os
import statistics
import sys
import time
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import SessionLocal
from backend.models import Checkpoint, ScanHistory, Alert
from backend.security_engine import evaluate_zero_trust_scan
from backend.seed import seed_database

TRIALS = 20
EMP, PIN, DURESS_PIN = "E101", "1234", "9999"
SPEED_TEST_LIMIT = 30      # seconds; scenario 5 uses a configurable limit (Problem 4)
OLD = 60                   # seconds to push earlier scans into the past


def new_uid(tag):
    return (tag + uuid.uuid4().hex)[:10].upper()


def backdate(db, uid, seconds):
    """Make all earlier scans of this tag `seconds` old so that only the rule
    being tested can fire (otherwise speed and clone rules fire together)."""
    rows = db.query(ScanHistory).filter(ScanHistory.rfid_uid == uid).all()
    for r in rows:
        r.timestamp = datetime.datetime.utcnow() - datetime.timedelta(seconds=seconds)
    db.commit()


def run_scan(db, uid, cp, tamper=False, pin=PIN):
    """One timed scan. Returns (result, seconds)."""
    t0 = time.perf_counter()
    res = evaluate_zero_trust_scan(db=db, rfid_uid=uid, checkpoint_id=cp,
                                   tamper_detected=tamper, employee_id=EMP, pin=pin)
    return res, time.perf_counter() - t0


# ---- scenarios: each returns (result, seconds, ok, expected_text, extra) ----
def sc1(db, i):   # genuine scan
    uid = new_uid("G")
    res, dt = run_scan(db, uid, "C01")
    ok = res["decision"] == "ALLOW" and res["trust_score"] == 100
    return res, dt, ok, "ALLOW, score 100", {}

def sc2(db, i):   # tampering
    uid = new_uid("T")
    res, dt = run_scan(db, uid, "C01", tamper=True)
    ok = res["decision"] == "QUARANTINE" and res["trust_score"] == 20
    return res, dt, ok, "QUARANTINE, score 20", {}

def sc3(db, i):   # route manipulation: odd = skip, even = backtrack
    uid = new_uid("R")
    run_scan(db, uid, "C01")
    backdate(db, uid, OLD)
    if i % 2:     # skip C02: scan at C03
        res, dt = run_scan(db, uid, "C03")
        ok = res["decision"] == "FLAG" and res["trust_score"] == 65
        return res, dt, ok, "FLAG, score 65 (skip)", {}
    run_scan(db, uid, "C02")
    backdate(db, uid, OLD)
    res, dt = run_scan(db, uid, "C01")   # go back to C01 when C03 expected
    ok = res["decision"] == "FLAG" and res["trust_score"] == 75
    return res, dt, ok, "FLAG, score 75 (backtrack)", {}

def sc4(db, i):   # RFID clone: same tag at C02 straight after C01
    uid = new_uid("C")
    run_scan(db, uid, "C01")
    res, dt = run_scan(db, uid, "C02")
    ok = res["decision"] == "QUARANTINE" and res["trust_score"] == 30
    return res, dt, ok, "QUARANTINE, score 30 (speed -30 + clone -40)", {}

def sc5(db, i):   # speed rule on its own (limit for C02 set to 30 s, tag last seen 15 s ago)
    uid = new_uid("S")
    cp = db.query(Checkpoint).filter(Checkpoint.checkpoint_id == "C02").first()
    old_limit = cp.min_travel_seconds
    cp.min_travel_seconds = SPEED_TEST_LIMIT
    db.commit()
    try:
        run_scan(db, uid, "C01")
        backdate(db, uid, 15)
        res, dt = run_scan(db, uid, "C02")
    finally:
        cp = db.query(Checkpoint).filter(Checkpoint.checkpoint_id == "C02").first()
        cp.min_travel_seconds = old_limit
        db.commit()
    ok = res["decision"] == "FLAG" and res["trust_score"] == 70
    return res, dt, ok, "FLAG, score 70 (speed -30 only)", {}

def sc6(db, i):   # silent duress
    uid = new_uid("D")
    res, dt = run_scan(db, uid, "C01", pin=DURESS_PIN)
    alert = (db.query(Alert).filter(Alert.scan_id == res["scan_id"],
                                    Alert.alert_type == "SILENT_DURESS").first())
    ok = (res["decision"] == "ALLOW" and res["display_status"] == "ALLOW (VERIFIED)"
          and res["is_duress"] and alert is not None)
    return res, dt, ok, "ALLOW on screen + SILENT_DURESS alert in log", {}


SCENARIOS = [
    (1, "Genuine scan, in order, seal closed", sc1),
    (2, "Package tampering (seal open)", sc2),
    (3, "Route manipulation (skip / backtrack)", sc3),
    (4, "RFID cloning (same UID at two checkpoints)", sc4),
    (5, "Suspicious travel speed", sc5),
    (6, "Silent duress PIN", sc6),
]


def main():
    seed_database()
    db = SessionLocal()
    rows, summary = [], []
    r3_false_alerts = 0      # R-3: TAMPER_DETECTED on untouched-seal scans (scenario 1)
    r5_bad = 0               # R-5: scans that did not add exactly one history row
    r4_ok = 0                # R-4: duress hidden in every trial

    for num, name, fn in SCENARIOS:
        correct, times = 0, []
        for i in range(1, TRIALS + 1):
            before = db.query(ScanHistory).count()
            res, dt, ok, expected, _ = fn(db, i)
            after = db.query(ScanHistory).count()
            correct += ok
            times.append(dt)
            if num == 1:
                a = db.query(Alert).filter(Alert.scan_id == res["scan_id"],
                                           Alert.alert_type == "TAMPER_DETECTED").count()
                r3_false_alerts += a
            if num == 6 and ok:
                r4_ok += 1
            rows.append([num, name, i, expected, res["decision"], res["trust_score"],
                         "PASS" if ok else "FAIL", round(dt, 4), after - before])
        summary.append((num, name, correct, statistics.mean(times), max(times)))

    # R-5: every scan in the "single scan" scenarios should add exactly one row.
    # Scenarios with set-up scans add 2-3 rows per trial, so R-5 is checked on 1, 2 and 6.
    for r in rows:
        if r[0] in (1, 2, 6) and r[8] != 1:
            r5_bad += 1

    with open("trial_results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["scenario", "name", "trial", "expected", "decision", "score",
                    "result", "seconds", "new_history_rows"])
        w.writerows(rows)

    total = sum(s[2] for s in summary)
    print("\nTable 6 - Results per scenario")
    print("%-3s %-45s %6s %8s %12s %10s" % ("#", "Scenario", "Trials", "Correct", "Mean (s)", "Max (s)"))
    for num, name, c, mean, mx in summary:
        print("%-3d %-45s %6d %8d %12.3f %10.3f" % (num, name, TRIALS, c, mean, mx))
    print("\nTotal correct: %d of %d" % (total, TRIALS * len(SCENARIOS)))
    print("\nTable 7 - Requirements")
    print("R-1 correctness      : %d of %d" % (total, TRIALS * len(SCENARIOS)))
    print("R-2 response time    : slowest single trial = %.3f s (benchmark < 2 s)" %
          max(s[4] for s in summary))
    print("R-3 false tamper     : %d false TAMPER_DETECTED alerts in %d untouched-seal scans" %
          (r3_false_alerts, TRIALS))
    print("R-4 duress hidden    : %d of %d trials" % (r4_ok, TRIALS))
    print("R-5 one row per scan : %d scans with a wrong row count (checked on scenarios 1, 2, 6)" % r5_bad)
    print("\nPer-trial log written to trial_results.csv")
    db.close()


if __name__ == "__main__":
    main()
