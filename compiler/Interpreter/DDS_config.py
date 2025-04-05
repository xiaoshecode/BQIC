from DDS_Seq import DDS, Seq

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
dds1 = DDS("dds1")
dds1.s0.f(100).a(0.5)
dds2 = DDS("dds2")
dds2.s0.f(100).a(0.5)
dds3 = DDS("dds3")
dds3.s0.f(100).a(0.5)


# DDS locations
# DDS.List = [  'Cooling','EITSigma',  'EITPi','Pumping',
#             'CoolingAxial', 'MW', 'Com411', 'Raman411',
#             'AOM411_1', 'AOM411_2', 'dds10', 'dds11',
#             'dds12', 'dds13', 'dds14', 'dds15',
#             'dds16', 'dds17', 'dds18', 'dds19',
#             'dds20', 'dds21', 'dds22', 'dds23'
#             ]
DDS.List = ["dds0", "dds1", "dds2", "dds3"]

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

Seq("Protect") | Cooling.s8 | Pumping.s8 | EITPi.s8 | EITSigma.s8 | 0

Seq("S0") | dds0.s0 | dds1.s0 | dds2.s0 | dds3.s0 | PMT  | 0
Seq("S1") | dds12.s0 | dds13.s0 | dds14.s0 | dds15.s0 | TTL_1  | 0