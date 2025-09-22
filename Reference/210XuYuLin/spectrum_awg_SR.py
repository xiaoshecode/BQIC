from pyspcm import *
from spcm_tools import *
import sys
import math 
# from enum import IntEnum
import numpy as np

import msvcrt
from time import sleep
import ctypes

import matplotlib.pyplot as plt



MAX_AMP_CH0 = 125 # mV, max output amplitude

AMP_SATURATION_GLOBAL = np.pi/2/1.78

# Utilities from the sample code from Spectrum

#
#**************************************************************************
# vWriteSegmentData: transfers the data for a segment to the card's memory
#**************************************************************************
#

# def vWriteSegmentData (hCard, lNumActiveChannels, dwSegmentIndex, dwSegmentLenSample, pvSegData):
#     lBytesPerSample = 2
#     dwSegLenByte = uint32 (dwSegmentLenSample * lBytesPerSample * lNumActiveChannels.value)
#
#     # setup
#     dwError = spcm_dwSetParam_i32 (hCard, SPC_SEQMODE_WRITESEGMENT, dwSegmentIndex)
#     if dwError == ERR_OK:
#         dwError = spcm_dwSetParam_i32 (hCard, SPC_SEQMODE_SEGMENTSIZE,  dwSegmentLenSample)
#
#     # write data to board (main) sample memory
#     if dwError == ERR_OK:
#         dwError = spcm_dwDefTransfer_i64 (hCard, SPCM_BUF_DATA, SPCM_DIR_PCTOCARD, 0, pvSegData, 0, dwSegLenByte)
#     if dwError == ERR_OK:
#         dwError = spcm_dwSetParam_i32 (hCard, SPC_M2CMD, M2CMD_DATA_STARTDMA | M2CMD_DATA_WAITDMA)


#
#**************************************************************************
# vWriteStepEntry
#**************************************************************************
#

# def vWriteStepEntry (hCard, dwStepIndex, dwStepNextIndex, dwSegmentIndex, dwLoops, dwFlags):
#     qwSequenceEntry = uint64 (0)
#
#     # setup register value
#     qwSequenceEntry = (dwFlags & ~SPCSEQ_LOOPMASK) | (dwLoops & SPCSEQ_LOOPMASK)
#     qwSequenceEntry <<= 32
#     qwSequenceEntry |= ((dwStepNextIndex << 16)& SPCSEQ_NEXTSTEPMASK) | (int(dwSegmentIndex) & SPCSEQ_SEGMENTMASK)
#
#     dwError = spcm_dwSetParam_i64 (hCard, SPC_SEQMODE_STEPMEM0 + dwStepIndex, int64(qwSequenceEntry))



def wrap_to_list(arg):
    # if the argument is not a list, wrap it into a list
    if type(arg) is not list:
        return [arg]
    else:
        return arg

def SinCombine(freq, amp, phase, duration, sample_rate):   
    #duration-us, amp-percentage of max range, freq-MHz, phase-2*pi, sample_rate-MHz
    
    freqlist = wrap_to_list(freq)
    amplist = wrap_to_list(amp)
    phaselist = wrap_to_list(phase)

    N = len(freqlist)

    t = np.arange(0, duration, 1/sample_rate)
    w = np.zeros(len(t))

    assert len(amplist)==N
    assert len(phaselist)==N


    for i in range(N):
        w = w + amplist[i] * np.sin(2.0 * np.pi * (freqlist[i] * t + phaselist[i]))

    return list(w)


def HS1_sweep(freq_start, freq_end, amp, beta, duration, sample_rate):
    # HS1 pulse
    # duration-us, amp-percentage of max range, freq-MHz, phase-2*pi, sample_rate-MHz

    t = np.arange(0, duration, 1 / sample_rate)
    dt = 1 / sample_rate
    w = np.zeros(len(t))
    f = (freq_end-freq_start)/2*np.tanh(beta*(2 * t/duration - 1))
    f_car = (freq_end + freq_start)/2


    w = w + amp /np.cosh(beta * (2 * t/duration - 1)) * np.sin(2.0 * np.pi * (np.cumsum(f) * dt + f_car * t))

    return list(w)

