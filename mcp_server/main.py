"""
EMBM-J DS MCP Server - Main FastAPI Application

This server implements the Model Context Protocol (MCP) to provide
spectrum management tools to AI agents.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
import structlog
from datetime import datetime, timezone
import os

from .models import MCPRequest, MCPResponse, MCPError
from . import tools

# Configure file logging
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from logging_config import configure_logging, get_logger as get_file_logger

configure_logging(log_level="INFO", log_to_file=True)

logger = structlog.get_logger("mcp_server")

# Create FastAPI app
app = FastAPI(
    title="EMBM-J DS MCP Server",
    description="Mock EMBM-J DS system implementing MCP for agent interaction",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Tool registry mapping method names to handler functions
TOOL_REGISTRY = {
    "get_spectrum_plan": tools.get_spectrum_plan,
    "request_deconfliction": tools.request_deconfliction,
    "allocate_frequency": tools.allocate_frequency,
    "report_emitter": tools.report_emitter,
    "analyze_coa_impact": tools.analyze_coa_impact,
    "get_interference_report": tools.get_interference_report,
}


@app.post("/mcp")
async def mcp_endpoint(request: Request) -> JSONResponse:
    """
    Main MCP endpoint implementing JSON-RPC 2.0 protocol.

    Accepts tool calls from agents and routes them to appropriate handlers.
    """
    try:
        # Parse request body
        body = await request.json()
        logger.info("mcp_request_received", method=body.get("method"))

        # Validate JSON-RPC 2.0 structure
        if body.get("jsonrpc") != "2.0":
            return _error_response(
                -32600,
                "Invalid Request: jsonrpc must be '2.0'",
                body.get("id")
            )

        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")

        if not method:
            return _error_response(
                -32600,
                "Invalid Request: method is required",
                request_id
            )

        # Route to appropriate tool
        if method not in TOOL_REGISTRY:
            logger.warning("method_not_found", method=method)
            return _error_response(
                -32601,
                f"Method not found: {method}",
                request_id
            )

        # Execute tool
        try:
            handler = TOOL_REGISTRY[method]
            result = await handler(**params)

            logger.info(
                "mcp_request_success",
                method=method,
                request_id=request_id
            )

            return JSONResponse({
                "jsonrpc": "2.0",
                "result": result,
                "id": request_id
            })

        except TypeError as e:
            logger.error("invalid_params", method=method, error=str(e))
            return _error_response(
                -32602,
                f"Invalid params: {str(e)}",
                request_id
            )

        except Exception as e:
            logger.error("tool_execution_error", method=method, error=str(e))
            return _error_response(
                -32603,
                f"Internal error: {str(e)}",
                request_id
            )

    except Exception as e:
        logger.error("request_parsing_error", error=str(e))
        return _error_response(
            -32700,
            "Parse error: Invalid JSON",
            None
        )


@app.get("/mcp/tools")
async def list_tools() -> Dict[str, Any]:
    """
    List all available MCP tools with their schemas.

    This endpoint allows agents to discover available tools.
    """
    tools_list = [
        {
            "name": "get_spectrum_plan",
            "description": "Retrieve current spectrum allocation plan for an area and time period",
            "input_schema": {
                "type": "object",
                "properties": {
                    "ao_geojson": {"type": "string", "description": "Area of operations as GeoJSON polygon"},
                    "start_time": {"type": "string", "format": "date-time", "description": "Start time (ISO 8601)"},
                    "end_time": {"type": "string", "format": "date-time", "description": "End time (ISO 8601)"}
                },
                "required": ["ao_geojson", "start_time", "end_time"]
            }
        },
        {
            "name": "request_deconfliction",
            "description": "Request spectrum deconfliction for a proposed frequency allocation",
            "input_schema": {
                "type": "object",
                "properties": {
                    "asset_rid": {"type": "string"},
                    "frequency_mhz": {"type": "number"},
                    "bandwidth_khz": {"type": "number"},
                    "power_dbm": {"type": "number"},
                    "location": {
                        "type": "object",
                        "properties": {
                            "lat": {"type": "number"},
                            "lon": {"type": "number"}
                        },
                        "required": ["lat", "lon"]
                    },
                    "start_time": {"type": "string", "format": "date-time"},
                    "duration_minutes": {"type": "integer"},
                    "priority": {"type": "string", "enum": ["ROUTINE", "PRIORITY", "IMMEDIATE", "FLASH"]},
                    "purpose": {"type": "string"}
                },
                "required": ["asset_rid", "frequency_mhz", "bandwidth_khz", "power_dbm", "location", "start_time", "duration_minutes", "priority", "purpose"]
            }
        },
        {
            "name": "allocate_frequency",
            "description": "Allocate a frequency after successful deconfliction",
            "input_schema": {
                "type": "object",
                "properties": {
                    "asset_id": {"type": "string"},
                    "frequency_mhz": {"type": "number"},
                    "bandwidth_khz": {"type": "number"},
                    "duration_minutes": {"type": "integer"},
                    "authorization_id": {"type": "string"},
                    "location": {"type": "object"},
                    "power_dbm": {"type": "number"},
                    "priority": {"type": "string"},
                    "purpose": {"type": "string"},
                    "service": {"type": "string"}
                },
                "required": ["asset_id", "frequency_mhz", "bandwidth_khz", "duration_minutes", "authorization_id", "location", "power_dbm", "priority", "purpose"]
            }
        },
        {
            "name": "report_emitter",
            "description": "Report a detected electromagnetic emitter",
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {"type": "object"},
                    "frequency_mhz": {"type": "number"},
                    "bandwidth_khz": {"type": "number"},
                    "signal_characteristics": {"type": "object"},
                    "detection_time": {"type": "string", "format": "date-time"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                },
                "required": ["location", "frequency_mhz", "bandwidth_khz", "signal_characteristics", "detection_time", "confidence"]
            }
        },
        {
            "name": "analyze_coa_impact",
            "description": "Analyze the impact of a Course of Action",
            "input_schema": {
                "type": "object",
                "properties": {
                    "coa_id": {"type": "string"},
                    "friendly_actions": {"type": "array", "items": {"type": "object"}}
                },
                "required": ["coa_id", "friendly_actions"]
            }
        },
        {
            "name": "get_interference_report",
            "description": "Get interference report for a location and frequency range",
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {"type": "object"},
                    "frequency_range_mhz": {
                        "type": "object",
                        "properties": {
                            "min": {"type": "number"},
                            "max": {"type": "number"}
                        }
                    }
                },
                "required": ["location", "frequency_range_mhz"]
            }
        }
    ]

    return {
        "tools": tools_list,
        "server_info": {
            "name": "EMBM-J DS Mock Server",
            "version": "0.1.0",
            "protocol_version": "mcp/1.0"
        }
    }


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "EMBM-J DS MCP Server"
    }


@app.get("/", response_class=HTMLResponse)
async def root() -> str:
    """Root endpoint with service information."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>EMBM-J DS MCP Server</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                max-width: 900px;
                margin: 0 auto;
                padding: 40px 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container {
                background: white;
                border-radius: 10px;
                padding: 40px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            }
            h1 {
                color: #333;
                margin-top: 0;
                border-bottom: 3px solid #667eea;
                padding-bottom: 10px;
            }
            .info {
                background: #f5f5f5;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }
            .endpoint {
                background: #e8f4f8;
                padding: 12px;
                margin: 10px 0;
                border-left: 4px solid #667eea;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
            }
            .endpoint-desc {
                color: #666;
                font-size: 0.9em;
                margin-top: 5px;
            }
            .status {
                display: inline-block;
                background: #4CAF50;
                color: white;
                padding: 5px 10px;
                border-radius: 3px;
                font-size: 0.9em;
                margin-left: 10px;
            }
            a {
                color: #667eea;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
            .links {
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🛰️ EMBM-J DS MCP Server <span class="status">Healthy</span></h1>

            <div class="info">
                <p><strong>Service:</strong> EMBM-J DS MCP Server</p>
                <p><strong>Version:</strong> 0.1.0</p>
                <p><strong>Description:</strong> Mock EMBM-J DS system implementing Model Context Protocol (MCP) for agent interaction</p>
            </div>

            <h2>📡 Available Endpoints</h2>

            <div class="endpoint">
                <strong>GET /health</strong>
                <div class="endpoint-desc">Health check endpoint - Returns server status</div>
            </div>

            <div class="endpoint">
                <strong>GET /mcp/tools</strong>
                <div class="endpoint-desc">List all available MCP tools with their schemas</div>
            </div>

            <div class="endpoint">
                <strong>POST /mcp</strong>
                <div class="endpoint-desc">Main MCP endpoint - Execute tool calls via JSON-RPC 2.0</div>
            </div>

            <div class="endpoint">
                <strong>GET /docs</strong>
                <div class="endpoint-desc">Interactive API documentation (Swagger UI)</div>
            </div>

            <div class="endpoint">
                <strong>GET /redoc</strong>
                <div class="endpoint-desc">Alternative API documentation (ReDoc)</div>
            </div>

            <div class="links">
                <h3>🔗 Quick Links</h3>
                <ul>
                    <li><a href="/health">Health Check</a></li>
                    <li><a href="/mcp/tools">List Tools</a></li>
                    <li><a href="/docs">API Documentation</a></li>
                    <li><a href="/redoc">ReDoc Documentation</a></li>
                </ul>
            </div>

            <div class="info" style="margin-top: 30px; background: #f0f7ff; border-left: 4px solid #667eea;">
                <h3 style="margin-top: 0;">ℹ️ About MCP</h3>
                <p>The Model Context Protocol (MCP) is a standardized protocol for AI agents to interact with external tools and services. This server provides spectrum management tools for the EMBM-J DS system.</p>
            </div>
        </div>
    </body>
    </html>
    """


def _error_response(code: int, message: str, request_id: Any) -> JSONResponse:
    """Create a JSON-RPC 2.0 error response."""
    return JSONResponse({
        "jsonrpc": "2.0",
        "error": {
            "code": code,
            "message": message
        },
        "id": request_id
    })


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize server on startup."""
    logger.info(
        "server_starting",
        service="EMBM-J DS MCP Server",
        version="0.1.0"
    )

    # Initialize with some sample data for testing
    from .data.allocations import allocation_store
    from .models import FrequencyAllocation, Location, ServiceBranch, Priority
    from datetime import timezone

    # Add sample allocations (using timezone-aware datetimes)
    now = datetime.now(timezone.utc)
    end_of_day = now.replace(hour=23, minute=59, second=59)

    sample_allocations = [
        FrequencyAllocation(
            asset_id="ASSET-001",
            frequency_mhz=150.0,
            bandwidth_khz=25.0,
            location=Location(lat=35.0, lon=45.0),
            start_time=now,
            end_time=end_of_day,
            service=ServiceBranch.AIR_FORCE,
            priority=Priority.ROUTINE,
            power_dbm=40.0,
            purpose="Training exercise communication"
        ),
        FrequencyAllocation(
            asset_id="ASSET-002",
            frequency_mhz=225.5,
            bandwidth_khz=25.0,
            location=Location(lat=35.2, lon=45.3),
            start_time=now,
            end_time=end_of_day,
            service=ServiceBranch.NAVY,
            priority=Priority.PRIORITY,
            power_dbm=45.0,
            purpose="Maritime patrol coordination"
        )
    ]

    for allocation in sample_allocations:
        await allocation_store.add(allocation)

    logger.info("sample_data_loaded", count=len(sample_allocations))


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on server shutdown."""
    logger.info("server_shutting_down")


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("EMBM_SERVER_PORT", "8000"))

    uvicorn.run(
        "mcp_server.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
