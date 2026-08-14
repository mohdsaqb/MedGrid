"""
Dummy data seeder - populates every table with 4-5 realistic rows for
local demos/manual testing. Safe to re-run: each section skips rows that
already exist (matched by their natural unique key) instead of erroring.

Run with: python -m scripts.seed_data
"""

from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import func

from app.database.session import SessionLocal
from app.models.appointment import Appointment, AppointmentStatus
from app.models.clinical_record import ClinicalRecord, RecordType
from app.models.doctor import Doctor
from app.models.encounter import Encounter, EncounterStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.models.lab_order import LabOrder, LabStatus
from app.models.lab_result import LabResult
from app.models.lab_test import LabTest
from app.models.patient import Gender, Patient
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.models.user import User, UserRole
from app.utils.password import hash_password


def seed_users(db) -> list[User]:
    rows = [
        dict(
            email="admin@medgrid.example",
            full_name="Grace Thompson",
            role=UserRole.ADMIN,
        ),
        dict(
            email="doctor@medgrid.example",
            full_name="James Anderson",
            role=UserRole.DOCTOR,
        ),
        dict(
            email="patient@medgrid.example",
            full_name="Emily Carter",
            role=UserRole.PATIENT,
        ),
        dict(
            email="labtech@medgrid.example",
            full_name="Kevin Brooks",
            role=UserRole.LAB_TECHNICIAN,
        ),
        dict(
            email="billing@medgrid.example",
            full_name="Rachel Adams",
            role=UserRole.BILLING_STAFF,
        ),
    ]
    users = []
    for row in rows:
        existing = db.query(User).filter(User.email == row["email"]).one_or_none()
        if existing:
            users.append(existing)
            continue
        user = User(hashed_password=hash_password("Password123!"), **row)
        db.add(user)
        users.append(user)
    db.commit()
    for user in users:
        db.refresh(user)
    return users


def seed_doctors(db) -> list[Doctor]:
    rows = [
        dict(
            name="Dr. James Anderson",
            specialization="Cardiology",
            department="Cardiology",
            license_number="LIC-10001",
            email="j.anderson@medgrid.example",
            phone="+1-312-555-0101",
        ),
        dict(
            name="Dr. Laura Bennett",
            specialization="Pediatrics",
            department="Pediatrics",
            license_number="LIC-10002",
            email="l.bennett@medgrid.example",
            phone="+1-312-555-0102",
        ),
        dict(
            name="Dr. Robert Clark",
            specialization="Orthopedics",
            department="Orthopedics",
            license_number="LIC-10003",
            email="r.clark@medgrid.example",
            phone="+1-312-555-0103",
        ),
        dict(
            name="Dr. Emily Turner",
            specialization="Dermatology",
            department="Dermatology",
            license_number="LIC-10004",
            email="e.turner@medgrid.example",
            phone="+1-312-555-0104",
        ),
        dict(
            name="Dr. Daniel Walker",
            specialization="Neurology",
            department="Neurology",
            license_number="LIC-10005",
            email="d.walker@medgrid.example",
            phone="+1-312-555-0105",
        ),
    ]
    doctors = []
    for row in rows:
        existing = db.query(Doctor).filter(Doctor.email == row["email"]).one_or_none()
        if existing:
            doctors.append(existing)
            continue
        doctor = Doctor(**row)
        db.add(doctor)
        doctors.append(doctor)
    db.commit()
    for doctor in doctors:
        db.refresh(doctor)
    return doctors


