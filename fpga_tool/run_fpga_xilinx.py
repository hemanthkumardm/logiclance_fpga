################################################################################
#                                                                              #
#                      L O G I C L A N C E   S Y S T E M                       #
#                                                                              #
#  Module: FPGA Automation Tool — Xilinx/Vivado Vendor Implementation          #
#  Author: Hemanth Kumar DM                                                    #
#  Role  : Physical Design Engineer, ASIC Automation Engineer                  #
#                                                                              #
#  Copyright (c) 2026 LogicLance. All rights reserved.                         #
#                                                                              #
################################################################################

"""
Xilinx/AMD Vivado vendor implementation.
Provides 4 flow functions:
  1. run_xilinx_sim          — Single post-impl simulation
  2. run_xilinx_cmod_sim     — C-model + simulation
  3. run_xilinx_regression   — Multi-testcase regression
  4. run_xilinx_full_flow    — Synth → Impl → Test → Bitstream → XSA
"""

import os
import sys
import subprocess
from datetime import datetime

# Resolve package root for imports
_pkg_dir = os.path.dirname(os.path.abspath(__file__))
_tool_root = os.path.dirname(_pkg_dir)

from fpga_tool.flow_utils import SimLogger, SmartInput, ArtifactManager, find_vivado
from fpga_tool.tcl_gen import generate_vivado_config_tcl
from fpga_tool.fpga_parser import parse_result_file, format_test_summary, VivadoRealtimeParser


# ──────────────────── Helpers ────────────────────

def _tcl_path(name):
    """Return absolute path to a Tcl script in tcl/ directory."""
    return os.path.join(_tool_root, "tcl", name)


def _run_vivado_batch(tcl_script, config_tcl, logger, timeout=None):
    """
    Launch Vivado in batch mode with the given Tcl script and config.

    Args:
        tcl_script: path to the flow .tcl file
        config_tcl: path to the generated _config.tcl
        logger: SimLogger instance
        timeout: max seconds (None = no limit)

    Returns:
        (exit_code, log_lines_list)
    """
    vivado_bin = find_vivado()
    if not vivado_bin:
        logger.error("Vivado not found. Set $XILINX_VIVADO or add vivado to PATH.")
        return 1, []

    logger.info(f"Vivado binary: {vivado_bin}")
    logger.info(f"Tcl script   : {tcl_script}")
    logger.info(f"Config       : {config_tcl}")

    cmd = [
        vivado_bin,
        "-mode", "batch",
        "-nojournal",
        "-nolog",
        "-source", tcl_script,
        "-tclargs", config_tcl,
    ]

    logger.info(f"Command: {' '.join(cmd)}")
    print()
    print("─" * 60)
    print("  VIVADO OUTPUT")
    print("─" * 60)

    log_lines = []
    try:
        # Sanitize environment: remove Vivado's LD_LIBRARY_PATH leaking
        env = os.environ.copy()

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            env=env,
            bufsize=1,
        )

        parser = VivadoRealtimeParser()
        for line in proc.stdout:
            log_lines.append(line)
            logger.vivado_line(line, print_to_stdout=False)
            parser.parse_line(line)

        proc.wait(timeout=timeout)
        exit_code = proc.returncode

    except subprocess.TimeoutExpired:
        proc.kill()
        logger.error(f"Vivado timed out after {timeout}s")
        exit_code = 124
    except FileNotFoundError:
        logger.error(f"Vivado binary not executable: {vivado_bin}")
        exit_code = 127
    except Exception as e:
        logger.error(f"Failed to launch Vivado: {e}")
        exit_code = 1

    print("─" * 60)
    print()

    if exit_code == 0:
        logger.success("Vivado completed successfully.")
    else:
        logger.error(f"Vivado exited with code {exit_code}")

    return exit_code, log_lines


