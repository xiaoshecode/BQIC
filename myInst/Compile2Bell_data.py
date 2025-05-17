import sys
import os
from DDS_config import *
import CompileUtils as utils

sys.path.append("..")
from compiler.Opfunc.OpfuncPulse import OpfuncPulse
from compiler.Opfunc.OpfuncRF_DDS import OpfuncRF_DDS

from typing import List

# init seq
Seq("S0") | dds0.s0 | dds1.s0 | dds2.s0 | dds3.s0 | PMT | 0
Seq("S1") | dds0.s1 | dds1.s1 | dds2.s1 | dds3.s1 | dds12.s0 | dds13.s0 | dds14.s0 | dds15.s0 | TTL_1 | 0
#Cooling
# Cooling.protect.f(90).a(0.8*Thresh['493'])
# Cooling.on.f(102).a(0.4*Thresh['493'])#105
# Cooling.detection.f(103).a(0.5*Thresh['493'])

dds0.s0.f(100).a(0.5)
dds1.s0.f(110).a(0.6)
dds2.s0.f(120).a(0.7)
dds3.s0.f(130).a(0.8)
# seq_cooling = Seq().Protect(2000).Cooling(1200).Detection(2000,10).Cooling(1000)

seq = Seq().S0(4).S1(5)
seqs4Bell = seq.seq

dds: List[OpfuncRF_DDS] = [OpfuncRF_DDS(DeviceID=i) for i in range(16)]
ttl: List[OpfuncPulse] = [OpfuncPulse(DeviceID=i) for i in range(32)]

seqsIR = utils.compile2Bell(seqs4Bell)  # Bell IR
print(seqsIR)
print("seqsIR length:", len(seqsIR))

# load IR to device
# 打开dds.txt文件，并将其清空
with open("data/dds.txt", "w") as f:
    pass
for seq in seqsIR:
    for item in seq:
        if item[0] == "dds":
            # dds[item[1]].reset()
            dds[item[1]].setwaveform(item[2], item[3], item[4], item[5])
            dds[item[1]].gen_assembler()
        elif item[0] == "TTL":
            # ttl[item[1]].reset()
            ttl[item[1]].setwaveform("output", 0,1, item[3])  # 设置为输出模式
    # print(len(dds[0].array_128bit[i]))


for i in range(4):
    dds[i].adjust_array_length()
    dds[i].output2file("data/dds.txt")
    for channel in range(5):
        dds[i].reset()
        for j in range(len(seqsIR)):
            dds[i].setwaveform(0,0,0,0)
            dds[i].gen_assembler()
        dds[i].adjust_array_length()
        dds[i].output2file("data/dds.txt")
utils.merge_param_files_with_header("data/dds.txt", "data/ddswithheader.txt")

# for i in range(len(ttl)):
    # ttl[i].output2file("data/ttl.txt")
# utils.merge_param_files_with_header("data/ttl.txt", "data/ttlwithheader.txt")
