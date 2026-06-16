################################################################################
#                                                                              #
#                      L O G I C L A N C E   S Y S T E M                       #
#                                                                              #
#  Module: FPGA Automation Tool — Intelligence Layer (Phase 1 foundations)     #
#  Author: Hemanth Kumar DM                                                    #
#  Role  : Physical Design Engineer, ASIC Automation Engineer                  #
#                                                                              #
#  Copyright (c) 2026 LogicLance. All rights reserved.                         #
#                                                                              #
################################################################################

"""
Intelligence foundations for the FPGA Automation Tool.

Provides design introspection, persistent history/recall, and rule-based
diagnostics & recommendations — all classical (no AI/LLMs).

This layer is deliberately best-effort and additive:
- Never breaks existing flows or rerun.
- All failures degrade to warnings.
- Designed to be called from run_fpga_xilinx flows.

Public API (re-exported):
    DesignModel, ModuleInfo
    HistoryDB
    build_intelligence_report, generate_recommendations
    build_design_model_safely, collect_run_metrics
"""

from .design_model import DesignModel, ModuleInfo
from .history import HistoryDB
from .diagnostics import (
    build_intelligence_report,
    generate_recommendations,
    generate_html_report,
    generate_additional_test_cases,
    assess_asic_readiness,
)
from .planner import FlowPlanner, create_planner_for_config
from .optimizer import Optimizer, timing_failure_checker, regression_failure_checker
from .knowledge import KnowledgeBase, get_knowledge_base
from .watcher import SourceWatcher, create_watcher_for_config
from .plugins import register_advisor, register_pack_loader, register_flow_hook, apply_advisors, get_advisors

# Convenience high-level entry points used by the flows
def build_design_model_safely(config, logger=None):
    """Best-effort builder. Returns a DesignModel (possibly minimal) or None."""
    try:
        model = DesignModel.from_config(config, logger=logger)
        model.build()
        if logger:
            logger.debug(f"Design model built: {model.short_digest().splitlines()[0] if model.short_digest() else 'minimal'}")
        return model
    except Exception as e:
        if logger:
            logger.warn(f"Intelligence: design model build skipped ({e})")
        return None


def collect_run_metrics_safely(output_dir, logger=None):
    """Best-effort metrics collection from the run's reports/ dir."""
    try:
        from fpga_tool.fpga_parser import collect_run_metrics
        return collect_run_metrics(output_dir)
    except Exception as e:
        if logger:
            logger.warn(f"Intelligence: metrics collection skipped ({e})")
        return {}


__all__ = [
    "DesignModel",
    "ModuleInfo",
    "HistoryDB",
    "FlowPlanner",
    "create_planner_for_config",
    "Optimizer",
    "timing_failure_checker",
    "regression_failure_checker",
    "KnowledgeBase",
    "get_knowledge_base",
    "SourceWatcher",
    "create_watcher_for_config",
    "register_advisor",
    "register_pack_loader",
    "register_flow_hook",
    "apply_advisors",
    "get_advisors",
    "build_intelligence_report",
    "generate_recommendations",
    "generate_html_report",
    "generate_additional_test_cases",
    "assess_asic_readiness",
    "build_design_model_safely",
    "collect_run_metrics_safely",
]

__version__ = "1.1.0-dev-intel"
