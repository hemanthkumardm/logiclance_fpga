# logiclance-fpga

FPGA Automation Tool for Xilinx/AMD Vivado.

A Python + Tcl framework that replaces ad-hoc project scripts with repeatable, intelligent flows for simulation, C-model co-simulation, regression, and full end-to-end builds (synth → impl → bitstream + XSA).

## Quick Links

- **[USER_MANUAL.md](USER_MANUAL.md)** — Primary user manual and usage reference (recommended starting point)
- **[USER_REFERENCE.md](USER_REFERENCE.md)** — Original detailed technical reference
- `python3 run_fpga` — Launches the GUI

## Highlights (Advanced Version)

- Four core flows: `sim`, `cmod`, `regression`, `full`
- Intelligent **Design Model** that understands your RTL
- **History + Recall** across runs
- **Planner** for safe incremental execution (skip synth/impl when possible)
- **Optimizer** (available in GUI) — history-guided strategy search and limited auto-retries on issues
- **Knowledge Packs** — extensible JSON rules (loaded automatically)
- **Watch / Continuous** support via GUI + intelligence layer
- Rich outputs: `intelligence_report.txt`, self-contained HTML report, `design_model.json`

## One-Time Setup (Recommended)

This project provides a single **one-stop setup script**.

Run this **once** from the project root:

```bash
cd ~/Desktop/LOG_FPGA/XSA_scripts1
./setup.sh
```

`setup.sh` will automatically:
- Install Python requirements (PyQt5, rich, ...)
- Install the package in editable mode (`pip install -e .`)
- Make the launcher scripts executable
- **Verify all external tools**: Vivado, gcc, and make (with clear pass/fail output)

After running `./setup.sh` you can start the tool with:

```bash
./run_fpga
# or simply
python3 run_fpga
```

## Getting Started

The tool is now **GUI only** and performs automatic dependency verification at startup for:
- Vivado (required)
- gcc + make (for C-model flows)

See [USER_MANUAL.md](USER_MANUAL.md) for full instructions, including the advanced intelligence features.

See [USER_MANUAL.md](USER_MANUAL.md) for full usage, examples, and explanation of the intelligence features.

## Verification

```bash
python3 test_phase3_leftovers.py
```

## Project Structure (Key Items)

- `run_fpga` — main CLI
- `fpga_tool/intelligence/` — advanced features
- `configs/packs/` — knowledge packs
- `sample_testcase/` — working example
- `tcl/` — Vivado automation scripts

---

This project is part of the LogicLance ecosystem. All intelligence features use classical methods (no LLMs).