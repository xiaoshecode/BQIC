# -*- coding: utf-8 -*-
"""
Created on Mon May 30 09:06:43 2022

@author: S210-CryoTrap
"""

"""
此类主要功能是完成了一个实时窗口显示，本质只是一个循环执行自定义的一个函数，并接受该函数的输出进行绘图
此类创建时接受的输入变量有：
1. func：需要循环执行的函数对象，此函数可以是无参量函数，用于不做变量扫描的实验；也可以是单参量函数，用于变量扫描的实验。
2. stopfunc：UI界面关闭时会执行的函数对象，一般用于进行仪器关闭。
3. fitfunc： 拟合函数对象，详情参照最底下的示例以及Fit文件中对于拟合函数对象的格式要求，为None时不做拟合。
4. xdata：变量扫描实验时，所扫变量的范围，要求类型必须是个list，为None时不做变量扫描，不保存数据。
5. fileprefix：保存数据时产生的保存文件名前缀。None时不保存数据。
6. widget：暂无用途。
7. autoRun：True时自动运行实验，结束时自动拟合（没有拟合函数时自动findpeak），而后自动关闭窗口，开启此功能时最好在运行结束时将此类生成的对象del，如示例所示；
            False时需手动点击start按钮开始实验，结束时需手动点fit按钮和窗口关闭

此类中包含的交互按键：
1. start：实验开始按钮
2. stop：实验终止按钮，若实验中途stop，再重新点击start时实验会从头开始
3. pause：实验暂停按钮，再次点击会在原来实验暂停点继续
4. fit：拟合按钮，根据所传入的fitfunc进行拟合，可以通过对象的fit_result属性在程序中获取拟合参数列表的第一个元素
5. findpeak：寻峰，基于CVIONS的GL_abs_cv

此类可接受的传入的func函数的返回值类型：
1. 列向量：列向量的每一个元素会单独画一个点，然后逐点绘制
2. 行向量：会把行向量理解为一个一维的数据，直接将这个行向量画在图上
3. 标量：正常的逐点绘制
4. 元组：元组的第二个元素是threshold方法的原始数据，原始数据会被保存为npy文件

bug：
1. 不时地会出现实验在运行，但是画图没有更新的情况。
2. 尝试加入保存图片的功能，但是会出现jupyter运行时闪退的问题
"""

import os

from PyQt5.Qt import *
from PyQt5 import QtCore
import pyqtgraph as pg
import threading
import numpy as np
import random
import time
import sys
from files import *
import Fit
from scipy.optimize import curve_fit
from CVIONS import GLcvion, GL_abs_cv
import pyqtgraph.exporters as exporter
from scipy.signal import find_peaks

pg.setConfigOption('background', (190, 190, 190))
pg.setConfigOption('foreground', 'k')

class MyWidget(QWidget):
    def __init__(self, closefunc):
        self.closefunc = closefunc
        super().__init__()
    
    def closeEvent(self, evt):
        result = QMessageBox.question(self, 'Close App', 'Are you sure to close?',QMessageBox.Yes|QMessageBox.No,QMessageBox.No)
        
        if result == QMessageBox.Yes:
            self.closefunc()
            evt.accept()
            QWidget.closeEvent(self, evt)
        else:
            evt.ignore()

class AutoCloseWidget(QWidget):
    def __init__(self, closefunc):
        self.closefunc = closefunc
        super().__init__()

    def closeEvent(self, evt):
        # print(self.children())
        self.closefunc()
        evt.accept()
        QWidget.closeEvent(self, evt)


class AutoDestroyWidget(QWidget):
    def __init__(self):
        super().__init__()

    def closeEvent(self, evt):
        for child in self.children():
            child.deleteLater()

        evt.accept()
        QWidget.closeEvent(self, evt)


