#!/bin/sh
set -eu
umask 022
cd "/root/Desktop/LOG_FPGA/XSA_scripts1/sample_testcase/c_model" || exit 97
: > "/tmp/fpga_cmodel_golden.txt" || exit 98
: > "/root/Desktop/LOG_FPGA/XSA_scripts1/output/cmodel_logs/cmodel_run_TC2.log"   || true
: > "/tmp/tc2_out.txt" || exit 99
make -k clean >/dev/null 2>&1 || true

if make -n manual >/dev/null 2>&1; then
  RUN_CMD="make manual < \"/root/Desktop/LOG_FPGA/XSA_scripts1/sample_testcase/test_cases/tc2_input.txt\" 2>&1"
else
  RUN_CMD="./manual < \"/root/Desktop/LOG_FPGA/XSA_scripts1/sample_testcase/test_cases/tc2_input.txt\" 2>&1"
fi
if command -v tee >/dev/null 2>&1; then
  ( nohup sh -c "$RUN_CMD" \
      | tee "/tmp/fpga_cmodel_golden.txt" \
      | tee -a "/root/Desktop/LOG_FPGA/XSA_scripts1/output/cmodel_logs/cmodel_run_TC2.log" \
      > "/tmp/tc2_out.txt" ) &
else
  ( nohup sh -c "$RUN_CMD" > "/tmp/fpga_cmodel_golden.txt" ) &
fi
pid=$!
echo "$pid" > "/root/Desktop/LOG_FPGA/XSA_scripts1/sample_testcase/c_model/.sim_tools/cmodel.pid"
exit 0
