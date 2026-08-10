"""
Reporting queries, written in raw SQL via SQLAlchemy's text() rather than
the ORM query builder - a deliberate departure from every other service
in this codebase. Reporting queries are read-only, multi-table
aggregations where the ORM's object-mapping layer adds no value and
often obscures exactly what's being asked of the database. When a query
IS the point (as it is in this whole module), writing it directly is
clearer and easier to reason about and tune - a preview of Module 11's
SQL optimization focus.
"""

from datetime import date, timedelta

from sqlalchemy import text
from sqlalchemy.orm import Session


def _trailing_window(days: int) -> tuple[date, date]:
    """
    Half-open interval [start, end) looking BACKWARD from today - see
    Part A on why not BETWEEN. Correct for data that only ever happens in
    the past/present, like payments.
    """
    end = date.today() + timedelta(days=1)
    start = end - timedelta(days=days + 1)
    return start, end


def _upcoming_window(days: int) -> tuple[date, date]:
    """
    Half-open interval [start, end) looking FORWARD from today. Correct
    for appointments specifically: Module 5's own business rule requires
    appointment_date >= today at booking time, so a BACKWARD-looking
    window would always be empty by construction - this isn't a
    hypothetical, it's what actually happens with this project's real
    data. The right window direction depends on the data's temporal
    nature, not a single generic "last N days" pattern applied everywhere.
    """
    start = date.today()
    end = start + timedelta(days=days)
    return start, end


def get_patients_report(db: Session) -> dict:
    total_patients = db.execute(text("SELECT COUNT(*) FROM patients")).scalar_one()

    # gender is a native Postgres ENUM column - cast to text before
    # COALESCE, which requires matching/compatible types.
    by_gender = db.execute(
        text(
            """
            SELECT COALESCE(gender::text, 'UNKNOWN') AS gender, COUNT(*) AS count
            FROM patients
            GROUP BY gender
            ORDER BY count DESC
            """
        )
    ).mappings().all()

    # LEFT JOIN from doctors: a department with doctors but zero
    # appointments must still be considered, not silently dropped. HAVING
    # then filters the resulting groups (not raw rows) to hide departments
    # with no patient traffic at all from THIS particular chart - a
    # deliberate choice, not something WHERE could express (COUNT doesn't
    # exist until after grouping).
    by_department = db.execute(
        text(
            """
            SELECT d.department, COUNT(DISTINCT a.patient_id) AS patient_count
            FROM doctors d
            LEFT JOIN appointments a ON a.doctor_id = d.id
            GROUP BY d.department
            HAVING COUNT(DISTINCT a.patient_id) > 0
            ORDER BY patient_count DESC
            """
        )
    ).mappings().all()

    return {
        "total_patients": total_patients,
        "patients_by_gender": list(by_gender),
        "patients_by_department": list(by_department),
    }


def get_appointments_report(db: Session, days: int) -> dict:
    total_appointments = db.execute(text("SELECT COUNT(*) FROM appointments")).scalar_one()

    by_status = db.execute(
        text(
            """
            SELECT status::text AS status, COUNT(*) AS count
            FROM appointments
            GROUP BY status
            ORDER BY count DESC
            """
        )
    ).mappings().all()

    start, end = _upcoming_window(days)
    by_day = db.execute(
        text(
            """
            SELECT appointment_date AS day, COUNT(*) AS count
            FROM appointments
            WHERE appointment_date >= :start AND appointment_date < :end
            GROUP BY appointment_date
            ORDER BY appointment_date
            """
        ),
        {"start": start, "end": end},
    ).mappings().all()

    return {
        "total_appointments": total_appointments,
        "appointments_by_status": list(by_status),
        "appointments_by_day": list(by_day),
    }


