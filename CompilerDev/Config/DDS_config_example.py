from CompilerDev.Interpreter.DDS_Seq import DDS, Seq

Thresh = {"493":0.14,"553":0.18,'614':0.35,'650':0.3,'1762EOM':0.2,'532':0.2}
# Pumping States
Pumping = DDS("Pumping")
Pumping.s0.f(100).a(0.2)
Pumping.s1.f(220).a(0.75)
Pumping.s2.f(110).a(0.5)
Pumping.s3.f(110).a(0.25)
Pumping.s4.f(220).a(1)
Pumping.s5.f(110).a(0.75)
Pumping.s6.f(220).a(0.5)
Pumping.s7.f(220).a(0.25)
Pumping.s8.f(220).a(0)
Pumping.on.f(120).a(0.1)
Pumping.on.f(125).a(0.5*Thresh['493'])
Pumping.off.f(125).a(0)

# Cooling States
Cooling = DDS("Cooling")
Cooling.s0.f(100).a(0.2)
Cooling.s1.f(110).a(0.75)
Cooling.s2.f(110).a(0.5)
Cooling.s3.f(110).a(0.25)
Cooling.s4.f(220).a(1)
Cooling.s5.f(220).a(0.75)
Cooling.s6.f(220).a(0.5)
Cooling.s7.f(220).a(0.25)
Cooling.s8.f(220).a(0)
Cooling.on.f(103).a(0.45*Thresh['493'])
Cooling.off.f(125).a(0)
Cooling.detection.f(104).a(0.4*Thresh['493'])

# 493 Protection
Protection = DDS('Protect')
Protection.on.f(120).a(0.12*Thresh['493']).p(0)
Protection.off.f(120).a(0) 

# Protection
Protection = DDS("Protection")
Protection.on.f(120).a(0.1)

#LoadLA553
LoadLA553 = DDS('LoadLA553')
LoadLA553.on.f(130).a(1*Thresh['553']).p(0)
LoadLA553.off.f(130).a(0)

#Pipuming
PiPumping = DDS("PiPumping")
PiPumping.on.f(130).a(0.2*Thresh['493'])
Pumping.power.f(148).a(0.1130000000000001)
PiPumping.off.f(130).a(0)

#AOM650
AOM650 = DDS("AOM650")
AOM650.on.f(130).a(0.13)
AOM650.off.f(130).a(0)

#614
AOM614 = DDS('AOM614')
AOM614.on.f(130).a(0.9*Thresh['614'])
AOM614.off.f(130).a(0)

#EOMCBG
EOMCBG = DDS("EOMCBG")
EOMCBG.test.f(237.743).a(0.02).p(0)
EOMCBG.on.f(237.743).a(0.1)
EOMCBG.off.f(235).a(0.2)

#EOM532
EOM532 = DDS("EOM532")
EOM532.test.f(237.243).a(0.02).p(0)
EOM532.on.f(237.743).a(0.7)
EOM532.off.f(235).a(0.2)

# EITSigma States
EITSigma = DDS("EITSigma")
EITSigma.s0.f(100).a(0.2)
EITSigma.s1.f(110).a(0.75)
EITSigma.s2.f(110).a(0.5)
EITSigma.s3.f(110).a(0.25)
EITSigma.s4.f(220).a(1)
EITSigma.s5.f(220).a(0.75)
EITSigma.s6.f(220).a(0.5)
EITSigma.s7.f(220).a(0.25)
EITSigma.s8.f(220).a(0)

# EITPi States
EITPi = DDS("EITPi")
EITPi.s0.f(100).a(0.2)
EITPi.s1.f(110).a(0.75)
EITPi.s2.f(110).a(0.5)
EITPi.s3.f(110).a(0.25)
EITPi.s4.f(220).a(1)
EITPi.s5.f(220).a(0.75)
EITPi.s6.f(220).a(0.5)
EITPi.s7.f(220).a(0.25)
EITPi.s8.f(220).a(0)

# CoolingAxial States
CoolingAxial = DDS("CoolingAxial")
CoolingAxial.s0.f(100).a(0.2)
CoolingAxial.s1.f(110).a(0.75)
CoolingAxial.s2.f(110).a(0.5)
CoolingAxial.s3.f(110).a(0.25)
CoolingAxial.s4.f(220).a(1)
CoolingAxial.s5.f(220).a(0.75)
CoolingAxial.s6.f(220).a(0.5)
CoolingAxial.s7.f(220).a(0.25)
CoolingAxial.s8.f(220).a(0)

