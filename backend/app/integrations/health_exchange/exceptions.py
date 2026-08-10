class HealthExchangeError(Exception):
    """
    Raised when the (simulated or real) external health system rejects
    or fails to accept a submitted resource. Same role as LimsServiceError
    (Module 7) and PaymentGatewayError (Module 8): reports that the
    integration boundary was crossed and failed, nothing more.
    """

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)
