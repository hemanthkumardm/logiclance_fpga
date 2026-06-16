################################################################################
#                                                                              #
#                      L O G I C L A N C E   S Y S T E M                       #
#                                                                              #
#  Module: FPGA Automation Tool — Shared Flow Utilities                        #
#  Author: Hemanth Kumar DM                                                    #
#  Role  : Physical Design Engineer, ASIC Automation Engineer                  #
#                                                                              #
#  Copyright (c) 2026 LogicLance. All rights reserved.                         #
#                                                                              #
################################################################################

import os
import sys
import json
import glob
import shutil
import subprocess
import readline
from datetime import datetime

# Re-export for convenience (HistoryDB is the Phase 1 memory)
try:
    from fpga_tool.intelligence.history import HistoryDB
except Exception:
    HistoryDB = None  # graceful

# ──────────────────── ANSI Colors ────────────────────

BLUE   = '\033[94m'
GREEN  = '\033[92m'
WARN   = '\033[93m'
FAIL   = '\033[91m'
BOLD   = '\033[1m'
DIM    = '\033[2m'
CYAN   = '\033[96m'
RESET  = '\033[0m'


# ──────────────────── SimLogger ────────────────────

class SimLogger:
    """Unified logger with colored terminal output and optional file logging."""

    def __init__(self, log_file=None, verbose=False):
        self.log_file = log_file
        self.verbose = verbose

    def set_log_file(self, log_file):
        self.log_file = log_file

    def _append(self, msg):
        if self.log_file:
            try:
                os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
                with open(self.log_file, "a") as f:
                    f.write(msg + "\n")
            except Exception:
                pass

    def debug(self, msg):
        if self.verbose:
            print(f"{DIM}[DEBUG] {msg}{RESET}")
        self._append(f"[DEBUG] {msg}")

    def info(self, msg):
        print(f"{BLUE}[INFO]{RESET} {msg}")
        self._append(f"[INFO] {msg}")

    def success(self, msg):
        print(f"{GREEN}[SUCCESS]{RESET} {msg}")
        self._append(f"[SUCCESS] {msg}")

    def warn(self, msg):
        print(f"{WARN}[WARN]{RESET} {msg}")
        self._append(f"[WARN] {msg}")

    def error(self, msg):
        print(f"{FAIL}[ERROR]{RESET} {msg}")
        self._append(f"[ERROR] {msg}")

    def halt(self, msg):
        print(f"{BOLD}{FAIL}[HALT] {msg}{RESET}")
        self._append(f"[HALT] {msg}")
        sys.exit(1)

    def vivado_line(self, line, print_to_stdout=True):
        """Print a line from Vivado output with smart coloring."""
        line = line.rstrip()
        if not line:
            return
        self._append(line)
        if not print_to_stdout:
            return
            
        if "ERROR" in line or "CRITICAL" in line:
            print(f"  {FAIL}{line}{RESET}")
        elif "WARNING" in line or "WARN" in line:
            print(f"  {WARN}{line}{RESET}")
        elif "INFO" in line:
            print(f"  {DIM}{line}{RESET}")
        else:
            print(f"  {line}")


# ──────────────────── SmartInput ────────────────────

