################################################################################
#                                                                              #
#                      L O G I C L A N C E   S Y S T E M                       #
#                                                                              #
#  Module: FPGA Automation Tool — Result & Report Parser                       #
#  Author: Hemanth Kumar DM                                                    #
#  Role  : Physical Design Engineer, ASIC Automation Engineer                  #
#                                                                              #
#  Copyright (c) 2026 LogicLance. All rights reserved.                         #
#                                                                              #
################################################################################

"""
Parses Vivado simulation results, timing reports, and utilization reports.
"""

import os
import re


def parse_result_file(result_path, pass_pattern="TEST_PASSED", fail_pattern="TEST_FAILED"):
    """
    Read a RESULT.txt file and check for PASS/FAIL markers.

    Returns:
        "PASS", "FAIL", or "UNKNOWN"
    """
    if not result_path or not os.path.exists(result_path):
        return "UNKNOWN"

    try:
        with open(result_path, 'r') as f:
            content = f.read().strip()

        if re.search(fail_pattern, content, re.IGNORECASE):
            return "FAIL"
        if re.search(pass_pattern, content, re.IGNORECASE):
            return "PASS"
    except Exception:
        pass

    return "UNKNOWN"


def parse_vivado_log_status(log_lines):
    """
    Parse Vivado stdout/log lines for overall status.

    Returns:
        dict with keys: errors, warnings, critical_warnings, info_count
    """
    stats = {
        "errors": 0,
        "warnings": 0,
        "critical_warnings": 0,
        "info_count": 0,
    }

    for line in log_lines:
        if "ERROR:" in line:
            stats["errors"] += 1
        elif "CRITICAL WARNING:" in line:
            stats["critical_warnings"] += 1
        elif "WARNING:" in line:
            stats["warnings"] += 1
        elif "INFO:" in line:
            stats["info_count"] += 1

    return stats


def parse_timing_summary(report_path):
    """
    Parse a Vivado timing summary report for key metrics.

    Returns:
        dict with keys: wns, tns, whs, ths, failing_endpoints
        or None if file doesn't exist / can't be parsed
    """
    if not report_path or not os.path.exists(report_path):
        return None

    result = {
        "wns": None,
        "tns": None,
        "whs": None,
        "ths": None,
        "failing_endpoints": None,
    }

    try:
        with open(report_path, 'r') as f:
            content = f.read()

        # WNS (Worst Negative Slack) — multiple possible formats in Vivado reports
        m = re.search(r'WNS\(ns\)\s*:\s*([-\d.]+)', content)
        if not m:
            m = re.search(r'WNS\s*[:=]\s*([-\d.]+)\s*ns', content, re.IGNORECASE)
        if m:
            result["wns"] = float(m.group(1))

        # TNS (Total Negative Slack)
        m = re.search(r'TNS\(ns\)\s*:\s*([-\d.]+)', content)
        if not m:
            m = re.search(r'TNS\s*[:=]\s*([-\d.]+)\s*ns', content, re.IGNORECASE)
        if m:
            result["tns"] = float(m.group(1))

        # WHS (Worst Hold Slack)
        m = re.search(r'WHS\(ns\)\s*:\s*([-\d.]+)', content)
        if m:
            result["whs"] = float(m.group(1))

        # THS (Total Hold Slack)
        m = re.search(r'THS\(ns\)\s*:\s*([-\d.]+)', content)
        if m:
            result["ths"] = float(m.group(1))

        # Failing endpoints
        m = re.search(r'Failing Endpoints\s*:\s*(\d+)', content)
        if m:
            result["failing_endpoints"] = int(m.group(1))

    except Exception:
        return None

    return result