def intensity_to_amp(I, amp_saturation):
    # Convert the desired intensity I to awg amplitude, based on the saturation amplitude amp_saturation from calibration
    return np.arcsin(I**0.25)/(np.pi/2 / amp_saturation)

def pulse_shape(t, t_shape, t_pulse, I_top, amp_saturation):
    return np.piecewise(t, [t < t_shape, ((t >= t_shape) & (t <= t_pulse - t_shape)), t > t_pulse - t_shape],
                        [lambda t: intensity_to_amp(np.sin(np.pi / 2 * t / t_shape) ** 2 * I_top, amp_saturation),
                         intensity_to_amp(I_top, amp_saturation),
                        lambda t: intensity_to_amp(np.sin(np.pi / 2 * (t_pulse - t) / t_shape) ** 2 * I_top, amp_saturation)])

    # return np.piecewise(t, [t < t_shape, ((t >= t_shape) & (t <= t_pulse - t_shape)), t > t_pulse - t_shape],
    #                     [lambda t: t / t_shape, 1,
    #                      lambda t: (t_pulse - t) / t_shape])


def ShapedSinCombine(freq, I_top, phase, duration, t_shape, sample_rate, amp_saturation):
    # duration-us, amp-percentage of max range, freq-MHz, phase-2*pi, sample_rate-MHz


    t = np.arange(0, duration, 1 / sample_rate)

    w = np.sin(2.0 * np.pi * (freq * t + phase)) * pulse_shape(t, t_shape, duration, I_top, amp_saturation)

    return list(w)


