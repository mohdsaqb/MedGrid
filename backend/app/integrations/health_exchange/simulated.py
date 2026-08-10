import random
import time

from app.integrations.health_exchange.base import HealthExchangeClient
from app.integrations.health_exchange.exceptions import HealthExchangeError


class SimulatedHealthExchangeClient(HealthExchangeClient):
    """
    Stands in for a real external health information exchange. Same
    reasoning as Modules 7/8's simulated clients: realistic latency and a
    nonzero rejection rate, so retry/failure handling has something real
    to react to.
    """

    def __init__(
        self, failure_rate: float = 0.15, min_latency_s: float = 0.2, max_latency_s: float = 0.6
    ) -> None:
        self.failure_rate = failure_rate
        self.min_latency_s = min_latency_s
        self.max_latency_s = max_latency_s

    def submit_resource(self, resource_type: str, payload: dict) -> None:
        time.sleep(random.uniform(self.min_latency_s, self.max_latency_s))

        if random.random() < self.failure_rate:
            raise HealthExchangeError(
                f"Simulated external health exchange rejected {resource_type}/{payload.get('id')}"
            )
