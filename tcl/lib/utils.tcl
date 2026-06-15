# ================================================================
# FPGA Automation Tool — Common Vivado Tcl Utilities
# LogicLance Compatible
#
# All procs prefixed with fpga_ to avoid namespace collisions.
# These procs read from config variables set by _vivado_config.tcl.
# ================================================================

# ──────────────── Error Handling ────────────────

proc fpga_die {msg} {
    puts stderr "ERROR: $msg"
    exit 1
}

proc fpga_nrm {p} {
    return [file normalize $p]
}

# ──────────────── Logging ────────────────

proc fpga_log_info {msg} {
    puts "INFO: $msg"
}

proc fpga_log_warn {msg} {
    puts "WARNING: $msg"
}

proc fpga_log_error {msg} {
    puts "ERROR: $msg"
}

# ──────────────── File Utilities ────────────────

proc fpga_rglob_ext {root exts} {
    # Recursively glob files matching given extensions
    set out {}
    if {![file isdirectory $root]} { return $out }
    foreach entry [glob -nocomplain -directory $root *] {
        if {[file isdirectory $entry]} {
            set out [concat $out [fpga_rglob_ext $entry $exts]]
        } else {
            set base [file tail $entry]
            foreach pat $exts {
                if {[string match $pat $base]} {
                    lappend out $entry
                    break
                }
            }
        }
    }
    return $out
}

proc fpga_rglob {root pats} {
    # Recursively glob files matching patterns against full path
    set out {}
    if {![file isdirectory $root]} { return $out }
    foreach e [glob -nocomplain -types {f d} -directory $root *] {
        if {[file isdirectory $e]} {
            set out [concat $out [fpga_rglob $e $pats]]
        } else {
            foreach p $pats {
                if {[string match $p $e]} {
                    lappend out $e
                    break
                }
            }
        }
    }
    return $out
}

proc fpga_file_contents_eq {path text} {
    if {![file exists $path]} { return 0 }
    set f [open $path r]; set cur [read $f]; close $f
    return [string equal $cur $text]
}

# ──────────────── HDL Module Scanner ────────────────

proc fpga_scan_modules {files} {
    # Parse HDL files to find module declarations
    set names {}
    foreach f $files {
        if {![file exists $f]} { continue }
        set ext [string tolower [file extension $f]]
        if {$ext ni {.v .sv .vh .svh}} { continue }
        set fh [open $f r]; set txt [read $fh]; close $fh
        foreach m [regexp -inline -all {(?m)^\s*module\s+([A-Za-z_][A-Za-z0-9_$]*)} $txt] {
            if {[regexp {module\s+([A-Za-z_][A-Za-z0-9_$]*)} $m -> nm]} {
                lappend names $nm
            }
        }
    }
    return [lsort -unique $names]
}

proc fpga_make_top_alias {real_top outpath} {
    # Generate a shim module aliasing 'top' to the real design top
    set fh [open $outpath w]
    puts $fh "// Auto-generated shim so TB can instantiate 'top' while real top is '$real_top'"
    puts $fh "module top(); $real_top dut(); endmodule"
    close $fh
}

# ──────────────── Result File Reader ────────────────

proc fpga_read_result_file {path pass_re fail_re} {
    # Returns: 1 = PASS, 0 = FAIL, -1 = UNKNOWN
    if {![file exists $path]} { return -1 }
    set fh [open $path r]
    set txt [string trim [read $fh]]
    close $fh
    if {[regexp -nocase -- $fail_re $txt]} { return 0 }
    if {[regexp -nocase -- $pass_re $txt]} { return 1 }
    return -1
}

# ──────────────── Shell Command Runner ────────────────

