# ================================================================
# FPGA Automation Tool — Single Post-Implementation Simulation
# LogicLance Compatible
#
# Usage: vivado -mode batch -source sim_single.tcl -tclargs <config.tcl>
# ================================================================

# Load config
if {$argc < 1} {
    puts stderr "Usage: vivado -source sim_single.tcl -tclargs <config.tcl>"
    exit 1
}
source [lindex $argv 0]

# Load utilities
source [file join $TOOL_DIR lib utils.tcl]

# ──────────────── Open Project ────────────────
fpga_validate_path $PROJECT_XPR "Vivado project (.xpr)"
open_project $PROJECT_XPR

# ──────────────── Open Implementation ────────────────
if {[string equal [get_runs -quiet impl_1] ""]} {
    fpga_die "impl_1 run not found in project."
}
open_run impl_1

# ──────────────── Prepare Simulation Fileset ────────────────
fpga_prepare_sim

# ──────────────── Launch Simulation ────────────────
fpga_log_info "Launching $SIM_MODE $SIM_TYPE simulation..."

launch_simulation -mode $SIM_MODE -type $SIM_TYPE

# ──────────────── Run ────────────────
run all
quit
