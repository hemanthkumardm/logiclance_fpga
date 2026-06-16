################################################################################
#                                                                              #
#                      L O G I C L A N C E   S Y S T E M                       #
#                                                                              #
#  Module: FPGA Automation Tool — Diagnostics, Narrative & Recommendations     #
#  (Phase 1 — rule-based "expert" explanations)                                #
#                                                                              #
################################################################################

"""
Generates the human-facing "Design Intelligence Report".

All logic is classical:
- Data from DesignModel + collected metrics + history recall
- Small set of deterministic rules + narrative templates
- Produces clear, actionable paragraphs that feel like an experienced engineer commenting on the run
"""

from typing import List, Dict, Any
import os
from datetime import datetime


def build_intelligence_report(design_model: Any = None,
                              metrics: Dict = None,
                              recalls: List[str] = None,
                              previous_metrics: Dict = None,
                              planner_decision: Any = None) -> str:
    """
    Main entry point. Returns a nicely formatted multi-section string.
    Safe on partial / missing data.
    """
    if metrics is None:
        metrics = {}
    if recalls is None:
        recalls = []

    # Detect if this run was incremental (planner decided to skip synth/impl and reuse previous reports)
    is_incremental = bool(planner_decision and planner_decision.get("can_skip_synth_impl"))

    lines = []
    lines.append("")
    lines.append("╔" + "═" * 68 + "╗")
    lines.append("║  DESIGN INTELLIGENCE REPORT" + " " * 41 + "║")
    lines.append("╚" + "═" * 68 + "╝")

    # 1. Design digest
    lines.append("\n── Design Digest ─────────────────────────────────────────────")
    if design_model and hasattr(design_model, "short_digest"):
        for line in design_model.short_digest().splitlines():
            lines.append("  " + line)
    else:
        lines.append("  (No detailed design model available for this run)")

    # 2. Key metrics (enhanced)
    lines.append("\n── Key Metrics ──────────────────────────────────────────────")
    t = metrics.get("timing") or {}
    p = metrics.get("power") or {}
    c = metrics.get("clock") or {}
    meth = metrics.get("methodology") or {}

    if t.get("wns") is not None:
        lines.append(f"  Timing WNS : {t['wns']} ns   (TNS: {t.get('tns', '?')})")
    elif "wns" in metrics:
        lines.append(f"  Timing WNS : {metrics.get('wns')} ns")

    if p.get("total_w") is not None:
        warn = "  ⚠️  " + "; ".join(p.get("warnings", [])) if p.get("warnings") else ""
        lines.append(f"  Power      : {p['total_w']} W total (dyn {p.get('dynamic_w','?')})  Junction {p.get('junction_c','?')}°C{warn}")

    if meth.get("no_clock"):
        line = f"  Check timing: {meth['no_clock']} registers with no clock (unconstrained)"
        if is_incremental:
            line += " (from previous implementation run)"
        lines.append(line)

    if c.get("bufg_used") is not None:
        lines.append(f"  Clocking   : {c['bufg_used']} BUFG used")

    if metrics.get("reports_found"):
        lines.append(f"  Reports archived: {metrics['reports_found']}")

    if is_incremental:
        lines.append("\n  (Note: This run was incremental - RTL unchanged, skipped synth/impl. The metrics and reports below are from the previous full implementation run. The auto-generated XDC added in a prior run will be used on the next full synth+impl.)")

    # 3. History recall
    if recalls:
        lines.append("\n── History Recall & Trends ─────────────────────────────────")
        for r in recalls[:5]:
            lines.append("  • " + r)

    # 3.5 ASIC / SoC Feasibility (new)
    asic_level, asic_score, asic_reasons, asic_caveats = assess_asic_readiness(design_model, metrics)
    lines.append("\n── ASIC / SoC Feasibility Prediction (Heuristic) ─────────────")
    lines.append(f"  Readiness : {asic_level} ({asic_score}/100)")
    if asic_reasons:
        for r in asic_reasons[:4]:
            lines.append("    • " + r)
    if asic_caveats:
        lines.append("  Important Caveats:")
        for c in asic_caveats[:3]:
            lines.append("    • " + c)
    lines.append("  (Classical heuristic only — run proper ASIC front-end tools for real assessment.)")

    # 4. Recommendations (the "expert advice")
    recs = generate_recommendations(design_model, metrics, recalls)
    if recs:
        lines.append("\n── Recommendations ─────────────────────────────────────────")
        for r in recs:
            lines.append("  → " + r)

    lines.append("\n" + "─" * 70)
    lines.append("  (Intelligence is best-effort and improves with more run history.)")
    lines.append("")

    return "\n".join(lines)


