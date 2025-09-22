
import csv, json, time, os
import numpy as np
import sys  
import os.path
from sympy import fu  
import win32clipboard as clipBoard   
import win32con  
import win32api
import shutil


calibfile = "E:\\PyPrograms\\210sequencer\\Configuration\\calibration.json"
sequencerConfigFile = "E:\\PyPrograms\\210sequencer\\Configuration\\sequencer.json"

DATE = time.strftime("%m%d")
def setDate(date = time.strftime("%m%d")):
    global DATE
    DATE = date

def getClipBoardText(): 
    clipBoard.OpenClipboard()  
    d = clipBoard.GetClipboardData(win32con.CF_TEXT)  
    clipBoard.CloseClipboard()  
    return d  

def setClipBoardText(aString): 
    clipBoard.OpenClipboard()  
    clipBoard.EmptyClipboard()  
    clipBoard.SetClipboardText(aString)  
    clipBoard.CloseClipboard()  

def loadConfig(fileName):
    # try:
        with open(fileName, 'r') as jf:
            config = json.load(jf)
        return config
    # except:
    #     print("file is None")
    #     return -1

def saveConfig(config, fileName):
    with open(fileName, "w+") as jf:
        jf.write(json.dumps(config,indent=4))

def genFile(fileName, start, stop):
    year_month = time.strftime("%Y%m")
    date_now = time.strftime("%m%d")
    time_now = time.strftime("%H-%M-%S")
    folder = os.getcwd() + '\\data\\' + year_month + "\\" + date_now + "\\" + time_now + "_" + fileName + "\\"
    if not os.path.exists(folder):
        os.makedirs(folder)

    # Copy the calibration file and the sequencer configuration file into the data folder
    shutil.copy2(calibfile, folder)
    shutil.copy2(sequencerConfigFile, folder)

    csvName = folder + fileName + \
        "_{:.3f}-{:.3f}".format(start, stop) + '-'+time_now+".csv"
    file = open(csvName, "w", newline='')
    csvWriter = csv.writer(file)
    # setClipBoardText(time_now)
    return csvWriter,file,csvName, folder

# data acquirization
def getNewestFile(date = None):
    # date == None, set date = today
    if date == None:
        date = time.strftime("%m%d")
    return searchFile(folder = date)


def searchFile(file=None,folder=None):
    global DATE
    # file is assigned in full path
    if "\\" in str(file):
        return file

    # acquire the data folder

    """
    if folder == None:
        month = time.strftime("%m") 
        day = time.strftime("%d")
    """
    if folder == DATE or folder == None:
        month = DATE[:2]
        day = DATE[2:]
    else:
        if len(str(folder)) < 3:
            month = time.strftime("%m") 
            day = "%02d"%folder

            # both month and day are assigned
        else:
            folderStr = "%04d" % int(folder)
            month = folderStr[:2]
            day = folderStr[2:]

    # get the data folder
    year = time.strftime("%Y")
    dataFolder = os.path.join(os.getcwd(),'data', year+month, month+day)

    # get all files
    fileList = os.listdir(dataFolder)
    fileLen = len(fileList)
    fileTimes = -np.ones(fileLen)
    
    # get the file genenrtion time
    for i in range(fileLen):
        item = fileList[i]
        if item[-3:] == "csv":
            fileTimes[i] = 60*int(item[-8:-6])+int(item[-6:-4])

    if file == None:
        targetTime = max(fileTimes)
    else:
        file = "%04d" % int(file)
        targetTime = 60*int(file[:2])+int(file[2:])

    if targetTime == -1:
        print("The folder is empty")
        return -1

    for i in range(fileLen):
        try:
            indx = np.where(fileTimes == targetTime)[0][0]
            targetFile = fileList[indx]
            fullPath = os.path.join(dataFolder,targetFile)
        except:
            print("CanNot Find File")
            fullPath = -1
    print("File:%s" % fullPath)
    print("FileTime:%s,%s%s" % ("%02d%02d" % (targetTime//60,targetTime%60),int(month),day))
    return fullPath

def getMatrix(file):
    data = np.genfromtxt(file, delimiter=',')
    return data

def getData(file=None,date = None):
    
    # get files
    filePath = searchFile(file, date)
    
    # import data
    if filePath == -1:
        print("File is Invalid")
        return -2
    else:
        data = getMatrix(filePath)
        if np.shape(data)[0]==0:
            print("File:%s is empty" % filePath)
            return -2
        if max(data[:,1]) > 1:
            data[:,1] = data[:,1]/100
        if "435" in filePath:
            data[:,1] = 1 - data[:,1]
        return data[:,:2]

def updateConfig(fitCenters,configName = "355SideBand.json"):
    configFile = "./Configuration/"+configName
    sbConfig = loadConfig(configFile)
    
    sbNum = len(fitCenters)
    carrier = sbConfig["carrier"]
    sb0 = sbConfig["sideBand"]["0"]
    sb1 = sbConfig["sideBand"]["1"]
    sb2 = sbConfig["sideBand"]["2"]

    # set threshold
    td = 0.1
    c = carrier
    b0 = sb0
    b1 = sb1
    b2 = sb2
    try:
        if sbNum%2 == 1:
            c = fitCenters[sbNum//2]
        b0 = fitCenters[[0,-1]]
        b1 = fitCenters[[1,-2]]
    except:
        pass
    
    if abs(carrier - c) < td:
        carrier = c
        sbConfig["carrier"] = carrier 
        
    for i  in range(3):
        bands = eval("sb%d"%i)
        if abs((b0-carrier).mean()) < td and max(abs(bands-b0))<td:
            sbConfig["sideBand"][str(i)] = list(np.round(b0,4))
            
        if abs((b1-carrier).mean()) < td and max(abs(bands-b1))<td:
            sbConfig["sideBand"][str(i)] = list(np.round(b1,4))
                   
    # it will be wrong when sb2 are integer
    sbConfig["sideBand"]["2"] = list(np.round(sb2,4))
    saveConfig(sbConfig,configFile)

def loadcalpara():
    calibrateParaFile = ".\Configuration\calibration.json"
    calconfig = loadConfig(calibrateParaFile)

    return calconfig

def savecalpara(name, value, filename):
    # print(os.getcwd())
    calconfig = loadConfig(filename)
    calconfig[name] = value
    # print(calconfig)
    saveConfig(calconfig, filename)

if __name__ == '__main__':
    setClipBoardText("hello World")
    print(getNewestFile())
    print(searchFile())
    print(searchFile(934,305))
    print(searchFile("934",305))
    print(searchFile(934,"305"))
    print(searchFile(folder = 305))
    print(searchFile(folder = "305"))
    print(searchFile(r'D:\Document\GitHub\Sequencer\data\202203\0305\355FrequencyScan241.692-248.590-1058.csv'))
    
    