def _collect_sim_inputs(logger, smart_in):
    """Collect inputs common to all simulation flows."""
    config = {}

    print(f"\n{'─' * 50}")
    print("  PROJECT CONFIGURATION")
    print(f"{'─' * 50}")

    config["project_xpr"] = smart_in.get(
        "Vivado project path (.xpr)", "project_xpr"
    )
    if not config["project_xpr"]:
        logger.halt("Project path is required.")

    print(f"\n{'─' * 50}")
    print("  TESTBENCH CONFIGURATION")
    print(f"{'─' * 50}")

    config["tb_top"] = smart_in.get(
        "Testbench top module name", "tb_top"
    )
    if not config["tb_top"]:
        logger.halt("Testbench top module is required.")

    # TB files or directory
    tb_mode = smart_in.get(
        "Testbench source: [1] File list  [2] Auto-discover from directory", "tb_mode", default="1"
    )

    if tb_mode == "2":
        config["tb_dir"] = smart_in.get(
            "Testbench directory path", "tb_dir"
        )
        config["tb_files"] = []
    else:
        config["tb_files"] = smart_in.get_list(
            "Testbench file(s) [space-separated paths]", "tb_files"
        )
        config["tb_dir"] = ""

    config["tb_includes"] = smart_in.get_list(
        "Include directories [space-separated, or empty]", "tb_includes", default=""
    )
    config["tb_defines"] = smart_in.get_list(
        "Verilog defines [space-separated]", "tb_defines", default="SIM=1"
    )

    print(f"\n{'─' * 50}")
    print("  SIMULATION SETTINGS")
    print(f"{'─' * 50}")

    config["sim_mode"] = smart_in.get(
        "Simulation mode (post-synthesis / post-implementation)",
        "sim_mode", default="post-implementation"
    )
    config["sim_type"] = smart_in.get(
        "Simulation type (functional / timing)",
        "sim_type", default="functional"
    )

    return config


def _collect_cmodel_inputs(logger, smart_in):
    """Collect C-model specific inputs."""
    config = {}

    print(f"\n{'─' * 50}")
    print("  C-MODEL CONFIGURATION")
    print(f"{'─' * 50}")

    config["cmodel_enable"] = True
    config["cmodel_dir"] = smart_in.get(
        "C-model directory (contains Makefile)", "cmodel_dir"
    )
    if not config["cmodel_dir"]:
        logger.halt("C-model directory is required for this flow.")

    config["cmodel_stdin"] = smart_in.get(
        "C-model stdin input file", "cmodel_stdin"
    )
    config["cmodel_stdout"] = smart_in.get(
        "C-model stdout capture file (golden output)", "cmodel_stdout", default=""
    )
    config["cmodel_clean_target"] = smart_in.get(
        "Make clean target", "cmodel_clean_target", default="clean"
    )
    config["cmodel_run_target"] = smart_in.get(
        "Make run target", "cmodel_run_target", default="manual"
    )
    config["cmodel_build_targets"] = smart_in.get_list(
        "Make build targets [space-separated, or empty for default]",
        "cmodel_build_targets", default=""
    )
    config["cmodel_timeout"] = smart_in.get_int(
        "C-model timeout (seconds)", "cmodel_timeout", default=900
    )
    config["cmodel_log"] = smart_in.get(
        "C-model log file path", "cmodel_log", default="./output/cmodel_run.log"
    )

    return config


def _collect_regression_inputs(logger, smart_in):
    """Collect multi-testcase regression inputs."""
    config = {}

    print(f"\n{'─' * 50}")
    print("  REGRESSION TEST CASES")
    print(f"{'─' * 50}")

    config["result_file"] = smart_in.get(
        "Result file path (TB writes PASS/FAIL here)", "result_file"
    )
    config["pass_pattern"] = smart_in.get(
        "Pass pattern in result file", "pass_pattern", default="TEST_PASSED"
    )
    config["fail_pattern"] = smart_in.get(
        "Fail pattern in result file", "fail_pattern", default="TEST_FAILED"
    )

    config["cmodel_out_fixed"] = smart_in.get(
        "Fixed C-model output path (TB reads this)", "cmodel_out_fixed", default=""
    )
    config["cmodel_log_dir"] = smart_in.get(
        "C-model log directory", "cmodel_log_dir", default="./output/cmodel_logs"
    )
    config["sim_log_dir"] = smart_in.get(
        "Simulation log directory", "sim_log_dir", default="./output/sim_logs"
    )

    # Collect test cases interactively
    test_cases = []
    print(f"\n  Add test cases (enter empty name to finish):")

    if smart_in.flow_type == 'rerun' and 'test_cases' in smart_in.rerun_inputs:
        # Restore from rerun
        saved = smart_in.rerun_inputs['test_cases']
        if isinstance(saved, list):
            test_cases = saved
            for tc in test_cases:
                logger.info(f"  Restored test case: {tc.get('name', '?')}")
    else:
        idx = 1
        while True:
            name = smart_in.get(f"  Test case {idx} name (empty to finish)", f"tc_{idx}_name", default="")
            if not name:
                break
            stdin_f = smart_in.get(f"  Test case {idx} stdin file", f"tc_{idx}_stdin")
            stdout_f = smart_in.get(f"  Test case {idx} stdout file", f"tc_{idx}_stdout", default="")
            test_cases.append({
                "name": name,
                "stdin": stdin_f,
                "stdout": stdout_f,
            })
            idx += 1

    if not test_cases:
        logger.halt("At least one test case is required for regression.")

    config["test_cases"] = test_cases
    smart_in.current_inputs["test_cases"] = test_cases

    return config


