# Opfunc

这个文件夹用来管理所有的上层设备驱动程序，包含每个设备允许操作的所有集合。
优点：使用寄存器寻址的方式尽可能提高通用性

## 派生结构

基类：OpfuncDevice

派生类：OpfuncRF、OpfuncPulse
TODO: OpfuncTDC...

OpfuncRF设备层Driver: OpfuncRF_DDS、OpfuncRF_AWG
OpfuncPulse设备层Driver: OpfuncPulse_TTL

## 设备操作
OpfuncDevice: 初始化一个设备
- init()
- open()
- close()
- reset()
- set()
- get()

OpfuncRF: 初始化一个RF设备
- init()
- open()
- close()
- reset()
- set() 需要重构
- get() 需要重构

OpfuncRF_DDS: 生成一个DDS设备，缓存自己的状态，并且通过set()发送命令
- init()
- open()
- close()
- reset()
- gen_assembler() #生成自己的命令
- set()
- get() # 获取频率、幅度、相位

OpfuncRF_AWG: 生成一个AWG设备，缓存自己的状态，并且通过set()发送命令
- init()
- open()
- close()
- reset()
- gen_assembler() #生成自己的命令
- set()
- get() # 获取波形、幅度、相位
- set_waveform() # 根据参数设置波形

OpfuncPulse: 初始化一个Pulse设备
- init()
- open()
- close()
- reset()
- set()
- get()
- gen_assembler() #生成自己的命令