def parse_utilization_summary(report_path):
    """
    Parse a Vivado utilization report for key resource usage.

    Returns:
        dict with resource types as keys, each having 'used', 'available', 'percent'
        or None if file doesn't exist
    """
    if not report_path or not os.path.exists(report_path):
        return None

    resources = {}

    try:
        with open(report_path, 'r') as f:
            content = f.read()

        # Match table rows like: | CLB LUTs | 12345 | 0 | 230400 | 5.36 |
        pattern = r'\|\s*([\w\s/]+?)\s*\|\s*(\d+)\s*\|\s*\d+\s*\|\s*(\d+)\s*\|\s*([\d.]+)\s*\|'
        for m in re.finditer(pattern, content):
            name = m.group(1).strip()
            used = int(m.group(2))
            available = int(m.group(3))
            percent = float(m.group(4))
            resources[name] = {
                "used": used,
                "available": available,
                "percent": percent,
            }

    except Exception:
        return None

    return resources if resources else None


def format_test_summary(results):
    """
    Format a list of test results into a printable summary table.

    Args:
        results: list of dicts with keys 'name' and 'result' (PASS/FAIL/UNKNOWN)

    Returns:
        Formatted string
    """
    if not results:
        return "No test results."

    lines = []
    lines.append("")
    lines.append("=" * 50)
    lines.append("  TEST RESULTS SUMMARY")
    lines.append("=" * 50)

    pass_count = 0
    fail_count = 0
    unknown_count = 0

    for r in results:
        name = r.get("name", "?")
        verdict = r.get("result", "UNKNOWN")

        if verdict == "PASS":
            marker = "\033[92m✔ PASS\033[0m"
            pass_count += 1
        elif verdict == "FAIL":
            marker = "\033[91m✘ FAIL\033[0m"
            fail_count += 1
        else:
            marker = "\033[93m? UNKNOWN\033[0m"
            unknown_count += 1

        lines.append(f"  {name:20s} : {marker}")

    lines.append("-" * 50)
    lines.append(f"  PASSED : {pass_count}")
    lines.append(f"  FAILED : {fail_count}")
    lines.append(f"  UNKNOWN: {unknown_count}")
    lines.append("=" * 50)

    return "\n".join(lines)


class VivadoRealtimeParser:
    """
    Parses raw Vivado log lines in real-time, filtering out noise and printing
    beautifully formatted output using the rich library.
    """
    def __init__(self):
        try:
            from rich.console import Console
            from rich.markup import escape
            self.console = Console(force_terminal=True, color_system="standard")
            self.escape = escape
        except ImportError:
            self.console = None
            self.escape = lambda x: x
            
        self.phase_re = re.compile(r'^(Phase \d+|Starting \w+|Finished \w+|Netlist sorting)(.*)')
        
    def parse_line(self, line):
        clean = line.strip()
        if not clean:
            return
            
        # Fallback if rich is not installed
        if not self.console:
            print(clean)
            return
            
        # Ignore raw Tcl commands unless they are our custom fpga_log_info
        if clean.startswith('#') and 'INFO:' not in clean and 'WARNING:' not in clean and 'ERROR:' not in clean:
            return
            
        # Suppress useless Vivado noise
        if "Time (s): cpu =" in clean or "Memory (MB): peak =" in clean:
            return
        if clean.startswith("****** Vivado") or clean.startswith("**** SW Build") or clean.startswith("**** IP Build"):
            return
        if clean.startswith("**** SharedData Build") or clean.startswith("**** Start of session"):
            return
        if clean.startswith("** Copyright"):
            return
            
        # Formatting rules
        e_clean = self.escape(clean)
        if clean.startswith('ERROR:'):
            self.console.print(f"[bold red]❌ {e_clean}[/bold red]")
        elif clean.startswith('CRITICAL WARNING:'):
            self.console.print(f"[bold red]💥 {e_clean}[/bold red]")
        elif clean.startswith('WARNING:'):
            self.console.print(f"[bold yellow]⚠️ {e_clean}[/bold yellow]")
        elif clean.startswith('INFO:'):
            # Check for milestones vs generic info
            if "completed successfully" in clean:
                self.console.print(f"[bold green]✅ {e_clean}[/bold green]")
            elif "Creating project" in clean or "Launching" in clean or "Running" in clean or "Generating" in clean:
                self.console.print(f"[bold blue]🚀 {e_clean}[/bold blue]")
            elif "Bitstream written" in clean or "XSA exported" in clean:
                self.console.print(f"[bold cyan]📦 {e_clean}[/bold cyan]")
            else:
                self.console.print(f"[dim]{e_clean}[/dim]")
        elif clean.startswith('RESULT:'):
            if 'PASS' in clean:
                self.console.print(f"[bold green]✅ {e_clean}[/bold green]")
            elif 'FAIL' in clean:
                self.console.print(f"[bold red]❌ {e_clean}[/bold red]")
            else:
                self.console.print(f"[bold yellow]❓ {e_clean}[/bold yellow]")
        elif self.phase_re.match(clean):
            self.console.print(f"[bold magenta]⚙️ {e_clean}[/bold magenta]")
        elif clean.startswith('PASSED:') or clean.startswith('FAILED:'):
            self.console.print(f"[bold cyan]{e_clean}[/bold cyan]")
        elif clean.startswith('===================='):
            self.console.print(f"[bold cyan]{e_clean}[/bold cyan]")
        else:
            self.console.print(f"[dim white]{e_clean}[/dim white]")


