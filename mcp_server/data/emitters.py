"""
In-memory storage for detected electromagnetic emitters.

Manages detected emitters and their threat assessments.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
from ..models import Emitter, Location, ThreatLevel


class EmitterStore:
    """
    Thread-safe in-memory storage for detected emitters.

    Emitters are automatically aged out after a configurable retention period.
    """

    def __init__(self, retention_hours: int = 24) -> None:
        self._emitters: Dict[str, Emitter] = {}
        self._lock = asyncio.Lock()
        self.retention_hours = retention_hours

    async def add(self, emitter: Emitter) -> None:
        """Add a new emitter detection."""
        async with self._lock:
            self._emitters[emitter.emitter_id] = emitter

    async def get(self, emitter_id: str) -> Optional[Emitter]:
        """Get an emitter by ID."""
        async with self._lock:
            return self._emitters.get(emitter_id)

    async def get_all(self) -> List[Emitter]:
        """Get all emitters."""
        async with self._lock:
            return list(self._emitters.values())

    async def get_by_location(
        self,
        location: Location,
        radius_km: float
    ) -> List[Emitter]:
        """Get all emitters within a geographic radius."""
        async with self._lock:
            return [
                emitter for emitter in self._emitters.values()
                if self._calculate_distance_km(location, emitter.location) <= radius_km
            ]

    async def get_by_frequency_range(
        self,
        min_freq: float,
        max_freq: float
    ) -> List[Emitter]:
        """Get all emitters within a frequency range."""
        async with self._lock:
            return [
                emitter for emitter in self._emitters.values()
                if self._frequencies_overlap(
                    emitter.frequency_mhz,
                    emitter.bandwidth_khz / 1000.0,
                    min_freq,
                    max_freq
                )
            ]

    async def get_by_threat_level(self, min_level: ThreatLevel) -> List[Emitter]:
        """Get all emitters at or above a specific threat level."""
        threat_order = {
            ThreatLevel.LOW: 0,
            ThreatLevel.MEDIUM: 1,
            ThreatLevel.HIGH: 2,
            ThreatLevel.CRITICAL: 3
        }
        min_order = threat_order[min_level]

        async with self._lock:
            return [
                emitter for emitter in self._emitters.values()
                if (emitter.threat_assessment and
                    threat_order.get(emitter.threat_assessment.threat_level, 0) >= min_order)
            ]

    async def update_threat_assessment(self, emitter_id: str, assessment: Any) -> bool:
        """Update the threat assessment for an emitter."""
        async with self._lock:
            if emitter_id in self._emitters:
                self._emitters[emitter_id].threat_assessment = assessment
                return True
            return False

    async def clear_old_detections(self, current_time: datetime) -> int:
        """Remove detections older than retention period. Returns count removed."""
        cutoff_time = current_time - timedelta(hours=self.retention_hours)

        async with self._lock:
            initial_count = len(self._emitters)
            self._emitters = {
                eid: emitter for eid, emitter in self._emitters.items()
                if emitter.detection_time > cutoff_time
            }
            return initial_count - len(self._emitters)

    async def clear_all(self) -> None:
        """Clear all emitters (useful for testing)."""
        async with self._lock:
            self._emitters.clear()

    @staticmethod
    def _frequencies_overlap(
        freq1_mhz: float,
        bandwidth1_mhz: float,
        min_freq: float,
        max_freq: float
    ) -> bool:
        """Check if a frequency overlaps with a frequency range."""
        freq1_min = freq1_mhz - (bandwidth1_mhz / 2)
        freq1_max = freq1_mhz + (bandwidth1_mhz / 2)
        return not (freq1_max < min_freq or freq1_min > max_freq)

    @staticmethod
    def _calculate_distance_km(loc1: Location, loc2: Location) -> float:
        """Calculate great-circle distance using Haversine formula."""
        import math

        R = 6371.0  # Earth's radius in km

        lat1 = math.radians(loc1.lat)
        lon1 = math.radians(loc1.lon)
        lat2 = math.radians(loc2.lat)
        lon2 = math.radians(loc2.lon)

        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))

        return R * c


# Global instance
emitter_store = EmitterStore()
