`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2024/11/14 17:13:37
// Design Name: 
// Module Name: inst_rom_tb
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


module inst_rom_tb();


reg         i_clk           ;
reg         i_rst           ;
reg  [11:0] i_iaddr         ;
wire [31:0] o_idata         ;
wire        o_rom_halt      ;
reg  [31:0] i_wdata         ;
reg         i_we            ;
reg  [11:0] i_waddr         ;
reg         i_init_done     ;

initial begin
    i_clk = 0;
    forever begin
        #5 i_clk = ~i_clk;
    end
end

integer i;

initial begin
    i_rst <= 1;
    i_iaddr <= 12'h0;
    i_waddr <= 12'h0;
    i_wdata <= 32'h0;
    i_we <= 0;
    i_waddr <= 12'h0;
    i_init_done <= 0;
    #105
    for(i = 0; i < 1024; i=i+1) begin
        i_wdata <= i+1;
        i_we <= 1;
        i_waddr <= i;
        #10;
    end
    i_init_done <= 1;
    i_we <= 0;
    #100
    i_rst <= 0;
    #10
    i_iaddr <= 12'h1;
    #10
    i_iaddr <= 12'h2;
    #10
    i_iaddr <= 12'h3;
    #10
    i_iaddr <= 12'h4;
    #10
    i_iaddr <= 12'h8;
    #10
    i_iaddr <= 12'h8;
    #10
    i_iaddr <= 12'h9;
    #10
    i_iaddr <= 12'h10;
    #10
    i_iaddr <= 12'h10;
    #10
    i_iaddr <= 12'h12;
    #10
    i_iaddr <= 12'h12;
    #10
    i_iaddr <= 12'h12;
end

inst_rom u_inst_rom(
    .i_clk       ( i_clk       ),
    .i_rst       ( i_rst       ),
    .i_iaddr     ( i_iaddr     ),
    .o_idata     ( o_idata     ),
    .o_rom_halt  ( o_rom_halt  ),
    .i_wdata     ( i_wdata     ),
    .i_we        ( i_we        ),
    .i_waddr     ( i_waddr     ),
    .i_init_done  ( i_init_done  )
);



endmodule
