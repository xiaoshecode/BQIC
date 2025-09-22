import serial
#import serial.tools.list_ports
import time
import struct
from abc import abstractmethod

from sqlalchemy import true

class DDS_Quad:
    def __init__(self):
        #print('Quad-channel DDS')
        self.com_port = None # void com port
        self._ser = None      # void serial
        self._dds = [0,1,2,3]
        # default values for each dds
        self._enabled = [0]*4
        self._profile = [0]*4
        self._amplitude = [[0.0 for _ in range(8)] for _ in range(4)]
        self._phase = [[0.0 for _ in range(8)] for _ in range(4)]
        self._frequency = [[10.0 for _ in range(8)] for _ in range(4)]   # MHz

    @abstractmethod
    def open(self, com_port):
        # create serial connection
        print('Serial: Create a serial connection in serial port',com_port)

    @abstractmethod
    def close(self):
        print('Serial: Close serial connection')

    @abstractmethod
    def _connectionCheck(self):
        print('DDS_Quad: _connectionCheck')

    @abstractmethod
    def _initSettings(self):
        print('DDS_Quad: _initSettings')

    @abstractmethod
    def _setChannel(self, dds_port, profile):
        # print('DDS_Quad: _setChannel')
        pass

    def setOnOff(self, dds_port, onoff):
        # turn on or off dds_port
        print('DDS_Quad: DDS',dds_port,'output state changed to',onoff,'.')
        self._enabled[dds_port] = onoff
        self._setChannel(dds_port,self._profile[dds_port])

    def setFrequency(self, dds_port, frequency, profile):
        # set the frequency of dds_port & profile in MHz
        #print('DDS_Quad: set frequency: DDS ',dds_port,' -profile ',profile,' -frequency changed to', frequency, 'MHz.')
        self._frequency[dds_port][profile] = frequency
        self._setChannel(dds_port,profile)

    def setAmplitude(self, dds_port, amplitude, profile):
        # set the amplitude of dds_port & profile
        #print('DDS_Quad: set amplitude: DDS ',dds_port,' -profile ',profile,' -amplitude changed to', amplitude, '.')
        self._amplitude[dds_port][profile] = amplitude
        self._setChannel(dds_port,profile)

    def setPhase(self, dds_port, phase, profile):
         # set the phase of a DDS in degree
        #print('DDS_Quad: set phase: DDS ',dds_port,' -profile ',profile,' -phase changed to', phase, 'degree.')
        self._phase[dds_port][profile] = phase
        self._setChannel(dds_port,profile)

    def setAll(self, dds_port, onoff, frequency, amplitude, phase, profile):
        # set all the parameters of a DDS
        print('DDS_Quad: DDS',dds_port,'reset.')
        self._enabled[dds_port] = onoff
        self._frequency[dds_port][profile] = frequency
        self._amplitude[dds_port][profile] = amplitude
        self._phase[dds_port][profile] = phase
        self._setChannel(dds_port,profile)


