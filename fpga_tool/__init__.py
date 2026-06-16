################################################################################
#                                                                              #
#                      L O G I C L A N C E   S Y S T E M                       #
#                                                                              #
#  Module: FPGA Automation Tool                                                #
#  Author: Hemanth Kumar DM                                                    #
#  Role  : Physical Design Engineer, ASIC Automation Engineer                  #
#                                                                              #
#  Copyright (c) 2026 LogicLance. All rights reserved.                         #
#                                                                              #
################################################################################

__version__ = "1.1.0-dev-intel-phase1"

# Phase 1 + Phase 2 + Phase 3 intelligence (self-optimizing, watch, knowledge, plugins foundation)
try:
    from .intelligence import (
        DesignModel,
        HistoryDB,
        FlowPlanner,
        create_planner_for_config,
        Optimizer,
        KnowledgeBase,
        get_knowledge_base,
        SourceWatcher,
        create_watcher_for_config,
        build_intelligence_report,
        generate_html_report,
        generate_additional_test_cases,
        build_design_model_safely,
        collect_run_metrics_safely,
    )
except Exception:
    pass
