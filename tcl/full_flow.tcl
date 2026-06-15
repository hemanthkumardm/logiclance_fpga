# ================================================================
# FPGA Automation Tool — Full Flow (Synth → Impl → Test → XSA)
# LogicLance Compatible
#
# Usage: vivado -mode batch -source full_flow.tcl -tclargs <config.tcl>
# ================================================================

if {$argc < 1} {
    puts stderr "Usage: vivado -source full_flow.tcl -tclargs <config.tcl>"
    exit 1
}
source [lindex $argv 0]
source [file join $TOOL_DIR lib utils.tcl]

# ── Step 1: Git Clone (optional) ──
if {[info exists GIT_ENABLE] && $GIT_ENABLE} {
    fpga_log_info "Cloning sources from Git..."
    fpga_git_clone_merge $GIT_REPO $GIT_COMMIT $GIT_DEST $GIT_SUBDIR
}

# ── Step 2: Create or Open Project ──
if {[info exists PROJECT_XPR] && $PROJECT_XPR ne ""} {
    fpga_validate_path $PROJECT_XPR "Vivado project (.xpr)"
    open_project $PROJECT_XPR
    fpga_log_info "Opened existing project: $PROJECT_XPR"
} else {
    # Create new project
    if {![info exists FPGA_PART] || $FPGA_PART eq ""} {
        fpga_die "Either PROJECT_XPR or FPGA_PART must be set."
    }

    set _proj_name [expr {[info exists PROJECT_NAME] ? $PROJECT_NAME : "fpga_project"}]
    set _proj_dir  [expr {[info exists PROJECT_DIR]  ? $PROJECT_DIR  : "./$_proj_name"}]

    fpga_log_info "Creating project: $_proj_name (part: $FPGA_PART)"
    create_project -force $_proj_name $_proj_dir -part $FPGA_PART

    # Board part
    if {[info exists BOARD_PART] && $BOARD_PART ne ""} {
        set_property -name "board_part" -value $BOARD_PART -objects [current_project]
    }

    # IP repos
    if {[info exists IP_REPO_PATHS] && [llength $IP_REPO_PATHS]} {
        set_property "ip_repo_paths" $IP_REPO_PATHS [get_filesets sources_1]
        update_ip_catalog -rebuild
    }

    # Source files
    if {[info exists SOURCE_FILES] && [llength $SOURCE_FILES]} {
        foreach src $SOURCE_FILES {
            if {[file isdirectory $src]} {
                add_files -fileset sources_1 [fpga_rglob $src {*.v *.sv *.vhd *.vhdl}]
            } elseif {[file exists $src]} {
                add_files -fileset sources_1 $src
            } else {
                fpga_log_warn "Source not found: $src"
            }
        }
    }

    # Block design Tcl
    if {[info exists BD_TCL_SCRIPT] && $BD_TCL_SCRIPT ne ""} {
        fpga_validate_path $BD_TCL_SCRIPT "Block design Tcl script"
        fpga_log_info "Sourcing block design: $BD_TCL_SCRIPT"
        source $BD_TCL_SCRIPT
    }

    update_compile_order -fileset sources_1
}

# ── Step 3: Synthesis ──
fpga_log_info "Launching synthesis..."
set _synth_jobs [expr {[info exists SYNTH_JOBS] ? $SYNTH_JOBS : 4}]

if {[string equal [get_runs -quiet synth_1] ""]} {
    create_run -name synth_1 -flow {Vivado Synthesis 2024} -strategy "Vivado Synthesis Defaults"
}
current_run -synthesis [get_runs synth_1]
launch_runs synth_1 -jobs $_synth_jobs
wait_on_run synth_1

set synth_status [get_property STATUS [get_runs synth_1]]
fpga_log_info "Synthesis status: $synth_status"

# ── Step 4: Implementation ──
fpga_log_info "Launching implementation..."
set _impl_jobs [expr {[info exists IMPL_JOBS] ? $IMPL_JOBS : 8}]