def get_labs_report(db: Session) -> dict:
    total_orders = db.execute(text("SELECT COUNT(*) FROM lab_orders")).scalar_one()

    by_status = db.execute(
        text(
            """
            SELECT status::text AS status, COUNT(*) AS count
            FROM lab_orders
            GROUP BY status
            ORDER BY count DESC
            """
        )
    ).mappings().all()
    completed_tests = next((row["count"] for row in by_status if row["status"] == "COMPLETED"), 0)

    pending_orders = db.execute(
        text(
            """
            SELECT
                lo.id::text AS id,
                p.first_name || ' ' || p.last_name AS patient_name,
                d.name AS doctor_name,
                lt.name AS test_name,
                lo.ordered_at::text AS ordered_at
            FROM lab_orders lo
            JOIN patients p ON p.id = lo.patient_id
            JOIN doctors d ON d.id = lo.doctor_id
            JOIN lab_tests lt ON lt.id = lo.test_id
            WHERE lo.status = 'PENDING'
            ORDER BY lo.ordered_at ASC
            LIMIT 50
            """
        )
    ).mappings().all()

    return {
        "total_orders": total_orders,
        "orders_by_status": list(by_status),
        "completed_tests": completed_tests,
        "pending_orders": list(pending_orders),
    }


def get_revenue_report(db: Session, days: int) -> dict:
    totals = db.execute(
        text(
            """
            WITH successful_payments AS (
                SELECT invoice_id, SUM(amount) AS paid_amount
                FROM payments
                WHERE payment_status = 'SUCCESS'
                GROUP BY invoice_id
            )
            SELECT
                COALESCE(SUM(sp.paid_amount), 0) AS total_revenue,
                COALESCE(SUM(i.amount), 0) AS total_invoiced,
                COALESCE(SUM(i.amount), 0) - COALESCE(SUM(sp.paid_amount), 0) AS outstanding_balance
            FROM invoices i
            LEFT JOIN successful_payments sp ON sp.invoice_id = i.id
            """
        )
    ).mappings().one()

    start, end = _trailing_window(days)
    by_day = db.execute(
        text(
            """
            SELECT DATE_TRUNC('day', paid_at)::date AS day, SUM(amount) AS revenue
            FROM payments
            WHERE payment_status = 'SUCCESS'
              AND paid_at >= :start AND paid_at < :end
            GROUP BY DATE_TRUNC('day', paid_at)
            ORDER BY day
            """
        ),
        {"start": start, "end": end},
    ).mappings().all()

    return {
        "total_revenue": totals["total_revenue"],
        "total_invoiced": totals["total_invoiced"],
        "outstanding_balance": totals["outstanding_balance"],
        "revenue_by_day": list(by_day),
    }


def get_doctor_performance_report(db: Session) -> dict:
    """
    The module's worked example (Part A) plus a second CTE for revenue.
    NOTE, an honest limitation: revenue here only counts invoices that
    have appointment_id set. Module 8's invoice-creation UI never links
    an appointment, so in this project's actual seed data every doctor's
    revenue will show as 0 - not a bug in this query, a real downstream
    consequence of an earlier module's scope decision.
    """
    rows = db.execute(
        text(
            """
            WITH doctor_appointments AS (
                SELECT doctor_id, COUNT(*) AS appointment_count
                FROM appointments
                GROUP BY doctor_id
            ),
            doctor_revenue AS (
                SELECT a.doctor_id, SUM(p.amount) AS revenue
                FROM appointments a
                JOIN invoices i ON i.appointment_id = a.id
                JOIN payments p ON p.invoice_id = i.id AND p.payment_status = 'SUCCESS'
                GROUP BY a.doctor_id
            )
            SELECT
                d.id::text AS id,
                d.name,
                d.specialization,
                d.department,
                COALESCE(da.appointment_count, 0) AS appointment_count,
                COALESCE(dr.revenue, 0) AS revenue
            FROM doctors d
            LEFT JOIN doctor_appointments da ON da.doctor_id = d.id
            LEFT JOIN doctor_revenue dr ON dr.doctor_id = d.id
            ORDER BY appointment_count DESC
            """
        )
    ).mappings().all()

    return {"doctors": list(rows)}