def generate_recommendations(design_model: Any, metrics: Dict, recalls: List[str], planner_decision: Dict = None, knowledge=None) -> List[str]:
    """Phase 3: rule engine + planner + knowledge packs."""
    recs: List[str] = []
    if metrics is None:
        metrics = {}

    t = metrics.get("timing") or {}
    p = metrics.get("power") or {}
    meth = metrics.get("methodology") or {}
    wns = t.get("wns") if isinstance(t, dict) else metrics.get("wns")

    # Planner-driven
    if planner_decision and planner_decision.get("can_skip_synth_impl"):
        recs.append(planner_decision.get("suggested_action", "Incremental reuse recommended."))

    # Knowledge pack rules (Phase 3)
    if knowledge:
        try:
            pack_recs = knowledge.get_recommendations(metrics, design_model)
            recs.extend(pack_recs)
        except Exception:
            pass

    # Unconstrained / methodology
    no_clock = meth.get("no_clock", 0) or metrics.get("no_clock", 0)
    if no_clock and no_clock > 4:
        msg = f"Add clock constraints (create_clock) and input/output delays. {no_clock} registers currently have no clock — this is the #1 reason for early timing failures."
        if planner_decision and planner_decision.get("can_skip_synth_impl"):
            msg += " (from previous implementation run; the auto-generated XDC was added in a subsequent run and will apply on the next full synthesis/implementation.)"
        recs.append(msg)

    # Power / thermal
    if p.get("warnings") or (p.get("junction_c") and p["junction_c"] > 100):
        recs.append("Junction temperature is high or exceeded. Consider lower clock frequency for bring-up, "
                    "or review toggle rates / use a commercial-grade part with better cooling for final runs.")

    # Timing + Closure
    if wns is not None:
        try:
            w = float(wns)
            if w < -0.8:
                recs.append(f"Significant negative slack ({wns} ns). Common high-leverage fixes: pipeline stages on long paths, "
                            "retiming, or moving logic across clock domains.")
            elif -0.8 <= w < 0:
                recs.append("Timing is close but negative. A single well-placed register or tighter constraint on a false path frequently closes it.")
        except Exception:
            pass

    if recalls:
        recs.append("Previous similar runs recorded — use 'Load Last Run Config' in the GUI for fast iteration.")

    if design_model and getattr(design_model, "estimated_size_proxy", 0) < 20 and no_clock > 0:
        msg = "Small design — missing XDC is usually the entire problem."
        if planner_decision and planner_decision.get("can_skip_synth_impl"):
            msg += " (XDC auto-generated in a later run; reports here are stale from pre-XDC implementation.)"
        recs.append(msg)

    # New ASIC readiness bullet
    try:
        level, score, _, _ = assess_asic_readiness(design_model, metrics)
        if level != "High":
            recs.append(f"ASIC/SoC Readiness is only '{level}' ({score}/100) — see the dedicated section in the intelligence report before starting a real ASIC flow.")
    except Exception:
        pass

    # Dedup
    seen = set()
    unique = []
    for r in recs:
        if r not in seen:
            seen.add(r)
            unique.append(r)
    return unique[:8]


# ─────────────────────────────────────────────────────────────
# Phase 3+: ASIC / SoC Feasibility Prediction (classical heuristic)
# ─────────────────────────────────────────────────────────────

def assess_asic_readiness(design_model, metrics=None):
    """
    Heuristic prediction: how ready is this design for ASIC/SoC porting?
    Returns (readiness_level, score_0_to_100, list_of_reasons, list_of_caveats)
    Purely rule-based from the DesignModel + available metrics.
    """
    if metrics is None:
        metrics = {}

    score = 100
    reasons = []
    caveats = []

    # Clock / CDC
    num_clocks = len(getattr(design_model, "clock_domains", [])) if design_model else 0
    if design_model and design_model.has_unconstrained_clocks():
        score -= 25
        reasons.append("Unconstrained clocks detected (will require full SDC + timing closure work in ASIC)")
    if num_clocks > 1:
        score -= 15
        reasons.append(f"{num_clocks} clock domains (CDC hardening, async FIFO design, and verification required for ASIC)")

    # Power / thermal from FPGA run (proxy for high toggle / power density)
    p = metrics.get("power") or {}
    total_power = p.get("total_w") or 0
    if total_power > 15 or any("junction" in str(w).lower() for w in p.get("warnings", [])):
        score -= 15
        reasons.append("High power / thermal in FPGA run (ASIC will need aggressive power gating, voltage islands, or lower frequency)")
        caveats.append("FPGA power is only a rough proxy; run ASIC power estimation (PrimePower / Joules) early")

    # Size / complexity proxy
    size = getattr(design_model, "estimated_size_proxy", 0) if design_model else 0
    if size > 5000:
        score -= 10
        reasons.append("Large estimated size (consider hierarchical floorplanning and DFT insertion for ASIC)")

    # Positive factors
    if num_clocks <= 1 and size < 2000 and total_power < 8:
        score += 5
        reasons.append("Relatively simple clocking + modest size + low power footprint (easier ASIC port)")

    # Final classification
    if score >= 80:
        level = "High"
    elif score >= 55:
        level = "Medium"
    else:
        level = "Low / Needs significant work"

    # Standard ASIC porting caveats
    caveats.append("This is a classical heuristic only — not a substitute for proper ASIC front-end (synthesis with Design Compiler, STA with PrimeTime, power analysis, DFT, etc.)")
    caveats.append("FPGA-specific resources (DSP blocks, BRAM, LUT RAM) will need ASIC equivalents or RTL changes")
    caveats.append("You will need a proper SDC (not XDC), full CDC verification, and usually some micro-architecture tweaks for timing/power")

    return level, max(0, min(100, score)), reasons, caveats


