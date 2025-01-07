/*
 * Copyright (c) 2018, Marcelo Samsoniuk
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * * Redistributions of source code must retain the above copyright notice, this
 *   list of conditions and the following disclaimer.
 *
 * * Redistributions in binary form must reproduce the above copyright notice,
 *   this list of conditions and the following disclaimer in the documentation
 *   and/or other materials provided with the distribution.
 *
 * * Neither the name of the copyright holder nor the names of its
 *   contributors may be used to endorse or promote products derived from
 *   this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

`timescale 1ns / 1ps

// implemented opcodes:

`define LUI     7'b01101_11      // lui   rd,imm[31:12]
`define AUIPC   7'b00101_11      // auipc rd,imm[31:12]
`define JAL     7'b11011_11      // jal   rd,imm[xxxxx]
`define JALR    7'b11001_11      // jalr  rd,rs1,imm[11:0]
`define BCC     7'b11000_11      // bcc   rs1,rs2,imm[12:1]
`define LCC     7'b00000_11      // lxx   rd,rs1,imm[11:0]
`define SCC     7'b01000_11      // sxx   rs1,rs2,imm[11:0]
`define MCC     7'b00100_11      // xxxi  rd,rs1,imm[11:0]
`define RCC     7'b01100_11      // xxx   rd,rs1,rs2
`define SYS     7'b11100_11      // exx, csrxx, mret

// proprietary extension (custom-0)
`define CUS     7'b00010_11      // cus   rd,rs1,rs2,fc3,fct5

// not implemented opcodes:
//`define FCC     7'b00011_11      // fencex


// configuration file

module darkriscv
#(
    parameter CPTR = 0
)
(
    input             CLK,   // clock
    input             RES,   // reset
    input             HLT,   // halt

    input      [31:0] IDATA, // instruction data bus
    output     [31:0] IADDR, // instruction addr bus

    input      [31:0] DATAI, // data bus (input)
    output     [31:0] DATAO, // data bus (output)
    output     [31:0] DADDR, // addr bus

    output     [ 2:0] DLEN, // data length
    output            DRW,  // data read/write
    output            DRD,  // data read
    output            DWR,  // data write
    output            DAS,  // address strobe

    output [3:0]  DEBUG       // old-school osciloscope based debug! :)
);

    // dummy 32-bit words w/ all-0s and all-1s:

    wire [31:0] ALL0  = 0;
    wire [31:0] ALL1  = -1;

    reg XRES = 1;

    // pipeline flow control on HLT!

    reg        HLT2   = 0;
    reg [31:0] IDATA2 = 0;

    always@(posedge CLK)
    begin
        HLT2 <= HLT;
        
        if(HLT2^HLT) IDATA2 <= IDATA;    
    end

    wire[31:0] IDATAX = XRES ? 0 : HLT2 ? IDATA2 : IDATA;

    // decode: IDATA is break apart as described in the RV32I specification

    reg [31:0] XIDATA;

    reg XLUI, XAUIPC, XJAL, XJALR, XBCC, XLCC, XSCC, XMCC, XRCC, XCUS, XSYS; //, XFCC, XSYS;

    reg [31:0] XSIMM;
    reg [31:0] XUIMM;

    always@(posedge CLK)
    begin
        XIDATA <= HLT ? XIDATA : IDATAX;

        XLUI   <= HLT ? XLUI   : IDATAX[6:0]==`LUI;
        XAUIPC <= HLT ? XAUIPC : IDATAX[6:0]==`AUIPC;
        XJAL   <= HLT ? XJAL   : IDATAX[6:0]==`JAL;
        XJALR  <= HLT ? XJALR  : IDATAX[6:0]==`JALR;

        XBCC   <= HLT ? XBCC   : IDATAX[6:0]==`BCC;
        XLCC   <= HLT ? XLCC   : IDATAX[6:0]==`LCC;
        XSCC   <= HLT ? XSCC   : IDATAX[6:0]==`SCC;
        XMCC   <= HLT ? XMCC   : IDATAX[6:0]==`MCC;

        XRCC   <= HLT ? XRCC   : IDATAX[6:0]==`RCC;
        XCUS   <= HLT ? XRCC   : IDATAX[6:0]==`CUS;
        //XFCC   <= HLT ? XFCC   : IDATAX[6:0]==`FCC;
        XSYS   <= HLT ? XSYS   : IDATAX[6:0]==`SYS;

        // signal extended immediate, according to the instruction type:

        XSIMM  <= HLT ? XSIMM :
                 IDATAX[6:0]==`SCC ? { IDATAX[31] ? ALL1[31:12]:ALL0[31:12], IDATAX[31:25],IDATAX[11:7] } : // s-type
                 IDATAX[6:0]==`BCC ? { IDATAX[31] ? ALL1[31:13]:ALL0[31:13], IDATAX[31],IDATAX[7],IDATAX[30:25],IDATAX[11:8],ALL0[0] } : // b-type
                 IDATAX[6:0]==`JAL ? { IDATAX[31] ? ALL1[31:21]:ALL0[31:21], IDATAX[31], IDATAX[19:12], IDATAX[20], IDATAX[30:21], ALL0[0] } : // j-type
                 IDATAX[6:0]==`LUI||
                 IDATAX[6:0]==`AUIPC ? { IDATAX[31:12], ALL0[11:0] } : // u-type
                                      { IDATAX[31] ? ALL1[31:12]:ALL0[31:12], IDATAX[31:20] }; // i-type
        // non-signal extended immediate, according to the instruction type:

        XUIMM  <= HLT ? XUIMM :
                 IDATAX[6:0]==`SCC ? { ALL0[31:12], IDATAX[31:25],IDATAX[11:7] } : // s-type
                 IDATAX[6:0]==`BCC ? { ALL0[31:13], IDATAX[31],IDATAX[7],IDATAX[30:25],IDATAX[11:8],ALL0[0] } : // b-type
                 IDATAX[6:0]==`JAL ? { ALL0[31:21], IDATAX[31], IDATAX[19:12], IDATAX[20], IDATAX[30:21], ALL0[0] } : // j-type
                 IDATAX[6:0]==`LUI||
                 IDATAX[6:0]==`AUIPC ? { IDATAX[31:12], ALL0[11:0] } : // u-type
                                      { ALL0[31:12], IDATAX[31:20] }; // i-type
    end

    reg [1:0] FLUSH = -1;  // flush instruction pipeline

    wire [4:0] DPTR   = XIDATA[11: 7]; // set SP_RESET when RES==1
    wire [4:0] S1PTR  = XIDATA[19:15];
    wire [4:0] S2PTR  = XIDATA[24:20];

    wire [6:0] OPCODE = FLUSH ? 0 : XIDATA[6:0];
    wire [2:0] FCT3   = XIDATA[14:12];
    wire [6:0] FCT7   = XIDATA[31:25];

    wire [31:0] SIMM  = XSIMM;
    wire [31:0] UIMM  = XUIMM;

    // main opcode decoder:

    wire    LUI = FLUSH ? 0 : XLUI;   // OPCODE==7'b0110111;
    wire  AUIPC = FLUSH ? 0 : XAUIPC; // OPCODE==7'b0010111;
    wire    JAL = FLUSH ? 0 : XJAL;   // OPCODE==7'b1101111;
    wire   JALR = FLUSH ? 0 : XJALR;  // OPCODE==7'b1100111;

    wire    BCC = FLUSH ? 0 : XBCC; // OPCODE==7'b1100011; //FCT3
    wire    LCC = FLUSH ? 0 : XLCC; // OPCODE==7'b0000011; //FCT3
    wire    SCC = FLUSH ? 0 : XSCC; // OPCODE==7'b0100011; //FCT3
    wire    MCC = FLUSH ? 0 : XMCC; // OPCODE==7'b0010011; //FCT3

    wire    RCC = FLUSH ? 0 : XRCC; // OPCODE==7'b0110011; //FCT3
    wire    CUS = FLUSH ? 0 : XCUS; // OPCODE==7'b0110011; //FCT3
    //wire    FCC = FLUSH ? 0 : XFCC; // OPCODE==7'b0001111; //FCT3
    wire    SYS = FLUSH ? 0 : XSYS; // OPCODE==7'b1110011; //FCT3

    reg [31:0] REGS [0:31];	// general-purpose 32x32-bit registers (s1)

    reg [31:0] NXPC;        // 32-bit program counter t+1
    reg [31:0] PC;		    // 32-bit program counter t+0
    reg [31:0] NXPC2;       // 32-bit program counter t+2


    // source-1 and source-1 register selection

    wire          [31:0] U1REG = REGS[S1PTR];
    wire          [31:0] U2REG = REGS[S2PTR];

    wire signed   [31:0] S1REG = U1REG;
    wire signed   [31:0] S2REG = U2REG;


    // L-group of instructions (OPCODE==7'b0000011)

    wire [31:0] LDATA = FCT3[1:0]==0 ? { FCT3[2]==0&&DATAI[ 7] ? ALL1[31: 8]:ALL0[31: 8] , DATAI[ 7: 0] } :
                        FCT3[1:0]==1 ? { FCT3[2]==0&&DATAI[15] ? ALL1[31:16]:ALL0[31:16] , DATAI[15: 0] } :
                                        DATAI;

    // C-group: CSRRW

    // RM-group of instructions (OPCODEs==7'b0010011/7'b0110011), merged! src=immediate(M)/register(R)

    wire signed [31:0] S2REGX = XMCC ? SIMM : S2REG;
    wire        [31:0] U2REGX = XMCC ? UIMM : U2REG;

    wire [31:0] RMDATA = FCT3==7 ? U1REG&S2REGX :
                         FCT3==6 ? U1REG|S2REGX :
                         FCT3==4 ? U1REG^S2REGX :
                         FCT3==3 ? U1REG<U2REGX : // unsigned
                         FCT3==2 ? S1REG<S2REGX : // signed
                         FCT3==0 ? (XRCC&&FCT7[5] ? U1REG-S2REGX : U1REG+S2REGX) :
                         FCT3==1 ? S1REG<<U2REGX[4:0] :
                         //FCT3==5 ?
                         !FCT7[5] ? S1REG>>U2REGX[4:0] :
                        $signed(S1REG)>>>U2REGX[4:0];  // (FCT7[5] ? U1REG>>>U2REG[4:0] :

    // J/B-group of instructions (OPCODE==7'b1100011)

    wire BMUX       = FCT3==7 && U1REG>=U2REG  || // bgeu
                      FCT3==6 && U1REG< U2REGX || // bltu
                      FCT3==5 && S1REG>=S2REG  || // bge
                      FCT3==4 && S1REG< S2REGX || // blt
                      FCT3==1 && U1REG!=U2REGX || // bne
                      FCT3==0 && U1REG==U2REGX; // beq

    wire [31:0] PCSIMM = PC+SIMM;
    wire        JREQ = JAL||JALR||(BCC && BMUX);
    wire [31:0] JVAL = JALR ? DADDR : PCSIMM; // SIMM + (JALR ? U1REG : PC);

    integer i;
    
    initial for(i=0;i!=32;i=i+1) REGS[i] = 0;

    always@(posedge CLK)
    begin
        XRES <= RES;
	    FLUSH <= XRES ? 1 : HLT ? FLUSH :        // reset and halt
	                       FLUSH ? FLUSH-1 :
	                       JREQ ? 1 : 0;  // flush the pipeline!
        REGS[DPTR] <=   XRES||DPTR[4:0]==0 ? 0  :        // reset x0
                       HLT ? REGS[DPTR] :        // halt
                       LCC ? LDATA :
                     AUIPC ? PCSIMM :
                      JAL||
                      JALR ? NXPC :
                       LUI ? SIMM :
                  MCC||RCC ? RMDATA:
                             REGS[DPTR];

        NXPC <= /*XRES ? `__RESETPC__ :*/ HLT ? NXPC : NXPC2;

	    NXPC2 <=  XRES ? 32'b0 : HLT ? NXPC2 :   // reset and halt
	                 JREQ ? JVAL :                    // jmp/bra
	                        NXPC2+4;                   // normal flow
        PC   <= /*XRES ? `__RESETPC__ :*/ HLT ? PC : NXPC; // current program counter
    end

    // IO and memory interface

    assign DATAO = U2REG;
    assign DADDR = U1REG + SIMM;

    // based in the Scc and Lcc

    assign DRW      = !SCC;
    assign DLEN[0] = (SCC||LCC)&&FCT3[1:0]==0; // byte
    assign DLEN[1] = (SCC||LCC)&&FCT3[1:0]==1; // word
    assign DLEN[2] = (SCC||LCC)&&FCT3[1:0]==2; // long

    assign DWR     = SCC;
    assign DRD     = LCC;
    assign DAS     = SCC||LCC;


    assign IADDR = NXPC2;
    assign DEBUG = { XRES, |FLUSH, SCC, LCC };


endmodule
