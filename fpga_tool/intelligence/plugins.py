################################################################################
#                                                                              #
#                      L O G I C L A N C E   S Y S T E M                       #
#                                                                              #
#  Module: FPGA Automation Tool — Simple Plugin Skeleton (Phase 3)             #
#                                                                              #
################################################################################

"""
Phase 3 plugin foundation.

Provides a minimal registry for:
- Custom advisors (extend recommendations)
- Pack loaders
- Flow step hooks

Usage:
  from fpga_tool.intelligence.plugins import register_advisor, get_advisors
  def my_advisor(model, metrics): ...
  register_advisor(my_advisor)

Plugins can be discovered from a plugins/ dir in future.
"""

from typing import Callable, List, Dict, Any

_advisors: List[Callable] = []
_pack_loaders: List[Callable] = []
_flow_hooks: Dict[str, List[Callable]] = {}


def register_advisor(func: Callable[[Any, Dict], List[str]]):
    """Register a function that takes (design_model, metrics) and returns list of rec strings."""
    _advisors.append(func)


def register_pack_loader(func: Callable[[], Dict]):
    """Register a function that returns a knowledge pack dict."""
    _pack_loaders.append(func)


def register_flow_hook(stage: str, func: Callable):
    """Register hook for stages like 'pre_full_flow', 'post_regression'."""
    _flow_hooks.setdefault(stage, []).append(func)


def get_advisors() -> List[Callable]:
    return list(_advisors)


def get_pack_loaders() -> List[Callable]:
    return list(_pack_loaders)


def get_flow_hooks(stage: str) -> List[Callable]:
    return _flow_hooks.get(stage, [])


def apply_advisors(design_model, metrics, base_recs: List[str]) -> List[str]:
    """Run all registered advisors and merge unique recs."""
    recs = list(base_recs)
    for adv in _advisors:
        try:
            extra = adv(design_model, metrics) or []
            for r in extra:
                if r not in recs:
                    recs.append(r)
        except Exception:
            pass
    return recs


# Example built-in plugin (can be extended)
def _example_plugin_advisor(model, metrics):
    if metrics.get("power", {}).get("total_w", 0) > 20:
        return ["Plugin: High power - consider PowerOpt strategy from pack."]
    return []


register_advisor(_example_plugin_advisor)
