"""
EMBM-J DS Web Dashboard Server.

PHASE 4 ENHANCEMENT: Real-time web dashboard with WebSocket support.

Provides:
- REST API for system status and metrics
- WebSocket for real-time event streaming
- Static file serving for web UI
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Set
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from contextlib import asynccontextmanager
import structlog

from config import get_config


logger = structlog.get_logger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections and broadcasts events.

    PHASE 4 ENHANCEMENT: Real-time event streaming to web clients.
    """

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.event_history: List[Dict] = []
        self.max_history = 100

    async def connect(self, websocket: WebSocket):
        """Add new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)

        logger.info(
            "websocket_connected",
            total_connections=len(self.active_connections)
        )

        # Send recent history to new connection
        for event in self.event_history[-20:]:  # Last 20 events
            try:
                await websocket.send_json(event)
            except Exception as e:
                logger.error("history_send_error", error=str(e))

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        self.active_connections.discard(websocket)

        logger.info(
            "websocket_disconnected",
            total_connections=len(self.active_connections)
        )

    async def broadcast(self, event: Dict):
        """
        Broadcast event to all connected clients.

        Args:
            event: Event dictionary to broadcast
        """
        # Add timestamp if not present
        if "timestamp" not in event:
            event["timestamp"] = datetime.utcnow().isoformat() + "Z"

        # Add to history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)

        # Broadcast to all connections
        disconnected = set()

        for connection in self.active_connections:
            try:
                await connection.send_json(event)
            except Exception as e:
                logger.error(
                    "broadcast_error",
                    error=str(e)
                )
                disconnected.add(connection)

        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)

    def get_history(self, limit: int = 20) -> List[Dict]:
        """Get recent event history."""
        return self.event_history[-limit:]


# Global WebSocket manager
ws_manager = WebSocketManager()


# Application state
app_state = {
    "agents": {
        "Spectrum Manager": {"status": "idle", "last_activity": None},
        "ISR Manager": {"status": "idle", "last_activity": None},
        "EW Planner": {"status": "idle", "last_activity": None}
    },
    "message_broker": {
        "total_messages": 0,
        "topics": [],
        "subscriptions": 0
    },
    "mcp_server": {
        "status": "unknown",
        "last_check": None
    },
    "metrics": {
        "deconfliction_requests": 0,
        "deconfliction_approvals": 0,
        "deconfliction_denials": 0,
        "roe_violations": 0
    }
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("web_server_starting")

    # Start background task for periodic updates
    update_task = asyncio.create_task(periodic_status_updates())

    yield

    # Cleanup
    update_task.cancel()
    try:
        await update_task
    except asyncio.CancelledError:
        pass

    logger.info("web_server_stopped")


# Create FastAPI app
app = FastAPI(
    title="EMBM-J DS Web Dashboard",
    description="Real-time monitoring dashboard for EMBM-J DS Multi-Agent System",
    version="1.0.0",
    lifespan=lifespan
)


# API Endpoints

@app.get("/api/status")
async def get_status():
    """Get current system status."""
    return {
        "status": "running",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "agents": app_state["agents"],
        "message_broker": app_state["message_broker"],
        "mcp_server": app_state["mcp_server"]
    }


@app.get("/api/metrics")
async def get_metrics():
    """Get system metrics."""
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "metrics": app_state["metrics"]
    }


@app.get("/api/agents")
async def get_agents():
    """Get agent status."""
    return {
        "agents": app_state["agents"]
    }


@app.get("/api/events/history")
async def get_event_history(limit: int = 20):
    """Get recent event history."""
    return {
        "events": ws_manager.get_history(limit=limit)
    }


@app.post("/api/events")
async def post_event(event: Dict):
    """
    Post a new event to be broadcasted.

    This endpoint allows other parts of the system to push events
    to the web dashboard.
    """
    await ws_manager.broadcast(event)

    return {"status": "broadcasted"}


# WebSocket endpoint

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates.

    Clients connect here to receive real-time events about:
    - Agent activity
    - Deconfliction decisions
    - Message broker activity
    - System status changes
    """
    await ws_manager.connect(websocket)

    try:
        while True:
            # Keep connection alive and receive any client messages
            data = await websocket.receive_text()

            # Handle client messages (ping/pong, commands, etc.)
            try:
                message = json.loads(data)

                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})

                elif message.get("type") == "get_status":
                    await websocket.send_json({
                        "type": "status",
                        "data": app_state
                    })

            except json.JSONDecodeError:
                logger.warning("invalid_json_from_client", data=data)

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error("websocket_error", error=str(e))
        ws_manager.disconnect(websocket)


