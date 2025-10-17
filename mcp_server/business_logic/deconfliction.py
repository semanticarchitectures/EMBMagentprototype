"""
Frequency deconfliction business logic.

Implements realistic spectrum deconfliction algorithms based on:
- Frequency separation requirements
- Geographic proximity
- Temporal overlap
- Power levels and propagation
- Policy and ROE constraints
"""

from typing import List, Tuple, Optional
from datetime import datetime, timedelta
import math
from ..models import (
    FrequencyAllocation,
    DeconflictionRequest,
    Conflict,
    ConflictType,
    Location,
    Priority
)


class DeconflictionEngine:
    """
    Implements realistic frequency deconfliction logic.

    This engine checks for conflicts between a proposed frequency allocation
    and existing allocations, considering frequency, geography, time, and power.
    """

    def __init__(self) -> None:
        # Configuration parameters (could be loaded from config)
        self.min_frequency_separation_mhz = 5.0  # Minimum safe frequency separation
        self.min_geographic_separation_km = 50.0  # Minimum distance for co-channel
        self.interference_threshold_db = -90.0   # Receiver sensitivity threshold
        self.adjacent_channel_rejection_db = 60.0  # Adjacent channel rejection

    def check_conflicts(
        self,
        request: DeconflictionRequest,
        existing_allocations: List[FrequencyAllocation]
    ) -> List[Conflict]:
        """
        Check a deconfliction request against existing allocations.

        Returns a list of conflicts found. Empty list means no conflicts.
        """
        conflicts: List[Conflict] = []

        # Calculate request time window
        request_end_time = request.start_time + timedelta(minutes=request.duration_minutes)

        for allocation in existing_allocations:
            # Check temporal overlap first (cheapest check)
            if not self._time_overlaps(
                request.start_time,
                request_end_time,
                allocation.start_time,
                allocation.end_time
            ):
                continue  # No temporal overlap, skip

            # Check frequency conflict
            freq_conflict = self._check_frequency_conflict(request, allocation)
            if freq_conflict:
                conflicts.append(freq_conflict)

            # Check geographic conflict (co-channel or near-channel)
            geo_conflict = self._check_geographic_conflict(request, allocation)
            if geo_conflict:
                conflicts.append(geo_conflict)

        return conflicts

    def _time_overlaps(
        self,
        start1: datetime,
        end1: datetime,
        start2: datetime,
        end2: datetime
    ) -> bool:
        """Check if two time periods overlap."""
        return not (end1 <= start2 or start1 >= end2)

    def _check_frequency_conflict(
        self,
        request: DeconflictionRequest,
        allocation: FrequencyAllocation
    ) -> Optional[Conflict]:
        """Check for frequency domain conflicts."""
        # Calculate frequency ranges (center ± bandwidth/2)
        req_bw_mhz = request.bandwidth_khz / 1000.0
        alloc_bw_mhz = allocation.bandwidth_khz / 1000.0

        req_min = request.frequency_mhz - (req_bw_mhz / 2)
        req_max = request.frequency_mhz + (req_bw_mhz / 2)
        alloc_min = allocation.frequency_mhz - (alloc_bw_mhz / 2)
        alloc_max = allocation.frequency_mhz + (alloc_bw_mhz / 2)

        # Check for frequency overlap
        if req_max <= alloc_min or req_min >= alloc_max:
            return None  # No overlap

        # Calculate overlap amount
        overlap_min = max(req_min, alloc_min)
        overlap_max = min(req_max, alloc_max)
        overlap_mhz = overlap_max - overlap_min

        # Calculate severity based on overlap percentage
        req_bandwidth = req_max - req_min
        severity = min(1.0, overlap_mhz / req_bandwidth)

        return Conflict(
            conflicting_asset=allocation.asset_id,
            conflict_type=ConflictType.FREQUENCY,
            severity=severity,
            description=(
                f"Frequency overlap with {allocation.asset_id}: "
                f"{overlap_mhz:.2f} MHz overlap on {allocation.frequency_mhz:.2f} MHz"
            ),
            frequency_mhz=allocation.frequency_mhz
        )

    def _check_geographic_conflict(
        self,
        request: DeconflictionRequest,
        allocation: FrequencyAllocation
    ) -> Optional[Conflict]:
        """Check for geographic conflicts (same or nearby frequencies in close proximity)."""
        # Calculate distance between locations
        distance_km = self._calculate_distance_km(request.location, allocation.location)

        # Check if frequencies are close enough to cause interference
        freq_separation_mhz = abs(request.frequency_mhz - allocation.frequency_mhz)

        # If frequencies are identical or very close
        if freq_separation_mhz < self.min_frequency_separation_mhz:
            if distance_km < self.min_geographic_separation_km:
                severity = 1.0 - (distance_km / self.min_geographic_separation_km)

                return Conflict(
                    conflicting_asset=allocation.asset_id,
                    conflict_type=ConflictType.GEOGRAPHIC,
                    severity=severity,
                    description=(
                        f"Geographic conflict with {allocation.asset_id}: "
                        f"{distance_km:.1f} km separation (minimum {self.min_geographic_separation_km} km) "
                        f"on similar frequency {allocation.frequency_mhz:.2f} MHz"
                    ),
                    distance_km=distance_km
                )

        # Check for potential interference based on power and distance
        interference_conflict = self._check_interference(request, allocation, distance_km)
        if interference_conflict:
            return interference_conflict

        return None

    def _check_interference(
        self,
        request: DeconflictionRequest,
        allocation: FrequencyAllocation,
        distance_km: float
    ) -> Optional[Conflict]:
        """
        Check if the requested transmission would cause harmful interference.

        Uses simplified path loss model (free space path loss).
        """
        # Calculate frequency separation
        freq_separation_mhz = abs(request.frequency_mhz - allocation.frequency_mhz)

        # Calculate path loss (free space path loss in dB)
        # FSPL = 20*log10(d) + 20*log10(f) + 32.45
        # where d is distance in km, f is frequency in MHz
        if distance_km < 0.001:  # Avoid log(0)
            distance_km = 0.001

        fspl_db = (
            20 * math.log10(distance_km) +
            20 * math.log10(request.frequency_mhz) +
            32.45
        )

        # Calculate received power at allocation location
        received_power_dbm = request.power_dbm - fspl_db

        # Apply adjacent channel rejection if frequencies are different
        if freq_separation_mhz > 0:
            # Simple model: -10dB per MHz separation, max 60dB
            rejection_db = min(freq_separation_mhz * 10, self.adjacent_channel_rejection_db)
            received_power_dbm -= rejection_db

        # Check if received power exceeds interference threshold
        if received_power_dbm > self.interference_threshold_db:
            excess_db = received_power_dbm - self.interference_threshold_db
            severity = min(1.0, excess_db / 20.0)  # Normalize to 0-1

            return Conflict(
                conflicting_asset=allocation.asset_id,
                conflict_type=ConflictType.GEOGRAPHIC,
                severity=severity,
                description=(
                    f"Potential interference to {allocation.asset_id}: "
                    f"received power {received_power_dbm:.1f} dBm "
                    f"exceeds threshold by {excess_db:.1f} dB at {distance_km:.1f} km"
                ),
                distance_km=distance_km
            )

        return None

    def suggest_alternatives(
        self,
        request: DeconflictionRequest,
        existing_allocations: List[FrequencyAllocation],
        num_suggestions: int = 3
    ) -> List[float]:
        """
        Suggest alternative frequencies that would have fewer conflicts.

        Returns a list of suggested frequencies in MHz.
        """
        suggestions: List[float] = []

        # Define search range (±10% of requested frequency)
        search_range = request.frequency_mhz * 0.1
        min_freq = request.frequency_mhz - search_range
        max_freq = request.frequency_mhz + search_range

        # Try frequencies at regular intervals
        step_mhz = 1.0
        current_freq = min_freq

        tested_freqs: List[Tuple[float, int]] = []  # (frequency, conflict_count)

        while current_freq <= max_freq and len(suggestions) < num_suggestions:
            # Create a test request with this frequency
            test_request = DeconflictionRequest(
                request_id=request.request_id,
                asset_rid=request.asset_rid,
                frequency_mhz=current_freq,
                bandwidth_khz=request.bandwidth_khz,
                power_dbm=request.power_dbm,
                location=request.location,
                start_time=request.start_time,
                duration_minutes=request.duration_minutes,
                priority=request.priority,
                purpose=request.purpose
            )

            conflicts = self.check_conflicts(test_request, existing_allocations)

            if len(conflicts) == 0:
                suggestions.append(current_freq)

            tested_freqs.append((current_freq, len(conflicts)))
            current_freq += step_mhz

        # If we didn't find enough conflict-free frequencies,
        # suggest frequencies with the fewest conflicts
        if len(suggestions) < num_suggestions:
            tested_freqs.sort(key=lambda x: x[1])  # Sort by conflict count
            for freq, _ in tested_freqs:
                if freq not in suggestions:
                    suggestions.append(freq)
                    if len(suggestions) >= num_suggestions:
                        break

        return suggestions[:num_suggestions]

    def evaluate_priority_override(
        self,
        request: DeconflictionRequest,
        conflicts: List[Conflict]
    ) -> bool:
        """
        Determine if request priority justifies overriding conflicts.

        Returns True if the request should be approved despite conflicts.
        """
        if not conflicts:
            return True  # No conflicts, approve

        # FLASH and IMMEDIATE priority can override lower-severity conflicts
        high_priority = request.priority in [Priority.FLASH, Priority.IMMEDIATE]

        if high_priority:
            # Check if all conflicts are low severity
            max_severity = max(c.severity for c in conflicts)
            return max_severity < 0.5  # Override if all conflicts are below 50% severity

        return False

    @staticmethod
    def _calculate_distance_km(loc1: Location, loc2: Location) -> float:
        """Calculate great-circle distance using Haversine formula."""
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
