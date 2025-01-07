// Copyright 1986-2019 Xilinx, Inc. All Rights Reserved.
// --------------------------------------------------------------------------------
// Tool Version: Vivado v.2019.2 (win64) Build 2708876 Wed Nov  6 21:40:23 MST 2019
// Date        : Wed Nov 20 10:37:02 2024
// Host        : DESKTOP-3GJBP8L running 64-bit major release  (build 9200)
// Command     : write_verilog -force -mode synth_stub f:/qbit/qubit_1.0/RISCQv1.1/ip_repos/vio_0/vio_0_stub.v
// Design      : vio_0
// Purpose     : Stub declaration of top-level module interface
// Device      : xcku060-ffva1156-2-i
// --------------------------------------------------------------------------------

// This empty module with port declaration file causes synthesis tools to infer a black box for IP.
// The synthesis directives are for Synopsys Synplify support to prevent IO buffer insertion.
// Please paste the declaration into a Verilog source file or add the file as an additional source.
(* X_CORE_INFO = "vio,Vivado 2019.2" *)
module vio_0(clk, probe_in0, probe_out0, probe_out1, 
  probe_out2, probe_out3, probe_out4, probe_out5, probe_out6)
/* synthesis syn_black_box black_box_pad_pin="clk,probe_in0[31:0],probe_out0[0:0],probe_out1[0:0],probe_out2[0:0],probe_out3[31:0],probe_out4[31:0],probe_out5[2:0],probe_out6[5:0]" */;
  input clk;
  input [31:0]probe_in0;
  output [0:0]probe_out0;
  output [0:0]probe_out1;
  output [0:0]probe_out2;
  output [31:0]probe_out3;
  output [31:0]probe_out4;
  output [2:0]probe_out5;
  output [5:0]probe_out6;
endmodule
