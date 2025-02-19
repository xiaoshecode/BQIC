import sys

sys.path.append("/home/xiaoshe/code/Bell/compiler/Opfunc")

from OpfuncAWG import OpfuncAWG
from OpfuncPulse import OpfuncPulse
from OpfuncRF_DDS import OpfuncRF_DDS

from DDS_Seq import DDS, Seq
from DDS_config import *

# first, initialize the sequence
DDS.VERBOSE = True
# print(DDS.All)
# print(len(DDS.List))
# detection
seq = Seq().S0(4)
# print(seq)
rd_seq = seq.compile()
print(seq.compile())
# print(seq.compile(4))
print("序列准备好了")

cseq = rd_seq[0]
dds = cseq[0]
Timing = cseq[-1]
print(cseq[0][0])  # dds0 - freq
print(cseq[0][1])  # dds0 - amp
print(cseq[0][2])  # dds0 - phase
# second, use Opfunc to generate the sequence
# [[dds0.s0 = [100, 0.5, 0], dds1.s0 = [100, 0.5, 0], dds2.s0 = [100, 0.5, 0], dds3.s0 = [100, 0.5, 0], 1, 4]]

# dds0 = OpfuncRF_DDS(DeviceID = 0)
# dds1 = OpfuncRF_DDS(DeviceID = 1)
# dds2 = OpfuncRF_DDS(DeviceID = 2)
# dds3 = OpfuncRF_DDS(DeviceID = 3)

dds = [OpfuncRF_DDS(DeviceID=i) for i in range(4)]
ttl = OpfuncPulse(DeviceID=0)
for cseq in rd_seq:  # 时间序列
    for i in range(len(dds)):
        dds[i].append(cseq[i][0], cseq[i][1], cseq[i][2], cseq[-1])
    ttl.append(1, 1, 0)
