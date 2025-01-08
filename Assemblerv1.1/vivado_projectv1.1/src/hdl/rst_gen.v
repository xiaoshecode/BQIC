`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2023/10/13 10:11:26
// Design Name: 
// Module Name: rst_gen
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
///////////////////////////////////////////////////////////////////////////////

//此处是跨时钟域rst信号处理，从快时钟到慢时钟，因此将rst信号拉长并且延后

module rst_gen(
    input               i_clk       ,
    input               i_rst       ,
    output              o_rst    
);

    reg             [7:0]   r_rst         ;

    always @(posedge i_clk, posedge i_rst) begin
        if(i_rst)
            r_rst <= 8'b00001111;
        else 
            r_rst <= r_rst << 1;
    end

    assign          o_rst           =   r_rst[7];

endmodule