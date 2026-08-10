"""expand patients table for module 4

Revision ID: 30b334618e49
Revises: 49c69d4f3076
Create Date: 2026-08-10 14:55:11.632003

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '30b334618e49'
down_revision: Union[str, Sequence[str], None] = '49c69d4f3076'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


patient_gender = sa.Enum("MALE", "FEMALE", "OTHER", "UNKNOWN", name="patient_gender")
patient_blood_group = sa.Enum(
    "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", name="patient_blood_group"
)


def upgrade() -> None:
    """Upgrade schema."""
    # Renames preserve existing data and the underlying unique index/constraint -
    # Postgres tracks columns by internal attnum, not name, so the rename is safe.
    # (The constraint itself keeps its old name, e.g. "patients_mrn_key" -
    # cosmetic only, not worth a separate rename.)
    op.alter_column("patients", "mrn", new_column_name="patient_number")
    op.alter_column("patients", "phone_number", new_column_name="phone")

    # Sequence backing patient_number generation (see patient_service.py).
    # Atomic under concurrent inserts, unlike a hand-rolled MAX(...)+1 query.
    op.execute("CREATE SEQUENCE IF NOT EXISTS patient_number_seq START WITH 1")

    patient_gender.create(op.get_bind())
    patient_blood_group.create(op.get_bind())

    op.add_column("patients", sa.Column("gender", patient_gender, nullable=True))
    op.add_column("patients", sa.Column("address", sa.Text(), nullable=True))
    op.add_column(
        "patients", sa.Column("blood_group", patient_blood_group, nullable=True)
    )
    op.create_index(op.f("ix_patients_phone"), "patients", ["phone"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_patients_phone"), table_name="patients")
    op.drop_column("patients", "blood_group")
    op.drop_column("patients", "address")
    op.drop_column("patients", "gender")

    patient_blood_group.drop(op.get_bind())
    patient_gender.drop(op.get_bind())

    op.execute("DROP SEQUENCE IF EXISTS patient_number_seq")

    op.alter_column("patients", "phone", new_column_name="phone_number")
    op.alter_column("patients", "patient_number", new_column_name="mrn")
