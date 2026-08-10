import random
import time

from app.integrations.lims.base import LimsClient
from app.integrations.lims.exceptions import LimsServiceError
from app.integrations.lims.schemas import LimsOrderRequest, LimsOrderResult

# Canned results per test name, so a demo/test run produces plausible,
# consistent-looking values instead of pure noise. Falls back to a generic
# qualitative result for any test not in this table.
_CANNED_RESULTS: dict[str, LimsOrderResult] = {
    "Complete Blood Count (CBC)": LimsOrderResult(
        result="7.8", unit="x10^9/L", reference_range="4.5-11.0"
    ),
    "Lipid Panel": LimsOrderResult(result="185", unit="mg/dL", reference_range="<200"),
    "Blood Glucose (Fasting)": LimsOrderResult(
        result="94", unit="mg/dL", reference_range="70-99"
    ),
}
_DEFAULT_RESULT = LimsOrderResult(result="Within normal limits", unit=None, reference_range=None)


class SimulatedLimsClient(LimsClient):
    """
    Stands in for a real external LIMS. Simulates realistic network
    latency and a nonzero chance of failure, so the rest of the system
    (retries, FAILED status, error handling) has something real to react
    to - not just a happy-path stub that always succeeds instantly.
    """

    def __init__(self, failure_rate: float = 0.15, min_latency_s: float = 0.2, max_latency_s: float = 0.6) -> None:
        self.failure_rate = failure_rate
        self.min_latency_s = min_latency_s
        self.max_latency_s = max_latency_s

    def process_order(self, request: LimsOrderRequest) -> LimsOrderResult:
        # Simulated network/processing latency - a real HTTP call to an
        # external system is never instantaneous.
        time.sleep(random.uniform(self.min_latency_s, self.max_latency_s))

        if random.random() < self.failure_rate:
            raise LimsServiceError(
                f"Simulated LIMS timeout processing order {request.order_id}"
            )

        return _CANNED_RESULTS.get(request.test_name, _DEFAULT_RESULT)
