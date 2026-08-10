from abc import ABC, abstractmethod

from app.integrations.payment_gateway.schemas import PaymentGatewayRequest


class PaymentGatewayClient(ABC):
    """
    The integration boundary for payment processing. Nothing else in this
    codebase talks to "the payment processor" directly - only through this
    interface. Swapping the simulation for a real Stripe/Razorpay client
    later means writing one new class implementing this same method and
    changing one factory function (see __init__.py) - no changes to
    services or routes.
    """

    @abstractmethod
    def confirm_payment(self, request: PaymentGatewayRequest) -> None:
        """Raises PaymentGatewayError if the gateway declines/fails."""
        raise NotImplementedError