class Rtplot():
    def __init__(self, func, stopfunc, fitfunc=None, xdata=None, fileprefix=None, widget=None, autoRun=False, random_x=False):
        self.sign = False  #终止循环子线程标志
        self.pausesign = False  #暂停标志
        self.autoRun = autoRun # Flag for automatically starting the scan and running the fit
        self.i = 0
        if random_x:
            self.xdata = list(np.random.permutation(xdata))
        else:
            self.xdata = xdata  #self.xdata不为None时才会保存数据
        self.xdatadraw = []
        self.ydatadraw = []
        self.func = func  #子线程执行的函数，需在其他py文件定义
        self.fitfunc = fitfunc
        self.fileName = None
        self.filePrefix = fileprefix
        self.folder = None
        self.drawlen = int(600)
        self.drawcolor = [(0,30,220), (20, 155, 55), (200, 40, 0), (0, 0, 0), (0, 255, 0), (255, 0, 0)]

        self.fit_result = [] # For storing the fit result

        # The parameter used for finding peaks
        self.peakheight = 0.1

        # Initialize RawData
        self.RawData = {}
        if xdata is not None:
            for x in xdata:
                self.RawData[x] = []

        self.app = QApplication(sys.argv) # 建立app
        if autoRun:
            self.win = AutoCloseWidget(stopfunc)
        else:
            self.win = MyWidget(stopfunc) # 建立窗口

        self.win.setWindowTitle('CryoTrap')
        self.win.resize(1000,500)
        self.stopbtn = QPushButton('Stop')
        self.startbtn = QPushButton('Start')
        self.pausebtn = QPushButton('Pause')
        self.fitbtn = QPushButton('Fit')
        self.findpeakbtn = QPushButton('FindPeak')
        self.savebtn = QPushButton('save')
        self.fitlabel = QLabel('fitpara = ')
        self.plot = pg.PlotWidget()
        if fileprefix != None:
            self.win.setWindowTitle(self.filePrefix+' '+time.strftime("%Y%m%d %H:%M"))
            self.plot = pg.PlotWidget(title=self.filePrefix+' '+time.strftime("%Y%m%d %H:%M"))



        self.layout = QGridLayout()
        self.layout.setSpacing(15)
        self.win.setLayout(self.layout)
        self.layout.addWidget(self.plot, 0, 0, 1, 6)
        self.layout.addWidget(self.startbtn, 2, 0)    
        self.layout.addWidget(self.stopbtn, 2, 1)
        self.layout.addWidget(self.pausebtn, 2, 2)
        self.layout.addWidget(self.fitbtn, 2, 3)
        self.layout.addWidget(self.findpeakbtn, 2, 4)
        self.layout.addWidget(self.savebtn, 2, 5)
        self.layout.addWidget(self.fitlabel, 1, 1, 1, 3)
        if widget != None:
            self.layout.addWidget(widget, 3, 0, 4, 4)


        
        self.plot.showGrid(True, True, 0.5)
        self.curve = self.plot.plot(pen=pg.mkPen(self.drawcolor[0], width=2))
        # self.curve = self.plot.plot(pen=None, symbol='o', symbolSize=10, symbolBrush=self.drawcolor[0])
        self.fitlabel.setFont(QFont("Roman times", 15, QFont.Bold))
        
        self.pausebtn.setEnabled(False)
        self.fitbtn.setEnabled(False)
        self.findpeakbtn.setEnabled(False)
        self.savebtn.setEnabled(False)
        if autoRun:
            self.startbtn.setEnabled(False)
        
        self.startbtn.clicked.connect(self.threadstart)
        self.stopbtn.clicked.connect(self.stop)
        self.pausebtn.clicked.connect(self.pause)
        self.fitbtn.clicked.connect(self.fit)
        self.findpeakbtn.clicked.connect(self.findpeak)
        self.savebtn.clicked.connect(self.save_pg_fig)
        
        self.win.show()

        if self.autoRun:
            # print("start")
            # self.startbtn.animateClick()
            self.threadstart()

        # sys.exit(self.app.exec_()) # Why enclosing self.app.exec_() in sys.exit()?
        self.app.exec_()


    
    def threadstart(self):  #start button connected function, start a new thread to run the cycle
        self.sign = True
        self.pausebtn.setEnabled(True)
        self.pausebtn.setText('Pause')
        self.fitbtn.setEnabled(False)
        self.t1 = threading.Thread(target=self.cycle)
        self.t1.setDaemon(True)
        self.t1.start()
    
    
    def cycle(self):    # the most important function in this class, which is used to update the figure while running the experiment
        if self.xdata != None and self.filePrefix != None:
            csvFile, file, self.fileName, self.folder = genFile(self.filePrefix, start=min(
                    self.xdata), stop=max(self.xdata))

        self.savebtn.setEnabled(True)
        
        self.ydatadraw=[]
        self.xdatadraw=[]

        
        while self.sign:
            self.startbtn.setEnabled(False)
            if self.pausesign:
                continue
            
            if self.xdata != None:
                res  = self.func(self.xdata[self.i])

                if type(res) is tuple:
                    y, rawdata = res
                    # self.RawData.append(rawdata)
                    # self.RawData.append(np.array([self.xdata[self.i], rawdata],dtype=object))
                    # self.RawData[self.xdata[self.i]] += list(rawdata[0])
                    if self.RawData[self.xdata[self.i]] == []:
                        self.RawData[self.xdata[self.i]] = rawdata
                    else:
                        self.RawData[self.xdata[self.i]] = np.hstack((self.RawData[self.xdata[self.i]], rawdata))
                else:
                    y = res
                try:
                    if type(y) == np.ndarray:
                        csvFile.writerow([self.xdata[self.i]]+y.ravel().tolist())
                        if self.i == 0 and y.shape[1] == 1:
                            self.plot.clear()
                    else:
                        csvFile.writerow([self.xdata[self.i], y])
                except:
                    print("writing file is wrong!")

                if type(y) == np.ndarray and y.shape[0]==1 and y.shape[1]!=1:
                    self.ydatadraw = y[0,:]
                    self.curve.setData(self.ydatadraw)

                elif type(y) == np.ndarray and y.shape[1] == 1 and self.i == 0:
                    self.xdatadraw.append(self.xdata[self.i])
                    self.ydatadraw = [[] for j in range(y.shape[0])]
                    self.curve = []
                    index_list = np.argsort(self.xdatadraw)
                    xdatasort = np.array(self.xdatadraw)[index_list]

                    for j in range(y.shape[0]):
                        self.ydatadraw[j].append(y[j, 0])


                    if y.shape[0] <= len(self.drawcolor):
                        for j in range(y.shape[0]):
                            if j < len(self.drawcolor):
                                self.curve.append(self.plot.plot(pen=None, symbol='o', symbolSize=10, symbolBrush=self.drawcolor[j]))
                                ydatasort = np.array(self.ydatadraw[j])[index_list]
                                self.curve[j].setData(xdatasort, ydatasort)
                            else:
                                pass
                    else:
                        # Curve for the 0th-ion
                        self.curve.append(
                            self.plot.plot(pen=None, symbol='o', symbolSize=10, symbolBrush=self.drawcolor[0]))
                        ydatasort = np.array(self.ydatadraw[0])[index_list]
                        self.curve[0].setData(xdatasort, ydatasort)

                        # Curve for the middle ion
                        curve_j = int(np.round(y.shape[0] / 2))
                        self.curve.append(
                            self.plot.plot(pen=None, symbol='o', symbolSize=10, symbolBrush=self.drawcolor[1]))
                        ydatasort = np.array(self.ydatadraw[curve_j])[index_list]
                        self.curve[1].setData(xdatasort, ydatasort)

                        # Curve for the last ion
                        curve_j = -1
                        self.curve.append(
                            self.plot.plot(pen=None, symbol='o', symbolSize=10, symbolBrush=self.drawcolor[2]))
                        ydatasort = np.array(self.ydatadraw[curve_j])[index_list]
                        self.curve[2].setData(xdatasort, ydatasort)



                elif type(y) == np.ndarray and y.shape[1] == 1 and self.i != 0:
                    if self.i < self.drawlen:
                        self.xdatadraw.append(self.xdata[self.i])
                    else:
                        self.xdatadraw[0:-1] = self.xdatadraw[1:]
                        self.xdatadraw[self.drawlen - 1] = self.xdata[self.i]
                    index_list = np.argsort(self.xdatadraw)
                    xdatasort = np.array(self.xdatadraw)[index_list]
                    for j in range(y.shape[0]):
                        if self.i < self.drawlen:
                            self.ydatadraw[j].append(y[j, 0])
                        else:
                            self.ydatadraw[j][0:-1] = self.ydatadraw[j][1:]
                            self.ydatadraw[j][self.drawlen - 1] = y[j, 0]
                    if y.shape[0] <= len(self.drawcolor):
                        for j in range(y.shape[0]):
                            if j < len(self.drawcolor):
                                ydatasort = np.array(self.ydatadraw[j])[index_list]
                                self.curve[j].setData(xdatasort, ydatasort)
                            else:
                                pass
                    else:
                        # Curve for the 0th-ion
                        ydatasort = np.array(self.ydatadraw[0])[index_list]
                        self.curve[0].setData(xdatasort, ydatasort)

                        # Curve for the middle ion
                        curve_j = int(np.round(y.shape[0] / 2))
                        ydatasort = np.array(self.ydatadraw[curve_j])[index_list]
                        self.curve[1].setData(xdatasort, ydatasort)

                        # Curve for the last ion
                        curve_j = -1
                        ydatasort = np.array(self.ydatadraw[curve_j])[index_list]
                        self.curve[2].setData(xdatasort, ydatasort)

                else:
                    if self.i < self.drawlen:
                        self.xdatadraw.append(self.xdata[self.i])
                        self.ydatadraw.append(y)
                    else:
                        self.xdatadraw[0:-1] = self.xdatadraw[1:]
                        self.ydatadraw[0:-1] = self.ydatadraw[1:]
                        self.xdatadraw[self.drawlen-1] = self.xdata[self.i]
                        self.ydatadraw[self.drawlen-1] = y
                    
                    self.curve.setData(self.xdatadraw, self.ydatadraw)
                self.i+=1
                if self.i >= len(self.xdata):
                    self.i = 0
                    self.fitbtn.setEnabled(True)
                    break
            else:
                y = self.func()
                if type(y) == np.ndarray and y.shape[0]==1 and y.shape[1]!=1:   #用CCD采集binning后的一维数据plot,目前不支持有自定义自变量的plot
                    self.ydatadraw = y[0,:]
                    self.curve.setData(self.ydatadraw)

                elif type(y) == np.ndarray and y.shape[1]==1 and self.i==0:
                    self.ydatadraw = [[] for j in range(y.shape[0])]
                    self.curve = []
                    for j in range(y.shape[0]):
                        self.ydatadraw[j].append(y[j,0])
                        if j<len(self.drawcolor):
                            self.curve.append(self.plot.plot(pen=pg.mkPen(self.drawcolor[j], width=2)))
                            self.curve[j].setData(self.ydatadraw[j])
                        else:
                            pass

                elif type(y) == np.ndarray and y.shape[1]==1 and self.i!=0:
                    for j in range(y.shape[0]):
                        if self.i < self.drawlen:
                            self.ydatadraw[j].append(y[j,0])
                        else:
                            self.ydatadraw[j][0:-1] = self.ydatadraw[j][1:]
                            self.ydatadraw[j][self.drawlen-1] = y[j,0]
                        if j<len(self.drawcolor):
                            self.curve[j].setData(self.ydatadraw[j])
                        else:
                            pass

                else:
                    if self.i < self.drawlen:
                        self.ydatadraw.append(y)
                    else:
                        self.ydatadraw[0:-1] = self.ydatadraw[1:]
                        self.ydatadraw[self.drawlen-1] = y
                
                    self.curve.setData(self.ydatadraw)
                self.i+=1
        self.startbtn.setEnabled(True)
        self.findpeakbtn.setEnabled(True)
        if len(self.RawData) != 0:
            # np.save("data/"+time.strftime("%Y%m")+'/'+time.strftime("%m%d")+'/'+self.filePrefix+time.strftime("%H%M")+".npy", np.array(self.RawData))
            self.RawdataPath = self.folder  + self.filePrefix + '_' + time.strftime("%H%M") + ".npy"
            np.save(self.RawdataPath, np.array([[key,self.RawData[key]] for key in self.RawData.keys()], dtype=object))

        if self.fitfunc != None:
            self.fitbtn.setEnabled(True)
        
        if self.fileName != None:
            file.close()

        if self.autoRun:
            # Automaticaly click the "Fit" button upon finishing the scan
            # print("Automatically run the fit")
            if self.fitfunc != None:
                self.fit()
            else:
                self.findpeak()
        # if self.filePrefix != None:
        #     self.save_pg_fig()

    def stop(self): #stop button connected function
        self.sign = False
        self.pausebtn.setEnabled(False)
        self.pausebtn.setText('Pause')
        self.fitbtn.setEnabled(True)
        self.findpeakbtn.setEnabled(True)
        while self.i != 0:
            time.sleep(0.1)
            if self.t1.is_alive() == False:
                self.i = 0
        
        
    def pause(self):    #pause button connected function
        if not self.pausesign:
            self.pausebtn.setText('Continue')
            self.pausesign = True
            self.fitbtn.setEnabled(True)
        else:
            self.pausebtn.setText('Pause')
            self.pausesign = False
            self.fitbtn.setEnabled(False)
            
    def fit(self):  #fit button connected function
        if self.fitfunc!=None:
            if type(self.ydatadraw[0]) != type([]):
                data = np.transpose(np.array([self.xdatadraw, self.ydatadraw]))
            else:
                data = np.transpose(np.array([self.xdatadraw]+self.ydatadraw))

            datafit = np.zeros((data.shape[0], 2))
            datafit[:, 0] = data[:, 0]

            fitpara0 = []
            for i in range(data.shape[1]-1):
                datafit[:,1] = data[:,i+1]
                try:
                    fitpara_fine, func = self.fitfunc(datafit)
                    fitpara = [round(para, 6) for para in fitpara_fine]
                    # print(fitpara)
                    fitpara0.append(fitpara)
                    xfitdraw = np.linspace(min(self.xdatadraw), max(self.xdatadraw), 200)
                    yfitdraw = func(xfitdraw, *fitpara_fine)
                    self.plot.plot(xfitdraw, yfitdraw, pen=pg.mkPen((200,50,50), style=QtCore.Qt.DotLine, width=1.5))
                except:
                    print("fit error")
                    fitpara = None
                    fitpara0 = None
            if i > 0:
                self.fitlabel.setText('fitpara=' + str(fitpara0))
                self.fitpara = np.array(fitpara0)
                if fitpara0 != None:
                    self.fitlabel.setText('fitpara=' + str(list(self.fitpara[:, 0])))
            else:
                self.fitlabel.setText('fitpara=' + str(fitpara))
                self.fitpara = np.array(fitpara0)
            try:
                self.fit_result = list(self.fitpara[:, 0])
            except:
                self.fit_result = None
        else:
            pass

        if self.autoRun:
            # Automatically close the window
            # print("Automatically close the window")
            time.sleep(2)
            QtCore.QTimer.singleShot(0, self.win.close)


    def findpeak(self): #findpeak button connected function
        # try:
        if type(self.ydatadraw[0]) != type([]):
            ydatafit = np.array(self.ydatadraw)
        else:
            ydatafit = np.mean(np.array(self.ydatadraw), axis=0)

        sortindex = np.argsort(self.xdatadraw)
        self.xdatadraw = np.array(self.xdatadraw)[sortindex]
        ydatafit = np.array(ydatafit)[sortindex]

        # image_lb = GL_abs_cv(np.array(ydatafit), LoG_sigma=1.8, threshold=0.6)
        # # para = cvion_fast_1d(np.array(self.ydatadraw), image_lb)
        # peaknum = np.max(image_lb)
        # peaklist = []
        # for lb in range(1, peaknum+1):
        #     peak = np.mean(np.array(self.xdatadraw)[image_lb==lb])
        #     peaklist.append(round(peak, 4))

        peak, properties = find_peaks(1 - ydatafit, height=self.peakheight, distance=10)
        peaklist = list(np.array(self.xdatadraw)[peak])
        peaklist = [round(peak, 4) for peak in peaklist]
        print(peaklist)
        xfitdraw = list(np.linspace(min(self.xdatadraw), max(self.xdatadraw), 100))+peaklist
        yfitdraw = list(np.zeros(100))+list(np.max(self.ydatadraw)*np.ones(len(peaklist)))
        sortindex = np.argsort(xfitdraw)
        xfitdraw = np.array(xfitdraw)[sortindex]
        yfitdraw = np.array(yfitdraw)[sortindex]
        self.plot.plot(xfitdraw, yfitdraw, pen=pg.mkPen((200,50,50), style=QtCore.Qt.DotLine, width=1.5))
        self.fitlabel.setText('fitpara= '+str(peaklist))
        self.fit_result = peaklist





        # except:
        #     print("Find Peak Error")
        #     self.fitlabel.setText('fitpara= ERROR')

        if self.autoRun:
            # Automatically close the window
            print("Automatically close the window")
            time.sleep(2)
            QtCore.QTimer.singleShot(0, self.win.close)


    def save_pg_fig(self):  #save button connected funciton, still not working well, since it will collapse the whole programme unintentionally
        ex = exporter.ImageExporter(self.plot.plotItem)
        ex.export(self.folder+self.filePrefix+'.png')
        time.sleep(0.2)



