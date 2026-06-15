# Sample Testcase: C-Model + RTL Regression

This is a complete, minimal example project you can use to test the **FPGA Automation Tool GUI**.

## What's included:
- **`rtl/adder.v`**: A simple 32-bit clocked adder.
- **`c_model/`**: A C program (`main.c`) and a `Makefile` that reads two integers and prints them along with their expected sum.
- **`sim/tb_adder.v`**: A testbench that reads the output of the C-model, drives `adder.v`, checks the result, and writes `TEST_PASSED` or `TEST_FAILED` to `RESULT.txt`.
- **`test_cases/`**: Two sample input files with random numbers.

---

## How to test this using the GUI:

1. Launch the GUI: `python3 run_fpga_gui.py`
2. Select **"Full Flow (Synth → Impl → Test → XSA)"** from the top dropdown.
3. Check the **"Run post-implementation regression tests?"** box at the bottom.

### Project Configuration:
- **Project Mode**: Create new project
- **FPGA part**: `xc7z020clg400-1` (or any available part)
- **Source HDL files/dirs**: Select **ONLY** the `sample_testcase/rtl` directory.

### Testbench Configuration:
- **Testbench top module name**: `tb_adder`
- **Testbench source**: Auto-discover from directory
- **Testbench directory**: Select the `sample_testcase/sim` directory.

### C-Model Configuration:
- **C-model directory**: Select `sample_testcase/c_model`
- **Make clean target**: `clean`
- **Make run target**: `manual`

### Regression Configuration:
- **Result file path**: `/path/to/XSA_scripts/fpga_project/fpga_project.sim/sim_1/impl/func/xsim/RESULT.txt` (or just `RESULT.txt` if you want it to land in the active execution dir).
- **Pass pattern**: `TEST_PASSED`
- **Fail pattern**: `TEST_FAILED`
- **Fixed C-model output path**: `/tmp/fpga_cmodel_golden.txt`

### Add Test Cases (in the table):
Click "+ Add Test Case" twice and fill the rows:
1. **Name**: `TC1`, **Stdin File**: `sample_testcase/test_cases/tc1_input.txt`, **Stdout**: `/tmp/tc1_out.txt`
2. **Name**: `TC2`, **Stdin File**: `sample_testcase/test_cases/tc2_input.txt`, **Stdout**: `/tmp/tc2_out.txt`

Finally, click **"▶ Run Selected Flow"** and watch it run!
