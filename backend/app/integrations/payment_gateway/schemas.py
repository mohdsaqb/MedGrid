from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class PaymentGatewayRequest:
    """
    What we send TO the gateway. Deliberately separate from our Payment
    DB model - a real gateway (Stripe, Razorpay, ...) would want its own
    specific request shape, and that translation belongs here, at the
    boundary, not spread through our domain code.
    """

    payment_id: str
    amount: Decimal
    method: str


# No result dataclass: unlike the LIMS integration (which returns an
# actual value/unit/range to store), a payment gateway confirmation is
# fundamentally binary - it either confirms the charge or it doesn't.
# confirm_payment() below returns nothing on success and raises
# PaymentGatewayError on failure.
