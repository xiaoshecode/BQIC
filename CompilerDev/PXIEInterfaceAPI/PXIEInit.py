import PXIEUtils

import ctypes, os
import time
import numpy as np

# sys_ttl_status(ttl0,ttl_config_init_num)
# ttl0 = "0007".encode("utf-8")
# ttl_config_init_num = ttl_config_init(ttl_in_out_config)

class PXIEDriver:
    def __init__(self, DriverPath,ttl_in_out_config):
        self.DRIVER_ELEC = PXIEUtils.DRIVERELEC(DriverPath) # 载入动态链接库
        self.awg0 = "0005"# 以str保存，在底层会转换为bytes
        self.awg1 = "000d"
        self.ttl0 = "0007"
        self.ttlconfig = ttl_in_out_config

    def init_ttl_config(self, ttl_in_out_config=None):
        # 如果有ttl_in_out_config 参数，则更新，否则保持原样
        if ttl_in_out_config is not None:
            self.ttlconfig = ttl_in_out_config
        self.DRIVER_ELEC.sys_ttl_status(self.ttl0, self.ttlconfig)

    def init(self, DeviceID, delay=90):
        # 机箱初次上电校准
        self.DRIVER_ELEC.awg_sync_delay_load(DeviceID, delay)
        self.DRIVER_ELEC.awg_calib_status(DeviceID)
        self.DRIVER_ELEC.awg_sync_delay_again(DeviceID)
        self.DRIVER_ELEC.awg_sync_delay_success(
            DeviceID
        )  # 执行本指令意思是调整延时完成，可以进行正常操作

    def HardReset(self, DeviceID):
        """
        用于对PXIE机箱进行硬件复位
        """
        self.DRIVER_ELEC.sys_reset(DeviceID)
        self.init_ttl_config()  # 重新设置TTL配置
    
    def LoadSeq(self,DeviceType, DeviceID, Inst):
        """
        DeviceType 目前有两种：0-DDS; 1-AWG; 2-TTL TODO：AWG暂无
        DeviceID: 设备ID
        Inst: 编译器编译出的指令
        """
        if DeviceType == "DDS" or DeviceType == 0:
            self.DRIVER_ELEC.awg_ddr_init(DeviceID, Inst)
        elif DeviceType == "TTL" or DeviceType == 2:
            self.DRIVER_ELEC.ttl_init(DeviceID, Inst)
    
    def SysTrigger(self,DeviceID):
        """
        用于对PXIE机箱进行系统触发，使得系统开始运行
        """
        self.DRIVER_ELEC.sys_trigger(DeviceID)

    def ReceiveData(self,DeviceID, TimeOut: int = 200000):
        """
        用于收集数据，从同步角度考虑，序列运行指令和序列复位指令都是在TTL板卡上接收，再由TCM板卡同步路由到所有板卡实现同步
        DeviceID: 设备ID
        TimeOut: 超时时间，单位为ms，默认200000ms（200秒）

        """
        buffer = ctypes.create_string_buffer(4096) # 创建一个4K的缓冲区
        self.DRIVER_ELEC.start_streaming(DeviceID, TimeOut) # DeviceID: 设备ID，TimeOut: 超时时间
        max_iterations = 100
        iteration = 0 
        try:
            while iteration < max_iterations:
                n = self.DRIVER_ELEC.get_latest_data(buffer, 4096)
                if n > 0:
                    data = np.frombuffer(buffer.raw[:n], dtype=np.uint8)
                    # print("Received data:", data)
                else:
                    time.sleep(1)
                    print("No data received, waiting...") 
                iteration += 1
        finally:
            self.DRIVER_ELEC.stop_streaming()


    def Calibrate4One(self, DeviceID, MaxDalay=200, step=10):
        """
        用于校准PXIE机箱的同步延时，同一机箱第一次上电之后可以将最终的同步延迟进行记录，同一个机箱下一次开机可以直接输入最终的同步延迟值而无需重复进行校准
        """
        flags = []
        for delay in range(0, MaxDalay + 1, step):
            self.DRIVER_ELEC.awg_sync_delay_load(DeviceID, delay)
            time.sleep(10)
            flag = self.DRIVER_ELEC.awg_calib_status(DeviceID)
            flags.append(flag)
            self.DRIVER_ELEC.awg_sync_delay_again(DeviceID)
            time.sleep(1)
        # 最终输出值为[1 1 1 1 1 0 0 0 0 0 0 0 0 0 1 1 1 1 1 1]
        # # 其中0表示同步成功，1表示同步失败，取最中间值0的索引对应的同步延迟输入值
        minIndex = None
        maxIndex = None
        for i in range(len(flags)):
            if flags[i] == 0:
                minIndex = i
                break
        for i in range(len(flags) - 1, -1, -1):
            if flags[i] == 0:
                maxIndex = i
                break
        if minIndex is not None and maxIndex is not None:
            if minIndex == maxIndex:
                Delay = minIndex * step
            else:
                # 保证为整数
                Delay = int(0 + (minIndex + maxIndex) / 2 * step)
            print("同步延迟值:", Delay)
            # 修改延迟
            self.SetDeley(DeviceID, Delay)
            # 返回同步延迟值
            return Delay
        else:
            print("未找到同步成功的延迟值")
            return -1

    def SetDeley(self, DeviceID, Delay):
        """
        用于设置同步延迟值
        """
        self.DRIVER_ELEC.awg_sync_delay_load(DeviceID, Delay)
        time.sleep(0.1)
        self.DRIVER_ELEC.awg_sync_delay_success(DeviceID)

    def SetTTL(self, DeviceID, ttl_config):
        """
        用于设置TTL配置
        """
        self.DRIVER_ELEC.sys_ttl_status(DeviceID, ttl_config)
    
if __name__ == "__main__":
    pass
    # 测试代码
    # flags = [1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
    # print("flags:", flags)
    # print("len(flags):", len(flags))
    # step = 10
    # for i in range(len(flags)):
    #     if flags[i] == 0:
    #         minIndex = i
    #         print("minIndex:", minIndex)
    #         break
    # for i in range(len(flags) - 1, -1, -1):
    #     if flags[i] == 0:
    #         maxIndex = i
    #         print("maxIndex:", maxIndex)
    #         break
    # if minIndex == maxIndex:
    #     delay = minIndex * step
    # else:
    #     # 保证为整数
    #     Delay = int(0 + (minIndex + maxIndex) / 2 * step)
    # print("Delay:", Delay)

    path = r'D:\qzz\riscq_test\TTL_32bit.txt'  # 这样就能直接生成带反斜杠的字符串
    print(path)
    # r'D:\qzz\riscq_test\TTL_32bit.txt' 生成这个字符串