# =============================================================================
# Phase 1 Enhanced Report Parsers (additive — all existing APIs unchanged)
# =============================================================================

def parse_clock_utilization_report(report_path):
    """
    Parse clock utilization report.
    Returns dict with clock count, BUFG usage, global clocks, etc. or None.
    """
    if not report_path or not os.path.exists(report_path):
        return None
    result = {"global_clocks": [], "bufg_used": 0, "bufg_available": 0, "clock_loads": 0}
    try:
        with open(report_path, 'r') as f:
            content = f.read()
        # BUFGCTRL line
        m = re.search(r'BUFGCTRL\s*\|\s*(\d+)\s*\|\s*(\d+)', content)
        if m:
            result["bufg_used"] = int(m.group(1))
            result["bufg_available"] = int(m.group(2))
        # Global clock details (rough)
        for line in content.splitlines():
            if "BUFG" in line and "O " in line and "|" in line:
                # crude extraction of net / period if present
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) > 5:
                    result["global_clocks"].append({"net": parts[-1][:40]})
        # Loads
        m = re.search(r'Clock Loads.*?(\d+)', content, re.DOTALL)
        if m:
            result["clock_loads"] = int(m.group(1))
    except Exception:
        return None
    return result


def parse_power_report(report_path):
    """
    Parse power report for total/dynamic/static + junction warnings.
    """
    if not report_path or not os.path.exists(report_path):
        return None
    result = {"total_w": None, "dynamic_w": None, "static_w": None, "junction_c": None, "warnings": []}
    try:
        with open(report_path, 'r') as f:
            content = f.read()
        m = re.search(r'Total On-Chip Power \(W\)\s*\|\s*([\d.]+)', content)
        if m:
            result["total_w"] = float(m.group(1))
        m = re.search(r'Dynamic \(W\)\s*\|\s*([\d.]+)', content)
        if m:
            result["dynamic_w"] = float(m.group(1))
        m = re.search(r'Device Static \(W\)\s*\|\s*([\d.]+)', content)
        if m:
            result["static_w"] = float(m.group(1))
        m = re.search(r'Junction Temperature \(C\)\s*\|\s*([\d.]+)', content)
        if m:
            result["junction_c"] = float(m.group(1))
        if "Junction temp exceeded" in content or "exceeded" in content.lower():
            result["warnings"].append("Junction temperature exceeded or marginal")
    except Exception:
        return None
    return result


