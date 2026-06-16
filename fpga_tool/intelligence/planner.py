################################################################################
#                                                                              #
#                      L O G I C L A N C E   S Y S T E M                       #
#                                                                              #
#  Module: FPGA Automation Tool — Flow Planner & Incremental Intelligence      #
#  (Phase 2)                                                                   #
#                                                                              #
################################################################################

"""
Phase 2: Autonomous flow planning and incremental execution intelligence.

The FlowPlanner uses the DesignModel (RTL-aware signature) + HistoryDB to:

- Decide whether expensive steps (synth/impl) can be safely skipped for the
  current flow (true incremental).
- Produce strong pre-run recommendations ("This RTL has not changed since the
  last successful routed run — you can jump straight to regression.").
- Suggest strategies and reuse opportunities.
- Provide "change delta" analysis.

All decisions are explainable and conservative (never silently skip if RTL changed).
"""

import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime


class FlowPlanner:
    """
    Expert planner for the FPGA flows.
    Instantiate with history and (optionally) a built design model.
    """

    def __init__(self, history_db=None, design_model=None, logger=None):
        self.history = history_db
        self.model = design_model
        self.logger = logger
        self._last_decision = None

    def analyze(self, config: dict, flow: str, previous_run_info: dict = None) -> dict:
        """
        Main entry: returns a rich decision dict with:
          - can_skip_synth_impl: bool
          - reason: str (human)
          - rtl_changed: bool
          - suggested_action: str
          - previous_success: dict or None
          - delta_summary: str
        """
        decision = {
            "flow": flow,
            "can_skip_synth_impl": False,
            "rtl_changed": True,
            "reason": "No prior successful implementation found for this design.",
            "suggested_action": "Run full synthesis + implementation as requested.",
            "previous_success": None,
            "delta_summary": "",
            "confidence": "low",
        }

        if not self.model or not self.history:
            return decision

        sig = getattr(self.model, "signature", "")
        part = getattr(self.model, "part", "") or config.get("fpga_part", "")

        if not sig:
            return decision

        # Look for last successful full or impl run with exact same RTL signature
        prev = self.history.get_last_successful_for_sig(sig) or \
               self._find_last_successful_impl(sig, part)

        if not prev:
            decision["reason"] = "First time this exact RTL signature has been seen."
            return decision

        decision["previous_success"] = {
            "run_id": prev.get("id"),
            "timestamp": prev.get("timestamp"),
            "flow": prev.get("flow"),
        }

        # Determine what changed
        current_input_sig = self._compute_input_sig(config)
        prev_metrics = {}
        try:
            prev_metrics = json.loads(prev.get("metrics_json") or "{}")
        except Exception:
            pass

        prev_input = prev_metrics.get("_input_sig", "")

        rtl_changed = (sig != prev.get("design_signature", ""))
        # Even if signature matches, we can further check explicit source hashes if wanted.
        # For Phase 2 we treat model.signature (which hashes HDL content) as the RTL truth.

        tb_or_cmodel_only = not rtl_changed and (current_input_sig != prev_input)

        decision["rtl_changed"] = rtl_changed

        if not rtl_changed and tb_or_cmodel_only:
            decision["can_skip_synth_impl"] = True
            decision["reason"] = (
                f"RTL content identical to successful run {prev.get('id')[:12]} "
                f"({prev.get('timestamp', '')[:16]}). Only testbench / C-model inputs changed."
            )
            decision["suggested_action"] = (
                "Safe to reuse previous placed-and-routed netlist for simulation/regression. "
                "Skip synth + impl for massive time savings."
            )
            decision["delta_summary"] = "RTL unchanged | TB/C-model delta detected"
            decision["confidence"] = "high"
        elif not rtl_changed:
            decision["can_skip_synth_impl"] = True
            decision["reason"] = "Exact same design signature as last successful implementation."
            decision["suggested_action"] = "You can jump straight to post-implementation simulation or regression."
            decision["delta_summary"] = "No significant input changes detected"
            decision["confidence"] = "medium"
        else:
            decision["reason"] = "RTL (or critical sources) have changed since last success."
            decision["suggested_action"] = "Full synth + impl required."
            decision["delta_summary"] = "RTL changed — incremental reuse not safe"

        self._last_decision = decision
        return decision

    def get_pre_run_advice(self, config: dict, flow: str) -> List[str]:
        """Returns a list of one-liner advice strings suitable for printing before a long run."""
        advice = []
        dec = self.analyze(config, flow)
        if dec.get("can_skip_synth_impl"):
            advice.append(f"[SMART] {dec['reason']}")
            advice.append(f"[ACTION] {dec['suggested_action']}")
        elif dec.get("previous_success"):
            advice.append(f"[INFO] Previous success for this exact design: {dec['previous_success']['timestamp'][:16]}")
        return advice

    def recommend_closure_actions(self, current_wns: Optional[float], history_trends: dict = None) -> List[str]:
        """Phase 2 Closure Advisor — used by diagnostics."""
        recs = []
        if current_wns is None:
            return recs
        try:
            w = float(current_wns)
        except Exception:
            return recs

        if w < -1.5:
            recs.append("WNS is quite negative. Strongly consider enabling 'ExtraTimingOpt' or 'Flow_ExtraTimingOpt' strategy on next impl attempt.")
        elif w < -0.5:
            recs.append("Moderate negative slack. Physical optimization + register duplication on high-fanout nets often helps here.")
        elif 0 > w >= -0.5:
            recs.append("Very close! One or two strategic multi-cycle or false-path constraints on non-critical CDCs usually closes it.")

        if history_trends and history_trends.get("avg_wns_last_3"):
            try:
                avg = float(history_trends["avg_wns_last_3"])
                if w > avg + 0.2:
                    recs.append(f"Improvement of {w - avg:.2f} ns vs your recent average on similar designs — good progress.")
            except Exception:
                pass
        return recs

    # --- helpers ---
    def _find_last_successful_impl(self, sig: str, part: str):
        if not self.history:
            return None
        # Try to find any previous run that reached "impl" successfully for this sig
        similars = self.history.find_similar_runs(sig, part, limit=5)
        for r in similars:
            if r.get("exit_code") == 0 and r.get("flow") in ("full", "impl"):
                return r
        return None

    def _compute_input_sig(self, config: dict) -> str:
        # Reuse / extend the simple one from Phase 1
        import hashlib
        h = hashlib.sha256()
        keys = ("project_xpr", "source_files", "tb_dir", "tb_files", "cmodel_dir", "cmodel_stdin", "result_file")
        for k in keys:
            v = config.get(k) or config.get(k.upper(), "")
            if isinstance(v, (list, tuple)):
                v = " ".join(str(x) for x in v)
            h.update(str(v).encode("utf-8", errors="ignore"))
        return h.hexdigest()[:16]


# Convenience factory used by flows
def create_planner_for_config(config: dict, logger=None) -> FlowPlanner:
    """Creates a planner wired to the current model + a live HistoryDB."""
    try:
        from fpga_tool.intelligence import build_design_model_safely, HistoryDB
        model = build_design_model_safely(config, logger=logger)
        hist = HistoryDB(logger=logger)
        return FlowPlanner(history_db=hist, design_model=model, logger=logger)
    except Exception as e:
        if logger:
            logger.debug(f"Planner creation degraded: {e}")
        return FlowPlanner(history_db=None, design_model=None, logger=logger)
