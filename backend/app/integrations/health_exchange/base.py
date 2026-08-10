from abc import ABC, abstractmethod


class HealthExchangeClient(ABC):
    """
    The integration boundary for TRANSMITTING already-mapped, FHIR-shaped
    data to an external system - a hospital's EHR, a national Health
    Information Exchange, another provider's FHIR server, etc.

    Deliberately separate from app.integrations.fhir: that package decides
    WHAT SHAPE the data is (the mapping, Part A point 9); this decides HOW
    it's transmitted and to whom (Part A point 10). Either could change
    independently - e.g. swapping which exchange we submit to doesn't
    touch the mapping code at all, and vice versa.
    """

    @abstractmethod
    def submit_resource(self, resource_type: str, payload: dict) -> None:
        """Raises HealthExchangeError if the external system rejects/fails."""
        raise NotImplementedError
