"""
Test LLM Response Caching.

Runs a simple workflow twice to demonstrate caching effectiveness.
"""

import asyncio
import os
from datetime import datetime, timedelta, timezone
import structlog

from llm_abstraction import get_global_registry, configure_global_cache
from mcp_client import MCPClient
from agents import SpectrumManagerAgent


logger = structlog.get_logger()


async def run_cache_test():
    """Run cache test workflow."""
    print("=" * 70)
    print("LLM Response Caching Test")
    print("=" * 70)
    print()

    # Configure cache with smaller size for testing
    configure_global_cache(max_size=50, default_ttl_seconds=300)  # 5 minute TTL
    print("✅ Cache configured (max_size=50, ttl=300s)")
    print()

    # Get MCP server URL
    server_url = os.getenv("EMBM_SERVER_URL", "http://localhost:8000")

    async with MCPClient(server_url) as mcp_client:
        # Check server health
        is_healthy = await mcp_client.health_check()
        if not is_healthy:
            print("ERROR: MCP server is not healthy!")
            return

        print("✅ MCP server is healthy")
        print()

        # Get LLM provider (with caching enabled by default)
        registry = get_global_registry()
        llm_provider = registry.get_provider()
        print(f"✅ Using {llm_provider.get_provider_name()} with caching enabled")
        print()

        # Create agent
        agent = SpectrumManagerAgent(
            llm_provider=llm_provider,
            mcp_client=mcp_client,
            max_iterations=3
        )
        print("✅ Spectrum Manager agent created")
        print()

        # Define a frequency allocation request
        start_time = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()

        request_params = {
            "asset_id": "TEST-ASSET-001",
            "frequency_mhz": 2400.0,
            "bandwidth_khz": 25.0,
            "power_dbm": 40.0,
            "latitude": 35.0,
            "longitude": 45.0,
            "start_time": start_time,
            "duration_minutes": 60,
            "priority": "ROUTINE",
            "purpose": "Test frequency allocation for caching demo"
        }

        print("=" * 70)
        print("FIRST RUN (Cold Cache)")
        print("=" * 70)
        print()

        # First run - should hit the API
        import time
        start = time.time()

        response1 = await agent.process_allocation_request(**request_params)

        elapsed1 = time.time() - start

        print(f"✅ First run completed in {elapsed1:.2f}s")
        print()
        print("Response preview:", response1[:200] + "..." if len(response1) > 200 else response1)
        print()

        # Get cache stats after first run
        cache_stats = llm_provider.get_cache_stats()
        if cache_stats:
            print("Cache Statistics after first run:")
            print(f"  - Size: {cache_stats['size']}/{cache_stats['max_size']}")
            print(f"  - Hits: {cache_stats['hits']}")
            print(f"  - Misses: {cache_stats['misses']}")
            print(f"  - Hit Rate: {cache_stats['hit_rate_percent']}%")
            print()

        print("=" * 70)
        print("SECOND RUN (Hot Cache - Same Request)")
        print("=" * 70)
        print()

        # Second run - should hit the cache
        start = time.time()

        response2 = await agent.process_allocation_request(**request_params)

        elapsed2 = time.time() - start

        print(f"✅ Second run completed in {elapsed2:.2f}s")
        print()

        # Get cache stats after second run
        cache_stats = llm_provider.get_cache_stats()
        if cache_stats:
            print("Cache Statistics after second run:")
            print(f"  - Size: {cache_stats['size']}/{cache_stats['max_size']}")
            print(f"  - Hits: {cache_stats['hits']}")
            print(f"  - Misses: {cache_stats['misses']}")
            print(f"  - Hit Rate: {cache_stats['hit_rate_percent']}%")
            print(f"  - Total Requests: {cache_stats['total_requests']}")
            print()

        # Compare performance
        speedup = elapsed1 / elapsed2 if elapsed2 > 0 else 0
        print("=" * 70)
        print("PERFORMANCE COMPARISON")
        print("=" * 70)
        print()
        print(f"First run (cold cache):  {elapsed1:.2f}s")
        print(f"Second run (hot cache):  {elapsed2:.2f}s")
        print(f"Speedup: {speedup:.2f}x faster")
        print()

        if speedup > 5:
            print("🎉 Excellent! Cache providing significant speedup!")
        elif speedup > 2:
            print("✅ Good! Cache is working effectively.")
        else:
            print("⚠️  Cache speedup lower than expected (may have additional overhead)")
        print()

        # Verify responses are identical
        if response1 == response2:
            print("✅ Both responses are identical (cache working correctly)")
        else:
            print("⚠️  Responses differ (this is unexpected with caching)")
        print()

        print("=" * 70)
        print("TEST COMPLETE")
        print("=" * 70)


async def main():
    """Main entry point."""
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ]
    )

    await run_cache_test()


if __name__ == "__main__":
    asyncio.run(main())