class Rtplot_SelectIon(Rtplot):
    '''
    Fit the data of the selected ion
    '''
    def __init__(self, func, stopfunc, ion=[0], xdata=None, fitfunc=None,fileprefix=None, autoRun=False):
        assert xdata is not None
        self.ion = ion
        super().__init__(func, stopfunc, fitfunc=fitfunc, xdata=xdata, fileprefix=fileprefix, widget=None, autoRun=autoRun, random_x=False)

    def fit(self):  #override the fit function so that we only fit the data of the ion we selected

        if self.fitfunc!=None:
            if type(self.ydatadraw[0]) != type([]):
                data = np.transpose(np.array([self.xdatadraw, self.ydatadraw]))
            else:
                data = np.transpose(np.array([self.xdatadraw]+self.ydatadraw))
            datafit = np.zeros((data.shape[0],2))
            fitpara0 = []
            for i in self.ion:
                datafit[:,0] = data[:,0]
                datafit[:,1] = data[:,i+1]
                try:
                    fitpara_fine, func = self.fitfunc(datafit)
                    fitpara = [round(para, 4) for para in fitpara_fine]
                    fitpara0.append(fitpara)
                    xfitdraw = np.linspace(min(self.xdatadraw), max(self.xdatadraw), 200)
                    yfitdraw = func(xfitdraw, *fitpara_fine)
                    self.plot.plot(xfitdraw, yfitdraw, pen=pg.mkPen((200,50,50), style=QtCore.Qt.DotLine, width=1.5))
                except:
                    print("fit error")
                    fitpara = None
                    fitpara0 = None
                    break
            if i > 0:
                self.fitlabel.setText('fitpara='+str(fitpara0))
                self.fitpara = np.array(fitpara0)
            else:
                self.fitlabel.setText('fitpara=' + str(fitpara))
                self.fitpara = np.array(fitpara0)
            try:
                self.fit_result = list(self.fitpara[:, 0])
            except:
                self.fit_result = None
        else:
            pass

        if self.autoRun:
            # Automatically close the window
            # print("Automatically close the window")
            time.sleep(2)
            QtCore.QTimer.singleShot(0, self.win.close)



