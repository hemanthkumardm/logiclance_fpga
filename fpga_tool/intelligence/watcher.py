################################################################################
#                                                                              #
#                      L O G I C L A N C E   S Y S T E M                       #
#                                                                              #
#  Module: FPGA Automation Tool — Continuous Watch Mode (Phase 3)              #
#                                                                              #
################################################################################

"""
Phase 3: Continuous / watch mode.

Monitors source directories for changes (using mtime + content hash polling — pure stdlib).
Uses Planner + DesignModel to decide the minimal intelligent re-action:
  - Only RTL changed? -> re-synth/impl + test
  - Only TB/C-model? -> re-sim/regression only
  - No material change? -> skip

Provides a long-running --watch mode in the CLI.
"""

import os
import time
import hashlib
from typing import Dict, Callable, List, Optional, Any


class SourceWatcher:
    """
    Polling-based watcher (stdlib only, cross-platform).
    Call .watch(...) with a callback that receives a delta dict.
    """

    def __init__(self, roots: List[str], poll_interval: float = 2.0, logger=None):
        self.roots = [os.path.abspath(r) for r in roots if r]
        self.poll_interval = poll_interval
        self.logger = logger
        self._last_state: Dict[str, str] = {}  # path -> hash

    def _hash_file(self, path: str) -> str:
        try:
            with open(path, "rb") as f:
                data = f.read(128 * 1024)  # head is enough for change detect
                return hashlib.sha256(data).hexdigest()[:12]
        except Exception:
            return "err"

    def _scan(self) -> Dict[str, str]:
        state = {}
        for root in self.roots:
            if not os.path.isdir(root):
                continue
            for dirpath, _, filenames in os.walk(root):
                for fn in filenames:
                    if fn.endswith((".v", ".sv", ".vhd", ".vhdl", ".c", ".h", "Makefile", ".tcl", ".xdc", ".xpr")):
                        p = os.path.join(dirpath, fn)
                        state[p] = self._hash_file(p)
        return state

    def compute_delta(self, current: Dict[str, str], previous: Dict[str, str]) -> Dict:
        added = [p for p in current if p not in previous]
        removed = [p for p in previous if p not in current]
        changed = [p for p in current if p in previous and current[p] != previous[p]]

        rtl_changed = any(p.endswith((".v", ".sv", ".vhd", ".vhdl")) for p in (added + changed))
        tb_changed = any("tb" in p.lower() or p.endswith((".v", ".sv")) for p in (added + changed)) and not rtl_changed
        cmodel_changed = any("c_model" in p.lower() or p.endswith((".c", "Makefile")) for p in (added + changed))

        return {
            "added": added,
            "removed": removed,
            "changed": changed,
            "rtl_changed": rtl_changed,
            "tb_or_cmodel_only": (tb_changed or cmodel_changed) and not rtl_changed,
            "has_change": bool(added or removed or changed),
        }

    def watch(self, on_change: Callable[[Dict], None], stop_event=None):
        """Long running watch loop. on_change receives delta dict."""
        if self.logger:
            self.logger.info(f"[WATCH] Monitoring {len(self.roots)} roots (poll {self.poll_interval}s)")

        self._last_state = self._scan()

        while True:
            if stop_event and stop_event.is_set():
                break

            time.sleep(self.poll_interval)
            current = self._scan()
            delta = self.compute_delta(current, self._last_state)

            if delta["has_change"]:
                if self.logger:
                    self.logger.info(f"[WATCH] Change detected: {len(delta['changed'])} changed, {len(delta['added'])} added")
                try:
                    on_change(delta)
                except Exception as e:
                    if self.logger:
                        self.logger.warn(f"[WATCH] Callback error (continuing): {e}")
                self._last_state = current


def create_watcher_for_config(config: dict, logger=None) -> Optional[SourceWatcher]:
    roots = []
    for k in ("source_files", "SOURCE_FILES", "tb_dir", "TB_DIR", "cmodel_dir", "project_dir"):
        v = config.get(k) or config.get(k.upper(), "")
        if isinstance(v, str) and v:
            roots.append(v)
        elif isinstance(v, list):
            roots.extend([str(x) for x in v if x])
    roots = list(set(os.path.abspath(r) for r in roots if r and os.path.exists(r)))
    if not roots:
        return None
    return SourceWatcher(roots, logger=logger)
