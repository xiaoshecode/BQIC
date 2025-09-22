import time

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
import datetime


MAX_AMP_CH0 = 140 # mV, max output amplitude
# The saturation amplitude of AOM1 and AOM2 from calibration.
AMP_SATURATION_AOM1 = np.pi/2/1.92 # 1.92 comes from the fit parameter of a sin^4 model
AMP_SATURATION_AOM2 = np.pi/2/1.84

# Utilities from the sample code from Spectrum

#
#**************************************************************************
# vWriteSegmentData: transfers the data for a segment to the card's memory
#**************************************************************************
#

def vWriteSegmentData (hCard, lNumActiveChannels, dwSegmentIndex, dwSegmentLenSample, pvSegData):
    lBytesPerSample = 2
    dwSegLenByte = uint32 (dwSegmentLenSample * lBytesPerSample * lNumActiveChannels.value)

    # setup
    dwError = spcm_dwSetParam_i32 (hCard, SPC_SEQMODE_WRITESEGMENT, dwSegmentIndex)
    if dwError == ERR_OK:
        dwError = spcm_dwSetParam_i32 (hCard, SPC_SEQMODE_SEGMENTSIZE,  dwSegmentLenSample)

    # write data to board (main) sample memory
    if dwError == ERR_OK:
        dwError = spcm_dwDefTransfer_i64 (hCard, SPCM_BUF_DATA, SPCM_DIR_PCTOCARD, 0, pvSegData, 0, dwSegLenByte)
    if dwError == ERR_OK:
        dwError = spcm_dwSetParam_i32 (hCard, SPC_M2CMD, M2CMD_DATA_STARTDMA | M2CMD_DATA_WAITDMA)


#
#**************************************************************************
# vWriteStepEntry
#**************************************************************************
#

def vWriteStepEntry (hCard, dwStepIndex, dwStepNextIndex, dwSegmentIndex, dwLoops, dwFlags):
    qwSequenceEntry = uint64 (0)

    # setup register value
    qwSequenceEntry = (dwFlags & ~SPCSEQ_LOOPMASK) | (dwLoops & SPCSEQ_LOOPMASK)
    qwSequenceEntry <<= 32
    qwSequenceEntry |= ((dwStepNextIndex << 16)& SPCSEQ_NEXTSTEPMASK) | (int(dwSegmentIndex) & SPCSEQ_SEGMENTMASK)

    dwError = spcm_dwSetParam_i64 (hCard, SPC_SEQMODE_STEPMEM0 + dwStepIndex, int64(qwSequenceEntry))



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

def pad_zero(list_input, N):
    # Extend the length of list_input to N by padding zeros to its end
    length_input = len(list_input)
    if length_input <= N:
        list_output = list_input + [0] * (N - length_input)
    else:
        list_output = list_input

    return list_output

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



def ShapedSinCombine(freq, I_top, phase, duration, t_shape, sample_rate, amp_saturation):
    # duration-us, amp-percentage of max range, freq-MHz, phase-2*pi, sample_rate-MHz


    t = np.arange(0, duration, 1 / sample_rate)

    w = np.sin(2.0 * np.pi * (freq * t + phase)) * pulse_shape(t, t_shape, duration, I_top, amp_saturation)

    return list(w)



def accumulate_pulse_time(t_pulse, t_overall, sample_rate):
    # Accumulate a pulse time (t_pulse) to a time counter (t_overall) for phase tracking.
    # Account for the discrete time steps on grids defined by the sample rate of AWG.
    if t_pulse > 0:
        t_overall += np.arange(0, t_pulse, 1 / sample_rate)[-1] + 1 / sample_rate
    return t_overall

def SK1_phi(theta):
    return np.arccos(-theta/4/np.pi)


# def SK1_pulse(freq, amp, phase, theta, rabi_rate, sample_rate):
#     phi0 = SK1_phi(theta)/2/2/np.pi  #double pass and unit
#
#     pi_duration = 1/rabi_rate/2
#     theta_duration = pi_duration * theta/np.pi
#
#     t_first = np.arange(0, theta_duration, 1 / sample_rate)
#
#
#     # for i in range(N):
#     #     w = w + amplist[i] * np.sin(2.0 * np.pi * (freqlist[i] * t + phaselist[i]))
#
#
#     pass



