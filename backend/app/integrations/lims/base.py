from abc import ABC, abstractmethod

from app.integrations.lims.schemas import LimsOrderRequest, LimsOrderResult


class LimsClient(ABC):
    """
    The integration boundary. Everything in this codebase that needs to
    talk to "the lab system" depends on THIS interface, never on a
    concrete implementation. A future RealLimsClient (making actual HTTP
    calls to a hospital's real LIMS) implements the exact same method
    signature - callers wouldn't need to change at all.
    """

    @abstractmethod
    def process_order(self, request: LimsOrderRequest) -> LimsOrderResult:
        """
        Attempt to process one order. Raises LimsServiceError on failure -
        callers (see lab_order_service.py) decide whether to retry.
        """
        raise NotImplementedError