def _collect_full_flow_inputs(logger, smart_in):
    """Collect inputs for the full end-to-end flow."""
    config = {}

    print(f"\n{'─' * 50}")
    print("  PROJECT SOURCE")
    print(f"{'─' * 50}")

    mode = smart_in.get(
        "Project mode: [1] Open existing .xpr  [2] Create new project", "project_mode", default="1"
    )

    if mode == "2":
        config["project_xpr"] = ""
        config["fpga_part"] = smart_in.get("FPGA part (e.g. xczu7ev-ffvc1156-2-e)", "fpga_part")
        config["board_part"] = smart_in.get("Board part [optional]", "board_part", default="")
        config["project_name"] = smart_in.get("Project name", "project_name", default="fpga_project")
        config["project_dir"] = smart_in.get("Project directory", "project_dir", default=f"./{config['project_name']}")
        config["ip_repo_paths"] = smart_in.get_list("IP repository paths [space-separated]", "ip_repo_paths", default="")
        config["source_files"] = smart_in.get_list("Source HDL files/dirs [space-separated]", "source_files", default="")
        config["bd_tcl_script"] = smart_in.get("Block design Tcl script [optional]", "bd_tcl_script", default="")
    else:
        config["project_xpr"] = smart_in.get("Vivado project path (.xpr)", "project_xpr")
        if not config["project_xpr"]:
            logger.halt("Project path is required.")

    # Git (optional)
    print(f"\n{'─' * 50}")
    print("  GIT SOURCE (optional)")
    print(f"{'─' * 50}")

    use_git = smart_in.get_bool("Clone/update IP sources from Git?", "git_enable", default=False)
    config["git_enable"] = use_git
    if use_git:
        config["git_repo"] = smart_in.get("Git repository URL", "git_repo")
        config["git_commit"] = smart_in.get("Git commit/tag/branch", "git_commit")
        config["git_dest"] = smart_in.get("Destination directory for cloned sources", "git_dest")
        config["git_subdir"] = smart_in.get("Subdirectory within repo [empty for full repo]", "git_subdir", default="")
    else:
        config["git_repo"] = ""
        config["git_commit"] = ""
        config["git_dest"] = ""
        config["git_subdir"] = ""

    # Output
    print(f"\n{'─' * 50}")
    print("  BUILD OUTPUT")
    print(f"{'─' * 50}")

    config["output_bit"] = smart_in.get("Output bitstream path (.bit) [empty to skip]", "output_bit", default="")
    config["output_xsa"] = smart_in.get("Output XSA path (.xsa) [empty to skip]", "output_xsa", default="")
    config["synth_jobs"] = smart_in.get_int("Synthesis parallel jobs", "synth_jobs", default=4)
    config["impl_jobs"] = smart_in.get_int("Implementation parallel jobs", "impl_jobs", default=8)

    return config