class PulsesLibrary_2ch:
    '''
    This class is used to store the waveform generating function which will be used in the class MultiPulses
    and provide an convenient and universal access to different generating functions
    '''
    def __init__(self):
        self.legal_class = ["simple_pulse", "2qgate", "ZZgate", "N-loop_ZZgate", "ShapedPulse", "SK1"]

    def func_call(self, pulse_class):

        if pulse_class == "simple_pulse":
            self.func = self.simple_pulse
        elif pulse_class == "2qgate":
            self.func = self.Modulated_gate_pulse
        elif pulse_class == "ZZgate":
            self.func = self.ZZ_gate_pulse
        elif pulse_class == "N-loop_ZZgate":
            self.func = self.N_loop_ZZgate_pulse
        elif pulse_class == "ShapedPulse":
            self.func = self.Shapedpulse_with_offtime
        elif pulse_class == "SK1":
            self.func = self.SK1_pulse
        else:
            pass

        return self.func


    def add_ShapedPulse_to_waveform(self, wf1, wf2, freq1, amp1, phase1, freq2, amp2, phase2, amp_saturation1, amp_saturation2, t, t_overall, sample_rate=1250):
        phase1 += freq1 * (t_overall)  # Calculate the phase in the phase-coherent manner
        phase2 += freq2 * (t_overall)
        wf1 = wf1 + ShapedSinCombine(freq1, amp1, phase1, t, 0, sample_rate, amp_saturation1)
        wf2 = wf2 + ShapedSinCombine(freq2, amp2, phase2, t, 0, sample_rate, amp_saturation2)
        if t > 0:
            t_overall = accumulate_pulse_time(t, t_overall, sample_rate)

        return wf1, wf2, t_overall


    def simple_pulse(self, AMP_SATURATION1, AMP_SATURATION2, waveform_params={}, sample_rate=1250):
        assert len(waveform_params) == 7
        amp1 = waveform_params['amp1']
        amp2 = waveform_params['amp2']
        freq1 = waveform_params['freq1']
        freq2 = waveform_params['freq2']
        phase1 = waveform_params["phase1"]
        phase2 = waveform_params["phase2"]
        t = waveform_params['t']

        waveform1 = SinCombine(freq1, amp1, phase1, t, sample_rate)

        waveform2 = SinCombine(freq2, amp2, phase2, t, sample_rate)

        return waveform1, waveform2



    def segmented_pulses(self, f_list, a_list, p_list, t_list, t_start, t_shape, N_segments, AMP_SATURATION1, AMP_SATURATION2, sample_rate):
        assert len(a_list) == N_segments
        assert len(f_list) == N_segments
        assert len(p_list) == N_segments
        assert len(t_list) == N_segments

        wf1 = []  # Waveform for channel 1
        wf2 = []  # Waveform for channel 2
        t_overall = t_start
        for i in range(N_segments):
            wf1 += ShapedSinCombine(f_list[i][0], a_list[i][0], p_list[i][0] + t_overall * f_list[i][0],
                                    t_list[i], t_shape, sample_rate, AMP_SATURATION1)
            wf2 += ShapedSinCombine(f_list[i][1], a_list[i][1], p_list[i][1] + t_overall * f_list[i][1],
                                    t_list[i], t_shape, sample_rate, AMP_SATURATION2)
            t_overall = accumulate_pulse_time(t_list[i], t_overall, sample_rate)
        return wf1, wf2, t_overall
    


    def ZZ_gate_pulse(self, AMP_SATURATION1, AMP_SATURATION2, waveform_params={}, sample_rate=1250):

        assert len(waveform_params)==9
        N_segments = waveform_params["N_segments"]
        a_list = waveform_params["a_list"]
        f_list = waveform_params["f_list"]
        p_list = waveform_params["p_list"]
        t = waveform_params["t"]
        t_shape = waveform_params["t_shape"]
        t_echo = waveform_params["t_echo"]

        t_off = waveform_params["t_off"]
        t_off_before = waveform_params["t_off_before"]

        t_list = [t/N_segments for _ in range(N_segments)]

        assert len(a_list) == N_segments
        assert len(p_list) == N_segments
        assert len(t_list) == N_segments
        assert len(f_list) == N_segments

        waveform1 = []
        waveform2 = []

        overall_probe_t = 0

        # Create the delay before the 1st pulse (for AOD ramping up)

        waveform1 += SinCombine(0, 0, 0, t_off_before, sample_rate)
        waveform2 += SinCombine(0, 0, 0, t_off_before, sample_rate)

        # The 1st pulse
        wf1, wf2, t_overall = self.segmented_pulses(f_list, a_list, p_list, t_list, overall_probe_t, t_shape,
                                                    N_segments, AMP_SATURATION1, AMP_SATURATION2, sample_rate)
        waveform1 += wf1
        waveform2 += wf2
        overall_probe_t = t_overall

        # Create the delay between the two pulses (for the MW pi pulse)
        waveform1 += SinCombine(0, 0, 0, t_echo, sample_rate)
        waveform2 += SinCombine(0, 0, 0, t_echo, sample_rate)
        overall_probe_t = accumulate_pulse_time(t_echo, overall_probe_t, sample_rate)


        # The 2nd pulse
        wf1, wf2, t_overall = self.segmented_pulses(f_list, a_list, p_list, t_list, overall_probe_t, t_shape,
                                                    N_segments, AMP_SATURATION1, AMP_SATURATION2, sample_rate)
        waveform1 += wf1
        waveform2 += wf2
        overall_probe_t = t_overall

        # Create the delay and t_off after all the pulses (for AOD ramping down)

        waveform1 += SinCombine(0, 0, 0, t_off, sample_rate)
        waveform2 += SinCombine(0, 0, 0, t_off, sample_rate)


        return waveform1, waveform2





    def N_loop_ZZgate_pulse(self, AMP_SATURATION1, AMP_SATURATION2, waveform_params={}, sample_rate=1250):

        assert len(waveform_params)==10
        N_segments = waveform_params["N_segments"]
        N_loop = waveform_params["N_loop"]
        a_list = waveform_params["a_list"]
        f_list = waveform_params["f_list"]
        p_list = waveform_params["p_list"]
        t = waveform_params["t"]
        t_shape = waveform_params["t_shape"]
        t_echo = waveform_params["t_echo"]

        t_off = waveform_params["t_off"]
        t_off_before = waveform_params["t_off_before"]

        t_list = [t/N_segments for _ in range(N_segments)]

        assert len(a_list) == N_segments
        assert len(p_list) == N_segments
        assert len(t_list) == N_segments
        assert len(f_list) == N_segments

        waveform1 = []
        waveform2 = []

        overall_probe_t = 0

        # Create the delay before the 1st pulse (for AOD ramping up)

        waveform1 += SinCombine(0, 0, 0, t_off_before, sample_rate)
        waveform2 += SinCombine(0, 0, 0, t_off_before, sample_rate)

        for i in range(N_loop):
            # The 1st pulse
            wf1, wf2, t_overall = self.segmented_pulses(f_list, a_list, p_list, t_list, overall_probe_t, t_shape,
                                                        N_segments, AMP_SATURATION1, AMP_SATURATION2, sample_rate)
            waveform1 += wf1
            waveform2 += wf2
            overall_probe_t = t_overall

            # Create the delay between the two pulses (for the MW pi pulse)
            waveform1 += SinCombine(0, 0, 0, t_echo, sample_rate)
            waveform2 += SinCombine(0, 0, 0, t_echo, sample_rate)
            overall_probe_t = accumulate_pulse_time(t_echo, overall_probe_t, sample_rate)


            # The 2nd pulse
            wf1, wf2, t_overall = self.segmented_pulses(f_list, a_list, p_list, t_list, overall_probe_t, t_shape,
                                                        N_segments, AMP_SATURATION1, AMP_SATURATION2, sample_rate)
            waveform1 += wf1
            waveform2 += wf2
            overall_probe_t = t_overall


        # Create the delay and t_off after all the pulses (for AOD ramping down)

        waveform1 += SinCombine(0, 0, 0, t_off, sample_rate)
        waveform2 += SinCombine(0, 0, 0, t_off, sample_rate)


        return waveform1, waveform2



    def Modulated_gate_pulse(self, AMP_SATURATION1, AMP_SATURATION2, waveform_params={}, sample_rate=1250):

        assert len(waveform_params)==10

        N_segments = waveform_params["N_segments"]
        a_list = waveform_params["a_list"]
        f_list = waveform_params["f_list"]
        p_list = waveform_params["p_list"]
        t = waveform_params["t"]
        t_shape = waveform_params["t_shape"]
        t_delay1 = waveform_params["t_delay1"]
        t_delay2 = waveform_params["t_delay2"]

        t_off = waveform_params["t_off"]
        t_off_before = waveform_params["t_off_before"]

        t_list = [t/N_segments for _ in range(N_segments)]

        assert len(a_list) == N_segments
        assert len(p_list) == N_segments
        assert len(t_list) == N_segments
        assert len(f_list) == N_segments

        waveform1 = []
        waveform2 = []

        overall_probe_t = 0

        # Create the delay before the 1st pulse (for the MW pi/2 pulse)

        waveform1 += SinCombine(0, 0, 0, t_delay1 + t_off_before, sample_rate)
        waveform2 += SinCombine(0, 0, 0, t_delay1 + t_off_before, sample_rate)

        # The 1st pulse
        wf1, wf2, t_overall = self.segmented_pulses(f_list, a_list, p_list, t_list, overall_probe_t, t_shape,
                                                    N_segments, AMP_SATURATION1, AMP_SATURATION2, sample_rate)
        waveform1 += wf1
        waveform2 += wf2
        overall_probe_t = t_overall

        # Create the delay between the two pulses (for the MW pi pulse)
        waveform1 += SinCombine(0, 0, 0, t_delay2, sample_rate)
        waveform2 += SinCombine(0, 0, 0, t_delay2, sample_rate)
        overall_probe_t = accumulate_pulse_time(t_delay2, overall_probe_t, sample_rate)

        # The 2nd pulse
        wf1, wf2, t_overall = self.segmented_pulses(f_list, a_list, p_list, t_list, overall_probe_t, t_shape,
                                                    N_segments, AMP_SATURATION1, AMP_SATURATION2, sample_rate)
        waveform1 += wf1
        waveform2 += wf2
        overall_probe_t = t_overall

        # Create the delay and t_off after all the pulses (for the MW pi/2 pulse and AOD ramping down)

        waveform1 += SinCombine(0, 0, 0, t_delay1 + t_off, sample_rate)
        waveform2 += SinCombine(0, 0, 0, t_delay1 + t_off, sample_rate)

        # if t_off is not None and t_off > 0:
        #     waveform1 += ShapedSinCombine(0, 0, 0, t_off, t_shape, sample_rate,
        #                                              AMP_SATURATION1)
        #     waveform2 += ShapedSinCombine(0, 0, 0, t_off, t_shape, sample_rate,
        #                                              AMP_SATURATION2)


        return waveform1, waveform2




    def Shapedpulse_with_offtime(self, AMP_SATURATION1, AMP_SATURATION2, waveform_params={}, sample_rate=1250):
        assert len(waveform_params) == 10
        amp1 = waveform_params['amp1']
        amp2 = waveform_params['amp2']
        freq1 = waveform_params['freq1']
        freq2 = waveform_params['freq2']
        phase1 = waveform_params["phase1"]
        phase2 = waveform_params["phase2"]
        t = waveform_params['t']
        t_shape = waveform_params['t_shape']
        t_off = waveform_params['t_off']
        t_off_before = waveform_params['t_off_before']

        waveform1 = []
        waveform2 = []

        if t_off_before is not None and t_off_before > 0:
            waveform1 += ShapedSinCombine(freq1, 0, 0, t_off_before, t_shape,
                                                        sample_rate, AMP_SATURATION1)
            waveform2 += ShapedSinCombine(freq2, 0, 0, t_off_before, t_shape,
                                                        sample_rate, AMP_SATURATION2)
        waveform1 += ShapedSinCombine(freq1, amp1, phase1, t, t_shape,
                                                 sample_rate, AMP_SATURATION1)
        waveform2 += ShapedSinCombine(freq2, amp2, phase2, t, t_shape,
                                                 sample_rate, AMP_SATURATION2)
        # Turn off the output for t_off after the probe
        if t_off is not None and t_off > 0:
            waveform1 += ShapedSinCombine(freq1, 0, 0, t_off, t_shape,
                                                     sample_rate, AMP_SATURATION1)
            waveform2 += ShapedSinCombine(freq2, 0, 0, t_off, t_shape,
                                                     sample_rate, AMP_SATURATION2)


        return waveform1, waveform2




    def SK1_pulse(self, AMP_SATURATION1, AMP_SATURATION2, waveform_params={}, sample_rate=1250):

        assert len(waveform_params)==10

        amp1 = waveform_params['amp1']
        amp2 = waveform_params['amp2']
        freq1 = waveform_params['freq1']
        freq2 = waveform_params['freq2']
        phase1 = waveform_params["phase1"]
        phase2 = waveform_params["phase2"]
        theta = waveform_params['theta']
        pi_time = waveform_params['pi_time']
        t_off = waveform_params['t_off']
        t_off_before = waveform_params['t_off_before']

        wf1 = []
        wf2 = []
        t_overall = 0

        t_theta = theta/np.pi * pi_time
        t_2pi = 2 * pi_time
        phi0 = SK1_phi(theta)/2/np.pi/2   #double pass and the unit of phase is 2*pi

        # delay for waiting the AOD ramping up
        wf1, wf2, t_overall = self.add_ShapedPulse_to_waveform(wf1, wf2, 0, 0, 0,
                                                         0, 0, 0, AMP_SATURATION1, AMP_SATURATION2,
                                                         t_off_before, t_overall,
                                                         sample_rate=sample_rate)


        # The SK1 waveform

        wf1, wf2, t_overall = self.add_ShapedPulse_to_waveform(wf1, wf2, freq1, amp1, phase1,
                                                         freq2, amp2, phase2,
                                                         AMP_SATURATION1, AMP_SATURATION2,
                                                         t_theta, t_overall,
                                                         sample_rate=sample_rate)

        # delay for AOM response
        wf1, wf2, t_overall = self.add_ShapedPulse_to_waveform(wf1, wf2, 0, 0, 0,
                                                               0, 0, 0, AMP_SATURATION1, AMP_SATURATION2,
                                                               1, t_overall,
                                                               sample_rate=sample_rate)

        wf1, wf2, t_overall = self.add_ShapedPulse_to_waveform(wf1, wf2, freq1, amp1, phase1+phi0,
                                                         freq2, amp2, phase2+phi0,
                                                         AMP_SATURATION1, AMP_SATURATION2,
                                                         t_2pi, t_overall,
                                                         sample_rate=sample_rate)

        # delay for AOM response
        wf1, wf2, t_overall = self.add_ShapedPulse_to_waveform(wf1, wf2, 0, 0, 0,
                                                               0, 0, 0, AMP_SATURATION1, AMP_SATURATION2,
                                                               1, t_overall,
                                                               sample_rate=sample_rate)

        wf1, wf2, t_overall = self.add_ShapedPulse_to_waveform(wf1, wf2, freq1, amp1, phase1-phi0,
                                                         freq2, amp2, phase2-phi0,
                                                         AMP_SATURATION1, AMP_SATURATION2,
                                                         t_2pi, t_overall,
                                                         sample_rate=sample_rate)

        # delay for waiting the AOD ramping down
        wf1, wf2, t_overall = self.add_ShapedPulse_to_waveform(wf1, wf2, 0, 0, 0,
                                                         0, 0, 0,
                                                         AMP_SATURATION1, AMP_SATURATION2,
                                                         t_off, t_overall,
                                                         sample_rate=sample_rate)




        return wf1, wf2



