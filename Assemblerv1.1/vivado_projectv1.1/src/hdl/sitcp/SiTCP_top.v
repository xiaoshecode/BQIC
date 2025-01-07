`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2023/07/28 09:57:38
// Design Name: 
// Module Name: SiTCP_top
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

//SiTCP顶层连接，SiTCP相当于TCP,IP到MAC三层逻辑，与vivado的PHY层IP核相连，同时通过AXIS接口
//接收外部输入数据，存入TCP发送FIFO。并且将RBCP相关的接口信号暴露到顶层，用于RBCP模块的SiTCP输出

module SiTCP_top(
    input           wire                            SiTCP_CLK           ,
    input           wire                            independent_clk     ,
    input           wire                            rst                 ,
    //AXIS signals
    input           wire                            s_axis_tvalid       ,
    input           wire    [7:0]                   s_axis_tdata        ,
    output          wire                            s_axis_tready       ,
    //SiTCP signals
    input           wire                            GTP_CLK_P           ,
    input           wire                            GTP_CLK_N           ,
    input           wire                            PHY_RXP             ,
    input           wire                            PHY_RXN             ,
    output          wire                            PHY_TXP             ,
    output          wire                            PHY_TXN             ,
    output          wire                            SFP_TX_DISABLE      ,
    output          wire                            led2                ,
                          
    output          wire    [31:0]                  RBCP_ADDR           ,                          
    output          wire    [7:0]                   RBCP_WD             ,                          
    output          wire                            RBCP_WE             ,                          
    output          wire                            RBCP_RE             ,                          
    input           wire                            RBCP_ACK            ,                          
    input           wire    [7:0]                   RBCP_RD             ,
    
    output          wire                            tcp_rx_wr           ,                   //接收数据有效信号
    output          wire    [7:0]                   tcp_rx_data
    );

    /***************************    参数    **********************************/

    parameter                   TIM_PERIOD  =   8'd150                  ;

    /****************************   寄存器  ***********************************/

    /****************************   网表    ***********************************/

    wire                        reset_sys                                   ;
    wire                        mmcm_locked_out                             ;
    wire  [15:0]                status_vector                               ;
    //tcp signals
    wire  [15:0]                tcp_rx_wc                                   ;
    wire  [47:0]                TCP_SERVER_MAC                              ;
    //RBCP signals
    wire                        RBCP_ACT                                    ;
    //sitcp signals 
    wire    [31:0] 	   		    my_ip_addr                                  ;
    wire    [15:0]              my_tcp_port                                 ;
    wire    [15:0]              my_rbcp_port                                ;
    wire    [4:0]               my_phy_mif_addr                             ;
    wire                        GMII_TX_EN                                  ;
    wire    [7:0]               GMII_TXD                                    ;
    wire                        GMII_TX_ER                                  ;
    wire                        GMII_RX_CLK                                 ;                 
    wire                        GMII_RX_DV                                  ;                
    wire    [7:0]               GMII_RXD                                    ;            
    wire                        GMII_RX_ER                                  ;                 
    wire                        GMII_CRS                                    ;            
    wire                        GMII_COL                                    ;
    wire                        GMII_RSTn                                   ; 
    wire                        TCP_OPEN_ACK                                ;
    wire                        TCP_ERROR                                   ;
    wire                        TCP_CLOSE_REQ                               ;
    (*mark_debug = "true"*) wire                        TCP_TX_FULL                                 ;
    (*mark_debug = "true"*) wire                        TCP_TX_WR                                   ;
    wire                        TCP_CLOSE_ACK                               ;
    (*mark_debug = "true"*) wire    [7:0]               TCP_TX_DATA                                 ;
    wire                        FORCE_DEFAULTn                              ;
    wire                        resetdone                                   ;

    wire                        gtrefclk_out                                ;

    /****************************   组合逻辑 **********************************/

    assign              reset_sys       =   rst                             ;
    assign              led2            =   resetdone                       ;
    assign              SFP_TX_DISABLE  =   1'b0                            ;
    assign              TCP_TX_WR       =   s_axis_tready & s_axis_tvalid   ;
    assign              TCP_TX_DATA     =   s_axis_tdata                    ;
    assign              s_axis_tready   =   ~TCP_TX_FULL                    ;

    /****************************   实例�?    ********************************/

/*      BUFG BUFG_inst (
      .O(GMII_RX_CLK), // 1-bit output: Clock output
      .I(usr_clk2)  // 1-bit input: Clock input
   ); */

    gig_ethernet_pcs_pma_0 u_gig_ethernet_pcs_pma_0 (
    .gtrefclk_p                 (GTP_CLK_P                  )               ,                          
    .gtrefclk_n                 (GTP_CLK_N                  )               ,                          
    .gtrefclk_out               (gtrefclk_out               )               ,                      
    .txn                        (PHY_TXN                    )               ,                                        
    .txp                        (PHY_TXP                    )               ,                                        
    .rxn                        (PHY_RXN                    )               ,                                        
    .rxp                        (PHY_RXP                    )               ,                                        
    .independent_clock_bufg     (independent_clk            )               ,  
    .userclk_out                (                           )               ,                        
    .userclk2_out               (GMII_RX_CLK                )               ,                      
    .rxuserclk_out              (                           )               ,                    
    .rxuserclk2_out             (                           )               ,                  
    .gtpowergood                (                           )               ,
    .resetdone                  (resetdone                  )               ,                            
    .pma_reset_out              (                           )               ,                    
    .mmcm_locked_out            (mmcm_locked_out            )               ,                
    .gmii_txd                   (GMII_TXD                   )               ,                              
    .gmii_tx_en                 (GMII_TX_EN                 )               ,                          
    .gmii_tx_er                 (GMII_TX_ER                 )               ,                          
    .gmii_rxd                   (GMII_RXD                   )               ,                              
    .gmii_rx_dv                 (GMII_RX_DV                 )               ,                          
    .gmii_rx_er                 (GMII_RX_ER                 )               ,                          
    .gmii_isolate               (                           )               ,                      
    .configuration_vector       (5'b10000                   )               ,      
    .an_interrupt               (                           )               ,                      
    .an_adv_config_vector       (16'b0000000_11_01_00000    )               ,      
    .an_restart_config          (1'b0                       )               ,            
    .status_vector              (status_vector              )               ,                    
    .reset                      (reset_sys                  )               ,                                    
    .signal_detect              (1'b1                       )               
    );     

    WRAP_SiTCP_GMII_XCKU_32K #(TIM_PERIOD)
    SITCP_inst(
	        .CLK                        (SiTCP_CLK                  )       ,                    
            .RST                        (reset_sys                  )       ,                   

            .FORCE_DEFAULTn             (1'b0                       )       ,  
            .EXT_IP_ADDR                ({8'hC0,8'hA8,8'h0a,8'h10}  )       ,  
            .EXT_TCP_PORT               (16'd24                     )       ,  
            .EXT_RBCP_PORT              (16'd4660                   )       ,  
            .PHY_ADDR                   (5'b00001                   )       ,  
        // EEPROM   
            .EEPROM_CS                  (                           )       ,
            .EEPROM_SK                  (                           )       ,  
            .EEPROM_DI                  (                           )       ,  
            .EEPROM_DO                  (1'b0                       )       ,  
        // user data, intialial values are stored in the EEPROM, 0xFFFF_FC3C-3F
            .USR_REG_X3C                (                           )       ,  
            .USR_REG_X3D                (                           )       ,  
            .USR_REG_X3E                (                           )       ,  
            .USR_REG_X3F                (                           )       ,  
        // MII interface    
            .GMII_RSTn                  (                           )       ,                
            .GMII_1000M                 (1'b1                       )       ,                
            // TX   
            .GMII_TX_CLK                (GMII_RX_CLK                )       ,                
            .GMII_TX_EN                 (GMII_TX_EN                 )       ,                
            .GMII_TXD                   (GMII_TXD                   )       ,            
            .GMII_TX_ER                 (GMII_TX_ER                 )       ,                
            // RX   
            .GMII_RX_CLK                (GMII_RX_CLK                )       ,                
            .GMII_RX_DV                 (GMII_RX_DV                 )       ,                
            .GMII_RXD                   (GMII_RXD                   )       ,            
            .GMII_RX_ER                 (GMII_RX_ER                 )       ,                
            .GMII_CRS                   (1'b0                       )       ,                    
            .GMII_COL                   (1'b0                       )       ,                   
            // Management IF    
            .GMII_MDC                   (                           )       ,                 
            .GMII_MDIO_IN               (1'b0                       )       ,             
            .GMII_MDIO_OUT              (                           )       ,                 
            .GMII_MDIO_OE               (                           )       ,                 
        // User I/F 
            .SiTCP_RST                  (                           )       ,                
            // TCP connection control
            .TCP_OPEN_REQ               (1'b0                       )       ,                        
            .TCP_OPEN_ACK               (TCP_OPEN_ACK               )       ,                
            .TCP_ERROR                  (TCP_ERROR                  )       ,                            
            .TCP_CLOSE_REQ              (TCP_CLOSE_REQ              )       ,            
            .TCP_CLOSE_ACK              (TCP_CLOSE_REQ              )       ,            
            // FIFO I/F
            .TCP_RX_WC                  ({4'b1111,12'b0}            )       ,            
            .TCP_RX_WR                  (tcp_rx_wr                  )       ,            
            .TCP_RX_DATA                (tcp_rx_data                )       ,          
            .TCP_TX_FULL                (TCP_TX_FULL                )       ,          
            .TCP_TX_WR                  (TCP_TX_WR                  )       ,            
            .TCP_TX_DATA                (TCP_TX_DATA                )       ,          
        // RBCP     
            .RBCP_ACT                   (  RBCP_ACT                 )       ,             
            .RBCP_ADDR                  (  RBCP_ADDR                )       ,            
            .RBCP_WD                    (  RBCP_WD                  )       ,              
            .RBCP_WE                    (  RBCP_WE                  )       ,              
            .RBCP_RE                    (  RBCP_RE                  )       ,              
            .RBCP_ACK                   (  RBCP_ACK                 )       ,             
            .RBCP_RD                    (  RBCP_RD                  )       
);      

endmodule
