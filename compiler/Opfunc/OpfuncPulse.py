from OpfuncDevice import OpfuncDevice


class OpfuncPulse(OpfuncDevice):
    def __init__(self, DeviceID):
        super().__init__(DeviceID)
        self.DeviceID = DeviceID
        self.array_32bit = []
        self.array_16bit = []
        self.param1 = 0  # 表示开关
        self.param2 = 0  # 表示延迟
        self.param3 = 0  # 表示持续时间
        self.number = 0  # 16bit
    def open(self):
        return super().open()

    def close(self):
        return super().close()

    def reset(self):
        return super().reset()

    def write(self):
        return super().write()

    def read(self):
        return super().read()

    def setwaveform(self, param1, param2, param3):
        if param1 == 1:
            number = 128 + param2
        else:
            number = param2

        # 检查生成数字是否在16位范围内
        if not 0 <= number < 2**16:
            raise ValueError("All parameters should be 16-bit integers(0 <= x < 2**16)")
        else:
            self.param1 = param1
            self.param2 = param2  
            self.param3 = param3
            self.number = number

    def gen_assembler(self):
        self.array_16bit.append(self.number)
        self.array_32bit.append(self.param3)
    
    def adjust_array_length(self):
        while len(self.array_16bit) % 8 != 7:
            self.array_16bit.append(0)
            self.array_32bit.append(0)

        self.array_16bit.append(0xFFFF)
        self.array_32bit.append(0xFFFFFFFF)

    def read_arrays(self):
        return self.array_16bit, self.array_32bit

    def getDeviceID(self):
        print("Pulse Device ID:", super().getDeviceID())
