import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text
from backend.database import Base

class Product(Base):
    __tablename__ = "products"

    product_id = Column(String, primary_key=True, index=True) # e.g. P1001
    product_name = Column(String, nullable=False)
    rfid_uid = Column(String, unique=True, index=True, nullable=False) # e.g. A1B2C3D4
    manufacturer = Column(String, nullable=False)
    status = Column(String, default="ALLOW") # ALLOW, FLAG, QUARANTINE
    current_checkpoint_id = Column(String, ForeignKey("checkpoints.checkpoint_id"), nullable=True)
    expected_next_checkpoint_id = Column(String, ForeignKey("checkpoints.checkpoint_id"), nullable=True)
    registered_at = Column(DateTime, default=datetime.datetime.utcnow)

class Checkpoint(Base):
    __tablename__ = "checkpoints"

    checkpoint_id = Column(String, primary_key=True, index=True) # C01, C02, C03, C04
    checkpoint_name = Column(String, nullable=False) # Manufacturer, Warehouse, Distributor, Retailer
    location = Column(String, nullable=False)
    sequence_order = Column(Integer, nullable=False) # 1, 2, 3, 4
    min_travel_seconds = Column(Integer, default=5) # minimum expected travel time from previous node
    max_travel_seconds = Column(Integer, default=86400) # maximum expected travel time (24h)

class Employee(Base):
    __tablename__ = "employees"

    employee_id = Column(String, primary_key=True, index=True) # E101
    name = Column(String, nullable=False)
    normal_pin = Column(String, nullable=False) # "1234"
    duress_pin = Column(String, nullable=False) # "9999"
    assigned_checkpoint_id = Column(String, ForeignKey("checkpoints.checkpoint_id"), nullable=True)

class ScanHistory(Base):
    __tablename__ = "scan_history"

    scan_id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String, nullable=True, index=True)
    rfid_uid = Column(String, nullable=False, index=True)
    checkpoint_id = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    tamper_detected = Column(Boolean, default=False)
    employee_id = Column(String, nullable=True)
    is_duress = Column(Boolean, default=False)
    trust_score = Column(Integer, nullable=False) # 0 to 100
    decision = Column(String, nullable=False) # ALLOW, FLAG, QUARANTINE
    violation_details = Column(Text, nullable=True) # JSON list or comma separated string of violations

class Alert(Base):
    __tablename__ = "alerts"

    alert_id = Column(Integer, primary_key=True, autoincrement=True)
    scan_id = Column(Integer, ForeignKey("scan_history.scan_id"), nullable=True)
    alert_type = Column(String, nullable=False) # RFID_CLONE, TAMPER_DETECTED, ROUTE_VIOLATION, IMPOSSIBLE_TRAVEL_SPEED, SILENT_DURESS, UNREGISTERED_RFID
    description = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    severity = Column(String, default="HIGH") # CRITICAL, HIGH, MEDIUM, LOW
    acknowledged = Column(Boolean, default=False)
