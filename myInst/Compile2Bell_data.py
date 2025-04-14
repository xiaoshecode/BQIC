import sys
import os
from DDS_config import *
import CompileUtils as utils

sys.path.append("..")
from compiler.Opfunc.OpfuncPulse import OpfuncPulse
from compiler.Opfunc.OpfuncRF_DDS import OpfuncRF_DDS

from typing import List

# init seq
seq = Seq().S0(4).S1(5)
seqs4Bell = seq.seq

dds: List[OpfuncRF_DDS] = [OpfuncRF_DDS(DeviceID=i) for i in range(16)]
ttl: List[OpfuncPulse] = [OpfuncPulse(DeviceID=i) for i in range(32)]

seqsIR = utils.compile2Bell(seqs4Bell)  # Bell IR
print(seqsIR)
print("seqsIR length:", len(seqsIR))
# load IR to device
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
