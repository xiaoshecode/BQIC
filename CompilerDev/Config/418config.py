from DDS_Seq import DDS, Seq

#sequencer.ccd = None
import numpy as np

#operate_zero_01 = DDS('Zero01')
# operate_zero_02 = DDS('Zero02')
# operate_zero_03 = DDS('Zero03')
operate_zero_10 = DDS('Zero10')
operate_zero_11 = DDS('Zero11')
operate_zero_12 = DDS('Zero12')
operate_zero_13 = DDS('Zero13')
operate_zero_20 = DDS('Zero20')
operate_zero_21 = DDS('Zero21')
operate_zero_22 = DDS('Zero22')
operate_zero_23 = DDS('Zero23')
operate_zero_30 = DDS('Zero30')
# print(0)

protection = DDS('Operate_dds_00')
cooling = DDS('Operate_dds_01')
pipumping = DDS('Operate_dds_02')
repumping = DDS('Operate_dds_03')
# repumping = DDS('Operate_dds_10')
protection.on.f(163).a(0.04)#protection0.045 163
cooling.detection.f(102).a(0.04)#carrier0.04 102
pipumping.on.f(102).a(0.08)#pi-pumping0.088,0.055  0.032 0.014
#pipumping.on.f(163).a(0.045)
cooling.on.f(102).a(0.038)#0.088
#cooling.on.f(100).a(0.008) #repumping0.5
repumping.on.f(125).a(0.44)

# Assign DDS sequences to physical ports.
DDS.List = ['Operate_dds_00', 'Operate_dds_01', 'Operate_dds_02', 'Operate_dds_03', 
            'Operate_dds_10', 'Zero11', 'Zero12', 'Zero13', 
            'Zero20', 'Zero21', 'Zero22', 'Zero23', 
            'Zero30']
#DDS.List = ['Zero01', 'Operate_dds_00']
for i in range(len(DDS.List)):
    name = DDS.List[i]
    dds = DDS.All.get(name, None)
    if type(dds) == DDS:
        DDS.Loc[name] = i

operate_ttl = 1
operate_ttl_1 = 2
operate_ttl_2 = 1
PMT = 0

Seq('Operate_0') | protection.on | cooling.on  | pipumping.on  | repumping.on  | 0
Seq('Operate')   | protection.on | cooling.on  | pipumping.on  | repumping.on  | operate_ttl |0
Seq('Operate_1') | protection.on | cooling.on  | pipumping.on  | operate_ttl_1 | 0
Seq('Operate_2') | protection.on | cooling.on  | pipumping.on  | operate_ttl_2 | 0

seq = Seq().Operate(4000)#g
seq_ttl = Seq().Operate_1(5).Operate_2(100)

with Seq('Detection'):
    protection.on | cooling.on | pipumping.on | repumping.on | PMT |  0
    protection.on | cooling.on | pipumping.on | repumping.on | 0
    
# seq_cooling = Seq().Operate(4000).Detection(10000,10).Operate_0(4000)
# data = sequencer.scan(seq_cooling,cooling.on.a,(0,0.025,0.005),"C0",100,repeats = 50)
# data = sequencer.sweep(seq_cooling,"C0",100,repeats = 50)
# print('done')
# print(seq_cooling.seq)

