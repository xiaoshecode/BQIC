`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2024/11/12 09:24:21
// Design Name: 
// Module Name: pc_reg
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
//扩展后的RISC-V指令集，RISCQ，增加了对于实时控制的操作以及case语句的支持

`include "defines.v"

module riscq(
    input           i_clk           , // 时钟      
    input           i_rst           , // 复位信号
    input           i_hlt           , // 暂停信号

    input   [31:0]  i_idata         , // 输入指令
    output  [31:0]  o_iaddr         , // 输出指令地址   

    input   [31:0]  i_ddata         , // 输入数据
    output  [31:0]  o_ddata         , // 输出数据
    output  [31:0]  o_daddr         , // 输出数据地址

    output          o_dwe           , // 写使能
    output          o_dre           , // 读使能
    output          o_das           , // 地址选通

    input   [31:0]  i_jmp_offset    , // 专用跳转寄存器内存储的相对于分支表基地址的偏移量

    output  [7:0]   o_ureg_waddr    , // 用户寄存器地址
    output  [31:0]  o_ureg_wdata    , // 用户寄存器数据输出
    output          o_ureg_we       , // 用户寄存器写使能

    input   [31:0]  i_ureg_rdata    , // 用户寄存器数据输入
    output  [2:0]   o_ureg_raddr      // 用户寄存器地址
);

/*************************wire************************/

    wire [31:0]         all0        ;
    wire [31:0]         all1        ;

    wire [31:0]         w_idatax    ;

    wire [4:0]          w_dptr      ;
    wire [4:0]          w_s1ptr     ;
    wire [4:0]          w_s2ptr     ;
    wire [2:0]          w_urptr     ;   //用户寄存器读指针
    wire [5:0]          w_uwptr     ;   //用户寄存器写指针

    wire [6:0]          w_opcode    ;
    wire [2:0]          w_funct3    ;
    wire [6:0]          w_funct7    ;

    wire [31:0]         w_simm      ;
    wire [31:0]         w_uimm      ;

    wire                w_lui       ;
    wire                w_auipc     ;
    wire                w_jal       ;
    wire                w_jalr      ;
    wire                w_bcc       ;
    wire                w_lcc       ;
    wire                w_scc       ;
    wire                w_mcc       ;
    wire                w_rcc       ;
    wire                w_lujr      ;   // 读分支跳转地址到通用寄存器
    wire                w_luw       ;   // 读用户寄存器到通用寄存器
    wire                w_setur     ;   // 写用户寄存器通过通用寄存器
    wire                w_setui     ;   // 写用户寄存器通过立即数

    wire [31:0]         w_u1reg     ;
    wire [31:0]         w_u2reg     ;

    wire [31:0]         w_uureg     ;   //读取的用户寄存器数据

    wire signed [31:0]  w_s1reg     ;
    wire signed [31:0]  w_s2reg     ;

    wire [31:0]         w_ldata     ;

    wire signed [31:0]  w_s2regx    ;
    wire [31:0]         w_u2regx    ;

    wire [31:0]         w_rmdata    ;

    wire                w_bmux      ;
    wire [31:0]         w_pcsimm    ;
    wire                w_jreq      ;
    wire [31:0]         w_jval      ;

/*************************reg*************************/

    reg             r_xres = 1              ;
    reg             r_hlt2 = 0              ;
    reg     [31:0]  r_idata2 = 0            ;

    reg     [31:0]  r_xidata                ;
    reg             r_xlui                  ;
    reg             r_xauipc                ;
    reg             r_xjal                  ;
    reg             r_xjalr                 ;
    reg             r_xbcc                  ;
    reg             r_xlcc                  ;
    reg             r_xscc                  ;
    reg             r_xmcc                  ;
    reg             r_xrcc                  ;
    reg             r_xlujr                 ;
    reg             r_xluw                  ;
    reg             r_xsetur                ;
    reg             r_xsetui                ;

    reg     [31:0]  r_xsimm                 ;
    reg     [31:0]  r_xuimm                 ;

    reg     [1:0]   r_flush = -1            ;

    reg     [31:0]  r_gen_regs[0:31]        ; // 32个通用寄存器

    reg     [31:0]  r_pc                    ; // 程序计数器
    reg     [31:0]  r_nxpc                  ; // 下一条指令地址
    reg     [31:0]  r_nxpc2                 ; // 下下条指令地址

/*************************assign**********************/

    assign all0 = 32'b0;
    assign all1 = -1;

    assign w_idatax = r_xres ? 0 : r_hlt2 ? r_idata2 : i_idata;

    assign w_dptr = r_xidata[11:7];
    assign w_s1ptr = r_xidata[19:15];
    assign w_s2ptr = r_xidata[24:20];
    //用户寄存器读写指针
    assign w_urptr = r_xidata[30:28];
    assign w_uwptr = r_xidata[27:20];

    assign w_opcode = r_flush ? 0 : r_xidata[6:0];
    assign w_funct3 = r_xidata[14:12];
    assign w_funct7 = r_xidata[31:25];

    assign w_simm = r_xsimm;
    assign w_uimm = r_xuimm;