MW = DDS("MW")
MW.s0.f(100).a(0.2)
MW.s1.f(110).a(0.75)
MW.s2.f(110).a(0.5)
MW.s3.f(110).a(0.25)
MW.s4.f(220).a(1)
MW.s5.f(220).a(0.75)
MW.s6.f(220).a(0.5)
MW.s7.f(220).a(0.25)
MW.s8.f(220).a(0)

Com411 = DDS("Com411")
Com411.s0.f(100).a(0.2)
Com411.s1.f(110).a(0.75)
Com411.s2.f(110).a(0.5)
Com411.s3.f(110).a(0.25)
Com411.s4.f(220).a(1)
Com411.s5.f(220).a(0.75)
Com411.s6.f(220).a(0.5)
Com411.s7.f(220).a(0.25)
Com411.s8.f(220).a(0)

Raman411 = DDS("Raman411")
Raman411.s0.f(100).a(0.2)
Raman411.s1.f(110).a(0.75)
Raman411.s2.f(110).a(0.5)
Raman411.s3.f(110).a(0.25)
Raman411.s4.f(220).a(1)
Raman411.s5.f(220).a(0.75)
Raman411.s6.f(220).a(0.5)
Raman411.s7.f(220).a(0.25)
Raman411.s8.f(220).a(0)

AOM411_1 = DDS("AOM411_1")
AOM411_1.s0.f(100).a(0.2)
AOM411_1.s1.f(110).a(0.75)
AOM411_1.s2.f(110).a(0.5)
AOM411_1.s3.f(110).a(0.25)
AOM411_1.s4.f(220).a(1)
AOM411_1.s5.f(220).a(0.75)
AOM411_1.s6.f(220).a(0.5)
AOM411_1.s7.f(220).a(0.25)
AOM411_1.s8.f(220).a(0)

AOM411_2 = DDS("AOM411_2")
AOM411_2.s0.f(100).a(0.2)
AOM411_2.s1.f(110).a(0.75)
AOM411_2.s2.f(110).a(0.5)
AOM411_2.s3.f(110).a(0.25)
AOM411_2.s4.f(220).a(1)
AOM411_2.s5.f(220).a(0.75)
AOM411_2.s6.f(220).a(0.5)
AOM411_2.s7.f(220).a(0.25)
AOM411_2.s8.f(220).a(0)

dds10 = DDS("dds10")
dds10.s0.f(100).a(0.2)
dds10.s1.f(110).a(0.75)
dds10.s2.f(110).a(0.5)
dds10.s3.f(110).a(0.25)
dds10.s4.f(220).a(1)
dds10.s5.f(220).a(0.75)
dds10.s6.f(220).a(0.5)
dds10.s7.f(220).a(0.25)
dds10.s8.f(220).a(0)

dds11 = DDS("dds11")
dds11.s0.f(100).a(0.2)
dds11.s1.f(110).a(0.75)
dds11.s2.f(110).a(0.5)
dds11.s3.f(110).a(0.25)
dds11.s4.f(220).a(1)
dds11.s5.f(220).a(0.75)
dds11.s6.f(220).a(0.5)
dds11.s7.f(220).a(0.25)
dds11.s8.f(220).a(0)

# 更改一下命名
dds12 = DDS("dds12")
dds12.s0.f(100).a(0.2)
dds12.s1.f(110).a(0.75)
dds12.s2.f(110).a(0.5)
dds12.s3.f(110).a(0.25)
dds12.s4.f(220).a(1)
dds12.s5.f(220).a(0.75)
dds12.s6.f(220).a(0.5)
dds12.s7.f(220).a(0.25)
dds12.s8.f(220).a(0)

dds13 = DDS("dds13")
dds13.s0.f(100).a(0.2)
dds13.s1.f(110).a(0.75)
dds13.s2.f(110).a(0.5)
dds13.s3.f(110).a(0.25)
dds13.s4.f(220).a(1)
dds13.s5.f(220).a(0.75)
dds13.s6.f(220).a(0.5)
dds13.s7.f(220).a(0.25)
dds13.s8.f(220).a(0)

