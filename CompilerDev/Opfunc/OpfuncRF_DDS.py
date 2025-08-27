from Opfunc.OpfuncDevice import OpfuncRF
# from OpfuncDevice import OpfuncRF  # 基类,调试用

class OpfuncRF_DDS(OpfuncRF):  # 这里针对Bell设备DDS完成子类
    def __init__(self, DeviceID):
        super().__init__(DeviceID)
        self.Freq_clk = 250 * 10**6  # 板载时钟频率250MHz
        self.Channel = 6 # 一个dds输出端口支持6个频率、相位、幅度可调的输出
        self.Freq = 0  # 24bit
        self.Amp = 0  # 16bit
        self.Phase = 0  # 24bit
        self.Delay = 0  # 32bit
        self.array_128bit = {0:[], 1:[], 2:[], 3:[], 4:[], 5:[]} #存储6个频率的128bit数据

    # 保留父类的方法，待后续扩展
    # def open(self):
    #     super().open()

    # def close(self):
    #     super().close()

    def reset(self):
        self.array_128bit = {0:[], 1:[], 2:[], 3:[], 4:[], 5:[]} #存储6个频率的128bit数据
        self.Freq = 0
        self.Amp = 0
        self.Phase = 0
        self.Delay = 0

    def read_state(self): # 读取当前状态 #TODO 设置查询参数的状态
        # super().read()
        return self.Freq , self.Amp, self.Phase, self.Delay

    def write(self):
        return super().write()

    def setwaveform(self, Freq:float = 0, Amp:float = 0.5, Phase:float = 0.0, Delay:int = 0):  # 添加十进制数据f、a、p、t
        """
        f: 频率，单位MHz，范围[0-400]
        a: 振幅，范围[0-1]
        p: 相位，范围[0-1]
        t: 延迟，单位us, 使用时间
        """
        if not all(
            0 <= x < 2**32 for x in [self.Freq, self.Amp, self.Phase, self.Delay]
        ):
            raise ValueError("All parameters should be 32-bit integers(0 <= x < 2**32)")
        else:
            self.Freq = Freq
            self.Amp = Amp
            self.Phase = Phase
            self.Delay = Delay

    def gen_assembler(self,channel):  # 转换a/f/p信息为二进制命令
        # TODO: 将通道的命名加上
        Freq_bin = int(self.Freq * 2**32 / 250)  # part1 f0 = K/2^32 * Fclk
        Phase_bin = int(self.Phase * 2**32)  # part2 p0 = K/2^32,p=[0,1]
        Amp_bin = int(self.Amp * 2**16)  # part3 Amp = K/2^16
        Delay_bin = int(self.Delay/4*1000) # 换算成时钟周期4ns 单位us
        full_128 = (int(Delay_bin)<<98) | (int(Freq_bin) << 64) | (int(Phase_bin)<< 32) | int(Amp_bin) #时间平移了2位，平移98位
        # full_128 是一个十进制数，将其转换为16进制数并补齐32位
        full_128hex = full_128.to_bytes(16, byteorder='big')
        
        self.array_128bit[channel].append(full_128hex)

    def read_arrays(self):
        return self.array_128bit
    
    def adjust_array_length(self):
        # 0xFF_FF_FF_FF
        #   FF_FF_FF_FF
        #   FF_FF_FF_FF
        #   FF_FF_FF_FF
        # self.array_128bit.append(b'\xFF'*16)
        # self.array_32bit.append(b'\xFF'*4)
        pass 

    def getDeviceID(self):
        return self.DeviceID


if __name__ == "__main__":
    DDS = OpfuncRF_DDS(DeviceID=0)
    DDS.setwaveform(Freq=100, Amp=0.5, Phase=0.5, Delay=100)
    DDS.gen_assembler(0)
    DDS.setwaveform(Freq=200, Amp=0.5, Phase=0.5, Delay=200)
    DDS.gen_assembler(1)
    DDS.setwaveform(Freq=300, Amp=0.5, Phase=0.5, Delay=300)
    DDS.gen_assembler(2)
    DDS.setwaveform(Freq=400, Amp=0.5, Phase=0.5, Delay=400)
    DDS.gen_assembler(3)
    # DDS.adjust_array_length()
    # DDS.output2file()
    arrays = DDS.read_arrays()
    array = arrays[0]
    array1 = arrays[1]
    arrays[0].append(array1)
    print(arrays)