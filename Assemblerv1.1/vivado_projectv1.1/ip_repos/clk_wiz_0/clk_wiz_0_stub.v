// Copyright 1986-2019 Xilinx, Inc. All Rights Reserved.
// --------------------------------------------------------------------------------
// Tool Version: Vivado v.2019.2 (win64) Build 2708876 Wed Nov  6 21:40:23 MST 2019
// Date        : Wed Nov 20 09:54:54 2024
// Host        : DESKTOP-3GJBP8L running 64-bit major release  (build 9200)
// Command     : write_verilog -force -mode synth_stub f:/qbit/qubit_1.0/RISCQv1.1/ip_repos/clk_wiz_0/clk_wiz_0_stub.v
// Design      : clk_wiz_0
// Purpose     : Stub declaration of top-level module interface
// Device      : xcku060-ffva1156-2-i
// --------------------------------------------------------------------------------

// This empty module with port declaration file causes synthesis tools to infer a black box for IP.
// The synthesis directives are for Synopsys Synplify support to prevent IO buffer insertion.
// Please paste the declaration into a Verilog source file or add the file as an additional source.
module clk_wiz_0(clk_200m, clk_20m, locked, clk_in1_p, clk_in1_n)
/* synthesis syn_black_box black_box_pad_pin="clk_200m,clk_20m,locked,clk_in1_p,clk_in1_n" */;
  output clk_200m;
  output clk_20m;
  output locked;
  input clk_in1_p;
  input clk_in1_n;
endmodule
