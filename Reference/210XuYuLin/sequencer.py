

import atexit
import re
import struct
import socket 
import time
import threading
import warnings

import matplotlib.pyplot as plt
import numpy as np
from serial import Serial
from tqdm import trange,tqdm

from DDS import DDS
from files import *

# all time is iterms of us
# all frequency is terms if Hz
def converter(intcode,reverse=1):
    a1=intcode%65536
    a2=intcode>>16
    if reverse==False:
        ba = struct.pack(">HH", a2, a1)
    else:
        ba = struct.pack(">HH", a1,a2)
    return ba

us = 1
ms = 1000
MHz = 10**6
kHz = 10**3

sequencerConfigFile = ".\Configuration\sequencer.json"

seqMatch = re.compile(r'(\*?)(\w+)\((\d{0,}\.?\d{0,})\)$')
seq = ["idle(1000)", "cooling(2000)", "pumping(5)"]
def checkprofilecode(a,b):
    for k in set.intersection(set(a.keys()),set(b.keys())):

        c1=a[k] if k in a.keys() else 0
        c2=b[k] if k in b.keys() else 0
        bitewise=c1 ^ c2
        if (bitewise & (bitewise-1) != 0):
            return [k,c1,c2]
    return None
# def is_power_of_two(n):
#     return (n & (n-1) == 0)



     