if {[string equal [get_runs -quiet impl_1] ""]} {
    create_run -name impl_1 -flow {Vivado Implementation 2024} -strategy "Vivado Implementation Defaults" -parent_run synth_1
}
current_run -implementation [get_runs impl_1]

# Run up to route_design first (needed for post-impl sim)
launch_runs impl_1 -to_step route_design -jobs $_impl_jobs
wait_on_run impl_1
open_run impl_1 -name impl_1

set impl_status [get_property STATUS [get_runs impl_1]]
fpga_log_info "Implementation status: $impl_status"

# ── Step 5: Regression Tests (optional) ──
if {[info exists TEST_CASES] && [llength $TEST_CASES]} {
    fpga_log_info "Running post-implementation regression tests..."

    # Prepare sim
    fpga_prepare_sim

    if {[info exists CMODEL_OUT_FIXED] && $CMODEL_OUT_FIXED ne ""} {
        file mkdir [file dirname [fpga_nrm $CMODEL_OUT_FIXED]]
        set _defs $TB_DEFINES
        lappend _defs "CMODEL_OUT=\\\"[fpga_nrm $CMODEL_OUT_FIXED]\\\""
        set_property verilog_define $_defs [get_filesets sim_1]
    }
    update_compile_order -fileset sim_1

    set pass_count 0
    set fail_count 0
    set results {}

    if {[info exists CMODEL_LOG_DIR]} { catch { file mkdir [fpga_nrm $CMODEL_LOG_DIR] } }
    if {[info exists SIM_LOG_DIR]}    { catch { file mkdir [fpga_nrm $SIM_LOG_DIR] } }
    if {[info exists RESULT_FILE]}    { catch { file mkdir [file dirname [fpga_nrm $RESULT_FILE]] } }

    foreach testcase $TEST_CASES {
        array set TC $testcase
        fpga_log_info "Running test: $TC(name)"

        if {[info exists CMODEL_ENABLE] && $CMODEL_ENABLE} {
            set cmodel_log [file join $CMODEL_LOG_DIR "cmodel_run_${TC(name)}.log"]
            set _fixed [expr {[info exists CMODEL_OUT_FIXED] ? $CMODEL_OUT_FIXED : ""}]
            set _stdout [expr {[info exists TC(stdout)] ? $TC(stdout) : ""}]
            fpga_cmodel_async $CMODEL_DIR $TC(stdin) $_stdout $_fixed $cmodel_log $CMODEL_TIMEOUT
            after 800
        }

        catch { stop }; catch { close_sim }; catch { reset_simulation -simset sim_1 }
        current_run -implementation [get_runs impl_1]
        launch_simulation -simset sim_1 -mode $SIM_MODE -type $SIM_TYPE

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
            lappend results [format "%s : UNKNOWN" $TC(name)]
            puts "RESULT: $TC(name) => UNKNOWN"
        }
        after 200
    }

    puts "\n==================== REGRESSION SUMMARY ===================="
    foreach r $results { puts $r }
    puts [format "PASSED: %d  FAILED: %d" $pass_count $fail_count]
    puts "============================================================"

    if {$fail_count > 0} {
        fpga_log_error "Regression FAILED — skipping bitstream/XSA."
        exit 1
    }
}

# ── Step 6: Bitstream (optional) ──
if {[info exists OUTPUT_BIT] && $OUTPUT_BIT ne ""} {
    fpga_log_info "Generating bitstream..."
    launch_runs impl_1 -to_step write_bitstream -jobs $_impl_jobs
    wait_on_run impl_1
    open_run impl_1 -name impl_1
    write_bitstream -force $OUTPUT_BIT
    fpga_log_info "Bitstream written: $OUTPUT_BIT"
}

# ── Step 7: XSA Export (optional) ──
if {[info exists OUTPUT_XSA] && $OUTPUT_XSA ne ""} {
    fpga_log_info "Exporting XSA..."
    write_hw_platform -fixed -include_bit -file $OUTPUT_XSA
    fpga_log_info "XSA exported: $OUTPUT_XSA"
}

fpga_log_info "Full flow completed successfully."
quit
