"""
Multi-Agent Coordination Workflow.

Demonstrates coordination between Spectrum Manager, ISR Manager, and EW Planner
agents using the message broker for agent-to-agent communication.

Scenario:
A high-value target area requires simultaneous ISR collection and EW jamming,
requiring careful coordination to avoid interference between friendly systems.
"""

import asyncio
import os
from datetime import datetime, timedelta, timezone
import structlog

from llm_abstraction import get_global_registry
from mcp_client import MCPClient
from agents import SpectrumManagerAgent, ISRManagerAgent, EWPlannerAgent
from broker import MessageBroker, MessageType


logger = structlog.get_logger()


class MultiAgentCoordinator:
    """
    Coordinates multiple agents working together on a complex scenario.
    """

    def __init__(
        self,
        spectrum_agent: SpectrumManagerAgent,
        isr_agent: ISRManagerAgent,
        ew_agent: EWPlannerAgent,
        broker: MessageBroker
    ):
        """
        Initialize the coordinator.

        Args:
            spectrum_agent: Spectrum Manager agent
            isr_agent: ISR Manager agent
            ew_agent: EW Planner agent
            broker: Message broker for agent communication
        """
        self.spectrum_agent = spectrum_agent
        self.isr_agent = isr_agent
        self.ew_agent = ew_agent
        self.broker = broker

        # Track agent responses
        self.agent_responses = {}

    async def setup_subscriptions(self):
        """Set up message broker subscriptions for agent coordination."""
        # Spectrum Manager subscribes to frequency requests
        await self.broker.subscribe(
            topic="spectrum.request",
            subscriber="Spectrum Manager",
            callback=self.handle_spectrum_request
        )

        # ISR Manager subscribes to sensor coordination
        await self.broker.subscribe(
            topic="isr.coordination",
            subscriber="ISR Manager",
            callback=self.handle_isr_coordination
        )

        # EW Planner subscribes to EW requests and warnings
        await self.broker.subscribe(
            topic="ew.request",
            subscriber="EW Planner",
            callback=self.handle_ew_request
        )

        # All agents subscribe to broadcast messages
        for agent_name in ["Spectrum Manager", "ISR Manager", "EW Planner"]:
            await self.broker.subscribe(
                topic="broadcast.all",
                subscriber=agent_name,
                callback=self.handle_broadcast
            )

        logger.info("agent_subscriptions_configured")

    async def handle_spectrum_request(self, message):
        """Handle spectrum allocation requests."""
        logger.info(
            "spectrum_request_received",
            sender=message.sender,
            message_id=message.id
        )
        # Store for processing
        self.agent_responses[message.id] = message

    async def handle_isr_coordination(self, message):
        """Handle ISR coordination messages."""
        logger.info(
            "isr_coordination_received",
            sender=message.sender,
            message_id=message.id
        )
        self.agent_responses[message.id] = message

    async def handle_ew_request(self, message):
        """Handle EW operation requests."""
        logger.info(
            "ew_request_received",
            sender=message.sender,
            message_id=message.id
        )
        self.agent_responses[message.id] = message

    async def handle_broadcast(self, message):
        """Handle broadcast messages."""
        logger.info(
            "broadcast_received",
            sender=message.sender,
            subscriber=message.metadata.get("subscriber"),
            message_id=message.id
        )


