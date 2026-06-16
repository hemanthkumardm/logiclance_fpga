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

# Linux-specific: Qt / XCB runtime libraries (very common on other laptops)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo
    echo -e "${YELLOW}[Linux only] GUI (PyQt5) often needs extra system libraries on other machines.${NC}"
    echo "If you later see the error:"
    echo "  'Could not load the Qt platform plugin \"xcb\"'"
    echo "Run this on the target laptop:"
    echo
    echo "  sudo apt update"
    echo "  sudo apt install -y \\"
    echo "      libxcb-xinerama0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \\"
    echo "      libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-xfixes0 \\"
    echo "      libxkbcommon-x11-0 libgl1-mesa-glx"
    echo
    echo "Then re-run the tool."
    echo
fi

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
echo "Important: When running on a *different* laptop (especially Ubuntu/Gnome/Wayland),"
echo "the GUI may fail with an 'xcb' plugin error. The required system packages"
echo "are listed above during setup. Install them and try again."
echo
echo -e "${BLUE}──────────────────────────────────────────────────────────────${NC}"
echo
echo "Run the following command anytime to re-verify your environment:"
echo "    python3 -c \"from fpga_tool.flow_utils import verify_environment; verify_environment()\""
echo
