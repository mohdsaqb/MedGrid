class LimsServiceError(Exception):
    """
    Raised when the (simulated or real) LIMS fails to process an order -
    a network timeout, the external service being down, a malformed
    response, etc. Callers decide what to do (retry, mark FAILED) - this
    exception only reports that the integration boundary was crossed
    and something went wrong on the other side of it.
    """

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)
