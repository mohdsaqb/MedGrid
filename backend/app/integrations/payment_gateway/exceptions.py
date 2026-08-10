class PaymentGatewayError(Exception):
    """
    Raised when the (simulated or real) payment gateway declines or fails
    to process a payment - a declined card, a network timeout, the
    processor being down, etc. Same role as LimsServiceError in Module 7:
    reports that the integration boundary was crossed and failed: nothing
    more.
    """

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)
