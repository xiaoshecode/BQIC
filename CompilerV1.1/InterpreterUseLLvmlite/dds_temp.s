# 自己动手，丰衣足食
# Seq.S0(4).S1(5)
# len of seq = 2 without branch 
addi x1 x0 0 
addi x2 x0 2 #循环次数
setur y0 x1 0 #DDS0
setur y1 x1 0 #DDS1
setur y2 x1 0 #DDS2
setur y3 x1 0 #DDS3
addi x1 x1 1
bne x1 x2 -20 #20是固定的 

jal x0 0 #结束指令

# case ttl0:
#     1:Seq1=Seq.S1(4).S2(5)
#     2:Seq2=Seq.S2(4).S3(5)
#     3:Seq3=Seq.S3(4).S4(5)
#     4:Seq4=Seq.S4(4).S5(5)
#     5:Seq5=Seq.S5(4).S6(5)
addi x1 x0 0 
addi x2 x0 1 #进入case前的序列进行循环
setur y0 x1 0 #DDS0
setur y1 x1 0 #DDS1
setur y2 x1 0 #DDS2
setur y3 x1 0 #DDS3
addi x1 x1 1
bne x1 x2 -20 #20是固定的 x1记录了现在运行date的位置

# case ttl1: 
setui halt 1 #暂停cpu

# luw x31 z1 #读取外部计数结果，如何给定需要读取数据的通道，指定跳转寄存器是x31
lujr x31 x0
jal x31 0 # jump to x0 x1 and save position to ra
#x31 = 0
addi x1 x0 0 
addi x2 x0 1 #x1进行循环，循环次数取决于时序单元数量
setur y0 x1 0 #DDS0
setur y1 x1 0 #DDS1
setur y2 x1 0 #DDS2
setur y3 x1 0 #DDS3
addi x1 x1 1
bne x1 x2 -20 #20是固定的 x1记录了现在运行date的位置
jal x30 0 #给出跳出case后的位置，这个参数需要给定

#x1 = 1
addi x1 x0 0 
addi x2 x0 1 #x1进行循环，循环次数取决于时序单元数量
setur y0 x1 0 #DDS0
setur y1 x1 0 #DDS1
setur y2 x1 0 #DDS2
setur y3 x1 0 #DDS3
addi x1 x1 1
bne x1 x2 -20 #20是固定的 x1记录了现在运行date的位置
jal x30 0 #给出跳出case后的位置，这个参数需要给定

#x1 = 2
addi x1 x0 0 
addi x2 x0 1 #x1进行循环，循环次数取决于时序单元数量
setur y0 x1 0 #DDS0
setur y1 x1 0 #DDS1
setur y2 x1 0 #DDS2
setur y3 x1 0 #DDS3
addi x1 x1 1
bne x1 x2 -20 #20是固定的 x1记录了现在运行date的位置
jal x30 0 #给出跳出case后的位置，这个参数需要给定

#x1 = 3
addi x1 x0 0 
addi x2 x0 1 #x1进行循环，循环次数取决于时序单元数量
setur y0 x1 0 #DDS0
setur y1 x1 0 #DDS1
setur y2 x1 0 #DDS2
setur y3 x1 0 #DDS3
addi x1 x1 1
bne x1 x2 -20 #20是固定的 x1记录了现在运行date的位置
jal x30 0 #给出跳出case后的位置，这个参数需要给定

#x1 = 4
addi x1 x0 0 
addi x2 x0 1 #x1进行循环，循环次数取决于时序单元数量
setur y0 x1 0 #DDS0
setur y1 x1 0 #DDS1
setur y2 x1 0 #DDS2
setur y3 x1 0 #DDS3
addi x1 x1 1
bne x1 x2 -20 #20是固定的 x1记录了现在运行date的位置
jal x30 0 #给出跳出case后的位置，这个参数需要给定

#x1 = 5
addi x1 x0 0 
addi x2 x0 1 #x1进行循环，循环次数取决于时序单元数量
setur y0 x1 0 #DDS0
setur y1 x1 0 #DDS1
setur y2 x1 0 #DDS2
setur y3 x1 0 #DDS3
addi x1 x1 1
bne x1 x2 -20 #20是固定的 x1记录了现在运行date的位置
jal x30 0 #给出跳出case后的位置，这个参数需要给定

#执行后续序列...

jal x0 0 #结束指令