def seed_patients(db) -> list[Patient]:
    rows = [
        dict(
            first_name="Emily",
            last_name="Carter",
            date_of_birth=date(1990, 4, 12),
            gender=Gender.FEMALE,
            email="emily.carter@example.com",
            phone="+1-415-555-0111",
            address="221 Maple Street, Springfield, IL",
        ),
        dict(
            first_name="Michael",
            last_name="Johnson",
            date_of_birth=date(1985, 9, 3),
            gender=Gender.MALE,
            email="michael.johnson@example.com",
            phone="+1-415-555-0112",
            address="48 Oak Avenue, Springfield, IL",
        ),
        dict(
            first_name="Sarah",
            last_name="Williams",
            date_of_birth=date(1998, 1, 27),
            gender=Gender.FEMALE,
            email="sarah.williams@example.com",
            phone="+1-415-555-0113",
            address="90 Birch Lane, Springfield, IL",
        ),
        dict(
            first_name="David",
            last_name="Brown",
            date_of_birth=date(1975, 6, 30),
            gender=Gender.MALE,
            email="david.brown@example.com",
            phone="+1-415-555-0114",
            address="12 Cedar Court, Springfield, IL",
        ),
        dict(
            first_name="Jessica",
            last_name="Miller",
            date_of_birth=date(2001, 11, 15),
            gender=Gender.FEMALE,
            email="jessica.miller@example.com",
            phone="+1-415-555-0115",
            address="305 Elm Drive, Springfield, IL",
        ),
    ]
    patients = []
    for row in rows:
        existing = db.query(Patient).filter(Patient.email == row["email"]).one_or_none()
        if existing:
            patients.append(existing)
            continue
        next_val = db.execute(func.nextval("patient_number_seq")).scalar_one()
        patient = Patient(patient_number=f"PT-{next_val:06d}", **row)
        db.add(patient)
        patients.append(patient)
    db.commit()
    for patient in patients:
        db.refresh(patient)
    return patients


def seed_appointments(db, patients: list[Patient], doctors: list[Doctor]) -> list[Appointment]:
    rows = [
        dict(
            patient=patients[0],
            doctor=doctors[0],
            appointment_date=date.today() + timedelta(days=3),
            appointment_time=time(9, 0),
            reason="Annual cardiac checkup",
            status=AppointmentStatus.SCHEDULED,
        ),
        dict(
            patient=patients[1],
            doctor=doctors[1],
            appointment_date=date.today() + timedelta(days=4),
            appointment_time=time(10, 30),
            reason="Child wellness visit",
            status=AppointmentStatus.SCHEDULED,
        ),
        dict(
            patient=patients[2],
            doctor=doctors[2],
            appointment_date=date.today() - timedelta(days=2),
            appointment_time=time(14, 0),
            reason="Knee pain follow-up",
            status=AppointmentStatus.COMPLETED,
        ),
        dict(
            patient=patients[3],
            doctor=doctors[3],
            appointment_date=date.today() - timedelta(days=5),
            appointment_time=time(11, 15),
            reason="Skin rash evaluation",
            status=AppointmentStatus.COMPLETED,
        ),
        dict(
            patient=patients[4],
            doctor=doctors[4],
            appointment_date=date.today() + timedelta(days=1),
            appointment_time=time(15, 45),
            reason="Recurring migraine consultation",
            status=AppointmentStatus.CANCELLED,
        ),
    ]
    appointments = []
    for row in rows:
        existing = (
            db.query(Appointment)
            .filter(
                Appointment.patient_id == row["patient"].id,
                Appointment.doctor_id == row["doctor"].id,
                Appointment.appointment_date == row["appointment_date"],
                Appointment.appointment_time == row["appointment_time"],
            )
            .one_or_none()
        )
        if existing:
            appointments.append(existing)
            continue
        appointment = Appointment(
            patient_id=row["patient"].id,
            doctor_id=row["doctor"].id,
            appointment_date=row["appointment_date"],
            appointment_time=row["appointment_time"],
            reason=row["reason"],
            status=row["status"],
        )
        db.add(appointment)
        appointments.append(appointment)
    db.commit()
    for appointment in appointments:
        db.refresh(appointment)
    return appointments


