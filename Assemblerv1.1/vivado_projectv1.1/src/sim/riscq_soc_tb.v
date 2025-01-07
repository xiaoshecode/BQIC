`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2024/11/15 17:36:45
// Design Name: 
// Module Name: riscq_soc_tb
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


module riscq_soc_tb();

reg             i_clk           ;
reg             i_rst           ;
reg             i_continue      ;       // 取消暂停信号

// inst_rom初始化接口
reg [11:0]      i_inst_waddr    ;       // 写地址
reg [31:0]      i_inst_wdata    ;       // 写数据
reg             i_inst_we       ;       // 写使能
reg             i_inst_init_done;       // 初始化信号
//data_ram初始化接口
reg [11:0]      i_data_waddr    ;       // 写地址
reg [31:0]      i_data_wdata    ;       // 写数据
reg             i_data_we       ;       // 写使能
reg             i_data_init_done;       // 初始化信号
//user_regs 接口


wire    [7:0]   w_ureg_waddr    ;
wire    [31:0]  w_ureg_wdata    ;
wire            w_ureg_we       ;
wire    [31:0]  w_ureg_rdata    ;
wire    [2:0]   w_ureg_raddr    ;

//user_regs 接口

reg            i_we_ext        ;
reg  [31:0]    i_wdata_ext     ;
reg  [2:0]     i_waddr_ext     ;

reg  [31:0]     r_inst_rom [0:1024];
reg  [31:0]     r_data_ram [0:1024];

reg  [31:0]     r_count;

always @(posedge i_clk) begin
    if(i_rst)
        r_count <= 32'h0;
    else 
        r_count <= r_count + 32'h1;
end

initial begin
    @(posedge w_ureg_we)
    $display("time =%d, w_ureg_waddr=%d, w_ureg_wdata=%d", r_count, w_ureg_waddr, w_ureg_wdata);
end


initial begin
    i_clk            = 1'b0;
    forever begin
        #5 i_clk = ~i_clk;
    end
end

integer i;

//初始化rom和ram，之后取消复位信号，开始运行
initial begin
    i=0;
    i_rst            <= 1'b1;
    i_continue       <= 1'b0;
    i_inst_waddr     <= 12'h0;
    i_inst_wdata     <= 32'h0;
    i_inst_we        <= 1'b0;
    i_inst_init_done <= 1'b0;
    i_data_waddr     <= 12'h0;
    i_data_wdata     <= 32'h0;
    i_data_we        <= 1'b0;
    i_data_init_done <= 1'b0;
    i_we_ext         <= 1'b0;
    i_wdata_ext      <= 32'h0;
    i_waddr_ext      <= 4'h0;
    #105
    $readmemh("F:/qbit/qubit_1.0/RISCQv1.1/src/hdl/inst_rom.mem", r_inst_rom);
    $readmemh("F:/qbit/qubit_1.0/RISCQv1.1/src/hdl/data_ram.mem", r_data_ram);
    #10
    for(i=0; i<1024; i=i+1)begin
        i_inst_waddr     <= i;
        i_inst_wdata     <= r_inst_rom[i];
        i_inst_we        <= 1'b1;
        i_inst_init_done <= 1'b0;
        i_data_waddr     <= i;
        i_data_wdata     <= r_data_ram[i];
        i_data_we        <= 1'b1;
        i_data_init_done <= 1'b0;
        #10;
    end
    i_inst_we        <= 1'b0;
    i_data_we        <= 1'b0;
    #20
    i_inst_init_done <= 1'b1;
    i_data_init_done <= 1'b1;
    #20
    i_rst            <= 1'b0;
end


riscq_soc u_riscq_soc(
    .i_clk            ( i_clk            ),
    .i_rst            ( i_rst            ),
    .i_continue       ( i_continue       ),
    .i_hlt_ext        ( 1'b0        ),

    .i_inst_waddr     ( i_inst_waddr     ),
    .i_inst_wdata     ( i_inst_wdata     ),
    .i_inst_we        ( i_inst_we        ),
    .i_inst_init_done ( i_inst_init_done ),

    .i_data_waddr     ( i_data_waddr     ),
    .i_data_wdata     ( i_data_wdata     ),
    .i_data_we        ( i_data_we        ),
    .i_data_init_done ( i_data_init_done ),

    .o_ureg_waddr     ( w_ureg_waddr     ), 
    .o_ureg_wdata     ( w_ureg_wdata     ), 
    .o_ureg_we        ( w_ureg_we        ),

    .i_ureg_rdata     ( w_ureg_rdata     ), 
    .o_ureg_raddr     ( w_ureg_raddr     ),

    .i_jmp_offset     ( 32'd4  )
    );

user_regs u_user_regs(
    .i_clk        ( i_clk        ),
    .i_rst        ( i_rst        ),
    .i_we_cpu     ( w_ureg_we    ), 
    .i_wdata_cpu  ( w_ureg_wdata ), 
    .i_waddr_cpu  ( w_ureg_waddr ),  
    .i_raddr_cpu  ( w_ureg_raddr ),
    .o_rdata_cpu  ( w_ureg_rdata ), 
    .i_we_ext     ( i_we_ext     ),
    .i_wdata_ext  ( i_wdata_ext  ),
    .i_waddr_ext  ( i_waddr_ext  ),
    .i_raddr_ext  (   ),
    .o_rdata_ext  (   )
);


endmodule
