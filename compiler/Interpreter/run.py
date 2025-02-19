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




