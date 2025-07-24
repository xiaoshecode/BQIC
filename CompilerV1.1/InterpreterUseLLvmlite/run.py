from DDS_Seq import DDS, Seq
from DDS_config import *

import sys
sys.path.append("/home/xiaoshe/code/Bell/compiler/Opfunc")

from OpfuncAWG import OpfuncAWG
from OpfuncPulse import OpfuncPulse
from OpfuncRF_DDS import OpfuncRF_DDS

# first, initialize the sequence
DDS.VERBOSE = True
# print(DDS.All)
# print(len(DDS.List))
# detection
# seq = Seq().S0(4)
seq = Seq().S0(4).S1(5)  # 序列
print(seq)
seq[0]
# rd_seq = seq.compile()
# print(seq.compile())
# print(seq.compile(4))
print("序列准备好了")

dds = [OpfuncRF_DDS(DeviceID=i) for i in range(16)]
ttl = [OpfuncPulse(DeviceID=i) for i in range(16)]

# def compile2Bell(seq):
#     """
#     将序列转换为Bell硬件执行的IR   
#     每个dds通道有4个参数[f,a,p,t]
#     每个ttl通道有1个参数[t]，暂时用来计数 #TODO 别的功能暂时还未考虑，等待实现
#     """

#     seq_len = len(seq)
#     seq4Bell = []
#     for item in seq:
#         item4Bell = []

