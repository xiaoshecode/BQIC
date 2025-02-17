from OpfuncDevice import OpfuncRF


class OpfuncRF_DDS(OpfuncRF):  # 这里针对Bell设备DDS完成子类
    def __init__(self, DeviceID):
        super().__init__(DeviceID)
        self.Freq_clk = 250 * 10**6  # 板载时钟频率250MHz
        self.Freq = 0  # 24bit
        self.Amp = 0  # 16bit
        self.Phase = 0  # 24bit
        self.Delay = 0  # 32bit
        self.array_128bit = []  # 128 bit array
        self.array_32bit = []  # 32 bit array

    # 保留父类的方法，待后续扩展
    # def open(self):
    #     super().open()

    # def close(self):
    #     super().close()

    def reset(self):
        super().reset()

    def read(self):
        super().read()

    def write(self):
        return super().write()

    def setwaveform(self, Freq, Amp, Phase, Delay):  # 添加十进制数据f、a、p、t
        if not all(
            0 <= x < 2**32 for x in [self.Freq, self.Amp, self.Phase, self.Delay]
        ):
            raise ValueError("All parameters should be 32-bit integers(0 <= x < 2**32)")
        else:
            self.Freq = Freq
            self.Amp = Amp
            self.Phase = Phase
            self.Delay = Delay

    def gen_assembler(self):  # 转换a/f/p信息为二进制命令

        Freq_bin = int(self.Freq * 2**32 / 250)  # part1 f0 = K/2^32 * Fclk
        Phase_bin = int(self.Phase * 2**24)  # part2 p0 = K/2^24,p=[0,1]
        Amp_bin = int(self.Amp * 2**16)  # part3 Amp = K/2^16

        full_128bin = (0<<96) | (int(Freq_bin) << 64) | (int(Phase_bin)<< 32) | int(Amp_bin) 

        self.array_128bit.append(full_128bin)
        self.array_32bit.append(self.Delay)

    def read_arrays(self):
        return self.array_128bit, self.array_32bit
    
    def adjust_array_length(self):
        while (len(self.array_128bit) % 4) !=3:
            self.array_128bit.append(0)
            self.array_32bit.append(0)

        self.array_128bit.append(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        self.array_32bit.append(0xFFFFFFFF)

    def getDeviceID(self):
        print("RF DDS Device ID: ", super().getDeviceID())
