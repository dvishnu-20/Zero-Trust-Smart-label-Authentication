import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import Base
from backend.models import Checkpoint, Product, Employee, ScanHistory, Alert
from backend.security_engine import evaluate_zero_trust_scan

# Isolated in-memory SQLite database for fast, self-contained unit tests
@pytest.fixture(scope="function")
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()

    # Seed test checkpoints
    checkpoints = [
        Checkpoint(checkpoint_id="C01", checkpoint_name="Manufacturer Node", location="Shenzhen Factory", sequence_order=1, min_travel_seconds=0),
        Checkpoint(checkpoint_id="C02", checkpoint_name="Central Warehouse", location="Hong Kong Hub", sequence_order=2, min_travel_seconds=5),
        Checkpoint(checkpoint_id="C03", checkpoint_name="Regional Distributor", location="Singapore DC", sequence_order=3, min_travel_seconds=5),
        Checkpoint(checkpoint_id="C04", checkpoint_name="Retail Store", location="Tokyo Store", sequence_order=4, min_travel_seconds=5),
    ]
    session.add_all(checkpoints)

    # Seed test employees (E101 - E104)
    employees = [
        Employee(employee_id="E101", name="Alice Smith", normal_pin="1234", duress_pin="9999", assigned_checkpoint_id="C01"),
        Employee(employee_id="E102", name="Bob Jones", normal_pin="1234", duress_pin="9999", assigned_checkpoint_id="C02"),
        Employee(employee_id="E103", name="Charlie Brown", normal_pin="1234", duress_pin="9999", assigned_checkpoint_id="C03"),
        Employee(employee_id="E104", name="Diana Prince", normal_pin="1234", duress_pin="9999", assigned_checkpoint_id="C04"),
    ]
    session.add_all(employees)

    # Seed test products
    products = [
        Product(product_id="P1001", product_name="Microprocessor Array", rfid_uid="A1B2C3D4", manufacturer="Apex Semi", status="ALLOW", expected_next_checkpoint_id="C01"),
        Product(product_id="P1002", product_name="Encryption Module", rfid_uid="E5F6G7H8", manufacturer="CipherTech", status="ALLOW", expected_next_checkpoint_id="C01"),
        Product(product_id="P1003", product_name="Sensor Array", rfid_uid="99887766", manufacturer="SensorDyne", status="ALLOW", expected_next_checkpoint_id="C01"),
        Product(product_id="P1004", product_name="Biometric Scanner", rfid_uid="11223344", manufacturer="BioSec", status="ALLOW", expected_next_checkpoint_id="C01"),
    ]
    session.add_all(products)
    session.commit()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)


def test_01_normal_valid_scan(db_session):
    """Test 1: Normal Valid Scan (Valid RFID + Correct Sequence) -> ALLOW (Trust >= 80, GREEN LED)"""
    res = evaluate_zero_trust_scan(
        db=db_session,
        rfid_uid="A1B2C3D4",
        checkpoint_id="C01",
        tamper_detected=False,
        employee_id="E101",
        pin="1234"
    )
    assert res["decision"] == "ALLOW"
    assert res["trust_score"] >= 80
    assert res["tamper_detected"] is False
    assert res["led"] == "GREEN"
    assert len(res["violations"]) == 0


def test_02_unregistered_rfid(db_session):
    """Test 2: Unregistered RFID tag at transit node -> QUARANTINE (Trust = 0, RED LED)"""
    res = evaluate_zero_trust_scan(
        db=db_session,
        rfid_uid="DEADBEEF99",
        checkpoint_id="C02",
        tamper_detected=False,
        employee_id="E102",
        pin="1234"
    )
    assert res["decision"] == "QUARANTINE"
    assert res["trust_score"] == 0
    assert res["led"] == "RED"
    assert any("UNREGISTERED_RFID" in v for v in res["violations"])


def test_03_physical_tamper_detection(db_session):
    """Test 3: Physical Tamper Detection (Tamper loop broken) -> QUARANTINE (Score -80, RED LED)"""
    res = evaluate_zero_trust_scan(
        db=db_session,
        rfid_uid="E5F6G7H8",
        checkpoint_id="C01",
        tamper_detected=True,
        employee_id="E101",
        pin="1234"
    )
    assert res["decision"] == "QUARANTINE"
    assert res["tamper_detected"] is True
    assert res["led"] == "RED"
    assert any("PACKAGE_TAMPERED" in v for v in res["violations"])


def test_04_route_violation(db_session):
    """Test 4: Route Violation (Skipped checkpoint C01 & C02 -> directly C03) -> FLAG (Score -35)"""
    res = evaluate_zero_trust_scan(
        db=db_session,
        rfid_uid="99887766",
        checkpoint_id="C03",
        tamper_detected=False,
        employee_id="E103",
        pin="1234"
    )
    assert res["decision"] in ["FLAG", "QUARANTINE"]
    assert any("ROUTE_VIOLATION" in v for v in res["violations"])


def test_05_silent_duress_mechanism(db_session):
    """Test 5: Silent Duress Emergency PIN (9999) -> Deceptive ALLOW on UI + Critical Silent Alert"""
    res = evaluate_zero_trust_scan(
        db=db_session,
        rfid_uid="11223344",
        checkpoint_id="C01",
        tamper_detected=False,
        employee_id="E101",
        pin="9999"  # Emergency Duress PIN
    )
    assert res["is_duress"] is True
    assert any("SILENT_DURESS" in v for v in res["violations"])
    
    # Verify critical covert alert created in database
    alert = db_session.query(Alert).filter(Alert.alert_type == "SILENT_DURESS").first()
    assert alert is not None
    assert alert.severity == "CRITICAL"