def explain_failure_causally(design_model: Any, metrics: Dict, history_runs: List[Dict] = None, planner_dec: Dict = None) -> str:
    """
    Phase 3 causal root cause explainer.
    Links design model problems (e.g. unconstrained clocks), specific report violations (no_clock, WNS),
    and past history failures into a narrative.
    """
    if not metrics:
        return "No metrics for causal analysis."
    parts = []
    t = metrics.get("timing") or {}
    meth = metrics.get("methodology") or {}
    wns = t.get("wns") or metrics.get("wns")
    no_clock = meth.get("no_clock", 0) or metrics.get("no_clock", 0)

    if design_model and design_model.has_unconstrained_clocks() and no_clock > 0:
        parts.append(f"Root cause likely: Design model shows no explicit clocks in RTL, matching {no_clock} 'no_clock' violations in reports. This directly caused the WNS={wns}.")

    if wns is not None and float(wns) < -0.5:
        parts.append(f"Timing failure (WNS {wns}ns) correlates with unconstrained logic in model and previous similar runs (see history).")

    if planner_dec and planner_dec.get("rtl_changed"):
        parts.append("Causal: RTL change detected by planner signature vs history; previous success no longer applies.")

    if history_runs:
        parts.append(f"Matches {len(history_runs)} prior failures with similar metrics; check those reports for common modules.")

    if not parts:
        parts.append("No strong causal link identified; review detailed timing paths and design model ports/clocks.")

    return "Causal Analysis: " + " ".join(parts)


# --- Phase 2: Rich HTML Report + Trends ---

