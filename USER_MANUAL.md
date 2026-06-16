# FPGA Automation Tool — User Manual

**Version**: Advanced (Phases 1–3) — GUI Only  
**Project**: logiclance-fpga (XSA Scripts)  
**Compatibility**: Xilinx Vivado 2024.1+ | Python 3.8+  

**Note**: The command-line interface has been removed. All interaction is now through the graphical user interface for better usability and to support the rich configuration needed by the advanced intelligence features.

This is the **official user manual** and usage reference for the FPGA Automation Tool. It explains the core flows and the advanced intelligence features (design model, history recall, planner, optimizer, knowledge packs, watch mode, rich reporting, etc.) which are all accessible via the GUI.

All "smart" behavior uses classical techniques only — rules, heuristics, history search, and static analysis. No AI or LLMs.

---

## Quick Reference

| Task                              | How to do it in GUI                              |
|-----------------------------------|--------------------------------------------------|
| Launch the tool                   | `python3 run_fpga` or `python3 run_fpga_gui.py` |
| Select flow & configure           | Use the top dropdown + form fields               |
| Enable optimizer (auto strategy retries) | Check "Enable Optimizer" or equivalent option (see advanced options) |
| Enable continuous watch mode      | Check the Watch Mode checkbox (if available) or use external file watcher with GUI |
| Load previous configuration       | Click "Load Last Run Config"                     |
| Run the flow                      | Click "▶ Run Selected Flow"                      |
| View live output & intelligence reports | Use the Live Console + open generated .html reports |
| Verify all features               | `python3 test_phase3_leftovers.py`               |
| View this manual                  | `less USER_MANUAL.md`                            |

---

## 1. Overview

The tool replaces manual, project-specific Vivado Tcl scripts with a repeatable Python + Tcl framework.

### Core Flows

| Flow                    | Shortcut    | What it does                                      |
|-------------------------|-------------|---------------------------------------------------|
| Post-Impl Simulation    | `sim`       | Run testbench on placed & routed netlist          |
| C-Model + Simulation    | `cmod`      | Build C golden model → run → compare in simulation |
| Multi-Test Regression   | `regression`| Execute many vectors with automatic PASS/FAIL     |
| Full Flow               | `full`      | Create/Open → Synth → Impl → (regression) → Bit + XSA |

### What the Advanced Version Adds

- **Design Model**: Automatically parses your RTL and project to understand clocks, resets, modules, and ports.
- **History & Recall**: Remembers every run and gives context-aware advice.
- **Planner**: Detects when you can safely skip synthesis/implementation.
- **Optimizer**: On failure with `--optimize`, it tries better strategies based on what worked for this exact design before.
- **Knowledge Packs**: Drop JSON files to extend recommendations and preferred strategies.
- **Watch / Continuous Mode**: The GUI supports monitoring workflows (intelligence layer provides change-aware advice in reports and console).
- **Rich Artifacts**: `intelligence_report.txt`, self-contained `.html`, and `design_model.json` for every run.

---

## 2. Prerequisites & Setup

### Required
- Python 3.8+
- Xilinx/AMD Vivado 2024.1 or newer

### One-Time Setup (Recommended)

From the project root, simply run:

```bash
./setup.sh
```

This single script handles:
- Installing Python dependencies (`PyQt5`, `rich`, etc.)
- Installing the package in editable mode
- Making `run_fpga` and `run_fpga_gui.py` executable
- Verifying external tools: **Vivado**, **gcc**, and **make**

After running `./setup.sh` you can start the tool with:

```bash
./run_fpga
# or
python3 run_fpga
# or (after PATH is updated by pip)
run-fpga-gui
```

### Recommended One-Time Setup (Vivado)

```bash
# Add to your shell profile or run per session
export XILINX_VIVADO=/tools/Xilinx/Vivado/2024.1
# or source the settings script:
# source /tools/Xilinx/Vivado/2024.1/settings64.sh
```

The tool searches for Vivado automatically in this order:
1. `$XILINX_VIVADO/bin/vivado`
2. `vivado` on your PATH
3. Common install locations

### Dependency Verification
On every GUI startup, the tool automatically runs a dependency check for:
- **Vivado** (required)
- **gcc** and **make** (required for any C-model flows)

You will see output like:
```
[Startup] Verifying external dependencies...
=== Dependency Verification ===
✅ Vivado found: /opt/VIVADO/2025.2/Vivado/bin/vivado
✅ gcc found: /usr/bin/gcc
✅ make found: /usr/bin/make
✅ All required external dependencies appear available.
```

If something is missing, clear warnings are shown before you waste time starting a flow.

### C-Model Flows
You need a working C compiler (usually `gcc`) + `make` if you use flows with a golden C model.

---