proc fpga_sh_run {cmd workdir logfile stdin_file stdout_file timeout_s} {
    # Run a shell command with sanitized environment, optional stdin/stdout, timeout
    if {![file isdirectory $workdir]} { fpga_die "Directory not found: $workdir" }
    set workdir   [fpga_nrm $workdir]
    set logfile   [fpga_nrm $logfile]
    set logdir    [file dirname $logfile]
    if {![file isdirectory $logdir]} { file mkdir $logdir }

    set wrap "cd [list $workdir] && "
    if {$timeout_s > 0} { append wrap "timeout --preserve-status ${timeout_s}s " }
    append wrap "stdbuf -oL -eL $cmd"

    # stdin
    if {[string length [string trim $stdin_file]]} {
        set stdin_file [fpga_nrm $stdin_file]
        if {![file exists $stdin_file]} { fpga_die "Stdin file not found: $stdin_file" }
        append wrap " < [list $stdin_file]"
    }

    # stdout capture
    if {[string length [string trim $stdout_file]]} {
        set stdout_file [fpga_nrm $stdout_file]
        set outdir [file dirname $stdout_file]
        if {![file isdirectory $outdir]} { file mkdir $outdir }
        append wrap " > [list $stdout_file] 2>&1"
    } else {
        append wrap " 2>&1 | tee -a [list $logfile]"
    }

    fpga_log_info "SHELL> $wrap"
    set rc [catch {exec /bin/sh -lc "$wrap"} out]
    puts $out
    if {$rc != 0} {
        puts stderr $out
        fpga_die "Shell command failed (rc=$rc). See log: $logfile"
    }
}

# ──────────────── Simulation Fileset Preparation ────────────────

proc fpga_prepare_sim {} {
    # Prepare the sim_1 fileset using config variables.
    # Expects: TB_TOP, TB_FILES or TB_DIR, TB_INCLUDES, TB_DEFINES

    global TB_TOP TB_FILES TB_DIR TB_INCLUDES TB_DEFINES

    # Create sim_1 if needed
    if {[string equal [get_filesets -quiet sim_1] ""]} {
        create_fileset -simset sim_1
    }

    # Close any open simulation
    catch { close_sim }

    # Clear existing files
    set _simfiles [get_files -quiet -of_objects [get_filesets sim_1]]
    if {[llength $_simfiles]} {
        remove_files -fileset sim_1 $_simfiles
    }

    # Collect TB files
    set _tb_add_list {}

    if {[info exists TB_DIR] && $TB_DIR ne ""} {
        # Auto-discover from directory
        if {![file isdirectory $TB_DIR]} { fpga_die "TB directory not found: $TB_DIR" }
        set tb_exts {*.sv *.svh *.v *.vh *.vhd *.vhdl}
        set auto_tbs [fpga_rglob_ext $TB_DIR $tb_exts]
        if {[llength $auto_tbs]} {
            foreach f $auto_tbs { lappend _tb_add_list [fpga_nrm $f] }
        } else {
            fpga_log_warn "No TB files found under $TB_DIR"
        }
    } elseif {[info exists TB_FILES] && [llength $TB_FILES]} {
        # Explicit file list
        foreach f $TB_FILES {
            if {![file exists $f]} { fpga_die "TB file not found: $f" }
            lappend _tb_add_list [fpga_nrm $f]
        }
    }

    if {[llength $_tb_add_list]} {
        add_files -fileset sim_1 $_tb_add_list
    }

    # Mark SystemVerilog files
    foreach f $_tb_add_list {
        if {[string match "*.sv" $f] || [string match "*.svh" $f]} {
            catch { set_property file_type {SystemVerilog} [get_files -of_objects [get_filesets sim_1] $f] }
        }
    }

    # Include directories
    if {[info exists TB_INCLUDES] && [llength $TB_INCLUDES]} {
        set incs {}
        foreach d $TB_INCLUDES {
            if {[file isdirectory $d]} { lappend incs [fpga_nrm $d] }
        }
        if {[llength $incs]} { set_property include_dirs $incs [get_filesets sim_1] }
    }

    # Verilog defines
    if {[info exists TB_DEFINES] && [llength $TB_DEFINES]} {
        set_property verilog_define $TB_DEFINES [get_filesets sim_1]
    }

    # Set TB top
    if {[info exists TB_TOP] && $TB_TOP ne ""} {
        set_property top $TB_TOP [get_filesets sim_1]
    }

    # Link to design sources
    catch { set_property SOURCE_SET sources_1 [get_filesets sim_1] }
    catch { set_property top_lib xil_defaultlib [get_filesets sim_1] }
    update_compile_order -fileset sim_1

    # XSIM settings
    set_property target_simulator XSIM [current_project]
    catch { set_property xsim.simulate.onfinish {quit} [get_filesets sim_1] }
    catch { set_property xsim.simulate.runtime {all} [get_filesets sim_1] }

    fpga_log_info "SIM TOP set to    : [get_property top [get_filesets sim_1]]"
    fpga_log_info "TB files in sim_1 : [llength [get_files -of_objects [get_filesets sim_1]]]"
}

