// Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
// Copyright 2022-2025 Advanced Micro Devices, Inc. All Rights Reserved.
// --------------------------------------------------------------------------------
// Tool Version: Vivado v.2025.2 (lin64) Build 6299465 Fri Nov 14 12:34:56 MST 2025
// Date        : Fri Jun 12 13:04:22 2026
// Host        : e2e-60-156 running 64-bit Ubuntu 22.04.5 LTS
// Command     : write_verilog -mode funcsim -nolib -force -file
//               /root/Desktop/LOG_FPGA/XSA_scripts/fpga_project1/fpga_project.sim/sim_1/impl/func/xsim/tb_adder_func_impl.v
// Design      : adder
// Purpose     : This verilog netlist is a functional simulation representation of the design and should not be modified
//               or synthesized. This netlist cannot be used for SDF annotated simulation.
// Device      : xc7z020clg400-1
// --------------------------------------------------------------------------------
`timescale 1 ps / 1 ps

(* ECO_CHECKSUM = "4503ad2b" *) 
(* NotValidForBitStream *)
(* \DesignAttr:ENABLE_NOC_NETLIST_VIEW  *) 
(* \DesignAttr:ENABLE_AIE_NETLIST_VIEW  *) 
module adder
   (clk,
    a,
    b,
    sum);
  input clk;
  input [31:0]a;
  input [31:0]b;
  output [31:0]sum;

  wire [31:0]a;
  wire [31:0]a_IBUF;
  wire [31:0]b;
  wire [31:0]b_IBUF;
  wire clk;
  wire clk_IBUF;
  wire clk_IBUF_BUFG;
  wire [31:0]p_0_in;
  wire [31:0]sum;
  wire \sum[11]_i_2_n_0 ;
  wire \sum[11]_i_3_n_0 ;
  wire \sum[11]_i_4_n_0 ;
  wire \sum[11]_i_5_n_0 ;
  wire \sum[15]_i_2_n_0 ;
  wire \sum[15]_i_3_n_0 ;
  wire \sum[15]_i_4_n_0 ;
  wire \sum[15]_i_5_n_0 ;
  wire \sum[19]_i_2_n_0 ;
  wire \sum[19]_i_3_n_0 ;
  wire \sum[19]_i_4_n_0 ;
  wire \sum[19]_i_5_n_0 ;
  wire \sum[23]_i_2_n_0 ;
  wire \sum[23]_i_3_n_0 ;
  wire \sum[23]_i_4_n_0 ;
  wire \sum[23]_i_5_n_0 ;
  wire \sum[27]_i_2_n_0 ;
  wire \sum[27]_i_3_n_0 ;
  wire \sum[27]_i_4_n_0 ;
  wire \sum[27]_i_5_n_0 ;
  wire \sum[31]_i_2_n_0 ;
  wire \sum[31]_i_3_n_0 ;
  wire \sum[31]_i_4_n_0 ;
  wire \sum[31]_i_5_n_0 ;
  wire \sum[3]_i_2_n_0 ;
  wire \sum[3]_i_3_n_0 ;
  wire \sum[3]_i_4_n_0 ;
  wire \sum[3]_i_5_n_0 ;
  wire \sum[7]_i_2_n_0 ;
  wire \sum[7]_i_3_n_0 ;
  wire \sum[7]_i_4_n_0 ;
  wire \sum[7]_i_5_n_0 ;
  wire [31:0]sum_OBUF;
  wire \sum_reg[11]_i_1_n_0 ;
  wire \sum_reg[15]_i_1_n_0 ;
  wire \sum_reg[19]_i_1_n_0 ;
  wire \sum_reg[23]_i_1_n_0 ;
  wire \sum_reg[27]_i_1_n_0 ;
  wire \sum_reg[3]_i_1_n_0 ;
  wire \sum_reg[7]_i_1_n_0 ;
  wire [2:0]\NLW_sum_reg[11]_i_1_CO_UNCONNECTED ;
  wire [2:0]\NLW_sum_reg[15]_i_1_CO_UNCONNECTED ;
  wire [2:0]\NLW_sum_reg[19]_i_1_CO_UNCONNECTED ;
  wire [2:0]\NLW_sum_reg[23]_i_1_CO_UNCONNECTED ;
  wire [2:0]\NLW_sum_reg[27]_i_1_CO_UNCONNECTED ;
  wire [3:0]\NLW_sum_reg[31]_i_1_CO_UNCONNECTED ;
  wire [2:0]\NLW_sum_reg[3]_i_1_CO_UNCONNECTED ;
  wire [2:0]\NLW_sum_reg[7]_i_1_CO_UNCONNECTED ;

  IBUF \a_IBUF[0]_inst 
       (.I(a[0]),
        .O(a_IBUF[0]));
  IBUF \a_IBUF[10]_inst 
       (.I(a[10]),
        .O(a_IBUF[10]));
  IBUF \a_IBUF[11]_inst 
       (.I(a[11]),
        .O(a_IBUF[11]));
  IBUF \a_IBUF[12]_inst 
       (.I(a[12]),
        .O(a_IBUF[12]));
  IBUF \a_IBUF[13]_inst 
       (.I(a[13]),
        .O(a_IBUF[13]));
  IBUF \a_IBUF[14]_inst 
       (.I(a[14]),
        .O(a_IBUF[14]));
  IBUF \a_IBUF[15]_inst 
       (.I(a[15]),
        .O(a_IBUF[15]));
  IBUF \a_IBUF[16]_inst 
       (.I(a[16]),
        .O(a_IBUF[16]));
  IBUF \a_IBUF[17]_inst 
       (.I(a[17]),
        .O(a_IBUF[17]));
  IBUF \a_IBUF[18]_inst 
       (.I(a[18]),
        .O(a_IBUF[18]));
  IBUF \a_IBUF[19]_inst 
       (.I(a[19]),
        .O(a_IBUF[19]));
  IBUF \a_IBUF[1]_inst 
       (.I(a[1]),
        .O(a_IBUF[1]));
  IBUF \a_IBUF[20]_inst 
       (.I(a[20]),
        .O(a_IBUF[20]));
  IBUF \a_IBUF[21]_inst 
       (.I(a[21]),
        .O(a_IBUF[21]));
  IBUF \a_IBUF[22]_inst 
       (.I(a[22]),
        .O(a_IBUF[22]));
  IBUF \a_IBUF[23]_inst 
       (.I(a[23]),
        .O(a_IBUF[23]));
  IBUF \a_IBUF[24]_inst 
       (.I(a[24]),
        .O(a_IBUF[24]));
  IBUF \a_IBUF[25]_inst 
       (.I(a[25]),
        .O(a_IBUF[25]));
  IBUF \a_IBUF[26]_inst 
       (.I(a[26]),
        .O(a_IBUF[26]));
  IBUF \a_IBUF[27]_inst 
       (.I(a[27]),
        .O(a_IBUF[27]));
  IBUF \a_IBUF[28]_inst 
       (.I(a[28]),
        .O(a_IBUF[28]));
  IBUF \a_IBUF[29]_inst 
       (.I(a[29]),
        .O(a_IBUF[29]));
  IBUF \a_IBUF[2]_inst 
       (.I(a[2]),
        .O(a_IBUF[2]));
  IBUF \a_IBUF[30]_inst 
       (.I(a[30]),
        .O(a_IBUF[30]));
  IBUF \a_IBUF[31]_inst 
       (.I(a[31]),
        .O(a_IBUF[31]));
  IBUF \a_IBUF[3]_inst 
       (.I(a[3]),
        .O(a_IBUF[3]));
  IBUF \a_IBUF[4]_inst 
       (.I(a[4]),
        .O(a_IBUF[4]));
  IBUF \a_IBUF[5]_inst 
       (.I(a[5]),
        .O(a_IBUF[5]));
  IBUF \a_IBUF[6]_inst 
       (.I(a[6]),
        .O(a_IBUF[6]));
  IBUF \a_IBUF[7]_inst 
       (.I(a[7]),
        .O(a_IBUF[7]));
  IBUF \a_IBUF[8]_inst 
       (.I(a[8]),
        .O(a_IBUF[8]));
  IBUF \a_IBUF[9]_inst 
       (.I(a[9]),
        .O(a_IBUF[9]));
  IBUF \b_IBUF[0]_inst 
       (.I(b[0]),
        .O(b_IBUF[0]));
  IBUF \b_IBUF[10]_inst 
       (.I(b[10]),
        .O(b_IBUF[10]));
  IBUF \b_IBUF[11]_inst 
       (.I(b[11]),
        .O(b_IBUF[11]));
  IBUF \b_IBUF[12]_inst 
       (.I(b[12]),
        .O(b_IBUF[12]));
  IBUF \b_IBUF[13]_inst 
       (.I(b[13]),
        .O(b_IBUF[13]));
  IBUF \b_IBUF[14]_inst 
       (.I(b[14]),
        .O(b_IBUF[14]));
  IBUF \b_IBUF[15]_inst 
       (.I(b[15]),
        .O(b_IBUF[15]));
  IBUF \b_IBUF[16]_inst 
       (.I(b[16]),
        .O(b_IBUF[16]));
  IBUF \b_IBUF[17]_inst 
       (.I(b[17]),
        .O(b_IBUF[17]));
  IBUF \b_IBUF[18]_inst 
       (.I(b[18]),
        .O(b_IBUF[18]));
  IBUF \b_IBUF[19]_inst 
       (.I(b[19]),
        .O(b_IBUF[19]));
  IBUF \b_IBUF[1]_inst 
       (.I(b[1]),
        .O(b_IBUF[1]));
  IBUF \b_IBUF[20]_inst 
       (.I(b[20]),
        .O(b_IBUF[20]));
  IBUF \b_IBUF[21]_inst 
       (.I(b[21]),
        .O(b_IBUF[21]));
  IBUF \b_IBUF[22]_inst 
       (.I(b[22]),
        .O(b_IBUF[22]));
  IBUF \b_IBUF[23]_inst 
       (.I(b[23]),
        .O(b_IBUF[23]));
  IBUF \b_IBUF[24]_inst 
       (.I(b[24]),
        .O(b_IBUF[24]));
  IBUF \b_IBUF[25]_inst 
       (.I(b[25]),
        .O(b_IBUF[25]));
  IBUF \b_IBUF[26]_inst 
       (.I(b[26]),
        .O(b_IBUF[26]));
  IBUF \b_IBUF[27]_inst 
       (.I(b[27]),
        .O(b_IBUF[27]));
  IBUF \b_IBUF[28]_inst 
       (.I(b[28]),
        .O(b_IBUF[28]));
  IBUF \b_IBUF[29]_inst 
       (.I(b[29]),
        .O(b_IBUF[29]));
  IBUF \b_IBUF[2]_inst 
       (.I(b[2]),
        .O(b_IBUF[2]));
  IBUF \b_IBUF[30]_inst 
       (.I(b[30]),
        .O(b_IBUF[30]));
  IBUF \b_IBUF[31]_inst 
       (.I(b[31]),
        .O(b_IBUF[31]));
  IBUF \b_IBUF[3]_inst 
       (.I(b[3]),
        .O(b_IBUF[3]));
  IBUF \b_IBUF[4]_inst 
       (.I(b[4]),
        .O(b_IBUF[4]));
  IBUF \b_IBUF[5]_inst 
       (.I(b[5]),
        .O(b_IBUF[5]));
  IBUF \b_IBUF[6]_inst 
       (.I(b[6]),
        .O(b_IBUF[6]));
  IBUF \b_IBUF[7]_inst 
       (.I(b[7]),
        .O(b_IBUF[7]));
  IBUF \b_IBUF[8]_inst 
       (.I(b[8]),
        .O(b_IBUF[8]));
  IBUF \b_IBUF[9]_inst 
       (.I(b[9]),
        .O(b_IBUF[9]));
  BUFG clk_IBUF_BUFG_inst
       (.I(clk_IBUF),
        .O(clk_IBUF_BUFG));
  IBUF clk_IBUF_inst
       (.I(clk),
        .O(clk_IBUF));
  LUT2 #(
    .INIT(4'h6)) 
    \sum[11]_i_2 
       (.I0(a_IBUF[11]),
        .I1(b_IBUF[11]),
        .O(\sum[11]_i_2_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \sum[11]_i_3 
       (.I0(a_IBUF[10]),
        .I1(b_IBUF[10]),
        .O(\sum[11]_i_3_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \sum[11]_i_4 
       (.I0(a_IBUF[9]),
        .I1(b_IBUF[9]),
        .O(\sum[11]_i_4_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \sum[11]_i_5 
       (.I0(a_IBUF[8]),
        .I1(b_IBUF[8]),
        .O(\sum[11]_i_5_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \sum[15]_i_2 
       (.I0(a_IBUF[15]),
        .I1(b_IBUF[15]),
        .O(\sum[15]_i_2_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \sum[15]_i_3 
       (.I0(a_IBUF[14]),
        .I1(b_IBUF[14]),
        .O(\sum[15]_i_3_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \sum[15]_i_4 
       (.I0(a_IBUF[13]),
        .I1(b_IBUF[13]),
        .O(\sum[15]_i_4_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \sum[15]_i_5 
       (.I0(a_IBUF[12]),
        .I1(b_IBUF[12]),
        .O(\sum[15]_i_5_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \sum[19]_i_2 
       (.I0(a_IBUF[19]),
        .I1(b_IBUF[19]),
        .O(\sum[19]_i_2_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \sum[19]_i_3 
       (.I0(a_IBUF[18]),
        .I1(b_IBUF[18]),
        .O(\sum[19]_i_3_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \sum[19]_i_4 
       (.I0(a_IBUF[17]),
        .I1(b_IBUF[17]),
        .O(\sum[19]_i_4_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \sum[19]_i_5 
       (.I0(a_IBUF[16]),
        .I1(b_IBUF[16]),
        .O(\sum[19]_i_5_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \sum[23]_i_2 
       (.I0(a_IBUF[23]),
        .I1(b_IBUF[23]),
        .O(\sum[23]_i_2_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \sum[23]_i_3 
       (.I0(a_IBUF[22]),
        .I1(b_IBUF[22]),
        .O(\sum[23]_i_3_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \sum[23]_i_4 
       (.I0(a_IBUF[21]),
        .I1(b_IBUF[21]),
        .O(\sum[23]_i_4_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \sum[23]_i_5 
       (.I0(a_IBUF[20]),
        .I1(b_IBUF[20]),
        .O(\sum[23]_i_5_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \sum[27]_i_2 
       (.I0(a_IBUF[27]),
        .I1(b_IBUF[27]),
        .O(\sum[27]_i_2_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \sum[27]_i_3 
       (.I0(a_IBUF[26]),
        .I1(b_IBUF[26]),
        .O(\sum[27]_i_3_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \sum[27]_i_4 
       (.I0(a_IBUF[25]),
        .I1(b_IBUF[25]),
        .O(\sum[27]_i_4_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \sum[27]_i_5 
       (.I0(a_IBUF[24]),
        .I1(b_IBUF[24]),
        .O(\sum[27]_i_5_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \sum[31]_i_2 
       (.I0(a_IBUF[31]),
        .I1(b_IBUF[31]),
        .O(\sum[31]_i_2_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \sum[31]_i_3 
       (.I0(a_IBUF[30]),
        .I1(b_IBUF[30]),
        .O(\sum[31]_i_3_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \sum[31]_i_4 
       (.I0(a_IBUF[29]),
        .I1(b_IBUF[29]),
        .O(\sum[31]_i_4_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \sum[31]_i_5 
       (.I0(a_IBUF[28]),
        .I1(b_IBUF[28]),
        .O(\sum[31]_i_5_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \sum[3]_i_2 
       (.I0(a_IBUF[3]),
        .I1(b_IBUF[3]),
        .O(\sum[3]_i_2_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \sum[3]_i_3 
       (.I0(a_IBUF[2]),
        .I1(b_IBUF[2]),
        .O(\sum[3]_i_3_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \sum[3]_i_4 
       (.I0(a_IBUF[1]),
        .I1(b_IBUF[1]),
        .O(\sum[3]_i_4_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \sum[3]_i_5 
       (.I0(a_IBUF[0]),
        .I1(b_IBUF[0]),
        .O(\sum[3]_i_5_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \sum[7]_i_2 
       (.I0(a_IBUF[7]),
        .I1(b_IBUF[7]),
        .O(\sum[7]_i_2_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \sum[7]_i_3 
       (.I0(a_IBUF[6]),
        .I1(b_IBUF[6]),
        .O(\sum[7]_i_3_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \sum[7]_i_4 
       (.I0(a_IBUF[5]),
        .I1(b_IBUF[5]),
        .O(\sum[7]_i_4_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \sum[7]_i_5 
       (.I0(a_IBUF[4]),
        .I1(b_IBUF[4]),
        .O(\sum[7]_i_5_n_0 ));
  OBUF \sum_OBUF[0]_inst 
       (.I(sum_OBUF[0]),
        .O(sum[0]));
  OBUF \sum_OBUF[10]_inst 
       (.I(sum_OBUF[10]),
        .O(sum[10]));
  OBUF \sum_OBUF[11]_inst 
       (.I(sum_OBUF[11]),
        .O(sum[11]));
  OBUF \sum_OBUF[12]_inst 
       (.I(sum_OBUF[12]),
        .O(sum[12]));
  OBUF \sum_OBUF[13]_inst 
       (.I(sum_OBUF[13]),
        .O(sum[13]));
  OBUF \sum_OBUF[14]_inst 
       (.I(sum_OBUF[14]),
        .O(sum[14]));
  OBUF \sum_OBUF[15]_inst 
       (.I(sum_OBUF[15]),
        .O(sum[15]));
  OBUF \sum_OBUF[16]_inst 
       (.I(sum_OBUF[16]),
        .O(sum[16]));
  OBUF \sum_OBUF[17]_inst 
       (.I(sum_OBUF[17]),
        .O(sum[17]));
  OBUF \sum_OBUF[18]_inst 
       (.I(sum_OBUF[18]),
        .O(sum[18]));
  OBUF \sum_OBUF[19]_inst 
       (.I(sum_OBUF[19]),
        .O(sum[19]));
  OBUF \sum_OBUF[1]_inst 
       (.I(sum_OBUF[1]),
        .O(sum[1]));
  OBUF \sum_OBUF[20]_inst 
       (.I(sum_OBUF[20]),
        .O(sum[20]));
  OBUF \sum_OBUF[21]_inst 
       (.I(sum_OBUF[21]),
        .O(sum[21]));
  OBUF \sum_OBUF[22]_inst 
       (.I(sum_OBUF[22]),
        .O(sum[22]));
  OBUF \sum_OBUF[23]_inst 
       (.I(sum_OBUF[23]),
        .O(sum[23]));
  OBUF \sum_OBUF[24]_inst 
       (.I(sum_OBUF[24]),
        .O(sum[24]));
  OBUF \sum_OBUF[25]_inst 
       (.I(sum_OBUF[25]),
        .O(sum[25]));
  OBUF \sum_OBUF[26]_inst 
       (.I(sum_OBUF[26]),
        .O(sum[26]));
  OBUF \sum_OBUF[27]_inst 
       (.I(sum_OBUF[27]),
        .O(sum[27]));
  OBUF \sum_OBUF[28]_inst 
       (.I(sum_OBUF[28]),
        .O(sum[28]));
  OBUF \sum_OBUF[29]_inst 
       (.I(sum_OBUF[29]),
        .O(sum[29]));
  OBUF \sum_OBUF[2]_inst 
       (.I(sum_OBUF[2]),
        .O(sum[2]));
  OBUF \sum_OBUF[30]_inst 
       (.I(sum_OBUF[30]),
        .O(sum[30]));
  OBUF \sum_OBUF[31]_inst 
       (.I(sum_OBUF[31]),
        .O(sum[31]));
  OBUF \sum_OBUF[3]_inst 
       (.I(sum_OBUF[3]),
        .O(sum[3]));
  OBUF \sum_OBUF[4]_inst 
       (.I(sum_OBUF[4]),
        .O(sum[4]));
  OBUF \sum_OBUF[5]_inst 
       (.I(sum_OBUF[5]),
        .O(sum[5]));
  OBUF \sum_OBUF[6]_inst 
       (.I(sum_OBUF[6]),
        .O(sum[6]));
  OBUF \sum_OBUF[7]_inst 
       (.I(sum_OBUF[7]),
        .O(sum[7]));
  OBUF \sum_OBUF[8]_inst 
       (.I(sum_OBUF[8]),
        .O(sum[8]));
  OBUF \sum_OBUF[9]_inst 
       (.I(sum_OBUF[9]),
        .O(sum[9]));
  FDRE #(
    .INIT(1'b0)) 
    \sum_reg[0] 
       (.C(clk_IBUF_BUFG),
        .CE(1'b1),
        .D(p_0_in[0]),
        .Q(sum_OBUF[0]),
        .R(1'b0));
  FDRE #(
    .INIT(1'b0)) 
    \sum_reg[10] 
       (.C(clk_IBUF_BUFG),
        .CE(1'b1),
        .D(p_0_in[10]),
        .Q(sum_OBUF[10]),
        .R(1'b0));
  FDRE #(
    .INIT(1'b0)) 
    \sum_reg[11] 
       (.C(clk_IBUF_BUFG),
        .CE(1'b1),
        .D(p_0_in[11]),
        .Q(sum_OBUF[11]),
        .R(1'b0));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \sum_reg[11]_i_1 
       (.CI(\sum_reg[7]_i_1_n_0 ),
        .CO({\sum_reg[11]_i_1_n_0 ,\NLW_sum_reg[11]_i_1_CO_UNCONNECTED [2:0]}),
        .CYINIT(1'b0),
        .DI(a_IBUF[11:8]),
        .O(p_0_in[11:8]),
        .S({\sum[11]_i_2_n_0 ,\sum[11]_i_3_n_0 ,\sum[11]_i_4_n_0 ,\sum[11]_i_5_n_0 }));
  FDRE #(
    .INIT(1'b0)) 
    \sum_reg[12] 
       (.C(clk_IBUF_BUFG),
        .CE(1'b1),
        .D(p_0_in[12]),
        .Q(sum_OBUF[12]),
        .R(1'b0));
  FDRE #(
    .INIT(1'b0)) 
    \sum_reg[13] 
       (.C(clk_IBUF_BUFG),
        .CE(1'b1),
        .D(p_0_in[13]),
        .Q(sum_OBUF[13]),
        .R(1'b0));
  FDRE #(
    .INIT(1'b0)) 
    \sum_reg[14] 
       (.C(clk_IBUF_BUFG),
        .CE(1'b1),
        .D(p_0_in[14]),
        .Q(sum_OBUF[14]),
        .R(1'b0));
  FDRE #(
    .INIT(1'b0)) 
    \sum_reg[15] 
       (.C(clk_IBUF_BUFG),
        .CE(1'b1),
        .D(p_0_in[15]),
        .Q(sum_OBUF[15]),
        .R(1'b0));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \sum_reg[15]_i_1 
       (.CI(\sum_reg[11]_i_1_n_0 ),
        .CO({\sum_reg[15]_i_1_n_0 ,\NLW_sum_reg[15]_i_1_CO_UNCONNECTED [2:0]}),
        .CYINIT(1'b0),
        .DI(a_IBUF[15:12]),
        .O(p_0_in[15:12]),
        .S({\sum[15]_i_2_n_0 ,\sum[15]_i_3_n_0 ,\sum[15]_i_4_n_0 ,\sum[15]_i_5_n_0 }));
  FDRE #(
    .INIT(1'b0)) 
    \sum_reg[16] 
       (.C(clk_IBUF_BUFG),
        .CE(1'b1),
        .D(p_0_in[16]),
        .Q(sum_OBUF[16]),
        .R(1'b0));
  FDRE #(
    .INIT(1'b0)) 
    \sum_reg[17] 
       (.C(clk_IBUF_BUFG),
        .CE(1'b1),
        .D(p_0_in[17]),
        .Q(sum_OBUF[17]),
        .R(1'b0));
  FDRE #(
    .INIT(1'b0)) 
    \sum_reg[18] 
       (.C(clk_IBUF_BUFG),
        .CE(1'b1),
        .D(p_0_in[18]),
        .Q(sum_OBUF[18]),
        .R(1'b0));
  FDRE #(
    .INIT(1'b0)) 
    \sum_reg[19] 
       (.C(clk_IBUF_BUFG),
        .CE(1'b1),
        .D(p_0_in[19]),
        .Q(sum_OBUF[19]),
        .R(1'b0));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \sum_reg[19]_i_1 
       (.CI(\sum_reg[15]_i_1_n_0 ),
        .CO({\sum_reg[19]_i_1_n_0 ,\NLW_sum_reg[19]_i_1_CO_UNCONNECTED [2:0]}),
        .CYINIT(1'b0),
        .DI(a_IBUF[19:16]),
        .O(p_0_in[19:16]),
        .S({\sum[19]_i_2_n_0 ,\sum[19]_i_3_n_0 ,\sum[19]_i_4_n_0 ,\sum[19]_i_5_n_0 }));
  FDRE #(
    .INIT(1'b0)) 
    \sum_reg[1] 
       (.C(clk_IBUF_BUFG),
        .CE(1'b1),
        .D(p_0_in[1]),
        .Q(sum_OBUF[1]),
        .R(1'b0));
  FDRE #(
    .INIT(1'b0)) 
    \sum_reg[20] 
       (.C(clk_IBUF_BUFG),
        .CE(1'b1),
        .D(p_0_in[20]),
        .Q(sum_OBUF[20]),
        .R(1'b0));
  FDRE #(
    .INIT(1'b0)) 
    \sum_reg[21] 
       (.C(clk_IBUF_BUFG),
        .CE(1'b1),
        .D(p_0_in[21]),
        .Q(sum_OBUF[21]),
        .R(1'b0));
  FDRE #(
    .INIT(1'b0)) 
    \sum_reg[22] 
       (.C(clk_IBUF_BUFG),
        .CE(1'b1),
        .D(p_0_in[22]),
        .Q(sum_OBUF[22]),
        .R(1'b0));
  FDRE #(
    .INIT(1'b0)) 
    \sum_reg[23] 
       (.C(clk_IBUF_BUFG),
        .CE(1'b1),
        .D(p_0_in[23]),
        .Q(sum_OBUF[23]),
        .R(1'b0));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \sum_reg[23]_i_1 
       (.CI(\sum_reg[19]_i_1_n_0 ),
        .CO({\sum_reg[23]_i_1_n_0 ,\NLW_sum_reg[23]_i_1_CO_UNCONNECTED [2:0]}),
        .CYINIT(1'b0),
        .DI(a_IBUF[23:20]),
        .O(p_0_in[23:20]),
        .S({\sum[23]_i_2_n_0 ,\sum[23]_i_3_n_0 ,\sum[23]_i_4_n_0 ,\sum[23]_i_5_n_0 }));
  FDRE #(
    .INIT(1'b0)) 
    \sum_reg[24] 
       (.C(clk_IBUF_BUFG),
        .CE(1'b1),
        .D(p_0_in[24]),
        .Q(sum_OBUF[24]),
        .R(1'b0));
  FDRE #(
    .INIT(1'b0)) 
    \sum_reg[25] 
       (.C(clk_IBUF_BUFG),
        .CE(1'b1),
        .D(p_0_in[25]),
        .Q(sum_OBUF[25]),
        .R(1'b0));
  FDRE #(
    .INIT(1'b0)) 
    \sum_reg[26] 
       (.C(clk_IBUF_BUFG),
        .CE(1'b1),
        .D(p_0_in[26]),
        .Q(sum_OBUF[26]),
        .R(1'b0));
  FDRE #(
    .INIT(1'b0)) 
    \sum_reg[27] 
       (.C(clk_IBUF_BUFG),
        .CE(1'b1),
        .D(p_0_in[27]),
        .Q(sum_OBUF[27]),
        .R(1'b0));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \sum_reg[27]_i_1 
       (.CI(\sum_reg[23]_i_1_n_0 ),
        .CO({\sum_reg[27]_i_1_n_0 ,\NLW_sum_reg[27]_i_1_CO_UNCONNECTED [2:0]}),
        .CYINIT(1'b0),
        .DI(a_IBUF[27:24]),
        .O(p_0_in[27:24]),
        .S({\sum[27]_i_2_n_0 ,\sum[27]_i_3_n_0 ,\sum[27]_i_4_n_0 ,\sum[27]_i_5_n_0 }));
  FDRE #(
    .INIT(1'b0)) 
    \sum_reg[28] 
       (.C(clk_IBUF_BUFG),
        .CE(1'b1),
        .D(p_0_in[28]),
        .Q(sum_OBUF[28]),
        .R(1'b0));
  FDRE #(
    .INIT(1'b0)) 
    \sum_reg[29] 
       (.C(clk_IBUF_BUFG),
        .CE(1'b1),
        .D(p_0_in[29]),
        .Q(sum_OBUF[29]),
        .R(1'b0));
  FDRE #(
    .INIT(1'b0)) 
    \sum_reg[2] 
       (.C(clk_IBUF_BUFG),
        .CE(1'b1),
        .D(p_0_in[2]),
        .Q(sum_OBUF[2]),
        .R(1'b0));
  FDRE #(
    .INIT(1'b0)) 
    \sum_reg[30] 
       (.C(clk_IBUF_BUFG),
        .CE(1'b1),
        .D(p_0_in[30]),
        .Q(sum_OBUF[30]),
        .R(1'b0));
  FDRE #(
    .INIT(1'b0)) 
    \sum_reg[31] 
       (.C(clk_IBUF_BUFG),
        .CE(1'b1),
        .D(p_0_in[31]),
        .Q(sum_OBUF[31]),
        .R(1'b0));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \sum_reg[31]_i_1 
       (.CI(\sum_reg[27]_i_1_n_0 ),
        .CO(\NLW_sum_reg[31]_i_1_CO_UNCONNECTED [3:0]),
        .CYINIT(1'b0),
        .DI({1'b0,a_IBUF[30:28]}),
        .O(p_0_in[31:28]),
        .S({\sum[31]_i_2_n_0 ,\sum[31]_i_3_n_0 ,\sum[31]_i_4_n_0 ,\sum[31]_i_5_n_0 }));
  FDRE #(
    .INIT(1'b0)) 
    \sum_reg[3] 
       (.C(clk_IBUF_BUFG),
        .CE(1'b1),
        .D(p_0_in[3]),
        .Q(sum_OBUF[3]),
        .R(1'b0));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \sum_reg[3]_i_1 
       (.CI(1'b0),
        .CO({\sum_reg[3]_i_1_n_0 ,\NLW_sum_reg[3]_i_1_CO_UNCONNECTED [2:0]}),
        .CYINIT(1'b0),
        .DI(a_IBUF[3:0]),
        .O(p_0_in[3:0]),
        .S({\sum[3]_i_2_n_0 ,\sum[3]_i_3_n_0 ,\sum[3]_i_4_n_0 ,\sum[3]_i_5_n_0 }));
  FDRE #(
    .INIT(1'b0)) 
    \sum_reg[4] 
       (.C(clk_IBUF_BUFG),
        .CE(1'b1),
        .D(p_0_in[4]),
        .Q(sum_OBUF[4]),
        .R(1'b0));
  FDRE #(
    .INIT(1'b0)) 
    \sum_reg[5] 
       (.C(clk_IBUF_BUFG),
        .CE(1'b1),
        .D(p_0_in[5]),
        .Q(sum_OBUF[5]),
        .R(1'b0));
  FDRE #(
    .INIT(1'b0)) 
    \sum_reg[6] 
       (.C(clk_IBUF_BUFG),
        .CE(1'b1),
        .D(p_0_in[6]),
        .Q(sum_OBUF[6]),
        .R(1'b0));
  FDRE #(
    .INIT(1'b0)) 
    \sum_reg[7] 
       (.C(clk_IBUF_BUFG),
        .CE(1'b1),
        .D(p_0_in[7]),
        .Q(sum_OBUF[7]),
        .R(1'b0));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \sum_reg[7]_i_1 
       (.CI(\sum_reg[3]_i_1_n_0 ),
        .CO({\sum_reg[7]_i_1_n_0 ,\NLW_sum_reg[7]_i_1_CO_UNCONNECTED [2:0]}),
        .CYINIT(1'b0),
        .DI(a_IBUF[7:4]),
        .O(p_0_in[7:4]),
        .S({\sum[7]_i_2_n_0 ,\sum[7]_i_3_n_0 ,\sum[7]_i_4_n_0 ,\sum[7]_i_5_n_0 }));
  FDRE #(
    .INIT(1'b0)) 
    \sum_reg[8] 
       (.C(clk_IBUF_BUFG),
        .CE(1'b1),
        .D(p_0_in[8]),
        .Q(sum_OBUF[8]),
        .R(1'b0));
  FDRE #(
    .INIT(1'b0)) 
    \sum_reg[9] 
       (.C(clk_IBUF_BUFG),
        .CE(1'b1),
        .D(p_0_in[9]),
        .Q(sum_OBUF[9]),
        .R(1'b0));
endmodule
`ifndef GLBL
`define GLBL
`timescale  1 ps / 1 ps