class DeviceSpectrumAWG:
    def __init__(self, address, init_card=True, Max_Vol=125, AMP_SATURATION_AOM1=np.pi/2/1.92, AMP_SATURATION_AOM2=np.pi/2/1.84):
        # open the card
        self.card = spcm_hOpen (create_string_buffer (address))
        if self.card == None:
            sys.stdout.write("no card found...\n")
            exit (1)

        # self.n_seg = 8 # the number of memory segments
        self.n_seg = 12 # the number of memory segments

        self._sample_rate = 1250 # MHz
        # the DAC range is from -32768 to 32767.
        self._full_scale = uint32 (32767)
        self._half_scale = uint32 (self._full_scale.value // 2)

        self.Max_Vol = Max_Vol
        self.AMP_SATURATION_AOM1 = AMP_SATURATION_AOM1
        self.AMP_SATURATION_AOM2 = AMP_SATURATION_AOM2

        
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
        # llChEnable = int64 (CHANNEL0)
        llChEnable = int64 (CHANNEL0 | CHANNEL1) # uncomment to enable two channels
        lMaxSegments = int32 (self.n_seg)
        spcm_dwSetParam_i32 (self.card, SPC_CARDMODE,            SPC_REP_STD_SEQUENCE)
        spcm_dwSetParam_i64 (self.card, SPC_CHENABLE,            llChEnable)
        dwErr = spcm_dwSetParam_i32 (self.card, SPC_SEQMODE_MAXSEGMENTS, lMaxSegments)
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
            # spcm_dwSetParam_i32(self.card, SPC_TRIG_TERM, 1) # 1 = 50 ohm termination, 0 = 1 kOhm termination
        else:
            spcm_dwSetParam_i32 (self.card, SPC_TRIG_ORMASK,      SPC_TMASK_SOFTWARE) # software trigger

        # spcm_dwSetParam_i32(self.card, SPC_TRIG_DELAY, 0)
        # spcm_dwSetParam_i32 (self.card, SPC_TRIG_ANDMASK,     0)
        # spcm_dwSetParam_i32 (self.card, SPC_TRIG_CH_ORMASK0,  0)
        # spcm_dwSetParam_i32 (self.card, SPC_TRIG_CH_ORMASK1,  0)
        # spcm_dwSetParam_i32 (self.card, SPC_TRIG_CH_ANDMASK0, 0)
        # spcm_dwSetParam_i32 (self.card, SPC_TRIG_CH_ANDMASK1, 0)
        spcm_dwSetParam_i32 (self.card, SPC_TRIGGEROUT,       0)

    def setup_channels(self):
        # setup the channels
        lNumChannels = int32 (0)
        spcm_dwGetParam_i32 (self.card, SPC_CHCOUNT, byref (lNumChannels))
        for lChannel in range (0, lNumChannels.value, 1):
            spcm_dwSetParam_i32 (self.card, SPC_ENABLEOUT0    + lChannel * (SPC_ENABLEOUT1    - SPC_ENABLEOUT0),    1)
            spcm_dwSetParam_i32 (self.card, SPC_AMP0          + lChannel * (SPC_AMP1          - SPC_AMP0),          self.Max_Vol)
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
        spcm_dwSetParam_i32(self.card, SPC_M2CMD, M2CMD_CARD_FORCETRIGGER); # Force trigger is used.

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

    # Implementation by Wang Ye
    def read_error_msg(self):
        buffer_error_msg = ctypes.create_string_buffer(100)
        spcm_dwGetErrorInfo_i32(self.card, ctypes.byref(ctypes.c_uint32()), ctypes.byref(ctypes.c_int32()), buffer_error_msg)
        print(buffer_error_msg.value.decode('ascii'))

    def write_segment_two_channels(self, waveform1, waveform2, segment_index):
        # t_start = datetime.datetime.now()
        # Adapted from vDoDataCalculation in the code example from Spectrum
        # t0 = time.time()

        waveform1 = list(waveform1) # waveform for channel 1
        waveform2 = list(waveform2) # waveform for channel 2

        # The minimal segment size is 192 for 2 channels
        waveform1 = pad_zero(waveform1, 192)
        waveform2 = pad_zero(waveform2, 192)

        # Make sure the two lists have the same length by padding zeros
        waveform1 = pad_zero(waveform1, len(waveform2))
        waveform2 = pad_zero(waveform2, len(waveform1))

        # Make sure the length of the waveform is integer times of 32 by padding zeros at its end
        n_zero = (32 - len(waveform1) % 32) % 32
        waveform1 = waveform1 + [0] * n_zero
        waveform2 = waveform2 + [0] * n_zero

        # Zip the two lists: https://stackoverflow.com/questions/7946798/interleave-multiple-lists-of-the-same-length-in-python
        waveform = [val for pair in zip(waveform1, waveform2) for val in pair]

        # print("time for dealing with waveform format:%.2f"%(time.time()-t0))  # for a 5-loop gate with about 1.7ms length, the time spent is about 0.7s.

        # t_interleave_data = datetime.datetime.now() - t_start
        # print(t_interleave_data)

        # t0 = time.time()

        dwSegmentLenSample = int(len(waveform1)) # the length of the waveform for a single channel, not the interleaved waveform for 2 channels
        # dwSegmentLenSample = int(np.maximum(len(waveform), 192))
        dwSegLenByte = uint32(0)

        # For our M4i.6631 model, this factor should be 6.
        dwFactor = 6

        # buffer for data transfer
        dwSegLenByte = 2 * dwFactor * dwSegmentLenSample
        # dwSegLenByte = dwFactor * dwSegmentLenSample * 1
        pvBuffer = pvAllocMemPageAligned(dwSegLenByte)
        pnData = cast(addressof(pvBuffer), ptr16)
        
        # print(pnData)
        # Make sure the waveform does not overflow the awg DAC
        assert np.max(np.abs(np.array(waveform))) <= 1.0

        # There should be a way to speed up this.
        # for i in range(0, len(waveform), 1):
        #     pnData[i] = int16(int(self._full_scale.value * waveform[i]))

        # print(pnData[1])
        # pnData = np.array(waveform) * self._full_scale.value.astype(np.int16)
        waveform = np.array(waveform) * self._full_scale.value  # Convert the amplitudes of waveform to DAC values
        waveform = waveform.astype(np.int16)
        waveform = np.ascontiguousarray(waveform, dtype=np.int16)
        waveform_ptr = waveform.ctypes.data_as(ctypes.POINTER(ctypes.c_int16))

        memmove(pnData, waveform_ptr, len(waveform)*2)

        # print("time for transferring the waveform to the buffer memory:%.2f"%(time.time()-t0))  #5-loop gate with ~1.7ms spends ~0.7s

        # t_organize = datetime.datetime.now() - t_start
        # print(t_organize)

        # t0 = time.time()

        vWriteSegmentData(self.card, uint32(2), segment_index, dwSegmentLenSample, pvBuffer)

        # print("time for writing the waveform into the AWG:%.2f"%(time.time()-t0))  # 5-loop gate with ~1.7ms spends ~0.4s
        # t_transmission = datetime.datetime.now() - t_organize - t_start
        # print(t_transmission)



class MultiPulses:

    def __init__(self, seq_dict={}, seq_list=[], device=None):
        '''

        Parameters
        ----------
        seq_dict: It is a dictionary whose keys are the names of the memory segments and
                  whose values are the pulse class used in the corresponding memory segment.
                  It looks like {1: "simple_pulse", 2: "2qgate"}. Notice:the names of the
                  memory seg must not be zero, since zero is occupied.
        seq_list: It is a list describing the sequence of how to play the memory segments.
                  For example [1, 2, 3] means 1 -> 2 -> 3 and each jump needs a ttl signal.
        device: awg device object generate by DeviceSpectrumAWG

        self.Block_params: It is used to store the waveform parameters for different memory segments.

        NOTICE
        ----------
        This class use the spectrum AWG in the sequence-replay way, which means there is a time jitter
        between replays. Thus it is not suitable to split the waveform into two memory segments and trigger
        to replay these two when the phase coherence during this waveform is important in your experiment.
        '''

        self.pulselib = PulsesLibrary_2ch()
        self._namelist = list(seq_dict.values())
        self._seglist = list(seq_dict.keys())
        self._seq_dict = seq_dict

        for i in range(len(self._namelist)):
            if not self._namelist[i] in self.pulselib.legal_class:
                print(str(self._namelist[i]) + "is illegal")
                assert self._namelist[i] in self.pulselib.legal_class

            else:
                pass

        assert set(seq_list)==set(self._seglist)


        if device is None:
            self.awg = DeviceSpectrumAWG(b'TCPIP::192.168.1.8::inst0::INSTR')
        else:
            # passing the instance of DeviceSpectrumAWG to this class might be safer
            self.awg = device
        self._sample_rate = self.awg._sample_rate

        # A safe margin time to account for the uncertainty of pulse starting time of the AWG,
        # to avoid the awg pulse overlapping with the other pulses
        self.t_margin = 3

        # the position of the idle pulse in the step register
        self._seq_start_step = 0

        self._step_end_of_sequence = self.awg.n_seg*2

        # generate an idle pulse for later uses
        self._seg_idle = 0
        self.waveform_idle1 = [0]
        self.waveform_idle2 = [0]


        self._step_blocks = seq_list
        self._seg_blocks = seq_list
        self._step_idle_gap = [self._step_end_of_sequence-seq_list[i] for i in range(len(seq_list)-1)]
        self._seg_blocks_set = list(set(seq_list))
        self.waveform1_blocks = []
        self.waveform2_blocks = []

        for i in range(len(self._seg_blocks_set)):
            self.waveform1_blocks.append([])
            self.waveform2_blocks.append([])



        # Write zeros to each segment in the initialization
        for i in range(len(self._seg_blocks_set)):
            self.awg.write_segment_two_channels([0], [0], segment_index=self._seg_blocks_set[i])

        # write the idle pulse to the idle segment of the awg memory
        self.awg.write_segment_two_channels(self.waveform_idle1, self.waveform_idle2, self._seg_idle)

        # Keep track of the overall probe time for phase calculation in the phase-coherent manner
        # self._overall_probe_t = 0
        self.Block_params = {}.fromkeys(self._seg_blocks_set, {})



        self.load_sequence()


    def load_sequence(self):
        # Configure the idle pulse at the beginning. Link it to the subsequent SBC pulses.
        # step_idle_gap = self._step_end_of_sequence-1

        vWriteStepEntry(self.awg.card, self._seq_start_step, self._step_blocks[0],
                        self._seg_idle, 1, SPCSEQ_ENDLOOPONTRIG)

        for i in range(len(self._step_blocks)-1):
            vWriteStepEntry(self.awg.card, self._step_blocks[i], self._step_idle_gap[i],
                            self._seg_blocks[i], 1, 0)

            vWriteStepEntry(self.awg.card, self._step_idle_gap[i], self._step_blocks[i+1],
                            self._seg_idle, 1, SPCSEQ_ENDLOOPONTRIG)

        # Configure the probe pulse. Link it to an idle pulse at the end of the sequence.
        vWriteStepEntry(self.awg.card, self._step_blocks[-1], self._step_end_of_sequence,
                        self._seg_blocks[-1], 1, 0)
        self.finish_sequence(self._step_end_of_sequence)


    def finish_sequence(self, last_step):
        # (not sure if there's a problem when the starting step is the only one. perhaps not?)
        assert last_step != self._seq_start_step

        # Link the last step to the idle segment and loop it back to the starting step
        vWriteStepEntry (self.awg.card,  last_step,  self._seq_start_step,
                         self._seg_idle,      1,  SPCSEQ_ENDLOOPALWAYS)
        # Configure the beginning (index of first seq-entry to start) of the sequence replay.
        spcm_dwSetParam_i32 (self.awg.card, SPC_SEQMODE_STARTSTEP, self._seq_start_step)



    def set_waveform(self, seg_name='all'):
        seg_names = list(self.Block_params.keys())

        if seg_name == 'all':
            # t0 = time.time()
        
            for i in range(len(seg_names)):

                pulsefunc = self.pulselib.func_call(self._seq_dict[seg_names[i]])
                wf1, wf2 = pulsefunc(self.awg.AMP_SATURATION_AOM1, self.awg.AMP_SATURATION_AOM2,
                                     waveform_params=self.Block_params[seg_names[i]], sample_rate=self._sample_rate)

                self.waveform1_blocks[i] = wf1
                self.waveform2_blocks[i] = wf2
            # print("time for waveform generation:%.2f"%(time.time()-t0))  #three 5-loop gate each with ~1.7ms spends ~1.3s


        else:
            assert seg_name in seg_names
            # t0 = time.time()

            ind = seg_names.index(seg_name)

            pulsefunc = self.pulselib.func_call(self._seq_dict[seg_name])
            wf1, wf2 = pulsefunc(self.awg.AMP_SATURATION_AOM1, self.awg.AMP_SATURATION_AOM2,
                                 waveform_params=self.Block_params[seg_name], sample_rate=self._sample_rate)

            self.waveform1_blocks[ind] = wf1
            self.waveform2_blocks[ind] = wf2

            # print("time for waveform generation:%.2f"%(time.time()-t0))


    def reset_waveform(self):

        self.waveform1_blocks = []
        self.waveform2_blocks = []

        for i in range(len(self._seg_blocks_set)):
            self.waveform1_blocks.append([])
            self.waveform2_blocks.append([])


    def update_idle(self):
        self.awg.stop_card()
        self.awg.write_segment_two_channels(self.waveform_idle1, self.waveform_idle2, self._seg_idle)
        self.awg.start_card()


    def update_segment(self, seg_name='all'):
        seg_names = list(self.Block_params.keys())

        if seg_name == 'all':
            # t0 = time.time()
            self.awg.stop_card()
            for i in range(len(seg_names)):
                self.awg.write_segment_two_channels(self.waveform1_blocks[i], self.waveform2_blocks[i], segment_index=seg_names[i])
            self.awg.start_card()
            # print("time for segment update:%.2f"%(time.time()-t0))  #three 5-loop gate each with ~1.7ms spends ~2.8s

        else:
            assert seg_name in seg_names
            # t0 = time.time()

            ind = seg_names.index(seg_name)
            self.awg.stop_card()
            self.awg.write_segment_two_channels(self.waveform1_blocks[ind], self.waveform2_blocks[ind], segment_index=seg_names[ind])

            self.awg.start_card()
            # print("time for segment update:%.2f"%(time.time()-t0))



class SequenceSpectrumAWG_2Channels:
    # This class keeps track of the sequence to run on Spectrum AWG,
    # and calls the lower-level functions to configure the sequence on the AWG.        
    def __init__(self, device=None):
        if device is None:
            self.awg = DeviceSpectrumAWG(b'TCPIP::192.168.1.8::inst0::INSTR')
        else:
            # passing the instance of DeviceSpectrumAWG to this class might be safer
            self.awg = device
        self._sample_rate = self.awg._sample_rate

        # A safe margin time to account for the uncertainty of pulse starting time of the AWG,
        # to avoid the awg pulse overlapping with the other pulses
        self.t_margin = 3

        # the position of the idle pulse in the step register
        self._seq_start_step = 0

        # the step for sideband cooling
        self._step_sbc = 1
        # the step for probe
        self._step_probe = 2
        # the step for shelving detection
        self._step_shelving = 3

        # generate an idle pulse for later uses
        self.waveform_idle1 = [0]
        self.waveform_idle2 = [0]

        self.waveform_probe1 = []
        self.waveform_probe2 = []

        self.waveform_sbc1 = []
        self.waveform_sbc2 = []

        self.waveform_shelving1 = []
        self.waveform_shelving2 = []

        self._seg_idle = 0
        self._seg_sbc = 1
        self._seg_probe = 2
        self._seg_shelving = 3

        # Write zeros to each segment in the initialization
        self.awg.write_segment_two_channels([0], [0], segment_index=self._seg_probe)
        self.awg.write_segment_two_channels([0], [0], segment_index=self._seg_shelving)
        
        # write the idle pulse to the idle segment of the awg memory
        self.awg.write_segment_two_channels(self.waveform_idle1, self.waveform_idle2, self._seg_idle)

        # Keep track of the overall probe time for phase calculation in the phase-coherent manner
        self._overall_probe_t = 0

    def finish_sequence(self, last_step):
        # (not sure if there's a problem when the starting step is the only one. perhaps not?)
        assert last_step != self._seq_start_step

        # Link the last step to the idle segment and loop it back to the starting step
        vWriteStepEntry (self.awg.card,  last_step,  self._seq_start_step, 
                         self._seg_idle,      1,  SPCSEQ_ENDLOOPALWAYS)
        # Configure the beginning (index of first seq-entry to start) of the sequence replay.
        spcm_dwSetParam_i32 (self.awg.card, SPC_SEQMODE_STARTSTEP, self._seq_start_step)

    def add_pulse_to_sbc(self, freq1, amp1, phase1, freq2, amp2, phase2, t):
        self.waveform_sbc1 = self.waveform_sbc1 + SinCombine(freq1, amp1, phase1, t, self._sample_rate)
        self.waveform_sbc2 = self.waveform_sbc2 + SinCombine(freq2, amp2, phase2, t, self._sample_rate)

    def add_sin_squared_pulse_to_sbc(self, freq1, I_top1, phase1, t_shape1, freq2, I_top2, phase2, t_shape2, duration):
        self.waveform_sbc1 = self.waveform_sbc1 + ShapedSinCombine(freq1, I_top1, phase1, duration,
                                                                     t_shape1, self._sample_rate,
                                                                     self.awg.AMP_SATURATION_AOM1)


        self.waveform_sbc2 = self.waveform_sbc2 + ShapedSinCombine(freq2, I_top2, phase2, duration,
                                                                     t_shape2, self._sample_rate,
                                                                     self.awg.AMP_SATURATION_AOM2)



    def add_pulse_to_idle(self, freq1, amp1, phase1, freq2, amp2, phase2, t):
        self.waveform_idle1 = self.waveform_idle1 + SinCombine(freq1, amp1, phase1, t, self._sample_rate)
        self.waveform_idle2 = self.waveform_idle2 + SinCombine(freq2, amp2, phase2, t, self._sample_rate)


    def add_pulse_to_probe(self, freq1, amp1, phase1, freq2, amp2, phase2, t):
        phase1 += freq1 * (self._overall_probe_t)  # Calculate the phase in the phase-coherent manner
        phase2 += freq2 * (self._overall_probe_t)
        self.waveform_probe1 = self.waveform_probe1 + SinCombine(freq1, amp1, phase1, t, self._sample_rate)
        self.waveform_probe2 = self.waveform_probe2 + SinCombine(freq2, amp2, phase2, t, self._sample_rate)
        if t > 0:
            self._overall_probe_t += np.arange(0, t, 1 / self._sample_rate)[-1] + 1 / self._sample_rate

    def add_HS1_to_probe(self, freq_start1, freq_end1, amp1, beta1, freq_start2, freq_end2, amp2, beta2, t):
        self.waveform_probe1 = self.waveform_probe1 + HS1_sweep(freq_start1, freq_end1, amp1, beta1, t, self._sample_rate)
        self.waveform_probe2 = self.waveform_probe2 + HS1_sweep(freq_start2, freq_end2, amp2, beta2, t, self._sample_rate)
        if t > 0:
            self._overall_probe_t += np.arange(0, t, 1 / self._sample_rate)[-1] + 1 / self._sample_rate

    def add_sin_squared_pulse_to_probe(self, freq1, I_top1, phase1,  t_shape1, freq2, I_top2, phase2, t_shape2, duration):
        phase1 += freq1 * (self._overall_probe_t)  # Calculate the phase in the phase-coherent manner
        phase2 += freq2 * (self._overall_probe_t)
        self.waveform_probe1 = self.waveform_probe1 + ShapedSinCombine(freq1, I_top1, phase1, duration,
                                                                     t_shape1, self._sample_rate,
                                                                     self.awg.AMP_SATURATION_AOM1)

        self.waveform_probe2 = self.waveform_probe2 + ShapedSinCombine(freq2, I_top2, phase2, duration,
                                                                       t_shape2, self._sample_rate,
                                                                       self.awg.AMP_SATURATION_AOM2)

        if duration > 0:
            self._overall_probe_t += np.arange(0, duration, 1 / self._sample_rate)[-1] + 1 / self._sample_rate



    def add_pulse_to_shelving(self, freq1, amp1, phase1, freq2, amp2, phase2, t):
        phase1 += freq1 * (self._overall_probe_t)  # Calculate the phase in the phase-coherent manner
        phase2 += freq2 * (self._overall_probe_t)
        self.waveform_shelving1 = self.waveform_shelving1 + SinCombine(freq1, amp1, phase1, t, self._sample_rate)
        self.waveform_shelving2 = self.waveform_shelving2 + SinCombine(freq2, amp2, phase2, t, self._sample_rate)
        if t > 0:
            self._overall_probe_t += np.arange(0, t, 1 / self._sample_rate)[-1] + 1 / self._sample_rate

    def reset_probe_waveform(self):
        self.waveform_probe1 = []
        self.waveform_probe2 = []
        self._overall_probe_t = 0

    # Load the waveforms to the awg memory
    def update_probe(self):
        self.awg.stop_card()
        self.awg.write_segment_two_channels(self.waveform_probe1, self.waveform_probe2, segment_index=self._seg_probe)
        self.awg.start_card()
        # plt.plot(np.arange(len(self.waveform_probe1)) / self._sample_rate, self.waveform_probe1)
        # plt.plot(np.arange(len(self.waveform_probe2)) / self._sample_rate, self.waveform_probe2)
        # plt.show()

    def update_sbc(self):
        self.awg.stop_card()
        self.awg.write_segment_two_channels(self.waveform_sbc1, self.waveform_sbc2, segment_index=self._seg_sbc)
        self.awg.start_card()
    
    def update_idle(self):
        self.awg.stop_card()
        self.awg.write_segment_two_channels(self.waveform_idle1, self.waveform_idle2, self._seg_idle)
        self.awg.start_card()

    def update_shelving(self):
        self.awg.stop_card()
        self.awg.write_segment_two_channels(self.waveform_shelving1, self.waveform_shelving2, segment_index=self._seg_shelving)
        self.awg.start_card()

class ProbeSequence(SequenceSpectrumAWG_2Channels):
    # A sub-class of SequenceSpectrumAWG
    def __init__(self, device=None):
        super().__init__(device)
        # Step for a short idle pulse at the end of the sequence.
        # Its location in the step register doesn't matter.
        self._step_end_of_sequence = 16

        self.t_probe = None
        self.t_off_before = 0 # An optional off-time before the probe sequence
        self.t_off = None
        self.a_probe1 = None
        self.f_probe1 = None
        self.a_probe2 = None
        self.f_probe2 = None

        self.load_sequence()

    def load_sequence(self):
        # Configure the idle pulse at the beginning. Link it to the probe pulses.
        vWriteStepEntry (self.awg.card,  self._seq_start_step,  self._step_probe,
                         self._seg_idle,      1,  SPCSEQ_ENDLOOPONTRIG)

        vWriteStepEntry(self.awg.card, self._step_probe, self._step_end_of_sequence,
                        self._seg_probe, 1, SPCSEQ_ENDLOOPALWAYS)
        self.finish_sequence(self._step_end_of_sequence)


    def update_freq(self, freq1, freq2):
        assert self.t_probe is not None and self.a_probe1 is not None and self.a_probe2 is not None
        self.f_probe1 = freq1
        self.f_probe2 = freq2
        self.waveform_probe1 = []
        self.waveform_probe2 = []
        if self.t_off_before > 0:
            self.waveform_probe1 += SinCombine(self.f_probe1, 0, 0, self.t_off_before, self._sample_rate)
            self.waveform_probe2 += SinCombine(self.f_probe2, 0, 0, self.t_off_before, self._sample_rate)
        # Overwrite the probe waveform using the new parameters
        self.waveform_probe1 += SinCombine(self.f_probe1, self.a_probe1, 0, self.t_probe, self._sample_rate)
        self.waveform_probe2 += SinCombine(self.f_probe2, self.a_probe2, 0, self.t_probe, self._sample_rate)
        if self.t_off is not None and self.t_off > 0:
            self.waveform_probe1 += SinCombine(self.f_probe1, 0, 0, self.t_off, self._sample_rate)
            self.waveform_probe2 += SinCombine(self.f_probe2, 0, 0, self.t_off, self._sample_rate)
        # Load the new waveform to the AWG
        self.update_probe()

    def update_time(self, t):
        assert self.f_probe1 is not None and self.a_probe1 is not None and self.f_probe2 is not None and self.a_probe2 is not None
        self.t_probe = t

        self.waveform_probe1 = []
        self.waveform_probe2 = []
        if self.t_off_before > 0:
            self.waveform_probe1 += SinCombine(self.f_probe1, 0, 0, self.t_off_before, self._sample_rate)
            self.waveform_probe2 += SinCombine(self.f_probe2, 0, 0, self.t_off_before, self._sample_rate)
        # Overwrite the probe waveform using the new parameters
        self.waveform_probe1 += SinCombine(self.f_probe1, self.a_probe1, 0, self.t_probe, self._sample_rate)
        self.waveform_probe2 += SinCombine(self.f_probe2, self.a_probe2, 0, self.t_probe, self._sample_rate)
        if self.t_off is not None and self.t_off > 0:
            self.waveform_probe1 += SinCombine(self.f_probe1, 0, 0, self.t_off, self._sample_rate)
            self.waveform_probe2 += SinCombine(self.f_probe2, 0, 0, self.t_off, self._sample_rate)
        self.update_probe()

    def update_waveform(self):
        assert self.t_probe is not None and self.a_probe1 is not None and self.f_probe1 is not None and self.a_probe2 is not None and self.f_probe2 is not None
        self.waveform_probe1 = []
        self.waveform_probe2 = []
        if self.t_off_before > 0:
            self.waveform_probe1 += SinCombine(self.f_probe1, 0, 0, self.t_off_before, self._sample_rate)
            self.waveform_probe2 += SinCombine(self.f_probe2, 0, 0, self.t_off_before, self._sample_rate)
        # Overwrite the probe waveform using the new parameters
        self.waveform_probe1 += SinCombine(self.f_probe1, self.a_probe1, 0, self.t_probe, self._sample_rate)
        self.waveform_probe2 += SinCombine(self.f_probe2, self.a_probe2, 0, self.t_probe, self._sample_rate)
        if self.t_off is not None and self.t_off > 0:
            self.waveform_probe1 += SinCombine(self.f_probe1, 0, 0, self.t_off, self._sample_rate)
            self.waveform_probe2 += SinCombine(self.f_probe2, 0, 0, self.t_off, self._sample_rate)
        self.update_probe()



class SbcProbeSequence(ProbeSequence):
    # This is a sub-class of the probe sequence, with the inclusion of SBC pulses
    def __init__(self, device=None):
        super().__init__(device)

    # Overload this method from the parent class
    def load_sequence(self):
        # Configure the idle pulse at the beginning. Link it to the subsequent SBC pulses.
        vWriteStepEntry (self.awg.card,  self._seq_start_step,  self._step_sbc,
                         self._seg_idle, 1,  SPCSEQ_ENDLOOPONTRIG)
        # vWriteStepEntry(self.awg.card, self._step_sbc, self._step_probe,
        #                 self._seg_sbc, 1, 0)
        # Configure the SBC pulse. Link it to another idle.
        vWriteStepEntry(self.awg.card, self._step_sbc, self._step_end_of_sequence - 1,
                        self._seg_sbc, 1, 0)
        # Configure the idle between SBC and probe. Link it to probe.
        vWriteStepEntry(self.awg.card, self._step_end_of_sequence - 1, self._step_probe,
                        self._seg_idle, 1, SPCSEQ_ENDLOOPONTRIG)
        # Configure the probe pulse. Link it to an idle pulse at the end of the sequence.
        vWriteStepEntry(self.awg.card, self._step_probe, self._step_end_of_sequence,
                        self._seg_probe, 1, 0)
        self.finish_sequence(self._step_end_of_sequence)

class ShelvingDetectionSequence(SequenceSpectrumAWG_2Channels):
    # A sub-class of SequenceSpectrumAWG
    def __init__(self, device=None):
        super().__init__(device)
        # Step for a short idle pulse at the end of the sequence.
        # Its location in the step register doesn't matter.
        self._step_end_of_sequence = 16

        self.load_sequence()

    def load_sequence(self):
        # Configure the idle pulse at the beginning. Link it to the shelving pulses.
        vWriteStepEntry (self.awg.card,  self._seq_start_step,  self._step_shelving,
                         self._seg_idle,      1,  SPCSEQ_ENDLOOPONTRIG)
        # Configure the shelving pulse. Link it to an idle pulse.
        vWriteStepEntry(self.awg.card, self._step_shelving, self._step_end_of_sequence,
                        self._seg_shelving, 1, SPCSEQ_ENDLOOPALWAYS)
        self.finish_sequence(self._step_end_of_sequence)


class SbcShelvingSequence(ShelvingDetectionSequence):
    def __init__(self, device=None):
        super().__init__(device)

    def load_sequence(self):
        idle_gap_1 = self._step_end_of_sequence - 1

        # Configure the idle pulse at the beginning. Link it to the subsequent SBC pulses.
        vWriteStepEntry(self.awg.card, self._seq_start_step, self._step_sbc,
                        self._seg_idle, 1, SPCSEQ_ENDLOOPONTRIG)
        # Configure the SBC pulse. Link it to another idle.
        vWriteStepEntry(self.awg.card, self._step_sbc, idle_gap_1,
                        self._seg_sbc, 1, 0)
        # Configure the idle between SBC and shelving. Link it to shelving.
        vWriteStepEntry(self.awg.card, idle_gap_1, self._step_shelving,
                        self._seg_idle, 1, SPCSEQ_ENDLOOPONTRIG)
        # Configure the shelving pulses. Link it to the idle pulse at the end of sequence
        vWriteStepEntry(self.awg.card, self._step_shelving, self._step_end_of_sequence,
                        self._seg_shelving, 1, 0)
        self.finish_sequence(self._step_end_of_sequence)


class ShapedProbeSequence(SequenceSpectrumAWG_2Channels):
    # A sub-class of SequenceSpectrumAWG
    def __init__(self, device=None):
        super().__init__(device)
        # Step for a short idle pulse at the end of the sequence.
        # Its location in the step register doesn't matter.
        self._step_end_of_sequence = 16

        self.t_probe = None
        self.t_shape = None
        self.t_off_before = 0
        self.t_off = None # A period where the output is set to zero, after the probe

        self.a_probe1 = None
        self.f_probe1 = None
        self.a_probe2 = None
        self.f_probe2 = None

        self.load_sequence()

    def load_sequence(self):
        # Configure the idle pulse at the beginning. Link it to the probe pulses.
        vWriteStepEntry (self.awg.card,  self._seq_start_step,  self._step_probe,
                         self._seg_idle,      1,  SPCSEQ_ENDLOOPONTRIG)

        vWriteStepEntry(self.awg.card, self._step_probe, self._step_end_of_sequence,
                        self._seg_probe, 1, SPCSEQ_ENDLOOPALWAYS)
        self.finish_sequence(self._step_end_of_sequence)

    def update_freq(self, freq1, freq2):
        assert self.t_probe is not None and self.a_probe1 is not None and self.a_probe2 is not None
        self.f_probe1 = freq1
        self.f_probe2 = freq2
        # Overwrite the probe waveform using the new parameters
        self.waveform_probe1 = []
        self.waveform_probe2 = []
        if self.t_off_before > 0:
            self.waveform_probe1 += ShapedSinCombine(self.f_probe1, 0, 0, self.t_off_before, self.t_shape,
                                                        self._sample_rate, self.awg.AMP_SATURATION_AOM1)
            self.waveform_probe2 += ShapedSinCombine(self.f_probe2, 0, 0, self.t_off_before, self.t_shape,
                                                        self._sample_rate, self.awg.AMP_SATURATION_AOM2)
        self.waveform_probe1 += ShapedSinCombine(self.f_probe1, self.a_probe1, 0, self.t_probe,
                                                 self.t_shape, self._sample_rate, self.awg.AMP_SATURATION_AOM1)
        self.waveform_probe2 += ShapedSinCombine(self.f_probe2, self.a_probe2, 0, self.t_probe,
                                                 self.t_shape, self._sample_rate, self.awg.AMP_SATURATION_AOM2)
        # Turn off the output for t_off after the probe
        if self.t_off is not None and self.t_off > 0:
            self.waveform_probe1 += ShapedSinCombine(self.f_probe1, 0, 0, self.t_off, self.t_shape,
                                                     self._sample_rate, self.awg.AMP_SATURATION_AOM1)
            self.waveform_probe2 += ShapedSinCombine(self.f_probe2, 0, 0, self.t_off, self.t_shape,
                                                     self._sample_rate, self.awg.AMP_SATURATION_AOM2)
        # Load the new waveform to the AWG
        self.update_probe()

    def update_time(self, t):
        assert self.f_probe1 is not None and self.a_probe1 is not None and self.f_probe2 is not None and self.a_probe2 is not None
        self.t_probe = t

        # t0 = time.time()
        self.waveform_probe1 = []
        self.waveform_probe2 = []

        if self.t_off_before > 0:
            self.waveform_probe1 += ShapedSinCombine(self.f_probe1, 0, 0, self.t_off_before, self.t_shape,
                                                        self._sample_rate, self.awg.AMP_SATURATION_AOM1)
            self.waveform_probe2 += ShapedSinCombine(self.f_probe2, 0, 0, self.t_off_before, self.t_shape,
                                                        self._sample_rate, self.awg.AMP_SATURATION_AOM2)
        self.waveform_probe1 += ShapedSinCombine(self.f_probe1, self.a_probe1, 0, self.t_probe, self.t_shape,
                                                 self._sample_rate, self.awg.AMP_SATURATION_AOM1)
        self.waveform_probe2 += ShapedSinCombine(self.f_probe2, self.a_probe2, 0, self.t_probe, self.t_shape,
                                                 self._sample_rate, self.awg.AMP_SATURATION_AOM2)
        # Turn off the output for t_off after the probe
        if self.t_off is not None and self.t_off > 0:
            self.waveform_probe1 += ShapedSinCombine(self.f_probe1, 0, 0, self.t_off, self.t_shape,
                                                     self._sample_rate, self.awg.AMP_SATURATION_AOM1)
            self.waveform_probe2 += ShapedSinCombine(self.f_probe2, 0, 0, self.t_off, self.t_shape,
                                                     self._sample_rate, self.awg.AMP_SATURATION_AOM2)

        # print(time.time()-t0)

        self.update_probe()


    def update_waveform(self):
        assert self.t_probe is not None and self.a_probe1 is not None and self.f_probe1 is not None and self.a_probe2 is not None and self.f_probe2 is not None
        self.waveform_probe1 = []
        self.waveform_probe2 = []

        if self.t_off_before > 0:
            self.waveform_probe1 += ShapedSinCombine(self.f_probe1, 0, 0, self.t_off_before, self.t_shape,
                                                        self._sample_rate, self.awg.AMP_SATURATION_AOM1)
            self.waveform_probe2 += ShapedSinCombine(self.f_probe2, 0, 0, self.t_off_before, self.t_shape,
                                                        self._sample_rate, self.awg.AMP_SATURATION_AOM1)
        self.waveform_probe1 += ShapedSinCombine(self.f_probe1, self.a_probe1, 0, self.t_probe, self.t_shape,
                                                 self._sample_rate, self.awg.AMP_SATURATION_AOM1)
        self.waveform_probe2 += ShapedSinCombine(self.f_probe2, self.a_probe2, 0, self.t_probe, self.t_shape,
                                                 self._sample_rate, self.awg.AMP_SATURATION_AOM2)
        # Turn off the output for t_off after the probe
        if self.t_off is not None and self.t_off > 0:
            self.waveform_probe1 += ShapedSinCombine(self.f_probe1, 0, 0, self.t_off, self.t_shape,
                                                     self._sample_rate, self.awg.AMP_SATURATION_AOM1)
            self.waveform_probe2 += ShapedSinCombine(self.f_probe2, 0, 0, self.t_off, self.t_shape,
                                                     self._sample_rate, self.awg.AMP_SATURATION_AOM2)

        self.update_probe()





class ShapedTwoLoopGate(SequenceSpectrumAWG_2Channels):
    # A sub-class of SequenceSpectrumAWG, specifically for driving the AOMs for the two-loop LS gate
    def __init__(self, device=None):
        super().__init__(device)
        # Step for a short idle pulse at the end of the sequence.
        # Its location in the step register doesn't matter.
        self._step_end_of_sequence = 16

        self.t_probe = None
        self.t_shape = None

        self.t_delay1 = None # Delay of the 1st pulse
        self.t_delay2 = None # Delay of the 2nd pulse
        self.t_off = None
        self.t_off_before = 0

        self.a_probe1 = None
        self.f_probe1 = None
        self.a_probe2 = None
        self.f_probe2 = None

        self.load_sequence()

    def load_sequence(self):
        # Configure the idle pulse at the beginning. Link it to the probe pulses.
        vWriteStepEntry (self.awg.card,  self._seq_start_step,  self._step_probe,
                         self._seg_idle,      1,  SPCSEQ_ENDLOOPONTRIG)

        vWriteStepEntry(self.awg.card, self._step_probe, self._step_end_of_sequence,
                        self._seg_probe, 1, SPCSEQ_ENDLOOPALWAYS)
        self.finish_sequence(self._step_end_of_sequence)

    def create_waveform(self):
        # Clear the existing waveforms
        self.waveform_probe1 = []
        self.waveform_probe2 = []
        # Clear the time counter for phase calculation
        self._overall_probe_t = 0

        # Create the delay before the 1st pulse (for the MW pi/2 pulse)
        self.waveform_probe1 += SinCombine(self.f_probe1, 0, 0, self.t_delay1 + self.t_off_before, self._sample_rate)
        self.waveform_probe2 += SinCombine(self.f_probe2, 0, 0, self.t_delay1 + self.t_off_before, self._sample_rate)

        # The 1st pulse
        self.waveform_probe1 += ShapedSinCombine(self.f_probe1, self.a_probe1, 0, self.t_probe, self.t_shape,
                                                 self._sample_rate, self.awg.AMP_SATURATION_AOM1)
        self.waveform_probe2 += ShapedSinCombine(self.f_probe2, self.a_probe2, 0, self.t_probe, self.t_shape,
                                                 self._sample_rate, self.awg.AMP_SATURATION_AOM2)
        self._overall_probe_t = accumulate_pulse_time(self.t_probe, self._overall_probe_t, self._sample_rate)

        # Create the delay between the two pulses (for the MW pi pulse)
        self.waveform_probe1 += SinCombine(self.f_probe1, 0, 0, self.t_delay2, self._sample_rate)
        self.waveform_probe2 += SinCombine(self.f_probe2, 0, 0, self.t_delay2, self._sample_rate)
        self._overall_probe_t = accumulate_pulse_time(self.t_delay2, self._overall_probe_t, self._sample_rate)

        # The 2nd pulse
        self.waveform_probe1 += ShapedSinCombine(self.f_probe1, self.a_probe1, self.f_probe1 * self._overall_probe_t,
                                                     self.t_probe, self.t_shape, self._sample_rate, self.awg.AMP_SATURATION_AOM1)
        self.waveform_probe2 += ShapedSinCombine(self.f_probe2, self.a_probe2, self.f_probe2 * self._overall_probe_t,
                                                     self.t_probe, self.t_shape, self._sample_rate, self.awg.AMP_SATURATION_AOM2)
        self._overall_probe_t = accumulate_pulse_time(self.t_probe, self._overall_probe_t, self._sample_rate)

        if self.t_off is not None and self.t_off > 0:
            self.waveform_probe1 += ShapedSinCombine(self.f_probe1, 0, 0, self.t_off, self.t_shape,
                                                     self._sample_rate, self.awg.AMP_SATURATION_AOM1)
            self.waveform_probe2 += ShapedSinCombine(self.f_probe2, 0, 0, self.t_off, self.t_shape,
                                                     self._sample_rate, self.awg.AMP_SATURATION_AOM2)

    def update_freq(self, freq1, freq2):
        self.f_probe1 = freq1
        self.f_probe2 = freq2
        # Overwrite the probe waveform using the new parameters
        self.create_waveform()
        # Load the new waveform to the AWG
        self.update_probe()

    def update_time(self, t):
        self.t_probe = t

        self.create_waveform()
        self.update_probe()

    def update_waveform(self):
        self.create_waveform()
        self.update_probe()



class ModulatedShapedTwoLoopGate(ShapedTwoLoopGate):
    # A sub-class of ShapedTwoLoopGate. The 'create_waveform' method is overloaded to create multi-segment modulation.
    def __init__(self, f_list, a_list, p_list, device=None):
        super().__init__(device)

        # Parameters of the multi-segment pulse, in the format of e.g. [(f11, f21), (f12, f22), ... (f1N, f2N)]
        # Each tuple contains two elements for the two channels. 
        # Each list contains N tuples for the N segments.
        self.f_list = f_list
        self.p_list = p_list
        self.a_list = a_list

        self.N_segments = len(self.f_list)
        # t_list has the form of [t1, t2, ..., tN]
        # self.t_list = t_list

    def segmented_pulses(self, f_list, a_list, p_list, t_list, t_start):
        assert len(a_list) == self.N_segments
        assert len(p_list) == self.N_segments
        assert len(t_list) == self.N_segments
        assert len(f_list) == self.N_segments

        wf1 = [] # Waveform for channel 1
        wf2 = [] # Waveform for channel 2
        t_overall = t_start
        for i in range(self.N_segments):
            wf1 += ShapedSinCombine(f_list[i][0], a_list[i][0], p_list[i][0] + t_overall * f_list[i][0],
                              t_list[i], self.t_shape, self._sample_rate, self.awg.AMP_SATURATION_AOM1)
            wf2 += ShapedSinCombine(f_list[i][1], a_list[i][1], p_list[i][1] + t_overall * f_list[i][1],
                              t_list[i], self.t_shape, self._sample_rate, self.awg.AMP_SATURATION_AOM2)
            t_overall = accumulate_pulse_time(t_list[i], t_overall, self._sample_rate)
        return wf1, wf2, t_overall

    def create_waveform(self):
        # Clear the existing waveforms
        self.waveform_probe1 = []
        self.waveform_probe2 = []
        # Clear the time counter for phase calculation
        self._overall_probe_t = 0

        # Create the delay before the 1st pulse (for the MW pi/2 pulse)
        self.waveform_probe1 += SinCombine(0, 0, 0, self.t_delay1 + self.t_off_before, self._sample_rate)
        self.waveform_probe2 += SinCombine(0, 0, 0, self.t_delay1 + self.t_off_before, self._sample_rate)

        # The 1st pulse
        wf1, wf2, t_overall= self.segmented_pulses(self.f_list, self.a_list, self.p_list, self.t_list, self._overall_probe_t)
        self.waveform_probe1 += wf1
        self.waveform_probe2 += wf2
        self._overall_probe_t = t_overall

        # Create the delay between the two pulses (for the MW pi pulse)
        self.waveform_probe1 += SinCombine(0, 0, 0, self.t_delay2, self._sample_rate)
        self.waveform_probe2 += SinCombine(0, 0, 0, self.t_delay2, self._sample_rate)
        self._overall_probe_t = accumulate_pulse_time(self.t_delay2, self._overall_probe_t, self._sample_rate)

        # The 2nd pulse
        wf1, wf2, t_pulses = self.segmented_pulses(self.f_list, self.a_list, self.p_list, self.t_list, self._overall_probe_t)
        self.waveform_probe1 += wf1
        self.waveform_probe2 += wf2
        self._overall_probe_t = t_overall

        if self.t_off is not None and self.t_off > 0:
            self.waveform_probe1 += ShapedSinCombine(0, 0, 0, self.t_off, self.t_shape, self._sample_rate, self.awg.AMP_SATURATION_AOM1)
            self.waveform_probe2 += ShapedSinCombine(0, 0, 0, self.t_off, self.t_shape, self._sample_rate, self.awg.AMP_SATURATION_AOM2)

    def update_time(self, t):
        # Break the given pulse length into N_segments equal pieces
        self.t_list = [t / self.N_segments for _ in range(self.N_segments)]

        self.create_waveform()
        self.update_probe()

class ShapedTwoLoopGate_PM(ShapedTwoLoopGate):
    # A sub-class of ShapedTwoLoopGate, running the Biercuk phase modulation in each loop
    def __init__(self, mode_freqs, device=None):
        self.mode_freqs = mode_freqs
        self.n_PM_seg = 2**len(self.mode_freqs) # The number of segments in the phase modulation

        self.p_pulse2 = 0 # Extra phase offset of the 2nd SDF pulse
        self.df_pulse2 = 0 # An optional offset of the SDF frequency for the 2nd pulse
        super().__init__(device)

    def update_mode_freqs(self, mode_freqs):
        self.mode_freqs = mode_freqs

    def update_phase_2nd_pulse(self, phase):
        self.p_pulse2 = phase
        self.create_waveform()
        self.update_probe()

    # Overwrite hte create_waveform method from the parent class
    def create_waveform(self):
        # Clear the existing waveforms
        self.waveform_probe1 = []
        self.waveform_probe2 = []
        # Clear the time counter for phase calculation
        self._overall_probe_t = 0

        # Create the delay before the 1st pulse (for the MW pi/2 pulse)
        self.waveform_probe1 += SinCombine(self.f_probe1, 0, 0, self.t_delay1 + self.t_off_before, self._sample_rate)
        self.waveform_probe2 += SinCombine(self.f_probe2, 0, 0, self.t_delay1 + self.t_off_before, self._sample_rate)

        # The 1st pulse
        waveform1, waveform2 = self.create_PM_pulses(self.t_probe, self.n_PM_seg, 0, 0)
        self.waveform_probe1 += waveform1
        self.waveform_probe2 += waveform2
        self._overall_probe_t = accumulate_pulse_time(self.t_probe, self._overall_probe_t, self._sample_rate)

        # Create the delay between the two pulses (for the MW pi pulse)
        self.waveform_probe1 += SinCombine(self.f_probe1, 0, 0, self.t_delay2, self._sample_rate)
        self.waveform_probe2 += SinCombine(self.f_probe2, 0, 0, self.t_delay2, self._sample_rate)
        self._overall_probe_t = accumulate_pulse_time(self.t_delay2, self._overall_probe_t, self._sample_rate)

        # The 2nd pulse
        waveform1, waveform2 = self.create_PM_pulses(self.t_probe, self.n_PM_seg,
                                                     self.f_probe1 * self._overall_probe_t,
                                                     self.f_probe2 * self._overall_probe_t + self.p_pulse2,
                                                     df_ch2=self.df_pulse2)
        self.waveform_probe1 += waveform1
        self.waveform_probe2 += waveform2
        self._overall_probe_t = accumulate_pulse_time(self.t_probe, self._overall_probe_t, self._sample_rate)

        if self.t_off is not None and self.t_off > 0:
            self.waveform_probe1 += ShapedSinCombine(self.f_probe1, 0, 0, self.t_off, self.t_shape,
                                                     self._sample_rate, self.awg.AMP_SATURATION_AOM1)
            self.waveform_probe2 += ShapedSinCombine(self.f_probe2, 0, 0, self.t_off, self.t_shape,
                                                     self._sample_rate, self.awg.AMP_SATURATION_AOM2)


    def create_PM_pulses(self, t_total, n_pulse, phi1_init, phi2_init, df_ch2=0):
        # t_total: the overall time of the pulses
        # n_pulse: the number of pulse segments
        # phi1_init, phi2_init: the initial phases of Ch1 and Ch2 at the start of first pulse
        # mode_freqs: the frequencies of the driven motional modes
        # df_ch2: a frequency offset of channel2 on top of self.f_probe2

        # Assume that f_probe2 is larger than f_probe1
        assert self.f_probe2 + df_ch2 > self.f_probe1
        f_SDF = (self.f_probe2 + df_ch2 - self.f_probe1) * 2
        detuning_list = f_SDF - np.array(self.mode_freqs)

        t_seg = t_total/n_pulse
        overall_t = 0

        waveform1 = []
        waveform2 = []
        for l in range(n_pulse):
            phi_PM = PM_Biercuk(l, detuning_list, t_seg) / 2 # Divide the phase by 2 because of the double-pass configuration we use
            # print(phi_PM)
            # phi_PM = -0.5
            waveform1 += ShapedSinCombine(self.f_probe1, self.a_probe1,
                                          phi1_init + self.f_probe1 * overall_t,
                                          t_seg, self.t_shape, self._sample_rate, self.awg.AMP_SATURATION_AOM1)
            waveform2 += ShapedSinCombine(self.f_probe2 + df_ch2, self.a_probe2,
                                          phi2_init + (self.f_probe2 + df_ch2) * overall_t + phi_PM,
                                          t_seg, self.t_shape, self._sample_rate, self.awg.AMP_SATURATION_AOM2)
            # calculate the phase on the grid of AWG sampling
            overall_t = accumulate_pulse_time(t_seg, overall_t, self._sample_rate)
            if l == 0:
                t_seg = overall_t

        return waveform1, waveform2

def PM_Biercuk(l, detuning_list, t_seg):
    # PhysRevLett.114.120502
    n_modes = len(detuning_list)
    assert l < 2**n_modes

    binary_rep = np.binary_repr(l, width=n_modes)
    Hamming_weight = np.sum([int(binary_rep[_]) for _ in range(n_modes)])

    # phi = - Hamming_weight * np.pi  #  Do we need np.pi here?
    phi = - Hamming_weight * 0.5
    for j in range(n_modes):
        phi += int(binary_rep[j]) * 2**j * detuning_list[j] * t_seg

    return -phi
    # return phi

class Ramseyseq_2_channel(ProbeSequence):
    def __init__(self, device=None):
        self.car_freq = None
        self.rsb_freq = None
        self.car_pihalf_time1 = None
        self.car_pihalf_time2 = None
        self.rsb_pi_time1 = None
        self.rsb_pi_time2 = None
        self.rsb_amp = None
        super().__init__(device)

    def create_Ramsey_waveform(self, delay):
        # Clear the existing waveforms
        self.waveform_probe1 = []
        self.waveform_probe2 = []
        # Clear the time counter for phase calculation
        self._overall_probe_t = 0

        if self.t_off_before > 0:
            self.waveform_probe1 += SinCombine(self.car_freq, 0, 0, self.t_off_before, self._sample_rate)
            self.waveform_probe2 += SinCombine(self.car_freq, 0, 0, self.t_off_before, self._sample_rate)

        self.waveform_probe1 += SinCombine(self.car_freq, self.a_probe1, 0, self.car_pihalf_time1, self._sample_rate)
        self.waveform_probe2 += SinCombine(self.car_freq, 0, 0, self.car_pihalf_time1, self._sample_rate)
        self._overall_probe_t = accumulate_pulse_time(self.car_pihalf_time1, self._overall_probe_t, self._sample_rate)

        self.waveform_probe1 += SinCombine(self.car_freq, 0, 0, delay, self._sample_rate)
        self.waveform_probe2 += SinCombine(self.car_freq, 0, 0, delay, self._sample_rate)
        self._overall_probe_t = accumulate_pulse_time(delay, self._overall_probe_t, self._sample_rate)

        self.waveform_probe1 += SinCombine(self.car_freq, 0, 0, self.car_pihalf_time2, self._sample_rate)
        self.waveform_probe2 += SinCombine(self.car_freq, self.a_probe2, self.car_freq*self._overall_probe_t, self.car_pihalf_time2, self._sample_rate)
        self._overall_probe_t = accumulate_pulse_time(self.car_pihalf_time2, self._overall_probe_t, self._sample_rate)

        if self.t_off is not None and self.t_off > 0:
            self.waveform_probe1 += SinCombine(self.car_freq, 0, 0, self.t_off, self._sample_rate)
            self.waveform_probe2 += SinCombine(self.car_freq, 0, 0, self.t_off, self._sample_rate)


    def create_motion_Ramsey_waveform_2Ch(self, delay, phase):
        # Clear the existing waveforms
        self.waveform_probe1 = []
        self.waveform_probe2 = []
        # Clear the time counter for phase calculation
        self._overall_probe_t = 0

        # idle for AOD ramping up
        if self.t_off_before > 0:
            self.waveform_probe1 += SinCombine(self.car_freq, 0, 0, self.t_off_before, self._sample_rate)
            self.waveform_probe2 += SinCombine(self.car_freq, 0, 0, self.t_off_before, self._sample_rate)

        # Beam 1 carrier pi/2 pulse
        self.waveform_probe1 += SinCombine(self.car_freq, self.a_probe1, 0, self.car_pihalf_time1, self._sample_rate)
        self.waveform_probe2 += SinCombine(self.car_freq, 0, 0, self.car_pihalf_time1, self._sample_rate)
        self._overall_probe_t = accumulate_pulse_time(self.car_pihalf_time1, self._overall_probe_t, self._sample_rate)

        # Beam 2 rsb pi pulse
        self.waveform_probe1 += SinCombine(self.rsb_freq, 0, 0, self.rsb_pi_time2, self._sample_rate)
        self.waveform_probe2 += SinCombine(self.rsb_freq, self.a_probe2, self.rsb_freq*self._overall_probe_t, self.rsb_pi_time2, self._sample_rate)
        self._overall_probe_t = accumulate_pulse_time(self.rsb_pi_time2, self._overall_probe_t, self._sample_rate)

        # delay
        self.waveform_probe1 += SinCombine(self.rsb_freq, 0, 0, delay, self._sample_rate)
        self.waveform_probe2 += SinCombine(self.rsb_freq, 0, self.rsb_freq * self._overall_probe_t, delay,
                                           self._sample_rate)
        self._overall_probe_t = accumulate_pulse_time(delay, self._overall_probe_t, self._sample_rate)

        # Beam 2 rsb pi pulse
        self.waveform_probe1 += SinCombine(self.rsb_freq, 0, 0, self.rsb_pi_time2, self._sample_rate)
        self.waveform_probe2 += SinCombine(self.rsb_freq, self.a_probe2, self.rsb_freq * self._overall_probe_t, self.rsb_pi_time2,
                                           self._sample_rate)
        self._overall_probe_t = accumulate_pulse_time(self.rsb_pi_time2, self._overall_probe_t, self._sample_rate)

        # Beam 1 carrier pi/2 pulse
        self.waveform_probe1 += SinCombine(self.car_freq, self.a_probe1, self.car_freq*self._overall_probe_t+phase, self.car_pihalf_time1, self._sample_rate)
        self.waveform_probe2 += SinCombine(self.car_freq, 0, 0, self.car_pihalf_time1, self._sample_rate)
        self._overall_probe_t = accumulate_pulse_time(self.car_pihalf_time1, self._overall_probe_t, self._sample_rate)

        # idle for AOD close
        if self.t_off is not None and self.t_off > 0:
            self.waveform_probe1 += SinCombine(self.car_freq, 0, 0, self.t_off, self._sample_rate)
            self.waveform_probe2 += SinCombine(self.car_freq, 0, 0, self.t_off, self._sample_rate)


    def create_motion_Ramsey_waveform_1Ch(self, delay, phase):
        # Clear the existing waveforms
        self.waveform_probe1 = []
        self.waveform_probe2 = []
        # Clear the time counter for phase calculation
        self._overall_probe_t = 0

        # idle for AOD ramping up
        if self.t_off_before > 0:
            self.waveform_probe1 += SinCombine(self.car_freq, 0, 0, self.t_off_before, self._sample_rate)
            self.waveform_probe2 += SinCombine(self.car_freq, 0, 0, self.t_off_before, self._sample_rate)

        # Beam 1 carrier pi/2 pulse
        self.waveform_probe1 += SinCombine(self.car_freq, self.a_probe1, 0, self.car_pihalf_time1, self._sample_rate)
        self.waveform_probe2 += SinCombine(self.car_freq, 0, 0, self.car_pihalf_time1, self._sample_rate)
        self._overall_probe_t = accumulate_pulse_time(self.car_pihalf_time1, self._overall_probe_t, self._sample_rate)

        # Beam 1 rsb pi pulse
        self.waveform_probe1 += SinCombine(self.rsb_freq, self.rsb_amp, 0, self.rsb_pi_time1, self._sample_rate)
        self.waveform_probe2 += SinCombine(self.rsb_freq, 0, self.rsb_freq * self._overall_probe_t,
                                           self.rsb_pi_time1, self._sample_rate)
        self._overall_probe_t = accumulate_pulse_time(self.rsb_pi_time1, self._overall_probe_t, self._sample_rate)

        # delay
        self.waveform_probe1 += SinCombine(self.rsb_freq, 0, 0, delay, self._sample_rate)
        self.waveform_probe2 += SinCombine(self.rsb_freq, 0, self.rsb_freq * self._overall_probe_t, delay,
                                           self._sample_rate)
        self._overall_probe_t = accumulate_pulse_time(delay, self._overall_probe_t, self._sample_rate)

        # Beam 1 rsb pi pulse
        self.waveform_probe1 += SinCombine(self.rsb_freq, self.rsb_amp, 0, self.rsb_pi_time1, self._sample_rate)
        self.waveform_probe2 += SinCombine(self.rsb_freq, 0, self.rsb_freq * self._overall_probe_t,
                                           self.rsb_pi_time1,
                                           self._sample_rate)
        self._overall_probe_t = accumulate_pulse_time(self.rsb_pi_time1, self._overall_probe_t, self._sample_rate)

        # Beam 1 carrier pi/2 pulse
        self.waveform_probe1 += SinCombine(self.car_freq, self.a_probe1, self.car_freq * self._overall_probe_t+phase,
                                           self.car_pihalf_time1, self._sample_rate)
        self.waveform_probe2 += SinCombine(self.car_freq, 0, 0, self.car_pihalf_time1, self._sample_rate)
        self._overall_probe_t = accumulate_pulse_time(self.car_pihalf_time1, self._overall_probe_t, self._sample_rate)


        # idle for AOD close
        if self.t_off is not None and self.t_off > 0:
            self.waveform_probe1 += SinCombine(self.car_freq, 0, 0, self.t_off, self._sample_rate)
            self.waveform_probe2 += SinCombine(self.car_freq, 0, 0, self.t_off, self._sample_rate)

        self.update_probe()

    def update_Ramsey_time(self, t):
        self.create_Ramsey_waveform(t)
        self.update_probe()


    def update_motion_Ramsey_time(self, t):
        self.create_motion_Ramsey_waveform(t)
        self.update_probe()




class ShapedNLoopGate(ModulatedShapedTwoLoopGate):
    def __init__(self, f_list, a_list, p_list, device=None):
        self.zz_waveform1 = []
        self.zz_waveform2 = []
        self.N_gate = None
        super().__init__(f_list, a_list, p_list, device)


    def create_zzgate_waveform(self):   #create waveform for two-loop gate

        self.zz_waveform1 = []
        self.zz_waveform2 = []
        # self._overall_probe_t = 0

        # The 1st pulse
        wf1, wf2, t_overall = self.segmented_pulses(self.f_list, self.a_list, self.p_list, self.t_list,
                                                    self._overall_probe_t)
        self.zz_waveform1 += wf1
        self.zz_waveform2 += wf2
        self._overall_probe_t = t_overall

        # Create the delay between the two pulses (for the MW pi pulse)
        self.zz_waveform1 += SinCombine(0, 0, 0, self.t_delay2, self._sample_rate)
        self.zz_waveform2 += SinCombine(0, 0, 0, self.t_delay2, self._sample_rate)
        self._overall_probe_t = accumulate_pulse_time(self.t_delay2, self._overall_probe_t, self._sample_rate)

        # The 2nd pulse
        wf1, wf2, t_overall = self.segmented_pulses(self.f_list, self.a_list, self.p_list, self.t_list,
                                                   self._overall_probe_t)

        self.zz_waveform1 += wf1
        self.zz_waveform2 += wf2
        self._overall_probe_t = t_overall


    def create_waveform(self, N):
        # Clear the existing waveforms
        self.waveform_probe1 = []
        self.waveform_probe2 = []
        # Clear the time counter for phase calculation
        self._overall_probe_t = 0

        # Create the delay before the 1st pulse (for the MW pi/2 pulse)
        self.waveform_probe1 += SinCombine(0, 0, 0, self.t_delay1 + self.t_off_before, self._sample_rate)
        self.waveform_probe2 += SinCombine(0, 0, 0, self.t_delay1 + self.t_off_before, self._sample_rate)

        for i in range(N):
            self.create_zzgate_waveform()
            self.waveform_probe1 += self.zz_waveform1
            self.waveform_probe2 += self.zz_waveform2


        if self.t_off is not None and self.t_off > 0:
            self.waveform_probe1 += ShapedSinCombine(0, 0, 0, self.t_off, self.t_shape, self._sample_rate, self.awg.AMP_SATURATION_AOM1)
            self.waveform_probe2 += ShapedSinCombine(0, 0, 0, self.t_off, self.t_shape, self._sample_rate, self.awg.AMP_SATURATION_AOM2)




    def update_time(self, t):

        assert self.N_gate is not None

        self.t_list = [t / self.N_segments for _ in range(self.N_segments)]

        self.create_waveform(self.N_gate)
        self.update_probe()


class ContinuousOutput(SequenceSpectrumAWG_2Channels):
    # A sub-class of SequenceSpectrumAWG
    def __init__(self, device=None):
        super().__init__(device)

        # Change to software trigger
        self.awg.setup_trigger(external_trigger=False)

        self.load_sequence()

    def load_sequence(self):
        # Simply loop the idle pulse endlessly
        vWriteStepEntry (self.awg.card,  self._seq_start_step,  self._seq_start_step + 1,
                         self._seg_idle,      1,  SPCSEQ_ENDLOOPALWAYS)

        self.finish_sequence(self._seq_start_step + 1)

    def set_output(self, freq1, amp1, freq2, amp2, t):
        waveform_idle1 = SinCombine(freq1, amp1, 0, t, self._sample_rate)
        waveform_idle2 = SinCombine(freq2, amp2, 0, t, self._sample_rate)
        # Write the new "idle" pulse to awg memory
        self.awg.stop_card()
        self.awg.write_segment_two_channels(waveform_idle1, waveform_idle2, self._seg_idle)
        self.awg.start_card()


if __name__ == "__main__":
    awg_aod = DeviceSpectrumAWG(b'TCPIP::192.168.1.81::inst0::INSTR', Max_Vol=90)
    awg_aom = DeviceSpectrumAWG(b'TCPIP::192.168.1.8::inst0::INSTR', Max_Vol=140)
    # awg_global = DeviceSpectrumAWG(b'TCPIP::192.168.1.39::inst0::INSTR', Max_Vol=125)

    start_time = time.time()
    continuousOut_aom = ContinuousOutput(awg_aom)
    continuousOut_aod = ContinuousOutput(awg_aod)

    print(time.time()-start_time)

    continuousOut_aom.set_output(130, 0, 130, 0, 2000)
    continuousOut_aod.set_output(145, 0, 145, 0, 2000)


    # probe = ProbeSequence(awg)
    # probe.t_probe = 100
    # probe.a_probe1 = 1
    # probe.f_probe1 = 130
    # probe.a_probe2 = 0
    # probe.f_probe2 = 130
    #
    # probe.update_waveform()

    # shaped_probe = ShapedProbeSequence(awg)
    # shaped_probe.waveform_idle1 = []
    # shaped_probe.waveform_idle2 = []
    # shaped_probe.add_pulse_to_idle(140, 0.2, 0, 140, 0.2, 0, 1)
    # shaped_probe.update_idle()
    # shaped_probe.t_shape = 2
    # shaped_probe.t_probe = 100
    # shaped_probe.a_probe1 = 1
    # shaped_probe.f_probe1 = 145
    # shaped_probe.a_probe2 = 1
    # shaped_probe.f_probe2 = 146
    #
    # shaped_probe.update_waveform()

    # sbc_probe = SbcProbeSequence(awg)
    # # Add the SBC pulse
    # sbc_probe.add_pulse_to_sbc(0.5, 0.3, 0, 0, 0, 0, 10)
    # sbc_probe.add_pulse_to_sbc(0.5, 0, 0, 0, 0, 0, 5)
    # sbc_probe.add_pulse_to_sbc(0.5, 0.3, 0, 0, 0, 0, 20)
    # sbc_probe.add_pulse_to_sbc(0.5, 0, 0, 0, 0, 0, 5)
    # sbc_probe.add_pulse_to_sbc(0.5, 0.3, 0, 0, 0, 0, 30)
    # sbc_probe.add_pulse_to_sbc(0.5, 0, 0, 0, 0, 0, 5)
    # sbc_probe.update_sbc()
    # # Add the probe pulse
    # sbc_probe.t_probe = 30
    # sbc_probe.a_probe1 = 0
    # sbc_probe.f_probe1 = 130
    # sbc_probe.a_probe2 = 1.0
    # sbc_probe.f_probe2 = 130
    #
    # sbc_probe.update_waveform()

    # shaped_pulse_AOM = ShapedTwoLoopGate(awg)
    # shaped_pulse_AOM.t_shape = 0  # 2 us rising and falling time
    # shaped_pulse_AOM.f_probe1 = 135
    # shaped_pulse_AOM.f_probe2 = 135 + 0.8
    # shaped_pulse_AOM.a_probe1 = 1.0
    # shaped_pulse_AOM.a_probe2 = 0.75
    #
    # shaped_pulse_AOM.t_delay1 = 15 + 2  # Delay the 1st SDF pulse by the MW pi/2 time, plus an extra 2 us margin
    # shaped_pulse_AOM.t_delay2 = 30 + 2 * 2  # Delay the 2nd SDF pulse by the MW pi time, plus 2 us margins before and after it
    #
    # shaped_pulse_AOM.update_time(100)

