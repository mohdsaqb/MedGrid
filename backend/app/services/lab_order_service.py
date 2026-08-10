import logging
import time
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.integrations.lims import get_lims_client
from app.integrations.lims.exceptions import LimsServiceError
from app.integrations.lims.schemas import LimsOrderRequest
from app.models.doctor import Doctor
from app.models.lab_order import LabOrder, LabStatus
from app.models.lab_result import LabResult
from app.models.lab_test import LabTest
from app.models.patient import Patient
from app.schemas.lab_order import LabOrderCreate

# Reuse the existing "does this patient/doctor exist" errors rather than
# defining parallel ones - same pattern as encounter_service.py.
from app.services.doctor_service import DoctorNotFoundError
from app.services.lab_test_service import LabTestNotFoundError
from app.services.patient_service import PatientNotFoundError

logger = logging.getLogger(__name__)

_WITH_RELATIONS = (
    selectinload(LabOrder.patient),
    selectinload(LabOrder.doctor),
    selectinload(LabOrder.test),
    selectinload(LabOrder.result),
)

MAX_PROCESSING_ATTEMPTS = 2
RETRY_DELAY_SECONDS = 0.3


class LabOrderNotFoundError(Exception):
    pass


class InvalidOrderStateError(Exception):
    """Raised when /process is called on an order that isn't PENDING or FAILED."""

    pass


class LabProcessingFailedError(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def create_lab_order(db: Session, data: LabOrderCreate) -> LabOrder:
    if db.get(Patient, data.patient_id) is None:
        raise PatientNotFoundError(data.patient_id)
    if db.get(Doctor, data.doctor_id) is None:
        raise DoctorNotFoundError(data.doctor_id)
    if db.get(LabTest, data.test_id) is None:
        raise LabTestNotFoundError(data.test_id)

    order = LabOrder(
        patient_id=data.patient_id, doctor_id=data.doctor_id, test_id=data.test_id
    )
    db.add(order)
    db.commit()
    return get_lab_order(db, order.id)


def get_lab_order(db: Session, order_id: uuid.UUID) -> LabOrder:
    # populate_existing=True: same reason as Module 6's encounter_service -
    # this function is called multiple times on the same object within one
    # request during process_lab_order(), and without this, an already
    # loaded `result` relationship (None, before processing) would be
    # returned stale even after a LabResult is created later in the request.
    order = db.scalar(
        select(LabOrder)
        .where(LabOrder.id == order_id)
        .options(*_WITH_RELATIONS)
        .execution_options(populate_existing=True)
    )
    if order is None:
        raise LabOrderNotFoundError(order_id)
    return order


def list_lab_orders(
    db: Session,
    *,
    page: int,
    page_size: int,
    patient_id: uuid.UUID | None,
    doctor_id: uuid.UUID | None,
    status_filter: LabStatus | None,
) -> tuple[list[LabOrder], int]:
    query = select(LabOrder)
    if patient_id is not None:
        query = query.where(LabOrder.patient_id == patient_id)
    if doctor_id is not None:
        query = query.where(LabOrder.doctor_id == doctor_id)
    if status_filter is not None:
        query = query.where(LabOrder.status == status_filter)

    total = db.scalar(select(func.count()).select_from(query.subquery()))

    rows = db.scalars(
        query.options(*_WITH_RELATIONS)
        .order_by(LabOrder.ordered_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return list(rows), total or 0


def process_lab_order(db: Session, order_id: uuid.UUID, simulate_failure: bool = False) -> LabOrder:
    """
    The doctor-ordered -> lab-tech-triggered -> simulated-LIMS-processed
    workflow, in one place. See Part B for the integration boundary design.
    """
    # with_for_update(): locks this row for the duration of THIS transaction,
    # so a concurrent second /process call on the same order blocks here
    # instead of racing past our status check below (Module 2's transaction
    # lesson, applied for real).
    order = db.scalar(
        select(LabOrder).where(LabOrder.id == order_id).with_for_update()
    )
    if order is None:
        raise LabOrderNotFoundError(order_id)
    if order.status not in (LabStatus.PENDING, LabStatus.FAILED):
        raise InvalidOrderStateError()

    order.status = LabStatus.PROCESSING
    # Commit immediately to release the row lock BEFORE the slow external
    # call below. Holding a database lock across network I/O is a classic
    # way to cause cascading slowness in production - the lock's only job
    # was to make the status check+transition atomic, which is now done.
    db.commit()

    test = db.get(LabTest, order.test_id)
    patient = db.get(Patient, order.patient_id)
    request = LimsOrderRequest(
        order_id=str(order.id),
        test_name=test.name,
        patient_reference=patient.patient_number,  # never send PHI like a name externally
    )

    reason = "Simulated forced failure for testing"
    if not simulate_failure:
        client = get_lims_client()
        for attempt in range(1, MAX_PROCESSING_ATTEMPTS + 1):
            try:
                result = client.process_order(request)
                break
            except LimsServiceError as exc:
                reason = exc.reason
                if attempt < MAX_PROCESSING_ATTEMPTS:
                    time.sleep(RETRY_DELAY_SECONDS)
        else:
            result = None
    else:
        result = None

    if result is not None:
        db.add(
            LabResult(
                lab_order_id=order.id,
                result=result.result,
                unit=result.unit,
                reference_range=result.reference_range,
                status=LabStatus.COMPLETED,
            )
        )
        order.status = LabStatus.COMPLETED
        db.commit()
        logger.info("Lab order completed", extra={"lab_order_id": str(order_id)})
        return get_lab_order(db, order_id)

    order.status = LabStatus.FAILED
    db.commit()
    logger.warning(
        "Lab integration failure - LIMS could not process order",
        extra={"lab_order_id": str(order_id), "reason": reason},
    )
    raise LabProcessingFailedError(reason)
