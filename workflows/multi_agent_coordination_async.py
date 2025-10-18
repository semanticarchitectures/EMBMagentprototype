"""
Multi-Agent Coordination Workflow with Async Parallel Execution.

PHASE 4 ENHANCEMENT: Demonstrates parallel agent execution for improved performance.

Key improvements over sequential execution:
- Independent agents (ISR, EW) run concurrently
- Dependent operations (Spectrum review) run after prerequisites
- Estimated 3x performance improvement for independent tasks

Scenario:
A high-value target area requires simultaneous ISR collection and EW jamming,
requiring careful coordination to avoid interference between friendly systems.
"""

import asyncio
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
import structlog

from llm_abstraction import get_global_registry
from mcp_client import MCPClient
from agents import SpectrumManagerAgent, ISRManagerAgent, EWPlannerAgent
from broker import MessageBroker, MessageType


logger = structlog.get_logger()


class AsyncMultiAgentCoordinator:
    """
    Coordinates multiple agents with parallel execution where possible.

    PHASE 4 ENHANCEMENT: Async coordination for better performance.
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

        # Performance metrics
        self.metrics = {
            "start_time": None,
            "end_time": None,
            "agent_execution_times": {},
            "parallel_operations": 0
        }

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

    async def execute_parallel_operations(
        self,
        operations: List[Dict[str, Any]]
    ) -> List[Any]:
        """
        Execute multiple agent operations in parallel.

        PHASE 4 ENHANCEMENT: Core async execution logic.

        Args:
            operations: List of operations, each with 'name', 'coro', 'broadcast' keys

        Returns:
            List of results from each operation
        """
        print(f"\n⚡ Running {len(operations)} operations in PARALLEL...")
        start_time = time.time()

        # Publish all broadcasts first
        for op in operations:
            if op.get('broadcast'):
                await self.broker.publish(**op['broadcast'])

        # Execute all coroutines in parallel
        tasks = [op['coro'] for op in operations]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        elapsed = time.time() - start_time
        print(f"✅ Parallel operations completed in {elapsed:.2f}s")

        self.metrics['parallel_operations'] += len(operations)

        # Log results
        for i, (op, result) in enumerate(zip(operations, results)):
            if isinstance(result, Exception):
                print(f"   ❌ {op['name']}: {str(result)}")
                logger.error(f"{op['name']}_error", error=str(result))
            else:
                self.metrics['agent_execution_times'][op['name']] = elapsed
                print(f"   ✅ {op['name']}: Complete")

        return results


async def run_async_multi_agent_workflow():
    """
    Run a multi-agent coordination workflow with ASYNC PARALLEL EXECUTION.

    PHASE 4 ENHANCEMENT: Demonstrates performance improvements from parallel execution.

    Scenario:
    High-value target area (35.1°N, 45.2°E) requires:
    1. ISR radar coverage at 3.2 GHz
    2. EW jamming of threat emitter at 3.3 GHz
    3. Spectrum Manager must deconflict both operations

    Execution Strategy:
    - Steps 1 & 2 run in PARALLEL (ISR + EW are independent)
    - Step 3 runs AFTER (Spectrum review depends on 1 & 2)
    """
    print("=" * 70)
    print("EMBM-J DS Multi-Agent System - PHASE 4 ENHANCEMENT")
    print("Workflow: Async Multi-Agent Coordination")
    print("=" * 70)
    print()

    overall_start = time.time()

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

        # Create coordinator with async support
        coordinator = AsyncMultiAgentCoordinator(
            spectrum_agent=spectrum_agent,
            isr_agent=isr_agent,
            ew_agent=ew_agent,
            broker=broker
        )
        coordinator.metrics['start_time'] = overall_start

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
        print("Execution Strategy: ISR and EW will run IN PARALLEL (independent)")
        print()

        print("=" * 70)
        print("PARALLEL EXECUTION: ISR Manager + EW Planner")
        print("=" * 70)

        # Define parallel operations
        parallel_ops = [
            {
                'name': 'ISR Manager',
                'broadcast': {
                    'topic': 'broadcast.all',
                    'content': {
                        'message': 'ISR Manager requesting radar sensor coordination',
                        'sensor': 'radar',
                        'frequency_mhz': 3200.0,
                        'location': {'lat': 35.0, 'lon': 45.0}
                    },
                    'sender': 'ISR Manager',
                    'message_type': MessageType.NOTIFICATION
                },
                'coro': isr_agent.coordinate_rf_sensor(
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
            },
            {
                'name': 'EW Planner',
                'broadcast': {
                    'topic': 'broadcast.all',
                    'content': {
                        'message': 'EW Planner initiating jamming operation',
                        'threat_freq_mhz': 3300.0,
                        'jammer_location': {'lat': 35.05, 'lon': 45.05}
                    },
                    'sender': 'EW Planner',
                    'message_type': MessageType.NOTIFICATION
                },
                'coro': ew_agent.plan_jamming_operation(
                    threat_emitter_freq_mhz=3300.0,
                    threat_location="35.1°N, 45.2°E",
                    jammer_location="35.05°N, 45.05°E",
                    jamming_technique="spot",
                    power_dbm=60.0,
                    duration_minutes=180,
                    priority="PRIORITY",
                    justification="Neutralize threat radar to enable friendly operations"
                )
            }
        ]

        # Execute in parallel
        results = await coordinator.execute_parallel_operations(parallel_ops)
        isr_response, ew_response = results

        print()
        if not isinstance(isr_response, Exception):
            print("ISR Manager Response:")
            print(isr_response)
            print()

        if not isinstance(ew_response, Exception):
            print("EW Planner Response:")
            print(ew_response)
            print()

        print("=" * 70)
        print("SEQUENTIAL EXECUTION: Spectrum Manager Review")
        print("(Depends on ISR + EW results)")
        print("=" * 70)
        print()

        review_start = time.time()

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

            review_elapsed = time.time() - review_start
            coordinator.metrics['agent_execution_times']['Spectrum Manager'] = review_elapsed

            print(f"✅ Spectrum Manager completed in {review_elapsed:.2f}s")
            print()
            print("Spectrum Manager Final Review:")
            print(spectrum_response)
            print()

        except Exception as e:
            print(f"ERROR in spectrum review: {str(e)}")
            logger.error("spectrum_review_error", error=str(e))

        # Calculate total time
        overall_elapsed = time.time() - overall_start
        coordinator.metrics['end_time'] = time.time()
        coordinator.metrics['total_duration'] = overall_elapsed

        print("=" * 70)
        print("PERFORMANCE METRICS")
        print("=" * 70)
        print()
        print(f"Total Execution Time: {overall_elapsed:.2f}s")
        print()
        print("Agent Execution Times:")
        for agent, duration in coordinator.metrics['agent_execution_times'].items():
            print(f"  - {agent}: {duration:.2f}s")
        print()
        print(f"Parallel Operations: {coordinator.metrics['parallel_operations']}")
        print()
        print("Performance Analysis:")
        print("  Sequential execution would take: ~sum of all agent times")
        print("  Parallel execution took: ~max(parallel agents) + sequential agent")
        print("  → Time saved by running ISR + EW in parallel!")
        print()

        print("=" * 70)
        print("MESSAGE BROKER STATISTICS")
        print("=" * 70)
        print()
        print(f"Total Topics: {len(broker.get_topics())}")
        print(f"Topics: {', '.join(broker.get_topics())}")
        print(f"Total Subscriptions: {broker.get_subscription_count()}")
        print(f"Message History: {len(await broker.get_history())} messages")
        print()

        print("=" * 70)
        print("WORKFLOW COMPLETE")
        print("=" * 70)
        print()
        print("Summary:")
        print("✓ Three agents coordinated on a complex scenario")
        print("✓ ISR and EW agents ran IN PARALLEL (independent operations)")
        print("✓ Spectrum Manager ran AFTER (dependent operation)")
        print("✓ Message broker facilitated agent-to-agent communication")
        print("✓ Each agent used MCP tools for EMBM-J DS interaction")
        print("✓ Frequency deconfliction performed across ISR and EW operations")
        print()
        print(f"🚀 PHASE 4 ENHANCEMENT: Async execution completed in {overall_elapsed:.2f}s")


async def main():
    """Main entry point."""
    # Configure structured logging
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ]
    )

    await run_async_multi_agent_workflow()


if __name__ == "__main__":
    asyncio.run(main())