module glbl ();

    parameter ROC_WIDTH = 100000;
    parameter TOC_WIDTH = 0;
    parameter GRES_WIDTH = 10000;
    parameter GRES_START = 10000;

//--------   STARTUP Globals --------------
    wire GSR;
    wire GTS;
    wire GWE;
    wire PRLD;
    wire GRESTORE;
    tri1 p_up_tmp;
    tri (weak1, strong0) PLL_LOCKG = p_up_tmp;

    wire PROGB_GLBL;
    wire CCLKO_GLBL;
    wire FCSBO_GLBL;
    wire [3:0] DO_GLBL;
    wire [3:0] DI_GLBL;
   
    reg GSR_int;
    reg GTS_int;
    reg PRLD_int;
    reg GRESTORE_int;

//--------   JTAG Globals --------------
    wire JTAG_TDO_GLBL;
    wire JTAG_TCK_GLBL;
    wire JTAG_TDI_GLBL;
    wire JTAG_TMS_GLBL;
    wire JTAG_TRST_GLBL;

    reg JTAG_CAPTURE_GLBL;
    reg JTAG_RESET_GLBL;
    reg JTAG_SHIFT_GLBL;
    reg JTAG_UPDATE_GLBL;
    reg JTAG_RUNTEST_GLBL;

    reg JTAG_SEL1_GLBL = 0;
    reg JTAG_SEL2_GLBL = 0 ;
    reg JTAG_SEL3_GLBL = 0;
    reg JTAG_SEL4_GLBL = 0;

    reg JTAG_USER_TDO1_GLBL = 1'bz;
    reg JTAG_USER_TDO2_GLBL = 1'bz;
    reg JTAG_USER_TDO3_GLBL = 1'bz;
    reg JTAG_USER_TDO4_GLBL = 1'bz;

    assign (strong1, weak0) GSR = GSR_int;
    assign (strong1, weak0) GTS = GTS_int;
    assign (weak1, weak0) PRLD = PRLD_int;
    assign (strong1, weak0) GRESTORE = GRESTORE_int;

    initial begin
	GSR_int = 1'b1;
	PRLD_int = 1'b1;
	#(ROC_WIDTH)
	GSR_int = 1'b0;
	PRLD_int = 1'b0;
    end

    initial begin
	GTS_int = 1'b1;
	#(TOC_WIDTH)
	GTS_int = 1'b0;
    end

    initial begin 
	GRESTORE_int = 1'b0;
	#(GRES_START);
	GRESTORE_int = 1'b1;
	#(GRES_WIDTH);
	GRESTORE_int = 1'b0;
    end

endmodule
`endif
