vlib work
vlib riviera

vlib riviera/xpm
vlib riviera/gtwizard_ultrascale_v1_7_7
vlib riviera/xil_defaultlib
vlib riviera/gig_ethernet_pcs_pma_v16_1_7

vmap xpm riviera/xpm
vmap gtwizard_ultrascale_v1_7_7 riviera/gtwizard_ultrascale_v1_7_7
vmap xil_defaultlib riviera/xil_defaultlib
vmap gig_ethernet_pcs_pma_v16_1_7 riviera/gig_ethernet_pcs_pma_v16_1_7

vlog -work xpm  -sv2k12 \
"C:/Xilinx/Vivado/2019.2/data/ip/xpm/xpm_cdc/hdl/xpm_cdc.sv" \
"C:/Xilinx/Vivado/2019.2/data/ip/xpm/xpm_fifo/hdl/xpm_fifo.sv" \
"C:/Xilinx/Vivado/2019.2/data/ip/xpm/xpm_memory/hdl/xpm_memory.sv" \

vcom -work xpm -93 \
"C:/Xilinx/Vivado/2019.2/data/ip/xpm/xpm_VCOMP.vhd" \

vlog -work gtwizard_ultrascale_v1_7_7  -v2k5 \
"../../../ipstatic/hdl/gtwizard_ultrascale_v1_7_bit_sync.v" \
"../../../ipstatic/hdl/gtwizard_ultrascale_v1_7_gte4_drp_arb.v" \
"../../../ipstatic/hdl/gtwizard_ultrascale_v1_7_gthe4_delay_powergood.v" \
"../../../ipstatic/hdl/gtwizard_ultrascale_v1_7_gtye4_delay_powergood.v" \
"../../../ipstatic/hdl/gtwizard_ultrascale_v1_7_gthe3_cpll_cal.v" \
"../../../ipstatic/hdl/gtwizard_ultrascale_v1_7_gthe3_cal_freqcnt.v" \
"../../../ipstatic/hdl/gtwizard_ultrascale_v1_7_gthe4_cpll_cal.v" \
"../../../ipstatic/hdl/gtwizard_ultrascale_v1_7_gthe4_cpll_cal_rx.v" \
"../../../ipstatic/hdl/gtwizard_ultrascale_v1_7_gthe4_cpll_cal_tx.v" \
"../../../ipstatic/hdl/gtwizard_ultrascale_v1_7_gthe4_cal_freqcnt.v" \
"../../../ipstatic/hdl/gtwizard_ultrascale_v1_7_gtye4_cpll_cal.v" \
"../../../ipstatic/hdl/gtwizard_ultrascale_v1_7_gtye4_cpll_cal_rx.v" \
"../../../ipstatic/hdl/gtwizard_ultrascale_v1_7_gtye4_cpll_cal_tx.v" \
"../../../ipstatic/hdl/gtwizard_ultrascale_v1_7_gtye4_cal_freqcnt.v" \
"../../../ipstatic/hdl/gtwizard_ultrascale_v1_7_gtwiz_buffbypass_rx.v" \
"../../../ipstatic/hdl/gtwizard_ultrascale_v1_7_gtwiz_buffbypass_tx.v" \
"../../../ipstatic/hdl/gtwizard_ultrascale_v1_7_gtwiz_reset.v" \
"../../../ipstatic/hdl/gtwizard_ultrascale_v1_7_gtwiz_userclk_rx.v" \
"../../../ipstatic/hdl/gtwizard_ultrascale_v1_7_gtwiz_userclk_tx.v" \
"../../../ipstatic/hdl/gtwizard_ultrascale_v1_7_gtwiz_userdata_rx.v" \
"../../../ipstatic/hdl/gtwizard_ultrascale_v1_7_gtwiz_userdata_tx.v" \
"../../../ipstatic/hdl/gtwizard_ultrascale_v1_7_reset_sync.v" \
"../../../ipstatic/hdl/gtwizard_ultrascale_v1_7_reset_inv_sync.v" \

vlog -work xil_defaultlib  -v2k5 \
"../../../../../ip_repos/gig_ethernet_pcs_pma_0/ip_0/sim/gtwizard_ultrascale_v1_7_gthe3_channel.v" \
"../../../../../ip_repos/gig_ethernet_pcs_pma_0/ip_0/sim/gig_ethernet_pcs_pma_0_gt_gthe3_channel_wrapper.v" \
"../../../../../ip_repos/gig_ethernet_pcs_pma_0/ip_0/sim/gig_ethernet_pcs_pma_0_gt_gtwizard_gthe3.v" \
"../../../../../ip_repos/gig_ethernet_pcs_pma_0/ip_0/sim/gig_ethernet_pcs_pma_0_gt_gtwizard_top.v" \
"../../../../../ip_repos/gig_ethernet_pcs_pma_0/ip_0/sim/gig_ethernet_pcs_pma_0_gt.v" \

vcom -work gig_ethernet_pcs_pma_v16_1_7 -93 \
"../../../ipstatic/hdl/gig_ethernet_pcs_pma_v16_1_rfs.vhd" \

vlog -work gig_ethernet_pcs_pma_v16_1_7  -v2k5 \
"../../../ipstatic/hdl/gig_ethernet_pcs_pma_v16_1_rfs.v" \

vlog -work xil_defaultlib  -v2k5 \
"../../../../../ip_repos/gig_ethernet_pcs_pma_0/synth/gig_ethernet_pcs_pma_0_resets.v" \
"../../../../../ip_repos/gig_ethernet_pcs_pma_0/synth/gig_ethernet_pcs_pma_0_clocking.v" \
"../../../../../ip_repos/gig_ethernet_pcs_pma_0/synth/gig_ethernet_pcs_pma_0_support.v" \
"../../../../../ip_repos/gig_ethernet_pcs_pma_0/synth/gig_ethernet_pcs_pma_0_reset_sync.v" \
"../../../../../ip_repos/gig_ethernet_pcs_pma_0/synth/gig_ethernet_pcs_pma_0_sync_block.v" \
"../../../../../ip_repos/gig_ethernet_pcs_pma_0/synth/transceiver/gig_ethernet_pcs_pma_0_transceiver.v" \
"../../../../../ip_repos/gig_ethernet_pcs_pma_0/synth/gig_ethernet_pcs_pma_0_block.v" \
"../../../../../ip_repos/gig_ethernet_pcs_pma_0/synth/gig_ethernet_pcs_pma_0.v" \

vlog -work xil_defaultlib \
"glbl.v"