class RtGetOptPos(Rtplot):

    '''
    This is the class used for find the optimal position of motor in our experiment. It inherits from Rtplot, but it doesn't have
    the fit function and find peak function, and does not support random_x by now
    '''

    def __init__(self, func, stopfunc, yopt, tolerance=0.15, ion=[0], xdata=None, fileprefix=None, autoRun=False):
        assert xdata is not None
        self.ion = ion
        self.yopt = yopt
        self.tolerance = tolerance
        super().__init__(func, stopfunc, fitfunc=None, xdata=xdata, fileprefix=fileprefix, widget=None, autoRun=autoRun, random_x=False)
        print(self.yopt)

    def cycle(self):
        # generate the data file
        if self.filePrefix != None:
            csvFile, file, self.fileName, self.folder = genFile(self.filePrefix, start=min(
                self.xdata), stop=max(self.xdata))

        self.savebtn.setEnabled(True)

        self.ydatadraw = []
        self.xdatadraw = []

        while self.sign:
            self.startbtn.setEnabled(False)
            if self.pausesign:
                continue


            res = self.func(self.xdata[self.i])

            if type(res) is tuple:
                y, rawdata = res
                # self.RawData.append(rawdata)
                self.RawData.append(np.array([self.xdata[self.i], rawdata], dtype=object))
            else:
                y = res
            try:
                if type(y) == np.ndarray:
                    csvFile.writerow([self.xdata[self.i]] + y.ravel().tolist())
                    if self.i == 0 and y.shape[1] == 1:
                        self.plot.clear()
                else:
                    csvFile.writerow([self.xdata[self.i], y])
            except:
                print("writing file is wrong!")

            if type(y) == np.ndarray and y.shape[0] == 1 and y.shape[1] != 1:
                print("The input is a row, not suitable for the RtGetOptPos")
                break

            elif type(y) == np.ndarray and y.shape[1] == 1 and self.i == 0: #the first point for multi ion, create ydata array to save the state of different ions
                self.xdatadraw.append(self.xdata[self.i])
                self.ydatadraw = [[] for j in range(y.shape[0])]
                self.curve = []
                index_list = np.argsort(self.xdatadraw)
                xdatasort = np.array(self.xdatadraw)[index_list]
                for j in range(y.shape[0]):
                    self.ydatadraw[j].append(y[j, 0])
                    if j < len(self.drawcolor):
                        self.curve.append(self.plot.plot(pen=pg.mkPen(self.drawcolor[j], width=2)))
                        ydatasort = np.array(self.ydatadraw[j])[index_list]
                        self.curve[j].setData(xdatasort, ydatasort)
                    else:
                        pass

            elif type(y) == np.ndarray and y.shape[1] == 1 and self.i != 0: # draw curve for multi ion
                if self.i < self.drawlen:
                    self.xdatadraw.append(self.xdata[self.i])
                else:
                    self.xdatadraw[0:-1] = self.xdatadraw[1:]
                    self.xdatadraw[self.drawlen - 1] = self.xdata[self.i]
                index_list = np.argsort(self.xdatadraw)
                xdatasort = np.array(self.xdatadraw)[index_list]
                for j in range(y.shape[0]):
                    if self.i < self.drawlen:
                        self.ydatadraw[j].append(y[j, 0])
                    else:
                        self.ydatadraw[j][0:-1] = self.ydatadraw[j][1:]
                        self.ydatadraw[j][self.drawlen - 1] = y[j, 0]
                    if j < len(self.drawcolor):
                        ydatasort = np.array(self.ydatadraw[j])[index_list]
                        self.curve[j].setData(xdatasort, ydatasort)
                    else:
                        pass

            else:   # draw curve for single ion
                if self.i < self.drawlen:
                    self.xdatadraw.append(self.xdata[self.i])
                    self.ydatadraw.append(y)
                else:
                    self.xdatadraw[0:-1] = self.xdatadraw[1:]
                    self.ydatadraw[0:-1] = self.ydatadraw[1:]
                    self.xdatadraw[self.drawlen - 1] = self.xdata[self.i]
                    self.ydatadraw[self.drawlen - 1] = y

                self.curve.setData(self.xdatadraw, self.ydatadraw)
            self.i += 1
            if self.i > 1:
                dy = np.abs(np.mean(y[self.ion]-np.array(self.ydatadraw)[self.ion][:,-2]))
            else:
                dy = self.yopt
            if np.abs(np.mean(y[self.ion])) > (1-self.tolerance) * self.yopt and dy<self.tolerance*self.yopt:
                print("find optimal position successfully")
                break

            if self.i >= len(self.xdata):
                self.i = 0
                self.fitbtn.setEnabled(True)
                break

        if len(self.RawData) != 0:
            # np.save("data/"+time.strftime("%Y%m")+'/'+time.strftime("%m%d")+'/'+self.filePrefix+time.strftime("%H%M")+".npy", np.array(self.RawData))
            self.RawdataPath = self.folder + self.filePrefix + '_' + time.strftime("%H%M") + ".npy"
            np.save(self.RawdataPath, np.array(self.RawData))

        if self.fitfunc != None:
            self.fitbtn.setEnabled(True)

        if self.fileName != None:
            file.close()

        if self.autoRun:
            # Automatically close the window
            # print("Automatically close the window")
            time.sleep(2)
            QtCore.QTimer.singleShot(0, self.win.close)


