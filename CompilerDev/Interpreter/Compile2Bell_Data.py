# 0. 导入必要的模块
import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# print("project_root:", project_root)
# print("sys.path:", sys.path)

from DDS_Seq import DDS, Seq
from config418 import *

import CompileUtils as utils

from Opfunc.OpfuncPulse import OpfuncPulse
from Opfunc.OpfuncRF_DDS import OpfuncRF_DDS

from typing import List

# 1.init seq 导入一个Config文件中定义好的时间序列或者基于已有的时序单元设计一个新的时间序列
seq_cooling = Seq().Operate(4000).Detection(10000, 10).Operate_0(5000)

# 2. 对序列进行编译，转换成需要的中间表示
seqs4Bell = seq_cooling.seq
seqsIR = utils.compile2Bell(seqs4Bell)  # Bell IR
# print("seqs4Bell:", seqs4Bell, "\n")
print("seqsIR:", seqsIR)
print("seqsIR length:", len(seqsIR))

# 3. 定义Bell设备的DDS和TTL通道
dds: List[OpfuncRF_DDS] = [
    OpfuncRF_DDS(DeviceID=i) for i in range(4)
]  # Bell设备有4个DDS通道，每个通道上有6个频率
# TODO：扩充通道数
ttl = OpfuncPulse(DeviceID=0)
ttl.reset()

# 4. 需要将IR指令转换为设备data数据
# load IR to device
OutputDir = "../Output/"
OutputPathDDS = OutputDir + "DataDDS.txt"
OutputPathTTL = OutputDir + "DataTTL.txt"
OutputPathDDSwithHeader = OutputDir + "DataDDSwithHeader.txt"
OutputPathTTLwithHeader = OutputDir + "DataTTLwithHeader.txt"

with open(OutputPathTTL, "w") as f:  # 打开ttl.txt文件，并将其清空
    pass

for seq in seqsIR:
    for i in range(len(dds)):
        # dds[i].reset()
        FlagWriteDDS = False
        for item in seq:
            if item[0] == "dds" and item[1] == i:
                dds[i].setwaveform(
                    item[2], item[3], item[4], item[5]
                )  # TODO: 只有一个频率分量
                dds[i].gen_assembler(0)
                # dds[i].adjust_array_length()
                dds[i].setwaveform(0, 0, 0, 0)
                dds[i].gen_assembler(1)
                # dds[i].adjust_array_length()
                dds[i].setwaveform(0, 0, 0, 0)
                dds[i].gen_assembler(2)
                # dds[i].adjust_array_length()
                dds[i].setwaveform(0, 0, 0, 0)
                dds[i].gen_assembler(3)
                # dds[i].adjust_array_length()
                dds[i].setwaveform(0, 0, 0, 0)
                dds[i].gen_assembler(4)
                # dds[i].adjust_array_length()
                dds[i].setwaveform(0, 0, 0, 0)
                dds[i].gen_assembler(5)
                # dds[i].adjust_array_length()
                FlagWriteDDS = True
                break  # 找到对应的dds通道后，跳出循环
        # # 如果没有找到对应的dds通道，则将其设置为0
        if FlagWriteDDS == False:
            dds[i].setwaveform(0, 0, 0, 0)
            dds[i].gen_assembler(0)
            #     dds[i].adjust_array_length()
            dds[i].setwaveform(0, 0, 0, 0)
            dds[i].gen_assembler(1)
            #     dds[i].adjust_array_length()
            dds[i].setwaveform(0, 0, 0, 0)
            dds[i].gen_assembler(2)
            #     dds[i].adjust_array_length()
            dds[i].setwaveform(0, 0, 0, 0)
            dds[i].gen_assembler(3)
            #     dds[i].adjust_array_length()
            dds[i].setwaveform(0, 0, 0, 0)
            dds[i].gen_assembler(4)
            #     dds[i].adjust_array_length()
            dds[i].setwaveform(0, 0, 0, 0)
            dds[i].gen_assembler(5)
            #     dds[i].adjust_array_length()

        #
    FlagWriteTTL = []
    for item in seq:
        if item[0] == "TTL":
            # State = "output" ? TTLState[i]==1 : "input"
            Channel = item[1]
            if TTLState[Channel] == 1:
                State = "output"
                ttl.setwaveform(
                    State, param1=item[2], param2=1, param3=0
                )  # 设置为输出模式
                ttl.gen_assembler(Channel)
            else:
                State = "input"
                ttl.setwaveform(
                    State, param1=item[2], param2=1, param3=0
                )  # 设置为输入模式
                ttl.gen_assembler(Channel)
            FlagWriteTTL.append(Channel)
            # break
    print("FlagWriteTTL:", FlagWriteTTL)
    for Channel in range(len(TTLState)):
        if Channel not in FlagWriteTTL:
            if TTLState[Channel] == 1:
                State = "output"
                ttl.setwaveform(
                    State, param1=item[2], param2=0, param3=0
                )  # 设置为输出模式
                ttl.gen_assembler(Channel)
            else:
                State = "input"
                ttl.setwaveform(
                    State, param1=item[2], param2=0, param3=0
                )  # 设置为输入模式
                ttl.gen_assembler(Channel)

    # print("dds info: ")
    # for i in range(len(dds)):
    #     print(i,dds[i].read_arrays())
    # dds[i].output2file(OutputPath) # 输出到文件
EOF = b"\xff" * 16
EOF_hex = "".join(format(x, "02x") for x in EOF)
with open(OutputPathDDS, "w") as f:
    # f.write("输出到文件")
    for i in range(len(dds)):
        # f.write(f"Channel {i}:\n")
        arrays = dds[i].read_arrays()
        for j in range(len(arrays)):
            for k in range(len(arrays[j])):
                # print(arrays[j][k])
                hex_string = "".join(format(x, "02x") for x in arrays[j][k])
                f.write(hex_string + "\n")
            f.write(EOF_hex + "\n")

with open(OutputPathTTL, "a") as f:
    arrays = ttl.read_arrays()
    print("ttl arrays:", arrays)
    for j in range(len(arrays)):
        for k in range(len(arrays[j])):
            print(arrays[j][k])
            hex_string = "".join(format(x, "02x") for x in arrays[j][k])
            f.write(hex_string + "\n")
        f.write(EOF_hex + "\n")

    # for i in range(len(ttl)):
    #     ttl[i].reset()
    #     for item in seq:
    #         if item[0]=="TTL" and item[1]==i:
    #             # print("item:", item)
    #             ttl[i].setwaveform("input", 0,1, item[2])  # 设置为输出模式
    #             ttl[i].gen_assembler()
    #             ttl[i].adjust_array_length() #add EOF

utils.merge_param_files_with_header(OutputPathDDS, OutputPathDDSwithHeader)
utils.merge_param_files_with_header(OutputPathTTL, OutputPathTTLwithHeader)
