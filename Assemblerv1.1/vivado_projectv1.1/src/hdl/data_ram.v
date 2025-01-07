`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2024/11/14 15:08:03
// Design Name: 
// Module Name: data_ram
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
//为了读写效率，只接受4字节的读写

module data_ram(
    input           i_clk               ,
    input           i_rst               ,       // cpu复位信号，该信号拉高后可以对ram进行初始化
    // riscq接口
    input   [31:0]  i_daddr             ,       // 指令寻址地址
    input   [31:0]  i_ddata             ,       // 写数据
    input           i_dwe               ,       // 写使能
    output  [31:0]  o_ddata             ,       // 读数据
    input           i_dre               ,       // 读使能
    input           i_das               ,       
    // 控制信号
    output          o_ram_halt          ,       //ram预取指没有对上,需要进入ram重新取数，所以需要多一个周期
    // 初始化信号
    input           i_init_done         ,       // 初始化完成标志
    input    [31:0] i_init_wdata        ,       // 写数据
    input           i_init_we           ,       // 写使能
    input    [11:0] i_init_waddr                // 写地址
);

/****************************parameter***************************/

    parameter   DATA_SEL = 2'b0;    // 表示高位地址，仿真时需要做修改

/****************************reg****************************/

    reg     [31:8]      ctag        [0:63]  ;    // 储存高位地址
    reg     [31:0]      cdata       [0:63]  ;    // 储存cache数据
    reg                 cval        [0:63]  ;    // 该处cache存储的数据有效
    reg                 dram_ack            ;   //一个周期的访存时间，所以就是把dram_en打一拍
    
    reg                 dram_init_flag      ;   //ram初始化标志

/****************************wire***************************/

    wire    [5:0]       cindex              ;    // cache索引
    wire                hit                 ;    // 是否击中
    wire                clr                 ;    // cache数据是否被修改
    wire                data_req            ;    // 是否需要从ram中取数据
    wire                ddack               ;    // 数据读取应答

    wire    [31:0]      dram_rdata          ;    // ram数据
    wire    [31:0]      dram_wdata          ;    // ram写数据
    wire    [11:0]      dram_addr           ;    // ram地址
    wire                dram_we             ;    // ram写使能
    wire                dram_en             ;    // ram使能
    wire                dram_re             ;    // ram读使能

/****************************assign*************************/

    assign cindex = i_daddr[7:2];
    assign hit = i_rst ? 0 : (i_dre && cval[cindex] && ctag[cindex] == i_daddr[31:8]);
    assign clr = i_rst ? 0 : (i_dwe && cval[cindex] && ctag[cindex] == i_daddr[31:8]);
    assign data_req = i_rst || hit ? 0 : (i_daddr[31:30] == DATA_SEL) && i_dre;   //分配给ram的高位地址
    assign o_ddata = hit ? cdata[cindex] : dram_rdata;
    assign ddack = hit ? 1 : dram_ack;
    assign dram_en = dram_init_flag ? 1 : hit ? 0 : i_das && (i_daddr[31:30] == DATA_SEL);
    assign dram_re = hit ? 0 : i_dre;
    assign dram_we = dram_init_flag ? i_init_we : hit ? 0 : i_dwe;
    assign dram_addr = dram_init_flag ? i_init_waddr : hit ? 0 : i_daddr[13:2];
    assign o_ram_halt = i_das && !ddack;
    assign dram_wdata = dram_init_flag ? i_init_wdata : hit ? 0 : i_ddata;

/****************************always*************************/

    genvar i;
    generate
        for(i = 0; i < 64; i = i + 1) begin
            always @(posedge i_clk) begin
                if(i_rst) begin
                    cdata[i] <= 0;
                    ctag[i] <= 0;
                    cval[i] <= 0;
                end
                else if(i == cindex)begin
                    if(data_req && dram_ack)begin
                        cdata[i] <= dram_rdata;
                        ctag[i] <= i_daddr[31:8];
                        cval[i] <= 1;
                    end
                    else if(clr)begin
                        cdata[i] <= i_ddata;
                        ctag[i] <= i_daddr[31:8];
                        cval[i] <= 1;
                    end
                    else begin
                        cval[i] <= cval[i];
                        cdata[i] <= cdata[i];
                        ctag[i] <= ctag[i];
                    end
                end
                else begin
                    cval[i] <= cval[i];
                    cdata[i] <= cdata[i];
                    ctag[i] <= ctag[i];
                end
            end
        end
    endgenerate

    always @(posedge i_clk) begin
        if(i_rst)
            dram_ack <= 0;
        else 
            dram_ack <= dram_en & ~dram_ack;
    end

    always @(posedge i_clk) begin
        if(i_init_done)
            dram_init_flag <= 0;
        else if(i_rst)
            dram_init_flag <= 1;
        else
            dram_init_flag <= dram_init_flag; 
    end

/******************************instantiation***************************/

    riscq_ram u_riscq_ram (
        .clka   (i_clk      ),  
        .ena    (dram_en    ),    
        .wea    (dram_we    ),    
        .addra  (dram_addr  ),
        .dina   (dram_wdata ),  
        .douta  (dram_rdata ) 
    );

endmodule