dds14 = DDS("dds14")
dds14.s0.f(100).a(0.2)
dds14.s1.f(110).a(0.75)
dds14.s2.f(110).a(0.5)
dds14.s3.f(110).a(0.25)
dds14.s4.f(220).a(1)
dds14.s5.f(220).a(0.75)
dds14.s6.f(220).a(0.5)
dds14.s7.f(220).a(0.25)
dds14.s8.f(220).a(0)

dds15 = DDS("dds15")
dds15.s0.f(100).a(0.2)
dds15.s1.f(110).a(0.75)
dds15.s2.f(110).a(0.5)
dds15.s3.f(110).a(0.25)
dds15.s4.f(220).a(1)
dds15.s5.f(220).a(0.75)
dds15.s6.f(220).a(0.5)
dds15.s7.f(220).a(0.25)
dds15.s8.f(220).a(0)

dds16 = DDS("dds16")
dds16.s0.f(100).a(0.2)
dds16.s1.f(110).a(0.75)
dds16.s2.f(110).a(0.5)
dds16.s3.f(110).a(0.25)
dds16.s4.f(220).a(1)
dds16.s5.f(220).a(0.75)
dds16.s6.f(220).a(0.5)
dds16.s7.f(220).a(0.25)
dds16.s8.f(220).a(0)

dds17 = DDS("dds17")
dds17.s0.f(100).a(0.2)
dds17.s1.f(110).a(0.75)
dds17.s2.f(110).a(0.5)
dds17.s3.f(110).a(0.25)
dds17.s4.f(220).a(1)
dds17.s5.f(220).a(0.75)
dds17.s6.f(220).a(0.5)
dds17.s7.f(220).a(0.25)
dds17.s8.f(220).a(0)

dds18 = DDS("dds18")
dds18.s0.f(100).a(0.2)
dds18.s1.f(110).a(0.75)
dds18.s2.f(110).a(0.5)
dds18.s3.f(110).a(0.25)
dds18.s4.f(220).a(1)
dds18.s5.f(220).a(0.75)
dds18.s6.f(220).a(0.5)
dds18.s7.f(220).a(0.25)
dds18.s8.f(220).a(0)

dds19 = DDS("dds19")
dds19.s0.f(100).a(0.2)
dds19.s1.f(110).a(0.75)
dds19.s2.f(110).a(0.5)
dds19.s3.f(110).a(0.25)
dds19.s4.f(220).a(1)
dds19.s5.f(220).a(0.75)
dds19.s6.f(220).a(0.5)
dds19.s7.f(220).a(0.25)
dds19.s8.f(220).a(0)

dds20 = DDS("dds20")
dds20.s0.f(100).a(0.2)
dds20.s1.f(110).a(0.75)
dds20.s2.f(110).a(0.5)
dds20.s3.f(110).a(0.25)
dds20.s4.f(220).a(1)
dds20.s5.f(220).a(0.75)
dds20.s6.f(220).a(0.5)
dds20.s7.f(220).a(0.25)
dds20.s8.f(220).a(0)

dds21 = DDS("dds21")
dds21.s0.f(100).a(0.2)
dds21.s1.f(110).a(0.75)
dds21.s2.f(110).a(0.5)
dds21.s3.f(110).a(0.25)
dds21.s4.f(220).a(1)
dds21.s5.f(220).a(0.75)
dds21.s6.f(220).a(0.5)
dds21.s7.f(220).a(0.25)
dds21.s8.f(220).a(0)

dds22 = DDS("dds22")
dds22.s0.f(100).a(0.2)
dds22.s1.f(110).a(0.75)
dds22.s2.f(110).a(0.5)
dds22.s3.f(110).a(0.25)
dds22.s4.f(220).a(1)
dds22.s5.f(220).a(0.75)
dds22.s6.f(220).a(0.5)
dds22.s7.f(220).a(0.25)
dds22.s8.f(220).a(0)

dds23 = DDS("dds23")
dds23.s0.f(100).a(0.2)
dds23.s1.f(110).a(0.75)
dds23.s2.f(110).a(0.5)
dds23.s3.f(110).a(0.25)
dds23.s4.f(220).a(1)
dds23.s5.f(220).a(0.75)
dds23.s6.f(220).a(0.5)
dds23.s7.f(220).a(0.25)
dds23.s8.f(220).a(0)


