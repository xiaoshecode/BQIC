import ctypes,os
# import chardet
# import binascii
# import sys
# from sys import getsizeof
# import numpy as np
# import math
# import time
# import matplotlib.pyplot as plt
# import scipy as sp
# from scipy.optimize import curve_fit
# from scipy.fftpack import fft,ifft
# from scipy import signal
# # import librosa
# import numpy.ctypeslib as npct
# from scipy.stats import norm

# D:\code\BQIC\CompilerDev\PXIEInterfaceAPI\Driver_isa0826.dll
DRIVER_ELEC = ctypes.cdll.LoadLibrary(r"D:\code\BQIC\CompilerDev\PXIEInterfaceAPI\Driver_isa0826.dll")


awg0 = '0008'.encode('utf-8')


DRIVER_ELEC.awg_sync_delay_load(awg0, 150) #调整通道延时
# time.sleep(0.1)
# DRIVER_ELEC.awg_sync_delay_success(awg0) #执行本指令意思是调整延时完成，可以进行正常操作

# tcm = '0005'.encode('utf-8')
# DRIVER_ELEC.sys_reset(tcm)


# DRIVER_ELEC.awg_ddr_init(awg0, r"C:\CODE\BQIC\CompilerDev\Output\inst_header.txt".encode('utf-8'))
# time.sleep(0.1)
# DRIVER_ELEC.awg_ddr_init(awg0, r"C:\CODE\BQIC\CompilerDev\Output\DatawithHeader.txt".encode('utf-8'))
# time.sleep(0.1)

# DRIVER_ELEC.sys_trigger(tcm)

# dac_status = DRIVER_ELEC.awg_dac_sync_success(awg0)
# if dac_status == 0x30303030:
#     print('dac sync success')
# else:
#     print('dac sync failed')


# freq = DRIVER_ELEC.awg_dac_freq(awg0, 0)
# freq = freq/2**30*250
# print(freq)