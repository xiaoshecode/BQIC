`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2024/11/15 15:58:44
// Design Name: 
// Module Name: user_regs
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
//分成两组，一组由CPU写入，外部信号读取，另一组由外部信号写入，CPU读取

module user_regs(
    input           i_clk       ,
    input           i_rst       ,
    input           i_we_cpu    ,
    input  [31:0]   i_wdata_cpu ,    
    input  [5:0]    i_waddr_cpu ,

    input  [2:0]    i_raddr_cpu ,
    output [31:0]   o_rdata_cpu ,

    input           i_we_ext    ,
    input  [31:0]   i_wdata_ext ,
    input  [2:0]    i_waddr_ext ,

    input  [5:0]    i_raddr_ext ,
    output [31:0]   o_rdata_ext
    );

/************************reg*************************/

    reg   [31:0]    user_regs_w  [0:63];  //CPUx写入，外部读取
    reg   [31:0]    user_regs_r  [0:7];  //外部写入，CPUx读取,外部很少有输入，因此只设置8个

/************************assign*************************/

    assign o_rdata_cpu = user_regs_r[i_raddr_cpu];
    assign o_rdata_ext = user_regs_w[i_raddr_ext];

/************************always*************************/

    genvar i;
    generate
        for(i = 0; i < 64; i = i+1)begin
            always @(posedge i_clk) begin
                if(i_rst)
                    user_regs_w[i] <= 32'h0;
                else if(i_we_cpu && i_waddr_cpu == i)
                    user_regs_w[i] <= i_wdata_cpu;
                else 
                    user_regs_w[i] <= user_regs_w[i];
            end
        end

        for(i = 0; i < 8; i = i+1)begin
            always @(posedge i_clk) begin
                if(i_rst)
                    user_regs_r[i] <= 32'h0;
                else if(i_we_ext && i_waddr_ext == i)
                    user_regs_r[i] <= i_wdata_ext;
                else 
                    user_regs_r[i] <= user_regs_r[i];
            end
        end
    endgenerate

endmodule