## 3. Directory Layout (Key Files)

```
XSA_scripts1/
├── run_fpga                    # Launcher for the GUI (CLI removed)
├── run_fpga_gui.py             # Graphical interface
├── fpga_tool/
│   └── intelligence/           # The "brain" (new in advanced version)
│       ├── design_model.py
│       ├── history.py
│       ├── planner.py
│       ├── optimizer.py
│       ├── knowledge.py
│       ├── watcher.py
│       └── ...
├── tcl/                        # Vivado Tcl scripts (called by Python)
├── configs/
│   ├── config_template.tcl
│   └── packs/                  # Extensible Knowledge Packs (JSON)
│       └── example_pack.json
├── sample_testcase/            # Ready-to-run example project
├── USER_MANUAL.md              # This file
├── USER_REFERENCE.md           # Original detailed reference
└── test_phase3_leftovers.py    # Self-test for all advanced features
```

---

## 4. Getting Started (GUI Only)

Launch the tool:

```bash
cd ~/Desktop/LOG_FPGA/XSA_scripts1
python3 run_fpga
```

(or `python3 run_fpga_gui.py`)

This starts the graphical interface.

**Recommended first run** (using the included sample):
- Select "Full Flow (Synth → Impl → Test → XSA)" from the dropdown
- In the Project section, choose create-new or point to an existing project
- Use the `sample_testcase/` directories for RTL, sim, and c_model (see `sample_testcase/README.md` for the exact recommended paths)
- Enable Optimizer or other advanced options in the form if desired
- Fill the Testbench and (if using regression) C-Model / Regression sections
- Click "▶ Run Selected Flow"

After any run you will find:
- A new `fpga_project/` directory (if creating)
- An `output/fpga_YYYYMMDD_HHMMSS/` folder with reports + intelligence artifacts:
  - `intelligence_report.txt`
  - `intelligence_report.html` (open in any browser)
  - `design_model.json`

Use the "Load Last Run Config" button to quickly restore previous form state (including the test case table).

---

## 5. GUI Controls Reference

The interface is form-driven:

- Top **Flow dropdown** selects between Simulation, C-Model + Sim, Regression, or Full Flow.
- Forms dynamically show/hide fields based on the flow.
- **Project section**: Open existing `.xpr` or create new (with part, sources, etc.).
- **Testbench section**: Top module name + file list or directory auto-discovery.
- **C-Model section**: Makefile dir, targets, input/output files.
- **Regression section**: Result patterns + editable table of test cases.
- **Advanced / Output**: Bitstream/XSA paths, job counts, optimizer/watch options (where applicable).

**Load Last Run Config** button restores previous form state (including test case table).

All intelligence features (planner advice, optimizer recommendations, knowledge pack rules) are active and appear in the **Live Console Output** pane during and after the run.

**New: Reports & Outputs panel**
At the bottom of the GUI there is now a "Reports & Outputs" section. It lets you:
- Browse recent runs from the `./output/` folder
- Preview intelligence reports, design model (JSON), and run logs directly in the GUI
- Open the full HTML intelligence report in your browser with one click
- Quickly open the entire output folder for a run

This means you no longer need to leave the GUI to inspect reports.

---

## 6. The Intelligence Features Explained

### Design Model
The tool scans your Verilog/SystemVerilog/VHDL and (optionally) the `.xpr` file. It extracts:
- Module names and ports
- Clocks (detected from sensitivity lists)
- Resets
- Rough size estimates

This model is used for history matching, constraint suggestions, and stimulus generation.

### History Database
Every completed run is stored locally in `.fpga_intel_history.db` (project-local by default). The tool uses the design signature to find previous similar runs and surface relevant advice.

### Planner
Before starting expensive work, the planner answers:
- "Has the RTL changed since the last successful implementation?"
- "Can I safely skip synthesis and implementation?"

You will see messages like:
> [SMART] RTL content identical to successful run ... Only testbench changed.

**Special case**: If the tool just auto-created a missing XDC, it will print a forcing message and override the skip suggestion to ensure a full constrained implementation run happens (producing fresh reports with the new XDC applied).

### Optimizer
When enabled in the GUI (Full Flow or Regression forms), the optimizer looks up historically successful strategies for the exact same design signature and can automatically suggest or (in supported flows) trigger limited retries with better synthesis/implementation settings. Retries are bounded for safety.

### Knowledge Packs
JSON files in `configs/packs/` let you extend the tool without modifying code.

Example of adding a rule:
```json
{
  "recommendations": [
    {
      "condition": {"wns": {"lt": -1.0}},
      "message": "For large negative slack, try retiming before increasing effort."
    }
  ]
}
```

Place your own `.json` files in `configs/packs/` — they are loaded automatically.

