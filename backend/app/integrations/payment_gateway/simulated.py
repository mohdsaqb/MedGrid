import random
import time

from app.integrations.payment_gateway.base import PaymentGatewayClient
from app.integrations.payment_gateway.exceptions import PaymentGatewayError
from app.integrations.payment_gateway.schemas import PaymentGatewayRequest


class SimulatedPaymentGatewayClient(PaymentGatewayClient):
    """
    Stands in for a real payment processor. Simulates realistic latency
    and a nonzero decline rate, same reasoning as Module 7's
    SimulatedLimsClient - the rest of the system needs a real failure
    path to react to, not just an always-succeeds stub.
    """

    def __init__(
        self, failure_rate: float = 0.15, min_latency_s: float = 0.2, max_latency_s: float = 0.6
    ) -> None:
        self.failure_rate = failure_rate
        self.min_latency_s = min_latency_s
        self.max_latency_s = max_latency_s

    def confirm_payment(self, request: PaymentGatewayRequest) -> None:
        time.sleep(random.uniform(self.min_latency_s, self.max_latency_s))

        if random.random() < self.failure_rate:
            raise PaymentGatewayError(
                f"Simulated gateway decline for payment {request.payment_id}"
            )
