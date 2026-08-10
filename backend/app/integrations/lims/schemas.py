from dataclasses import dataclass


@dataclass(frozen=True)
class LimsOrderRequest:
    """
    What we send TO the LIMS. Deliberately NOT the same class as our
    LabOrder DB model or our API's LabOrderCreate schema - this is the
    integration boundary's own contract. If a real LIMS wants the test
    name spelled differently, or needs a different identifier format,
    that translation happens here, in ONE place, instead of leaking the
    external system's quirks into our internal domain model.
    """

    order_id: str
    test_name: str
    patient_reference: str  # e.g. patient_number - never send raw PHI like a name


@dataclass(frozen=True)
class LimsOrderResult:
    """What we get BACK from the LIMS on success - translated into this
    shape regardless of what the real external API's response actually
    looks like."""

    result: str
    unit: str | None
    reference_range: str | None
