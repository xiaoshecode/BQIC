`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2024/11/20 09:46:47
// Design Name: 
// Module Name: top
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


module top(
    input           i_clk_p                 ,
    input           i_clk_n                 ,
    //sitcp signals
    input           i_gtp_clk_p             ,
    input           i_gtp_clk_n             ,
    input           i_phy_rxp               ,
    input           i_phy_rxn               ,
    output          o_phy_txp               ,
    output          o_phy_txn               ,
    output          o_sfp_tx_disable        ,
    output          o_sitcp_reset_done      ,
    //test signal led
    output          o_test                
    );

/***************************wire***************************/

    wire            w_clk_200m              ;
    wire            w_clk_20m               ;
    wire            w_locked                ;
    wire            w_rst                   ;
    wire            w_rst_200m              ;
    wire            w_rst_20m               ;
    wire            w_cpu_rst               ;   //写
    wire            w_tcp_rx_valid          ;
    wire    [7:0]   w_tcp_rx_data           ;

    wire            w_fifo_rd_en            ;
    wire    [31:0]  w_fifo_dout             ;
    wire            w_fifo_full             ;
    wire            w_fifo_empty            ;

    wire    [11:0]  w_inst_waddr            ;
    wire    [31:0]  w_inst_wdata            ;
    wire            w_inst_we               ;
    wire            w_inst_init_done        ;
    wire    [11:0]  w_data_waddr            ;
    wire    [31:0]  w_data_wdata            ;
    wire            w_data_we               ;
    wire            w_data_init_done        ;

    wire            w_hlt_ext               ;   //写
    wire            w_continue              ;   //写

    wire    [7:0]   w_ureg_waddr            ;
    wire    [31:0]  w_ureg_wdata            ;
    wire            w_ureg_we               ;
    wire    [2:0]   w_ureg_raddr            ;
    wire    [31:0]  w_ureg_rdata            ;   
    wire    [31:0]  w_jmp_offset            ;   //写

    wire            w_we_ext                ;    
    wire    [31:0]  w_wdata_ext             ;   //写
    wire    [2:0]   w_waddr_ext             ;   //写
    wire    [5:0]   w_raddr_ext             ;   //写
    wire    [31:0]  w_rdata_ext             ;   //读

/***************************assign***************************/

    assign          w_fifo_rd_en = ~w_fifo_empty;
    assign          w_rst = ~w_locked;

/***************************instantiation*********************************/

    vio_0 u_vio (
        .clk        (w_clk_200m     ),  
        .probe_in0  (w_rdata_ext    ), 
        .probe_out0 (w_cpu_rst      ),   
        .probe_out1 (w_hlt_ext      ),   
        .probe_out2 (w_continue     ),  
        .probe_out3 (w_jmp_offset   ),
        .probe_out4 (w_wdata_ext    ), 
        .probe_out5 (w_waddr_ext    ), 
        .probe_out6 (w_raddr_ext    )  
    );

    clk_wiz_0 u_clk_wiz_0(
        .clk_200m           (w_clk_200m         ),  
        .clk_20m            (w_clk_20m          ), 
        .locked             (w_locked           ),       
        .clk_in1_p          (i_clk_p            ), 
        .clk_in1_n          (i_clk_n            )
    );

    rst_gen u_rst_gen_200m(
        .i_clk              ( w_clk_200m        ),    
        .i_rst              ( w_rst             ),
        .o_rst              ( w_rst_200m        )     
    );  

    rst_gen u_rst_gen_20m(
        .i_clk              ( w_clk_20m         ),    
        .i_rst              ( w_rst             ),
        .o_rst              ( w_rst_20m         )     
    );

    SiTCP_top u_SiTCP_top(
        .SiTCP_CLK          ( w_clk_200m          ),
        .independent_clk    ( w_clk_20m           ),
        .rst                ( w_rst_200m          ),
        .s_axis_tvalid      (                     ),         
        .s_axis_tdata       (                     ),       
        .s_axis_tready      (                     ),
        .GTP_CLK_P          ( i_gtp_clk_p         ),
        .GTP_CLK_N          ( i_gtp_clk_n         ),
        .PHY_RXP            ( i_phy_rxp           ),
        .PHY_RXN            ( i_phy_rxn           ),
        .PHY_TXP            ( o_phy_txp           ),
        .PHY_TXN            ( o_phy_txn           ),
        .SFP_TX_DISABLE     ( o_sfp_tx_disable    ),
        .led2               ( o_sitcp_reset_done  ),
        .RBCP_ADDR          (                     ),
        .RBCP_WD            (                     ),
        .RBCP_WE            (                     ),
        .RBCP_RE            (                     ),    
        .RBCP_ACK           (                     ),
        .RBCP_RD            (                     ),
        .tcp_rx_wr          ( w_tcp_rx_valid      ),
        .tcp_rx_data        ( w_tcp_rx_data       )
    );

    fifo_trans_width u_fifo_trans_width (
        .clk                (w_clk_200m     ),                
        .srst               (w_rst_200m     ),              
        .din                (w_tcp_rx_data  ),                
        .wr_en              (w_tcp_rx_valid ),            
        .rd_en              (w_fifo_rd_en   ),            
        .dout               (w_fifo_dout    ),              
        .full               (w_fifo_full    ),              
        .empty              (w_fifo_empty   ),            
        .wr_rst_busy        (),
        .rd_rst_busy        () 
    );

    riscq_init u_riscq_init(
        .i_clk             ( w_clk_200m             ),
        .i_rst             ( w_rst_200m             ),
        .i_cpu_rst         ( w_cpu_rst              ),
        .i_data            ( w_fifo_dout            ),
        .i_data_valid      ( w_fifo_rd_en           ),
        .o_inst_waddr      ( w_inst_waddr           ),
        .o_inst_wdata      ( w_inst_wdata           ),
        .o_inst_we         ( w_inst_we              ),
        .o_inst_init_done  ( w_inst_init_done       ),
        .o_data_waddr      ( w_data_waddr           ),
        .o_data_wdata      ( w_data_wdata           ),
        .o_data_we         ( w_data_we              ),
        .o_data_init_done  ( w_data_init_done       )
    );

    riscq_soc u_riscq_soc(
        .i_clk            ( w_clk_200m              ),
        .i_rst            ( w_rst_200m              ),
        .i_continue       ( w_continue              ),
        .i_hlt_ext        ( w_hlt_ext               ),
        .i_inst_waddr     ( w_inst_waddr            ),
        .i_inst_wdata     ( w_inst_wdata            ),
        .i_inst_we        ( w_inst_we               ),
        .i_inst_init_done ( w_inst_init_done        ),
        .i_data_waddr     ( w_data_waddr            ),
        .i_data_wdata     ( w_data_wdata            ),
        .i_data_we        ( w_data_we               ),
        .i_data_init_done ( w_data_init_done        ),
        .o_ureg_waddr     ( w_ureg_waddr            ),
        .o_ureg_wdata     ( w_ureg_wdata            ),
        .o_ureg_we        ( w_ureg_we               ),
        .o_ureg_raddr     ( w_ureg_raddr            ),
        .i_ureg_rdata     ( w_ureg_rdata            ),
        .i_jmp_offset     ( w_jmp_offset            )
    );

    user_regs u_user_regs(
        .i_clk            ( w_clk_200m          ),
        .i_rst            ( w_cpu_rst           ),
        .i_we_cpu         ( w_ureg_we           ),
        .i_wdata_cpu      ( w_ureg_wdata        ),
        .i_waddr_cpu      ( w_ureg_waddr[5:0]   ),
        .i_raddr_cpu      ( w_ureg_raddr        ),
        .o_rdata_cpu      ( w_ureg_rdata        ),
        .i_we_ext         ( w_we_ext            ),
        .i_wdata_ext      ( w_wdata_ext         ),
        .i_waddr_ext      ( w_waddr_ext         ),
        .i_raddr_ext      ( w_raddr_ext         ),
        .o_rdata_ext      ( w_rdata_ext         )
    );



endmodule
