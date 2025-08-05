#0. 导入必要的模块
import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# print("project_root:", project_root)
# print("sys.path:", sys.path)

from DDS_Seq import DDS,Seq
from config418 import * 

import CompileUtils as utils

from Opfunc.OpfuncPulse import OpfuncPulse
from Opfunc.OpfuncRF_DDS import OpfuncRF_DDS

from typing import List

#1.init seq 导入一个Config文件中定义好的时间序列或者基于已有的时序单元设计一个新的时间序列
seq_cooling = Seq().Operate(4000).Detection(10000,10).Operate_0(5000)

#2. 对序列进行编译，转换成需要的中间表示
seqs4Bell = seq_cooling.seq
seqsIR = utils.compile2Bell(seqs4Bell)  # Bell IR
# print("seqs4Bell:", seqs4Bell,"\n")
print("seqsIR:",seqsIR)
print("seqsIR length:", len(seqsIR))

#3. 定义Bell设备的DDS和TTL通道
dds: List[OpfuncRF_DDS] = [OpfuncRF_DDS(DeviceID=i) for i in range(4)] # Bell设备有4个DDS通道，每个通道上有6个频率，TODO：扩充通道数
ttl: List[OpfuncPulse] = [OpfuncPulse(DeviceID=i) for i in range(32)]



#4. 需要将IR指令转换为设备data数据
# load IR to device
OutputDir = "../Output/"
OutputPath = OutputDir + "Data.txt"
OutputPathwithHeader = OutputDir + "DatawithHeader.txt"
with open(OutputPath, "w") as f: # 打开dds.txt文件，并将其清空
    pass

for seq in seqsIR:
    for i in range(len(dds)):
        dds[i].reset()
        flag_write = False
        for item in seq:
            if item[0]=="dds" and item[1]==i:
                dds[i].setwaveform(item[2], item[3], item[4], item[5]) # TODO: 只有一个频率分量
                dds[i].gen_assembler()
                dds[i].setwaveform(0,0,0,0)
                dds[i].gen_assembler()
                dds[i].gen_assembler()
                dds[i].gen_assembler()
                dds[i].gen_assembler()
                dds[i].gen_assembler()
                dds[i].adjust_array_length() #add EOF
                flag_write = True
                break # 找到对应的dds通道后，跳出循环
        # 如果没有找到对应的dds通道，则将其设置为0
        if flag_write==False:
            dds[i].setwaveform(0,0,0,0)
            dds[i].gen_assembler()
            dds[i].gen_assembler()
            dds[i].gen_assembler()
            dds[i].gen_assembler()
            dds[i].gen_assembler()
            dds[i].gen_assembler()
            dds[i].adjust_array_length() #add EOF
    

    for i in range(len(dds)):
        dds[i].output2file(OutputPath) # 输出到文件

    for i in range(len(ttl)):
        ttl[i].reset()
        for item in seq:
            if item[0]=="TTL" and item[1]==i:
                # print("item:", item)
                ttl[i].setwaveform("input", 0,1, item[2])  # 设置为输出模式
                ttl[i].gen_assembler()
                ttl[i].adjust_array_length() #add EOF

utils.merge_param_files_with_header(OutputPath, OutputPathwithHeader)

    # for item in seq:
    #     if item[0] == "dds":
    #         # print("item:", item)
    #         # dds[item[1]].reset()
    #         dds[item[1]].setwaveform(item[2], item[3], item[4], item[5])
    #         dds[item[1]].gen_assembler()
        # elif item[0] == "TTL":
            # ttl[item[1]].reset()
            # ttl[item[1]].setwaveform("input", 0,1, item[3])  # 设置为输出模式
    # print(len(dds[0].array_128bit[i]))
# dds[0].adjust_array_length()
# for i in range(5):
#     dds[0].setwaveform(0,0,0,0)
#     dds[0].gen_assembler()
#     dds[0].gen_assembler()
#     dds[0].gen_assembler()
#     dds[0].gen_assembler()
#     dds[0].adjust_array_length()
# dds[0].output2file("data/dds.txt")

# dds[1].adjust_array_length()
# for i in range(5):
#     dds[1].setwaveform(0,0,0,0)
#     dds[1].gen_assembler()
#     dds[1].gen_assembler()
#     dds[1].gen_assembler()
#     dds[1].gen_assembler()
#     dds[1].adjust_array_length()
# # dds[1].output2file("data/dds.txt")

# dds[2].adjust_array_length()
# for i in range(5):
#     dds[2].setwaveform(0,0,0,0)
#     dds[2].gen_assembler()
#     dds[2].gen_assembler()
#     dds[2].gen_assembler()
#     dds[2].gen_assembler()
#     dds[2].adjust_array_length()
# # dds[2].output2file("data/dds.txt")

# dds[3].adjust_array_length()
# for i in range(5):
#     dds[3].setwaveform(0,0,0,0)
#     dds[3].gen_assembler()
#     dds[3].gen_assembler()
#     dds[3].gen_assembler()
#     dds[3].gen_assembler()
#     dds[3].adjust_array_length()
# dds[3].output2file("data/dds.txt")
# dds[1].output2file("data/dds.txt")
# dds[2].output2file("data/dds.txt")
# dds[3].output2file("data/dds.txt")
# dds[3].reset()
#Freq 95-131 step 3

# dds[3].output2file("data/scan.txt")

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
# utils.merge_param_files_with_header("data/dds.txt", "data/ddswithheader.txt")

# for i in range(len(ttl)):
    # ttl[i].output2file("data/ttl.txt")
# utils.merge_param_files_with_header("data/ttl.txt", "data/ttlwithheader.txt")
