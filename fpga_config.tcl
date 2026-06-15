# ================================================================
# FPGA Automation Tool — Configuration Template
# LogicLance Compatible
#
# Copy this file and edit for your project.
# Usage: Provide values to run_fpga or use interactively.
# ================================================================

# ──── PROJECT ────
# Option A: Path to existing Vivado project
set PROJECT_XPR       ""          ;# e.g. "/path/to/project.xpr"

# Option B: Create new project (leave PROJECT_XPR empty)
set FPGA_PART         ""          ;# e.g. "xczu7ev-ffvc1156-2-e"
set BOARD_PART        ""          ;# e.g. "xilinx.com:zcu106:part0:2.6"
set PROJECT_NAME      "my_project"
set PROJECT_DIR       "./my_project"
set IP_REPO_PATHS     [list]      ;# List of IP repository directories
set SOURCE_FILES      [list]      ;# List of source HDL files/directories
set BD_TCL_SCRIPT     ""          ;# Path to block design Tcl script (optional)

# ──── TESTBENCH ────
set TB_TOP            ""          ;# Testbench top module name
set TB_FILES          [list]      ;# Explicit list of TB file paths
set TB_DIR            ""          ;# OR: directory for auto-discovery
set TB_INCLUDES       [list]      ;# Include directories
set TB_DEFINES        [list SIM=1] ;# Verilog defines

# ──── SIMULATION ────
set SIM_MODE          "post-implementation"  ;# post-synthesis | post-implementation
set SIM_TYPE          "functional"           ;# functional | timing

# ──── C-MODEL (optional) ────
set CMODEL_ENABLE     0
set CMODEL_DIR        ""          ;# Directory containing Makefile
set CMODEL_CLEAN_TARGET "clean"
set CMODEL_BUILD_TARGETS [list]   ;# e.g. [list compiler conv_controller comparator]
set CMODEL_RUN_TARGET "manual"
set CMODEL_STDIN      ""          ;# Input file (parameter answers)
set CMODEL_STDOUT     ""          ;# Capture golden output here
set CMODEL_LOG        ""          ;# Log file
set CMODEL_TIMEOUT    900         ;# 15 minutes

# ──── REGRESSION (optional) ────
# Each entry: {name "tc1" stdin "/path/in.txt" stdout "/path/out.txt"}
set TEST_CASES        [list]
set RESULT_FILE       ""          ;# TB writes PASS/FAIL markers here
set PASS_PATTERN      "TEST_PASSED"
set FAIL_PATTERN      "TEST_FAILED"
set CMODEL_OUT_FIXED  ""          ;# Fixed path TB reads C-model output from
set CMODEL_LOG_DIR    ""
set SIM_LOG_DIR       ""

# ──── GIT (optional) ────
set GIT_ENABLE        0
set GIT_REPO          ""
set GIT_COMMIT        ""
set GIT_DEST          ""
set GIT_SUBDIR        ""          ;# Empty for full repo

# ──── OUTPUT ────
set OUTPUT_BIT        ""          ;# Empty to skip bitstream
set OUTPUT_XSA        ""          ;# Empty to skip XSA export
set SYNTH_JOBS        4
set IMPL_JOBS         8