class DeviceSpectrumAWG:
    # This class packages the basic function used in the spectrum awg for one channel single restart mode.
    # It contains 1: set up the single restart mode; 2: set up the trigger mode; 3: set up the analog outputs of the channel
    # 4: set up the clock mode; 5: start, stop and restart the card; 6: write the waveform data into the AWG card
    def __init__(self, address, init_card=True, MAX_VOLT_CH0=125, AMP_SATURATION = np.pi/2/1.78):
        # open the card
        self.card = spcm_hOpen (create_string_buffer (address))
        if self.card == None:
            sys.stdout.write("no card found...\n")
            exit (1)

        # self.n_seg = 8 # the number of memory segments


        self._sample_rate = 1250 # MHz
        self.MAX_VOLT_CH0 = MAX_VOLT_CH0
        self.AMP_SATURATION = AMP_SATURATION
        # the DAC range is from -32768 to 32767.
        self._full_scale = uint32 (32767)
        self._half_scale = uint32 (self._full_scale.value // 2)
        
        if init_card:
            self.init_card()

    def __del__(self):
        # self.stop_card()
        # close the connection to the awg when destructing the class object
        spcm_vClose(self.card)

    def init_card(self):
        # stop any possible outputs before configuring the card 
        self.reset_card()
        # set up the card
        self.setup_mode()
        self.setup_trigger()
        self.setup_channels()
        self.setup_clock()

    def setup_mode(self):
        # setup the mode
        llChEnable = int64 (CHANNEL0)
        llLoops = int64(0)  # replay on each detection of trigger
        llMemSamples = int64(KILO_B(10))
        #llChEnable = int64 (CHANNEL0 | CHANNEL1) # uncomment to enable two channels
        # lMaxSegments = int32 (self.n_seg)
        spcm_dwSetParam_i32 (self.card, SPC_CARDMODE,            SPC_REP_STD_SINGLERESTART) #single restart mode
        spcm_dwSetParam_i64 (self.card, SPC_CHENABLE,            llChEnable)
        spcm_dwSetParam_i64(self.card, SPC_MEMSIZE, llMemSamples)
        dwErr = spcm_dwSetParam_i64(self.card, SPC_LOOPS, llLoops)    #
        # dwErr = spcm_dwSetParam_i32 (self.card, SPC_SEQMODE_MAXSEGMENTS, lMaxSegments)
        if dwErr != ERR_OK:
            spcm_dwSetParam_i32(self.card, SPC_M2CMD, M2CMD_CARD_STOP)
            sys.stdout.write("... Error: {0:d}\n".format(dwErr))
            exit(1)

    def setup_trigger(self, external_trigger=True):
        # setup trigger
        if external_trigger:
            spcm_dwSetParam_i32(self.card, SPC_TRIG_ORMASK, SPC_TMASK_EXT0)  # Use external trig0
            spcm_dwSetParam_i32(self.card, SPC_TRIG_EXT0_LEVEL0, 1500)  # Trigger level at 1.5 V
            spcm_dwSetParam_i32(self.card, SPC_TRIG_EXT0_MODE, SPC_TM_POS)  # Trigger on rising edge
            spcm_dwSetParam_i32(self.card, SPC_TRIG_TERM, 0) # 1 = 50 ohm termination, 0 = 1 kOhm termination
        else:
            spcm_dwSetParam_i32(self.card, SPC_TRIG_ORMASK,      SPC_TMASK_SOFTWARE) # software trigger

        # spcm_dwSetParam_i32(self.card, SPC_TRIG_DELAY, 0)
        # spcm_dwSetParam_i32 (self.card, SPC_TRIG_ANDMASK,     0)
        # spcm_dwSetParam_i32 (self.card, SPC_TRIG_CH_ORMASK0,  0)
        # spcm_dwSetParam_i32 (self.card, SPC_TRIG_CH_ORMASK1,  0)
        # spcm_dwSetParam_i32 (self.card, SPC_TRIG_CH_ANDMASK0, 0)
        # spcm_dwSetParam_i32 (self.card, SPC_TRIG_CH_ANDMASK1, 0)
        spcm_dwSetParam_i32(self.card, SPC_TRIGGEROUT,       0)
        # spcm_dwSetParam_i32(self.card, SPC_M2CMD, M2CMD_CARD_ENABLETRIGGER)

    def setup_channels(self):
        # setup the channels
        lNumChannels = int32 (0)
        spcm_dwGetParam_i32 (self.card, SPC_CHCOUNT, byref (lNumChannels))
        for lChannel in range (0, lNumChannels.value, 1):
            spcm_dwSetParam_i32 (self.card, SPC_ENABLEOUT0    + lChannel * (SPC_ENABLEOUT1    - SPC_ENABLEOUT0),    1)
            spcm_dwSetParam_i32 (self.card, SPC_AMP0          + lChannel * (SPC_AMP1          - SPC_AMP0),          self.MAX_VOLT_CH0)
            # spcm_dwSetParam_i32 (self.card, SPC_CH0_STOPLEVEL + lChannel * (SPC_CH1_STOPLEVEL - SPC_CH0_STOPLEVEL), SPCM_STOPLVL_HOLDLAST)
            spcm_dwSetParam_i32(self.card, SPC_CH0_STOPLEVEL + lChannel * (SPC_CH1_STOPLEVEL - SPC_CH0_STOPLEVEL),
                                SPCM_STOPLVL_ZERO)

    def setup_clock(self):
        # use extenal reference clock at 10 MHz
        # spcm_dwSetParam_i32(self.card, SPC_CLOCKMODE, SPC_CM_EXTREFCLOCK); # Set to reference clock mode
        # spcm_dwSetParam_i32(self.card, SPC_REFERENCECLOCK, 10000000); # Reference clock that is fed in is 10 MHz
        # use internal clock, set samplerate, no clock output
        spcm_dwSetParam_i32 (self.card, SPC_CLOCKMODE, SPC_CM_INTPLL)

        spcm_dwSetParam_i64 (self.card, SPC_SAMPLERATE, MEGA(self._sample_rate))
        dwErr = spcm_dwSetParam_i32 (self.card, SPC_CLOCKOUT,   0)
        if dwErr != ERR_OK:
            spcm_dwSetParam_i32(self.card, SPC_M2CMD, M2CMD_CARD_STOP)
            sys.stdout.write("... Error: {0:d}\n".format(dwErr))
            exit(1)

    def start_card(self):
        # disable the timeout
        spcm_dwSetParam_i32(self.card, SPC_TIMEOUT, 0)
        # start the card and enable the trigger engine
        # sys.stdout.write("\nStarting the card\n")
        dwErr = spcm_dwSetParam_i32(self.card, SPC_M2CMD, M2CMD_CARD_START | M2CMD_CARD_ENABLETRIGGER)
        if dwErr != ERR_OK:
            spcm_dwSetParam_i32(self.card, SPC_M2CMD, M2CMD_CARD_STOP)
            sys.stdout.write("... Error: {0:d}\n".format(dwErr))
            exit(1)

        # Send one force trigger command to "start" the sequence
        # (otherwise a TTL pulse would be consumed to actually start the card)
        # spcm_dwSetParam_i32(self.card, SPC_M2CMD, M2CMD_CARD_FORCETRIGGER) # Force trigger is used.

    def stop_card(self):
        dwErr = spcm_dwSetParam_i32(self.card, SPC_M2CMD, M2CMD_CARD_STOP)
        if dwErr != ERR_OK:
            sys.stdout.write("... Error: {0:d}\n".format(dwErr))
            exit(1)

    def reset_card(self):
        spcm_dwSetParam_i32(self.card, SPC_M2CMD, M2CMD_CARD_RESET)

    # Doesn't work
    # def read_error_msg(self):
    #     buffer_error_msg = int32(200)
    #     spcm_dwGetErrorInfo_i32(self.card, None, None, byref(buffer_error_msg))
    #     print(buffer_error_msg)


    # def write_segment_single_channel(self, waveform, segment_index):
    #     # Adapted from vDoDataCalculation in the code example from Spectrum
    #
    #     waveform = list(waveform)
    #     # The minimal segment size is 384 for 1-channel
    #     if len(waveform) < 384:
    #         waveform = waveform + [0] * (384 - len(waveform))
    #
    #     # Make sure the length of the waveform is integer times of 32 by padding zeros at its end
    #     n_zero = (32 - len(waveform) % 32) % 32
    #     waveform = waveform + [0] * n_zero
    #
    #     dwSegmentLenSample = int(len(waveform))
    #     # dwSegmentLenSample = int(np.maximum(len(waveform), 192))
    #     dwSegLenByte  = uint32 (0)
    #
    #     # For our M4i.6631 model, this factor should be 6.
    #     dwFactor = 6
    #
    #     # buffer for data transfer
    #     dwSegLenByte = 2 * dwFactor * dwSegmentLenSample * 1
    #     pvBuffer = pvAllocMemPageAligned (dwSegLenByte)
    #     pnData = cast (addressof (pvBuffer), ptr16)
    #
    #     # Make sure the waveform does not overflow the awg DAC
    #     assert np.max(np.abs(waveform)) <= 1.0
    #
    #     # There should be a way to speed up this.
    #     # for i in range (0, dwSegmentLenSample, 1):
    #     #     # pnData[i] = int16 (dwFShalf.value + int(dwFShalf.value * waveform[i] + 0.5))
    #     #     pnData[i] = int16(int(self._full_scale.value * waveform[i]))
    #
    #     waveform = np.array(waveform) * self._full_scale.value  # Convert the amplitudes of waveform to DAC values
    #     waveform = waveform.astype(np.int16)
    #     waveform = np.ascontiguousarray(waveform, dtype=np.int16)
    #     waveform_ptr = waveform.ctypes.data_as(ctypes.POINTER(ctypes.c_int16))
    #
    #     memmove(pnData, waveform_ptr, len(waveform) * 2)
    #
    #     vWriteSegmentData (self.card, uint32(1), segment_index, dwSegmentLenSample, pvBuffer) # would need to change the 2nd param if 2 channels are used


    def writedata_single_ch(self, waveform):
        waveform = list(waveform)

        # The minimum memory size should be 32
        if len(waveform) < 32:
            waveform = waveform + [0] * (32 - len(waveform))

        # Make sure the length of the waveform is integer times of 32 by padding zeros at its end
        n_zero = (32 - len(waveform) % 32) % 32
        waveform = waveform + [0] * n_zero
        llMemSamples = int64(len(waveform))


        lBytesPerSample = 2
        ch_num = 1


        spcm_dwSetParam_i64(self.card, SPC_MEMSIZE, llMemSamples)

        # set up buffer for the data transfer
        qwBufferSize = uint64(llMemSamples.value * lBytesPerSample * ch_num)
        pvBuffer = c_void_p()
        pvBuffer = pvAllocMemPageAligned(qwBufferSize.value)

        pnData = cast(addressof(pvBuffer), ptr16)

        # Make sure the waveform does not overflow the awg DAC
        # print(np.max(np.abs(waveform)))
        assert np.max(np.abs(waveform)) <= 1.0

        waveform = np.array(waveform) * self._full_scale.value  # Convert the amplitudes of waveform to DAC values
        waveform = waveform.astype(np.int16)
        waveform = np.ascontiguousarray(waveform, dtype=np.int16)
        waveform_ptr = waveform.ctypes.data_as(ctypes.POINTER(ctypes.c_int16))

        memmove(pnData, waveform_ptr, len(waveform) * 2)

        dwError = spcm_dwDefTransfer_i64(self.card, SPCM_BUF_DATA, SPCM_DIR_PCTOCARD, int32(0), pvBuffer, uint64(0), qwBufferSize)
        if dwError == ERR_OK:
            spcm_dwSetParam_i32(self.card, SPC_M2CMD, M2CMD_DATA_STARTDMA | M2CMD_DATA_WAITDMA)


class SingleRestartSpectrumAWG:
    # This class contains the basic waveform generation function,
    # and calls the lower-level functions to configure the sequence on the AWG.        
    def __init__(self, device=None):
        if device is None:
            # in case there are multiple objects of this class or its sub-classes,
            # problems may rise if each object creates its own instance of DeviceSpectrumAWG?
            self.awg = DeviceSpectrumAWG(b'TCPIP::192.168.1.8::inst0::INSTR')
        else:
            # passing the instance of DeviceSpectrumAWG to this class might be safer
            self.awg = device
        self._sample_rate = self.awg._sample_rate 


        # generate an idle pulse for later uses
        # self.waveform_idle = SinCombine(0, 0, 0, self._t_idle, self._sample_rate)
        self.waveform = []

        # Keep track of the overall probe time for phase calculation in the phase-coherent manner
        self._overall_probe_t = 0
        self.a_probe = None
        self.f_probe = None
        self.t_probe = None


    # Add pulses (specified by their freqs, amps, phases, and durations) to the waveforms

    def add_pulse_to_waveform(self, freq, amp, phase, t):
        phase += freq * (self._overall_probe_t) # Calculate the phase in the phase-coherent manner
        self.waveform = self.waveform + SinCombine(freq, amp, phase, t, self._sample_rate)
        if t > 0:
            self._overall_probe_t += np.arange(0, t, 1/self._sample_rate)[-1]+ 1/self._sample_rate


    def add_HS1_to_waveform(self, freq_start, freq_end, amp, beta, t):
        self.waveform = self.waveform + HS1_sweep(freq_start, freq_end, amp, beta, t, self._sample_rate)
        if t > 0:
            self._overall_probe_t += np.arange(0, t, 1 / self._sample_rate)[-1] + 1 / self._sample_rate

    def add_sin_squared_pulse_to_waveform(self, freq, I_top, phase, duration, t_shape):
        phase += freq * (self._overall_probe_t)  # Calculate the phase in the phase-coherent manner
        self.waveform = self.waveform + ShapedSinCombine(freq, I_top, phase, duration,
                                                                     t_shape, self._sample_rate,
                                                            self.awg.AMP_SATURATION)

        if duration > 0:
            self._overall_probe_t += np.arange(0, duration, 1 / self._sample_rate)[-1] + 1 / self._sample_rate


    # Clear the probe waveform and reset the time counter for the phase calculation
    def reset_waveform(self):
        self.waveform = []
        self._overall_probe_t = 0

    # Load the waveforms to the awg memory

    def update_waveform(self):
        self.awg.stop_card()
        if len(self.waveform) == 0:
            # when the waveform is empty during initialization, write zero to the awg memory
            self.awg.writedata_single_ch([0])
        else:
            self.awg.writedata_single_ch(self.waveform)

        self.awg.start_card()
        # plt.plot(np.arange(len(self.waveform)) / self._sample_rate, self.waveform)
        # plt.show()


    def update_freq(self, freq, freq2=0):
        # freq2 is not used in this case, since only one channel of the AWG is used
        assert self.t_probe is not None and self.a_probe is not None
        self.f_probe = freq
        # Overwrite the probe waveform using the new parameters
        self.waveform = SinCombine(self.f_probe, self.a_probe, 0, self.t_probe, self._sample_rate)
        # Load the new waveform to the AWG
        self.update_waveform()


    def update_time(self, t):
        assert self.f_probe is not None and self.a_probe is not None
        self.t_probe = t

        self.waveform = SinCombine(self.f_probe, self.a_probe, 0, self.t_probe, self._sample_rate)
        self.update_waveform()

    def update_probe(self):
        assert self.f_probe is not None and self.a_probe is not None and self.t_probe is not None

        self.waveform = SinCombine(self.f_probe, self.a_probe, 0, self.t_probe, self._sample_rate)
        self.update_waveform()



class ContinuousOutput(SingleRestartSpectrumAWG):

    def __init__(self, device=None):
        super().__init__(device)

        # Change to software trigger
        self.awg.setup_trigger(external_trigger=False)


    def set_output(self, freq, amp, t):
        self.waveform = SinCombine(freq, amp, 0, t, self._sample_rate)
        # Write the new waveform to awg memory
        self.awg.stop_card()
        self.awg.writedata_single_ch(self.waveform)
        self.awg.start_card()




if __name__ == "__main__":
    import time
    # awg = DeviceSpectrumAWG(b'TCPIP::192.168.1.8::inst0::INSTR')
    # awg = DeviceSpectrumAWG(b'TCPIP::192.168.1.81::inst0::INSTR')
    awg = DeviceSpectrumAWG(b'TCPIP::192.168.1.28::inst0::INSTR', MAX_VOLT_CH0=176, AMP_SATURATION=np.pi/2/1.57)
    # awg = DeviceSpectrumAWG(b'TCPIP::192.168.1.39::inst0::INSTR', MAX_VOLT_CH0=176, AMP_SATURATION=np.pi/2/1.57)
    #
    continuousOut = ContinuousOutput(awg)
    continuousOut.set_output(220, 0, 2000)
    time.sleep(0.1)
    # continuousOut.set_output(221, 0.0, 2000)

    # continuousOut.set_output((125*2+145)/2+0.9, 1 * 0.45, 2000)

    # SingleRestart = SingleRestartSpectrumAWG(awg)
    # SingleRestart.add_pulse_to_waveform(221.4, 1, 0, 2000)
    # SingleRestart.update_waveform()