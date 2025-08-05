# @author: xiaoshe
# -*- coding: utf-8 -*-
import ctypes
import time

def reverse_every_16_bytes(byte_array):
    # 将字节数组分成每16字节一组
    chunks = [byte_array[i : i + 16] for i in range(0, len(byte_array), 16)]

    # 对每一组进行翻转
    reversed_chunks = [chunk[::-1] for chunk in chunks]

    # 将翻转后的组合并成一个新的字节数组
    return b"".join(reversed_chunks)


def print_hex(bytes):
    l = [hex(int(i)) for i in bytes]
    print(l)


def extract_16byte_numbers(data):
    """
    将数据每 16 个字节提取为一个大数，组成数组返回。

    参数:
    - data: bytes 或 bytearray 类型，表示输入的二进制数据。

    返回:
    - 一个数组，每个元素是从 16 字节解析出的整数。
    """
    # 检查输入长度是否为16的倍数
    if len(data) % 16 != 0:
        raise ValueError("Input data length must be a multiple of 16 bytes.")
    else:
        numbers = []
        for i in range(0, len(data), 16):
            # 提取16字节
            chunk = data[i : i + 16]
            # 将16字节转化为无符号整数-大端序
            number = int.from_bytes(chunk, byteorder="big", signed=False)
            numbers.append(number)

    return numbers


def ttl_config_init(bits):
    number = 0
    for i in range(0, 32, 1):
        number += bits[i] << i
    return number


class DRIVERELEC:
    # 设置动态链接库中的函数名称，使得下面的python代码可以调用C++中的函数
    # 进行了数据转换，上层调用时只用考虑python数据类型即可
    def __init__(self, path):
        self.lib = ctypes.cdll.LoadLibrary(path)  # 导入C++编译生成的动态链接库

    # 序列执行
    def sys_trigger(self,DeviceID:str):
        DeviceIDByte = DeviceID.encode("utf-8")
        self.lib.sys_trigger(DeviceIDByte)

    # 数据收集
    def start_streaming(self,ttlID:str, Time):
        ttlIDByte = ttlID.encode("utf-8")
        self.lib.start_streaming(ttlIDByte, 200000)

    def get_latest_data(self,buffer,buffer_size):
        """
        获取最新数据，放进缓存区里 TODO:这里的解释不一定准确
        """  
        n = self.lib.get_latest_data(buffer,buffer_size)
        return n 
    
    def stop_streaming(self):
        """
        停止数据收集
        """
        self.lib.stop_streaming()
        
    # Load Data
    # TODO: 取消文件操作，使用别的数据结构方便中间层表示，重构将init操作更加精简，使用一个函数完成
    def ttl_init(self, ttlID: str, path: str): 
        """
        通过输入路径加载对应ttl的指令
        r'D:\qzz\riscq_test\TTL_16bit.txt'
        注意有反斜杠的转义符
        """
        ttlIDByte = ttlID.encode("utf-8")
        pathByte = path.encode("utf-8")
        self.lib.ttl_init(ttlIDByte, pathByte)
        time.sleep(0.1)
    
    def awg_ddr_init(self, awgID:str,path:str):
        """
        通过输入路径加载对应ttl的指令
        r'D:\qzz\riscq_test\TTL_16bit.txt'
        注意有反斜杠的转义符
        """
        awgIDByte = awgID.encode("utf-8")
        pathByte  = path.encode("utf-8")
        self.lib.awg_ddr_init(awgIDByte,pathByte)
        time.sleep(0.1)

    def sys_reset(self, DeviceID: str):
        """
        用于对PXIE机箱进行硬件复位
        """
        DeviceIDByte = DeviceID.encode("utf-8")
        self.lib.sys_reset(DeviceIDByte)

    def sys_ttl_status(self, ttlID: str, ttl_config):
        ttlIDByte = ttlID.encode("utf-8")
        ttl_config_InitNum = ttl_config_init(ttl_config)
        self.lib.sys_ttl_status(ttlIDByte, ttl_config_InitNum)

    def awg_sync_delay_load(self, awgID: str, delay):
        """
        awgID: AWG设备ID
        delay: 延时值，单位为ns，0-200之间选择
        通常校准阶段以10为步长进行扫描
        """
        awgIDByte = awgID.encode("utf-8")
        self.lib.awg_sync_delay_load(awgIDByte, delay)

    def awg_calib_status(self, awgID: str):
        """
        用于在输入同步延迟值之后观察同步状态，如果同步出错，则返回1，如果同步成功则返回0
        """
        awgIDByte = awgID.encode("utf-8")
        flag = self.lib.awg_calib_status(awgIDByte)
        return flag

    def awg_sync_delay_again(self, awgID: str):
        """
        用于再次输入新的同步延迟值之前的复位
        """
        awgIDByte = awgID.encode("utf-8")
        self.lib.awg_sync_delay_again(awgIDByte)

    def awg_sync_delay_success(self, awgID: str):
        """
        用于通知板卡校准完成
        """
        # 执行本指令意思是调整延时完成，可以进行正常操作
        awgIDByte = awgID.encode("utf-8")
        self.lib.awg_sync_delay_success(awgIDByte)

    def awg_dac_sync_success(self,awgID:str):
        """
        用于查询DAC上电同步状态
        对于单个DAC来说，上电同步状态完成从板卡上查询到的状态是0x30，由于每次查询到的是32bit数据，因此将4片DAC状态合并为32bit,0x30303030表示4片DAC均上电同步成功
        """
        awgIDByte = awgID.encode("utf-8")
        DacStatus = self.lib.awg_dac_sync_success(awgIDByte)
        return DacStatus
    
    def awg_dac_freq(self,awgID:str,BoardID:int):
        """
        用于查询DAC当前输出的主频
        BoardID: DAC板卡ID，0，1，2，3
        由于设定的频率字的位宽是32位，但是会出现频率大于250M的情况，因此实际位宽是34位，而查询寄存器的位宽是32位，因此截取频率字的高32位进行读出，由于去掉了低两位，因此还原数据应该是freq/2^30*250
        """
        awgIDByte = awgID.encode("utf-8")
        Freq = self.lib.awg_dac_freq(awgIDByte,BoardID)
        Freq = Freq/2**30*250
        return Freq


# 具体使用
# ttl_config_init_num = ttl_config_init(ttl_in_out_config)

# print(type(ttl_config_init_num))
# print(type(ttl0))
