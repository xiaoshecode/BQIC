from OpfuncDevice import OpfuncRF


class OpfuncAWG(OpfuncRF):  # 这里针对Bell设备的AWG完成Amp、phase、freq参数控制子类
    def __init__(self, DeviceID, Config_method):
        super().__init__(DeviceID)
        self.array_128bit = []  # 128 bit array
        self.array_32bit = []  # 32 bit array
        self.u0 = 0
        self.u1 = 0
        self.u2 = 0
        self.u3 = 0
        self.Delay = 0
        self.Config_method = Config_method  # 配置方法: 0: Amp, 1: Phase, 2: Freq

    def setwaveform(self, u0, u1, u2, u3, Delay):
        if not all(0 <= x < 2**32 for x in [u0, u1, u2, u3, Delay]):
            raise ValueError("All parameters should be 32-bit integers(0 <= x < 2**32)")
        else:
            self.u0 = u0
            self.u1 = u1
            self.u2 = u2
            self.u3 = u3
            self.Delay = Delay

    def gen_assembler_AMP(self):
        u0_bin = int(self.u0 * 2**16)  # Amp = K/2^16
        u1_bin = int(self.u1 * 2**16)
        u2_bin = int(self.u2 * 2**16)
        u3_bin = int(self.u3 * 2**16)

        v0_bin = u0_bin
        v1_bin = u1_bin + u2_bin / 2 + u3_bin / 6
        v2_bin = u2_bin + u3_bin
        v3_bin = u3_bin

        full_128bin = (
            (int(v3_bin) << 96)
            | (int(v2_bin) << 64)
            | (int(v1_bin) << 32)
            | int(v0_bin)
        )

        self.array_128bit.append(full_128bin)
        self.array_32bit.append(self.Delay)

    def gen_assembler_PHASE(self):
        u0_bin = int(self.u0 * 2**24)  # part2 p0 = K/2^24,p=[0,1]
        u1_bin = int(self.u1 * 2**24) 
        u2_bin = int(self.u2 * 2**24)
        u3_bin = int(self.u3 * 2**24)

        v0_bin = u0_bin
        v1_bin = u1_bin + u2_bin / 2 + u3_bin / 6
        v2_bin = u2_bin + u3_bin
        v3_bin = u3_bin

        full_128bin = (int(v3_bin) << 96) | (int(v2_bin) << 64) | (int(v1_bin) << 32) | int(v0_bin)

        self.array_128bit.append(full_128bin)
        self.array_32bit.append(self.Delay)
    
    def gen_assembler_FREQ(self):
        u0_bin = int(self.u0 * 2**24 / 250) # part1 f0 = K/2^24 * Fclk
        u1_bin = int(self.u1 * 2**24 / 250)
        u2_bin = int(self.u2 * 2**24 / 250)
        u3_bin = int(self.u3 * 2**24 / 250)

        v0_bin = u0_bin
        v1_bin = u1_bin + u2_bin / 2 + u3_bin / 6
        v2_bin = u2_bin + u3_bin
        v3_bin = u3_bin

        full_128bin = (int(v3_bin) << 96) | (int(v2_bin) << 64) | (int(v1_bin) << 32) | int(v0_bin)

        self.array_128bit.append(full_128bin)
        self.array_32bit.append(self.Delay)

    def gen_assembler(self):
        if self.Config_method == 0:
            self.gen_assembler_AMP()
        elif self.Config_method == 1:
            self.gen_assembler_PHASE()
        elif self.Config_method == 2:
            self.gen_assembler_FREQ()
        else:
            raise ValueError("Invalid Config_method")

    def read_arrays(self):
        return self.array_128bit, self.array_32bit

    def adjust_array_length(self):
        while (len(self.array_128bit) % 4) != 3:
            self.array_128bit.append(0)
            self.array_32bit.append(0)

        self.array_128bit.append(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        self.array_32bit.append(0xFFFFFFFF)
