from app.integrations.payment_gateway.base import PaymentGatewayClient
from app.integrations.payment_gateway.simulated import SimulatedPaymentGatewayClient

__all__ = ["PaymentGatewayClient", "SimulatedPaymentGatewayClient", "get_payment_gateway_client"]


def get_payment_gateway_client() -> PaymentGatewayClient:
    """
    The single swap point. To integrate a real processor later: write
    `StripeGatewayClient(PaymentGatewayClient)` making actual API calls,
    add a settings flag, and change only this return statement - same
    pattern as get_lims_client() in Module 7.
    """
    return SimulatedPaymentGatewayClient()
