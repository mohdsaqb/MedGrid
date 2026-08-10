from app.integrations.lims.base import LimsClient
from app.integrations.lims.simulated import SimulatedLimsClient

__all__ = ["LimsClient", "SimulatedLimsClient", "get_lims_client"]


def get_lims_client() -> LimsClient:
    """
    The single place that decides WHICH LimsClient implementation is
    active. Everything else (services, routes) calls get_lims_client()
    and only ever sees the LimsClient interface.

    To integrate a real LIMS later: write `RealLimsClient(LimsClient)` in
    this package making actual HTTP calls, add a settings flag (e.g.
    `settings.lims_provider`), and change ONLY the return statement below.
    No other file in the codebase would need to change.
    """
    return SimulatedLimsClient()