class SmartInput:
    """
    Handles interactive user input with rerun support.
    On rerun, values are restored from saved context instead of prompting.
    """

    def __init__(self, logger, flow_type='default', rerun_data=None):
        self.logger = logger
        self.flow_type = flow_type
        self.current_inputs = {}
        self.rerun_inputs = {}

        if flow_type == 'rerun' and rerun_data:
            self.rerun_inputs = rerun_data.get('context', {}).get('inputs', {})

    def get(self, prompt, key, default=None):
        """
        Prompt the user for input.
        On rerun, restores the saved value silently.
        """
        if self.flow_type == 'rerun' and key in self.rerun_inputs:
            val = self.rerun_inputs[key]
            self.logger.info(f"Restored {key}: {val}")
            self.current_inputs[key] = val
            return val

        try:
            if default is not None:
                user_val = input(f"{prompt} [{default}]: ").strip()
            else:
                user_val = input(f"{prompt}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            self.logger.halt("Input cancelled by user.")

        if not user_val and default is not None:
            user_val = str(default)

        self.current_inputs[key] = user_val
        return user_val

    def get_list(self, prompt, key, default=None):
        """Prompt for space-separated values, return as list."""
        raw = self.get(prompt, key, default=default or "")
        if not raw:
            return []
        if isinstance(raw, list):
            return raw
        return [x.strip() for x in raw.split() if x.strip()]

    def get_bool(self, prompt, key, default=True):
        """Prompt for yes/no."""
        default_str = "Y/n" if default else "y/N"
        raw = self.get(prompt, key, default=default_str)
        if raw in ("Y/n", "y/N"):
            return default
        return raw.lower() in ("y", "yes", "1", "true")

    def get_int(self, prompt, key, default=4):
        """Prompt for integer."""
        raw = self.get(prompt, key, default=str(default))
        try:
            return int(raw)
        except ValueError:
            return default

    def get_inputs(self):
        return self.current_inputs.copy()


# ──────────────────── CommandManager ────────────────────

class CommandManager:
    """Saves and loads tool execution context for --rerun support."""

    def __init__(self, root_dir, logger):
        self.root = root_dir
        self.logger = logger
        self.config_path = os.path.join(root_dir, ".fpga_tool_state.json")

    def load_last_command(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    return data.get('last_run')
        except Exception as e:
            self.logger.warn(f"Failed to load saved state: {e}")
        return None

    def save_last_command(self, cmd, context):
        try:
            data = {}
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    try:
                        data = json.load(f)
                    except Exception:
                        pass

            data['last_run'] = {
                'command': cmd,
                'context': context,
                'timestamp': datetime.now().isoformat()
            }

            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=4)
            self.logger.debug(f"Context saved to: {self.config_path}")
        except Exception as e:
            self.logger.warn(f"Failed to save state: {e}")


# ──────────────────── ArtifactManager ────────────────────

class ArtifactManager:
    """Handles archiving of simulation logs, reports, outputs."""

    def __init__(self, output_dir, logger):
        self.output_dir = output_dir
        self.logger = logger

    def ensure_dirs(self):
        """Create output subdirectories."""
        for sub in ["logs", "reports", "outputs"]:
            os.makedirs(os.path.join(self.output_dir, sub), exist_ok=True)

    def archive_file(self, src, sub="logs"):
        """Copy a file into the output directory."""
        if not os.path.exists(src):
            return
        dst_dir = os.path.join(self.output_dir, sub)
        os.makedirs(dst_dir, exist_ok=True)
        try:
            shutil.copy2(src, dst_dir)
            self.logger.debug(f"Archived: {src} → {dst_dir}/")
        except Exception as e:
            self.logger.warn(f"Failed to archive {src}: {e}")

    def archive_glob(self, pattern, sub="logs"):
        """Archive all files matching a glob pattern."""
        for f in glob.glob(pattern):
            self.archive_file(f, sub)


# ──────────────────── Dependency Verification ────────────────────

def find_vivado():
    """
    Find the Vivado binary. Search order:
    1. $XILINX_VIVADO/bin/vivado
    2. 'vivado' on PATH
    3. Common install paths
    """
    # Check XILINX_VIVADO environment
    xv = os.environ.get("XILINX_VIVADO")
    if xv:
        candidate = os.path.join(xv, "bin", "vivado")
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate

    # Check PATH
    result = shutil.which("vivado")
    if result:
        return result

    # Common install paths
    for base in ["/opt/Xilinx/Vivado", "/tools/Xilinx/Vivado"]:
        if os.path.isdir(base):
            versions = sorted(os.listdir(base), reverse=True)
            for v in versions:
                candidate = os.path.join(base, v, "bin", "vivado")
                if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                    return candidate

    return None


def find_gcc():
    """Find gcc C compiler (used by C-model flows)."""
    return shutil.which("gcc")


def find_make():
    """Find GNU make (used by C-model flows)."""
    return shutil.which("make")


def check_dependencies():
    """
    Check all external tools required by the FPGA Automation Tool.
    Returns a dict with tool name -> found_path or None.
    """
    return {
        "vivado": find_vivado(),
        "gcc": find_gcc(),
        "make": find_make(),
    }


def verify_environment(logger=None, require_vivado=True, require_cmodel_tools=False):
    """
    Verify that required external tools are available.
    Prints status using the provided logger (or prints to stdout).
    Returns True if all required tools are present.
    """
    deps = check_dependencies()
    all_ok = True

    def log(msg, level="info"):
        if logger:
            if level == "warn":
                logger.warn(msg)
            elif level == "error":
                logger.error(msg)
            else:
                logger.info(msg)
        else:
            print(msg)

    log("=== Dependency Verification ===")

    # Vivado (always required for FPGA flows)
    if deps["vivado"]:
        log(f"✅ Vivado found: {deps['vivado']}")
    else:
        log("❌ Vivado NOT FOUND. Set $XILINX_VIVADO or add 'vivado' to PATH.", "error")
        all_ok = False
        if require_vivado:
            return False

    # C-model tools (gcc + make) - only strictly required if using C-model flows
    cmodel_ok = bool(deps["gcc"] and deps["make"])
    if deps["gcc"]:
        log(f"✅ gcc found: {deps['gcc']}")
    else:
        log("⚠️  gcc NOT FOUND. C-model flows will fail.", "warn")
    if deps["make"]:
        log(f"✅ make found: {deps['make']}")
    else:
        log("⚠️  make NOT FOUND. C-model flows will fail.", "warn")

    if require_cmodel_tools and not cmodel_ok:
        log("C-model tools (gcc + make) are required for this flow.", "error")
        all_ok = False

    if all_ok:
        log("✅ All required external dependencies appear available.")
    else:
        log("⚠️  Some dependencies are missing. Flows may fail.")

    log("================================")
    return all_ok


# ──────────────────── Tab Completion ────────────────────

def enable_tab_completion():
    """Enables TAB completion for file path inputs."""
    def path_completer(text, state):
        if '~' in text:
            text = os.path.expanduser(text)
        if os.path.isdir(text) and not text.endswith('/'):
            text += "/"
        matches = glob.glob(text + '*')
        results = [x + "/" if os.path.isdir(x) else x for x in matches]
        return results[state] if state < len(results) else None

    try:
        readline.set_completer_delims(' \t\n;')
        readline.parse_and_bind("tab: complete")
        readline.set_completer(path_completer)
    except Exception:
        pass