def seed_encounters(
    db, patients: list[Patient], doctors: list[Doctor], appointments: list[Appointment]
) -> list[Encounter]:
    rows = [
        dict(
            patient=patients[2],
            doctor=doctors[2],
            appointment=appointments[2],
            encounter_date=datetime.now() - timedelta(days=2),
            diagnosis="Mild patellar tendinitis",
            symptoms="Knee pain on stairs, mild swelling",
            notes="Recommended rest and physical therapy for 2 weeks.",
            status=EncounterStatus.CLOSED,
        ),
        dict(
            patient=patients[3],
            doctor=doctors[3],
            appointment=appointments[3],
            encounter_date=datetime.now() - timedelta(days=5),
            diagnosis="Contact dermatitis",
            symptoms="Localized redness and itching on forearm",
            notes="Prescribed topical corticosteroid cream.",
            status=EncounterStatus.CLOSED,
        ),
        dict(
            patient=patients[0],
            doctor=doctors[0],
            appointment=None,
            encounter_date=datetime.now() - timedelta(days=10),
            diagnosis="Hypertension, well controlled",
            symptoms="Routine follow-up, no acute complaints",
            notes="Continue current medication, recheck in 6 months.",
            status=EncounterStatus.CLOSED,
        ),
        dict(
            patient=patients[1],
            doctor=doctors[1],
            appointment=None,
            encounter_date=datetime.now() - timedelta(days=1),
            diagnosis="Seasonal allergic rhinitis",
            symptoms="Sneezing, nasal congestion",
            notes=None,
            status=EncounterStatus.OPEN,
        ),
    ]
    encounters = []
    for row in rows:
        existing = (
            db.query(Encounter)
            .filter(
                Encounter.patient_id == row["patient"].id,
                Encounter.doctor_id == row["doctor"].id,
                Encounter.diagnosis == row["diagnosis"],
            )
            .one_or_none()
        )
        if existing:
            encounters.append(existing)
            continue
        encounter = Encounter(
            patient_id=row["patient"].id,
            doctor_id=row["doctor"].id,
            appointment_id=row["appointment"].id if row["appointment"] else None,
            encounter_date=row["encounter_date"],
            diagnosis=row["diagnosis"],
            symptoms=row["symptoms"],
            notes=row["notes"],
            status=row["status"],
        )
        db.add(encounter)
        encounters.append(encounter)
    db.commit()
    for encounter in encounters:
        db.refresh(encounter)
    return encounters


def seed_clinical_records(db, encounters: list[Encounter], doctor_user: User) -> list[ClinicalRecord]:
    rows = [
        dict(
            encounter=encounters[0],
            record_type=RecordType.DIAGNOSIS,
            description="Patellar tendinitis, right knee, mild.",
        ),
        dict(
            encounter=encounters[0],
            record_type=RecordType.PRESCRIPTION,
            description="Ibuprofen 400mg, twice daily with food, 7 days.",
        ),
        dict(
            encounter=encounters[1],
            record_type=RecordType.DIAGNOSIS,
            description="Contact dermatitis, left forearm.",
        ),
        dict(
            encounter=encounters[2],
            record_type=RecordType.VITALS,
            description="BP 128/82, HR 76, Temp 98.4F.",
        ),
        dict(
            encounter=encounters[3],
            record_type=RecordType.GENERAL_NOTE,
            description="Patient reports symptoms worsen outdoors; advised antihistamines.",
        ),
    ]
    records = []
    for row in rows:
        existing = (
            db.query(ClinicalRecord)
            .filter(
                ClinicalRecord.encounter_id == row["encounter"].id,
                ClinicalRecord.description == row["description"],
            )
            .one_or_none()
        )
        if existing:
            records.append(existing)
            continue
        record = ClinicalRecord(
            encounter_id=row["encounter"].id,
            record_type=row["record_type"],
            description=row["description"],
            created_by_user_id=doctor_user.id,
        )
        db.add(record)
        records.append(record)
    db.commit()
    for record in records:
        db.refresh(record)
    return records