/*********************** main decoder **************************/

    assign w_lui = r_flush ? 0 : r_xlui;
    assign w_auipc = r_flush ? 0 : r_xauipc;
    assign w_jal = r_flush ? 0 : r_xjal;
    assign w_jalr = r_flush ? 0 : r_xjalr;
    assign w_bcc = r_flush ? 0 : r_xbcc;
    assign w_lcc = r_flush ? 0 : r_xlcc;
    assign w_scc = r_flush ? 0 : r_xscc;
    assign w_mcc = r_flush ? 0 : r_xmcc;
    assign w_rcc = r_flush ? 0 : r_xrcc;
    assign w_lujr = r_flush ? 0 : r_xlujr;
    assign w_luw = r_flush ? 0 : r_xluw;
    assign w_setur = r_flush ? 0 : r_xsetur;
    assign w_setui = r_flush ? 0 : r_xsetui;

    assign w_u1reg = r_gen_regs[w_s1ptr];
    assign w_u2reg = r_gen_regs[w_s2ptr];
    //用户寄存器操作
    assign w_uureg = i_ureg_rdata;
    assign o_ureg_raddr = w_urptr;
    assign o_ureg_waddr = w_uwptr;
    assign o_ureg_we = w_setur || w_setui;
    assign o_ureg_wdata = w_setur ? w_u1reg + w_uimm : w_setui ? w_uimm : 0;

    assign w_s1reg = r_gen_regs[w_s1ptr];
    assign w_s2reg = r_gen_regs[w_s2ptr];

    // load指令译码

    //assign w_ldata = w_funct3[1:0]==0 ? { w_funct3[2]==0 && i_ddata[ 7] ? all1[31: 8]:all0[31: 8] , i_ddata[ 7: 0] } :
    //                w_funct3[1:0]==1 ? { w_funct3[2]==0 && i_ddata[15] ? all1[31:16]:all0[31:16] , i_ddata[15: 0] } :
    //                                    i_ddata;

    assign w_ldata = i_ddata;

    // RM指令译码

    assign w_s2regx = r_xmcc ? w_simm : w_s2reg;
    assign w_u2regx = r_xmcc ? w_uimm : w_u2reg;
    assign w_rmdata =   w_funct3==7 ? w_u1reg & w_s2regx :
                        w_funct3==6 ? w_u1reg | w_s2regx :
                        w_funct3==4 ? w_u1reg ^ w_s2regx :
                        w_funct3==3 ? w_u1reg < w_u2regx : // unsigned
                        w_funct3==2 ? w_s1reg < w_s2regx : // signed
                        w_funct3==0 ? (r_xrcc && w_funct7[5] ? w_u1reg-w_s2regx : w_u1reg+w_s2regx) :
                        w_funct3==1 ? w_s1reg << w_u2regx[4:0] :
                         //FCT3==5 ?
                        !w_funct7[5] ? w_s1reg >> w_u2regx[4:0] :
                        $signed(w_s1reg)>>>w_u2regx[4:0];  // (w_funct7[5] ? U1REG>>>U2REG[4:0] :

    // 跳转指令

    assign w_bmux   = w_funct3 == 7 && w_u1reg >= w_u2reg  || // bgeu
                      w_funct3 == 6 && w_u1reg <  w_u2regx || // bltu
                      w_funct3 == 5 && w_s1reg >= w_s2reg  || // bge
                      w_funct3 == 4 && w_s1reg <  w_s2regx || // blt
                      w_funct3 == 1 && w_u1reg != w_u2regx || // bne
                      w_funct3 == 0 && w_u1reg == w_u2regx; // beq

    assign w_pcsimm = r_pc + w_simm;
    assign w_jreq = w_jal || w_jalr || (w_bcc && w_bmux);
    assign w_jval = w_jalr ? o_daddr : w_pcsimm;    // 实际上load和jalr指令的地址是一致的

/*************************output*************************/

    assign o_ddata = w_u2reg;
    assign o_daddr = w_lujr ? w_u1reg + i_jmp_offset : w_u1reg + w_simm;

    //assign o_dlen[0] = (w_scc || w_lcc) && w_funct3[1:0] == 0;
    //assign o_dlen[1] = (w_scc || w_lcc) && w_funct3[1:0] == 1;
    //assign o_dlen[2] = (w_scc || w_lcc) && w_funct3[1:0] == 2;

    assign o_dwe = w_scc;
    assign o_dre = w_lcc || w_lujr;
    assign o_das = w_lcc || w_scc || w_lujr;

    assign o_iaddr = r_nxpc2;
    
