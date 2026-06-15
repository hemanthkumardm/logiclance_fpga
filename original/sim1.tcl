# ================================================================
# Post-Implementation Functional Simulation (force specified TB)
# Vivado 2024.1
# ================================================================

# ------------- PROJECT / TESTBENCH CONFIG -------------
# Project (.xpr)
set XPR "/mnt/newvolume/darshan/VIVAD_2024.1/Test_proj/Test_proj/Test_proj.xpr"

# Testbench top (module/entity name, NOT filename)
set TB_TOP "AcceleratorWrapperTB"

# ABSOLUTE PATH to your TB TOP FILE (edit if needed)
# If your TB is elsewhere, change this path accordingly:
set TB_TOP_FILE "/mnt/newvolume/darshan/VIVAD_2024.1/Test_proj/BehavioralTB.sv"

# (Optional) additional TB files (packages/agents/etc.)
set TB_EXTRA_FILES {
    # "/mnt/newvolume/darshan/VIVAD_2024.1/Test_proj/tb/tb_pkg.sv"
    # "/mnt/newvolume/darshan/VIVAD_2024.1/Test_proj/tb/agents/axi_agent.sv"
}

# (Optional) include dirs for `include headers
set TB_INCLUDE_DIRS {
    # "/mnt/newvolume/darshan/VIVAD_2024.1/Test_proj/tb/include"
}

# (Optional) Verilog/SystemVerilog defines for TB
set TB_DEFINES {SIM=1}

# ------------- HELPERS -------------
proc die {msg} { puts stderr "ERROR: $msg"; exit 1 }
proc nrm {p} { return [file normalize $p] }

# ------------- OPEN PROJECT -------------
if {![file exists $XPR]} { die "Project not found: $XPR" }
open_project $XPR

# ------------- PREP sim_1 WITH ONLY YOUR TB -------------
if {[string equal [get_filesets -quiet sim_1] ""]} { create_fileset -simset sim_1 }

# Clear sim_1 to avoid stale/extra files
set _simfiles [get_files -quiet -of_objects [get_filesets sim_1]]
if {[llength $_simfiles]} { remove_files -fileset sim_1 $_simfiles }

# Validate TB top file and add TB files
if {![file exists $TB_TOP_FILE]} { die "TB top file not found: $TB_TOP_FILE" }
set tb_files [list [nrm $TB_TOP_FILE]]
foreach f $TB_EXTRA_FILES {
  if {[string trim $f] eq ""} { continue }
  if {[file exists $f]} { lappend tb_files [nrm $f] } else { puts "WARN: TB extra file not found: $f" }
}
add_files -fileset sim_1 $tb_files

# Ensure SystemVerilog file type where applicable
foreach f $tb_files {
  if {[string match "*.sv" $f] || [string match "*.svh" $f]} {
    catch { set_property file_type {SystemVerilog} [get_files -of_objects [get_filesets sim_1] $f] }
  }
}

# Includes & defines
set incs {}
foreach d $TB_INCLUDE_DIRS { if {[file isdirectory $d]} { lappend incs [nrm $d] } }
if {[llength $incs]} { set_property include_dirs $incs [get_filesets sim_1] }
if {[llength $TB_DEFINES]} { set_property verilog_define $TB_DEFINES [get_filesets sim_1] }

# Force TB as sim top
set_property top $TB_TOP [get_filesets sim_1]

# Bind sim_1 to design sources and update order
catch { set_property SOURCE_SET sources_1 [get_filesets sim_1] }
update_compile_order -fileset sim_1

# Safety: end sim when $finish occurs
catch { set_property xsim.simulate.onfinish {quit} [get_filesets sim_1] }
# Let $finish end early (don’t force a long runtime)
catch { set_property xsim.simulate.runtime {all} [get_filesets sim_1] }

puts "INFO: SIM TOP set to    : [get_property top [get_filesets sim_1]]"
puts "INFO: TB files in sim_1 : [llength [get_files -of_objects [get_filesets sim_1]]]"

# ------------- USE EXISTING IMPLEMENTED RESULTS -------------
if {[string equal [get_runs -quiet impl_1] ""]} { die "impl_1 run not found in project." }
open_run impl_1

# ------------- SELECT SIMULATOR & LAUNCH -------------
set_property target_simulator XSIM [current_project]

# Post-implementation (routed netlist), functional (NO SDF)
launch_simulation -mode post-implementation -type functional

# ------------- RUN -------------
run all
quit