def seed_lab_tests(db) -> list[LabTest]:
    rows = [
        dict(
            name="Complete Blood Count (CBC)",
            description="Measures red cells, white cells, and platelets.",
            price=Decimal("25.00"),
            normal_range="4.5-11.0 x10^9/L (WBC)",
        ),
        dict(
            name="Lipid Panel",
            description="Cholesterol and triglyceride levels.",
            price=Decimal("40.00"),
            normal_range="Total cholesterol < 200 mg/dL",
        ),
        dict(
            name="Blood Glucose (Fasting)",
            description="Fasting blood sugar level.",
            price=Decimal("15.00"),
            normal_range="70-99 mg/dL",
        ),
        dict(
            name="Urinalysis",
            description="General urine screening panel.",
            price=Decimal("20.00"),
            normal_range="Negative for protein, glucose, blood",
        ),
        dict(
            name="Thyroid Stimulating Hormone (TSH)",
            description="Screens for thyroid function.",
            price=Decimal("35.00"),
            normal_range="0.4-4.0 mIU/L",
        ),
    ]
    tests = []
    for row in rows:
        existing = db.query(LabTest).filter(LabTest.name == row["name"]).one_or_none()
        if existing:
            tests.append(existing)
            continue
        test = LabTest(**row)
        db.add(test)
        tests.append(test)
    db.commit()
    for test in tests:
        db.refresh(test)
    return tests


def seed_lab_orders(
    db, patients: list[Patient], doctors: list[Doctor], tests: list[LabTest]
) -> list[LabOrder]:
    rows = [
        dict(patient=patients[0], doctor=doctors[0], test=tests[1], status=LabStatus.COMPLETED),
        dict(patient=patients[1], doctor=doctors[1], test=tests[0], status=LabStatus.COMPLETED),
        dict(patient=patients[2], doctor=doctors[2], test=tests[2], status=LabStatus.PROCESSING),
        dict(patient=patients[3], doctor=doctors[3], test=tests[3], status=LabStatus.PENDING),
        dict(patient=patients[4], doctor=doctors[4], test=tests[4], status=LabStatus.COMPLETED),
    ]
    orders = []
    for row in rows:
        existing = (
            db.query(LabOrder)
            .filter(
                LabOrder.patient_id == row["patient"].id,
                LabOrder.test_id == row["test"].id,
            )
            .one_or_none()
        )
        if existing:
            orders.append(existing)
            continue
        order = LabOrder(
            patient_id=row["patient"].id,
            doctor_id=row["doctor"].id,
            test_id=row["test"].id,
            status=row["status"],
        )
        db.add(order)
        orders.append(order)
    db.commit()
    for order in orders:
        db.refresh(order)
    return orders


def seed_lab_results(db, orders: list[LabOrder]) -> list[LabResult]:
    rows = [
        dict(order=orders[0], result="185", unit="mg/dL", reference_range="< 200 mg/dL"),
        dict(order=orders[1], result="6.8", unit="x10^9/L", reference_range="4.5-11.0 x10^9/L"),
        dict(order=orders[4], result="2.1", unit="mIU/L", reference_range="0.4-4.0 mIU/L"),
    ]
    results = []
    for row in rows:
        existing = (
            db.query(LabResult).filter(LabResult.lab_order_id == row["order"].id).one_or_none()
        )
        if existing:
            results.append(existing)
            continue
        result = LabResult(
            lab_order_id=row["order"].id,
            result=row["result"],
            unit=row["unit"],
            reference_range=row["reference_range"],
            status=LabStatus.COMPLETED,
        )
        db.add(result)
        results.append(result)
    db.commit()
    for result in results:
        db.refresh(result)
    return results


