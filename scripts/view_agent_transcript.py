#!/usr/bin/env python3
"""
View Agent Transcript - Display inter-agent communications from log files.

Formats message broker activity as a readable conversation transcript,
similar to viewing traffic on a voice network.

Usage:
    python scripts/view_agent_transcript.py [options]

Options:
    --log FILE          Log file to parse (default: logs/embm_app.log)
    --agent AGENT       Filter by agent name
    --topic TOPIC       Filter by message topic
    --start TIME        Start time (ISO format)
    --end TIME          End time (ISO format)
    --verbose           Show detailed agent activity (tool calls, iterations)
    --format FORMAT     Output format: transcript (default) or json
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


class TranscriptViewer:
    """Parse and display agent communication transcripts from log files."""

    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.events: List[Dict[str, Any]] = []

    def load_logs(self, start_time: Optional[str] = None, end_time: Optional[str] = None):
        """Load and parse log entries."""
        with open(self.log_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # Skip non-JSON lines (like HTTP requests)
                if not line.startswith('{'):
                    continue

                try:
                    event = json.loads(line)

                    # Filter by time range
                    if start_time and event.get('timestamp', '') < start_time:
                        continue
                    if end_time and event.get('timestamp', '') > end_time:
                        continue

                    self.events.append(event)
                except json.JSONDecodeError:
                    continue

    def filter_events(self, agent: Optional[str] = None, topic: Optional[str] = None):
        """Filter events by agent and/or topic."""
        filtered = self.events

        if agent:
            filtered = [
                e for e in filtered
                if (e.get('agent') == agent or
                    e.get('sender') == agent or
                    e.get('subscriber') == agent)
            ]

        if topic:
            filtered = [e for e in filtered if e.get('topic') == topic]

        return filtered

    def format_timestamp(self, timestamp: str) -> str:
        """Format ISO timestamp for display."""
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime('%H:%M:%S.%f')[:-3]  # HH:MM:SS.mmm
        except:
            return timestamp

    def format_transcript(self, events: List[Dict], verbose: bool = False):
        """Format events as a readable transcript."""
        print("=" * 80)
        print("EMBM-J DS AGENT COMMUNICATION TRANSCRIPT")
        print("=" * 80)
        print()

        last_timestamp = None
        session_start = None

        for event in events:
            timestamp = event.get('timestamp', '')
            event_type = event.get('event', '')

            if not session_start and event_type == 'agent_subscriptions_configured':
                session_start = timestamp
                print(f"[{self.format_timestamp(timestamp)}] SESSION START")
                print("─" * 80)
                continue

            # Message broker events (primary communication)
            if event_type == 'message_published':
                ts = self.format_timestamp(timestamp)
                sender = event.get('sender', 'Unknown')
                topic = event.get('topic', 'unknown')
                msg_type = event.get('type', 'unknown')
                msg_id = event.get('message_id', '')[:8]

                print(f"\n[{ts}] {sender} → {topic} [{msg_type}]")
                print(f"           Message ID: {msg_id}")

            elif event_type == 'broadcast_received':
                ts = self.format_timestamp(timestamp)
                sender = event.get('sender', 'Unknown')
                subscriber = event.get('subscriber') or '(all subscribers)'
                msg_id = event.get('message_id', '')[:8]

                print(f"           ↳ Received by {subscriber}")

            elif event_type == 'request_sent':
                ts = self.format_timestamp(timestamp)
                sender = event.get('sender', 'Unknown')
                topic = event.get('topic', 'unknown')
                corr_id = event.get('correlation_id', '')[:8]

                print(f"\n[{ts}] {sender} → {topic} [REQUEST]")
                print(f"           Correlation ID: {corr_id}")

            elif event_type == 'response_sent':
                ts = self.format_timestamp(timestamp)
                sender = event.get('sender', 'Unknown')
                corr_id = event.get('correlation_id', '')[:8]

                print(f"\n[{ts}] {sender} ← [RESPONSE]")
                print(f"           Correlation ID: {corr_id}")

            # Agent lifecycle events
            elif verbose and event_type == 'agent_run_start':
                ts = self.format_timestamp(timestamp)
                agent = event.get('agent', 'Unknown')
                msg_len = event.get('message_length', 0)

                print(f"\n[{ts}] ┌─ {agent} ACTIVATED")
                print(f"           Message length: {msg_len} chars")

            elif verbose and event_type == 'agent_calling_tool':
                ts = self.format_timestamp(timestamp)
                agent = event.get('agent', 'Unknown')
                tool = event.get('tool', 'unknown')

                print(f"[{ts}] │  {agent} calling tool: {tool}")

            elif verbose and event_type == 'mcp_tool_call':
                ts = self.format_timestamp(timestamp)
                tool = event.get('tool', 'unknown')
                params = event.get('params', {})

                # Show key parameters
                key_params = {}
                if 'asset_rid' in params:
                    key_params['asset'] = params['asset_rid']
                if 'frequency_mhz' in params:
                    key_params['frequency'] = f"{params['frequency_mhz']} MHz"
                if 'priority' in params:
                    key_params['priority'] = params['priority']
                if 'location' in params:
                    loc = params['location']
                    key_params['location'] = f"({loc['lat']}, {loc['lon']})"

                if key_params:
                    param_str = ', '.join(f"{k}={v}" for k, v in key_params.items())
                    print(f"           Parameters: {param_str}")

            elif verbose and event_type == 'deconfliction_complete':
                ts = self.format_timestamp(timestamp)
                status = event.get('status', 'UNKNOWN')
                conflicts = event.get('conflicts', 0)
                req_id = event.get('request_id', '')[:8]

                status_symbol = "✓" if status == "APPROVED" else "✗"
                print(f"[{ts}] │  {status_symbol} Deconfliction: {status} ({conflicts} conflicts)")
                print(f"           Request ID: {req_id}")

            elif verbose and event_type == 'request_denied_roe':
                ts = self.format_timestamp(timestamp)
                violations = event.get('violations', [])

                print(f"[{ts}] │  ✗ ROE VIOLATION:")
                for violation in violations:
                    print(f"           - {violation}")

            elif verbose and event_type == 'agent_run_complete':
                ts = self.format_timestamp(timestamp)
                agent = event.get('agent', 'Unknown')
                iterations = event.get('iterations', 0)
                error = event.get('error')

                status = "COMPLETED" if not error else f"ERROR: {error}"
                print(f"[{ts}] └─ {agent} {status} ({iterations} iterations)")

            elif event_type == 'subscription_created':
                # Only show on first occurrence or if verbose
                if not session_start or verbose:
                    ts = self.format_timestamp(timestamp)
                    subscriber = event.get('subscriber', 'Unknown')
                    topic = event.get('topic', 'unknown')
                    sub_id = event.get('subscription_id', '')[:8]

                    if verbose:
                        print(f"[{ts}] {subscriber} subscribed to {topic} [{sub_id}]")

        print("\n" + "=" * 80)
        print(f"END OF TRANSCRIPT ({len(events)} events)")
        print("=" * 80)

    def format_json(self, events: List[Dict]):
        """Format events as JSON array."""
        print(json.dumps(events, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="View agent communication transcript from log files"
    )
    parser.add_argument(
        '--log',
        type=Path,
        default=Path('logs/embm_app.log'),
        help='Log file to parse (default: logs/embm_app.log)'
    )
    parser.add_argument(
        '--agent',
        help='Filter by agent name'
    )
    parser.add_argument(
        '--topic',
        help='Filter by message topic'
    )
    parser.add_argument(
        '--start',
        help='Start time (ISO format)'
    )
    parser.add_argument(
        '--end',
        help='End time (ISO format)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed agent activity (tool calls, iterations)'
    )
    parser.add_argument(
        '--format',
        choices=['transcript', 'json'],
        default='transcript',
        help='Output format (default: transcript)'
    )

    args = parser.parse_args()

    # Verify log file exists
    if not args.log.exists():
        print(f"Error: Log file not found: {args.log}", file=sys.stderr)
        sys.exit(1)

    # Load and parse logs
    viewer = TranscriptViewer(args.log)
    viewer.load_logs(start_time=args.start, end_time=args.end)

    # Filter events
    events = viewer.filter_events(agent=args.agent, topic=args.topic)

    if not events:
        print("No events found matching the criteria.", file=sys.stderr)
        sys.exit(1)

    # Display results
    if args.format == 'json':
        viewer.format_json(events)
    else:
        viewer.format_transcript(events, verbose=args.verbose)


if __name__ == '__main__':
    main()
