"""
EW Planner Agent.

Specialized agent responsible for Electronic Warfare planning and coordination,
including jamming operations, electronic protection, and EW/ISR deconfliction.
"""

from typing import Optional
import structlog

from agents.base_agent import BaseAgent, AgentConfig
from llm_abstraction import LLMProvider
from mcp_client import MCPClient


logger = structlog.get_logger()


class EWPlannerAgent(BaseAgent):
    """
    Electronic Warfare Planner Agent.

    Responsibilities:
    - Plan and coordinate EW operations (jamming, electronic protection)
    - Deconflict EW operations with friendly communications and sensors
    - Analyze threat emitters and recommend countermeasures
    - Coordinate with Spectrum Manager for EW frequency assignments
    - Coordinate with ISR Manager to avoid sensor interference
    - Assess EW effectiveness and recommend adjustments
    """

    SYSTEM_PROMPT = """You are an expert Electronic Warfare (EW) Planner for the EMBM-J DS system.

Your role and responsibilities:
- Plan and execute EW operations including jamming and electronic protection
- Coordinate EW operations with friendly communications and sensors
- Analyze threat emitters and develop countermeasures
- Work with Spectrum Manager to obtain jamming frequency approvals
- Coordinate with ISR Manager to prevent interference with sensors
- Assess EW effectiveness and recommend tactical adjustments
- Ensure EW operations comply with Rules of Engagement (ROE)

EW planning considerations:
1. Identify and prioritize threat emitters
2. Select appropriate jamming techniques (barrage, spot, deception)
3. Ensure deconfliction with friendly systems
4. Consider power levels, frequency bands, and coverage
5. Assess collateral effects on friendly operations
6. Coordinate timing with other operations
7. Plan for dynamic frequency changes (frequency agility)

Types of EW operations:
- Electronic Attack (EA): Jamming, deception, directed energy
- Electronic Protection (EP): ECCM, frequency hopping, LPI techniques
- Electronic Warfare Support (ES): Threat detection and analysis

Available MCP tools:
- get_spectrum_plan: Check spectrum for deconfliction
- request_deconfliction: Request jamming frequency approval
- report_emitter: Report detected threat emitters
- get_interference_report: Analyze interference effects
- analyze_coa_impact: Assess EW impact on courses of action

Multi-agent coordination:
You MUST coordinate with other agents to prevent fratricide:
- Spectrum Manager: For jamming frequency approval and deconfliction
- ISR Manager: To avoid interfering with friendly sensors
- Battle Manager: For mission approval and ROE guidance

Coordination protocol:
1. Before planning EW operations, consult with Spectrum Manager
2. Coordinate with ISR Manager if EW may affect sensor operations
3. Request approval from Battle Manager for high-risk operations
4. Provide clear warnings about potential friendly system impacts

Communication style:
- Be professional, clear, and concise
- Provide specific technical details (frequencies, power, jamming techniques)
- Always explain your reasoning and risk assessment
- CLEARLY communicate any risks to friendly systems
- If you need more information, ask for it
- Acknowledge uncertainties when they exist

CRITICAL: EW operations can have significant impacts on friendly systems. Always prioritize deconfliction and coordination with other agents. When in doubt, seek approval before executing."""

    def __init__(
        self,
        llm_provider: LLMProvider,
        mcp_client: MCPClient,
        max_iterations: int = 10
    ):
        """
        Initialize the EW Planner Agent.

        Args:
            llm_provider: LLM provider for generation
            mcp_client: MCP client for tool calls
            max_iterations: Maximum reasoning iterations
        """
        config = AgentConfig(
            name="EW Planner",
            role="Electronic Warfare Planner",
            system_prompt=self.SYSTEM_PROMPT,
            max_iterations=min(max_iterations, 5),  # Limit iterations
            temperature=0.3  # Lower temperature for careful EW planning
        )

        super().__init__(config, llm_provider, mcp_client)

        logger.info("ew_planner_initialized")

    async def plan_jamming_operation(
        self,
        threat_emitter_freq_mhz: float,
        threat_location: str,
        jammer_location: str,
        jamming_technique: str,
        power_dbm: float,
        duration_minutes: int,
        priority: str,
        justification: str
    ) -> str:
        """
        Plan a jamming operation against a threat emitter.

        Args:
            threat_emitter_freq_mhz: Threat frequency in MHz
            threat_location: Location of threat emitter
            jammer_location: Location of jammer
            jamming_technique: Jamming technique (barrage/spot/deception)
            power_dbm: Jamming power in dBm
            duration_minutes: Duration in minutes
            priority: Priority level
            justification: Mission justification

        Returns:
            Agent's jamming plan and coordination actions
        """
        request_message = f"""Plan a jamming operation with the following parameters:

Threat Emitter Frequency: {threat_emitter_freq_mhz} MHz
Threat Location: {threat_location}
Jammer Location: {jammer_location}
Jamming Technique: {jamming_technique}
Jamming Power: {power_dbm} dBm
Duration: {duration_minutes} minutes
Priority: {priority}
Justification: {justification}

REQUIRED ACTIONS:
1. Coordinate with Spectrum Manager for frequency approval
2. Coordinate with ISR Manager to check for sensor interference
3. Perform deconfliction analysis
4. Assess risks to friendly systems
5. Provide detailed jamming plan

Ensure all coordination is completed before approving the operation."""

        return await self.run(request_message)

    async def analyze_threat_emitter(
        self,
        emitter_freq_mhz: float,
        emitter_location: str,
        signal_characteristics: dict,
        threat_level: str
    ) -> str:
        """
        Analyze a threat emitter and recommend countermeasures.

        Args:
            emitter_freq_mhz: Emitter frequency in MHz
            emitter_location: Location of emitter
            signal_characteristics: Signal characteristics
            threat_level: Threat assessment (LOW/MEDIUM/HIGH/CRITICAL)

        Returns:
            Threat analysis and countermeasure recommendations
        """
        char_str = "\n".join(f"{k}: {v}" for k, v in signal_characteristics.items())

        request_message = f"""Analyze this threat emitter:

Frequency: {emitter_freq_mhz} MHz
Location: {emitter_location}
Threat Level: {threat_level}

Signal Characteristics:
{char_str}

Provide:
1. Emitter identification and capabilities
2. Threat assessment to friendly operations
3. Recommended countermeasures (jamming, avoidance, etc.)
4. Coordination requirements
5. Risk analysis"""

        return await self.run(request_message)

    async def deconflict_ew_with_comms(
        self,
        ew_freq_range_mhz: tuple,
        ew_location: str,
        affected_area_km: float,
        start_time: str,
        duration_minutes: int
    ) -> str:
        """
        Deconflict EW operations with friendly communications.

        Args:
            ew_freq_range_mhz: EW frequency range (min, max) in MHz
            ew_location: Location of EW operation
            affected_area_km: Affected area radius in km
            start_time: Start time (ISO format)
            duration_minutes: Duration in minutes

        Returns:
            Deconfliction analysis and recommendations
        """
        request_message = f"""Deconflict this EW operation with friendly communications:

EW Frequency Range: {ew_freq_range_mhz[0]}-{ew_freq_range_mhz[1]} MHz
EW Location: {ew_location}
Affected Area: {affected_area_km} km radius
Start Time: {start_time}
Duration: {duration_minutes} minutes

REQUIRED:
1. Check current spectrum plan for conflicts
2. Coordinate with Spectrum Manager
3. Identify affected friendly systems
4. Recommend frequency avoidance or time deconfliction
5. Assess residual risks"""

        return await self.run(request_message)

    async def assess_ew_effectiveness(
        self,
        operation_id: str,
        target_frequency_mhz: float,
        jamming_power_dbm: float,
        observed_effects: str
    ) -> str:
        """
        Assess effectiveness of an ongoing EW operation.

        Args:
            operation_id: EW operation identifier
            target_frequency_mhz: Target frequency in MHz
            jamming_power_dbm: Jamming power in dBm
            observed_effects: Observed effects description

        Returns:
            Effectiveness assessment and recommendations
        """
        request_message = f"""Assess the effectiveness of this EW operation:

Operation ID: {operation_id}
Target Frequency: {target_frequency_mhz} MHz
Jamming Power: {jamming_power_dbm} dBm

Observed Effects:
{observed_effects}

Provide:
1. Effectiveness assessment (% degradation to threat)
2. Recommendations for improvement (power, frequency, technique)
3. Assessment of collateral effects
4. Suggested adjustments"""

        return await self.run(request_message)