class DDS_AD9910_Teensy(DDS_Quad):
    ## Serial connection methods
    def open(self,com_port):
        super(DDS_AD9910_Teensy,self).open(com_port)
        if not self.com_port is None:
            self._ser.close()
        try:
            self._ser = serial.Serial(com_port,timeout=1000)
        except serial.SerialException: # ???
            print('Cannot connect to DDS in serial port',com_port)
            return False
        else:
            self.com_port = com_port
            connection_valid = self._connectionCheck()
            if connection_valid:
                # only do the next things if connected
                print('Connected with DDS.')
                self._initSettings()
                return True
            else:
                print('DDS unavailable.')
                self.com_port = None
                return False

    def close(self):
        super(DDS_AD9910_Teensy,self).close()
        if not self.com_port is None:
            # close serial connection
            for i_dds in self._dds:
                self.setOnOff(i_dds,False)  # close all the channels/ports before close the connection
            print('Close serial connection')
            time.sleep(1)
            self._ser.close()
        self._ser = None
        self.com_port = None

    def _initSettings(self):
        # send initialization commands to each DDS channel/port
        # copy these commands if you what to use
        # 32*dds_port+4,0,0,128,0,0
        # 32*dds_port+4,1,1,64,8,32: 64: single tune mode
        # 32*dds_port+4,2,29,63,65,200
        # 32*dds_port+4,3,0,0,0,127
        
        super(DDS_AD9910_Teensy,self)._initSettings()
        for i_dds in self._dds:
            self._ser.write(struct.pack('6B',32*i_dds+4,0,0,128,0,0))#
            #print(struct.pack('6B',32*i_dds+4,1,1,64,8,32))
            self._ser.write(struct.pack('6B',32*i_dds+4,1,1,64,8,32))
            self._ser.write(struct.pack('6B',32*i_dds+4,2,29,63,65,200))
            self._ser.write(struct.pack('6B',32*i_dds+4,3,0,0,0,255))   ### 255 for max ouput current
            self.__update(i_dds)
        time.sleep(0.2)    
        # set each DDS output to disabled
        for i_dds in self._dds:
            self.setOnOff(i_dds,False)
        print('AD9910 initialized')

    def _setChannel(self, dds_port, profile = 0):
        super(DDS_AD9910_Teensy,self)._setChannel(dds_port,profile)
        # every time the parameter of one DDS channel/port is changed, its state is updated so that the actual output state is updated
        if self.com_port is None:
            raise ValueError('DDS not connected.')
        # encode parameters
        freq_f = max(min(self._frequency[dds_port][profile]/1000 , 1) , 0)
        freq_b = round(freq_f*0xffffffff)
        amp_f = max(min(self._amplitude[dds_port][profile] , 1) , 0) * int(self._enabled[dds_port])
        amp_b = round(amp_f*0x3fff)
        phase_f = max(min(self._phase[dds_port][profile]/360 , 1) , 0)
        phase_b = round(phase_f*0xffff)
        # send commands
        # print('AD9910: _setChannel: ',dds_port,' output-', self._enabled[dds_port],' freq-',freq_f,' amp-',amp_f,' phase-',phase_f)
        # print(32*dds_port+8,profile+14,amp_b,phase_b,freq_b)
        self._ser.write(struct.pack('>2B2HI',32*dds_port+8,profile+14,amp_b,phase_b,freq_b))  # set parameters to register 14 of dds_port
        self.__update(dds_port)
        #time.sleep(0.1)

    def __getChannel(self, dds_port, profile = 0):
        ## if you need to read back any profile register, the three external pin must be used to choose to that profile
        if self.com_port is None:
            raise ValueError('DDS not connected.')
        #print('AD9910: __getChannel: ',struct.pack('2B',32*dds_port+136, profile+14))
        self._ser.write(struct.pack('2B',32*dds_port+136, profile+14))    # get paramters from register 14 of dds_port
        recv_bin = self._ser.read(size = 8)
        para =  struct.unpack('>2HI',recv_bin)  # read 8 bytes
        print('AD9910: __getChannel: ',para)
        if self._enabled[dds_port]:
            self._amplitude[dds_port][profile] = para[0]/0x3fff
        self._phase[dds_port][profile] = para[1]/0xffff*360
        self._frequency[dds_port][profile] = para[2]/0xffffffff*1000
        print('AD9910: __getChannel: ',self._amplitude[dds_port][profile],self._phase[dds_port][profile],self._frequency[dds_port][profile])

    def __update(self,dds_port):
        ## update the output state of one DDS/channel
        self._ser.write(struct.pack('B',32*dds_port+128)) # update  

    def _connectionCheck(self):
        #super(DDS_AD9910_Teensy,self)._connectionCheck()
        print('AD9910: connectionCheck')
        try: 
            self.__getChannel(0,0)
        except Exception as excp:
            print(excp)
            self.close()
            return False
        else:
            return True

    def getOnOff(self, dds_port):
        return self._enabled[dds_port]
       
    def getFrequency(self, dds_port, profile = 0):
        # get the frequency of a DDS in MHz
        self.__getChannel(dds_port,profile)
        print('AD9910: get frequency: DDS ',dds_port,' -profile ',profile,' -frequency is ',self._frequency[dds_port][profile],'.')
        return self._frequency[dds_port][profile]
           
    def getAmplitude(self, dds_port, profile = 0):
        if self._enabled[dds_port]:
            self.__getChannel(dds_port,profile)
            print('AD9910: get amplitude DDS ',dds_port,' -profile ',profile,' -amplitude is ',self._amplitude[dds_port],'.')
        return self._amplitude[dds_port][profile]    

    def getPhase(self, dds_port, profile = 0):
        self.__getChannel(dds_port,profile)
        print('AD9910: get phase: DDS ',dds_port,' -profile ',profile,' -phase is ',self._phase[dds_port],'.')
        return self._phase[dds_port][profile]

    def getAll(self, dds_port, profile = 0):
        if self.com_port is None:
            raise ValueError('DDS unavailable')
        self.__getChannel(dds_port,profile)
        print('AD9910: DDS',dds_port,'get status')
        return self._enabled[dds_port], self._frequency[dds_port][profile], self._amplitude[dds_port][profile], self._phase[dds_port][profile]

