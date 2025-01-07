`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2024/11/12 20:07:47
// Design Name: 
// Module Name: inst_rom
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

//本模块，reset之后首先进入初始化阶段，这个时候由上位机load指令到该RAM中，初始化完成会给出初始化完成的标志


module inst_rom(
    input           i_clk               ,
    input           i_rst               , 
    // cpu复位信号，该信号拉高后可以对ram进行初始化，
    //由于ram中的内容运行之后一定会有改变，因此暂时不考虑复位直接运行，每次都应该重新加载指令          
    input   [11:0]  i_iaddr             ,       // 指令寻址地址
    output  [31:0]  o_idata             ,       // 指令数据
    output          o_rom_halt          ,       //rom预取指没有对上，就会进入ram重新取指，多一个周期，所以需要拉高halt信号
    
    input   [31:0]  i_wdata             ,       // 写数据
    input           i_we                ,       // 写使能
    input   [11:0]  i_waddr             ,       // 写地址
    input           i_init_done                 // 初始化完成标志
    );

/*********************reg***********************************/

    reg             r_init_flag          ;
    reg  [11:0]     r_addra              ;
    reg  [11:0]     r_addrb              ;
    reg             r_dout_sel           ;
    reg             r_rst                ;

/*********************wire**********************************/

    wire [11:0]     w_addra              ;
    wire [11:0]     w_addrb              ;

    wire [31:0]     w_douta              ;
    wire [31:0]     w_doutb              ;

    wire            w_dout_sel           ;


/*********************assign*******************************/

    assign w_addra = r_init_flag ? i_waddr : i_iaddr;
    assign w_addrb = r_init_flag ? 0 : i_iaddr + 12'h1;
    //assign w_addrb = i_iaddr + 12'h1;

    assign o_idata = w_dout_sel ? w_douta : w_doutb;
    assign w_dout_sel = (r_addra == i_iaddr) ;
    assign o_rom_halt = (r_addra != i_iaddr) && (r_addrb != i_iaddr);

/*********************always********************************/

    always @(posedge i_clk) begin
        if(i_init_done)
            r_init_flag <= 1'b0;
        else if(i_rst)
            r_init_flag <= 1'b1;
        else
            r_init_flag <= r_init_flag;                 
    end

    always @(posedge i_clk) begin
        if(i_rst)
            r_addra <= 12'h0;
        else
            r_addra <= w_addra; 
    end

    always @(posedge i_clk) begin
        if(i_rst)
            r_addrb <= 12'h0;
        else
            r_addrb <= w_addrb;
    end

    always @(posedge i_clk) begin
        if(i_rst)
            r_dout_sel <= 1'b0;
        else
            r_dout_sel <= w_dout_sel;
    end

    always @(posedge i_clk) begin
        r_rst <= i_rst;
    end

/*********************instantiation*************************/

    riscq_rom u_riscq_rom (
        .clka   (i_clk      ),   
        .ena    (1'b1       ),     
        .wea    (i_we       ),     
        .addra  (w_addra    ), 
        .dina   (i_wdata    ),   
        .douta  (w_douta    ), 
        .clkb   (i_clk      ),   
        .enb    (1'b1       ),     
        .web    (1'b0       ),     
        .addrb  (w_addrb    ), 
        .dinb   (32'h0      ),   
        .doutb  (w_doutb    )  
    );

endmodule
