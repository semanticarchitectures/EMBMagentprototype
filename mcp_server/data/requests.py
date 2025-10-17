"""
In-memory storage for deconfliction requests.

Tracks the history of all deconfliction requests and their outcomes.
"""

from typing import Dict, List, Optional
from datetime import datetime
import asyncio
from ..models import DeconflictionRequest, DeconflictionResponse, DeconflictionStatus


class RequestStore:
    """
    Thread-safe in-memory storage for deconfliction requests and responses.
    """

    def __init__(self) -> None:
        self._requests: Dict[str, DeconflictionRequest] = {}
        self._responses: Dict[str, DeconflictionResponse] = {}
        self._lock = asyncio.Lock()

    async def add_request(self, request: DeconflictionRequest) -> None:
        """Add a new deconfliction request."""
        async with self._lock:
            self._requests[request.request_id] = request

    async def add_response(self, response: DeconflictionResponse) -> None:
        """Add a response to a deconfliction request."""
        async with self._lock:
            self._responses[response.request_id] = response

    async def get_request(self, request_id: str) -> Optional[DeconflictionRequest]:
        """Get a request by ID."""
        async with self._lock:
            return self._requests.get(request_id)

    async def get_response(self, request_id: str) -> Optional[DeconflictionResponse]:
        """Get a response by request ID."""
        async with self._lock:
            return self._responses.get(request_id)

    async def get_all_requests(self) -> List[DeconflictionRequest]:
        """Get all requests."""
        async with self._lock:
            return list(self._requests.values())

    async def get_all_responses(self) -> List[DeconflictionResponse]:
        """Get all responses."""
        async with self._lock:
            return list(self._responses.values())

    async def get_requests_by_asset(self, asset_id: str) -> List[DeconflictionRequest]:
        """Get all requests from a specific asset."""
        async with self._lock:
            return [
                req for req in self._requests.values()
                if req.asset_rid == asset_id
            ]

    async def get_requests_by_status(
        self,
        status: DeconflictionStatus
    ) -> List[tuple[DeconflictionRequest, Optional[DeconflictionResponse]]]:
        """Get all requests with a specific status."""
        async with self._lock:
            result = []
            for request in self._requests.values():
                response = self._responses.get(request.request_id)
                if response and response.status == status:
                    result.append((request, response))
            return result

    async def get_pending_requests(self) -> List[DeconflictionRequest]:
        """Get all requests that don't have a response yet."""
        async with self._lock:
            return [
                req for req in self._requests.values()
                if req.request_id not in self._responses
            ]

    async def get_approved_requests(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[tuple[DeconflictionRequest, DeconflictionResponse]]:
        """Get all approved requests, optionally filtered by time range."""
        async with self._lock:
            result = []
            for request in self._requests.values():
                response = self._responses.get(request.request_id)
                if response and response.status == DeconflictionStatus.APPROVED:
                    # Apply time filter if specified
                    if start_time and request.start_time < start_time:
                        continue
                    request_end = request.start_time
                    # Add duration to start_time for end comparison
                    from datetime import timedelta
                    request_end = request.start_time + timedelta(minutes=request.duration_minutes)
                    if end_time and request_end > end_time:
                        continue
                    result.append((request, response))
            return result

    async def clear_all(self) -> None:
        """Clear all requests and responses (useful for testing)."""
        async with self._lock:
            self._requests.clear()
            self._responses.clear()


# Global instance
request_store = RequestStore()
