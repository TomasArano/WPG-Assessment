import logging
import httpx
from typing import List, Set, Optional
from pydantic import ValidationError
from src.shared.models import SeismicEvent

# Configure a logger for anomalies
logger = logging.getLogger(__name__)

class SeismicListener:
    """
    Orchestrates the retrieval of seismic data.
    Handles fallbacks between agencies, data validation, and deduplication.
    """

    def __init__(self, http_client: httpx.AsyncClient, agency_a_url: str, agency_b_url: str):
        self._client = http_client
        self._primary_url = agency_a_url
        self._fallback_url = agency_b_url
        self._processed_eids: Set[int] = set()

    async def pull_events(self) -> List[SeismicEvent]:
        """
        Attempts to pull events from the primary agency, falling back if necessary.
        Validates and deduplicates the results.
        """
        raw_payload = await self._fetch_from_agencies()
        if not raw_payload:
            return []

        return self._process_and_validate(raw_payload)

    async def _fetch_from_agencies(self) -> Optional[List[dict]]:
        """Handles the HTTP requests and the fallback routing."""
        try:
            response = await self._client.get(self._primary_url, timeout=5.0)
            response.raise_for_status()
            return response.json()
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.warning(f"Agency A failed: {e}. Falling back to Agency B.")
            try:
                fallback_response = await self._client.get(self._fallback_url, timeout=5.0)
                fallback_response.raise_for_status()
                return fallback_response.json()
            except (httpx.RequestError, httpx.HTTPStatusError) as fallback_e:
                logger.error(f"Both agencies failed. Fallback error: {fallback_e}")
                return None

    def _process_and_validate(self, raw_payload: List[dict]) -> List[SeismicEvent]:
        """
        Validates raw dictionaries against the Pydantic model and drops duplicates.
        Logs anomalies without crashing the pipeline.
        """
        valid_events = []
        for item in raw_payload:
            try:
                # 1. Check if we already processed this event (Deduplication)
                eid = item.get("eid")
                if eid in self._processed_eids:
                    continue
                
                # 2. Validate data types and constraints
                event = SeismicEvent(**item)
                
                # 3. Store valid event and record its ID
                valid_events.append(event)
                self._processed_eids.add(event.eid)

            except ValidationError as e:
                logger.error(f"Data anomaly detected. Invalid payload: {item}. Error: {e}")
            except Exception as e:
                logger.error(f"Unexpected error processing item {item}: {e}")

        return valid_events