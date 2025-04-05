import sys
sys.path.append("/home/xiaoshe/code/Bell/compiler/Opfunc")

from OpfuncAWG import OpfuncAWG
from OpfuncPulse import OpfuncPulse
from OpfuncRF_DDS import OpfuncRF_DDS

dds = [OpfuncRF_DDS(DeviceID=i) for i in range(4)]
ttl = OpfuncPulse(DeviceID=0)

freq = 100
amp =  0.5
phase = 0
delay = 1 #us
dds[0].setwaveform(freq, amp , phase, delay)
# print(dds[0].read_state())

class Seq:
    """
    作用: 帮助将一个数据结构转换成一个seq类，一个seq对象包含一个序列，其产生的数据结构如下所示
     
    """