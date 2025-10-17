"""
Frequency Allocation Workflow.

Demonstrates a simple single-agent workflow where the Spectrum Manager
processes a frequency allocation request.
"""

import asyncio
import os
from datetime import datetime, timedelta
import structlog

from llm_abstraction import get_global_registry
from mcp_client import MCPClient
from agents import SpectrumManagerAgent


logger = structlog.get_logger()


async def run_frequency_allocation_workflow():
    """
    Run a simple frequency allocation workflow.

    Scenario:
    An asset requests frequency allocation for a training exercise.
    The Spectrum Manager agent reviews the request, checks for conflicts,
    and makes a decision.
    """
    print("=" * 70)
    print("EMBM-J DS Multi-Agent System")
    print("Workflow: Frequency Allocation")
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

        # Discover available tools
        print("Discovering MCP tools...")
        tools = await mcp_client.discover_tools()
        print(f"✅ Found {len(tools)} tools:")
        for tool in tools:
            print(f"   - {tool.name}: {tool.description}")
        print()

        # Get LLM provider
        print("Initializing LLM provider...")
        registry = get_global_registry()
        llm_provider = registry.get_provider()  # Uses default (Anthropic)
        print(f"✅ Using {llm_provider.get_provider_name()} with model {llm_provider.config.model}")
        print()

        # Create Spectrum Manager agent
        print("Creating Spectrum Manager agent...")
        agent = SpectrumManagerAgent(
            llm_provider=llm_provider,
            mcp_client=mcp_client,
            max_iterations=10
        )
        print("✅ Agent created")
        print()

        # Define the allocation request
        print("=" * 70)
        print("SCENARIO: Frequency Allocation Request")
        print("=" * 70)
        print()

        from datetime import timezone

        asset_id = "TRAINING-ASSET-042"
        frequency_mhz = 151.5
        bandwidth_khz = 25.0
        power_dbm = 35.0
        latitude = 35.05
        longitude = 45.05
        start_time = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        duration_minutes = 120
        priority = "ROUTINE"
        purpose = "Training exercise - tactical communication"

        print(f"Asset ID: {asset_id}")
        print(f"Requested Frequency: {frequency_mhz} MHz")
        print(f"Bandwidth: {bandwidth_khz} kHz")
        print(f"Power: {power_dbm} dBm")
        print(f"Location: {latitude}°N, {longitude}°E")
        print(f"Start Time: {start_time}")
        print(f"Duration: {duration_minutes} minutes")
        print(f"Priority: {priority}")
        print(f"Purpose: {purpose}")
        print()

        print("=" * 70)
        print("AGENT PROCESSING...")
        print("=" * 70)
        print()

        # Process the request
        try:
            response = await agent.process_allocation_request(
                asset_id=asset_id,
                frequency_mhz=frequency_mhz,
                bandwidth_khz=bandwidth_khz,
                power_dbm=power_dbm,
                latitude=latitude,
                longitude=longitude,
                start_time=start_time,
                duration_minutes=duration_minutes,
                priority=priority,
                purpose=purpose
            )

            print("=" * 70)
            print("AGENT RESPONSE:")
            print("=" * 70)
            print()
            print(response)
            print()

            print("=" * 70)
            print("WORKFLOW COMPLETE")
            print("=" * 70)

        except Exception as e:
            print(f"ERROR: {str(e)}")
            logger.error("workflow_error", error=str(e))


async def main():
    """Main entry point."""
    # Configure structured logging
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ]
    )

    await run_frequency_allocation_workflow()


if __name__ == "__main__":
    asyncio.run(main())