/*************************always***********************/

    always @(posedge i_clk) begin
        r_hlt2 <= i_hlt;
    end

    always @(posedge i_clk) begin
        if(i_hlt ^ r_hlt2)
            r_idata2 <= i_idata;
        else 
            r_idata2 <= r_idata2;
    end

    // 指令大类区分，通过指令的低7位
    always @(posedge i_clk) begin
        r_xidata <= i_hlt ? r_xidata : w_idatax;
        r_xlui   <= i_hlt ? r_xlui   : w_idatax[6:0] == `LUI;
        r_xauipc <= i_hlt ? r_xauipc : w_idatax[6:0] == `AUIPC;
        r_xjal   <= i_hlt ? r_xjal   : w_idatax[6:0] == `JAL;
        r_xjalr  <= i_hlt ? r_xjalr  : w_idatax[6:0] == `JALR;
        r_xbcc   <= i_hlt ? r_xbcc   : w_idatax[6:0] == `BCC;
        r_xlcc   <= i_hlt ? r_xlcc   : w_idatax[6:0] == `LCC;
        r_xscc   <= i_hlt ? r_xscc   : w_idatax[6:0] == `SCC;
        r_xmcc   <= i_hlt ? r_xmcc   : w_idatax[6:0] == `MCC;
        r_xrcc   <= i_hlt ? r_xrcc   : w_idatax[6:0] == `RCC;
        r_xlujr  <= i_hlt ? r_xlujr  : w_idatax[6:0] == `LUJR;
        r_xluw   <= i_hlt ? r_xluw   : w_idatax[6:0] == `LUW;
        r_xsetur <= i_hlt ? r_xsetur : w_idatax[6:0] == `SETUR;
        r_xsetui <= i_hlt ? r_xsetui : w_idatax[6:0] == `SETUI;
    end

    // 有符号立即数输入

    always @(posedge i_clk) begin
        if(i_hlt)
            r_xsimm <= r_xsimm;
        else begin
            case (w_idatax[6:0])
                `LUI   : r_xsimm <= { w_idatax[31:12], all0[11:0] };
                `AUIPC : r_xsimm <= { w_idatax[31:12], all0[11:0] };
                `JAL   : r_xsimm <= { w_idatax[31] ? all1[31:21]:all0[31:21], w_idatax[31], w_idatax[19:12], w_idatax[20], w_idatax[30:21], all0[0] };
                `BCC   : r_xsimm <= { w_idatax[31] ? all1[31:13]:all0[31:13], w_idatax[31],w_idatax[7],w_idatax[30:25],w_idatax[11:8],all0[0] };
                `SCC   : r_xsimm <= { w_idatax[31] ? all1[31:12]:all0[31:12], w_idatax[31:25],w_idatax[11:7] };
                default: r_xsimm <= { w_idatax[31] ? all1[31:12]:all0[31:12], w_idatax[31:20] };
            endcase
        end
    end

    // 无符号立即数输入,USER寄存器指令默认无符号数

    always @(posedge i_clk) begin
        if(i_hlt)
            r_xuimm <= r_xuimm;
        else begin
            case (w_idatax[6:0])
                `LUI   : r_xuimm <= { w_idatax[31:12], all0[11:0] };
                `AUIPC : r_xuimm <= { w_idatax[31:12], all0[11:0] };
                `JAL   : r_xuimm <= { all0[31:21], w_idatax[31], w_idatax[19:12], w_idatax[20], w_idatax[30:21], all0[0] };
                `BCC   : r_xuimm <= { all0[31:13], w_idatax[31],w_idatax[7],w_idatax[30:25],w_idatax[11:8],all0[0] };
                `SCC   : r_xuimm <= { all0[31:12], w_idatax[31:25],w_idatax[11:7] };
                `SETUI : r_xuimm <= { all0[31:16], w_idatax[30:28],w_idatax[19:7] };
                `SETUR : r_xuimm <= { all0[31:16], w_idatax[31:28],w_idatax[14:7] };
                default: r_xuimm <= { all0[31:12], w_idatax[31:20] };
            endcase
        end
    end

    // reset信号打拍

    always @(posedge i_clk) begin
        r_xres <= i_rst;
    end

    // flush信号

    always @(posedge i_clk) begin
        r_flush <= r_xres ? 1 : i_hlt ? r_flush:
                    r_flush ? r_flush - 1 : 
                    w_jreq ? 2 : 0; //实际上就是一个计数器，在发生跳转之后需要冲刷两个周期的指令信息 
    end

    // pc指针

    always @(posedge i_clk) begin
        r_pc <= i_hlt ? r_pc : r_nxpc;
        r_nxpc <= i_hlt ? r_nxpc : r_nxpc2;
        r_nxpc2 <= r_xres ? 0 : i_hlt ? r_nxpc2 :
                    w_jreq ? w_jval : r_nxpc2 + 4;
    end

    // 通用寄存器

    genvar i;
    generate
        for(i = 0; i < 32; i = i+1) begin
            always @(posedge i_clk) begin
                if(i_rst)
                    r_gen_regs[i] <='d0;
                else if(i == w_dptr)
                    r_gen_regs[i] <= r_xres || i == 0 ? 0 :
                            i_hlt ? r_gen_regs[i] :
                            w_lcc || w_lujr ? w_ldata :
                            w_auipc ? w_pcsimm :
                            w_jal || w_jalr ? r_nxpc :
                            w_lui ? w_simm :
                            w_rcc || w_mcc ? w_rmdata :
                            w_luw ? w_uureg :
                            r_gen_regs[i];
                else 
                    r_gen_regs[i] <= r_gen_regs[i];
            end
        end
    endgenerate

endmodule
