################################################################################
#                                                                              #
#                      L O G I C L A N C E   S Y S T E M                       #
#                                                                              #
#  Module: FPGA Automation Tool — Knowledge / Rule Packs (Phase 3)             #
#                                                                              #
################################################################################

"""
Phase 3: Extensible knowledge system.

Knowledge packs are loadable JSON (or simple dicts) that extend:
- Recommendations
- Planner rules
- XDC templates
- Strategy preferences

Users or teams can drop packs into configs/packs/ or pass custom ones.
No code changes needed to add domain knowledge.

Default built-in pack covers common FPGA gotchas.
"""

import os
import json
from typing import List, Dict, Any, Optional


DEFAULT_PACK = {
    "name": "builtin_core",
    "version": "1.0",
    "recommendations": [
        {
            "condition": {"no_clock": {"gt": 4}},
            "message": "Add clock constraints (create_clock) and input/output delays. Unconstrained registers are the #1 source of early timing failures."
        },
        {
            "condition": {"wns": {"lt": -0.8}},
            "message": "Significant negative slack. Try pipeline insertion, retiming, or physical optimization. History shows +0.3 to +0.7ns gains common."
        },
        {
            "condition": {"junction_c": {"gt": 100}},
            "message": "High junction temperature. Reduce clock rate for bring-up or improve cooling / use industrial part."
        }
    ],
    "strategy_prefs": {
        "timing_critical": ["ExtraTiming", "Aggressive"],
        "power_sensitive": ["PowerOpt"],
        "small_designs": ["Default", "AreaOpt"]
    },
    "xdc_templates": {
        "common_resets": ["reset", "rst", "areset_n"]
    }
}


class KnowledgeBase:
    """Loads and applies extensible rule packs."""

    def __init__(self, pack_paths: Optional[List[str]] = None, logger=None):
        self.logger = logger
        self.packs: List[Dict] = [DEFAULT_PACK]
        self._load_packs(pack_paths or self._default_pack_locations())

    def _default_pack_locations(self) -> List[str]:
        candidates = [
            "configs/packs",
            os.path.join(os.path.dirname(__file__), "..", "..", "configs", "packs"),
            os.path.expanduser("~/.logiclance/packs"),
        ]
        return [c for c in candidates if os.path.isdir(c)]

    def _load_packs(self, locations: List[str]):
        for loc in locations:
            try:
                for fn in os.listdir(loc):
                    if fn.endswith(".json"):
                        path = os.path.join(loc, fn)
                        with open(path) as f:
                            pack = json.load(f)
                            self.packs.append(pack)
                            if self.logger:
                                self.logger.debug(f"Loaded knowledge pack: {pack.get('name')}")
            except Exception as e:
                if self.logger:
                    self.logger.debug(f"Pack load skipped ({loc}): {e}")

    def get_recommendations(self, metrics: Dict, design_model: Any = None) -> List[str]:
        recs = []
        for pack in self.packs:
            for rule in pack.get("recommendations", []):
                if self._matches(rule.get("condition", {}), metrics, design_model):
                    recs.append(rule["message"])
        return recs

    def _matches(self, cond: Dict, metrics: Dict, model: Any) -> bool:
        if not cond:
            return False
        for key, rule in cond.items():
            val = None
            # pull from flat metrics or nested
            if key in metrics:
                val = metrics[key]
            elif key in (metrics.get("timing") or {}):
                val = metrics["timing"][key]
            elif key in (metrics.get("power") or {}):
                val = metrics["power"][key]
            elif key in (metrics.get("methodology") or {}):
                val = metrics["methodology"][key]
            elif key == "no_clock" and model:
                # heuristic from model
                val = 32 if getattr(model, "has_unconstrained_clocks", lambda: False)() else 0

            if val is None:
                continue

            if isinstance(rule, dict):
                if "gt" in rule and not (float(val) > rule["gt"]): return False
                if "lt" in rule and not (float(val) < rule["lt"]): return False
                if "eq" in rule and val != rule["eq"]: return False
            else:
                if val != rule:
                    return False
        return True

    def get_strategy_prefs(self, context: str = "timing_critical") -> List[str]:
        prefs = []
        for pack in self.packs:
            prefs.extend(pack.get("strategy_prefs", {}).get(context, []))
        return prefs or ["Default"]

    def get_xdc_hints(self) -> Dict:
        hints = {}
        for pack in self.packs:
            hints.update(pack.get("xdc_templates", {}))
        return hints

    def all_packs(self) -> List[str]:
        return [p.get("name", "unnamed") for p in self.packs]


# Singleton-ish loader for flows
def get_knowledge_base(logger=None) -> KnowledgeBase:
    return KnowledgeBase(logger=logger)