# ──────────────── Async C-Model Launcher ────────────────

proc fpga_cmodel_async {workdir stdin_file pertest_out fixed_out logfile timeout_s} {
    # Launch C-model in background, return PID or "" on failure
    if {![file isdirectory $workdir]} { fpga_die "C-model dir not found: $workdir" }
    set workdir     [file normalize $workdir]
    set stdin_file  [file normalize $stdin_file]
    set pertest_out [file normalize $pertest_out]
    set fixed_out   [file normalize $fixed_out]
    set logfile     [file normalize $logfile]

    foreach d [list [file dirname $pertest_out] [file dirname $fixed_out] [file dirname $logfile]] {
        if {![file isdirectory $d]} { file mkdir $d }
    }
    if {![file exists $stdin_file]} { fpga_die "C-model stdin not found: $stdin_file" }

    set tools_dir [file join $workdir .sim_tools]
    if {![file isdirectory $tools_dir]} { file mkdir $tools_dir }
    set runner  [file join $tools_dir cmodel_run.sh]
    set pidfile [file join $tools_dir cmodel.pid]

    global CMODEL_CLEAN_TARGET CMODEL_BUILD_TARGETS CMODEL_RUN_TARGET
    set clean_tgt [expr {[info exists CMODEL_CLEAN_TARGET] ? $CMODEL_CLEAN_TARGET : "clean"}]
    set run_tgt   [expr {[info exists CMODEL_RUN_TARGET]   ? $CMODEL_RUN_TARGET   : "manual"}]

    # Build targets string
    set build_tgts ""
    if {[info exists CMODEL_BUILD_TARGETS] && [llength $CMODEL_BUILD_TARGETS]} {
        set build_tgts [join $CMODEL_BUILD_TARGETS " "]
    }

    set template "#!/bin/sh
set -eu
umask 022
cd \"$workdir\" || exit 97
: > \"$fixed_out\" || exit 98
: > \"$logfile\"   || true
: > \"$pertest_out\" || exit 99
make -k $clean_tgt >/dev/null 2>&1 || true
"

    if {$build_tgts ne ""} {
        append template "make $build_tgts 1>>\"$logfile\" 2>&1 || { echo 'ERROR: build failed' >> \"$logfile\"; exit 95; }\n"
    }

    append template "
if make -n $run_tgt >/dev/null 2>&1; then
  RUN_CMD=\"make $run_tgt < \\\"$stdin_file\\\" 2>&1\"
else
  RUN_CMD=\"./$run_tgt < \\\"$stdin_file\\\" 2>&1\"
fi
if command -v tee >/dev/null 2>&1; then
  ( nohup sh -c \"\$RUN_CMD\" \\
      | tee \"$fixed_out\" \\
      | tee -a \"$logfile\" \\
      > \"$pertest_out\" ) &
else
  ( nohup sh -c \"\$RUN_CMD\" > \"$fixed_out\" ) &
fi
pid=\$!
echo \"\$pid\" > \"$pidfile\"
exit 0
"
    if {![fpga_file_contents_eq $runner $template]} {
        set fh [open $runner w]; puts -nonewline $fh $template; close $fh
        file attributes $runner -permissions u+x,g+x,o+x
    }

    fpga_log_info "C-MODEL> launching via $runner"
    set rc [catch { exec $runner } msg]
    if {$rc != 0} {
        fpga_log_error "C-model runner failed to start: $msg"
        return ""
    }

    if {![file exists $pidfile]} { fpga_log_error "pidfile not created"; return "" }
    set pf [open $pidfile r]; set pid [string trim [read $pf]]; close $pf
    if {$pid eq ""} { fpga_log_error "pidfile empty"; return "" }
    return $pid
}

# ──────────────── Git Clone & Merge ────────────────

proc fpga_git_clone_merge {repo commit dest subdir} {
    # Clone repo at specific commit, merge files into dest directory
    if {[catch {exec /usr/bin/env -i PATH=/usr/bin:/bin:/usr/local/bin git --version} _]} {
        fpga_die "git not found in PATH"
    }

    set CWD [pwd]
    set TMP [file normalize [file join [pwd] "__git_tmp__[pid]"]]
    file delete -force $TMP
    file mkdir $TMP
    set CHECKOUT [file join $TMP repo]

    fpga_log_info "Cloning $repo ..."
    if {[catch {exec /usr/bin/env -i PATH=/usr/bin:/bin:/usr/local/bin HOME=$::env(HOME) \
        git clone --recurse-submodules --depth 1 --no-single-branch $repo $CHECKOUT >@ stdout 2>@ stderr} e]} {
        fpga_log_warn "Shallow clone failed, trying full clone..."
        if {[catch {exec /usr/bin/env -i PATH=/usr/bin:/bin:/usr/local/bin HOME=$::env(HOME) \
            git clone --recurse-submodules $repo $CHECKOUT >@ stdout 2>@ stderr} e2]} {
            file delete -force $TMP
            fpga_die "git clone failed:\n$e\n$e2"
        }
    }

    cd $CHECKOUT
    catch { exec git fetch --all --tags --prune >@ stdout 2>@ stderr }
    catch { exec git fetch --depth 1 origin $commit >@ stdout 2>@ stderr }
    if {[catch {exec git checkout $commit >@ stdout 2>@ stderr} e]} {
        cd $CWD; file delete -force $TMP
        fpga_die "git checkout $commit failed: $e"
    }
    catch { exec git submodule update --init --recursive >@ stdout 2>@ stderr }
    set SHA [string trim [exec git rev-parse HEAD]]
    cd $CWD

    set SRCROOT $CHECKOUT
    if {$subdir ne ""} {
        set SRCROOT [file normalize [file join $CHECKOUT $subdir]]
        if {![file isdirectory $SRCROOT]} {
            file delete -force $TMP
            fpga_die "Subdir not found in repo: $subdir"
        }
    }

    # Recursive merge copy
    fpga_copy_dir_merge $SRCROOT $dest

    file delete -force $TMP
    fpga_log_info "Git merged commit $SHA into $dest"
    return $SHA
}

proc fpga_copy_dir_merge {src dst} {
    if {![file isdirectory $dst]} { file mkdir $dst }
    foreach p [glob -nocomplain -directory $src *] {
        set base [file tail $p]
        if {$base eq ".git"} { continue }
        set tgt [file join $dst $base]
        if {[file isdirectory $p]} {
            fpga_copy_dir_merge $p $tgt
        } else {
            file copy -force $p $tgt
        }
    }
}

# ──────────────── Validate Path Helper ────────────────

proc fpga_validate_path {path desc} {
    if {$path eq ""} { fpga_die "$desc is not configured (empty path)." }
    if {![file exists $path]} { fpga_die "$desc not found: $path" }
}