class DDS_AD9910_SiliconLab(DDS_Quad):
    ## Serial connection methods
    def open(self,com_port):
        super(DDS_AD9910_SiliconLab,self).open(com_port)
        try:
            self._ser = serial.Serial(com_port,256000,timeout=0.01)
        except serial.SerialException: # ???
            print('Cannot connect to DDS in serial port',com_port)
            return False
        else:
            connection_valid = self._connectionCheck()
            if connection_valid:
                # only do the next things if connected
                print('Connected with DDS.')
                self.com_port = com_port
                # self._ser.flushInput()
                # self._ser.flushOutput()
                self._initSettings()
                return True
            else:
                print('DDS unavailable.')
                return False

    def close(self):
        super(DDS_AD9910_SiliconLab,self).close()
        if not self.com_port is None:
            # close serial connection
            for i_dds in self._dds:
                self.setOnOff(i_dds,False)  # close all the channels/ports before close the connection
            print('Close serial connection')
            time.sleep(1)
            self._ser.close()
        self._ser = None
        self.com_port = None

    def writeKey(self, key):
        # This function should write key into fpga 100% correctly.
        # We assume ser is open. Check this before use.
        self._ser.write(key)
        if self._ser.read(size = 12) != key:
            print('**********!update wrong failure!****************************************************************************************************')           
            while self._ser.read(size = 12) == b'':
                print('**********!re align!****************************************************************************************************')
                self._ser.write(struct.pack('B', 0))
            self.writeKey(key)

    def _initSettings(self):
        # send initialization commands to each DDS channel/port
        # not initialize all profiles
        super(DDS_AD9910_SiliconLab,self)._initSettings()
        for i_dds in self._dds:
            self.writeKey(struct.pack('>2B5H',  0xE0+i_dds, 0xFE, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000))  # E0 FE 0000 0000 0000 0000 0000  Master reset
            self.writeKey(struct.pack('>2B5H',  0xE0+i_dds, 0x02, 0x0000, 0x0000, 0x0001, 0x0140, 0x0020))  # E0 02 0000 0000 0001 0140 0020  set CFR2, enable amp scale from profile and SYNC_CLK
            self.writeKey(struct.pack('>2B5H',  0xE0+i_dds, 0x02, 0x0000, 0x0000, 0x0002, 0x0D3F, 0x41C8))  # E0 02 0000 0000 0002 0D3F 41C8  set CFR3, enable 100x PLL
            self.writeKey(struct.pack('>2B5H',  0xE0+i_dds, 0x02, 0x0000, 0x0000, 0x0003, 0x0000, 0x007F))  # E0 02 0000 0000 0003 0000 007F  set DAC control as default
            self.writeKey(struct.pack('>2B3HI', 0xE0+i_dds, 0x01, 0x000E, 0x0000, 0x0000, 0x028F5C29))      # E0 01 000E 0000 0000 028F 5C29  write profile0, amp=0, phase=0, freq=10
            # self._ser.write(struct.pack('>2B5H',  0xE0+i_dds, 0xFF, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000))  # E0 FF 0000 0000 0000 0000 0000  IOUPDATE
            print('initial ok')
            self.__update(i_dds)
            time.sleep(0.2)    
        
        # clear the read buffer every time you write something to dds
        # num = self._ser.inWaiting()  # should be 12*5*4=240
        # print(num)
        # self._ser.read(size = num)
        
        self.writeKey(struct.pack('>2B3HI', 0xD0, 0x00, 0x0000, 0x0000, 0x0000, 0x00000001))      # D0 00 0000 0000 0000 0000 0000  enable switch profile by external ttl
        # self._ser.read(size = 12)
        print('enable external ttl to change profile.')

        time.sleep(0.2)    
        # set each DDS output to disabled
        for i_dds in self._dds:
            self.setOnOff(i_dds,False)
        print('AD9910 initialized')

    def _setChannel(self, dds_port, profile = 0):
        super(DDS_AD9910_SiliconLab,self)._setChannel(dds_port,profile)
        # every time the parameter of one DDS channel/port is changed, its state is updated so that the actual output state is updated
        if self.com_port is None:
            raise ValueError('DDS not connected.')
        # encode parameters
        freq_f = max(min(self._frequency[dds_port][profile]/1000 , 1) , 0)
        freq_b = round(freq_f*0xffffffff)
        amp_f = max(min(self._amplitude[dds_port][profile] , 1) , 0) * int(self._enabled[dds_port])
        amp_b = round(amp_f*0x3fff)
        phase_f = max(min(self._phase[dds_port][profile]/360 , 1) , 0)
        phase_b = round(phase_f*0xffff)
        # send commands
        # print('AD9910: _setChannel: ',dds_port,' output-', self._enabled[dds_port],' freq-',freq_f*1000,' amp-',amp_f,' phase-',phase_f)
        # check if the commands are correct
        # print(32*dds_port+8,profile+14,amp_b,phase_b,freq_b)
        self.writeKey(struct.pack('>2B3HI', 0xE0+dds_port, 0x01, 0x000E+profile, amp_b, phase_b, freq_b))  # E(dds_port) 01 000(E+profile) (2-bytes amp) (2-bytes phase) (4-bytes freq)
        # print([hex(i)[2:] for i in struct.unpack('>2B3HI',struct.pack('>2B3HI', 0xE0+dds_port, 0x01, 0x000E+profile, amp_b, phase_b, freq_b))])  # check the command given to dds

        # clear the read buffer every time you write something to dds
        # num = self._ser.inWaiting()
        # self._ser.read(size = 12)

        self.__update(dds_port)

    def __isAvailable(self):
        ## quest 0xF1F2F3F4F1F2F3F4F1F2F3F4, expect 0x0A0B0C0D0A0B0C0D0A0B0C0D (96 bits 12 Bytes) for a DDS.
        print('AD9910: __isAvailable: F1F2F3F4F1F2F3F4F1F2F3F4')
        print(self._ser)
        self._ser.write(b'\xF1\xF2\xF3\xF4\xF1\xF2\xF3\xF4\xF1\xF2\xF3\xF4')    # write '0xF1F2F3F4F1F2F3F4F1F2F3F4'
        # num = self._ser.inWaiting()  # should be 12
        # print(num)
        recv_raw = self._ser.read(size = 12)
        if recv_raw == b'\n\x0b\x0c\r\n\x0b\x0c\r\n\x0b\x0c\r':
            return True
        else:
            return False

    def __update(self,dds_port):
        ## update the output state of one DDS/channel
        self.writeKey(struct.pack('>2B5H',  0xE0+dds_port, 0xFF, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000))  # E0 FF 0000 0000 0000 0000 0000  IOUPDATE

        # clear the read buffer every time you write something to dds
        # num = self._ser.inWaiting()
        # self._ser.read(size = 12)
        
    def _connectionCheck(self):
        super(DDS_AD9910_SiliconLab,self)._connectionCheck()
        print('AD9910: connectionCheck')
        try: 
            connectionCheck = self.__isAvailable()
        except Exception as excp:
            self.close()
            return False
        else:
            return connectionCheck


if __name__ == "__main__":
    dds = DDS_AD9910_SiliconLab()
    # dds = DDS_AD9910_Teensy()
    is_open = dds.open('COM9')
    if is_open:
        dds.setFrequency(0,10,0)
    #    dds.getFrequency(0,0)
    #    dds.setFrequency(0,12,1)
    #    dds.getFrequency(0,1)       
    dds.close()            
