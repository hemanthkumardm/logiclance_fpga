################################################################################
#                                                                              #
#                      L O G I C L A N C E   S Y S T E M                       #
#                                                                              #
#  Module: FPGA Automation Tool — Self-Optimization & Strategy Search (Phase 3)#
#                                                                              #
################################################################################

"""
Phase 3: Autonomous optimization without AI.

- History-guided strategy selection: "what worked last time for this signature?"
- Limited self-directed retry loops for full flows on timing/power/regression failures.
- Simple search over known good directives (no ML, just ordered trials + scoring from history).
- Integrates with Planner and feeds recommendations.

Strategies are safe, bounded (max_attempts), and fully logged/explainable.
"""

import json
from typing import List, Dict, Any, Optional

# Default strategy library (realistic Vivado ones + our custom)
DEFAULT_STRATEGIES = [
    {"name": "Default", "synth": "Vivado Synthesis Defaults", "impl": "Vivado Implementation Defaults", "synth_jobs": 4, "impl_jobs": 8},
    {"name": "ExtraTiming", "synth": "Flow_ExtraTiming", "impl": "Flow_ExtraTimingOpt", "synth_jobs": 6, "impl_jobs": 12},
    {"name": "Aggressive", "synth": "Vivado Synthesis Defaults", "impl": "Performance_NetDelay_high", "synth_jobs": 8, "impl_jobs": 16},
    {"name": "AreaOpt", "synth": "Flow_AreaOptimized_high", "impl": "Flow_RuntimeOptimized", "synth_jobs": 4, "impl_jobs": 8},
    {"name": "PowerOpt", "synth": "Vivado Synthesis Defaults", "impl": "Flow_PowerOptimized_high", "synth_jobs": 4, "impl_jobs": 8},
]

class Optimizer:
    """
    Phase 3 optimizer.
    Uses history to score strategies per design signature and suggests or iterates limited trials.
    """

    def __init__(self, history_db=None, design_model=None, logger=None, max_attempts: int = 3):
        self.history = history_db
        self.model = design_model
        self.logger = logger
        self.max_attempts = max_attempts
        self.strategies = DEFAULT_STRATEGIES.copy()

    def best_strategy_for_signature(self, signature: str, part: str = "") -> Dict:
        """Return the strategy that historically gave best WNS (or success) for this sig."""
        if not self.history or not signature:
            return self.strategies[0]

        # Pull past runs for this sig that succeeded with full/impl
        similars = self.history.find_similar_runs(signature, part, limit=10)
        best = None
        best_score = -999

        for run in similars:
            if run.get("exit_code") != 0:
                continue
            try:
                m = json.loads(run.get("metrics_json") or "{}")
                wns = None
                if isinstance(m, dict):
                    wns = m.get("wns") or (m.get("timing") or {}).get("wns")
                score = float(wns) if wns is not None else 0.0
                if score > best_score:
                    best_score = score
                    # Try to recover strategy if we stored it, else default
                    strat_name = m.get("_strategy_name") if isinstance(m, dict) else None
                    if strat_name:
                        for s in self.strategies:
                            if s["name"] == strat_name:
                                best = s
                                break
            except Exception:
                continue

        return best or self.strategies[0]

    def suggest_strategies(self, signature: str, part: str = "", num: int = 3) -> List[Dict]:
        """Ordered list of strategies to try, best first."""
        best = self.best_strategy_for_signature(signature, part)
        ordered = [best] + [s for s in self.strategies if s["name"] != best["name"]]
        return ordered[:num]

    def run_optimization_loop(self, flow_runner_callable, base_config: dict, 
                              failure_checker, max_attempts: int = None) -> Dict:
        """
        Self-directed optimization loop (used in full flow on failure).

        flow_runner_callable(config) -> (exit_code, metrics_dict)
        failure_checker(metrics, exit_code) -> bool  (True if still bad)

        Returns final result + log of attempts.
        Bounded and safe.
        """
        if max_attempts is None:
            max_attempts = self.max_attempts

        sig = getattr(self.model, "signature", "") if self.model else ""
        part = getattr(self.model, "part", "") if self.model else base_config.get("fpga_part", "")

        attempts = []
        strategies_to_try = self.suggest_strategies(sig, part, num=max_attempts)

        current_config = dict(base_config)

        for i, strat in enumerate(strategies_to_try):
            attempt_config = dict(current_config)
            attempt_config["_strategy_name"] = strat["name"]
            # Inject strategy hints (tcl_gen and full_flow.tcl will pick up if extended, or we log)
            attempt_config["synth_directive"] = strat["synth"]
            attempt_config["impl_directive"] = strat["impl"]
            attempt_config["synth_jobs"] = strat["synth_jobs"]
            attempt_config["impl_jobs"] = strat["impl_jobs"]

            if self.logger:
                self.logger.info(f"[OPTIMIZER] Attempt {i+1}/{max_attempts}: strategy={strat['name']}")

            try:
                exit_code, metrics = flow_runner_callable(attempt_config)
                attempts.append({"strategy": strat["name"], "exit_code": exit_code, "metrics": metrics})

                if not failure_checker(metrics, exit_code):
                    if self.logger:
                        self.logger.success(f"[OPTIMIZER] Success on attempt {i+1} with {strat['name']}")
                    return {"success": True, "attempts": attempts, "final_strategy": strat, "final_metrics": metrics}
            except Exception as e:
                if self.logger:
                    self.logger.warn(f"[OPTIMIZER] Attempt {i+1} failed internally: {e}")
                attempts.append({"strategy": strat["name"], "error": str(e)})

        return {"success": False, "attempts": attempts, "final_strategy": strategies_to_try[-1]}

    def score_from_history(self, signature: str) -> Dict:
        """Simple stats for reports."""
        trend = self.history.get_closure_trend(signature) if self.history else {}
        best = self.best_strategy_for_signature(signature)
        return {"best_known_strategy": best["name"], "trend": trend}


# Simple failure checkers for common cases
def timing_failure_checker(metrics: dict, exit_code: int) -> bool:
    if exit_code != 0:
        return True
    t = metrics.get("timing") or {}
    wns = t.get("wns") if isinstance(t, dict) else metrics.get("wns")
    try:
        return float(wns) < -0.1 if wns is not None else False
    except Exception:
        return False

def regression_failure_checker(metrics: dict, exit_code: int) -> bool:
    return exit_code != 0 or metrics.get("failed_tests", 0) > 0