# test define
dds0 = DDS("dds0")
dds0.s0.f(100).a(0.5)
dds0.s1.f(140).a(0.5)
dds1 = DDS("dds1")
dds1.s0.f(110).a(0.6)
dds1.s1.f(150).a(0.6)
dds2 = DDS("dds2")
dds2.s0.f(120).a(0.7)
dds2.s1.f(160).a(0.7)
dds3 = DDS("dds3")
dds3.s0.f(130).a(0.8)
dds3.s1.f(170).a(0.8)

# DDS locations
# DDS.List = [  'Cooling','EITSigma',  'EITPi','Pumping',
#             'CoolingAxial', 'MW', 'Com411', 'Raman411',
#             'AOM411_1', 'AOM411_2', 'dds10', 'dds11',
#             'dds12', 'dds13', 'dds14', 'dds15',
#             'dds16', 'dds17', 'dds18', 'dds19',
#             'dds20', 'dds21', 'dds22', 'dds23'
#             ]

# DDS.List = ["dds0", "dds1", "dds2", "dds3"]

for i in range(len(DDS.List)):
    name = DDS.List[i]
    dds = DDS.All.get(name, None)
    if type(dds) == DDS:
        DDS.Loc[name] = i

# TTL
TTL_pumping = 1 << 0
TTL_AWGTrig = 1 << 1
TTL_AWGSwitch = 1 << 2
TTL_0 = 1 << 16
TTL_1 = 1 << 17
TTL_2 = 1 << 18
TTL_3 = 1 << 19
TTL_4 = 1 << 20
TTL_5 = 1 << 21
TTL_6 = 1 << 22
TTL_7 = 1 << 23
PMT0 = 1 << 3
TTL_CCD = 1 << 4
PMT1 = 1 << 24
PMT2 = 1 << 25

Pulse = 1
PMT = 2
TTL_1 = 3
# Seq
# Seq("S0") | Cooling.s0 | Pumping.s0 | EITSigma.s0 | EITPi.s0 | TTL_0 | 0
# Seq("S1") | Cooling.s1 | Pumping.s1 | EITSigma.s1 | EITPi.s1 | TTL_1 | 0
# Seq("S2") | Cooling.s2 | Pumping.s2 | EITSigma.s2 | EITPi.s2 | TTL_2 | 0
# Seq("S3") | Cooling.s3 | Pumping.s3 | EITSigma.s3 | EITPi.s3 | TTL_3 | 0
# Seq("S4") | Cooling.s4 | Pumping.s4 | EITSigma.s4 | EITPi.s4 | TTL_4 | 0
# Seq("S5") | Cooling.s5 | Pumping.s5 | EITSigma.s5 | EITPi.s5 | TTL_5 | 0
# Seq("S6") | Cooling.s6 | Pumping.s6 | EITSigma.s6 | EITPi.s6 | TTL_6 | 0
# Seq("S7") | Cooling.s7 | Pumping.s7 | EITSigma.s7 | EITPi.s7 | TTL_7 | 0
# Seq("S8") | Cooling.s8 | Pumping.s8 | EITSigma.s8 | EITPi.s8 | TTL_0 | 0
# Seq("S9") | CoolingAxial.s0 | MW.s0 | Com411.s0 | Raman411.s0 | TTL_0 | 0
# Seq("S10") | AOM411_1.s0 | AOM411_2.s0 | dds10.s0 | dds11.s0 | TTL_0 | 0
# Seq("S11") | dds12.s0 | dds13.s0 | dds14.s0 | dds15.s0 | TTL_0 | 0
# Seq("S12") | dds16.s0 | dds17.s0 | dds18.s0 | dds19.s0 | TTL_0 | 0
# Seq("S13") | dds20.s0 | dds21.s0 | dds22.s0 | dds23.s0 | TTL_0 | 0
# Seq(
#     "S14"
# ) | Cooling.s0 | Pumping.s0 | EITSigma.s0 | EITPi.s0 | CoolingAxial.s0 | MW.s0 | Com411.s0 | Raman411.s0 | AOM411_1.s0 | AOM411_2.s0 | dds10.s0 | dds11.s0 | dds12.s0 | dds13.s0 | dds14.s0 | dds15.s0 | dds16.s0 | dds17.s0 | dds18.s0 | dds19.s0 | dds20.s0 | dds21.s0 | dds22.s0 | dds23.s0 | TTL_0 | 0

with Seq("Detection"):
    Cooling.off | PMT2 | 0
    Cooling.off | TTL_0 | 0

