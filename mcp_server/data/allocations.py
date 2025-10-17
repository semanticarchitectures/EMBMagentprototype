"""
In-memory storage for spectrum allocations.

Manages the current state of all frequency allocations, providing thread-safe
access and querying capabilities.
"""

from typing import Dict, List, Optional
from datetime import datetime
import asyncio
from ..models import FrequencyAllocation, Location


class AllocationStore:
    """
    Thread-safe in-memory storage for spectrum allocations.

    In a production system, this would be backed by a database.
    For the prototype, we use in-memory storage for simplicity.
    """

    def __init__(self) -> None:
        self._allocations: Dict[str, FrequencyAllocation] = {}
        self._lock = asyncio.Lock()

    async def add(self, allocation: FrequencyAllocation) -> None:
        """Add a new allocation to the store."""
        async with self._lock:
            self._allocations[allocation.allocation_id] = allocation

    async def get(self, allocation_id: str) -> Optional[FrequencyAllocation]:
        """Get an allocation by ID."""
        async with self._lock:
            return self._allocations.get(allocation_id)

    async def remove(self, allocation_id: str) -> bool:
        """Remove an allocation by ID. Returns True if removed, False if not found."""
        async with self._lock:
            if allocation_id in self._allocations:
                del self._allocations[allocation_id]
                return True
            return False

    async def get_all(self) -> List[FrequencyAllocation]:
        """Get all allocations."""
        async with self._lock:
            return list(self._allocations.values())

    async def get_active_allocations(self, at_time: datetime) -> List[FrequencyAllocation]:
        """Get all allocations active at a specific time."""
        async with self._lock:
            return [
                alloc for alloc in self._allocations.values()
                if alloc.start_time <= at_time <= alloc.end_time
            ]

    async def get_by_frequency_range(
        self,
        min_freq: float,
        max_freq: float,
        at_time: datetime
    ) -> List[FrequencyAllocation]:
        """Get all active allocations within a frequency range."""
        active = await self.get_active_allocations(at_time)
        return [
            alloc for alloc in active
            if self._frequencies_overlap(
                alloc.frequency_mhz,
                alloc.bandwidth_khz / 1000.0,  # Convert to MHz
                min_freq,
                max_freq
            )
        ]

    async def get_by_location(
        self,
        location: Location,
        radius_km: float,
        at_time: datetime
    ) -> List[FrequencyAllocation]:
        """Get all active allocations within a geographic radius."""
        active = await self.get_active_allocations(at_time)
        return [
            alloc for alloc in active
            if self._calculate_distance_km(location, alloc.location) <= radius_km
        ]

    async def get_by_asset(self, asset_id: str) -> List[FrequencyAllocation]:
        """Get all allocations for a specific asset."""
        async with self._lock:
            return [
                alloc for alloc in self._allocations.values()
                if alloc.asset_id == asset_id
            ]

    async def clear_expired(self, current_time: datetime) -> int:
        """Remove all expired allocations. Returns count of removed allocations."""
        async with self._lock:
            initial_count = len(self._allocations)
            self._allocations = {
                aid: alloc for aid, alloc in self._allocations.items()
                if alloc.end_time > current_time
            }
            return initial_count - len(self._allocations)

    async def clear_all(self) -> None:
        """Clear all allocations (useful for testing)."""
        async with self._lock:
            self._allocations.clear()

    @staticmethod
    def _frequencies_overlap(
        freq1_mhz: float,
        bandwidth1_mhz: float,
        min_freq: float,
        max_freq: float
    ) -> bool:
        """Check if a frequency allocation overlaps with a frequency range."""
        freq1_min = freq1_mhz - (bandwidth1_mhz / 2)
        freq1_max = freq1_mhz + (bandwidth1_mhz / 2)

        # Check for any overlap
        return not (freq1_max < min_freq or freq1_min > max_freq)

    @staticmethod
    def _calculate_distance_km(loc1: Location, loc2: Location) -> float:
        """
        Calculate great-circle distance between two locations using Haversine formula.

        Returns distance in kilometers.
        """
        import math

        # Earth's radius in kilometers
        R = 6371.0

        # Convert to radians
        lat1 = math.radians(loc1.lat)
        lon1 = math.radians(loc1.lon)
        lat2 = math.radians(loc2.lat)
        lon2 = math.radians(loc2.lon)

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))

        return R * c


# Global instance
allocation_store = AllocationStore()
