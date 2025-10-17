"""
Rules of Engagement (ROE) constraint engine.

Validates spectrum operations against ROE, policies, and constraints.
"""

from typing import List
from ..models import (
    DeconflictionRequest,
    FriendlyAction,
    Location,
    ActionType,
    Priority
)


class ROEEngine:
    """
    Enforces Rules of Engagement and policy constraints for spectrum operations.

    In a real system, these rules would be loaded from a configuration system
    and updated based on mission requirements and theater-specific ROE.
    """

    def __init__(self) -> None:
        # Frequency restrictions (example: avoid certain protected bands)
        self.restricted_frequencies = [
            (121.5, 121.5),   # Emergency frequency
            (243.0, 243.0),   # Military emergency
            (406.0, 406.1),   # COSPAS-SARSAT emergency
        ]

        # Geographic restrictions (example: no-RF zones)
        self.restricted_zones: List[dict] = [
            # Example: Hospital zone
            {
                "name": "Medical Facility Alpha",
                "location": Location(lat=35.0, lon=45.0),
                "radius_km": 5.0,
                "allowed_actions": [],  # No RF allowed
            }
        ]

        # Power limits by frequency band (example)
        self.power_limits = {
            (30.0, 88.0): 50.0,      # VHF: max 50 dBm
            (225.0, 400.0): 55.0,    # UHF: max 55 dBm
            (1000.0, 2000.0): 60.0,  # L-band: max 60 dBm
        }

        # Priority restrictions
        self.max_concurrent_flash = 5  # Max simultaneous FLASH priority requests

    def validate_request(
        self,
        request: DeconflictionRequest,
        current_flash_count: int = 0
    ) -> List[str]:
        """
        Validate a deconfliction request against ROE.

        Returns a list of violations. Empty list means compliant.
        """
        violations: List[str] = []

        # Check frequency restrictions
        freq_violations = self._check_frequency_restrictions(request.frequency_mhz)
        violations.extend(freq_violations)

        # Check geographic restrictions
        geo_violations = self._check_geographic_restrictions(
            request.location,
            ActionType.COMMUNICATION  # Assume communication for deconfliction request
        )
        violations.extend(geo_violations)

        # Check power limits
        power_violations = self._check_power_limits(
            request.frequency_mhz,
            request.power_dbm
        )
        violations.extend(power_violations)

        # Check priority constraints
        if request.priority == Priority.FLASH:
            if current_flash_count >= self.max_concurrent_flash:
                violations.append(
                    f"Maximum concurrent FLASH priority requests exceeded "
                    f"({current_flash_count}/{self.max_concurrent_flash})"
                )

        return violations

    def validate_coa_actions(
        self,
        actions: List[FriendlyAction]
    ) -> List[str]:
        """
        Validate Course of Action against ROE.

        Returns a list of violations. Empty list means compliant.
        """
        violations: List[str] = []

        for i, action in enumerate(actions):
            action_id = f"Action {i+1} ({action.action_type.value})"

            # Check frequency restrictions
            freq_violations = self._check_frequency_restrictions(action.frequency_mhz)
            for violation in freq_violations:
                violations.append(f"{action_id}: {violation}")

            # Check geographic restrictions
            geo_violations = self._check_geographic_restrictions(
                action.location,
                action.action_type
            )
            for violation in geo_violations:
                violations.append(f"{action_id}: {violation}")

            # Check power limits
            power_violations = self._check_power_limits(
                action.frequency_mhz,
                action.power_dbm
            )
            for violation in power_violations:
                violations.append(f"{action_id}: {violation}")

            # Special checks for jamming
            if action.action_type == ActionType.JAMMING:
                jamming_violations = self._check_jamming_constraints(action)
                for violation in jamming_violations:
                    violations.append(f"{action_id}: {violation}")

        return violations

    def _check_frequency_restrictions(self, frequency_mhz: float) -> List[str]:
        """Check if frequency is in a restricted band."""
        violations: List[str] = []

        for min_freq, max_freq in self.restricted_frequencies:
            if min_freq <= frequency_mhz <= max_freq:
                violations.append(
                    f"Frequency {frequency_mhz} MHz is in restricted band "
                    f"{min_freq}-{max_freq} MHz"
                )

        return violations

    def _check_geographic_restrictions(
        self,
        location: Location,
        action_type: ActionType
    ) -> List[str]:
        """Check if location is in a restricted zone."""
        violations: List[str] = []

        for zone in self.restricted_zones:
            distance_km = self._calculate_distance_km(location, zone["location"])

            if distance_km <= zone["radius_km"]:
                # Check if this action type is allowed in the zone
                if action_type not in zone["allowed_actions"]:
                    violations.append(
                        f"Location within restricted zone '{zone['name']}' "
                        f"({distance_km:.1f} km from center, {zone['radius_km']} km radius). "
                        f"Action type {action_type.value} not permitted."
                    )

        return violations

    def _check_power_limits(
        self,
        frequency_mhz: float,
        power_dbm: float
    ) -> List[str]:
        """Check if transmit power exceeds limits for the frequency band."""
        violations: List[str] = []

        for (min_freq, max_freq), max_power in self.power_limits.items():
            if min_freq <= frequency_mhz <= max_freq:
                if power_dbm > max_power:
                    violations.append(
                        f"Power {power_dbm} dBm exceeds limit of {max_power} dBm "
                        f"for frequency band {min_freq}-{max_freq} MHz"
                    )

        return violations

    def _check_jamming_constraints(self, action: FriendlyAction) -> List[str]:
        """Additional constraints specific to jamming operations."""
        violations: List[str] = []

        # Example: Jamming requires higher power
        min_jamming_power = 40.0  # dBm
        if action.power_dbm < min_jamming_power:
            violations.append(
                f"Jamming power {action.power_dbm} dBm below minimum "
                f"{min_jamming_power} dBm"
            )

        # Example: Time limit on jamming
        max_jamming_duration = 60  # minutes
        if action.duration_minutes > max_jamming_duration:
            violations.append(
                f"Jamming duration {action.duration_minutes} minutes exceeds "
                f"maximum {max_jamming_duration} minutes"
            )

        return violations

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
