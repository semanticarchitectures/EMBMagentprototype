"""
ISR Collection Manager Agent.

Specialized agent responsible for Intelligence, Surveillance, and Reconnaissance
collection management, sensor tasking, and coordination with other agents.
"""

from typing import Optional
import structlog

from agents.base_agent import BaseAgent, AgentConfig
from llm_abstraction import LLMProvider
from mcp_client import MCPClient


logger = structlog.get_logger()


class ISRManagerAgent(BaseAgent):
    """
    ISR Collection Manager Agent.

    Responsibilities:
    - Manage ISR collection requirements
    - Task and coordinate sensors (radar, EO/IR, SIGINT, etc.)
    - Coordinate with Spectrum Manager for RF sensor frequencies
    - Analyze collection results and gaps
    - Prioritize collection based on intelligence requirements
    - Deconflict sensor operations
    """

    SYSTEM_PROMPT = """You are an expert ISR (Intelligence, Surveillance, Reconnaissance) Collection Manager for the EMBM-J DS system.

Your role and responsibilities:
- Manage ISR collection operations and sensor tasking
- Coordinate radar, EO/IR (Electro-Optical/Infrared), SIGINT, and other sensor operations
- Work with the Spectrum Manager to coordinate RF spectrum for sensors
- Analyze intelligence requirements and prioritize collection
- Identify collection gaps and recommend sensor tasking
- Deconflict sensor operations to prevent interference
- Assess sensor coverage and effectiveness

Collection planning considerations:
1. Match sensor capabilities to collection requirements
2. Consider environmental factors (weather, terrain, time of day)
3. Ensure spectrum deconfliction for RF sensors
4. Optimize sensor positioning and coverage
5. Balance collection priorities and sensor availability
6. Coordinate with other agents (Spectrum Manager, EW Planner)

Available MCP tools:
- get_spectrum_plan: Check spectrum allocations for RF sensors
- request_deconfliction: Request frequency approval for RF sensors
- get_interference_report: Analyze RF interference affecting sensors
- report_emitter: Report detected targets/emitters

Multi-agent coordination:
You can communicate with other agents through the message broker:
- Spectrum Manager: For RF spectrum coordination
- EW Planner: For EW/ISR deconfliction
- Battle Manager: For taskings and reporting

When working with other agents:
- Send clear, structured messages
- Include all necessary technical details
- Acknowledge responses and confirm coordination
- Escalate conflicts or issues when needed

Communication style:
- Be professional, clear, and concise
- Provide specific technical details (frequencies, coordinates, sensor types)
- Always explain your reasoning
- If you need more information, ask for it
- Acknowledge uncertainties when they exist

Remember: Effective ISR collection is critical for situational awareness and mission success. Your coordination with other agents ensures optimal sensor performance and mission effectiveness."""

    def __init__(
        self,
        llm_provider: LLMProvider,
        mcp_client: MCPClient,
        max_iterations: int = 10
    ):
        """
        Initialize the ISR Collection Manager Agent.

        Args:
            llm_provider: LLM provider for generation
            mcp_client: MCP client for tool calls
            max_iterations: Maximum reasoning iterations
        """
        config = AgentConfig(
            name="ISR Collection Manager",
            role="Intelligence, Surveillance, Reconnaissance Manager",
            system_prompt=self.SYSTEM_PROMPT,
            max_iterations=min(max_iterations, 5),  # Limit iterations
            temperature=0.4  # Moderate temperature for balanced decisions
        )

        super().__init__(config, llm_provider, mcp_client)

        logger.info("isr_manager_initialized")

    async def task_sensor(
        self,
        sensor_type: str,
        target_area: str,
        collection_requirement: str,
        priority: str,
        duration_minutes: int,
        additional_params: Optional[dict] = None
    ) -> str:
        """
        Task a sensor for collection.

        Args:
            sensor_type: Type of sensor (RADAR, EO/IR, SIGINT, etc.)
            target_area: Target area (GeoJSON or description)
            collection_requirement: What to collect
            priority: Priority level (ROUTINE/PRIORITY/IMMEDIATE/FLASH)
            duration_minutes: Collection duration
            additional_params: Additional sensor-specific parameters

        Returns:
            Agent's tasking decision and coordination actions
        """
        params_str = ""
        if additional_params:
            params_str = "\n".join(f"{k}: {v}" for k, v in additional_params.items())

        request_message = f"""Please task the following sensor for collection:

Sensor Type: {sensor_type}
Target Area: {target_area}
Collection Requirement: {collection_requirement}
Priority: {priority}
Duration: {duration_minutes} minutes
{params_str}

Coordinate with other agents as needed (e.g., Spectrum Manager for RF sensors).
Provide a detailed tasking plan and any necessary coordination actions."""

        return await self.run(request_message)

    async def analyze_collection_gap(
        self,
        intelligence_requirement: str,
        current_coverage: str,
        available_sensors: list
    ) -> str:
        """
        Analyze a collection gap and recommend actions.

        Args:
            intelligence_requirement: Intelligence requirement description
            current_coverage: Current sensor coverage
            available_sensors: List of available sensors

        Returns:
            Gap analysis and recommendations
        """
        sensors_str = "\n".join(f"- {s}" for s in available_sensors)

        request_message = f"""Please analyze this collection gap:

Intelligence Requirement: {intelligence_requirement}
Current Coverage: {current_coverage}

Available Sensors:
{sensors_str}

Provide:
1. Gap analysis
2. Recommended sensor tasking
3. Coordination requirements with other agents
4. Risk assessment"""

        return await self.run(request_message)

    async def coordinate_rf_sensor(
        self,
        sensor_id: str,
        frequency_mhz: float,
        bandwidth_khz: float,
        power_dbm: float,
        latitude: float,
        longitude: float,
        start_time: str,
        duration_minutes: int,
        purpose: str
    ) -> str:
        """
        Coordinate RF spectrum for a radar or SIGINT sensor.

        Args:
            sensor_id: Sensor identifier
            frequency_mhz: Operating frequency in MHz
            bandwidth_khz: Bandwidth in kHz
            power_dbm: Transmit power in dBm
            latitude: Latitude of sensor
            longitude: Longitude of sensor
            start_time: Start time (ISO format)
            duration_minutes: Duration in minutes
            purpose: Collection purpose

        Returns:
            Coordination result
        """
        request_message = f"""Coordinate RF spectrum for this sensor:

Sensor ID: {sensor_id}
Operating Frequency: {frequency_mhz} MHz
Bandwidth: {bandwidth_khz} kHz
Power: {power_dbm} dBm
Location: {latitude}°N, {longitude}°E
Start Time: {start_time}
Duration: {duration_minutes} minutes
Purpose: {purpose}

Work with the Spectrum Manager to obtain frequency approval.
Ensure no interference with friendly communications or other sensors."""

        return await self.run(request_message)
