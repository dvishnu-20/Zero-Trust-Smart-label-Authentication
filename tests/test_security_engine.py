import os
import sys
import unittest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import engine, Base, SessionLocal
from backend.models import Checkpoint, Product, Employee, ScanHistory, Alert
from backend.security_engine import evaluate_zero_trust_scan
from backend.seed import seed_database

class TestZeroTrustSecurityEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create schema and seed test data
        seed_database()

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_01_normal_valid_scan(self):
        """Valid RFID + correct sequential route -> ALLOW (Score >= 80)"""
        res = evaluate_zero_trust_scan(
            db=self.db,
            rfid_uid="A1B2C3D4", # P1001
            checkpoint_id="C01",
            tamper_detected=False,
            employee_id="E101",
            pin="1234"
        )
        self.assertEqual(res["decision"], "ALLOW")
        self.assertGreaterEqual(res["trust_score"], 80)
        self.assertEqual(res["tamper_detected"], False)
        self.assertEqual(res["led"], "GREEN")

    def test_02_unregistered_rfid(self):
        """Unknown RFID UID -> QUARANTINE (Score = 0)"""
        res = evaluate_zero_trust_scan(
            db=self.db,
            rfid_uid="DEADBEEF99",
            checkpoint_id="C01",
            tamper_detected=False,
            employee_id="E101",
            pin="1234"
        )
        self.assertEqual(res["decision"], "QUARANTINE")
        self.assertEqual(res["trust_score"], 0)
        self.assertEqual(res["led"], "RED")
        self.assertTrue(any("UNREGISTERED_RFID" in v for v in res["violations"]))

    def test_03_physical_tamper_detection(self):
        """Valid RFID + Broken tamper loop -> QUARANTINE"""
        res = evaluate_zero_trust_scan(
            db=self.db,
            rfid_uid="E5F6G7H8", # P1002
            checkpoint_id="C01",
            tamper_detected=True,
            employee_id="E101",
            pin="1234"
        )
        self.assertEqual(res["decision"], "QUARANTINE")
        self.assertTrue(res["tamper_detected"])
        self.assertEqual(res["led"], "RED")
        self.assertTrue(any("PACKAGE_TAMPERED" in v for v in res["violations"]))

    def test_04_route_violation(self):
        """Skipping required checkpoint -> FLAG (Route Violation)"""
        # P1003 expects C01 first, but we scan at C03 directly
        res = evaluate_zero_trust_scan(
            db=self.db,
            rfid_uid="99887766", # P1003
            checkpoint_id="C03",
            tamper_detected=False,
            employee_id="E103",
            pin="1234"
        )
        self.assertIn(res["decision"], ["FLAG", "QUARANTINE"])
        self.assertTrue(any("ROUTE_VIOLATION" in v for v in res["violations"]))

    def test_05_silent_duress_mechanism(self):
        """Duress PIN '9999' -> Triggers is_duress=True, generates silent alert"""
        res = evaluate_zero_trust_scan(
            db=self.db,
            rfid_uid="11223344", # P1004
            checkpoint_id="C01",
            tamper_detected=False,
            employee_id="E101",
            pin="9999" # Duress PIN
        )
        self.assertTrue(res["is_duress"])
        self.assertTrue(any("SILENT_DURESS" in v for v in res["violations"]))
        # Check database for Silent Duress alert
        alert = self.db.query(Alert).filter(Alert.alert_type == "SILENT_DURESS").first()
        self.assertIsNotNone(alert)
        self.assertEqual(alert.severity, "CRITICAL")

if __name__ == "__main__":
    unittest.main()
