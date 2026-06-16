################################################################################
#                                                                              #
#                      L O G I C L A N C E   S Y S T E M                       #
#                                                                              #
#  Module: FPGA Automation Tool — Run History + Case-Based Recall (Phase 1)    #
#  Author: Hemanth Kumar DM                                                    #
#                                                                              #
################################################################################

"""
Persistent history of runs + lightweight case-based reasoning / recall.

Uses only stdlib (sqlite3). Designed to feel like the tool "remembers" what
worked (and what failed) on similar designs.

- Records rich context after every flow.
- Provides human-readable advice strings based on similar past runs + simple rules.
- Stable design signatures from DesignModel make matching reliable.
"""

import os
import json
import sqlite3
import time
from datetime import datetime
from typing import List, Dict, Optional, Any


class HistoryDB:
    """Lightweight persistent history for the FPGA tool."""

    def __init__(self, db_path: Optional[str] = None, logger=None):
        self.logger = logger
        self.db_path = self._resolve_db_path(db_path)
        self._conn = None
        self._ensure_tables()

    # ------------------------------------------------------------------ #
    # Path handling (project-local preferred)
    # ------------------------------------------------------------------ #
    def _resolve_db_path(self, explicit: Optional[str]) -> str:
        if explicit:
            return os.path.abspath(explicit)
        # Project-local first (easy to gitignore, per workspace)
        local = os.path.abspath(".fpga_intel_history.db")
        try:
            os.makedirs(os.path.dirname(local) or ".", exist_ok=True)
            # Touch to make sure we can write here
            with open(local, "a"):
                pass
            return local
        except Exception:
            pass

        # Fallback next to tool or in home
        candidates = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".fpga_intel_history.db"),
            os.path.expanduser("~/.fpga_intel_history.db"),
        ]
        for c in candidates:
            try:
                d = os.path.abspath(c)
                os.makedirs(os.path.dirname(d) or ".", exist_ok=True)
                return d
            except Exception:
                continue
        # Last resort: in-memory (loses data between invocations but never crashes)
        if self.logger:
            self.logger.warn("HistoryDB: using in-memory DB (no persistence across runs)")
        return ":memory:"

    # ------------------------------------------------------------------ #
    # Schema
    # ------------------------------------------------------------------ #
    def _get_conn(self):
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, timeout=5)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _ensure_tables(self):
        try:
            conn = self._get_conn()
            conn.execute("""
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    flow TEXT,
                    design_signature TEXT,
                    part TEXT,
                    status TEXT,
                    exit_code INTEGER,
                    duration_sec REAL,
                    config_json TEXT,
                    model_json TEXT,
                    metrics_json TEXT,
                    notes TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    run_id TEXT,
                    metric_name TEXT,
                    value REAL,
                    unit TEXT,
                    FOREIGN KEY(run_id) REFERENCES runs(id)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_sig ON runs(design_signature)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_part ON runs(part)")
            conn.commit()
        except Exception as e:
            if self.logger:
                self.logger.warn(f"HistoryDB schema setup warning: {e}")

    # ------------------------------------------------------------------ #
    # Record
    # ------------------------------------------------------------------ #
    def record_run(self,
                   run_id: str,
                   flow: str,
                   design_model: Any = None,
                   metrics: Dict = None,
                   status: str = "unknown",
                   exit_code: int = 0,
                   output_dir: str = "",
                   config_summary: Dict = None,
                   duration_sec: float = 0.0):
        """Store a completed (or attempted) run with rich context."""
        if not run_id:
            return
        now = datetime.utcnow().isoformat()
        sig = ""
        part = ""
        model_json = "{}"
        if design_model is not None:
            try:
                if hasattr(design_model, "signature"):
                    sig = design_model.signature
                if hasattr(design_model, "part"):
                    part = design_model.part or ""
                if hasattr(design_model, "to_dict"):
                    model_json = json.dumps(design_model.to_dict(), default=str)
                elif isinstance(design_model, dict):
                    model_json = json.dumps(design_model, default=str)
            except Exception:
                pass

        metrics_json = "{}"
        if metrics:
            try:
                metrics_json = json.dumps(metrics, default=str)
            except Exception:
                pass

        config_json = "{}"
        if config_summary:
            try:
                config_json = json.dumps(config_summary, default=str)
            except Exception:
                pass

        try:
            conn = self._get_conn()
            conn.execute("""
                INSERT OR REPLACE INTO runs
                (id, timestamp, flow, design_signature, part, status, exit_code,
                 duration_sec, config_json, model_json, metrics_json, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (run_id, now, flow, sig, part, status, exit_code,
                  duration_sec, config_json, model_json, metrics_json, output_dir))
            # Denormalized metrics for easy querying
            conn.execute("DELETE FROM metrics WHERE run_id = ?", (run_id,))
            flat = self._flatten_metrics(metrics or {})
            for name, val in flat.items():
                try:
                    conn.execute("INSERT INTO metrics (run_id, metric_name, value, unit) VALUES (?,?,?,?)",
                                 (run_id, name, float(val), ""))
                except Exception:
                    pass
            conn.commit()
            if self.logger:
                self.logger.debug(f"History: recorded run {run_id} (sig {sig[:8] if sig else 'n/a'})")
        except Exception as e:
            if self.logger:
                self.logger.warn(f"HistoryDB record failed (non-fatal): {e}")

    def _flatten_metrics(self, m: dict) -> dict:
        out = {}
        if not isinstance(m, dict):
            return out
        # Pull common interesting leaves
        for k in ("wns", "tns", "total_w", "dynamic_w", "bufg_used", "no_clock"):
            if k in m and m[k] is not None:
                out[k] = m[k]
        t = m.get("timing") or {}
        for k in ("wns", "tns"):
            if t.get(k) is not None:
                out[k] = t[k]
        p = m.get("power") or {}
        for k in ("total_w", "dynamic_w"):
            if p.get(k) is not None:
                out[k] = p[k]
        meth = m.get("methodology") or {}
        if meth.get("no_clock"):
            out["no_clock"] = meth["no_clock"]
        return out

    # ------------------------------------------------------------------ #
    # Recall & Advice (the "AI-like" memory)
    # ------------------------------------------------------------------ #
    def recall_advice(self, design_model: Any = None, current_metrics: Dict = None,
                      flow: str = None) -> List[str]:
        """Return a list of human-readable insight strings."""
        advice = []
        if design_model is None:
            return advice

        sig = getattr(design_model, "signature", "") or ""
        part = getattr(design_model, "part", "") or ""

        similar = self.find_similar_runs(sig, part, limit=4)
        if similar:
            best = similar[0]
            ts = best.get("timestamp", "")[:16].replace("T", " ")
            wns = "?"
            try:
                mj = json.loads(best.get("metrics_json") or "{}")
                if isinstance(mj, dict):
                    wns = mj.get("wns") or (mj.get("timing") or {}).get("wns") or "?"
            except Exception:
                pass
            advice.append(f"Recall: similar design last run on {ts} (WNS ~{wns}).")

            # Very simple trend hint
            if len(similar) >= 2:
                advice.append(f"{len(similar)} similar runs found in history — pattern data available.")

        # Lightweight rule-based memory (works even on first run)
        if current_metrics:
            meth = current_metrics.get("methodology") or {}
            if meth.get("no_clock", 0) > 8:
                advice.append(f"History note: designs with {meth['no_clock']} no_clock issues usually require explicit XDC clock + I/O constraints before timing closure.")
            pw = current_metrics.get("power") or {}
            if pw.get("warnings"):
                advice.append("Power warning seen in past similar runs — watch junction temperature on long impl runs.")

        return advice

    def find_similar_runs(self, signature: str, part: str = None, limit: int = 5) -> List[Dict]:
        if not signature:
            return []
        try:
            conn = self._get_conn()
            if part:
                rows = conn.execute(
                    "SELECT * FROM runs WHERE design_signature = ? OR (part = ? AND design_signature != '') "
                    "ORDER BY timestamp DESC LIMIT ?",
                    (signature, part, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM runs WHERE design_signature = ? ORDER BY timestamp DESC LIMIT ?",
                    (signature, limit)
                ).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []

    def get_last_successful_for_sig(self, signature: str):
        try:
            conn = self._get_conn()
            row = conn.execute(
                "SELECT * FROM runs WHERE design_signature = ? AND exit_code = 0 "
                "ORDER BY timestamp DESC LIMIT 1", (signature,)
            ).fetchone()
            return dict(row) if row else None
        except Exception:
            return None

    # --- Phase 2 enhancements: trends & analytics ---
    def get_trend_data(self, signature: str, metric: str = "wns", limit: int = 8) -> List[Dict]:
        """Return recent values for a metric across similar runs (for trend views)."""
        try:
            conn = self._get_conn()
            rows = conn.execute("""
                SELECT r.timestamp, m.value
                FROM runs r JOIN metrics m ON r.id = m.run_id
                WHERE r.design_signature = ? AND m.metric_name = ?
                ORDER BY r.timestamp DESC LIMIT ?
            """, (signature, metric, limit)).fetchall()
            return [{"ts": r[0], "value": r[1]} for r in rows]
        except Exception:
            return []

    def get_closure_trend(self, signature: str) -> dict:
        data = self.get_trend_data(signature, "wns", 6)
        if not data:
            return {}
        vals = [d["value"] for d in data if d["value"] is not None]
        if not vals:
            return {}
        return {
            "count": len(vals),
            "latest": vals[0],
            "avg_last_3": sum(vals[:3]) / min(3, len(vals)),
            "improving": vals[0] > vals[-1] if len(vals) > 1 else None,
        }

    def close(self):
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None
