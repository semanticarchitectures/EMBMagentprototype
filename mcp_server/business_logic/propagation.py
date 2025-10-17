"""
RF propagation models for electromagnetic interference analysis.

Provides simplified propagation models for estimating signal strength,
interference levels, and detection probability.
"""

import math
from typing import Tuple
from ..models import Location


class PropagationModel:
    """
    RF propagation models for spectrum analysis.

    Implements simplified propagation models suitable for prototype demonstration.
    In a production system, these would be replaced with more sophisticated
    models (e.g., ITM, Longley-Rice, or custom terrain-aware models).
    """

    def __init__(self) -> None:
        # Atmospheric loss factor (dB/km)
        self.atmospheric_loss_db_per_km = 0.1

        # Ground reflection factor (simplified)
        self.ground_reflection_loss_db = 6.0

    def calculate_path_loss(
        self,
        frequency_mhz: float,
        distance_km: float,
        include_atmospheric: bool = True
    ) -> float:
        """
        Calculate path loss using Free Space Path Loss model.

        FSPL (dB) = 20*log10(d) + 20*log10(f) + 32.45
        where d is distance in km, f is frequency in MHz

        Args:
            frequency_mhz: Frequency in MHz
            distance_km: Distance in kilometers
            include_atmospheric: Whether to include atmospheric absorption

        Returns:
            Path loss in dB
        """
        if distance_km < 0.001:  # Avoid log(0)
            distance_km = 0.001

        # Free space path loss
        fspl = (
            20 * math.log10(distance_km) +
            20 * math.log10(frequency_mhz) +
            32.45
        )

        # Add atmospheric loss if requested
        if include_atmospheric:
            atmospheric_loss = self.atmospheric_loss_db_per_km * distance_km
            fspl += atmospheric_loss

        return fspl

    def calculate_received_power(
        self,
        tx_power_dbm: float,
        frequency_mhz: float,
        distance_km: float,
        tx_gain_dbi: float = 0.0,
        rx_gain_dbi: float = 0.0
    ) -> float:
        """
        Calculate received power at a distance.

        Args:
            tx_power_dbm: Transmit power in dBm
            frequency_mhz: Frequency in MHz
            distance_km: Distance in kilometers
            tx_gain_dbi: Transmit antenna gain in dBi
            rx_gain_dbi: Receive antenna gain in dBi

        Returns:
            Received power in dBm
        """
        path_loss = self.calculate_path_loss(frequency_mhz, distance_km)

        # Link budget equation
        rx_power = tx_power_dbm + tx_gain_dbi + rx_gain_dbi - path_loss

        return rx_power

    def calculate_interference_level(
        self,
        interferer_power_dbm: float,
        interferer_freq_mhz: float,
        victim_freq_mhz: float,
        distance_km: float
    ) -> Tuple[float, float]:
        """
        Calculate interference level at victim receiver.

        Args:
            interferer_power_dbm: Interfering transmitter power
            interferer_freq_mhz: Interferer frequency
            victim_freq_mhz: Victim receiver frequency
            distance_km: Distance between interferer and victim

        Returns:
            Tuple of (interference_power_dbm, normalized_interference_level_0_to_1)
        """
        # Calculate received power at victim location
        rx_power = self.calculate_received_power(
            interferer_power_dbm,
            interferer_freq_mhz,
            distance_km
        )

        # Apply frequency separation loss
        freq_separation_mhz = abs(interferer_freq_mhz - victim_freq_mhz)
        separation_loss = self._calculate_frequency_separation_loss(freq_separation_mhz)
        interference_power = rx_power - separation_loss

        # Normalize to 0-1 scale (assuming -90 dBm is threshold, 0 dBm is maximum)
        # This is a simplified model
        threshold_dbm = -90.0
        max_dbm = 0.0
        normalized = (interference_power - threshold_dbm) / (max_dbm - threshold_dbm)
        normalized = max(0.0, min(1.0, normalized))  # Clamp to [0, 1]

        return interference_power, normalized

    def calculate_detection_probability(
        self,
        signal_power_dbm: float,
        distance_km: float,
        frequency_mhz: float,
        detector_sensitivity_dbm: float = -100.0
    ) -> float:
        """
        Estimate probability that a signal will be detected.

        Args:
            signal_power_dbm: Transmitted signal power
            distance_km: Distance to detector
            frequency_mhz: Signal frequency
            detector_sensitivity_dbm: Detector sensitivity threshold

        Returns:
            Detection probability 0-1
        """
        # Calculate received power at detector
        rx_power = self.calculate_received_power(
            signal_power_dbm,
            frequency_mhz,
            distance_km
        )

        # Calculate margin above sensitivity
        margin_db = rx_power - detector_sensitivity_dbm

        # Convert to probability (simplified sigmoid-like function)
        # P_detect ≈ 1 / (1 + exp(-margin/3))
        # This gives smooth transition around threshold
        probability = 1.0 / (1.0 + math.exp(-margin_db / 3.0))

        return probability

    def calculate_jamming_effectiveness(
        self,
        jammer_power_dbm: float,
        jammer_freq_mhz: float,
        target_signal_power_dbm: float,
        target_freq_mhz: float,
        distance_to_target_km: float,
        distance_to_victim_km: float
    ) -> float:
        """
        Estimate jamming effectiveness (J/S ratio).

        Args:
            jammer_power_dbm: Jammer transmit power
            jammer_freq_mhz: Jammer frequency
            target_signal_power_dbm: Target signal power
            target_freq_mhz: Target signal frequency
            distance_to_target_km: Distance from target transmitter to victim receiver
            distance_to_victim_km: Distance from jammer to victim receiver

        Returns:
            J/S ratio (Jammer-to-Signal ratio) in dB
        """
        # Jammer power at victim receiver
        jammer_rx_power = self.calculate_received_power(
            jammer_power_dbm,
            jammer_freq_mhz,
            distance_to_victim_km
        )

        # Target signal power at victim receiver
        signal_rx_power = self.calculate_received_power(
            target_signal_power_dbm,
            target_freq_mhz,
            distance_to_target_km
        )

        # Apply frequency separation loss to jammer if frequencies differ
        freq_separation_mhz = abs(jammer_freq_mhz - target_freq_mhz)
        separation_loss = self._calculate_frequency_separation_loss(freq_separation_mhz)
        jammer_effective_power = jammer_rx_power - separation_loss

        # Calculate J/S ratio
        js_ratio_db = jammer_effective_power - signal_rx_power

        return js_ratio_db

    def _calculate_frequency_separation_loss(self, separation_mhz: float) -> float:
        """
        Calculate additional loss due to frequency separation.

        Simplified model: -10 dB per MHz separation, max 60 dB.
        In reality, this depends on receiver selectivity and filter characteristics.

        Args:
            separation_mhz: Frequency separation in MHz

        Returns:
            Additional loss in dB
        """
        if separation_mhz == 0:
            return 0.0

        # -10 dB per MHz, max 60 dB
        loss = min(separation_mhz * 10.0, 60.0)
        return loss

    @staticmethod
    def calculate_distance_km(loc1: Location, loc2: Location) -> float:
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

    def calculate_coverage_radius(
        self,
        tx_power_dbm: float,
        frequency_mhz: float,
        rx_sensitivity_dbm: float,
        required_margin_db: float = 10.0
    ) -> float:
        """
        Calculate effective coverage radius for a transmitter.

        Args:
            tx_power_dbm: Transmit power
            frequency_mhz: Frequency
            rx_sensitivity_dbm: Receiver sensitivity
            required_margin_db: Required link margin

        Returns:
            Coverage radius in kilometers
        """
        # Required received power = sensitivity + margin
        required_rx_power = rx_sensitivity_dbm + required_margin_db

        # Maximum allowable path loss
        max_path_loss = tx_power_dbm - required_rx_power

        # Solve FSPL equation for distance
        # FSPL = 20*log10(d) + 20*log10(f) + 32.45
        # 20*log10(d) = FSPL - 20*log10(f) - 32.45
        # log10(d) = (FSPL - 20*log10(f) - 32.45) / 20
        # d = 10^((FSPL - 20*log10(f) - 32.45) / 20)

        exponent = (max_path_loss - 20 * math.log10(frequency_mhz) - 32.45) / 20.0
        distance_km = 10 ** exponent

        # Account for atmospheric loss (iterative approximation)
        # This is simplified; a more accurate method would iterate
        atmospheric_correction = 1.0 - (self.atmospheric_loss_db_per_km * distance_km / max_path_loss)
        distance_km *= atmospheric_correction

        return max(0.0, distance_km)