class RtVideo_Timer():
    def __init__(self, func, stopfunc, ImageSize=(510, 100),
                 TimerTime=None, Timerfunc=None,
                 Timerargs=None, autoRun=False, autoscale=True):
        self.sign = False  # 终止循环子线程标志
        self.pausesign = False  # 暂停标志
        self.autoRun = autoRun  # Flag for automatically starting the scan and running the fit
        self.i = 0
        self.autoscale = autoscale
        self.t1 = None
        # if random_x:
        #     self.xdata = list(np.random.permutation(xdata))
        # else:
        #     self.xdata = xdata  # self.xdata不为None时才会保存数据
        # self.xdatadraw = []
        # self.ydatadraw = []
        self.image = np.zeros(ImageSize)
        self.func = func  # 子线程执行的函数，需在其他py文件定义
        self.stopfunc = stopfunc  # 点击stop button时会发生的事
        # self.fitfunc = fitfunc
        self.TimerTime = TimerTime  # unit -- s
        self.Timerfunc = Timerfunc
        self.Timerargs = Timerargs
        # self.fileName = None
        # self.filePrefix = fileprefix
        # self.folder = None
        self.LabelText = None
        self.hopping_time = None
        # self.drawlen = int(600)
        # self.drawcolor = [(0, 30, 220), (20, 155, 55), (220, 30, 0), (0, 0, 0)]

        # self.fit_result = []  # For storing the fit result

        # # The parameter used for finding peaks
        # self.peakheight = 0.1

        # # Initialize RawData
        # self.RawData = {}
        # if xdata is not None:
        #     for x in xdata:
        #         self.RawData[x] = []

        self.app = QApplication(sys.argv)  # 建立app

        # self.win = QWidget()  # 建立窗口
        self.win = AutoDestroyWidget()

        self.win.setWindowTitle('CryoTrap')
        self.win.resize(1000, 900)
        self.stopbtn = QPushButton('Stop', parent=self.win)
        self.startbtn = QPushButton('Start', parent=self.win)
        self.pausebtn = QPushButton('Pause', parent=self.win)
        # self.fitbtn = QPushButton('Fit')
        # self.findpeakbtn = QPushButton('FindPeak')
        # self.savebtn = QPushButton('save')
        self.fitlabel = QLabel('0', parent=self.win)

        # self.startbtn.setGeometry(0, 0, 100, 40)
        # self.stopbtn.setGeometry(200, 0, 100, 40)
        # self.pausebtn.setGeometry(400, 0, 100, 40)
        # self.fitlabel.setGeometry(10, 150, 500, 40)
        # self.graphicslayout = pg.GraphicsLayoutWidget(parent=self.win)
        # self.viewbox = self.graphicslayout.addViewBox(row=0, col=0)
        # self.viewbox.resize(400, 80)
        # self.viewbox.setAspectLocked(True)
        self.plot = pg.ImageView(parent=self.win)

        self.plot.ui.histogram.hide()
        self.plot.ui.menuBtn.hide()
        self.plot.ui.roiBtn.hide()

        # self.plot.show()
        self.plot.setImage(self.image)

        # self.plotwidget = MatplotlibWidget(parent=self.win)
        # self.fig = self.plotwidget.getFigure()
        # self.ax = self.fig.subplots()
        # self.ax.imshow(self.image)
        # if fileprefix != None:
        #     self.win.setWindowTitle(self.filePrefix + ' ' + time.strftime("%Y%m%d %H:%M"))
        #     self.plot = pg.ImageView(title=self.filePrefix + ' ' + time.strftime("%Y%m%d %H:%M"))
        if self.TimerTime != None and self.Timerfunc != None:
            self.Timer = QtCore.QTimer()
            self.Timer.timeout.connect(self.TimeoutExecFunc)

        self.win.setWindowTitle(time.strftime("%Y%m%d %H:%M"))

        self.layout = QGridLayout()
        self.layout.setSpacing(15)
        self.win.setLayout(self.layout)
        self.layout.addWidget(self.plot, 0, 0, 1, 3)
        self.layout.addWidget(self.startbtn, 2, 0)
        self.layout.addWidget(self.stopbtn, 2, 1)
        self.layout.addWidget(self.pausebtn, 2, 2)
        # self.layout.addWidget(self.fitbtn, 2, 3)
        # self.layout.addWidget(self.findpeakbtn, 2, 4)
        # self.layout.addWidget(self.savebtn, 2, 5)
        self.layout.addWidget(self.fitlabel, 1, 1, 1, 3)
        # if widget != None:
        #     self.layout.addWidget(widget, 3, 0, 4, 4)

        # self.plot.showGrid(True, True, 0.5)
        # self.curve = self.plot.plot(pen=pg.mkPen(self.drawcolor[0], width=2))
        # self.curve = self.plot.plot(pen=None, symbol='o', symbolSize=10, symbolBrush=self.drawcolor[0])
        self.fitlabel.setFont(QFont("Roman times", 15, QFont.Bold))

        self.pausebtn.setEnabled(False)
        # self.fitbtn.setEnabled(False)
        # self.findpeakbtn.setEnabled(False)
        # self.savebtn.setEnabled(False)
        if autoRun:
            self.startbtn.setEnabled(False)

        self.startbtn.clicked.connect(self.threadstart)
        self.stopbtn.clicked.connect(self.stop)
        self.pausebtn.clicked.connect(self.pause)
        # self.fitbtn.clicked.connect(self.fit)
        # self.findpeakbtn.clicked.connect(self.findpeak)
        # self.savebtn.clicked.connect(self.save_pg_fig)

        self.win.show()

        if self.autoRun:
            # print("start")
            # self.startbtn.animateClick()
            self.threadstart()

        # sys.exit(self.app.exec_()) # Why enclosing self.app.exec_() in sys.exit()?
        self.app.exec_()

    def cycle(self):  # the most important function in this class, which is used to update the figure while running the experiment
        # self.savebtn.setEnabled(True)


        t0 = time.time()
        while self.sign:
            self.startbtn.setEnabled(False)
            if self.pausesign:
                continue

            res = self.func()
            if type(res) == tuple:
                image_new, pos = res
                self.LabelText = str(len(pos))
                if self.i == 0:
                    if len(pos) > 1:
                        self.hopping_time = 0
                        pos_old = pos
                else:
                    pos_new = pos
                    hopping = self.Hopping_detect(pos_old, pos_new)
                    self.hopping_time += hopping
                    if hopping == 1:
                        print("hopping on %s"%time.strftime("%H-%M-%S"))
                        print(time.time()-t0)
                    pos_old = pos

                # Num = len(pos)
            else:
                image_new = res
            if self.i == 0:
                y_scale = np.max(image_new)-np.min(image_new)




            if self.autoscale:
                self.image = image_new/(np.max(image_new)-np.min(image_new))
            else:
                self.image = image_new/y_scale
            # self.plot.autoLevels()
            self.plot.setImage(self.image)
            # self.ax.imshow(self.image)
            if self.LabelText != None:
                self.fitlabel.setText(self.LabelText)

            time.sleep(0.2)

            self.i = 1

        self.startbtn.setEnabled(True)
        # self.findpeakbtn.setEnabled(True)

        # if self.fitfunc != None:
        #     self.fitbtn.setEnabled(True)

    def threadstart(self):  # start button connected function, start a new thread to run the cycle
        if self.TimerTime != None and self.Timerfunc != None:
            self.Timer.setSingleShot(True)
            self.Timer.start(self.TimerTime * 1000)

        self.sign = True
        self.i = 0
        self.pausebtn.setEnabled(True)
        self.pausebtn.setText('Pause')
        # self.fitbtn.setEnabled(False)
        self.t1 = threading.Thread(target=self.cycle)
        self.t1.daemon = True
        self.t1.start()

    def stop(self):  # stop button connected function
        self.sign = False
        self.i = 0
        if self.TimerTime != None and self.Timerfunc != None:
            self.Timer.stop()
            while self.Timer.isActive():
                time.sleep(0.05)
            print("Timer stop")
        if self.t1 != None:
            while self.t1.is_alive():
                time.sleep(0.05)
        print("threading stop")
        self.stopfunc()
        self.pausebtn.setEnabled(False)
        self.pausebtn.setText('Pause')
        # self.fitbtn.setEnabled(True)
        # self.findpeakbtn.setEnabled(True)

        if self.hopping_time != None:
            print("hopping time=%d"%(self.hopping_time))

    def pause(self):  # pause button connected function
        if not self.pausesign:
            self.pausebtn.setText('Continue')
            self.pausesign = True
            # self.fitbtn.setEnabled(True)
        else:
            self.pausebtn.setText('Pause')
            self.pausesign = False
            # self.fitbtn.setEnabled(False)

    def TimeoutExecFunc(self):
        self.sign = False
        while self.t1.is_alive():
            time.sleep(0.02)
        print("threading stop")

        if self.Timerargs != None:
            self.Timerfunc(self.Timerargs)
        else:
            self.Timerfunc()
        time.sleep(0.5)
        if self.hopping_time != None:
            print("hopping time=%d"%(self.hopping_time))
        self.win.close()


    def fit(self):
        pass

    def findpeak(self):
        pass

    def Hopping_detect(self, x1, x2, threshold_diff=6):
        if len(x2) != len(x1):
            return 1
        else:
            diff_x = np.abs(np.array(x2) - np.array(x1))
            max_difference = np.max(diff_x)
            if max_difference > threshold_diff:
                return 1
            else:
                return 0

    # def save_pg_fig(self):  # save button connected funciton, still not working well, since it will collapse the whole programme unintentionally
    #     ex = exporter.ImageExporter(self.plot.ImageItem)
    #     year_month = time.strftime("%Y%m")
    #     date_now = time.strftime("%m%d")
    #     self.folder = "E:\\PyPrograms\\210sequencer\\data\\%s\\%s\\" % (year_month, date_now)
    #     ex.export(self.folder + self.filePrefix + '.png')
    #     time.sleep(0.1)
            
    
           


    
    
