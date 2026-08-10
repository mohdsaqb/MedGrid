"""
Manual exercise script for Module 2 - not part of the application.

Demonstrates INSERT / SELECT / UPDATE / DELETE and transaction rollback
against the real `patients` table, using the same Session machinery
the FastAPI app will use starting Module 4.

Run with: python -m scripts.db_playground
"""

from datetime import date

from app.database.session import SessionLocal
from app.models.patient import Patient


def main() -> None:
    db = SessionLocal()

    print("\n--- INSERT ---")
    patient = Patient(
        first_name="Ayesha",
        last_name="Khan",
        date_of_birth=date(1990, 4, 12),
        email="ayesha.khan@example.com",
        phone_number="+92-300-1234567",
        mrn="MRN-000123",
    )
    db.add(patient)
    db.commit()  # writes the row and ends the transaction
    db.refresh(patient)  # reload server-generated fields (id, created_at, ...)
    print(f"Inserted: {patient}")
    print(f"  id={patient.id}")
    print(f"  created_at={patient.created_at}")

    print("\n--- SELECT ---")
    found = db.query(Patient).filter(Patient.mrn == "MRN-000123").one()
    print(f"Found by MRN: {found}")

    print("\n--- UPDATE ---")
    found.phone_number = "+92-300-9999999"
    db.commit()
    db.refresh(found)
    print(f"Updated phone_number: {found.phone_number}")
    print(f"  updated_at is now: {found.updated_at}")

    print("\n--- Transaction ROLLBACK demonstration ---")
    bad_patient = Patient(
        first_name="Test",
        last_name="Rollback",
        date_of_birth=date(2000, 1, 1),
        phone_number="+92-300-0000000",
        mrn="MRN-000123",  # duplicate MRN on purpose - violates UNIQUE constraint
    )
    db.add(bad_patient)
    try:
        db.commit()
    except Exception as exc:
        print(f"Commit failed as expected: {type(exc).__name__}")
        db.rollback()  # required before the session can be used again
        print("Rolled back. Session is usable again.")

    still_one = db.query(Patient).filter(Patient.last_name == "Rollback").count()
    print(f"Rows with last_name='Rollback' after rollback: {still_one} (should be 0)")

    print("\n--- DELETE ---")
    db.delete(found)
    db.commit()
    remaining = db.query(Patient).filter(Patient.mrn == "MRN-000123").count()
    print(f"Rows with mrn='MRN-000123' after delete: {remaining} (should be 0)")

    db.close()


if __name__ == "__main__":
    main()
