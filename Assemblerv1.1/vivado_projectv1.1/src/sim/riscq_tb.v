`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2024/11/12 20:29:54
// Design Name: 
// Module Name: riscq_tb
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


module riscq_tb( );


reg         i_clk           ;
reg         i_rst           ;
reg         i_hlt           ;

wire [31:0] i_idata         ;
wire [31:0] o_iaddr         ;

wire [31:0] i_ddata         ;
wire [31:0] o_ddata         ;
wire [31:0]  o_daddr         ;
wire [9:0]  o_dlen          ;
wire         o_drw           ;
wire         o_dwe           ;
wire         o_dre           ;

wire        das             ;
wire [7:0]  o_ureg_waddr    ;
wire [31:0] o_ureg_wdata    ;
wire        o_ureg_we       ;
wire [31:0] i_ureg_rdata = 32'h0;   
wire [31:0] o_ureg_rdata    ;
wire [7:0]  o_ureg_raddr    ;


initial begin
    i_clk = 1'b0;
    forever begin
        #5 i_clk = ~i_clk;
    end
end

initial begin
    i_rst = 1'b1;
    i_hlt = 1'b0;
    #105
    i_rst = 1'b0;
end


riscq u_riscq(
    .i_clk         ( i_clk         ),
    .i_rst         ( i_rst         ),
    .i_hlt         ( i_hlt         ),
    .i_idata       ( i_idata       ),
    .o_iaddr       ( o_iaddr       ),
    .i_ddata       ( i_ddata       ),
    .o_ddata       ( o_ddata       ),
    .o_daddr       ( o_daddr       ),
    .o_dlen        ( o_dlen        ),
    .o_drw         ( o_drw         ),
    .o_dwe         ( o_dwe         ),
    .o_dre         ( o_dre         ),
    .o_das         ( das           ),
    .o_ureg_waddr  ( o_ureg_waddr  ),
    .o_ureg_wdata  ( o_ureg_wdata  ),
    .o_ureg_we     ( o_ureg_we     ),
    .i_ureg_rdata  ( i_ureg_rdata  ),
    .o_ureg_rdata  ( o_ureg_rdata  ),
    .o_ureg_raddr  ( o_ureg_raddr  )
); 

/* darkriscv#(
    .CPTR  ( 0 )
)u_darkriscv(
    .CLK   ( i_clk   ),
    .RES   ( i_rst   ),
    .HLT   ( i_hlt   ),
    .IDATA ( i_idata ),
    .IADDR ( o_iaddr ),
    .DATAI ( i_ddata ),
    .DATAO ( o_ddata ),
    .DADDR ( o_daddr ),
    .DLEN  ( o_dlen  ),
    .DRW   ( o_drw   ),
    .DRD   ( o_dre   ),
    .DWR   ( o_dwe   ),
    .DAS   ( das   ),
    .DEBUG  (   )
); */



inst_rom u_inst_rom(
    .i_clk    ( i_clk    ),
    .i_rst    ( i_rst    ),
    .i_iaddr  ( {2'b0,o_iaddr[31:2]}  ),
    .o_idata  ( i_idata  )
);

data_ram u_data_ram(
    .i_clk    ( i_clk    ),
    .i_rst    ( i_rst    ),
    .i_addr   ( {2'b0,o_daddr[31:2]}  ),
    .o_rdata  ( i_ddata  ),
    .i_we     ( o_dwe    ),
    .i_wdata  ( o_wdata  )
);




endmodule