# Background tasks

async def periodic_status_updates():
    """
    Periodically broadcast status updates.

    Sends heartbeat and status updates every 30 seconds.
    """
    config = get_config()
    interval = config.web_dashboard.websocket.heartbeat_interval

    while True:
        try:
            await asyncio.sleep(interval)

            # Broadcast heartbeat
            await ws_manager.broadcast({
                "type": "heartbeat",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "connected_clients": len(ws_manager.active_connections)
            })

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("periodic_update_error", error=str(e))


# Static file serving for web UI

# Check if web_ui directory exists
web_ui_dir = Path(__file__).parent / "web_ui"
if web_ui_dir.exists():
    app.mount("/static", StaticFiles(directory=str(web_ui_dir / "static")), name="static")

    @app.get("/")
    async def serve_dashboard():
        """Serve the main dashboard HTML."""
        index_file = web_ui_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return HTMLResponse(get_default_dashboard_html())
else:
    @app.get("/")
    async def serve_dashboard():
        """Serve default dashboard HTML."""
        return HTMLResponse(get_default_dashboard_html())


def get_default_dashboard_html() -> str:
    """
    Get default embedded dashboard HTML.

    Simple dashboard with real-time WebSocket updates.
    """
    return """
<!DOCTYPE html>
<html>
<head>
    <title>EMBM-J DS Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #1a1a2e;
            color: #eee;
            padding: 20px;
        }

        .header {
            background: #16213e;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }

        h1 {
            color: #0f4c75;
            font-size: 28px;
            margin-bottom: 5px;
        }

        .subtitle {
            color: #888;
            font-size: 14px;
        }

        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            margin-left: 10px;
        }

        .status-connected { background: #27ae60; color: white; }
        .status-disconnected { background: #e74c3c; color: white; }

        .container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }

        .panel {
            background: #16213e;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }

        .panel h2 {
            color: #3498db;
            font-size: 18px;
            margin-bottom: 15px;
            border-bottom: 2px solid #0f4c75;
            padding-bottom: 8px;
        }

        .agent-card {
            background: #1a1a2e;
            padding: 12px;
            margin-bottom: 10px;
            border-radius: 6px;
            border-left: 4px solid #3498db;
        }

        .agent-name {
            font-weight: bold;
            color: #3498db;
            margin-bottom: 5px;
        }

        .agent-status {
            font-size: 13px;
            color: #888;
        }

        .metric {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #2c2c3e;
        }

        .metric:last-child { border-bottom: none; }

        .metric-label { color: #aaa; }
        .metric-value {
            font-weight: bold;
            color: #3498db;
        }

        .event-feed {
            grid-column: 1 / -1;
        }

        .event {
            background: #1a1a2e;
            padding: 12px;
            margin-bottom: 8px;
            border-radius: 6px;
            border-left: 4px solid #27ae60;
            font-size: 13px;
        }

        .event-error { border-left-color: #e74c3c; }
        .event-warning { border-left-color: #f39c12; }

        .event-time {
            color: #888;
            font-size: 11px;
            margin-bottom: 4px;
        }

        .event-content { color: #eee; }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .event {
            animation: fadeIn 0.3s ease-out;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>EMBM-J DS Multi-Agent Dashboard</h1>
        <p class="subtitle">Electromagnetic Battle Management - Joint Decision Support</p>
        <span id="connection-status" class="status-badge status-disconnected">Disconnected</span>
    </div>

    <div class="container">
        <div class="panel">
            <h2>Agents</h2>
            <div id="agents-container">
                <p style="color: #888;">Connecting...</p>
            </div>
        </div>

        <div class="panel">
            <h2>Metrics</h2>
            <div id="metrics-container">
                <div class="metric">
                    <span class="metric-label">Deconfliction Requests</span>
                    <span class="metric-value" id="metric-requests">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Approvals</span>
                    <span class="metric-value" id="metric-approvals">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Denials</span>
                    <span class="metric-value" id="metric-denials">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">ROE Violations</span>
                    <span class="metric-value" id="metric-violations">0</span>
                </div>
            </div>
        </div>

        <div class="panel event-feed">
            <h2>Real-Time Event Feed</h2>
            <div id="events-container">
                <p style="color: #888;">Waiting for events...</p>
            </div>
        </div>
    </div>

    <script>
        let ws;
        let reconnectAttempts = 0;
        const maxReconnectAttempts = 5;

        function connect() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;

            ws = new WebSocket(wsUrl);

            ws.onopen = () => {
                console.log('WebSocket connected');
                document.getElementById('connection-status').textContent = 'Connected';
                document.getElementById('connection-status').className = 'status-badge status-connected';
                reconnectAttempts = 0;

                // Request initial status
                ws.send(JSON.stringify({ type: 'get_status' }));

                // Start heartbeat
                setInterval(() => {
                    if (ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({ type: 'ping' }));
                    }
                }, 30000);
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                handleEvent(data);
            };

            ws.onclose = () => {
                console.log('WebSocket disconnected');
                document.getElementById('connection-status').textContent = 'Disconnected';
                document.getElementById('connection-status').className = 'status-badge status-disconnected';

                // Attempt reconnect
                if (reconnectAttempts < maxReconnectAttempts) {
                    reconnectAttempts++;
                    setTimeout(connect, 2000 * reconnectAttempts);
                }
            };

            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        }

        function handleEvent(event) {
            if (event.type === 'status') {
                updateStatus(event.data);
            } else if (event.type === 'heartbeat') {
                // Heartbeat received
            } else {
                addEventToFeed(event);
            }
        }

        function updateStatus(data) {
            // Update agents
            if (data.agents) {
                const container = document.getElementById('agents-container');
                container.innerHTML = '';

                for (const [name, status] of Object.entries(data.agents)) {
                    const card = document.createElement('div');
                    card.className = 'agent-card';
                    card.innerHTML = `
                        <div class="agent-name">${name}</div>
                        <div class="agent-status">Status: ${status.status}</div>
                    `;
                    container.appendChild(card);
                }
            }

            // Update metrics
            if (data.metrics) {
                document.getElementById('metric-requests').textContent =
                    data.metrics.deconfliction_requests || 0;
                document.getElementById('metric-approvals').textContent =
                    data.metrics.deconfliction_approvals || 0;
                document.getElementById('metric-denials').textContent =
                    data.metrics.deconfliction_denials || 0;
                document.getElementById('metric-violations').textContent =
                    data.metrics.roe_violations || 0;
            }
        }

        function addEventToFeed(event) {
            const container = document.getElementById('events-container');

            // Clear "waiting" message
            if (container.querySelector('p')) {
                container.innerHTML = '';
            }

            const eventEl = document.createElement('div');
            eventEl.className = 'event';

            // Determine event class based on type
            if (event.level === 'error') {
                eventEl.classList.add('event-error');
            } else if (event.level === 'warning') {
                eventEl.classList.add('event-warning');
            }

            const time = new Date(event.timestamp).toLocaleTimeString();
            const content = event.message || event.event || JSON.stringify(event);

            eventEl.innerHTML = `
                <div class="event-time">${time}</div>
                <div class="event-content">${content}</div>
            `;

            container.insertBefore(eventEl, container.firstChild);

            // Keep only last 20 events
            while (container.children.length > 20) {
                container.removeChild(container.lastChild);
            }
        }

        // Connect on page load
        connect();

        // Fetch initial status
        fetch('/api/status')
            .then(r => r.json())
            .then(updateStatus)
            .catch(console.error);
    </script>
</body>
</html>
    """


if __name__ == "__main__":
    import uvicorn

    config = get_config()

    logger.info(
        "starting_web_server",
        host=config.web_dashboard.host,
        port=config.web_dashboard.port
    )

    uvicorn.run(
        app,
        host=config.web_dashboard.host,
        port=config.web_dashboard.port,
        log_level="info"
    )
