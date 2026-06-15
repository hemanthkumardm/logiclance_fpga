# =================================================================
# C-model: make clean -> make manual (stdin from file)
# then Vivado Post-Implementation Functional Simulation (force TB)
# Vivado 2024.1 — headless
# =================================================================

# ---------------- USER CONFIG: C-MODEL ----------------
# Directory that contains your Makefile for the C-model
set CMODEL_DIR     "/mnt/newvolume/darshan/VIVAD_2024.1/Interrupt_debug/cmod/cmodel_exsleratev2/systemc-perf-model"

# Input answers file (one value per line in the order your model prompts)
# Example contents:
# 32
# 32
# 32
# 3
# 3
# 32
# 2
# 2
# 0
# 0
# 0
# 0
set CMODEL_STDIN   "/mnt/newvolume/darshan/VIVAD_2024.1/Test_proj/cmod_in.txt"

# Optional: capture C-model stdout to a file (leave empty to only log)
set CMODEL_STDOUT  "/mnt/newvolume/darshan/cmodel/out_golden.txt"

# Log file for C-model build/run
set CMODEL_LOG     "/mnt/newvolume/darshan/cmodel/cmodel_run.log"

# Kill C-model steps if they exceed this many seconds (0 = no timeout)
set TIMEOUT_SEC    900   ;# 15 minutes

# ---------------- USER CONFIG: VIVADO SIM ----------------
set XPR            "/mnt/newvolume/darshan/VIVAD_2024.1/Test_proj/Test_proj/Test_proj.xpr"
set TB_TOP         "AcceleratorWrapperTB"
set TB_FILES       [list \
  "/mnt/newvolume/darshan/VIVAD_2024.1/Test_proj/BehavioralTB.sv" \
]
set TB_INCLUDE_DIRS [list]
set TB_DEFINES       [list SIM=1]
# If TB needs the C-model output path, pass it as a define:
# lappend TB_DEFINES CMODEL_OUT=\"/mnt/newvolume/darshan/cmodel/out_golden.txt\"

# ---------------- HELPERS ----------------
proc die {msg} { puts stderr "ERROR: $msg"; exit 1 }
proc nrm {p}  { return [file normalize $p] }

# Run a shell command from Tcl, with optional stdin file, stdout capture, timeout, and logging.
proc sh_run {cmd workdir logfile stdin_file stdout_file timeout_s} {
  if {![file isdirectory $workdir]} { die "Directory not found: $workdir" }
  set workdir   [nrm $workdir]
  set logfile   [nrm $logfile]
  set logdir    [file dirname $logfile]
  if {![file isdirectory $logdir]} { file mkdir $logdir }

  set wrap "cd [list $workdir] && "
  if {$timeout_s > 0} { append wrap "timeout --preserve-status ${timeout_s}s " }
  # stdbuf helps flush lines quickly into the log; harmless if absent
  append wrap "stdbuf -oL -eL $cmd"

  # stdin
  if {[string length [string trim $stdin_file]]} {
    set stdin_file [nrm $stdin_file]
    if {![file exists $stdin_file]} { die "Stdin file not found: $stdin_file" }
    append wrap " < [list $stdin_file]"
  }

  # stdout capture or tee to log
  if {[string length [string trim $stdout_file]]} {
    set stdout_file [nrm $stdout_file]
    set outdir [file dirname $stdout_file]
    if {![file isdirectory $outdir]} { file mkdir $outdir }
    append wrap " > [list $stdout_file] 2>&1"
    set postcopy " && { echo '\n==== APPENDING STDOUT TO LOG ====' >> [list $logfile] ; cat [list $stdout_file] >> [list $logfile] ; }"
  } else {
    append wrap " 2>&1 | tee -a [list $logfile]"
    set postcopy ""
  }

  puts "SHELL> $wrap"
  set rc [catch {exec /bin/sh -lc "$wrap$postcopy"} out]
  puts $out
  if {$rc != 0} {
    puts stderr $out
    die "Shell command failed (rc=$rc). See log: $logfile"
  }
}

# ---------------- STEP 1: C-MODEL CLEAN ----------------
puts "INFO: C-model: make clean"
sh_run "make clean" $CMODEL_DIR $CMODEL_LOG "" "" $TIMEOUT_SEC

# ---------------- STEP 2: C-MODEL RUN (manual with stdin file) ----------------
puts "INFO: C-model: make manual (feeding stdin from file)"
sh_run "make manual" $CMODEL_DIR $CMODEL_LOG $CMODEL_STDIN $CMODEL_STDOUT $TIMEOUT_SEC
if {[string length [string trim $CMODEL_STDOUT]]} {
  puts "INFO: C-model stdout captured at: [nrm $CMODEL_STDOUT]"
}

# ---------------- STEP 3: VIVADO PIM FUNCTIONAL SIM (your known-good block) ----------------
# OPEN PROJECT
if {![file exists $XPR]} { die "Project not found: $XPR" }
open_project $XPR

# Ensure implemented results exist
if {[string equal [get_runs -quiet impl_1] ""]} { die "impl_1 run not found in project." }
open_run impl_1

# PREP sim_1
if {[string equal [get_filesets -quiet sim_1] ""]} {
  create_fileset -simset sim_1
}

# If a sim is currently open, close it first
catch { close_sim }

# Remove any existing files from sim_1
set _simfiles [get_files -quiet -of_objects [get_filesets sim_1]]
if {[llength $_simfiles]} {
  remove_files -fileset sim_1 $_simfiles
}

# Add TB files
set _tb_add_list {}
foreach f $TB_FILES {
  if {![file exists $f]} { die "TB file not found: $f" }
  lappend _tb_add_list [nrm $f]
}
add_files -fileset sim_1 $_tb_add_list

# Mark SystemVerilog files
foreach f $_tb_add_list {
  if {[string match "*.sv" $f] || [string match "*.svh" $f]} {
    catch { set_property file_type {SystemVerilog} [get_files -of_objects [get_filesets sim_1] $f] }
  }
}

# Includes & defines
if {[llength $TB_INCLUDE_DIRS]} {
  set incs {}
  foreach d $TB_INCLUDE_DIRS { if {[file isdirectory $d]} { lappend incs [nrm $d] } }
  if {[llength $incs]} { set_property include_dirs $incs [get_filesets sim_1] }
}
if {[llength $TB_DEFINES]} {
  set_property verilog_define $TB_DEFINES [get_filesets sim_1]
}

# Force TB as sim top
set_property top $TB_TOP [get_filesets sim_1]
# Make sure the top library is the default one
catch { set_property top_lib xil_defaultlib [get_filesets sim_1] }

# Recompute compile order for sim_1
update_compile_order -fileset sim_1

# Simulator & finish behavior
set_property target_simulator XSIM [current_project]
catch { set_property xsim.simulate.onfinish {quit} [get_filesets sim_1] }
catch { set_property xsim.simulate.runtime {all} [get_filesets sim_1] }

puts "INFO: SIM TOP set to    : [get_property top [get_filesets sim_1]]"
puts "INFO: TB files in sim_1 : [llength [get_files -of_objects [get_filesets sim_1]]]"

# Optionally reset sim artifacts (2024.1 has no -clean switch)
catch { reset_simulation -simset sim_1 }

# ---------------- LAUNCH (POST-IMPL FUNCTIONAL) ----------------
launch_simulation -simset sim_1 -mode post-implementation -type functional

# ------------- RUN ----------------
run all
quit
