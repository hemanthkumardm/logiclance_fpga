# FPGA Automation Tool — User Reference

> **Version**: 1.0.0  
> **Author**: Hemanth Kumar DM  
> **Compatibility**: Xilinx Vivado 2024.1+ | Python 3.8+  
> **License**: LogicLance © 2026

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Directory Structure](#directory-structure)
4. [Quick Start](#quick-start)
5. [CLI Usage](#cli-usage)
6. [Flow 1 — Post-Implementation Simulation](#flow-1--post-implementation-simulation)
7. [Flow 2 — C-Model + Simulation](#flow-2--c-model--simulation)
8. [Flow 3 — Multi-Test Regression](#flow-3--multi-test-regression)
9. [Flow 4 — Full Flow (Synth → Impl → Test → XSA)](#flow-4--full-flow-synth--impl--test--xsa)
10. [Rerun Support](#rerun-support)
11. [Config Template](#config-template)
12. [Output & Logs](#output--logs)
13. [Troubleshooting](#troubleshooting)
14. [LogicLance Integration](#logiclance-integration)

---

## Overview

The **FPGA Automation Tool** is a generic, design-independent automation framework for Xilinx/AMD Vivado FPGA workflows. It replaces hardcoded, project-specific Tcl scripts with an interactive Python+Tcl hybrid that works with **any** Vivado project.

### Supported Flows

| # | Flow | Description |
|---|------|-------------|
| 1 | **Post-Impl Simulation** | Run a testbench against the routed netlist |
| 2 | **C-Model + Simulation** | Build & run a C/SystemC golden model, then simulate |
| 3 | **Multi-Test Regression** | Run multiple test vectors with PASS/FAIL gating |
| 4 | **Full Flow** | Synth → Impl → Regression → Bitstream → XSA export |

### How It Works

```
User → python3 run_fpga → Interactive Prompts → Generates _config.tcl
    → vivado -mode batch -source flow.tcl -tclargs _config.tcl
    → Real-time colored output → Results summary
```

Python collects all inputs, generates a Tcl config file, launches Vivado in batch mode, streams output with color coding, and parses results.

---

## Prerequisites

### Required

| Requirement | Details |
|-------------|---------|
| **Python 3.8+** | Standard library only — no pip packages needed |
| **Xilinx Vivado** | 2024.1 or later recommended |

### Vivado Setup

The tool auto-detects Vivado. Set one of these:

```bash
# Option 1: Environment variable (recommended)
export XILINX_VIVADO=/tools/Xilinx/Vivado/2024.1

# Option 2: Add to PATH
export PATH=/tools/Xilinx/Vivado/2024.1/bin:$PATH
```

The tool searches in this order:
1. `$XILINX_VIVADO/bin/vivado`
2. `vivado` on system `$PATH`
3. Common install paths (`/opt/Xilinx/Vivado/`, `/tools/Xilinx/Vivado/`)

---

## Directory Structure

```
XSA_scripts/
├── run_fpga                          # Entry point — run this
├── fpga_tool/                        # Python package
│   ├── __init__.py                   #   Package init
│   ├── flow_utils.py                 #   Logger, input handler, state manager
│   ├── tcl_gen.py                    #   Python → Tcl config generator
│   ├── fpga_parser.py                #   Result & report parser
│   └── run_fpga_xilinx.py            #   Xilinx/Vivado flow implementations
├── tcl/                              # Vivado Tcl scripts (executed by Vivado)
│   ├── lib/utils.tcl                 #   Common Tcl helpers
│   ├── sim_single.tcl                #   Flow 1: single simulation
│   ├── cmod_sim.tcl                  #   Flow 2: C-model + simulation
│   ├── regression.tcl                #   Flow 3: multi-test regression
│   └── full_flow.tcl                 #   Flow 4: end-to-end
├── configs/
│   └── config_template.tcl           # Annotated config template
├── original/                         # Backup of original design-specific scripts
│   ├── sim1.tcl
│   ├── cmod_sim.tcl
│   ├── cmod_sim_mult.tcl
│   └── Test_proj.tcl
└── USER_REFERENCE.md                 # This file
```

---

## Quick Start

### 1. Copy to your server

Copy the entire `XSA_scripts/` folder to the machine where Vivado is installed:

```bash
scp -r XSA_scripts/ user@server:/path/to/
```

### 2. Set up Vivado

```bash
export XILINX_VIVADO=/opt/VIVADO/2025.2/Vivado/bin/vivado
```

### 3. Run a simulation

```bash
cd /path/to/XSA_scripts
python3 run_fpga --flow sim
```

The tool will prompt for:
- Project path (`.xpr`)
- Testbench top module name
- Testbench source files
- Simulation settings

Then it launches Vivado automatically.

---

## GUI Usage

A light-themed, user-friendly PyQt5 GUI is available to easily configure and launch flows without using the command line.

```bash
# Launch the GUI
python3 run_fpga_gui.py
```

### Features:
1. **Flow Selection**: Use the top dropdown to select the flow. The form will dynamically show only the fields needed for that flow.
2. **File Browsers**: Click `Browse...` next to any path field to easily select directories and files.
3. **Save/Load State**: Click "Load Last Run Config" to instantly populate the form with values from your previous run.
4. **Live Log**: The bottom pane shows real-time color-coded Vivado execution output.

---

## CLI Usage

### Interactive Menu

```bash
python3 run_fpga
```

Displays:
```
╔════════════════════════════════════════════════════╗
║         FPGA Automation Tool v1.0                  ║
║         (LogicLance Compatible)                    ║
╠════════════════════════════════════════════════════╣
║  1 │ Post-Implementation Simulation               ║
║  2 │ C-Model + Simulation                         ║
║  3 │ Multi-Test Regression                        ║
║  4 │ Full Flow (Synth → Impl → Test → XSA)        ║
║  5 │ Generate Config Template                      ║
║  0 │ Exit                                          ║
╚════════════════════════════════════════════════════╝
```

### Command-Line Flags

| Flag | Description | Example |
|------|-------------|---------|
| `--flow <name>` | Skip menu, run a flow directly | `--flow sim` |
| `--rerun` | Repeat the last run with saved inputs | `--rerun` |
| `--generate-config` | Write `fpga_config.tcl` template to current dir | `--generate-config` |
| `--verbose` | Enable debug-level output | `--verbose` |
| `--watch` | Phase 3: Continuous monitoring mode with intelligent delta-driven re-runs | `--watch --flow regression` |
| `--optimize` / `--opt` | Phase 3: Enable optimizer for history-guided strategy search and limited auto-retries on failure | `--optimize --flow full` |
| `--no-intel` | Disable all intelligence features (design model, reports, optimizer, watch) | `--no-intel --flow sim` |

### Flow Name Shortcuts

| Shortcut | Flow |
|----------|------|
| `sim` | Post-Implementation Simulation |
| `cmod` | C-Model + Simulation |
| `regression` | Multi-Test Regression |
| `full` | Full Flow (Synth → Impl → Test → XSA) |

### Examples

```bash
# Interactive menu
python3 run_fpga

# Direct flow selection
python3 run_fpga --flow sim
python3 run_fpga --flow cmod
python3 run_fpga --flow regression
python3 run_fpga --flow full

# Repeat last run (no prompts)
python3 run_fpga --rerun

# Debug mode
python3 run_fpga --flow sim --verbose

# Generate config template
python3 run_fpga --generate-config
```

---

## Flow 1 — Post-Implementation Simulation

**What it does**: Opens an existing Vivado project, loads the implemented (placed & routed) netlist, and runs a functional simulation using XSIM.

**When to use**: Quick verification that your design works correctly after place-and-route.

**Requirements**:
- An existing Vivado project (`.xpr`) with synthesis and implementation already completed
- A testbench file (`.sv` / `.v`)

### Prompts

```
──────────────────────────────────────────────────
  PROJECT CONFIGURATION
──────────────────────────────────────────────────
Vivado project path (.xpr): /path/to/project/project.xpr

──────────────────────────────────────────────────
  TESTBENCH CONFIGURATION
──────────────────────────────────────────────────
Testbench top module name: AcceleratorWrapperTB
Testbench source: [1] File list  [2] Auto-discover from directory [1]: 1
Testbench file(s) [space-separated paths]: /path/to/BehavioralTB.sv
Include directories [space-separated, or empty] []: 
Verilog defines [space-separated] [SIM=1]: SIM=1

──────────────────────────────────────────────────
  SIMULATION SETTINGS
──────────────────────────────────────────────────
Simulation mode (post-synthesis / post-implementation) [post-implementation]: 
Simulation type (functional / timing) [functional]: 
```

### Prompt Details

| Prompt | What to Enter | Default |
|--------|---------------|---------|
| **Vivado project path** | Full absolute path to your `.xpr` file | *(none — required)* |
| **Testbench top module** | The module/entity name of your TB (not the filename) | *(none — required)* |
| **Testbench source** | `1` for explicit file paths, `2` to scan a directory | `1` |
| **Testbench file(s)** | Space-separated absolute paths to `.sv`/`.v` files | *(none — required)* |
| **Include directories** | Paths to directories with `` `include `` headers | *(empty)* |
| **Verilog defines** | Space-separated defines like `SIM=1 DEBUG=0` | `SIM=1` |
| **Simulation mode** | `post-synthesis` or `post-implementation` | `post-implementation` |
| **Simulation type** | `functional` (no timing) or `timing` (with SDF) | `functional` |

### Example

```bash
python3 run_fpga --flow sim
# Enter:
#   Project: /mnt/data/vivado/my_design/my_design.xpr
#   TB top:  my_testbench
#   TB file: /mnt/data/vivado/my_design/sim/my_testbench.sv
#   Mode:    post-implementation
#   Type:    functional
```

---

## Flow 2 — C-Model + Simulation

**What it does**: First builds and runs a C/SystemC golden reference model (using `make`), captures its output, then runs the Vivado post-implementation simulation so the testbench can compare against the golden output.

**When to use**: When you have a software reference model that produces expected output that your RTL testbench compares against.

**Requirements**:
- Everything from Flow 1
- A C-model project directory with a Makefile
- An input file (stdin parameters for the C-model)

### Additional Prompts (C-Model Section)

```
──────────────────────────────────────────────────
  C-MODEL CONFIGURATION
──────────────────────────────────────────────────
C-model directory (contains Makefile): /path/to/cmodel/
C-model stdin input file: /path/to/cmod_in.txt
C-model stdout capture file (golden output) []: /path/to/out_golden.txt
Make clean target [clean]: clean
Make run target [manual]: manual
Make build targets [space-separated, or empty]: compiler conv_controller comparator
C-model timeout (seconds) [900]: 900
C-model log file path [./output/cmodel_run.log]: 
```

### Prompt Details

| Prompt | What to Enter | Default |
|--------|---------------|---------|
| **C-model directory** | Path to directory containing the Makefile | *(required)* |
| **C-model stdin file** | Input file with parameters (one per line) | *(required)* |
| **C-model stdout file** | Where to save the golden output | *(empty)* |
| **Make clean target** | The `make` target for cleaning | `clean` |
| **Make run target** | The `make` target for running the model | `manual` |
| **Make build targets** | Space-separated build targets (e.g., `compiler conv_controller`) | *(empty = default make)* |
| **Timeout** | Max seconds for C-model execution | `900` (15 min) |
| **Log file** | Where to write build/run logs | `./output/cmodel_run.log` |

### C-Model Input File Example

The stdin file contains one value per line, answering the C-model's interactive prompts:
```
32
32
32
3
3
32
2
2
0
0
0
0
```

---

## Flow 3 — Multi-Test Regression

**What it does**: Runs multiple test cases in sequence. For each test case: launches the C-model asynchronously with that test's inputs, runs the post-implementation simulation, reads a `RESULT.txt` file for PASS/FAIL markers, and produces a summary table.

**When to use**: Regression testing with multiple test vectors before tapeout or bitstream generation.

**Requirements**:
- Everything from Flow 2
- Multiple test case input files
- Your testbench must write `TEST_PASSED` or `TEST_FAILED` to a result file

### Additional Prompts (Regression Section)

```
──────────────────────────────────────────────────
  REGRESSION TEST CASES
──────────────────────────────────────────────────
Result file path (TB writes PASS/FAIL here): /path/to/RESULT.txt
Pass pattern in result file [TEST_PASSED]: TEST_PASSED
Fail pattern in result file [TEST_FAILED]: TEST_FAILED
Fixed C-model output path (TB reads this) []: /path/to/CMODEL_OUT.txt
C-model log directory [./output/cmodel_logs]: 
Simulation log directory [./output/sim_logs]: 

  Add test cases (enter empty name to finish):
  Test case 1 name (empty to finish): tc1
  Test case 1 stdin file: /path/to/cmod_in_tc1.txt
  Test case 1 stdout file []: /path/to/out_golden_tc1.txt
  Test case 2 name (empty to finish): tc2
  Test case 2 stdin file: /path/to/cmod_in_tc2.txt
  Test case 2 stdout file []: /path/to/out_golden_tc2.txt
  Test case 3 name (empty to finish): 
```

### Prompt Details

| Prompt | What to Enter | Default |
|--------|---------------|---------|
| **Result file** | File your TB writes PASS/FAIL markers to | *(required)* |
| **Pass pattern** | String to search for in result file indicating pass | `TEST_PASSED` |
| **Fail pattern** | String to search for indicating failure | `TEST_FAILED` |
| **Fixed C-model output** | Path the TB reads golden output from | *(empty)* |
| **Test case name** | Short identifier (e.g., `tc1`, `tc2`) | *(empty = done adding)* |
| **Test case stdin** | Input file for this test case | *(required per test)* |
| **Test case stdout** | Where to capture C-model output for this test | *(empty)* |

### Output Example

```
==================================================
  TEST RESULTS SUMMARY
==================================================
  tc1                  : ✔ PASS
  tc2                  : ✔ PASS
  tc3                  : ✘ FAIL
--------------------------------------------------
  PASSED : 2
  FAILED : 1
  UNKNOWN: 0
==================================================
```

### Testbench Requirement

Your testbench **must** write to the result file. Example SystemVerilog:

```systemverilog
// At end of simulation:
integer result_fd;
initial begin
    // ... run tests ...
    result_fd = $fopen("RESULT.txt", "w");
    if (all_tests_passed)
        $fwrite(result_fd, "TEST_PASSED\n");
    else
        $fwrite(result_fd, "TEST_FAILED\n");
    $fclose(result_fd);
    $finish;
end
```

---

## Flow 4 — Full Flow (Synth → Impl → Test → XSA)

**What it does**: End-to-end automation — from project creation through bitstream and XSA export:

1. **Optional**: Clone IP sources from Git
2. **Create or open** Vivado project
3. **Run synthesis**
4. **Run implementation** (place & route)
5. **Optional**: Run post-implementation regression tests
6. **Optional**: Generate bitstream (`.bit`)
7. **Optional**: Export hardware platform (`.xsa`)

**When to use**: CI/CD pipelines, one-command builds, clean server builds.

### Additional Prompts

```
──────────────────────────────────────────────────
  PROJECT SOURCE
──────────────────────────────────────────────────
Project mode: [1] Open existing .xpr  [2] Create new project [1]: 

  (If [1]) Vivado project path (.xpr): /path/to/project.xpr

  (If [2]) FPGA part: xczu7ev-ffvc1156-2-e
           Board part [optional]: xilinx.com:zcu106:part0:2.6
           Project name [fpga_project]: my_accelerator
           IP repository paths: /path/to/ip_repo
           Source HDL files/dirs: /path/to/src/
           Block design Tcl script [optional]: /path/to/bd.tcl

──────────────────────────────────────────────────
  GIT SOURCE (optional)
──────────────────────────────────────────────────
Clone/update IP sources from Git? [y/N]: n

──────────────────────────────────────────────────
  BUILD OUTPUT
──────────────────────────────────────────────────
Output bitstream path (.bit) [empty to skip]: ./output/design.bit
Output XSA path (.xsa) [empty to skip]: ./output/design.xsa
Synthesis parallel jobs [4]: 4
Implementation parallel jobs [8]: 8

Run post-implementation regression tests? [Y/n]: y
  (... then TB and regression prompts from Flows 1-3 ...)
```

### Regression Gate Behavior

If regression tests are enabled and **any test fails**, the tool:
- Prints the failure summary
- **Skips bitstream and XSA generation**
- Exits with code `1`

This makes it safe to use in CI/CD — bad designs don't produce outputs.

---

## Rerun Support

Every successful flow saves its configuration to `.fpga_tool_state.json`. Use `--rerun` to repeat:

```bash
# First run (interactive — all prompts)
python3 run_fpga --flow sim

# Later — repeat with exact same inputs (no prompts)
python3 run_fpga --rerun
```

The saved state includes:
- Flow type
- All user-provided values (paths, settings, test cases)
- Vendor selection
- Run ID

This is useful for:
- Re-running after RTL changes
- Quick iteration during debugging
- Scripting repeated runs

---

## Config Template

Generate an annotated config template:

```bash
python3 run_fpga --generate-config
```

This writes `fpga_config.tcl` to the current directory. You can edit this file and use it as reference for what values the tool expects.

The template contains all configurable variables with descriptions:

```tcl
# ──── PROJECT ────
set PROJECT_XPR       ""          ;# e.g. "/path/to/project.xpr"
set FPGA_PART         ""          ;# e.g. "xczu7ev-ffvc1156-2-e"

# ──── TESTBENCH ────
set TB_TOP            ""          ;# Testbench top module name
set TB_FILES          [list]      ;# Explicit list of TB file paths
set TB_DIR            ""          ;# OR: directory for auto-discovery

# ──── SIMULATION ────
set SIM_MODE          "post-implementation"
set SIM_TYPE          "functional"

# ... (see configs/config_template.tcl for full list)
```

---

## Output & Logs

Each run creates an output directory:

```
output/
└── fpga_20260609_103500/         # Timestamped run folder
    ├── _vivado_config.tcl        # Generated Tcl config (for debugging)
    ├── logs/
    │   └── vivado_sim.log        # Full Vivado output
    ├── reports/                  # Timing/utilization reports (if available)
    └── outputs/                  # Bitstream, XSA (if generated)
```

### Vivado Output Colors

During execution, Vivado output is color-coded:

| Color | Meaning |
|-------|---------|
| 🔴 Red | `ERROR` or `CRITICAL` messages |
| 🟡 Yellow | `WARNING` messages |
| ⚪ Dim | `INFO` messages |
| ⬜ Normal | All other output |

---

## Troubleshooting

### "Vivado not found"

```
[WARN] Vivado not found in PATH or $XILINX_VIVADO.
```

**Fix**: Set the Vivado environment before running:
```bash
export XILINX_VIVADO=/tools/Xilinx/Vivado/2024.1
# OR
source /tools/Xilinx/Vivado/2024.1/settings64.sh
```

### "impl_1 run not found in project"

Your project hasn't been synthesized and implemented yet. Either:
- Use **Flow 4 (Full Flow)** which handles synth+impl automatically
- Or manually run synth+impl in Vivado GUI first, then use Flow 1

### "TB file not found"

Check the path you entered. Must be an **absolute path** to the `.sv`/`.v` file.

### "C-model runner failed to start"

Common causes:
- `make` is not installed on the system
- The Makefile directory path is wrong
- Build dependencies are missing (check the log file)

### "RESULT.txt: UNKNOWN"

Your testbench isn't writing the result file, or is writing it to a different path than what you specified. Verify:
1. The `RESULT_FILE` path matches what your TB uses in `$fopen()`
2. Your TB actually reaches the `$fwrite` / `$finish` block
3. The pass/fail patterns match exactly (default: `TEST_PASSED` / `TEST_FAILED`)

### Debugging

Use `--verbose` for detailed debug output:
```bash
python3 run_fpga --flow sim --verbose
```

Check the generated config to verify inputs were captured correctly:
```bash
cat output/fpga_<timestamp>/_vivado_config.tcl
```

### GUI fails to start with "Could not load the Qt platform plugin 'xcb'"

This is extremely common when you clone the repo and run it on a *different* Linux laptop (Ubuntu 22.04/24.04, Fedora, Pop!_OS, any Gnome/Wayland desktop).

**Error looks like:**
```
qt.qpa.plugin: Could not load the Qt platform plugin "xcb" ...
Available platform plugins are: ... xcb ...
Aborted (core dumped)
```

**Fix (on the target machine):**

```bash
sudo apt update
sudo apt install -y \
    libxcb-xinerama0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
    libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-xfixes0 \
    libxkbcommon-x11-0 libgl1-mesa-glx
```

Then try again:
```bash
./run_fpga
```

**Alternative (force Wayland):**
```bash
QT_QPA_PLATFORM=wayland ./run_fpga
```

The `setup.sh` script now prints this advice automatically on Linux.

---

## LogicLance Integration

This tool is designed for direct integration into the [LogicLance](https://github.com/hemanthkumardm/logiclance) ASIC automation framework.

### Integration Steps

1. Copy `fpga_tool/` → `logiclance/commands/frontend/fpga/`
2. Copy `run_fpga` → `logiclance/commands/frontend/run_fpga`
3. Copy `tcl/` → `logiclance/flows/xilinx/`
4. Add `"xilinx"` vendor to `logiclance/configs/tools.json`
5. Add `"fpga"` keyword to frontend role in `logiclance/configs/roles.json`

The tool already follows all LogicLance patterns:
- `SimLogger` for colored logging
- `SmartInput` for interactive prompts with rerun
- `CommandManager` for saving/loading execution context
- `ArtifactManager` for archiving outputs

After integration, users can type `run_fpga` in the LogicLance shell just like `run_sim` or `run_synth`.

---

## Support

For issues, refer to the original design-specific scripts in `original/` for working examples of each flow configuration.