### ASIC / SoC Feasibility Prediction
After every Full Flow the intelligence report now contains a new section:

```
── ASIC / SoC Feasibility Prediction (Heuristic) ─────────────
  Readiness : Medium (62/100)
    • Unconstrained clocks detected...
    • Multiple clock domains (CDC hardening required...)
  Important Caveats:
    • Classical heuristic only...
```

It is a fast, rule-based prediction using:
- Number of clock domains + unconstrained clocks (from the Design Model)
- Power/thermal numbers observed during the FPGA run
- Overall design size proxy

**Purpose**: Give you an early, no-cost signal of whether the current RTL is likely "portable to ASIC/SoC with reasonable effort" before you commit to a full ASIC flow (synthesis, STA, power analysis, DFT, etc.).

**Important**: This is **not** real ASIC sign-off. It will never replace Design Compiler, PrimeTime, Joules, or formal tools. Treat it as a helpful red/yellow/green flag + list of porting risks.

The assessment also influences the Recommendations list.

### Watch Mode
The GUI + intelligence layer provide change-aware advice (planner deltas, incremental recommendations). True continuous monitoring can be achieved by keeping the GUI open or combining with simple file watchers.

### Generated Reports
Every run produces:
- `intelligence_report.txt` — terminal-style summary with recommendations
- `intelligence_report.html` — nicely formatted, self-contained HTML (Tailwind) with planner decision and metrics
- `design_model.json` — structured data for downstream tools or CI

---

## 7. GUI Usage

Launch with:
```bash
python3 run_fpga
# or
python3 run_fpga_gui.py
```

The GUI supports the same four flows. Key features:
- Flow selector at the top
- Dynamic forms that only show fields relevant to the chosen flow
- "Load Last Run Config" button
- Live color-coded log output
- Table for adding multiple regression test cases

The GUI also respects the intelligence layer (planner advice appears in the log pane).

---

## 8. Practical Examples (GUI)

### Development Loop (Recommended)
Launch the GUI (`python3 run_fpga`), select the Regression flow, configure your sources/testbench/C-model once, then re-run as you edit files. The Live Console will show planner advice on what changed and any new recommendations.

### One-Shot Production Build
Select Full Flow in the GUI, enable the Optimizer option in the form if desired, fill in project details (or load previous config), and click Run. The intelligence layer will provide advice; the optimizer can help on retries if issues occur.

### Using Your Own Project
1. Launch the GUI (`python3 run_fpga`)
2. Select Full Flow
3. Choose "Open existing .xpr" or create new in the Project section
4. Fill in the required fields (testbench, C-model if regression, etc.)
5. **Smart auto XDC + force full impl**: If no .xdc file is detected, the tool automatically generates `auto_generated.xdc`, adds it to the project, **forces a full synthesis + implementation** (even if the planner would suggest skipping due to identical RTL), and logs the forcing. This guarantees fresh reports with the new constraints applied. 

On subsequent *incremental* runs (only TB/C-model changed), the report will note that it is reusing previous implementation reports and that the XDC is now in place for the next full run. The "missing XDC" warnings will be qualified with "(from previous implementation run)" so they don't keep nagging after the XDC has been auto-added.

---

## 9. Extending the Tool

- **Knowledge Packs** — easiest way (see section 6).
- **Plugins** — advanced users can register custom advisors via the plugin API in `fpga_tool/intelligence/plugins.py`.
- **Custom Tcl** — edit files under `tcl/` (the Python layer will still call them).

---

## 10. Troubleshooting

- **Vivado not found**: Set `XILINX_VIVADO` or add `vivado` to PATH.
- **Intelligence not working**: Make sure you are not using `--no-intel`. Check that `fpga_tool/intelligence/` exists.
- **Watch mode ignores changes**: It watches the directories you provided during the prompts (RTL, TB, C-model). Re-run to update the watched roots.
- **Optimizer never retries**: It only activates on failure **and** when `--optimize` is passed.
- **History is empty**: First run for this design signature. Run again after making a change.

Use `--verbose` for maximum visibility into decisions.

---

## 11. Verification

Run the self-test (works without Vivado):

```bash
python3 test_phase3_leftovers.py
```

It exercises the design model, optimizer, knowledge base, watcher, plugins, and causal analysis.

---

## 12. Related Documentation

- `USER_REFERENCE.md` — original deep reference for the base tool
- `sample_testcase/README.md` — how to use the included example
- `configs/config_template.tcl` — annotated template you can copy

---

**Tip**: Start with the sample using the Full Flow in the GUI (with Optimizer enabled if desired). Use "Load Last Run Config" for fast iteration while developing. The intelligence layer will provide advice and reports automatically.

If you create useful knowledge packs for your designs, consider sharing them with your team by committing them under `configs/packs/`.