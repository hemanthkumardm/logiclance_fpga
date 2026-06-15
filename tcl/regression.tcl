# ================================================================
# FPGA Automation Tool — Multi-Testcase Regression
# LogicLance Compatible
#
# Usage: vivado -mode batch -source regression.tcl -tclargs <config.tcl>
# ================================================================

if {$argc < 1} {
    puts stderr "Usage: vivado -source regression.tcl -tclargs <config.tcl>"
    exit 1
}
source [lindex $argv 0]
source [file join $TOOL_DIR lib utils.tcl]

# ── Open Project & Impl ──
fpga_validate_path $PROJECT_XPR "Vivado project (.xpr)"
open_project $PROJECT_XPR
if {[string equal [get_runs -quiet impl_1] ""]} { fpga_die "impl_1 not found." }
fpga_log_info "impl_1 status: [get_property STATUS [get_runs impl_1]]"
open_run impl_1
current_run -implementation [get_runs impl_1]

# ── Prepare sim_1 ──
fpga_prepare_sim

# Pass C-model path as define
set _defs $TB_DEFINES
if {[info exists CMODEL_OUT_FIXED] && $CMODEL_OUT_FIXED ne ""} {
    file mkdir [file dirname [fpga_nrm $CMODEL_OUT_FIXED]]
    lappend _defs "CMODEL_OUT=\\\"[fpga_nrm $CMODEL_OUT_FIXED]\\\""
}
if {[llength $_defs]} {
    set_property verilog_define $_defs [get_filesets sim_1]
}

update_compile_order -fileset sim_1

# ── Run Test Cases ──
set pass_count 0
set fail_count 0
set unknown_count 0
set results {}

if {[info exists CMODEL_LOG_DIR]} { catch { file mkdir [fpga_nrm $CMODEL_LOG_DIR] } }
if {[info exists SIM_LOG_DIR]}    { catch { file mkdir [fpga_nrm $SIM_LOG_DIR] } }
if {[info exists RESULT_FILE]}    { catch { file mkdir [file dirname [fpga_nrm $RESULT_FILE]] } }

set _cmodel_start_delay 800

foreach testcase $TEST_CASES {
    array set TC $testcase

    puts "\n=================================================================="
    puts "RUNNING TEST CASE: $TC(name)"
    puts "=================================================================="

    # Launch C-model async (if enabled)
    if {[info exists CMODEL_ENABLE] && $CMODEL_ENABLE} {
        set cmodel_log [file join $CMODEL_LOG_DIR "cmodel_run_${TC(name)}.log"]
        set _fixed [expr {[info exists CMODEL_OUT_FIXED] ? $CMODEL_OUT_FIXED : ""}]
        set _stdout [expr {[info exists TC(stdout)] ? $TC(stdout) : ""}]

        set cmodel_pid [fpga_cmodel_async $CMODEL_DIR $TC(stdin) $_stdout $_fixed $cmodel_log $CMODEL_TIMEOUT]
        if {$cmodel_pid eq ""} {
            fpga_log_error "C-model did not start for $TC(name)"
        } else {
            fpga_log_info "C-model PID for $TC(name): $cmodel_pid"
        }
        after $_cmodel_start_delay
    }

    # Reset and launch simulation
    catch { stop }
    catch { close_sim }
    catch { reset_simulation -simset sim_1 }

    fpga_log_info "Launching simulation for $TC(name)"
    current_run -implementation [get_runs impl_1]
    current_fileset -simset [get_filesets sim_1]
    launch_simulation -simset sim_1 -mode $SIM_MODE -type $SIM_TYPE

    # Archive sim log
    if {[info exists SIM_LOG_DIR]} {
        set sim_log [file join $SIM_LOG_DIR "sim_log_${TC(name)}.txt"]
        catch { file copy -force xsim.dir/xsim.log $sim_log }
    }

    # Extract RESULT.txt from the simulation working directory
    set sim_root [file join [get_property DIRECTORY [current_project]] [current_project].sim]
    
    # Robust recursive find
    proc find_result {dir} {
        foreach f [glob -nocomplain -directory $dir -type f RESULT.txt] { return $f }
        foreach d [glob -nocomplain -directory $dir -type d *] {
            set r [find_result $d]; if {$r ne ""} { return $r }
        }
        return ""
    }
    
    set generated_res [find_result $sim_root]
    
    # Copy it to the GUI's expected RESULT_FILE
    if {$generated_res ne ""} {
        puts "INFO: Found testbench result at: $generated_res"
        if {[info exists RESULT_FILE] && $RESULT_FILE ne ""} {
            set dest [fpga_nrm $RESULT_FILE]
            if {[catch { file copy -force $generated_res $dest } e]} {
                puts "WARNING: Failed to copy result to $dest: $e"
            } else {
                puts "INFO: Copied result to $dest"
            }
        }
    } else {
        puts "WARNING: RESULT.txt not found anywhere in $sim_root"
    }

    # Check result
    set verdict [fpga_read_result_file $RESULT_FILE $PASS_PATTERN $FAIL_PATTERN]
    if {$verdict == 1} {
        incr pass_count
        lappend results [format "%s : PASS" $TC(name)]
        puts "RESULT: $TC(name) => PASS"
    } elseif {$verdict == 0} {
        incr fail_count
        lappend results [format "%s : FAIL" $TC(name)]
        puts "RESULT: $TC(name) => FAIL"
    } else {
        incr unknown_count
        lappend results [format "%s : UNKNOWN" $TC(name)]
        puts "RESULT: $TC(name) => UNKNOWN (no marker in RESULT.txt)"
    }

    after 200
}

# ── Summary ──
puts "\n==================== SUMMARY ===================="
foreach r $results { puts $r }
puts "------------------------------------------------"
puts [format "PASSED : %d" $pass_count]
puts [format "FAILED : %d" $fail_count]
puts [format "UNKNOWN: %d" $unknown_count]
puts "================================================"

if {$fail_count > 0} { exit 1 }
quit
