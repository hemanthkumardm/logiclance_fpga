# ================================================================
# FPGA Automation Tool — C-Model + Post-Implementation Simulation
# LogicLance Compatible
#
# Usage: vivado -mode batch -source cmod_sim.tcl -tclargs <config.tcl>
# ================================================================

if {$argc < 1} {
    puts stderr "Usage: vivado -source cmod_sim.tcl -tclargs <config.tcl>"
    exit 1
}
source [lindex $argv 0]
source [file join $TOOL_DIR lib utils.tcl]

# ── Step 1: C-Model ──
if {[info exists CMODEL_ENABLE] && $CMODEL_ENABLE} {
    fpga_validate_path $CMODEL_DIR "C-model directory"
    set _cmod_log [expr {[info exists CMODEL_LOG] && $CMODEL_LOG ne "" ? $CMODEL_LOG : [file join $OUTPUT_LOG_DIR "cmodel_run.log"]}]
    set _clean_tgt [expr {[info exists CMODEL_CLEAN_TARGET] && $CMODEL_CLEAN_TARGET ne "" ? $CMODEL_CLEAN_TARGET : "clean"}]
    set _run_tgt [expr {[info exists CMODEL_RUN_TARGET] && $CMODEL_RUN_TARGET ne "" ? $CMODEL_RUN_TARGET : "manual"}]

    fpga_log_info "C-model: make $_clean_tgt"
    fpga_sh_run "make $_clean_tgt" $CMODEL_DIR $_cmod_log "" "" $CMODEL_TIMEOUT

    if {[info exists CMODEL_BUILD_TARGETS] && [llength $CMODEL_BUILD_TARGETS]} {
        fpga_log_info "C-model: make [join $CMODEL_BUILD_TARGETS { }]"
        fpga_sh_run "make [join $CMODEL_BUILD_TARGETS { }]" $CMODEL_DIR $_cmod_log "" "" $CMODEL_TIMEOUT
    }

    set _stdin [expr {[info exists CMODEL_STDIN] && $CMODEL_STDIN ne "" ? $CMODEL_STDIN : ""}]
    set _stdout [expr {[info exists CMODEL_STDOUT] && $CMODEL_STDOUT ne "" ? $CMODEL_STDOUT : ""}]

    fpga_log_info "C-model: make $_run_tgt"
    fpga_sh_run "make $_run_tgt" $CMODEL_DIR $_cmod_log $_stdin $_stdout $CMODEL_TIMEOUT
    if {$_stdout ne ""} { fpga_log_info "C-model stdout: [fpga_nrm $_stdout]" }
}

# ── Step 2: Open Project & Impl ──
fpga_validate_path $PROJECT_XPR "Vivado project (.xpr)"
open_project $PROJECT_XPR
if {[string equal [get_runs -quiet impl_1] ""]} { fpga_die "impl_1 not found." }
open_run impl_1

# ── Step 3: Sim ──
fpga_prepare_sim
catch { reset_simulation -simset sim_1 }
launch_simulation -simset sim_1 -mode $SIM_MODE -type $SIM_TYPE
run all
quit
