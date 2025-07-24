addi x1 x0 0
addi x2 x0 2000 # x1循环变量，x2阈值
setur y0 x0 0
addi x1 x1 1
bne x1 x2 -8
jal x0 0
jal x0 0