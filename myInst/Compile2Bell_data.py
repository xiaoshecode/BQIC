import sys
import os
from ZHXconfig import *
import CompileUtils as utils

sys.path.append("..")
from compiler.Opfunc.OpfuncPulse import OpfuncPulse
from compiler.Opfunc.OpfuncRF_DDS import OpfuncRF_DDS

from typing import List

# init seq
# Seq("S0") | dds0.s0 | dds1.s0 | dds2.s0 | dds3.s0 | 0
# Seq("S1") | dds0.s1 | dds1.s1 | dds2.s1 | dds3.s1 | dds12.s0 | dds13.s0 | dds14.s0 | dds15.s0 | TTL_1 | 0
#Cooling
# Cooling.protect.f(90).a(0.8*Thresh['493'])
# Cooling.on.f(102).a(0.4*Thresh['493'])#105
# Cooling.detection.f(103).a(0.5*Thresh['493'])

# dds0.s0.f(163).a(0.04)
# dds1.s0.f(102).a(0.04)
# dds2.s0.f(125).a(0.08)
# dds3.s0.f(0).a(0)
seq_cooling = Seq().Operate(4000).Detection(10000,10).Operate_0(4000)

# seq = Seq().S0(4)
seqs4Bell = seq_cooling.seq
print("seqs4Bell:", seqs4Bell,"\n")
dds: List[OpfuncRF_DDS] = [OpfuncRF_DDS(DeviceID=i) for i in range(4)]
ttl: List[OpfuncPulse] = [OpfuncPulse(DeviceID=i) for i in range(32)]

seqsIR = utils.compile2Bell(seqs4Bell)  # Bell IR
print("seqsIR:",seqsIR)
print("seqsIR length:", len(seqsIR))



# load IR to device
# 打开dds.txt文件，并将其清空
with open("data/dds.txt", "w") as f:
    pass
for seq in seqsIR:
    for item in seq:
        if item[0] == "dds":
            # print("item:", item)
            # dds[item[1]].reset()
            dds[item[1]].setwaveform(item[2], item[3], item[4], item[5])
            dds[item[1]].gen_assembler()
        # elif item[0] == "TTL":
            # ttl[item[1]].reset()
            # ttl[item[1]].setwaveform("input", 0,1, item[3])  # 设置为输出模式
    # print(len(dds[0].array_128bit[i]))
dds[0].adjust_array_length()
for i in range(5):
    dds[0].setwaveform(0,0,0,0)
    dds[0].gen_assembler()
    dds[0].gen_assembler()
    dds[0].gen_assembler()
    dds[0].gen_assembler()
    dds[0].adjust_array_length()
dds[0].output2file("data/dds.txt")

dds[1].adjust_array_length()
for i in range(5):
    dds[1].setwaveform(0,0,0,0)
    dds[1].gen_assembler()
    dds[1].gen_assembler()
    dds[1].gen_assembler()
    dds[1].gen_assembler()
    dds[1].adjust_array_length()
dds[1].output2file("data/dds.txt")

dds[2].adjust_array_length()
for i in range(5):
    dds[2].setwaveform(0,0,0,0)
    dds[2].gen_assembler()
    dds[2].gen_assembler()
    dds[2].gen_assembler()
    dds[2].gen_assembler()
    dds[2].adjust_array_length()
dds[2].output2file("data/dds.txt")

dds[3].adjust_array_length()
for i in range(5):
    dds[3].setwaveform(0,0,0,0)
    dds[3].gen_assembler()
    dds[3].gen_assembler()
    dds[3].gen_assembler()
    dds[3].gen_assembler()
    dds[3].adjust_array_length()
dds[3].output2file("data/dds.txt")
# dds[1].output2file("data/dds.txt")
# dds[2].output2file("data/dds.txt")
# dds[3].output2file("data/dds.txt")
dds[3].reset()
#Freq 95-131 step 3
for i in range(95, 132, 3):
    dds[3].setwaveform(i,0,0,0)
    dds[3].gen_assembler()
read_arrayys = dds[3].read_arrays()
dds[3].output2file("data/scan.txt")

#         # # 5个没用到的频率
#         # dds[item[1]].reset()
#         # dds[item[1]].setwaveform(0,0,0,0)
#         # dds[item[1]].gen_assembler()
#         # dds[item[1]].setwaveform(0,0,0,0)
#         # dds[item[1]].gen_assembler()
#         # dds[item[1]].setwaveform(0,0,0,0)
#         # dds[item[1]].gen_assembler() 
#         # dds[item[1]].setwaveform(0,0,0,0)
#         # dds[item[1]].gen_assembler()
#         # dds[item[1]].setwaveform(0,0,0,0)
#         # dds[item[1]].gen_assembler()
#         # dds[item[1]].adjust_array_length()

#         dds[item[1]].output2file("data/dds.txt")
#         dds[item[1]].reset()
# dds[0].reset()
# dds[0].setwaveform(163,0.04,0,4000)
utils.merge_param_files_with_header("data/dds.txt", "data/ddswithheader.txt")

# for i in range(len(ttl)):
    # ttl[i].output2file("data/ttl.txt")
# utils.merge_param_files_with_header("data/ttl.txt", "data/ttlwithheader.txt")
