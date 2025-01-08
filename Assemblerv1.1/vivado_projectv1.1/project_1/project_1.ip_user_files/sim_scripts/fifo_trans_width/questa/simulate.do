onbreak {quit -f}
onerror {quit -f}

vsim -t 1ps -lib xil_defaultlib fifo_trans_width_opt

do {wave.do}

view wave
view structure
view signals

do {fifo_trans_width.udo}

run -all

quit -force
