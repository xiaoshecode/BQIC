Calib.py是管理连接设备，完成各设备协同运行实验的脚本。里面有封装好的自动化校准函数（函数名称中一般带有“cal”字样）以及封装好的实验序列生成函数（函数名称中一般带有“seq”字样）。这个程序是运行实验的最核心程序。

.ipynb文件为jupyter notebook文件用于调用Calib.py中定义的类中的函数并结合每个实验实际的需求完成实验。

CVIONS.py里面是离子识别以及态判断的相关算法。
files.py里面包含文件读写相关的函数。
Fit.py是完成函数拟合的相关函数，可以被其他程序（主要是rtplot.py生成的ui对象）调用方便进行拟合和画图

rtplot.py：简单的用于实时绘制的UI界面，可被其他程序调用。

DDS.py，DDS1.py：DDS控制程序。
E8663D.py：罗德信号源和keysight信号源的控制程序。
spectrum_awg_2channel.py：spectrum awg的控制程序，用于sequence replay模式的双通道输出。里面还封装了一些便于生成我们实验所需的awg波形点列的函数。
spectrum_awg_SR.py：spectrum awg的控制程序，用于single restart模式输出。
sequencer.py：郭伟轩sequencer控制程序。

Configuration文件夹内主要存放实验相关的json，包括了存储校准参数结果的json文件，dds的参数文件，sequencer的序列命令定义文件。
simulation文件夹内主要存放一些理论模拟的相关程序。
