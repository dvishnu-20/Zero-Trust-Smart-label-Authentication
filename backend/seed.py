from backend.database import engine, Base, SessionLocal
from backend.models import Checkpoint, Product, Employee, ScanHistory, Alert

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Clear existing tables for fresh seed
    db.query(Alert).delete()
    db.query(ScanHistory).delete()
    db.query(Product).delete()
    db.query(Employee).delete()
    db.query(Checkpoint).delete()
    db.commit()

    print("Seeding Checkpoints...")
    checkpoints = [
        Checkpoint(checkpoint_id="C01", checkpoint_name="Manufacturer Node", location="Factory Floor #1 (Shenzhen)", sequence_order=1, min_travel_seconds=0, max_travel_seconds=3600),
        Checkpoint(checkpoint_id="C02", checkpoint_name="Central Warehouse", location="Logistics Hub A (Hong Kong)", sequence_order=2, min_travel_seconds=5, max_travel_seconds=86400),
        Checkpoint(checkpoint_id="C03", checkpoint_name="Regional Distributor", location="Distribution Center B (Singapore)", sequence_order=3, min_travel_seconds=5, max_travel_seconds=86400),
        Checkpoint(checkpoint_id="C04", checkpoint_name="Retail Store", location="Retail Store #104 (Tokyo)", sequence_order=4, min_travel_seconds=5, max_travel_seconds=86400),
    ]
    db.add_all(checkpoints)
    db.commit()

    print("Seeding Employees...")
    employees = [
        Employee(employee_id="E101", name="Alice Smith (Manufacturer Admin)", normal_pin="1234", duress_pin="9999", assigned_checkpoint_id="C01"),
        Employee(employee_id="E102", name="Bob Jones (Warehouse Operator)", normal_pin="1234", duress_pin="9999", assigned_checkpoint_id="C02"),
        Employee(employee_id="E103", name="Charlie Brown (Distributor Admin)", normal_pin="1234", duress_pin="9999", assigned_checkpoint_id="C03"),
        Employee(employee_id="E104", name="Diana Prince (Retail Manager)", normal_pin="1234", duress_pin="9999", assigned_checkpoint_id="C04"),
    ]
    db.add_all(employees)
    db.commit()

    print("Seeding Products with Smart RFID Tags...")
    products = [
        Product(
            product_id="P1001",
            product_name="High-Grade Microprocessor Array",
            rfid_uid="72955006",
            manufacturer="Apex Semiconductor Inc.",
            status="ALLOW",
            current_checkpoint_id=None,
            expected_next_checkpoint_id="C01"
        ),
    ]
    db.add_all(products)
    db.commit()
    db.close()
    print("Database successfully seeded!")

if __name__ == "__main__":
    seed_database()
