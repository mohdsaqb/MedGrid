"""add get_patient_lab_summary function

Revision ID: 2f830ba7085c
Revises: d4448748e84b
Create Date: 2026-08-10 19:31:53.466153

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f830ba7085c'
down_revision: Union[str, Sequence[str], None] = 'd4448748e84b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        CREATE OR REPLACE FUNCTION get_patient_lab_summary(p_patient_id UUID)
        RETURNS TABLE (
            test_name VARCHAR,
            status TEXT,
            result VARCHAR,
            unit VARCHAR,
            reference_range VARCHAR,
            ordered_at TIMESTAMPTZ
        )
        LANGUAGE sql
        STABLE
        AS $$
            SELECT
                lt.name,
                lo.status::text,
                lr.result,
                lr.unit,
                lr.reference_range,
                lo.ordered_at
            FROM lab_orders lo
            JOIN lab_tests lt ON lt.id = lo.test_id
            LEFT JOIN lab_results lr ON lr.lab_order_id = lo.id
            WHERE lo.patient_id = p_patient_id
            ORDER BY lo.ordered_at DESC;
        $$;
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP FUNCTION IF EXISTS get_patient_lab_summary(UUID);")
