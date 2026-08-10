from app.integrations.health_exchange.base import HealthExchangeClient
from app.integrations.health_exchange.simulated import SimulatedHealthExchangeClient

__all__ = ["HealthExchangeClient", "SimulatedHealthExchangeClient", "get_health_exchange_client"]


def get_health_exchange_client() -> HealthExchangeClient:
    """
    The single swap point - same pattern as get_lims_client() (Module 7)
    and get_payment_gateway_client() (Module 8). A real integration later
    means writing one new class and changing only this return statement.
    """
    return SimulatedHealthExchangeClient()