def seed_invoices(db, patients: list[Patient], appointments: list[Appointment]) -> list[Invoice]:
    rows = [
        dict(patient=patients[0], appointment=appointments[0], amount=Decimal("150.00")),
        dict(patient=patients[1], appointment=appointments[1], amount=Decimal("90.00")),
        dict(patient=patients[2], appointment=appointments[2], amount=Decimal("120.00")),
        dict(patient=patients[3], appointment=appointments[3], amount=Decimal("75.00")),
        dict(patient=patients[4], appointment=None, amount=Decimal("35.00")),
    ]
    invoices = []
    for row in rows:
        existing = (
            db.query(Invoice)
            .filter(
                Invoice.patient_id == row["patient"].id,
                Invoice.amount == row["amount"],
            )
            .one_or_none()
        )
        if existing:
            invoices.append(existing)
            continue
        invoice = Invoice(
            patient_id=row["patient"].id,
            appointment_id=row["appointment"].id if row["appointment"] else None,
            amount=row["amount"],
        )
        db.add(invoice)
        invoices.append(invoice)
    db.commit()
    for invoice in invoices:
        db.refresh(invoice)
    return invoices


def seed_payments(db, invoices: list[Invoice], billing_user: User) -> list[Payment]:
    rows = [
        dict(
            invoice=invoices[0],
            amount=Decimal("150.00"),
            method=PaymentMethod.CARD,
            status=PaymentStatus.SUCCESS,
        ),
        dict(
            invoice=invoices[1],
            amount=Decimal("90.00"),
            method=PaymentMethod.CASH,
            status=PaymentStatus.SUCCESS,
        ),
        dict(
            invoice=invoices[2],
            amount=Decimal("60.00"),
            method=PaymentMethod.BANK_TRANSFER,
            status=PaymentStatus.SUCCESS,
        ),
        dict(
            invoice=invoices[3],
            amount=Decimal("75.00"),
            method=PaymentMethod.CARD,
            status=PaymentStatus.FAILED,
        ),
        dict(
            invoice=invoices[4],
            amount=Decimal("35.00"),
            method=PaymentMethod.CASH,
            status=PaymentStatus.PENDING,
        ),
    ]
    payments = []
    for row in rows:
        existing = (
            db.query(Payment)
            .filter(
                Payment.invoice_id == row["invoice"].id,
                Payment.amount == row["amount"],
                Payment.payment_method == row["method"],
            )
            .one_or_none()
        )
        if existing:
            payments.append(existing)
            continue
        payment = Payment(
            invoice_id=row["invoice"].id,
            amount=row["amount"],
            payment_method=row["method"],
            payment_status=row["status"],
            paid_at=datetime.now() if row["status"] == PaymentStatus.SUCCESS else None,
            recorded_by_user_id=billing_user.id,
        )
        db.add(payment)
        payments.append(payment)
    db.commit()
    for payment in payments:
        db.refresh(payment)
    return payments


def main() -> None:
    db = SessionLocal()
    try:
        users = seed_users(db)
        doctor_user = next(u for u in users if u.role == UserRole.DOCTOR)
        billing_user = next(u for u in users if u.role == UserRole.BILLING_STAFF)

        doctors = seed_doctors(db)
        patients = seed_patients(db)
        appointments = seed_appointments(db, patients, doctors)
        encounters = seed_encounters(db, patients, doctors, appointments)
        seed_clinical_records(db, encounters, doctor_user)

        tests = seed_lab_tests(db)
        orders = seed_lab_orders(db, patients, doctors, tests)
        seed_lab_results(db, orders)

        invoices = seed_invoices(db, patients, appointments)
        seed_payments(db, invoices, billing_user)

        print("Seed data applied:")
        print(f"  users:            {len(users)}")
        print(f"  doctors:          {len(doctors)}")
        print(f"  patients:         {len(patients)}")
        print(f"  appointments:     {len(appointments)}")
        print(f"  encounters:       {len(encounters)}")
        print(f"  lab_tests:        {len(tests)}")
        print(f"  lab_orders:       {len(orders)}")
        print(f"  invoices:         {len(invoices)}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