def parse_methodology_and_check_timing(report_path):
    """
    Parse common issues from timing summary / methodology / check_timing sections
    (no_clock, unconstrained endpoints, etc.).
    Works on the main timing_summary_routed.rpt which contains these tables.
    """
    if not report_path or not os.path.exists(report_path):
        return None
    result = {"methodology_violations": 0, "no_clock": 0, "unconstrained_endpoints": 0, "other_issues": []}
    try:
        with open(report_path, 'r') as f:
            content = f.read()
        # Methodology table
        m = re.search(r'Rule\s+Severity.*?Violations\s*\n(.*?)(?:\n\n|\Z)', content, re.DOTALL)
        if m:
            # Count numeric violations
            nums = re.findall(r'\|\s*(\d+)\s*$', m.group(1), re.MULTILINE)
            result["methodology_violations"] = sum(int(x) for x in nums) if nums else 0
        # check_timing no_clock etc.
        m = re.search(r'checking no_clock \((\d+)\)', content)
        if m:
            result["no_clock"] = int(m.group(1))
        m = re.search(r'unconstrained_internal_endpoints \((\d+)\)', content)
        if m:
            result["unconstrained_endpoints"] = int(m.group(1))
        if result["no_clock"] > 0:
            result["other_issues"].append(f"{result['no_clock']} registers with no clock (no_clock check)")
    except Exception:
        return None
    return result


def parse_detailed_timing_paths(report_path, max_paths=3):
    """
    Light extraction of top violating path endpoints when the report contains them.
    """
    if not report_path or not os.path.exists(report_path):
        return []
    paths = []
    try:
        with open(report_path, 'r') as f:
            content = f.read()
        # Look for simple "Path 1" or endpoint lines in detailed reports
        for m in re.finditer(r'(?:Path\s+\d+|From:\s*|To:\s*)([^\n]{10,80})', content):
            p = m.group(1).strip()
            if p and len(paths) < max_paths:
                paths.append(p[:70])
    except Exception:
        return []
    return paths


def collect_run_metrics(output_dir):
    """
    High-level collector used by the intelligence layer.

    Looks for the reports/ subdirectory created by ArtifactManager (or the Vivado
    project runs dir as fallback). Returns a flat dict of useful metrics.
    Safe to call on any output dir; returns {} on problems.
    """
    if not output_dir:
        return {}
    reports_dir = os.path.join(output_dir, "reports")
    if not os.path.isdir(reports_dir):
        # try common Vivado location relative to a project dir guess
        reports_dir = output_dir

    metrics = {
        "timing": None,
        "utilization": None,
        "clock": None,
        "power": None,
        "methodology": None,
        "top_violating_paths": [],
    }

    # Find likely report files (the tool already archives many)
    candidates = {}
    for fn in os.listdir(reports_dir) if os.path.isdir(reports_dir) else []:
        low = fn.lower()
        if "timing" in low and "summary" in low:
            candidates["timing"] = os.path.join(reports_dir, fn)
        elif "utilization" in low:
            candidates["util"] = os.path.join(reports_dir, fn)
        elif "clock" in low:
            candidates["clock"] = os.path.join(reports_dir, fn)
        elif "power" in low:
            candidates["power"] = os.path.join(reports_dir, fn)

    # Parse what we can
    if "timing" in candidates:
        metrics["timing"] = parse_timing_summary(candidates["timing"])
        metrics["top_violating_paths"] = parse_detailed_timing_paths(candidates["timing"])
        mt = parse_methodology_and_check_timing(candidates["timing"])
        if mt:
            metrics["methodology"] = mt

    if "util" in candidates:
        metrics["utilization"] = parse_utilization_summary(candidates["util"])

    if "clock" in candidates:
        metrics["clock"] = parse_clock_utilization_report(candidates["clock"])

    if "power" in candidates:
        metrics["power"] = parse_power_report(candidates["power"])

    # Also attach a count of available reports
    try:
        metrics["reports_found"] = len([f for f in os.listdir(reports_dir) if f.endswith(".rpt")]) if os.path.isdir(reports_dir) else 0
    except Exception:
        pass

    return metrics
