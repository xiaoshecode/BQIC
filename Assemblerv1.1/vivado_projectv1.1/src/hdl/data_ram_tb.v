`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2024/11/15 11:26:53
// Design Name: 
// Module Name: data_ram_tb
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


module data_ram_tb();

reg                 i_clk   ;
reg                 i_rst   ;
reg [31:0]          i_daddr ;
reg [31:0]          i_ddata ;
reg                 i_dwe   ;
wire [31:0]         o_ddata ;
reg                 i_dre   ;
reg                 i_das   ;

wire                o_ram_halt  ;

reg                 i_init_done ;
reg [31:0]          i_init_wdata ;
reg                 i_init_we ;
reg [11:0]          i_init_waddr ;

initial begin
    i_clk = 0;
    forever begin
        #5 i_clk = ~i_clk;
    end
end

integer i;

initial begin
    i_rst <= 1;
    i_daddr <= 32'h0;
    i_ddata <= 32'h0;
    i_dwe <= 0;
    i_dre <= 0;
    i_das <= 0;
    i_init_done <= 0;
    i_init_wdata <= 32'h0;
    i_init_we <= 0;
    i_init_waddr <= 12'h0;
    #105
    for(i = 0; i < 1024; i=i+1) begin
        i_init_wdata <= i+1;
        i_init_we <= 1;
        i_init_waddr <= i;
        #10;
    end
    i_init_done <= 1;
    i_init_we <= 0;
    #100
    i_rst <= 0;
    i_daddr <= 32'h4000_0004;
    i_dre <= 1;
    i_das <= 1;
    #20
    i_daddr <= 32'h4000_0008;
    i_dre <= 1;
    i_das <= 1;
    #20
    i_daddr <= 32'h4000_0004;
    i_dre <= 1;
    i_das <= 1;
    #10
    i_daddr <= 32'h4000_0004;
    i_dre <= 1;
    i_das <= 1;
    #10
    i_daddr <= 32'h4000_0008;
    #10
    i_dre <= 0;
    i_daddr <= 32'h4000_0004;
    i_dwe <= 1;
    i_ddata <= 32'h1234_5678;
    #20
    i_das <= 1;
    i_dwe <= 0;
    i_dre <= 1;
    i_daddr <= 32'h4000_0004;
    #10
    i_daddr <= 32'h4000_0008;
    #10
    i_daddr <= 32'h4000_0404;
    #20
    i_daddr <= 32'h4000_0004;
    #20
    i_das <= 1;
    i_dre <= 0;
    i_dwe <= 1;
    i_daddr <= 32'h4000_0004;
    i_ddata <= 32'h1234_0000;
    #20
    i_daddr <= 32'h4000_0008;
    #20
    i_daddr <= 32'h4000_000C;
    #20
    i_dwe <= 0;
    i_dre <= 1;
    i_daddr <= 32'h4000_000C;
    #20
    i_dre <= 0;
    i_das <= 0;
end

data_ram u_data_ram(
    .i_clk         ( i_clk         ),
    .i_rst         ( i_rst         ),
    .i_daddr       ( i_daddr       ),
    .i_ddata       ( i_ddata       ),
    .i_dwe         ( i_dwe         ),
    .o_ddata       ( o_ddata       ),
    .i_dre         ( i_dre         ),
    .i_das         ( i_das         ),
    .o_ram_halt    ( o_ram_halt    ),
    .i_init_done   ( i_init_done   ),
    .i_init_wdata  ( i_init_wdata  ),
    .i_init_we     ( i_init_we     ),
    .i_init_waddr  ( i_init_waddr  )
);

endmodule
