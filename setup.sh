#!/bin/bash
#
# LogicLance FPGA Automation Tool
# One-Time Setup Script
#
# This is the SINGLE command you need to run for first-time setup.
#
# It will:
#   1. Install all Python requirements (PyQt5, rich, etc.)
#   2. Install this package in editable mode
#   3. Make launcher scripts executable
#   4. Verify all external tools: Vivado, gcc, make
#
# Usage:
#   ./setup.sh
#
# You can safely re-run this script anytime.
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     LogicLance FPGA Tool — One-Time Setup (setup.sh)         ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${GREEN}[Step 1] Checking Python 3...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: python3 not found. Please install Python 3.8 or newer.${NC}"
    exit 1
fi
python3 --version

if ! python3 -c "import pip" &> /dev/null 2>&1; then
    echo -e "${YELLOW}pip not available as module. Trying to ensure pip...${NC}"
    python3 -m ensurepip --upgrade || true
fi

PIP_CMD="python3 -m pip"

echo
echo -e "${GREEN}[Step 2] Installing Python dependencies from requirements.txt...${NC}"
$PIP_CMD install --upgrade pip
$PIP_CMD install -r requirements.txt

echo
echo -e "${GREEN}[Step 3] Installing logiclance-fpga in editable mode...${NC}"
$PIP_CMD install -e .

echo
echo -e "${GREEN}[Step 4] Making launcher scripts executable...${NC}"
chmod +x run_fpga run_fpga_gui.py
echo "  ✓ run_fpga"
echo "  ✓ run_fpga_gui.py"

echo
echo -e "${GREEN}[Step 5] Verifying external tools (Vivado, gcc, make)...${NC}"
echo

# Run verification using the installed package
python3 -c "
from fpga_tool.flow_utils import verify_environment, check_dependencies
print()
verify_environment(require_vivado=True, require_cmodel_tools=False)
print()
print('Detailed status:')
deps = check_dependencies()
for tool, path in deps.items():
    if path:
        print(f'  ✅ {tool.upper():8} → {path}')
    else:
        print(f'  ❌ {tool.upper():8} → NOT FOUND')
"

echo
echo -e "${BLUE}──────────────────────────────────────────────────────────────${NC}"
echo -e "${GREEN}Setup completed!${NC}"
echo
echo "You can now start the tool with:"
echo "    ./run_fpga"
echo "    or"
echo "    python3 run_fpga"
echo "    or (if the console script was created)"
echo "    run-fpga-gui"
echo
echo "Tip: If Vivado is not found, set the environment variable:"
echo "    export XILINX_VIVADO=/opt/VIVADO/2025.2/Vivado"
echo
echo -e "${BLUE}──────────────────────────────────────────────────────────────${NC}"
echo
echo "Run the following command anytime to re-verify your environment:"
echo "    python3 -c \"from fpga_tool.flow_utils import verify_environment; verify_environment()\""
echo