class sequencer():
    def __init__(self, port="COM7", dds_port=None,config=sequencerConfigFile,check=True) -> None:
        self.seq = Serial(port)
        self.seq.badurate = 500000
        self.seq.stopbits = 1
        self.seq.timeout = 0.1
        self.bytesize = 8

        if type(config)==type("a"):
            config = loadConfig(config)
        self.config=config

        self.allCode = config["code"]
        self.allCodeStr = self.allCode.keys()
        try:
            self.profilecode = config["profile_code"]
        except:
            self.profilecode = {}
        self.check=check
        self.singleCode = config["switch_code"]
        self.singleCodeStr = self.singleCode.keys()

        self.spellComb = config["spellCombo"]
        self.CCDdetCode = config["CCDdetCode"]

        if not self.seq.isOpen():
            self.seq.open()
        self.setIdle()

        # set sequence parameters
        self.repeatTimes = 1
        self.threshold = 2
        self.sequence = []

        self.scanValue = None
        self.runningTime = 0
        self.totlalRunningTime = 0
        self.runningTimelist = []
        self.DetIndex = []
        self.DetTime = 0
        self.runTime_all_InDet = []

        # to store scanvlue, currnet evevnt count and all photon count
        self.data = [None, 0, 0]
        self.fileName = None

        # setup DDS
        if dds_port is not None:
            self.dds = DDS(dds_port)
            self.dds_port = dds_port
        else:
            self.dds=None
        atexit.register(self.exit)

    def checkprofile(self,a,b):
        if a in self.profilecode.keys() and b in self.profilecode.keys() :
            result=checkprofilecode(self.profilecode[a],self.profilecode[b])
        else:
            result=None
        if result is not None:
            print("警告profile切换有问题",result)
            return False
        else:
            return True
        
    

    def loadSeq(self, seq=[]):

        # reset ruuning time
        self.runningTime = 0
        self.totlalRunningTime = 0
        self.DetTime = 0
        self.runningTimelist = []
        self.DetIndex = []
        self.runTime_all_InDet = []
        codeNumber = len(seq)

        if codeNumber == 0:
            self.setIdle()
            raise ValueError("No sequence")

        # if codeNumber >= 1024:
        #     raise ValueError("Seqnece exceed 1024")

        self.sequence = seq

        # write the number of code
        self.seq.write(b"w")

        # goto 有害，不再实现这一功能
        # struct 常用的参数： B:byte 1byte, H:ushort16 2byte I:uint32 4byte >:big endian
        decisionTree = 0
        ba = struct.pack(">BH", decisionTree, codeNumber-1)
        self.seq.write(ba)

        # write sequence in order
        codeName = "idle"
        codeName_last="idle"
        runTime = 10

        # insert idle in the last line
        # seq = seq + ["idle(10)"]
        for i in range(codeNumber):

            # if it the time to scan
            # the code looks like *pumping(5)
            # the time will be substituted by scan time
            # 正则匹配
            try:
                codes = seqMatch.match(seq[i]).groups()
            except:
                raise KeyError(seq[i]+" is undefined")
            (isScan, codeName, runTime) = codes

            # check
            if codeName == "" or runTime == "":
                raise KeyError("code fromat in line%d is wrong" % (i+1))

            if codeName in self.CCDdetCode:
                self.DetTime += 1
                self.DetIndex.append(i)




            # set scan value, avoid use scan value in non scan mode
            isScan = (isScan == "*") and self.scanValue != None
            runTime = (isScan) and self.scanValue or float(runTime)
            
            # if the run time is set to 0 substitute it by free
            # if not isScan and runTime<0.02:
            #     warnings.warn("Code:%s's ruuning time is 0, substitute by Free(1)")
            #     rumTime = 0.02
            #     codeName = "free"

            # if not isScan and runTime>8e7:
            #     warnings.warn("Code:%s's ruuning time is larger than 80s, substitute by 80s")
            #     rumTime = 8e7
            #     # codeName = "free"

            if  runTime<0.02:
                warnings.warn("Code:%s's ruuning time is 0, substitute by Free(1)")
                rumTime = 0.02
                codeName = "free"

            if  runTime>8e7:
                warnings.warn("Code:%s's ruuning time is larger than 80s, substitute by 80s")
                rumTime = 8e7
                # codeName = "free"

            # if detect endcode = 255 else 254
            # convert runnignTime to machine unit
            # int it used to convert numpy.int
            #print(codeName,runTime)
            if (codeName in self.allCodeStr):
                intCode = self.allCode[codeName]
            else:
                if codeName in self.singleCodeStr:
                    intCode = self.singleCode[codeName]
                else:
                    self.setIdle()
                    raise KeyError(codeName+" in line %d is undefined" % (i+1))

            # print(runTime)
            self.runningTimelist.append(runTime)

            mTime = int(round(runTime*50))
            # endCode = ("detect" in codeName) and 255 or 254 #把我坑惨了！
            endCode = (i==codeNumber-1) and 255 or 254 #把我坑惨了！
            # write code
            # print("idneCode:%s, mTime:%s,%s" % (intCode,mTime, endCode))
            ba = converter(intCode,False)+struct.pack(">IB", mTime, endCode)
            self.seq.write(ba)
            self.runningTime = self.runningTime + runTime
            if self.check:
                self.checkprofile(codeName,codeName_last)
            codeName_last=codeName#上一句

        # if codeNumber>1024:
        #     print("超过1024！codeNumber=", codeNumber, seq[-10:-1])
        if codeNumber > 4096:
            print("超过4096！codeNumber=", codeNumber, seq[-10:-1])

        self.runningTimelist = np.array(self.runningTimelist)

        if self.DetTime>0:
            for i in range(self.DetTime-1):
                self.runTime_all_InDet.append(np.sum(self.runningTimelist[self.DetIndex[i]+1:self.DetIndex[i+1]]))

    
        # threshold ==0: sequencer返回值 allCount, detailedCount
        # threshold > 0: sequencer返回值 allEvent, detailedCount
        # 设置 threshold 恒为 0, self.threshold 将用于后续的计算

        threshold = 0
        self.seq.write(b"t")
        ba = bytearray(1)
        ba[0] = threshold & 0xff
        self.seq.write(ba)

    def setThreshold(self, threshold = 1):
        self.threshold = threshold

    def linetrigger_change(self):
        self.seq.write(b"c")
        print("The line trigger state has changed")

    def InterruptSeq(self):
        self.seq.write(b"b")
        print("The interrupt command has been sent to the mojo")

    def startSeq(self, repeatTimes=1, returnselfreadData=False):

        # check
        if repeatTimes > 232:
            raise("repeattime out of range")

        # set repeatTime
        self.seq.write(b"r")
        ba = int.to_bytes(repeatTimes-1, 2, byteorder='big')
        self.seq.write(ba)

        # start sequence
        self.seq.write(b"s")
        self.repeatTimes = repeatTimes
        self.totlalRunningTime = self.repeatTimes*self.runningTime

        """
        time.sleep(self.totalRuningTime/10**6)
        return (self.readData())
        """
        if returnselfreadData:
            return self.readData()

    # set idle mode
    # it will be excuate in initialization and end of running
    # assigne any code or intCdoe as idle mode
    def waitingData(self):
        # wait for sequence complete
        dataSize = self.seq.inWaiting()
        # ToDo: 目前为阻塞读取，后面改成 threading 在新的线程里面进行操作?
        while dataSize < 4:
            time.sleep(0.001)
            dataSize = self.seq.inWaiting()


    def setIdle(self, codeName="idle"):
        
        if type(codeName) == str:
            intCode = self.allCode[codeName]
        elif type(codeName) == int and codeName >= 0:
            intCode = codeName
        else:
            raise ValueError("idle code is not assigned")
        self.seq.write(b"i")

        self.seq.write(converter(intCode,False))
        #print("set idle")

    # scan 的时候序列会执行很多次，之后一次性给出结果
    def readData(self):

        # wait for sequence complete
        # time.sleep(self.runningTime/10**6)
        dataSize = self.seq.inWaiting()


        # ToDo: 目前为阻塞读取，后面改成 threading 在新的线程里面进行操作?
        while dataSize < 4:
            time.sleep(0.00001)
            dataSize = self.seq.inWaiting()

        # all photon count
        tempData = self.seq.read(dataSize)
        data1 = int.from_bytes(
                tempData, byteorder="little")/self.repeatTimes

        # read all count data
        if dataSize  == 4:
            self.seq.write(b"d")
            ba = bytearray(1)
            ba[0] = (self.repeatTimes-1) & 0xff
            self.seq.write(ba)
            tempData = self.seq.read(self.repeatTimes)
            data2 = np.array(bytearray(tempData))

            # append data to self.data
            self.data[0] = self.scanValue
            self.data[1] = 100/self.repeatTimes*np.sum(data2 >= self.threshold)
            self.data[2] = data1
            # print(self.data)

            # data1 Event Count Rate, a number
            # data2 Detail Count Data, an array
            return (data1, data2)
        else:
            print('ReadData Failed')
            return(-1,-1)
    # dynamic plot

    
    def genSeq(self, codeName, runTime):
        self.seq = self.seq + [codeName, runTime]

    def saveSeq(self, seq, seqName):
        self.config["spellCombo"][seqName] = seq

    def resetSeq(self):
        self.sequence = []
        self.runningTime = 0
        self.scanValue = None
        self.totalRunningTime = 0
        self.data = [None, 0, 0]

    def version(self):
        self.seq.write(b"v")
        time.sleep(0.00001)
        print(self.seq.read(self.seq.inWaiting()))

    def exit(self):
        print("Quit Sequencer and Set Idle Mode")
        self.setIdle()
        self.seq.close()
        if self.dds is not None:
            self.dds.exit()
        # saveConfig(self.config, sequencerConfigFile)
    
    def DDS_reconnet(self):
        if self.dds is not None:
            self.dds.ser.close()
            self.dds = DDS(self.dds_port)
        else:
            print("No dds connected")


if __name__ == "__main__":
    seq = sequencer(port="COM15")

    test_seq = ["cooling(5000)",
                "free(500)",
                "CCD(155)",
                "ccddetcooling(1000)",
                "detectionfree(400)",
                "free(%d)"%3e7,
                "CCD(155)",
                "ccddetcooling(1000)",
                "detectionfree(400)",
                "free(%d)" % 4e7,
                "CCD(155)",
                "ccddetcooling(1000)",
                "detectionfree(400)",
                ]

    # seq.seq.write(b"c")
    seq.loadSeq(seq=test_seq)
    print(seq.DetTime)
    print(seq.runTime_all_InDet)
    # t0 = time.time()
    # seq.startSeq(repeatTimes=100)
    # t1 = time.time()
    # print(t1-t0)
    # seq.setIdle(1)



