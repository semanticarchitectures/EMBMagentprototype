"""
Spectrum Manager Agent.

Specialized agent responsible for electromagnetic spectrum management,
including frequency allocation, deconfliction, and interference analysis.
"""

from typing import Optional
import structlog

from agents.base_agent import BaseAgent, AgentConfig
from llm_abstraction import LLMProvider
from mcp_client import MCPClient


logger = structlog.get_logger()


class SpectrumManagerAgent(BaseAgent):
    """
    Spectrum Manager Agent.

    Responsibilities:
    - Review and approve/deny frequency allocation requests
    - Perform spectrum deconfliction
    - Analyze interference reports
    - Recommend alternative frequencies when conflicts exist
    - Ensure compliance with ROE and spectrum policies
    """

    SYSTEM_PROMPT = """You are an expert Spectrum Manager Agent for the EMBM-J DS (Electromagnetic Battle Management - Joint Decision Support) system.

Your role and responsibilities:
- Manage electromagnetic spectrum allocations for military operations
- Review frequency allocation requests and perform deconfliction analysis
- Identify and resolve frequency conflicts across different services (Air Force, Navy, Army, Marines)
- Analyze interference reports and recommend mitigation strategies
- Ensure all spectrum usage complies with Rules of Engagement (ROE) and policies
- Consider frequency separation, geographic distance, power levels, and time windows
- Prioritize requests based on mission criticality (FLASH > IMMEDIATE > PRIORITY > ROUTINE)

When processing requests:
1. Always check the current spectrum plan first to understand existing allocations
2. Perform thorough deconfliction analysis considering:
   - Frequency overlap with existing allocations
   - Geographic proximity (co-channel operations require sufficient separation)
   - Temporal conflicts (time window overlaps)
   - Power levels and potential interference
3. If conflicts exist, suggest alternative frequencies or time windows
4. Provide clear, concise justifications for your decisions
5. Use MCP tools to interact with the EMBM-J DS system

Available MCP tools:
- get_spectrum_plan: Get current spectrum allocations for an area/time
- request_deconfliction: Request frequency deconfliction approval
- allocate_frequency: Allocate an approved frequency
- get_interference_report: Get interference analysis for a location
- report_emitter: Report detected electromagnetic emitters

Communication style:
- Be professional, clear, and concise
- Provide specific technical details (frequencies in MHz, distances in km, power in dBm)
- Always explain your reasoning
- If you need more information, ask for it
- Acknowledge uncertainties when they exist

Remember: Spectrum management is critical to mission success. Your decisions directly impact communication, radar, and electronic warfare capabilities."""

    def __init__(
        self,
        llm_provider: LLMProvider,
        mcp_client: MCPClient,
        max_iterations: int = 10
    ):
        """
        Initialize the Spectrum Manager Agent.

        Args:
            llm_provider: LLM provider for generation
            mcp_client: MCP client for tool calls
            max_iterations: Maximum reasoning iterations
        """
        config = AgentConfig(
            name="Spectrum Manager",
            role="Electromagnetic Spectrum Manager",
            system_prompt=self.SYSTEM_PROMPT,
            max_iterations=min(max_iterations, 5),  # Limit iterations
            temperature=0.3  # Lower temperature for more consistent decisions
        )

        super().__init__(config, llm_provider, mcp_client)

        logger.info("spectrum_manager_initialized")

    async def process_allocation_request(
        self,
        asset_id: str,
        frequency_mhz: float,
        bandwidth_khz: float,
        power_dbm: float,
        latitude: float,
        longitude: float,
        start_time: str,
        duration_minutes: int,
        priority: str,
        purpose: str
    ) -> str:
        """
        Process a frequency allocation request.

        Args:
            asset_id: Requesting asset identifier
            frequency_mhz: Requested frequency in MHz
            bandwidth_khz: Bandwidth in kHz
            power_dbm: Transmit power in dBm
            latitude: Latitude of operation
            longitude: Longitude of operation
            start_time: Start time (ISO format)
            duration_minutes: Duration in minutes
            priority: Priority level (ROUTINE/PRIORITY/IMMEDIATE/FLASH)
            purpose: Purpose of the allocation

        Returns:
            Agent's decision and reasoning
        """
        request_message = f"""Please process this frequency allocation request:

Asset ID: {asset_id}
Requested Frequency: {frequency_mhz} MHz
Bandwidth: {bandwidth_khz} kHz
Transmit Power: {power_dbm} dBm
Location: {latitude}°N, {longitude}°E
Start Time: {start_time}
Duration: {duration_minutes} minutes
Priority: {priority}
Purpose: {purpose}

Perform deconfliction analysis and make a recommendation. If approved, allocate the frequency. If denied, provide alternatives."""

        return await self.run(request_message)

    async def analyze_interference(
        self,
        latitude: float,
        longitude: float,
        min_freq_mhz: float,
        max_freq_mhz: float
    ) -> str:
        """
        Analyze interference at a location.

        Args:
            latitude: Latitude
            longitude: Longitude
            min_freq_mhz: Minimum frequency in MHz
            max_freq_mhz: Maximum frequency in MHz

        Returns:
            Interference analysis
        """
        request_message = f"""Please analyze the electromagnetic interference at this location:

Location: {latitude}°N, {longitude}°E
Frequency Range: {min_freq_mhz}-{max_freq_mhz} MHz

Provide a detailed interference analysis including:
- Number and characteristics of interference sources
- Severity of interference
- Recommendations for mitigation
- Affected frequency bands"""

        return await self.run(request_message)

    async def review_spectrum_plan(
        self,
        ao_geojson: str,
        start_time: str,
        end_time: str
    ) -> str:
        """
        Review the current spectrum plan for an area.

        Args:
            ao_geojson: Area of operations as GeoJSON
            start_time: Start time (ISO format)
            end_time: End time (ISO format)

        Returns:
            Spectrum plan analysis
        """
        request_message = f"""Please review the current spectrum plan:

Area of Operations: {ao_geojson}
Time Window: {start_time} to {end_time}

Provide an analysis including:
- Total number of active allocations
- Frequency utilization across bands
- Potential conflicts or congestion
- Service breakdown (by military branch)
- Recommendations for optimization"""

        return await self.run(request_message)
