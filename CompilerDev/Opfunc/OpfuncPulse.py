from Opfunc.OpfuncDevice import OpfuncDevice

class OpfuncPulse(OpfuncDevice):
    def __init__(self, DeviceID):
        super().__init__(DeviceID)
        self.DeviceID = DeviceID
        self.array_128bit = []
        # mode = "nan" # "nan"表示未定义，"output"表示输出模式，"input"表示输入模式
        self.mode = "nan"  # "output"表示输出模式，"input"表示输入模式
        self.threshold = 0  # 持续时间,0表示一直保持状态
        # input parameters
        self.countmode = 0  # 0表示不计数，1表示计数
        self.address = 0  # 存入的用户寄存器地址[2:0]
        # output parameters
        self.Vout = 0  # 输出电压，0表示低电平，1表示高电平
        self.delay = 0  # 输出延时[6:0]

    def open(self):
        return super().open()

    def close(self):
        return super().close()

    def reset(self):
        super().reset()
        self.array_128bit = []
        self.mode = "nan"
        self.threshold = 0
        self.countmode = 0
        self.address = 0
        self.Vout = 0
        self.delay = 0


    def write(self):
        return super().write()

    def read(self):
        return super().read()

    def setwaveform(
        self, mode: str = "nan", param1: int = 0, param2: int = 0, param3: int = 0
    ):
        """
        mode: "output"表示输出模式，"input"表示输入模式
        param1: 32-bit integer, 0 <= x < 2^32
        param2: 1-bit integer
        param3: 3-bit integer, 0 <= x < 2^3 (input mode only)
        param3: 8-bit integer, 0 <= x < 2^8 (output mode only)
        """
        if mode not in ["output", "input"]:
            raise ValueError("mode should be 'output' or 'input'")
        if not 0 <= param1 < 2**32:
            raise ValueError("param1 should be 32-bit integer(0 <= x < 2**32)")
        if not 0 <= param3 < 2**8 and mode == "output":
            raise ValueError("param3 should be 8-bit integer(0 <= x < 2^8)")
        if not 0 <= param2 < 2**3 and mode == "input":
            raise ValueError("param2 should be 8-bit integer(0 <= x < 2^3)")
        else:
            self.mode = mode
            if mode == "output":
                self.threshold = param1
                self.Vout = param2
                self.delay = param3
            else:
                self.threshold = param1
                self.countmode = param2
                self.address = param3

    def gen_assembler(self):
        if self.mode == "output":
            full_128 = (int(self.threshold)<<96) | (int(self.Vout)<< 95) | (int(self.delay)<< 88)
        elif self.mode == "input":
            full_128 = (int(self.threshold)<<96) | (int(self.countmode)<< 95) | (int(self.address)<<88)
        
        full_128hex = full_128.to_bytes(16, byteorder="big")

        self.array_128bit.append(full_128hex)

    def adjust_array_length(self):
        self.array_128bit.append(b'\xFF'*16)

    def read_arrays(self):
        return self.array_128bit

    def getDeviceID(self):
        return self.DeviceID

    def output2file(self, filename="OpfuncPulse.txt"):
        with open(filename, "a") as f:
            for item in self.array_128bit:
                hex_string = ''.join(format(x, '02x') for x in item)
                f.write(hex_string + '\n')


if __name__ == "__main__":
    # 测试代码
    pulse = OpfuncPulse(DeviceID=1)
    pulse.setwaveform(mode="output", param1=100, param2=1, param3=10)
    pulse.gen_assembler()
    pulse.adjust_array_length()
    pulse.output2file()
    print(pulse.read_arrays())