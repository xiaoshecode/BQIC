`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2024/11/19 20:36:21
// Design Name: 
// Module Name: riscq_init_tb
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////


module riscq_init_tb();

reg             i_clk           ;
reg             i_rst           ;
reg             i_cpu_rst       ;
reg     [31:0]  i_data          ;
reg             i_data_valid    ;

wire    [11:0]  o_inst_waddr    ;
wire    [31:0]  o_inst_wdata    ;
wire            o_inst_we       ;
wire            o_inst_init_done;

wire    [11:0]  o_data_waddr    ;
wire    [31:0]  o_data_wdata    ;
wire            o_data_we       ;
wire            o_data_init_done;

initial begin
    i_clk = 1'b0;
    forever begin
        #5 i_clk = ~i_clk;
    end
end

integer i;
initial begin
    i_rst <= 1'b1;
    i_cpu_rst <= 1'b1;
    i_data <= 32'h00000000;
    i_data_valid <= 1'b0;
    #105
    i_rst <= 1'b0;
    #10
    for(i=0; i<32; i=i+1) begin
        i_data <= i;
        i_data_valid <= 1'b1;
        #10;
    end
    i_data <= 32'hffffffff;
    #10
    for(i=0; i<32; i=i+1) begin
        i_data <= i;
        i_data_valid <= 1'b1;
        #10;
    end
    i_data <= 32'hffffffff;
    #10
    i_data_valid <= 1'b0;
    #10
    i_cpu_rst <= 1'b0;
    #100
    i_cpu_rst <= 1'b1;
    #10
    for (i=0; i<32; i=i+1) begin
        i_data <= i;
        i_data_valid <= 1'b1;
        #10;
    end
    i_data <= 32'hffffffff;
    #10
    for (i=0; i<32; i=i+1) begin
        i_data <= i;
        i_data_valid <= 1'b1;
        #10;
    end
    i_data <= 32'hffffffff;
    #10
    i_data_valid <= 1'b0;
end

riscq_init u_riscq_init(
    .i_clk             ( i_clk             ),
    .i_rst             ( i_rst             ),
    .i_cpu_rst         ( i_cpu_rst         ),
    .i_data            ( i_data            ),
    .i_data_valid      ( i_data_valid      ),
    .o_inst_waddr      ( o_inst_waddr      ),
    .o_inst_wdata      ( o_inst_wdata      ),
    .o_inst_we         ( o_inst_we         ),
    .o_inst_init_done  ( o_inst_init_done  ),
    .o_data_waddr      ( o_data_waddr      ),
    .o_data_wdata      ( o_data_wdata      ),
    .o_data_we         ( o_data_we         ),
    .o_data_init_done  ( o_data_init_done  )
);

endmodule
