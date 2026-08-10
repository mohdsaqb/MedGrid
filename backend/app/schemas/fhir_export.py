from typing import Literal

from pydantic import BaseModel, Field


class ExportRequest(BaseModel):
    """
    fail_first_n_attempts is a TEST/DEMO HOOK ONLY, same spirit as Modules
    7/8's simulate_failure - a real external system has no such setting.
    0 = let the simulated exchange's own randomness decide (normal path).
    1..N-1 = guarantees that many failures, then a guaranteed recovery -
    a deterministic way to demonstrate the RETRY path reliably.
    >=N = guarantees every attempt fails - a deterministic FAILED demo.
    """

    fail_first_n_attempts: int = Field(0, ge=0, le=5)


class ExportAttempt(BaseModel):
    attempt: int
    outcome: Literal["SUCCESS", "FAILED"]
    detail: str


class ExportResult(BaseModel):
    status: Literal["SUCCESS", "FAILED"]
    resource: dict
    attempts: list[ExportAttempt]