def generate_html_report(design_model: Any = None, metrics: Dict = None,
                         recalls: List[str] = None, recommendations: List[str] = None,
                         planner_decision: Dict = None, trend_data: List[Dict] = None) -> str:
    """
    Produce a beautiful, self-contained HTML report (Tailwind via CDN).
    Can be opened directly in any browser. Includes the intelligence narrative plus
    Phase 2 extras (planner decision, trend table).
    """
    if metrics is None: metrics = {}
    if recalls is None: recalls = []
    if recommendations is None: recommendations = []
    if trend_data is None: trend_data = []

    title = "Design Intelligence Report"
    if design_model and getattr(design_model, "project_name", None):
        title = f"Intelligence — {design_model.project_name}"

    # Simple CSS + Tailwind CDN for "rich" modern look with zero install
    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body {{ font-family: system-ui, sans-serif; }}
    .metric-card {{ transition: all 0.1s ease; }}
    .section-header {{ border-bottom: 3px solid #1e40af; }}
  </style>
</head>
<body class="bg-slate-950 text-slate-200">
<div class="max-w-5xl mx-auto p-8">
  <div class="flex items-center justify-between mb-6">
    <div>
      <h1 class="text-4xl font-bold tracking-tight text-white">{title}</h1>
      <p class="text-slate-400 mt-1">Generated by LogicLance FPGA Automation — Phase 2 Intelligence</p>
    </div>
    <div class="text-right text-sm text-slate-400">
      {datetime.now().strftime('%Y-%m-%d %H:%M')}
    </div>
  </div>

  <!-- Design Digest -->
  <div class="bg-slate-900 rounded-2xl p-6 mb-6">
    <h2 class="section-header text-xl font-semibold pb-2 mb-4 text-blue-400">Design Digest</h2>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
"""

    if design_model:
        html += f"""
      <div><span class="text-slate-400">Part:</span> <span class="font-mono">{getattr(design_model, 'part', '?')}</span></div>
      <div><span class="text-slate-400">Modules:</span> {len(getattr(design_model, 'modules', []))}</div>
      <div><span class="text-slate-400">Clocks:</span> {', '.join(getattr(design_model, 'clock_domains', [])) or 'None detected'}</div>
      <div><span class="text-slate-400">Size proxy:</span> ~{getattr(design_model, 'estimated_size_proxy', 0)}</div>
"""
    else:
        html += "<div class='text-slate-400'>No design model available.</div>"

    html += """
    </div>
  </div>

  <!-- Metrics + Planner -->
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
    <div class="bg-slate-900 rounded-2xl p-6">
      <h2 class="section-header text-xl font-semibold pb-2 mb-4 text-emerald-400">Key Metrics</h2>
      <div class="space-y-2 text-sm font-mono">
"""

    t = metrics.get("timing") or {}
    p = metrics.get("power") or {}
    if t.get("wns") is not None:
        html += f"<div>WNS: <span class='text-red-400'>{t['wns']} ns</span></div>"
    if p.get("total_w"):
        html += f"<div>Total Power: {p['total_w']} W</div>"

    html += """
      </div>
    </div>

    <div class="bg-slate-900 rounded-2xl p-6">
      <h2 class="section-header text-xl font-semibold pb-2 mb-4 text-amber-400">Planner Decision (Incremental)</h2>
"""
    if planner_decision and planner_decision.get("can_skip_synth_impl"):
        html += f"""<div class="text-emerald-400 font-medium">✓ {planner_decision.get('reason')}</div>
<div class="mt-2 text-xs bg-emerald-950 p-3 rounded">{planner_decision.get('suggested_action')}</div>"""
    else:
        html += "<div class='text-slate-400'>Full flow recommended (RTL changed or no prior success).</div>"

    html += """
    </div>
  </div>

  <!-- Recommendations -->
  <div class="bg-slate-900 rounded-2xl p-6 mb-6">
    <h2 class="section-header text-xl font-semibold pb-2 mb-4 text-violet-400">Recommendations</h2>
    <ul class="list-disc list-inside space-y-1 text-sm">
"""
    for rec in recommendations:
        html += f"<li>{rec}</li>"
    html += """
    </ul>
  </div>

  <!-- History / Trends -->
  <div class="bg-slate-900 rounded-2xl p-6">
    <h2 class="section-header text-xl font-semibold pb-2 mb-4 text-cyan-400">History & Trends</h2>
"""
    if recalls:
        for r in recalls[:4]:
            html += f"<div class='text-sm py-0.5'>• {r}</div>"
    else:
        html += "<div class='text-slate-400 text-sm'>No prior similar runs recorded yet.</div>"

    if trend_data:
        html += "<div class='mt-4 text-xs text-slate-400'>Recent similar runs WNS trend available in full JSON export.</div>"

    html += """
  </div>

  <div class="mt-8 text-[10px] text-slate-500 text-center">
    This report is fully self-contained. Re-run your flow to update.
  </div>
</div>
</body>
</html>"""
    return html


# --- Phase 2: Stimulus Intelligence (auto test case generation) ---

def generate_additional_test_cases(design_model: Any, existing_cases: List[Dict], num_extra: int = 2) -> List[Dict]:
    """
    Very lightweight stimulus generator.
    Uses port width info from the design model to create additional "interesting"
    input vectors for C-model style regression (all-0s, all-1s, walking ones, etc.).
    Returns list of dicts compatible with TEST_CASES format: {"name": , "stdin": path or None, ...}
    This is purely deterministic and helps achieve better coverage without user effort.
    """
    if not design_model or not hasattr(design_model, "modules") or not existing_cases:
        return []

    extra = []
    # Find widest input-ish ports as a proxy for data width
    max_width = 8
    for mod in getattr(design_model, "modules", []):
        for p in getattr(mod, "ports", []):
            if p.get("dir") in ("input", "inout"):
                try:
                    w = int(str(p.get("width", "1")).replace("[", "").replace("]", "").split(":")[0]) + 1
                    max_width = max(max_width, min(w, 64))
                except Exception:
                    pass

    bases = [0, (1 << max_width) - 1, 0x5555, 0xAAAA, 1]
    for i in range(min(num_extra, len(bases))):
        name = f"AUTO_{i+1}"
        # For C-model flows the "stdin" is a file with the values the C-model expects.
        # We just suggest the values; the actual file writing can be done by caller or user.
        val_a = bases[i] % (1 << (max_width // 2 or 8))
        val_b = (bases[i] >> 2) % (1 << (max_width // 2 or 8))
        extra.append({
            "name": name,
            "stdin": None,  # caller can materialize to a temp file
            "suggested_values": [val_a, val_b],
            "note": f"Auto-generated from port width ~{max_width}"
        })
    return extra