if __name__ == '__main__':
    import matplotlib.pyplot as plt


    def newdata(x):
        y0 = 0.5 * Fit.cosgaussian(x, 2, 1, 0.02) + 0.5 * Fit.cosgaussian(x, 2.85, 1, 0.02)
        y1 = Fit.cosgaussian(x, 1.5, 0.5, 0.4) + 0.2 * (random.random() - 0.5)
        y2 = Fit.cosgaussian(x, 2.5, 0.6, 0.4) + 0.2 * (random.random() - 0.5)
        y3 = Fit.cosgaussian(x, 1, 0.6, 0.6) + 0.2 * (random.random() - 0.5)
        # y=np.array([[y0],[y1],[y2],[y3]])
        y = np.array([[y0], [y1]])
        time.sleep(0.1)

        return y


    def newImage():
        x = np.linspace(-5, 5, 100)
        y = np.linspace(-3, 3, 510)
        X, Y = np.meshgrid(x, y)
        Z = np.exp(-(X ** 2 + Y ** 2) / 2)
        image = 0.1 * np.random.rand(510, 100)
        image = 5000*(Z + image)

        return image


    def stopfunc():
        print("exitting now! please waiting~")
        time.sleep(1)

    def timerfunc(x):
        print(x)
        print("Timer is timeout")

    x = list(np.linspace(0, 5, 100))
    for i in range(2):
        rp = RtVideo_Timer(newImage, stopfunc, TimerTime=5, Timerfunc=timerfunc, Timerargs=1, autoRun=True)
        # time.sleep(1)
        del rp

    # print(rp.xdata)
    # print(rp.ydatadraw)

    # def rtplotloop():
    #     for i in range(2):
    #         rp = Rtplot(newdata, stopfunc, xdata=x, fileprefix='rptest', autoRun="True")
    #         del rp

    # rtplotloop()

    print("exit successfully")
    
