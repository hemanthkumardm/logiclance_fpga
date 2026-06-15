#!/usr/bin/env python3
################################################################################
#                                                                              #
#                      L O G I C L A N C E   S Y S T E M                       #
#                                                                              #
#  Module: FPGA Automation Tool — GUI Entry Point                              #
#  Author: Hemanth Kumar DM                                                    #
#                                                                              #
################################################################################

import os
import sys
import json
import threading
import subprocess
from datetime import datetime
import re

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QComboBox, QPushButton, 
                             QLineEdit, QFileDialog, QGroupBox, QFormLayout,
                             QScrollArea, QCheckBox, QSpinBox, QTextEdit, 
                             QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QTimer
from PyQt5.QtGui import QFont, QColor, QTextCursor

# Ensure package is importable
_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)

from fpga_tool.flow_utils import SimLogger, SmartInput, CommandManager, find_vivado
from fpga_tool.run_fpga_xilinx import (
    run_xilinx_sim,
    run_xilinx_cmod_sim,
    run_xilinx_regression,
    run_xilinx_full_flow,
)

# ──────────────────── Qt Signal Emitter for Thread-Safe Logging ────────────────────

class LogEmitter(QObject):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def write(self, text):
        self.log_signal.emit(text)

    def flush(self):
        pass

# ──────────────────── GUI Application ────────────────────

class FPGAGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LogicLance — FPGA Automation Tool")
        self.resize(1000, 800)
        self.setup_light_theme()
        
        self.cmd_mgr = CommandManager(_script_dir, SimLogger(verbose=False))
        
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)
        
        self.setup_top_bar()
        self.setup_scroll_area()
        self.setup_log_area()
        
        self.flow_combo.currentIndexChanged.connect(self.update_visibility)
        self.update_visibility()

    def setup_light_theme(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #f8fafc; }
            QWidget { font-family: 'Segoe UI', Inter, sans-serif; font-size: 10pt; color: #1e293b; }
            QGroupBox { font-weight: bold; border: 1px solid #cbd5e1; border-radius: 6px; margin-top: 12px; padding-top: 10px; background-color: #ffffff; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; color: #334155; }
            QLineEdit { border: 1px solid #cbd5e1; border-radius: 4px; padding: 5px; background-color: #ffffff; }
            QLineEdit:focus { border: 1px solid #3b82f6; }
            QComboBox { border: 1px solid #cbd5e1; border-radius: 4px; padding: 5px; background-color: #ffffff; }
            QPushButton { background-color: #3b82f6; color: white; border: none; border-radius: 4px; padding: 6px 12px; font-weight: bold; }
            QPushButton:hover { background-color: #2563eb; }
            QPushButton#browse_btn { background-color: #e2e8f0; color: #1e293b; font-weight: normal; }
            QPushButton#browse_btn:hover { background-color: #cbd5e1; }
            QTextEdit { background-color: #1e293b; color: #f8fafc; font-family: monospace; border-radius: 4px; }
            QTableWidget { border: 1px solid #cbd5e1; border-radius: 4px; gridline-color: #e2e8f0; }
            QHeaderView::section { background-color: #f1f5f9; padding: 4px; border: 1px solid #e2e8f0; font-weight: bold; }
        """)

    def create_browse_field(self, layout, label_text, is_dir=False, default=""):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        
        line_edit = QLineEdit()
        line_edit.setText(default)
        browse_btn = QPushButton("Browse...")
        browse_btn.setObjectName("browse_btn")
        
        def do_browse():
            if is_dir:
                path = QFileDialog.getExistingDirectory(self, "Select Directory", line_edit.text() or os.getcwd())
            else:
                path, _ = QFileDialog.getOpenFileName(self, "Select File", line_edit.text() or os.getcwd())
            if path:
                line_edit.setText(path)
                
        browse_btn.clicked.connect(do_browse)
        
        row_layout.addWidget(line_edit)
        row_layout.addWidget(browse_btn)
        
        layout.addRow(label_text, row_widget)
        return line_edit

    def setup_top_bar(self):
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("<b>Select Flow:</b>"))
        
        self.flow_combo = QComboBox()
        self.flow_combo.addItems([
            "Post-Implementation Simulation",
            "C-Model + Simulation",
            "Multi-Test Regression",
            "Full Flow (Synth → Impl → Test → XSA)"
        ])
        top_bar.addWidget(self.flow_combo)
        top_bar.addStretch()
        
        load_btn = QPushButton("Load Last Run Config")
        load_btn.setObjectName("browse_btn")
        load_btn.clicked.connect(self.load_last_run)
        top_bar.addWidget(load_btn)
        
        clear_btn = QPushButton("Clear Log")
        clear_btn.setObjectName("browse_btn")
        clear_btn.clicked.connect(self.clear_log)
        top_bar.addWidget(clear_btn)
        
        self.run_btn = QPushButton("▶ Run Selected Flow")
        self.run_btn.setStyleSheet("background-color: #10b981;")
        self.run_btn.clicked.connect(self.start_flow)
        top_bar.addWidget(self.run_btn)
        
        self.main_layout.addLayout(top_bar)

    def setup_scroll_area(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        self.form_layout = QVBoxLayout(content)
        
        # ── PROJECT GROUP ──
        self.grp_proj = QGroupBox("Project Configuration")
        l_proj = QFormLayout(self.grp_proj)
        self.f_proj_mode = QComboBox()
        self.f_proj_mode.addItems(["Open existing .xpr", "Create new project"])
        self.f_proj_mode.currentIndexChanged.connect(self.update_visibility)
        l_proj.addRow("Project Mode:", self.f_proj_mode)
        
        self.f_project_xpr = self.create_browse_field(l_proj, "Vivado project path (.xpr):")
        
        # Create new project fields
        self.f_fpga_part = QComboBox()
        self.f_fpga_part.setEditable(True)
        self.f_fpga_part.addItems([
            "",
            "xczu7ev-ffvc1156-2-e",     # Zynq UltraScale+ ZCU106
            "xczu9eg-ffvb1156-2-e",     # Zynq UltraScale+ ZCU102
            "xczu7ev-ffvc1156-2-i",     # Zynq UltraScale+
            "xc7z020clg400-1",          # Zynq-7000 (Zybo / PYNQ-Z1)
            "xc7a100tcsg324-1",         # Artix-7 (Arty A7-100)
            "xcku040-ffva1156-2-e",     # Kintex UltraScale
            "xcvu9p-flga2104-2L-e"      # Virtex UltraScale+
        ])
        l_proj.addRow("FPGA part:", self.f_fpga_part)
        
        self.f_board_part = QComboBox()
        self.f_board_part.setEditable(True)
        self.f_board_part.addItems([
            "",
            "xilinx.com:zcu106:part0:2.6",
            "xilinx.com:zcu104:part0:1.1",
            "xilinx.com:zcu102:part0:3.4",
            "xilinx.com:zc702:part0:1.4",
            "digilentinc.com:arty-a7-100:part0:1.1",
            "digilentinc.com:zybo-z7-20:part0:1.1"
        ])
        l_proj.addRow("Board part (optional):", self.f_board_part)
        self.f_project_name = QLineEdit("fpga_project")
        l_proj.addRow("Project name:", self.f_project_name)
        self.f_project_dir = self.create_browse_field(l_proj, "Project directory:", is_dir=True, default="./fpga_project")
        self.f_source_files = self.create_browse_field(l_proj, "Source HDL files/dirs (space-sep):", is_dir=True)
        self.f_ip_repo = self.create_browse_field(l_proj, "IP repo paths (space-sep):", is_dir=True)
        self.f_bd_tcl = self.create_browse_field(l_proj, "Block design Tcl script (optional):")
        self.form_layout.addWidget(self.grp_proj)

        # ── TESTBENCH GROUP ──
        self.grp_tb = QGroupBox("Testbench Configuration")
        l_tb = QFormLayout(self.grp_tb)
        self.f_tb_top = QLineEdit()
        l_tb.addRow("Testbench top module name:", self.f_tb_top)
        
        self.f_tb_mode = QComboBox()
        self.f_tb_mode.addItems(["File list", "Auto-discover from directory"])
        self.f_tb_mode.currentIndexChanged.connect(self.update_visibility)
        l_tb.addRow("Testbench source:", self.f_tb_mode)
        
        self.f_tb_files = self.create_browse_field(l_tb, "Testbench file(s) (space-sep):")
        self.f_tb_dir = self.create_browse_field(l_tb, "Testbench directory:", is_dir=True)
        
        self.f_tb_includes = QLineEdit()
        l_tb.addRow("Include directories (space-sep):", self.f_tb_includes)
        self.f_tb_defines = QLineEdit("SIM=1")
        l_tb.addRow("Verilog defines (space-sep):", self.f_tb_defines)
        
        self.f_sim_mode = QComboBox()
        self.f_sim_mode.addItems(["post-implementation", "post-synthesis"])
        l_tb.addRow("Simulation mode:", self.f_sim_mode)
        self.f_sim_type = QComboBox()
        self.f_sim_type.addItems(["functional", "timing"])
        l_tb.addRow("Simulation type:", self.f_sim_type)
        self.form_layout.addWidget(self.grp_tb)

        # ── C-MODEL GROUP ──
        self.grp_cmod = QGroupBox("C-Model Configuration")
        l_cmod = QFormLayout(self.grp_cmod)
        self.f_cmod_dir = self.create_browse_field(l_cmod, "C-model directory (has Makefile):", is_dir=True)
        self.f_cmod_stdin = self.create_browse_field(l_cmod, "C-model stdin input file:")
        self.f_cmod_stdout = self.create_browse_field(l_cmod, "C-model stdout capture file:")
        self.f_cmod_clean = QLineEdit("clean")
        l_cmod.addRow("Make clean target:", self.f_cmod_clean)
        self.f_cmod_run = QLineEdit("manual")
        l_cmod.addRow("Make run target:", self.f_cmod_run)
        self.f_cmod_build = QLineEdit()
        l_cmod.addRow("Make build targets (space-sep):", self.f_cmod_build)
        self.f_cmod_timeout = QSpinBox()
        self.f_cmod_timeout.setMaximum(99999)
        self.f_cmod_timeout.setValue(900)
        l_cmod.addRow("Timeout (seconds):", self.f_cmod_timeout)
        self.f_cmod_log = QLineEdit("./output/cmodel_run.log")
        l_cmod.addRow("C-model log file:", self.f_cmod_log)
        self.form_layout.addWidget(self.grp_cmod)

        # ── REGRESSION GROUP ──
        self.grp_reg = QGroupBox("Regression Configuration")
        l_reg = QFormLayout(self.grp_reg)
        self.f_res_file = self.create_browse_field(l_reg, "Result file path (TB writes PASS/FAIL):")
        self.f_pass_pat = QLineEdit("TEST_PASSED")
        l_reg.addRow("Pass pattern:", self.f_pass_pat)
        self.f_fail_pat = QLineEdit("TEST_FAILED")
        l_reg.addRow("Fail pattern:", self.f_fail_pat)
        self.f_cmod_out_fixed = QLineEdit()
        l_reg.addRow("Fixed C-model output path (TB reads this):", self.f_cmod_out_fixed)
        self.f_cmod_log_dir = QLineEdit("./output/cmodel_logs")
        l_reg.addRow("C-model log directory:", self.f_cmod_log_dir)
        self.f_sim_log_dir = QLineEdit("./output/sim_logs")
        l_reg.addRow("Simulation log directory:", self.f_sim_log_dir)
        
        # Test Cases Table
        self.tc_table = QTableWidget(0, 3)
        self.tc_table.setHorizontalHeaderLabels(["Test Case Name", "Stdin File", "Stdout File"])
        self.tc_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tc_table.setMinimumHeight(150)
        btn_add_tc = QPushButton("+ Add Test Case")
        btn_add_tc.setObjectName("browse_btn")
        btn_add_tc.clicked.connect(self.add_tc_row)
        
        l_reg.addRow(btn_add_tc)
        l_reg.addRow(self.tc_table)
        self.form_layout.addWidget(self.grp_reg)

        # ── FULL FLOW OUTPUT GROUP ──
        self.grp_full = QGroupBox("Full Flow Output & Options")
        l_full = QFormLayout(self.grp_full)
        self.f_out_bit = QLineEdit("./output/design.bit")
        l_full.addRow("Output bitstream path (.bit):", self.f_out_bit)
        self.f_out_xsa = QLineEdit("./output/design.xsa")
        l_full.addRow("Output XSA path (.xsa):", self.f_out_xsa)
        self.f_synth_jobs = QSpinBox()
        self.f_synth_jobs.setMinimum(1)
        self.f_synth_jobs.setValue(4)
        l_full.addRow("Synthesis parallel jobs:", self.f_synth_jobs)
        self.f_impl_jobs = QSpinBox()
        self.f_impl_jobs.setMinimum(1)
        self.f_impl_jobs.setValue(8)
        l_full.addRow("Implementation parallel jobs:", self.f_impl_jobs)
        
        self.f_run_tests = QCheckBox("Run post-implementation regression tests?")
        self.f_run_tests.setChecked(True)
        self.f_run_tests.stateChanged.connect(self.update_visibility)
        l_full.addRow("", self.f_run_tests)
        self.form_layout.addWidget(self.grp_full)
        
        self.form_layout.addStretch()
        scroll.setWidget(content)
        self.main_layout.addWidget(scroll, stretch=2)

    def setup_log_area(self):
        log_grp = QGroupBox("Live Console Output")
        log_layout = QVBoxLayout(log_grp)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Courier New", 10))
        log_layout.addWidget(self.log_text)
        self.main_layout.addWidget(log_grp, stretch=1)
        
        # Setup stdout redirection
        self.emitter = LogEmitter()
        self.emitter.log_signal.connect(self.append_log)
        self.emitter.finished_signal.connect(lambda: self.run_btn.setEnabled(True))
        
        class StreamRedirect:
            def __init__(self, emitter):
                self.emitter = emitter
            def write(self, text):
                self.emitter.write(text)
            def flush(self):
                pass
                
        self.original_stdout = sys.stdout
        sys.stdout = StreamRedirect(self.emitter)

    def append_log(self, text):
        html = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        html = html.replace('\n', '<br>')
        
        # Standard colors
        html = re.sub(r'\x1b\[31m', '<span style="color:#ef4444;">', html)
        html = re.sub(r'\x1b\[32m', '<span style="color:#22c55e;">', html)
        html = re.sub(r'\x1b\[33m', '<span style="color:#eab308;">', html)
        html = re.sub(r'\x1b\[34m', '<span style="color:#3b82f6;">', html)
        html = re.sub(r'\x1b\[35m', '<span style="color:#d946ef;">', html)
        html = re.sub(r'\x1b\[36m', '<span style="color:#06b6d4;">', html)
        
        # Bold colors
        html = re.sub(r'\x1b\[1;31m', '<span style="color:#ef4444; font-weight:bold;">', html)
        html = re.sub(r'\x1b\[1;32m', '<span style="color:#22c55e; font-weight:bold;">', html)
        html = re.sub(r'\x1b\[1;33m', '<span style="color:#eab308; font-weight:bold;">', html)
        html = re.sub(r'\x1b\[1;34m', '<span style="color:#3b82f6; font-weight:bold;">', html)
        html = re.sub(r'\x1b\[1;35m', '<span style="color:#d946ef; font-weight:bold;">', html)
        html = re.sub(r'\x1b\[1;36m', '<span style="color:#06b6d4; font-weight:bold;">', html)
        
        # Dim / White / Default
        html = re.sub(r'\x1b\[2m', '<span style="color:#9ca3af;">', html)
        html = re.sub(r'\x1b\[37m', '<span style="color:#374151;">', html)
        html = re.sub(r'\x1b\[2;37m', '<span style="color:#9ca3af;">', html)
        html = re.sub(r'\x1b\[2;39m', '<span style="color:#9ca3af;">', html)
        html = re.sub(r'\x1b\[39m', '<span style="color:#111827;">', html)
        html = re.sub(r'\x1b\[96m', '<span style="color:#0891b2;">', html) # bright cyan -> darker cyan
        html = re.sub(r'\x1b\[92m', '<span style="color:#16a34a;">', html) # bright green -> darker green
        html = re.sub(r'\x1b\[91m', '<span style="color:#dc2626;">', html) # bright red -> darker red
        html = re.sub(r'\x1b\[93m', '<span style="color:#ca8a04;">', html) # bright yellow -> darker yellow
        
        # Reset
        html = re.sub(r'\x1b\[0m', '</span>', html)
        
        # Strip any remaining ANSI escape codes
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        html = ansi_escape.sub('', html)
        
        self.log_text.moveCursor(QTextCursor.End)
        self.log_text.insertHtml(html)
        self.log_text.moveCursor(QTextCursor.End)

    def clear_log(self):
        self.log_text.clear()
        self.run_btn.setEnabled(True)

    def add_tc_row(self, name="", stdin="", stdout=""):
        row = self.tc_table.rowCount()
        self.tc_table.insertRow(row)
        self.tc_table.setItem(row, 0, QTableWidgetItem(name))
        self.tc_table.setItem(row, 1, QTableWidgetItem(stdin))
        self.tc_table.setItem(row, 2, QTableWidgetItem(stdout))

    def set_row_visible(self, field, layout, visible):
        if field.parentWidget() != layout.parentWidget():
            # It's a browse field row (wrapped in a QWidget)
            row_widget = field.parentWidget()
            row_widget.setVisible(visible)
            label = layout.labelForField(row_widget)
            if label:
                label.setVisible(visible)
        else:
            field.setVisible(visible)
            label = layout.labelForField(field)
            if label:
                label.setVisible(visible)

    def update_visibility(self):
        flow_idx = self.flow_combo.currentIndex()
        # 0: Sim, 1: Cmod, 2: Reg, 3: Full
        
        # Project visibility
        is_full = (flow_idx == 3)
        is_create = is_full and self.f_proj_mode.currentIndex() == 1
        
        l_proj = self.grp_proj.layout()
        self.set_row_visible(self.f_proj_mode, l_proj, is_full)
        self.set_row_visible(self.f_project_xpr, l_proj, not is_create)
        self.set_row_visible(self.f_fpga_part, l_proj, is_create)
        self.set_row_visible(self.f_board_part, l_proj, is_create)
        self.set_row_visible(self.f_project_name, l_proj, is_create)
        self.set_row_visible(self.f_project_dir, l_proj, is_create)
        self.set_row_visible(self.f_source_files, l_proj, is_create)
        self.set_row_visible(self.f_ip_repo, l_proj, is_create)
        self.set_row_visible(self.f_bd_tcl, l_proj, is_create)

        # Full Flow output group
        self.grp_full.setVisible(is_full)

        # Testbench visibility
        needs_tb = (flow_idx in [0, 1, 2]) or (is_full and self.f_run_tests.isChecked())
        self.grp_tb.setVisible(needs_tb)
        
        tb_mode_dir = self.f_tb_mode.currentIndex() == 1
        l_tb = self.grp_tb.layout()
        self.set_row_visible(self.f_tb_files, l_tb, not tb_mode_dir)
        self.set_row_visible(self.f_tb_dir, l_tb, tb_mode_dir)
        
        # C-Model visibility
        needs_cmod = (flow_idx in [1, 2]) or (is_full and self.f_run_tests.isChecked())
        self.grp_cmod.setVisible(needs_cmod)
        l_cmod = self.grp_cmod.layout()
        self.set_row_visible(self.f_cmod_stdin, l_cmod, flow_idx == 1) # only simple cmod needs direct stdin
        
        # Regression visibility
        needs_reg = (flow_idx == 2) or (is_full and self.f_run_tests.isChecked())
        self.grp_reg.setVisible(needs_reg)

    def build_gui_inputs(self):
        # Gather all inputs into a dictionary matching SmartInput keys
        flow_idx = self.flow_combo.currentIndex()
        inputs = {}
        
        # Project
        if flow_idx == 3:
            inputs["project_mode"] = str(self.f_proj_mode.currentIndex() + 1)
            inputs["project_xpr"] = self.f_project_xpr.text()
            inputs["fpga_part"] = self.f_fpga_part.currentText()
            inputs["board_part"] = self.f_board_part.currentText()
            inputs["project_name"] = self.f_project_name.text()
            inputs["project_dir"] = self.f_project_dir.text()
            inputs["source_files"] = self.f_source_files.text()
            inputs["ip_repo_paths"] = self.f_ip_repo.text()
            inputs["bd_tcl_script"] = self.f_bd_tcl.text()
            inputs["git_enable"] = "n"
            inputs["output_bit"] = self.f_out_bit.text()
            inputs["output_xsa"] = self.f_out_xsa.text()
            inputs["synth_jobs"] = str(self.f_synth_jobs.value())
            inputs["impl_jobs"] = str(self.f_impl_jobs.value())
            inputs["run_tests"] = "y" if self.f_run_tests.isChecked() else "n"
        else:
            inputs["project_xpr"] = self.f_project_xpr.text()
            
        # Testbench
        inputs["tb_top"] = self.f_tb_top.text()
        inputs["tb_mode"] = str(self.f_tb_mode.currentIndex() + 1)
        inputs["tb_files"] = self.f_tb_files.text()
        inputs["tb_dir"] = self.f_tb_dir.text()
        inputs["tb_includes"] = self.f_tb_includes.text()
        inputs["tb_defines"] = self.f_tb_defines.text()
        inputs["sim_mode"] = self.f_sim_mode.currentText()
        inputs["sim_type"] = self.f_sim_type.currentText()
        
        # C-Model
        inputs["cmodel_dir"] = self.f_cmod_dir.text()
        inputs["cmodel_stdin"] = self.f_cmod_stdin.text()
        inputs["cmodel_stdout"] = self.f_cmod_stdout.text()
        inputs["cmodel_clean_target"] = self.f_cmod_clean.text()
        inputs["cmodel_run_target"] = self.f_cmod_run.text()
        inputs["cmodel_build_targets"] = self.f_cmod_build.text()
        inputs["cmodel_timeout"] = str(self.f_cmod_timeout.value())
        inputs["cmodel_log"] = self.f_cmod_log.text()
        
        # Regression
        inputs["result_file"] = self.f_res_file.text()
        inputs["pass_pattern"] = self.f_pass_pat.text()
        inputs["fail_pattern"] = self.f_fail_pat.text()
        inputs["cmodel_out_fixed"] = self.f_cmod_out_fixed.text()
        inputs["cmodel_log_dir"] = self.f_cmod_log_dir.text()
        inputs["sim_log_dir"] = self.f_sim_log_dir.text()
        
        test_cases = []
        for i in range(self.tc_table.rowCount()):
            name = self.tc_table.item(i, 0).text() if self.tc_table.item(i, 0) else ""
            stdin = self.tc_table.item(i, 1).text() if self.tc_table.item(i, 1) else ""
            stdout = self.tc_table.item(i, 2).text() if self.tc_table.item(i, 2) else ""
            if name:
                test_cases.append({"name": name, "stdin": stdin, "stdout": stdout})
        
        # We need to simulate the user hitting enter on empty test case to end
        inputs["test_cases"] = test_cases
        
        # Bypass confirmation prompts in GUI
        inputs["_confirm"] = "y"
        
        return inputs

    def load_last_run(self):
        last_run = self.cmd_mgr.load_last_command()
        if not last_run:
            QMessageBox.warning(self, "Load Failed", "No previous run state found.")
            return
            
        flow_key = last_run.get('command')
        gui_map = {"sim": 0, "cmod": 1, "regression": 2, "full": 3}
        if flow_key in gui_map:
            self.flow_combo.setCurrentIndex(gui_map[flow_key])
            
        inputs = last_run.get('context', {}).get('inputs', {})
        
        def set_val(field, key, default=""):
            if isinstance(field, QLineEdit):
                field.setText(str(inputs.get(key, default)))
            elif isinstance(field, QComboBox):
                if field.isEditable():
                    field.setCurrentText(str(inputs.get(key, default)))
                else:
                    val = inputs.get(key)
                    if val and val.isdigit():
                        field.setCurrentIndex(int(val)-1)
            elif isinstance(field, QSpinBox):
                val = inputs.get(key)
                if val and val.isdigit():
                    field.setValue(int(val))
                    
        set_val(self.f_project_xpr, "project_xpr")
        set_val(self.f_fpga_part, "fpga_part")
        set_val(self.f_board_part, "board_part")
        set_val(self.f_tb_top, "tb_top")
        set_val(self.f_tb_mode, "tb_mode")
        set_val(self.f_tb_files, "tb_files")
        set_val(self.f_tb_dir, "tb_dir")
        set_val(self.f_tb_includes, "tb_includes")
        set_val(self.f_tb_defines, "tb_defines")
        
        set_val(self.f_cmod_dir, "cmodel_dir")
        set_val(self.f_cmod_stdin, "cmodel_stdin")
        set_val(self.f_cmod_stdout, "cmodel_stdout")
        set_val(self.f_cmod_clean, "cmodel_clean_target")
        set_val(self.f_cmod_run, "cmodel_run_target")
        set_val(self.f_cmod_build, "cmodel_build_targets")
        set_val(self.f_cmod_timeout, "cmodel_timeout", 900)
        set_val(self.f_cmod_log, "cmodel_log")
        
        set_val(self.f_res_file, "result_file")
        set_val(self.f_pass_pat, "pass_pattern")
        set_val(self.f_fail_pat, "fail_pattern")
        set_val(self.f_cmod_out_fixed, "cmodel_out_fixed")
        set_val(self.f_cmod_log_dir, "cmodel_log_dir")
        set_val(self.f_sim_log_dir, "sim_log_dir")
        
        # Load test cases
        tcs = inputs.get("test_cases", [])
        if isinstance(tcs, list):
            self.tc_table.setRowCount(0)
            for tc in tcs:
                if isinstance(tc, dict):
                    self.add_tc_row(tc.get("name", ""), tc.get("stdin", ""), tc.get("stdout", ""))

        QMessageBox.information(self, "Loaded", "Last run configuration loaded successfully.")

    def start_flow(self):
        if not find_vivado():
            reply = QMessageBox.warning(self, "Vivado Not Found", 
                "Vivado was not found in PATH or $XILINX_VIVADO.\n\nSimulation will fail if not run in a valid environment.\nProceed anyway?",
                QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return

        self.run_btn.setEnabled(False)
        self.log_text.clear()
        
        inputs = self.build_gui_inputs()
        flow_idx = self.flow_combo.currentIndex()
        
        flow_key = ["sim", "cmod", "regression", "full"][flow_idx]
        
        # Save context so CLI rerun works
        context = {
            "vendor": "xilinx",
            "flow": flow_key,
            "inputs": inputs,
        }
        self.cmd_mgr.save_last_command(flow_key, context)
        
        # Run in thread
        threading.Thread(target=self._run_thread, args=(flow_idx, inputs), daemon=True).start()

    def _run_thread(self, flow_idx, inputs):
        logger = SimLogger(verbose=False)
        # Override logger to prevent sys.exit(1) on halt
        def safe_halt(msg):
            print(f"HALT: {msg}")
            raise Exception(msg)
        logger.halt = safe_halt
        
        smart_in = SmartInput(logger, flow_type='rerun', rerun_data={'context': {'inputs': inputs}})
        run_id = f"fpga_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            if flow_idx == 0:
                rc = run_xilinx_sim(logger, smart_in, run_id)
            elif flow_idx == 1:
                rc = run_xilinx_cmod_sim(logger, smart_in, run_id)
            elif flow_idx == 2:
                rc = run_xilinx_regression(logger, smart_in, run_id)
            elif flow_idx == 3:
                rc = run_xilinx_full_flow(logger, smart_in, run_id)
            
            if rc == 0:
                print("\n✅ FLOW COMPLETED SUCCESSFULLY")
            else:
                print(f"\n❌ FLOW FAILED WITH CODE {rc}")
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            
        # Re-enable button safely through the main thread
        self.emitter.finished_signal.emit()

    def closeEvent(self, event):
        sys.stdout = self.original_stdout
        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = FPGAGUI()
    gui.show()
    sys.exit(app.exec_())
