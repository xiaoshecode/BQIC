`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2024/11/15 16:12:44
// Design Name: 
// Module Name: riscq_soc
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


module riscq_soc(
    input           i_clk           ,
    input           i_rst           ,
    input           i_continue      ,       // 取消暂停信号
    input           i_hlt_ext       ,       // 外部暂停信号

    // inst_rom初始化接口
    input [11:0]    i_inst_waddr    ,       // 写地址
    input [31:0]    i_inst_wdata    ,       // 写数据
    input           i_inst_we       ,       // 写使能
    input           i_inst_init_done,       // 初始化信号
    //data_ram初始化接口
    input [11:0]    i_data_waddr    ,       // 写地址
    input [31:0]    i_data_wdata    ,       // 写数据
    input           i_data_we       ,       // 写使能
    input           i_data_init_done,       // 初始化信号
    //user_regs 接口
    output [7:0]    o_ureg_waddr    ,       // 用户寄存器写地址
    output [31:0]   o_ureg_wdata    ,       // 用户寄存器写数据
    output          o_ureg_we       ,       // 用户寄存器写使能
    
    output [2:0]    o_ureg_raddr    ,       // 用户寄存器读地址
    input  [31:0]   i_ureg_rdata    ,       // 用户寄存器读数据

    input  [31:0]   i_jmp_offset            // 跳转偏移量
    );

/**********************************wire*******************************/

    wire            w_hlt           ;       // 暂停信号
    wire            w_ram_halt      ;       // ram暂停信号
    wire            w_rom_halt      ;       // rom暂停信号
    wire            w_user_halt     ;       // user_regs暂停信号
    
    wire    [31:0]  w_idata         ;       // 指令数据
    wire    [31:0]  w_iaddr         ;       // 指令地址

    wire    [31:0]  w_ddatai        ;
    wire    [31:0]  w_ddatao        ;
    wire    [31:0]  w_daddr         ;
    wire            w_dwe           ;
    wire            w_dre           ;
    wire            w_das           ;

    wire    [31:0]  w_dram_wdata    ;
    wire    [31:0]  w_dram_rdata    ;
    wire    [11:0]  w_dram_addr     ;
    wire            w_dram_we       ;
    wire            w_dram_das      ;
    wire            w_dram_re       ;

/**********************************reg*******************************/

    reg         r_cont_flag     ;       // 取消用户暂停标志

/**********************************assign*******************************/

    assign      w_user_halt = (o_ureg_waddr[7] && o_ureg_we) & !r_cont_flag;               
    assign      w_hlt = w_ram_halt | w_rom_halt | w_user_halt | i_hlt_ext;

    assign      w_dram_wdata = w_ddatao;
    assign      w_dram_we = w_dwe;
    assign      w_dram_das = w_das;
    assign      w_dram_re = w_dre;
    assign      w_dram_addr = w_daddr[7:2];
    assign      w_ddatai = w_dram_rdata;

/**********************************always*******************************/

    always @(posedge i_clk) begin
        if(i_rst) 
            r_cont_flag <= 1'b0;
        else if(i_continue)
            r_cont_flag <= 1'b1;
        else if(o_ureg_waddr[7] && o_ureg_we)                      
            r_cont_flag <= 1'b0; 
        else 
            r_cont_flag <= r_cont_flag;
    end

/**********************************instantiation*******************************/

riscq u_riscq(
    .i_clk         ( i_clk         ),
    .i_rst         ( i_rst         ),
    .i_hlt         ( w_hlt         ),
    .i_idata       ( w_idata       ),
    .o_iaddr       ( w_iaddr       ),
    .i_ddata       ( w_ddatai      ),
    .o_ddata       ( w_ddatao      ),
    .o_daddr       ( w_daddr       ),

    .o_dwe         ( w_dwe         ),
    .o_dre         ( w_dre         ),
    .o_das         ( w_das         ),
    .i_jmp_offset  ( i_jmp_offset  ),            
    .o_ureg_waddr  ( o_ureg_waddr  ),
    .o_ureg_wdata  ( o_ureg_wdata  ),
    .o_ureg_we     ( o_ureg_we     ),
    .i_ureg_rdata  ( i_ureg_rdata  ),
    .o_ureg_raddr  ( o_ureg_raddr  )
);

inst_rom u_inst_rom(
    .i_clk          ( i_clk                ),
    .i_rst          ( i_rst                ),
    .i_iaddr        ( w_iaddr[13:2]        ),
    .o_idata        ( w_idata              ),
    .o_rom_halt     ( w_rom_halt           ),
    .i_wdata        ( i_inst_wdata         ),
    .i_we           ( i_inst_we            ),
    .i_waddr        ( i_inst_waddr         ),
    .i_init_done    ( i_inst_init_done     ) 
);

data_ram u_data_ram(
    .i_clk         ( i_clk              ),
    .i_rst         ( i_rst              ),
    .i_daddr       ( w_daddr            ),
    .i_ddata       ( w_dram_wdata       ),   
    .i_dwe         ( w_dram_we          ),   
    .o_ddata       ( w_dram_rdata       ),    
    .i_dre         ( w_dram_re          ),
    .i_das         ( w_dram_das         ),
    .o_ram_halt    ( w_ram_halt         ),
    .i_init_done   ( i_data_init_done   ),  
    .i_init_wdata  ( i_data_wdata       ),
    .i_init_we     ( i_data_we          ),
    .i_init_waddr  ( i_data_waddr       )
);

endmodule
