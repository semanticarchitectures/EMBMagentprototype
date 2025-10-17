#!/bin/bash
# Quick test of MCP server

echo "Testing MCP server health endpoint..."
curl -s http://localhost:8000/health | python3 -m json.tool

echo
echo "Testing MCP tools list..."
curl -s http://localhost:8000/mcp/tools | python3 -m json.tool
