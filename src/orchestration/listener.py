import httpx
from src.shared.models import SeismicEvent

class SeismicListener:
    """
    A listener class to pull seismic events from agencies.
    """
    def __init__(self, http_client: httpx.AsyncClient, agency_a_url: str, agency_b_url: str):
        """
        Initializes the SeismicListener.
        """
        self.http_client = http_client
        self.agency_a_url = agency_a_url
        self.agency_b_url = agency_b_url

    async def pull_events(self) -> list[SeismicEvent]:
        """
        Pulls seismic events from the configured agencies.
        Returns an empty list for now to ensure tests fail initially (TDD).
        """
        return []
