#!/bin/bash

# EMBM Agent Prototype Setup Script
# This script sets up the development environment

set -e  # Exit on error

echo "=========================================="
echo "EMBM Agent Prototype Setup"
echo "=========================================="
echo

# Check Python version
echo "Checking Python version..."
if ! command -v python3.11 &> /dev/null; then
    echo "Warning: python3.11 not found. Trying python3..."
    PYTHON_CMD=python3
else
    PYTHON_CMD=python3.11
fi

$PYTHON_CMD --version
echo

# Create virtual environment
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists. Skipping..."
else
    $PYTHON_CMD -m venv venv
    echo "Virtual environment created."
fi
echo

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip --quiet
echo

# Install dependencies
echo "Installing dependencies..."
pip install -e ".[dev,dashboard]" --quiet
echo "Dependencies installed."
echo

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo ".env file created."
    echo
    echo "⚠️  IMPORTANT: Please edit .env and add your API keys:"
    echo "   - ANTHROPIC_API_KEY"
    echo "   - OPENAI_API_KEY (optional)"
    echo
else
    echo ".env file already exists. Skipping..."
    echo
fi

# Create necessary directories
echo "Creating data directories..."
mkdir -p logs
mkdir -p data
mkdir -p evaluation/results
touch data/.gitkeep
touch evaluation/results/.gitkeep
echo "Directories created."
echo

# Create a simple test script
echo "Creating test script..."
cat > scripts/test_server.sh << 'EOF'
#!/bin/bash
# Quick test of MCP server

echo "Testing MCP server health endpoint..."
curl -s http://localhost:8000/health | python3 -m json.tool

echo
echo "Testing MCP tools list..."
curl -s http://localhost:8000/mcp/tools | python3 -m json.tool
EOF

chmod +x scripts/test_server.sh
echo "Test script created at scripts/test_server.sh"
echo

echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo
echo "Next steps:"
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo
echo "2. Edit .env file and add your API keys"
echo
echo "3. Start the MCP server:"
echo "   python scripts/run_server.py"
echo
echo "4. In another terminal, test the server:"
echo "   ./scripts/test_server.sh"
echo
echo "For more information, see README.md"
echo