def _print_config_summary(config, flow_name):
    """Print a summary of the configuration before proceeding."""
    print(f"\n{'═' * 50}")
    print(f"  CONFIGURATION SUMMARY — {flow_name}")
    print(f"{'═' * 50}")

    # Project
    if config.get("project_xpr"):
        print(f"  Project  : {config['project_xpr']}")
    elif config.get("fpga_part"):
        print(f"  Part     : {config['fpga_part']}")
        print(f"  Name     : {config.get('project_name', '?')}")

    # Testbench
    if config.get("tb_top"):
        print(f"  TB Top   : {config['tb_top']}")
    if config.get("tb_files"):
        print(f"  TB Files : {len(config['tb_files'])} file(s)")
    elif config.get("tb_dir"):
        print(f"  TB Dir   : {config['tb_dir']}")

    # Simulation
    if config.get("sim_mode"):
        print(f"  Sim Mode : {config['sim_mode']} {config.get('sim_type', 'functional')}")

    # C-Model
    if config.get("cmodel_enable"):
        print(f"  C-Model  : {config.get('cmodel_dir', '?')}")

    # Regression
    if config.get("test_cases"):
        print(f"  Tests    : {len(config['test_cases'])} test case(s)")
        for tc in config["test_cases"]:
            print(f"             - {tc.get('name', '?')}")

    # Output
    if config.get("output_bit"):
        print(f"  Bitstream: {config['output_bit']}")
    if config.get("output_xsa"):
        print(f"  XSA      : {config['output_xsa']}")

    print(f"{'═' * 50}")


def _build_run_config(config, run_id, logger):
    """Generate the _config.tcl and return its path."""
    output_dir = os.path.join(".", "output", run_id)
    os.makedirs(output_dir, exist_ok=True)

    config["output_log_dir"] = os.path.abspath(output_dir)
    config_tcl_path = os.path.join(output_dir, "_vivado_config.tcl")

    tcl_dir = os.path.join(_tool_root, "tcl")
    generate_vivado_config_tcl(config, config_tcl_path, tool_dir=tcl_dir)
    logger.info(f"Generated config: {config_tcl_path}")

    return config_tcl_path, output_dir


# ──────────────────── Flow 1: Single Simulation ────────────────────