async def run_multi_agent_workflow():
    """
    Run a multi-agent coordination workflow.

    Scenario:
    High-value target area (35.1°N, 45.2°E) requires:
    1. ISR radar coverage at 3.2 GHz
    2. EW jamming of threat emitter at 3.3 GHz
    3. Spectrum Manager must deconflict both operations
    """
    print("=" * 70)
    print("EMBM-J DS Multi-Agent System")
    print("Workflow: Multi-Agent Coordination")
    print("=" * 70)
    print()

    # Get MCP server URL from environment
    server_url = os.getenv("EMBM_SERVER_URL", "http://localhost:8000")
    print(f"MCP Server: {server_url}")
    print()

    # Initialize MCP client
    async with MCPClient(server_url) as mcp_client:
        # Check server health
        print("Checking MCP server health...")
        is_healthy = await mcp_client.health_check()

        if not is_healthy:
            print("ERROR: MCP server is not healthy!")
            return

        print("✅ MCP server is healthy")
        print()

        # Get LLM provider
        print("Initializing LLM provider...")
        registry = get_global_registry()
        llm_provider = registry.get_provider()
        print(f"✅ Using {llm_provider.get_provider_name()}")
        print()

        # Initialize message broker
        print("Initializing message broker...")
        broker = MessageBroker(max_history=1000)
        print("✅ Message broker ready")
        print()

        # Create agents
        print("Creating agents...")
        spectrum_agent = SpectrumManagerAgent(
            llm_provider=llm_provider,
            mcp_client=mcp_client,
            max_iterations=5
        )
        isr_agent = ISRManagerAgent(
            llm_provider=llm_provider,
            mcp_client=mcp_client,
            max_iterations=5
        )
        ew_agent = EWPlannerAgent(
            llm_provider=llm_provider,
            mcp_client=mcp_client,
            max_iterations=5
        )
        print("✅ All agents created")
        print()

        # Create coordinator
        coordinator = MultiAgentCoordinator(
            spectrum_agent=spectrum_agent,
            isr_agent=isr_agent,
            ew_agent=ew_agent,
            broker=broker
        )

        await coordinator.setup_subscriptions()
        print("✅ Agent subscriptions configured")
        print()

        # Define scenario
        print("=" * 70)
        print("SCENARIO: Coordinated ISR and EW Operations")
        print("=" * 70)
        print()

        target_area = "High-value target area: 35.1°N, 45.2°E"
        start_time = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()

        print("Target Area: 35.1°N, 45.2°E")
        print("Start Time:", start_time)
        print()
        print("Requirements:")
        print("1. ISR radar coverage of target area")
        print("   - Frequency: 3200 MHz (3.2 GHz)")
        print("   - Radar location: 35.0°N, 45.0°E")
        print("   - Duration: 180 minutes")
        print()
        print("2. EW jamming of threat emitter in target area")
        print("   - Threat frequency: 3300 MHz (3.3 GHz)")
        print("   - Jammer location: 35.05°N, 45.05°E")
        print("   - Duration: 180 minutes")
        print()
        print("Challenge: Both operations use nearby frequencies and must be")
        print("deconflicted to prevent interference between friendly systems.")
        print()

        print("=" * 70)
        print("STEP 1: ISR Manager - Coordinate Radar Sensor")
        print("=" * 70)
        print()

        try:
            # Publish ISR coordination request to broker
            await broker.publish(
                topic="broadcast.all",
                content={
                    "message": "ISR Manager requesting radar sensor coordination",
                    "sensor": "radar",
                    "frequency_mhz": 3200.0,
                    "location": {"lat": 35.0, "lon": 45.0}
                },
                sender="ISR Manager",
                message_type=MessageType.NOTIFICATION
            )

            # ISR Manager coordinates radar
            isr_response = await isr_agent.coordinate_rf_sensor(
                sensor_id="RADAR-01",
                frequency_mhz=3200.0,
                bandwidth_khz=50.0,
                power_dbm=55.0,
                latitude=35.0,
                longitude=45.0,
                start_time=start_time,
                duration_minutes=180,
                purpose="Target area surveillance"
            )

            print("ISR Manager Response:")
            print(isr_response)
            print()

        except Exception as e:
            print(f"ERROR in ISR coordination: {str(e)}")
            logger.error("isr_coordination_error", error=str(e))

        print("=" * 70)
        print("STEP 2: EW Planner - Plan Jamming Operation")
        print("=" * 70)
        print()

        try:
            # Publish EW planning request to broker
            await broker.publish(
                topic="broadcast.all",
                content={
                    "message": "EW Planner initiating jamming operation",
                    "threat_freq_mhz": 3300.0,
                    "jammer_location": {"lat": 35.05, "lon": 45.05}
                },
                sender="EW Planner",
                message_type=MessageType.NOTIFICATION
            )

            # EW Planner plans jamming
            ew_response = await ew_agent.plan_jamming_operation(
                threat_emitter_freq_mhz=3300.0,
                threat_location="35.1°N, 45.2°E",
                jammer_location="35.05°N, 45.05°E",
                jamming_technique="spot",
                power_dbm=60.0,
                duration_minutes=180,
                priority="PRIORITY",
                justification="Neutralize threat radar to enable friendly operations"
            )

            print("EW Planner Response:")
            print(ew_response)
            print()

        except Exception as e:
            print(f"ERROR in EW planning: {str(e)}")
            logger.error("ew_planning_error", error=str(e))

        print("=" * 70)
        print("STEP 3: Spectrum Manager - Review Overall Plan")
        print("=" * 70)
        print()

        try:
            # Publish final coordination message
            await broker.publish(
                topic="broadcast.all",
                content={
                    "message": "All agents have submitted plans. Spectrum Manager reviewing.",
                    "isr_freq_mhz": 3200.0,
                    "ew_freq_mhz": 3300.0,
                    "frequency_separation_mhz": 100.0
                },
                sender="Coordinator",
                message_type=MessageType.BROADCAST
            )

            # Spectrum Manager reviews the plan
            review_message = """Review this coordinated operation plan:

OPERATION: Simultaneous ISR and EW in target area 35.1°N, 45.2°E

ISR RADAR:
- Frequency: 3200 MHz
- Bandwidth: 50 kHz
- Power: 55 dBm
- Location: 35.0°N, 45.0°E
- Duration: 180 minutes

EW JAMMING:
- Target Frequency: 3300 MHz
- Jamming Power: 60 dBm
- Location: 35.05°N, 45.05°E
- Duration: 180 minutes

Assess:
1. Frequency separation (100 MHz) - is it sufficient?
2. Geographic separation - potential for interference?
3. Any other spectrum conflicts in the area?
4. Recommendations for optimization

Provide final approval or suggest modifications."""

            spectrum_response = await spectrum_agent.run(review_message)

            print("Spectrum Manager Final Review:")
            print(spectrum_response)
            print()

        except Exception as e:
            print(f"ERROR in spectrum review: {str(e)}")
            logger.error("spectrum_review_error", error=str(e))

        print("=" * 70)
        print("MESSAGE BROKER STATISTICS")
        print("=" * 70)
        print()
        print(f"Total Topics: {len(broker.get_topics())}")
        print(f"Topics: {', '.join(broker.get_topics())}")
        print(f"Total Subscriptions: {broker.get_subscription_count()}")
        print(f"Message History: {len(await broker.get_history())} messages")
        print()

        # Show recent messages
        history = await broker.get_history(limit=10)
        if history:
            print("Recent Messages:")
            for msg in history:
                print(f"  - [{msg.type.value}] {msg.sender} -> {msg.topic}")
        print()

        print("=" * 70)
        print("WORKFLOW COMPLETE")
        print("=" * 70)
        print()
        print("Summary:")
        print("✓ Three agents coordinated on a complex scenario")
        print("✓ Message broker facilitated agent-to-agent communication")
        print("✓ Each agent used MCP tools for EMBM-J DS interaction")
        print("✓ Frequency deconfliction performed across ISR and EW operations")


async def main():
    """Main entry point."""
    # Configure structured logging
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ]
    )

    await run_multi_agent_workflow()


if __name__ == "__main__":
    asyncio.run(main())