# Seq('Protect') | Cooling.on | Protection.on | AOM614.on | AOM650.on | EOM532.off  |EOMCBG.off| 0
# Seq('Catch') | Cooling.on | Protection.on | LoadLA553.on | AOM614.on | AOM650.on| 0
# Seq('Cooling') | Cooling.on | Pumping.off | PiPumping.off| AOM614.on | AOM650.on | EOMCBG.off|Protection.on | EOM532.off |  0
# Seq('COoling') | Cooling.on | Pumping.off | PiPumping.off | LoadLA553.on|Protection.on |AOM614.on | AOM650.on |0

# with Seq('Detection'):
#     Cooling.detection | AOM650.on | AOM614.off | EOM532.off | EOMCBG.off|PMT |  0
#     Cooling.on | AOM614.off  | AOM650.on| EOM532.off |  0

Seq("S0") | dds0.s0 | dds1.s0 | dds2.s0 | dds3.s0 | PMT | 0
Seq("S1") | dds0.s1 | dds1.s1 | dds2.s1 | dds3.s1 | dds12.s0 | dds13.s0 | dds14.s0 | dds15.s0 | TTL_1 | 0

Seq('Protect') | Cooling.on | Protection.on | AOM614.on | AOM650.on |  0
Seq('Catch') | Cooling.on | Protection.on | AOM614.on | AOM650.on| 0
Seq('Cooling') | Cooling.on | AOM614.on | AOM650.on |Protection.on |  0
Seq('test')| EOM532.test |0
with Seq('Detection'):
    Cooling.on | AOM650.on | PMT |  0
    Cooling.on | AOM614.off  | AOM650.on |  0

# DDS.List = [ 'PiPumping','Cooling', 'Pumping', 'dds03',
#             'AOM614', 'AOM650', 'EOMCBG', 'EOM532',
#              'LoadLA553', 'AOM1762', 'Protect', 'dds23',
#             'EOM1762', 'MW', 'dds32', 'dds33',
#             'dds40', 'dds41', 'dds42', 'dds43',
#             'CBGAOM', '532AOM2', '532AOM3', '532AOM'             
#             ]

seq_cooling = Seq().Protect(2000).Cooling(1200).Detection(5000,10).Cooling(1000)

# print(seq_cooling.seq)
# [[Cooling.on = [103, 0.06300000000000001, 0], Protection.on = [120, 0.1, 0], AOM614.on = [130, 0.315, 0], AOM650.on = [130, 0.13, 0], 2000], [Cooling.on = [103, 0.06300000000000001, 0], AOM614.on = [130, 0.315, 0], AOM650.on = [130, 0.13, 0], Protection.on = [120, 0.1, 0], 1200], [Cooling.on = [103, 0.06300000000000001, 0], AOM650.on = [130, 0.13, 0], 2, 5000], [Cooling.on = [103, 0.06300000000000001, 0], AOM614.off = [130, 0, 0], AOM650.on = [130, 0.13, 0], 10], [Cooling.on = [103, 0.06300000000000001, 0], AOM614.on = [130, 0.315, 0], AOM650.on = [130, 0.13, 0], Protection.on = [120, 0.1, 0], 1000]]
# seqs = seq_cooling.seq
# for seq in seqs:
        # 逆序遍历
        # Flag_TTL = False
        # Flag_Delay = False
        # delay = 0
        # DDSList = []
        # for item in seq[::-1]:
            # print(type(item))
            # if type(item)==type(DDS("dds")):
                # DeviceID = extract_number(item.name[0])
                # Freq = item[0]
                # Amp = item[1]
                # Phase = item[2]
                # DDSList.append(["dds",DeviceID, Freq, Amp, Phase,delay])
            # elif Flag_Delay == False:
                # delay = item # 读取延时
                # Flag_Delay = True
                # print("delay:", delay)
            # elif Flag_TTL==False: # 读取TTL
                # TTL = item
                # mode = 1
                # if mode == #TTL mode 在硬件中不能导入
                # Flag_TTL = True
                # print("TTL channel:", TTL)
        # DDSList.reverse() # 反转顺序
        # DDSList.append(["TTL",TTL, mode, delay])
        # print("DDSList:", DDSList)
        # seq4Bell.append(DDSList)
    # print("Bell序列:", seq4Bell)
# print(type(seq[::-1]))
# print(type(DDS("dds")))
