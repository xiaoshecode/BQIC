class OpfuncRF_DDS(OpfuncRF):  # 这里针对Bell设备DDS完成子类
    def __init__(self, DeviceID):
        super().__init__(DeviceID)
        self.Freq = 0
        self.Amp = 0
        self.Phase = 0
        self.Delay = 0
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

    def setwaveform(self, Freq, Amp, Phase, Delay):#添加十进制数据f、a、p、t
        self.Freq = Freq
        self.Amp = Amp
        self.Phase = Phase
        self.Delay = Delay

    def getDeviceID(self):
        print("RF DDS Device ID: ", super().getDeviceID())