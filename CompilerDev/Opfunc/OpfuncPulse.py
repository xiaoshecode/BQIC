from Opfunc.OpfuncDevice import OpfuncDevice

# from OpfuncDevice import OpfuncDevice  # 基类,调试用

class OpfuncPulse(OpfuncDevice):
    def __init__(self, DeviceID):
        super().__init__(DeviceID)
        self.DeviceID = DeviceID
        self.Channel = 32
        self.array_128bit = {0:[],1:[],2:[],3:[],4:[],5:[],6:[],7:[],
                             8:[],9:[],10:[],11:[],12:[],13:[],14:[],15:[],
                             16:[],17:[],18:[],19:[],20:[],21:[],22:[],23:[],
                             24:[],25:[],26:[],27:[],28:[],29:[],30:[],31:[]
                            }#32路ttl输入输出
        self.mode = "nan"  # "output"表示输出模式，"input"表示输入模式

        # parameters for both input and output mode
        self.threshold = 0  # 持续时间,0表示一直保持状态， -1表示关闭（负数表示关闭） [127:96]
        # input parameters counter 
        self.InputCounter = 0  # 0表示不计数，1表示计数 [95]
        self.InputAddress = 0  # 存入的用户寄存器地址[2:0]，用来跳转的寄存器地址，默认值为0 [94:88]

        # output parameters
        self.OutputVoltage = 0  # 输出电压，0表示低电平，1表示高电平 [95]
        self.OutputDelay = 0  # 输出延时[6:0] [94:88]

    def open(self):
        return super().open()

    def close(self):
        return super().close()

    def reset(self):
        super().reset()
        self.array_128bit = {
            0:[],1:[],2:[],3:[],4:[],5:[],6:[],7:[],
            8:[],9:[],10:[],11:[],12:[],13:[],14:[],15:[],
            16:[],17:[],18:[],19:[],20:[],21:[],22:[],23:[],
            24:[],25:[],26:[],27:[],28:[],29:[],30:[],31:[]
        }
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
        Output模式
        param1: 32-bit，表示持续时间
        param2: 1-bit，output:0-低电平，1-高电平 input:0-不计数，1-计数
        param3: 7-bit integer，output:输出延时,input:存入用户寄存器地址
        Input模式
        param1: 32-bit，表示持续时间
        param2: 1-bit，0-不计数，1-计数
        param3: 3-bit integer，存入用户寄存器地址
        """
        if mode not in ["output", "input"]:
            raise ValueError("mode should be 'output' or 'input'")
        if not 0 <= param1 < 2**32:
            raise ValueError("param1 should be 32-bit integer(0 <= x < 2**32)")
        # if not 0 <= param3 < 2**7 and mode == "output":
        #     raise ValueError("param3 should be 7-bit integer(0 <= x < 2^7)")
        # if not 0 <= param2 < 2**1 and mode == "input":
        #     raise ValueError("param2 should be 1-bit integer(0 <= x < 2^1)")
        else:
            self.mode = mode
            if mode == "output":
                self.threshold = param1
                self.OutputVoltage = param2
                self.OutputDelay = param3
            elif mode == "input":
                self.threshold = param1
                self.InputCounter = param2
                self.InputAddress = param3

    def gen_assembler(self,Channel):
        if self.mode == "output":
            full_128 = (int(self.threshold)<<96) | (int(self.OutputVoltage)<< 95) | (int(self.OutputDelay)<< 88)
        elif self.mode == "input":
            full_128 = (int(self.threshold)<<96) | (int(self.InputCounter)<< 95) | (int(self.InputAddress)<<88)

        full_128hex = full_128.to_bytes(16, byteorder="big")

        self.array_128bit[Channel].append(full_128hex)

    def read_arrays(self):
        return self.array_128bit

    def getDeviceID(self):
        return self.DeviceID

    # def output2file(self, filename="OpfuncPulse.txt"):
    #     with open(filename, "a") as f:
    #         for item in self.array_128bit:
    #             hex_string = ''.join(format(x, '02x') for x in item)
    #             f.write(hex_string + '\n')


if __name__ == "__main__":
    # 测试代码
    pulse = OpfuncPulse(DeviceID=1)
    pulse.setwaveform(mode="output", param1=100, param2=1, param3=50) # Output模式
    pulse.gen_assembler(0)
    pulse.setwaveform(mode="input", param1=200, param2=1, param3=0)  # Input模式
    pulse.gen_assembler(1)
    arrays = pulse.read_arrays()
    array = arrays[0]
    array1 = arrays[1]
    # arrays[0].append(array1)
    print(arrays)