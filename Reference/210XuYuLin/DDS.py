
# DDS Class
import atexit
import struct
import time
import argparse

from serial import Serial
from serial.tools import list_ports

from files import loadConfig, saveConfig

comPorts = [item.device for item in list_ports.comports()]
MHz = 10**6
kHz = 10**3

ddsConfigFile = ".\Configuration\dds.json"
ddsConfig = loadConfig(ddsConfigFile)

class DDS(object):
    def __init__(self, port="COM5") -> None:
        super().__init__()

        if not port in comPorts:
            raise KeyError("Port Number is Wrong")
        self.ser = Serial(port)
        if not self.ser.isOpen():
            self.ser.open()

        self.ser.baudrate = 9600
        self.ser.stopbits = 1
        self.ser.timeout = 0.1
        self.ser.bytesize = 8
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()

        # init dds
        ba2 = bytearray.fromhex("040101400820")
        ba3 = bytearray.fromhex("04021d3f41c8")
        ba4 = bytearray.fromhex("04030000007f")

        self.ser.write(bytearray.fromhex("040000800000"))
        time.sleep(0.001)

        # set all dds amplitude to 0
        for i in range(4):
            ba2[0] = (32*i+4) & 0xff
            self.ser.write(ba2)

            ba3[0] = (32*i+4) & 0xff
            self.ser.write(ba3)

            ba4[0] = (32*i+4) & 0xff
            self.ser.write(ba4)

        # only store present using data
        # ampplitude [channel][profile]
        # 不能直接写成 [[100]*8]*4 会存在 浅拷贝 导致复制出现问题
        self.isOn = [[False]*8 for i in range(8)]
        self.amplitude = [[0.0]*8 for i in range(8)]
        self.frequency = [[100.0]*8 for i in range(8)]
        self.phase = [[0.0]*8 for i in range(8)]
        atexit.register(self.exit)

        # set up data
        for i in range(len(ddsConfig)):
            profiles = ddsConfig["channel"+str(i)]
            for j in range(len(profiles)):
                amplitude = profiles[str(j)]["amplitude"]
                phase = profiles[str(j)]["phase"]
                frequency = profiles[str(j)]["frequency"]
                output = profiles[str(j)]["output"]

                self.amplitude[i][j] = amplitude
                self.phase[i][j] = phase
                self.frequency[i][j] = frequency
                self.isOn[i][j] = output

                self.setProfile(
                    channel=i, profile=j, frequency=frequency, amplitude=amplitude, phase=phase, isOn = output)                   
    def setFrequency(self, channel=0, profile = 0, frequency=240.0):
        if frequency < 0 or frequency > 1000:
            raise ValueError("Fre out of range")
        self.frequency[channel][profile] = frequency
        self.setProfile(channel=channel, profile = profile)

    def setAmplitude(self, channel=0, profile = 0, amp=0.0):
        if amp < 0 or amp > 1:
            raise ValueError("amplitude is over range")
        self.amplitude[channel][profile] = amp
        self.setProfile(channel=channel, profile= profile)

    def setPhase(self, channel=0, profile = 0, phase=0):
        self.phase[channel][profile] = phase
        self.setProfile(channel=channel, profile = profile)

    def setProfile(self, channel=0, profile = 0, frequency=None, amplitude=None, phase=None,isOn = True):
        # update config file
        if frequency == None:
            frequency = self.frequency[channel][profile]

        if amplitude == None:
            amplitude = self.amplitude[channel][profile]

        if phase == None:
            phase = self.phase[channel][profile]

        if amplitude < 0 or amplitude > 1:
            raise ValueError("amplitude out of range")

        if frequency < 0 or frequency > 1000:
            raise ValueError("frequency out of range")

        # if off set amplitude = 0 once
        amp = (isOn and amplitude or 0)
        # set profile and destination
        # 2B：2 bytes 2H:2 unsigned short int 4bytes I: unsigned int 4 bytes
        # int is used to convert np.int32/64 to python int
        if channel < 4:
            ba = struct.pack(">2B2HI", 32*channel+8, 14+profile, int(round(amp*0x3fff)),
                            int(round(phase*0xffff)), int(round(frequency/1000*0xffffffff)))

            # write data and update
            self.ser.write(ba)
            signal = int.to_bytes(32*channel+128, 1, byteorder="big")
            self.ser.write(signal)
        else: 
            channel2 = int(channel-4)
            
            # dds2.setProfile(ch=channel2,profile=profile,frequency=frequency,amplitude = amplitude)

        # update configuration
        ddsConfig["channel"+str(channel)][str(profile)] = {
            "amplitude": amplitude,
            "frequency": frequency,
            "phase": phase,
            "output":isOn
        }
        self.amplitude[channel][profile] = amplitude
        self.phase[channel][profile] = phase
        self.frequency[channel][profile] = frequency

    def on(self, channel=0, profile = 0):
        self.isOn[channel][profile] = True
        self.setProfile(channel=channel, profile=profile)

    def off(self, channel=0, profile = 0):
        self.isOn[channel] = False
        self.setProfile(channel=channel, profile = 0)

    def exit(self):
        self.ser.close()
        # dds2.exit()
        # saveConfig(ddsConfig, ddsConfigFile)
        print("Close port and write back configuration")

    def getConfig(self, channel=0, profile = 0):
        return ddsConfig["channel%d"%channel]["%d"%profile]


if __name__ == "__main__":
    dds = DDS(port="COM31")
    """
    for i in range(10):
        dds.setProfile(0,0,200,0.25)
        if i%2:
            dds.setProfile(0,0,280,0.25)
        time.sleep(0.9)
    """
    # dds.setProfile(1,0,150, 0.0,0.0)
    # dds.setAmplitude(0,0,0.4)
    # dds.setFrequency(1,0,150)
    """
    dds.on(3,0)
    dds.on(0,0)

    dds.setProfile(0,0,frequency=250, amplitude=0.4)
    dds.setFrequency(3,0, 240)
    dds.setAmplitude(3,0, 0.5)
    dds.setProfile(3,1,242.0,0.5)
    dds.setProfile(3,2,243,0.5)

    for i in range(5):
        dds.setFrequency(3,0,200+0.5*i)
        time.sleep(2)
    """
    