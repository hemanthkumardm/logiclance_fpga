# =================================================================
# post_impl_multi_test_gate.tcl
# Wraps your multi-test post-implementation XSIM flow into a proc
# Returns: 1 if all tests PASS, else 0
# =================================================================

proc run_post_impl_tests {} {
  # ---------------- CONFIG (your paths) ----------------
  set TB_DIR                          "/mnt/newvolume/darshan/VIVAD_2024.1/working_proj_tcl_29_09/tb"
  set TB_FILES                        [list \
    "/mnt/newvolume/darshan/VIVAD_2024.1/working_proj_tcl_29_09/tb/BehavioralTB.sv" \
  ]

  set RESULT_FILE                     "/mnt/newvolume/darshan/VIVAD_2024.1/working_proj_tcl_29_09/tb/RESULT.txt"

  set CMODEL_DIR                      "/mnt/newvolume/darshan/VIVAD_2024.1/Interrupt_debug/cmod/cmodel_exsleratev2/systemc-perf-model"
  set CMODEL_OUT_FIXED                "/mnt/newvolume/darshan/VIVAD_2024.1/working_proj_tcl_29_09/Cmod_Out/CMODEL_OUT.txt"

  set CMODEL_LOG_DIR                  "/mnt/newvolume/darshan/VIVAD_2024.1/working_proj_tcl_29_09/Cmod_Out/Test_proj"
  set SIM_LOG_DIR                     "/mnt/newvolume/darshan/VIVAD_2024.1/working_proj_tcl_29_09/Run_log/Test_proj"

  set TEST_CASES {
    {name "tc1" stdin "/mnt/newvolume/darshan/VIVAD_2024.1/working_proj_tcl_29_09/Cmod_In/cmod_in_tc1.txt" stdout "/mnt/newvolume/darshan/VIVAD_2024.1/working_proj_tcl_29_09/Run_log/out_golden_tc1.txt"}
    {name "tc2" stdin "/mnt/newvolume/darshan/VIVAD_2024.1/working_proj_tcl_29_09/Cmod_In/cmod_in_tc2.txt" stdout "/mnt/newvolume/darshan/VIVAD_2024.1/working_proj_tcl_29_09/Run_log/out_golden_tc2.txt"}
    {name "tc3" stdin "/mnt/newvolume/darshan/VIVAD_2024.1/working_proj_tcl_29_09/Cmod_In/cmod_in_tc3.txt" stdout "/mnt/newvolume/darshan/VIVAD_2024.1/working_proj_tcl_29_09/Run_log/out_golden_tc3.txt"}
  }

  # ---------------- OTHER CONFIG ----------------
  set TB_TOP                   "AcceleratorWrapperTB"
  set TB_DEFINES_BASE          {SIM=1}
  set TB_EXTRA_INCLUDES        {}
  set TIMEOUT_SEC              900
  set CMODEL_START_DELAY_MS    800
  set PASS_PATTERN             {TEST_PASSED}
  set FAIL_PATTERN             {TEST_FAILED}

  # ---------------- HELPERS ----------------
  proc _pim_die {msg} { puts stderr "ERROR: $msg"; return -code error $msg }
  proc _norm {p} { return [file normalize $p] }

  proc _rglob_ext {root exts} {
    set out {}
    if {![file isdirectory $root]} { return $out }
    foreach entry [glob -nocomplain -directory $root *] {
      if {[file isdirectory $entry]} {
        set out [concat $out [_rglob_ext $entry $exts]]
      } else {
        set base [file tail $entry]
        foreach pat $exts { if {[string match $pat $base]} { lappend out $entry; break } }
      }
    }
    return $out
  }

  proc _rglob {root pats} {
    set out {}
    if {![file isdirectory $root]} { return $out }
    foreach e [glob -nocomplain -types {f d} -directory $root *] {
      if {[file isdirectory $e]} {
        set out [concat $out [_rglob $e $pats]]
      } else {
        foreach p $pats { if {[string match $p $e]} { lappend out $e; break } }
      }
    }
    return $out
  }

  proc _file_contents_eq {path text} {
    if {![file exists $path]} { return 0 }
    set f [open $path r]; set cur [read $f]; close $f
    return [string equal $cur $text]
  }

  proc _start_cmodel_async {workdir stdin_file pertest_out fixed_out logfile timeout_s} {
    if {![file isdirectory $workdir]} { _pim_die "C-model dir not found: $workdir" }
    set workdir     [file normalize $workdir]
    set stdin_file  [file normalize $stdin_file]
    set pertest_out [file normalize $pertest_out]
    set fixed_out   [file normalize $fixed_out]
    set logfile     [file normalize $logfile]

    foreach d [list [file dirname $pertest_out] [file dirname $fixed_out] [file dirname $logfile]] {
      if {![file isdirectory $d]} { file mkdir $d }
    }
    if {![file exists $stdin_file]} { _pim_die "C-model stdin not found: $stdin_file" }

    set tools_dir [file join $workdir .sim_tools]
    if {![file isdirectory $tools_dir]} { file mkdir $tools_dir }
    set runner  [file join $tools_dir cmodel_run.sh]
    set pidfile [file join $tools_dir cmodel.pid]

    set template {#!/bin/sh
set -eu
umask 022
cd "@WORKDIR@" || exit 97
: > "@FIXED_OUT@" || exit 98
: > "@LOGFILE@"   || true
: > "@PERTEST_OUT@" || exit 99
BASE_ENV="PATH=/usr/bin:/bin:/usr/local/bin HOME=${HOME:-} USER=${USER:-}"
CLEAN="env -i ${BASE_ENV}"
$CLEAN LD_LIBRARY_PATH= LD_PRELOAD= make -k -C "@WORKDIR@" clean >/dev/null 2>&1 || true
build_with_fs_shim=0
build_ok=0
if $CLEAN LD_LIBRARY_PATH= LD_PRELOAD= make -C "@WORKDIR@" compiler conv_controller comparator 1>>"@LOGFILE@" 2>&1; then
  build_ok=1
else
  echo "WARN: first build failed — will retry with -lstdc++fs shim" >> "@LOGFILE@"
fi
if [ $build_ok -eq 0 ]; then
  REAL_GXX="$(command -v g++ || true)"
  if [ -z "$REAL_GXX" ]; then
    echo "ERROR: g++ not found on PATH" >> "@LOGFILE@"
    exit 95
  fi
  mkdir -p "@TOOLS_DIR@"
  cat > "@TOOLS_DIR@/g++" <<'EOSH'
#!/bin/sh
: "${GXX_REAL:=/usr/bin/g++}"
exec "$GXX_REAL" "$@" -lstdc++fs
EOSH
  chmod +x "@TOOLS_DIR@/g++"
  CLEAN_SHIM="env -i PATH=@TOOLS_DIR@:/usr/bin:/bin:/usr/local/bin HOME=${HOME:-} USER=${USER:-} GXX_REAL=$REAL_GXX"
  if $CLEAN_SHIM LD_LIBRARY_PATH= LD_PRELOAD= make -C "@WORKDIR@" clean >/dev/null 2>&1; then :; fi
  if $CLEAN_SHIM LD_LIBRARY_PATH= LD_PRELOAD= make -C "@WORKDIR@" compiler conv_controller comparator 1>>"@LOGFILE@" 2>&1; then
    build_ok=1
    build_with_fs_shim=1
    echo "INFO: build succeeded with -lstdc++fs shim" >> "@LOGFILE@"
  else
    echo "ERROR: build still failing even with -lstdc++fs shim" >> "@LOGFILE@"
    exit 95
  fi
fi
if $CLEAN LD_LIBRARY_PATH= LD_PRELOAD= make -C "@WORKDIR@" -n manual >/dev/null 2>&1; then
  RUN_ENV="$CLEAN"; [ $build_with_fs_shim -eq 1 ] && RUN_ENV="$CLEAN_SHIM"
  RUN_CMD="$RUN_ENV LD_LIBRARY_PATH= LD_PRELOAD= make -C \"@WORKDIR@\" manual < \"@STDIN@\" 2>&1"
else
  RUN_ENV="$CLEAN"; [ $build_with_fs_shim -eq 1 ] && RUN_ENV="$CLEAN_SHIM"
  RUN_CMD="$RUN_ENV LD_LIBRARY_PATH= LD_PRELOAD= sh -c './compiler --manual < \"@STDIN@\" && ./conv_controller && ./comparator' 2>&1"
fi
if command -v tee >/dev/null 2>&1; then
  ( nohup sh -c "$RUN_CMD" \
      | tee "@FIXED_OUT@" \
      | tee -a "@LOGFILE@" \
      > "@PERTEST_OUT@" ) &
else
  ( nohup sh -c "$RUN_CMD" > "@FIXED_OUT@" ) &
fi
pid=$!
echo "$pid" > "@PIDFILE@"
sleep 0.3
kill -0 "$pid" >/dev/null 2>&1 || {
  echo "ERROR: background run not alive (pid=$pid)" >> "@LOGFILE@"
  exit 96
}
exit 0
}
    set script [string map [list \
      @WORKDIR@     $workdir \
      @STDIN@       $stdin_file \
      @PERTEST_OUT@ $pertest_out \
      @FIXED_OUT@   $fixed_out \
      @LOGFILE@     $logfile \
      @PIDFILE@     $pidfile \
      @TOOLS_DIR@   $tools_dir \
    ] $template]

    if {![ _file_contents_eq $runner $script]} {
      set fh [open $runner w]; puts -nonewline $fh $script; close $fh
      file attributes $runner -permissions u+x,g+x,o+x
    }

    puts "C-MODEL> launching via $runner"
    set rc [catch { exec $runner } msg]
    if {$rc != 0} {
      puts "ERROR: C-model runner failed to start: $msg"
      if {[file exists $pidfile]} {
        set f [open $pidfile r]; set pidtxt [string trim [read $f]]; close $f
        puts "INFO: pidfile exists: $pidtxt"
      }
      return ""
    }

    if {![file exists $pidfile]} { puts "ERROR: pidfile not created"; return "" }
    set pf [open $pidfile r]; set pid [string trim [read $pf]]; close $pf
    if {$pid eq ""} { puts "ERROR: pidfile empty"; return "" }
    return $pid
  }

  proc _scan_modules {files} {
    set names {}
    foreach f $files {
      if {![file exists $f]} { continue }
      set ext [string tolower [file extension $f]]
      if {$ext ni {.v .sv .vh .svh}} { continue }
      set fh [open $f r]; set txt [read $fh]; close $fh
      foreach m [regexp -inline -all {(?m)^\s*module\s+([A-Za-z_][A-Za-z0-9_$]*)} $txt] {
        if {[regexp {module\s+([A-Za-z_][A-Za-z0-9_$]*)} $m -> nm]} { lappend names $nm }
      }
    }
    return [lsort -unique $names]
  }

  proc _make_top_alias {real_top outpath} {
    set fh [open $outpath w]
    puts $fh "// Auto-generated shim so TB can instantiate 'top' while real top is '$real_top'"
    puts $fh "module top(); $real_top dut(); endmodule"
    close $fh
  }

  proc _read_result_file {path pass_re fail_re} {
    if {![file exists $path]} { return -1 }
    set fh [open $path r]
    set txt [string trim [read $fh]]
    close $fh
    if {[regexp -nocase -- $fail_re $txt]} { return 0 }
    if {[regexp -nocase -- $pass_re $txt]} { return 1 }
    return -1
  }

  # ---------------- Assume project & impl_1 already open ----------------
  if {[string equal [get_runs -quiet impl_1] ""]} { _pim_die "impl_1 run not found in project." }
  puts "INFO: impl_1 status: [get_property STATUS [get_runs impl_1]]"
  open_run impl_1
  current_run -implementation [get_runs impl_1]

  # ---------------- PREP sim_1 ----------------
  if {[string equal [get_filesets -quiet sim_1] ""]} { create_fileset -simset sim_1 }
  set_property target_simulator XSIM [current_project]
  catch { set_property xsim.simulate.onfinish {quit -force} [get_filesets sim_1] }
  catch { set_property xsim.simulate.runtime {all} [get_filesets sim_1] }

  if {[string equal [get_filesets -quiet sources_1] ""]} { _pim_die "sources_1 fileset not found in project." }
  set_property SOURCE_SET sources_1 [get_filesets sim_1]
  current_fileset -simset [get_filesets sim_1]

  catch { upgrade_ip [get_ips *] }
  catch { generate_target {simulation} [get_ips *] }
  catch { export_ip_user_files -of_objects [get_ips *] -no_script -sync -quiet }
  set _simip_dir [file join [get_property DIRECTORY [current_project]] .ip_sim]
  catch { file mkdir $_simip_dir }
  catch { export_simulation -of_objects [get_ips *] -simulator xsim -directory $_simip_dir -force }

  foreach f [get_files -of_objects [get_filesets sources_1]] {
    catch { set_property USED_IN_SIMULATION true $f }
  }

  catch { reset_simulation -simset sim_1 }
  set _simfiles [get_files -quiet -of_objects [get_filesets sim_1]]
  if {[llength $_simfiles]} { remove_files -fileset sim_1 $_simfiles }

  # Import design HDL into sim_1 (in addition to SOURCE_SET)
  set design_files [get_files -of_objects [get_filesets sources_1]]
  set design_hdl {}
  foreach f $design_files {
    set ext [string tolower [file extension $f]]
    if {$ext in {.v .sv .vh .svh .vhd .vhdl}} { lappend design_hdl $f }
  }
  if {[llength $design_hdl]} {
    add_files -fileset sim_1 $design_hdl
    foreach f $design_hdl { catch { set_property USED_IN_SIMULATION true $f } }
  }

  # Auto-discover IP HDL
  set PROJ_DIR [get_property DIRECTORY [current_project]]
  set IP_DIRS {}
  foreach ipuf [glob -nocomplain -types d -directory $PROJ_DIR *.ip_user_files] {
    foreach bd     [glob -nocomplain -types d -directory $ipuf bd *] {
      foreach ips  [glob -nocomplain -types d -directory $bd ipshared *] {
        foreach leaf [glob -nocomplain -types d -directory $ips *] {
          set srcdir [file join $leaf src]
          if {[file isdirectory $srcdir]} { lappend IP_DIRS [file normalize $srcdir] }
        }
      }
    }
  }
  set IP_DIRS [lsort -unique $IP_DIRS]
  if {[llength $IP_DIRS]} {
    puts "INFO: Found IP src dirs:"; foreach d $IP_DIRS { puts "  - $d" }
    set added_ip_files 0
    set incs [get_property include_dirs [get_filesets sim_1]]
    foreach d $IP_DIRS {
      set hdl [_rglob $d {*.sv *.svh *.v *.vh *.vhd *.vhdl}]
      if {[llength $hdl]} {
        add_files -fileset sim_1 $hdl
        foreach f $hdl { catch { set_property USED_IN_SIMULATION true $f } }
        incr added_ip_files [llength $hdl]
        lappend incs $d
      }
    }
    if {[llength $incs]} { set_property include_dirs $incs [get_filesets sim_1] }
    puts "INFO: Added $added_ip_files IP HDL files from discovered dirs"
  } else {
    puts "WARN: No IP src dirs found under $PROJ_DIR/*.ip_user_files/bd/*/ipshared/*/src"
  }

  # Add glbl.v
  if {[info exists ::env(XILINX_VIVADO)]} {
    set glblv [file join $::env(XILINX_VIVADO) data verilog src glbl.v]
    if {[file exists $glblv]} { add_files -fileset sim_1 $glblv }
  }

  # Add TB
  set _tb_add_list {}
  if {$TB_DIR ne ""} {
    if {![file isdirectory $TB_DIR]} { _pim_die "TB dir not found: $TB_DIR" }
    set tb_exts {*.sv *.svh *.v *.vh *.vhd *.vhdl}
    set auto_tbs [_rglob_ext $TB_DIR $tb_exts]
    if {[llength $auto_tbs]} {
      foreach f $auto_tbs { lappend _tb_add_list [_norm $f] }
    } else {
      puts "WARN: No TB files found under $TB_DIR"
    }
  } else {
    foreach f $TB_FILES {
      if {![file exists $f]} { _pim_die "TB file not found: $f" }
      lappend _tb_add_list [_norm $f]
    }
  }
  if {[llength $_tb_add_list]} { add_files -fileset sim_1 $_tb_add_list }

  foreach f $_tb_add_list {
    if {[string match "*.sv" $f] || [string match "*.svh" $f]} {
      catch { set_property file_type {SystemVerilog} [get_files -of_objects [get_filesets sim_1] $f] }
    }
  }
  puts "INFO: TB files added: [llength [get_files -of_objects [get_filesets sim_1]]]"

  # Includes / defines
  set incs {}
  if {$TB_DIR ne "" && [file isdirectory [file join $TB_DIR include]]} {
    lappend incs [_norm [file join $TB_DIR include]]
  }
  foreach p $TB_EXTRA_INCLUDES { if {[file isdirectory $p]} { lappend incs [_norm $p] } }
  if {[llength $incs]} { catch { set_property include_dirs $incs [get_filesets sim_1] } }

  file mkdir [file dirname [_norm $CMODEL_OUT_FIXED]]
  set TB_DEFINES $TB_DEFINES_BASE
  lappend TB_DEFINES CMODEL_OUT=\"[_norm $CMODEL_OUT_FIXED]\"
  set_property verilog_define $TB_DEFINES [get_filesets sim_1]

  # Make 'top' shim if needed
  set sim_files_all [get_files -of_objects [get_filesets sim_1]]
  set mod_names [_scan_modules $sim_files_all]
  if {[lsearch -exact $mod_names top] < 0} {
    set real_top [get_property top [get_filesets sources_1]]
    if {$real_top eq ""} {
      if {[llength $mod_names] > 0} {
        set real_top [lindex $mod_names 0]
        puts "WARN: sources_1 has no 'top' property; guessing '$real_top'"
      } else {
        _pim_die "No modules found to alias as 'top'."
      }
    }
    set shim_dir [file join [get_property DIRECTORY [current_project]] .sim_shim]
    if {![file isdirectory $shim_dir]} { file mkdir $shim_dir }
    set shim_sv  [file join $shim_dir auto_top_alias_for_tb.sv]
    _make_top_alias $real_top $shim_sv
    add_files -fileset sim_1 $shim_sv
    catch {
      set obj [get_files -of_objects [get_filesets sim_1] $shim_sv]
      if {[llength $obj]} { set_property file_type {SystemVerilog} $obj }
    }
    puts "INFO: Created alias shim 'top' -> '$real_top'"
  }

  # Set TB TOP
  if {$TB_TOP ne ""} { set_property top $TB_TOP [get_filesets sim_1] }
  catch { set_property top_lib xil_defaultlib [get_filesets sim_1] }
  update_compile_order -fileset sim_1

  puts "INFO: SIM TOP set to: [get_property top [get_filesets sim_1]]"
  puts "INFO: sim_1 file count: [llength [get_files -of_objects [get_filesets sim_1]]]"

  # ---------------- RUN MULTIPLE TESTCASES ----------------
  set pass_count 0
  set fail_count 0
  set unknown_count 0
  set results {}

  catch { file mkdir [_norm $CMODEL_LOG_DIR] }
  catch { file mkdir [_norm $SIM_LOG_DIR] }
  catch { file mkdir [file dirname [_norm $RESULT_FILE]] }

  foreach testcase $TEST_CASES {
    array set TC $testcase
    puts "\n=================================================================="
    puts "RUNNING TEST CASE: $TC(name)"
    puts "=================================================================="

    set cmodel_log [file join $CMODEL_LOG_DIR "cmodel_run_${TC(name)}.log"]
    set cmodel_pid [_start_cmodel_async $CMODEL_DIR $TC(stdin) $TC(stdout) $CMODEL_OUT_FIXED $cmodel_log $TIMEOUT_SEC]
    if {$cmodel_pid eq ""} {
      puts "ERROR: C-model did not start for testcase $TC(name). See: $cmodel_log"
    } else {
      puts "INFO: C-model PID for $TC(name): $cmodel_pid"
    }

    after $CMODEL_START_DELAY_MS

    catch { stop }
    catch { close_sim }
    catch { reset_simulation -simset sim_1 }

    puts "INFO: Launching Post-Implementation Functional Simulation for $TC(name)"
    current_run -implementation [get_runs impl_1]
    current_fileset -simset [get_filesets sim_1]
    launch_simulation -simset sim_1 -mode post-implementation -type functional

    set sim_log [file join $SIM_LOG_DIR "sim_log_${TC(name)}.txt"]
    catch { file copy -force xsim.dir/xsim.log $sim_log }

    set verdict [_read_result_file $RESULT_FILE $PASS_PATTERN $FAIL_PATTERN]
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

  puts "\n==================== SUMMARY ===================="
  foreach r $results { puts $r }
  puts "------------------------------------------------"
  puts [format "PASSED : %d" $pass_count]
  puts [format "FAILED : %d" $fail_count]
  puts [format "UNKNOWN: %d" $unknown_count]
  puts "================================================"

  if {$fail_count > 0} { return 0 }
  return 1
}