def run_xilinx_sim(logger, smart_in, run_id):
    """
    Post-implementation functional simulation (single testbench).

    Returns: exit_code (int)
    """
    config = _collect_sim_inputs(logger, smart_in)

    _print_config_summary(config, "Post-Implementation Simulation")
    if not smart_in.get_bool("Proceed?", "_confirm", default=True):
        logger.info("Cancelled by user.")
        return 130

    config_tcl, output_dir = _build_run_config(config, run_id, logger)
    artifacts = ArtifactManager(output_dir, logger)
    artifacts.ensure_dirs()

    exit_code, log_lines = _run_vivado_batch(
        _tcl_path("sim_single.tcl"), config_tcl, logger
    )

    # Save log
    log_path = os.path.join(output_dir, "logs", "vivado_sim.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, 'w') as f:
        f.writelines(log_lines)

    return exit_code


# ──────────────────── Flow 2: C-Model + Simulation ────────────────────

def run_xilinx_cmod_sim(logger, smart_in, run_id):
    """
    C-model build & run, then post-impl simulation.

    Returns: exit_code (int)
    """
    config = _collect_sim_inputs(logger, smart_in)
    config.update(_collect_cmodel_inputs(logger, smart_in))

    _print_config_summary(config, "C-Model + Simulation")
    if not smart_in.get_bool("Proceed?", "_confirm", default=True):
        logger.info("Cancelled by user.")
        return 130

    config_tcl, output_dir = _build_run_config(config, run_id, logger)
    artifacts = ArtifactManager(output_dir, logger)
    artifacts.ensure_dirs()

    exit_code, log_lines = _run_vivado_batch(
        _tcl_path("cmod_sim.tcl"), config_tcl, logger
    )

    log_path = os.path.join(output_dir, "logs", "vivado_cmod_sim.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, 'w') as f:
        f.writelines(log_lines)

    return exit_code


# ──────────────────── Flow 3: Multi-Test Regression ────────────────────

def run_xilinx_regression(logger, smart_in, run_id):
    """
    Multi-testcase regression: for each test → C-model (async) → sim → PASS/FAIL.

    Returns: exit_code (int)
    """
    config = _collect_sim_inputs(logger, smart_in)
    config.update(_collect_cmodel_inputs(logger, smart_in))
    config.update(_collect_regression_inputs(logger, smart_in))

    _print_config_summary(config, "Multi-Test Regression")
    if not smart_in.get_bool("Proceed?", "_confirm", default=True):
        logger.info("Cancelled by user.")
        return 130

    config_tcl, output_dir = _build_run_config(config, run_id, logger)
    artifacts = ArtifactManager(output_dir, logger)
    artifacts.ensure_dirs()

    exit_code, log_lines = _run_vivado_batch(
        _tcl_path("regression.tcl"), config_tcl, logger
    )

    log_path = os.path.join(output_dir, "logs", "vivado_regression.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, 'w') as f:
        f.writelines(log_lines)

    # Parse results from Vivado output
    results = []
    for tc in config.get("test_cases", []):
        name = tc.get("name", "?")
        # Check if Vivado printed the result
        verdict = "UNKNOWN"
        for line in log_lines:
            if f"RESULT: {name} =>" in line:
                if "PASS" in line:
                    verdict = "PASS"
                elif "FAIL" in line:
                    verdict = "FAIL"
                break
        results.append({"name": name, "result": verdict})

    print(format_test_summary(results))

    # Return 1 if any test failed
    if any(r["result"] == "FAIL" for r in results):
        return 1
    if any(r["result"] == "UNKNOWN" for r in results):
        return 2
    return exit_code


# ──────────────────── Flow 4: Full Flow ────────────────────

def run_xilinx_full_flow(logger, smart_in, run_id):
    """
    End-to-end: create/open project → synth → impl → test → bitstream → XSA.

    Returns: exit_code (int)
    """
    config = _collect_full_flow_inputs(logger, smart_in)

    # Testbench (needed if running regression)
    run_tests = smart_in.get_bool("Run post-implementation regression tests?", "run_tests", default=True)

    if run_tests:
        # Collect TB info
        print(f"\n{'─' * 50}")
        print("  TESTBENCH CONFIGURATION")
        print(f"{'─' * 50}")

        config["tb_top"] = smart_in.get("Testbench top module name", "tb_top")
        tb_mode = smart_in.get(
            "Testbench source: [1] File list  [2] Auto-discover from directory", "tb_mode", default="1"
        )
        if tb_mode == "2":
            config["tb_dir"] = smart_in.get("Testbench directory path", "tb_dir")
            config["tb_files"] = []
        else:
            config["tb_files"] = smart_in.get_list("Testbench file(s) [space-separated]", "tb_files")
            config["tb_dir"] = ""

        config["tb_includes"] = smart_in.get_list("Include directories [optional]", "tb_includes", default="")
        config["tb_defines"] = smart_in.get_list("Verilog defines", "tb_defines", default="SIM=1")
        config["sim_mode"] = "post-implementation"
        config["sim_type"] = "functional"

        # C-Model & regression inputs
        config.update(_collect_cmodel_inputs(logger, smart_in))
        config.update(_collect_regression_inputs(logger, smart_in))
    else:
        config["tb_top"] = ""
        config["tb_files"] = []
        config["tb_dir"] = ""
        config["tb_includes"] = []
        config["tb_defines"] = []
        config["cmodel_enable"] = False
        config["test_cases"] = []

    _print_config_summary(config, "Full Flow (Synth → Impl → Test → XSA)")
    if not smart_in.get_bool("Proceed?", "_confirm", default=True):
        logger.info("Cancelled by user.")
        return 130

    config_tcl, output_dir = _build_run_config(config, run_id, logger)
    artifacts = ArtifactManager(output_dir, logger)
    artifacts.ensure_dirs()

    exit_code, log_lines = _run_vivado_batch(
        _tcl_path("full_flow.tcl"), config_tcl, logger,
        timeout=None  # Full flow can take hours
    )

    log_path = os.path.join(output_dir, "logs", "vivado_full_flow.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, 'w') as f:
        f.writelines(log_lines)

    # Archive outputs
    if config.get("output_bit") and os.path.exists(config["output_bit"]):
        artifacts.archive_file(config["output_bit"], "outputs")
    if config.get("output_xsa") and os.path.exists(config["output_xsa"]):
        artifacts.archive_file(config["output_xsa"], "outputs")
        
    # Archive reports
    project_name = config.get("project_name", "fpga_project")
    project_dir = config.get("project_dir", f"./{project_name}")
    runs_dir = os.path.join(project_dir, f"{project_name}.runs")
    artifacts.archive_glob(os.path.join(runs_dir, "synth_1", "*.rpt"), "reports")
    artifacts.archive_glob(os.path.join(runs_dir, "impl_1", "*.rpt"), "reports")

    return exit_code
