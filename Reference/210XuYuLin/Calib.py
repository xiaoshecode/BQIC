import os
from ctypes import *
import clr
import System

# from sequencerCCDFor import *
from sequencer import *
import DDS1
# from motorctrl import *
import socket
from datetime import datetime
from pathlib import Path
from files import *
import rtplot
import numpy as np
import matplotlib.pyplot as pl
import time
import Fit
from scipy.optimize import curve_fit
from CVIONS import *
import AWG4100_DDS_mode as AWG
import spectrum_awg as SpectrumAWG
import spectrum_awg_2channel as SpectrumAWG2
import spectrum_awg_SR as SpectrumAWGSR
from E8663D import E8663D
from scipy.special import jv
import picomotor as pmotor
import simulation.TrapFreqCAL as TrapFreqCAL
import simulation.phase_modulation_robust_Xu_v2 as PMdesign

'''
note: 第二路相关的控制校准需要修改补充，motorscan。
'''



def AutoRunStopFunc():
    # print("next para calib")
    pass


def tnow():
    return datetime.now().strftime('%Y%m%d%H%M%S')


a = clr.AddReference("Newport.CONEXCC.CommandInterface")
#
from CommandInterfaceConexCC import *


# motorctrlmodule = PyDLL('E:/PyPrograms/210sequencer/Newport.CONEXCC.CommandInterface.dll')
# print(motorctrlmodule.ConexCC)
# ctrller = motorctrlmodule.ConexCC()
# success = ctrller.OpenInstrument("COM20")

class Motor():
    def __init__(self, com="COM17", velocity=1.0):  # velocity refers to maximum moving velocity
        self.driver = ConexCC()
        self.connect = self.driver.OpenInstrument(com)  # open the connection
        self.velocity = velocity
        self.homing_velocity = velocity

        if self.connect == 0:
            # print("connect successfully")
            self.setvelocity(velocity)
            self.sethomingvelocity(velocity)
            # self.velocity = self.getvelocity()
            # self.homing_velocity = self.gethomingvelocity()
            self.getstate()
            print("cur_pos is " + str(self.getpos()))
            # print("velocity is " + str(self.velocity))
            # print("controller state is " + str(self.state))

        else:
            print("connect unsuccessfully")

    def getdevices(self):
        pass

    def getstate(self):  # get the state of the controller

        '''
            – 0A: NOT REFERENCED from RESET.
            – 0B: NOT REFERENCED from HOMING.
            – 0C: NOT REFERENCED from CONFIGURATION.
            – 0D: NOT REFERENCED from DISABLE.
            – 0E: NOT REFERENCED from READY.
            – 0F: NOT REFERENCED from MOVING.
            – 10: NOT REFERENCED - NO PARAMETERS IN MEMORY.
            – 14: CONFIGURATION.
            – 1E: HOMING.
            – 28: MOVING.
            – 32: READY from HOMING.
            – 33: READY from MOVING.
            – 34: READY from DISABLE.
            – 36: READY T from READY.
            – 37: READY T from TRACKING.
            – 38: READY T from DISABLE T.
            – 3C: DISABLE from READY.
            – 3D: DISABLE from MOVING.
            – 3E: DISABLE from TRACKING.
            – 3F: DISABLE from READY T.
            – 46: TRACKING from READY T.
            – 47: TRACKING from TRACKING.
        '''
        err_str = ''
        resp = ''
        resp2 = ''
        res, resp, resp2, errString = self.driver.TS(1, resp, resp2, err_str)

        if res == 0:
            self.state = resp2
            self.positioner_err = resp
        else:
            print("get state error, error string is" + errString)

    # def getconfiguration(self): # get the configuration setting(not changed even power off) of the controller
    #     para = ''
    #     err_str = ''
    #     res, para, err_str = self.driver.ZT(1, para, err_str)

    #     if res == 0:
    #         print(para)
    #         return para
    #     else:
    #         print("error! error string is "+err_str)
    #         return err_str

    def getrevision(self):
        rev = ''
        err_str = ''
        res, rev, err_str = self.driver.VE(1, rev, err_str)
        if res == 0:
            print("revision is" + rev)
        else:
            print("error! error string is " + err_str)

    def exit_disable_state(self):
        err_str = ''
        state = 1  # enable
        res, err_str = self.driver.MM_Set(1, state, err_str)
        if res != 0 or err_str != '':
            print('Oops: Leave Disable: result=%d,errString=\'%s\'' % (res, err_str))
        else:
            print('Exiting DISABLE state')
            time.sleep(0.2)

    def is_ready(self):  # to see whether the controller is ready or not
        self.getstate()

        if self.state in ('3D', '3C'):  # in DISABLE state
            self.exit_disable_state()
            time.sleep(0.2)
            self.getstate()
        elif self.state.startswith('0'):  # not referenced state
            self.homesearch()
            time.sleep(0.1)
            self.getstate()

        # ('32','33','34') means in READY state
        ready = self.positioner_err == '' and self.state in ('32', '33', '34')
        return ready

    def close(self):  # close the connection
        self.driver.CloseInstrument()

    def reconnect(self, com="COM17"):  # reconnect to the device
        self.close()
        self.driver.OpenInstrument(com)

    def reset(self):  # reset controller
        pass

    def homesearch(self):
        self.getstate()
        if self.state[0] == '0':
            err_str = ''
            res, err_str = self.driver.OR(1, err_str)
            if res != 0 or err_str != '':
                print('Oops: Find Home: result=%d,errString=\'%s\'' % (res, err_str))
            else:
                print('Finding Home')
            while True:
                self.getstate()
                if self.state == '32':
                    print('homing done!')
                    break
                time.sleep(0.1)

        else:
            print("homing forbbiden")

    def relativemove(self, distance):  # unit-mm, move distance mm from current position
        if self.is_ready():  # only when the controller is ready,the motor can move.
            err_str = ''
            res, err_str = self.driver.PR_Set(1, distance, err_str)
            if res != 0 or err_str != '':
                print('Oops: Move Relative: result=%d,errString=\'%s\'' % (res, err_str))
            else:
                # print('Moving Relative %.4f mm' % distance)
                pass
            while True:
                self.getstate()
                if self.state == '33':
                    # print('moving done!')
                    break
                time.sleep(0.1)

    def absolutemove(self, pos):  # move to pos mm
        if self.is_ready():  # only when the controller is ready,the motor can move.
            err_str = ''
            res, err_str = self.driver.PA_Set(1, pos, err_str)
            if res != 0 or err_str != '':
                print('Oops: Move Relative: result=%d,errString=\'%s\'' % (res, err_str))
            else:
                # print('Moving to position %.4f mm' % pos)
                pass
            while True:
                self.getstate()
                if self.state == '33':
                    # print('moving done!')
                    break
                time.sleep(0.1)

    def getpos(self):  # get the current poition and return position value in unit mm
        resp = 0
        err_str = ''
        res, resp, err_str = self.driver.TP(1, resp, err_str)

        return resp

    def getvelocity(self):  # get the maximum moving velocity in unit mm/s
        resp = 0
        err_str = ''
        res, resp, err_str = self.driver.VA_Get(1, resp, err_str)
        if res == 0:
            return resp
        else:
            return err_str

    def setvelocity(self, velocity):  # set the maximum moving velocity in unit mm/s
        if velocity > 2 or velocity < 0:  # TRB-CC maximum speed is 2 mm/s
            velocity == 2
            print("the setting velocity is out of range")

        err_str = ''
        res, err_str = self.driver.VA_Set(1, velocity, err_str)

        if res == 0:
            # print('velocity Set to %.1f mm/s' % velocity)
            self.velocity = velocity
        else:
            print("velocity set error!")

    def gethomingvelocity(self):  # set the maximum homesearching velocity in unit mm/s
        resp = 0
        err_str = ''
        res, resp, err_str = self.driver.OH_Get(1, resp, err_str)
        if res == 0:
            return resp
        else:
            return err_str

    def sethomingvelocity(self, velocity):  # get the maximum homesearching velocity in unit mm/s
        if velocity > 2 or velocity < 0:  # TRB-CC maximum speed is 2 mm/s
            velocity == 2
            print("the setting homing velocity is out of range")

        err_str = ''
        res, err_str = self.driver.OH_Set(1, velocity, err_str)

        if res == 0:
            # print('homing velocity Set to %.1f mm/s' % velocity)
            self.homing_velocity = velocity
        else:
            print("homing velocity set error!")


class ConnectError(Exception):
    pass


class CaliB():

    def __init__(self, calibfile = ".\Configuration\calibration.json", sequencerConfigFile = ".\Configuration\sequencer.json"):

        self.__ccd_resolution = 0.386  #um/pixel
        self.ion_num = 0
        self.ion_pos = np.array([])
        self.ion_disp = 0
        self.ion_allcount = 0
        # self.awgwaveform = {}
        self.motor = [["COM20", "COM21"], ["", "COM19"]]
        self.motor_ctrl = None

        self.motor370_slave = 1
        self.motor370_axis = 2
        self.picomotor_all_step = 0
        self.picomotor_all = None

        self.calibfile = calibfile

        self._repeattime = 100
        self._binning = (1, 100)
        self._roi = (1,200,511,100)
        self._LoG_sigma = 1.8
        self._cvthr = 0.7
        self._detectionthr = 4000
        self._coolingthr = 4500
        self.PMT_threshold = 20
        self._d = 2
        self.LineTrigger_Flag= 0

        self.__beta = np.linspace(0.2, 2.3, 400)
        self.__Besselratio = jv(2, self.__beta)/jv(0, self.__beta)
        self.__beta0 = 1.8413

        self.T_INDIVIDUAL1_CALIB = 30
        self.T_INDIVIDUAL2_CALIB = 60
        self.T_IONCOUNT_CALIB = 60

        # The TTL pulse width for triggering Spectrum AWG
        self.T_AWG_TRIG = 1

        # Initial directions of the fast calibration for the individual addressing beam
        self.direction_x1 = 1
        self.direction_x2 = 1
        self.direction_y1 = 1
        self.direction_y2 = 1

        self._used_awg_channels = []



        # self._detuning_2q_gate = 0.01 / 2

        #constant for signal sources. dds:0,1-dds;2-awg.
        self._ch_global_411 = 2
        self._ch_3432 = 1
        # self._ch_aom_ind1 = 3
        # self._ch_aom_ind2 = 0
        self._ch_aod_ind1 = 4
        self._ch_aod_ind2 = 2
        self._ch_370 = 1
        self._ch_MW = 0
        self._ch_935 = 0
        self._ch_EITpump = 0

        self._dds_global_411 = 1
        self._dds_3432 = 1
        self._dds_aod_ind1 = 2
        self._dds_aod_ind2 = 2
        self._dds_aom_ind1 = 0
        self._dds_aom_ind2 = 0
        self._dds_370 = 0
        self._dds_MW = 0
        self._dds_935 = 1
        self._dds_MW_F = 3
        self._dds_EITpump = 1
        

        # self._amp_global_411 = 122
        self._amp_global_411 = 0.246 #max amp for dds to drive the AOM
        self.amp_sbc = 1 # use 0-p1 cooling with conversion EOM on
        self._amp_aod_ind1 = 0.5 #90
        self._amp_aod_ind2 = 0.5 #90
        self.max_volt_aod = 180
        self._amp_aom_ind1 = 0.7
        self._amp_aom_ind2 = 0.5
        self._acs_freq = 393 #406.4# 442.3318
        self._f_aom_ind1 = 130
        self._f_aom_ind2 = 130
        self._amp_MW = 0.15
        self._amp_935 = 0.4
        self._amp_3432 = 0.18
        self._amp_3432_low = 0.18
        self.amp_370 = None
        self._amp_rhode = 18 #dBm
        self._amp_EITpump = 0.0785


        self._awg_amp_aom_ind1 = 1 #0.85
        self._awg_amp_aom_ind2 = 1 #0.85

        self._tcal_global411 = 20   #unit-us
        self._t_shape_sbc = 2
        self._t_fine_cal_trap_freq = 75

        self.t_PMT_exposure = 400
        self.t_DopplerC_PMT = 2000

        self.t_aod_total = 600 # The overall time that the individual beams are turned on.
        # frequency and amplitude of the AOD when it stands by
        self.f_aod_idle = 130
        self.t_aod_idle = 1 # us, The AWG will loop the idle pulse until receiving trigger

        self.f_aom_idle = 125
        self.t_aom_idle = 1

        self._sbc_tlist = [[50], [50]]
        self._sbc_cycle = 60

        # The measured delay between the awg trigger and its ouput is within 39.9 us to 40.6 us (1 channel output)
        self._delay_spectrum_awg = 20.5
        # 0.5 us is therefore a conservative estimation of the timing uncertainty
        self._jitter_spectrum_awg = 0.5
        # The ttl length for global 411 AOM spectrum AWG
        self._delay_spectrum_global = 5

        self.load_calibration()

        self.sequencerConfigFile = sequencerConfigFile
        self.load_seqconfig()

        self.ioncsvfile, self.ionfile, self.ionfileName, folder = genFile('ion_count', start=0, stop=0)

        self.open_calibration_log()


        try:
            # connect to motor
            # self.motor[0][0] = Motor(com="COM20", velocity=2.0)
            # self.motor[0][1] = Motor(com="COM21", velocity=2.0)
            # self.motor[1][1] = Motor(com="COM22", velocity=2.0)
            # print("motor init successfully")

            # connect to the sequencer and DDS created by Guo
            self.seq = sequencer(port="COM15", dds_port="COM31") #the phase setting range is [0,1]
            print("seq init successfully")

            # connect to the new dds created by Yao
            self.ddsad = DDS1.DDS_AD9910_SiliconLab() #the phase setting range is [0,360]
            self.ddsad.open("COM9")
            self._initdds(ddschoice=1)

            self.Config_dds()

            print("dds init successfully")

            # Connect AWG 4100
            # self.awg = AWG.InitializeAwg4100()

            # Connect the Spectrum AWG
                # The two driving the global 411
            self.awg_spectrum1 = SpectrumAWGSR.DeviceSpectrumAWG(b'TCPIP::192.168.1.28::inst0::INSTR', MAX_VOLT_CH0=176, AMP_SATURATION = np.pi/2/1.5732) #use for SBC
            # print("28")
            # self.awg_spectrum2 = SpectrumAWGSR.DeviceSpectrumAWG(b'TCPIP::192.168.1.39::inst0::INSTR', MAX_VOLT_CH0=176, AMP_SATURATION = np.pi/2/1.5839) #use for probe, 411 calibration, shelving
            # self.awg_spectrum2 = SpectrumAWG2.DeviceSpectrumAWG(b'TCPIP::192.168.1.39::inst0::INSTR') #use for probe, 411 calibration, shelving
            # print("39")
                # The one driving the AOMs of beam1 and beam2
            self.awg_spectrum_aom = SpectrumAWG2.DeviceSpectrumAWG(b'TCPIP::192.168.1.8::inst0::INSTR', Max_Vol=140, AMP_SATURATION_AOM1 = np.pi/2/1.92, AMP_SATURATION_AOM2 = np.pi/2/1.84)
            # print("8")
                # The one driving the AODs of beam1 and beam2
            self.awg_spectrum_aod = SpectrumAWG2.DeviceSpectrumAWG(b'TCPIP::192.168.1.81::inst0::INSTR', Max_Vol=self.max_volt_aod)
            # print("81")


            # Connect to the E8663D
            self.PSG = E8663D('192.168.1.15', power_limit=4)

            res_ampset = self.PSG.set_level(self._CEOMamp, unit='DBM')
            if res_ampset['status']=='pass':
                print("level set successfully")
            else:
                print("WARNING: EOM LEVEL SETTING UNSUCCESSFULLY!")

            res_freqset = self.PSG.set_frequency(self._CEOMfreq, unit='GHZ')
            if res_freqset['status']=='pass':
                print("EOM freq set successfully")
            else:
                print("WARNING: EOM FREQ SETTING UNSUCCESSFULLY!")

            if res_ampset['status']=='pass' and res_freqset['status']=='pass':
                res_poweron = self.PSG.set_power('On')
                if res_poweron['status']=='pass':
                    print("EOM signal source power on")
                else:
                    print("WARNING: EOM POWER CAN NOT BE TURNNED ON!")

            self.RHODE = E8663D('192.168.1.54', power_limit=18)

            res_ampset = self.RHODE.set_level(self._amp_rhode, unit='DBM')
            if res_ampset['status'] == 'pass':
                print("level set successfully")
            else:
                print("WARNING: MW_F LEVEL SETTING UNSUCCESSFULLY!")

            res_freqset = self.set_ddsfreq(self._MWfreq_F, channel=0, profile=0, ddschoice=self._dds_MW_F)
            if res_freqset['status'] == 'pass':
                print("MW_F freq set successfully")
            else:
                print("WARNING: MW_F FREQ SETTING UNSUCCESSFULLY!")

            if res_ampset['status'] == 'pass' and res_freqset['status'] == 'pass':
                res_poweron = self.PSG.set_power('On')
                if res_poweron['status'] == 'pass':
                    print("MW_F signal source power on")
                else:
                    print("WARNING: MW_F POWER CAN NOT BE TURNNED ON!")
            # continuousOut_aom = SpectrumAWG2.ContinuousOutput(self.awg_spectrum_aom)
            # continuousOut_aod = SpectrumAWG2.ContinuousOutput(self.awg_spectrum_aod)
            #
            # continuousOut_aom.set_output(125, 1, 125, 1, 2000)
            # continuousOut_aod.set_output(130, 0.5, 130, 0.5, 2000)

            # creat a client to communicate with CCD
            self.client = socket.socket()
            self.client.connect(('192.168.1.100', 10030))
            self.client.settimeout(None)
            print("CCD standby")

        except:
            raise ConnectError("connection error--check the com port!")

        os.chdir('E:/PyPrograms/210sequencer')
        pos = self.ion_count()
        self.old_ion_pos_beam2_cal = pos
        self.old_ion_pos_beam1_cal = pos

        TFcalc = TrapFreqCAL.trapfreqcalc(self._com_freq, self.ion_pos.reshape(-1)*self.__ccd_resolution)
        V, freq = TFcalc.calc_normal_mode()
        self.mode_vector = V[:, ::-1]
        nanjudge = np.sum(np.isnan(freq))
        # print(freq)
        if len(self.ion_pos.reshape(-1)) != len(self._sb_freqlist) and nanjudge == 0:
            self._sb_freqlist = list(np.round(freq[::-1], 4))
            savecalpara("SB_freq", self._sb_freqlist, self.calibfile)


    def PMseq_gen(self, f_sdf, f_noise, ion=[0,1], tau=150, nseg=15, ramp_tau=2, dphi=0.6, regularization=5, cut=1, nbar = 0.1, sep=0, method='search',g_phase=np.pi/4,return_sign=False):

        mass = 171*1.66054e-27
        Reduced_Plank = 6.62607e-34 / 2 / np.pi
        wl = 411e-9

        mu = 2*np.pi*f_sdf
        nu = 2*np.pi*f_noise

        omega_k = 2*np.pi*np.array(self._sb_freqlist)
        eta_k = 2 * 2 * np.pi / wl * np.sqrt(Reduced_Plank / 2 / mass/ omega_k / 1e6)*np.cos(np.pi/4)

        b_ik = self.mode_vector[ion, :]
        g_ik = eta_k.reshape((1, -1)) * b_ik

        nk = np.ones(len(omega_k)) * nbar

        if dphi != 0:
            # Apply single frequency oscillation
            omega_new, g_new = PMdesign.single_frequency_oscillation(omega_k, g_ik, nu, dphi, cut)
            n_new = np.tile(nk, 2 * cut + 1)
        else:
            omega_new, g_new, n_new = omega_k, g_ik, nk

        infd, rabi, sol = PMdesign.robust_sequence(nseg, tau, mu, omega_new, g_new, n_new,
                                                   x0=method, display=False, regularization=regularization,
                                                   ramp_tau=ramp_tau, ramp='sin', sep=sep, g_phase=g_phase, return_sign=return_sign)

        if sol.success:
            x = (sol.x / 2 / np.pi) % 1
            if nseg % 2 == 0:
                seq_2pi = np.round(np.concatenate((x, -x[::-1])), 4)
            else:
                seq_2pi = np.round(np.concatenate((x, [0], -x[::-1])), 4)


            detuning_list = np.linspace(-0.0015, 0.0015, 20) * 2 * np.pi

            PMdesign.plot_robustness(nseg, tau, mu, omega_k, rabi, detuning_list, g_ik, nk,
                                     x0=seq_2pi, ramp_tau=ramp_tau, ramp='sin', sep=sep, g_phase=g_phase, return_sign=return_sign)

            self.PMseq_doublepass = list(seq_2pi/2)
            savecalpara("PMseq_DP", self.PMseq_doublepass, self.calibfile)

            return seq_2pi/2  #Consider that the phase in the double pass AOM will be doubled

        else:
            print("No appropriate phase sequence found!")
            return 0


    def open_calibration_log(self):
        data_folder = 'E:\\PyPrograms\\210sequencer\\data\\'
        time_now = datetime.now()
        folder_month = time_now.strftime("%Y%m")
        folder_day = time_now.strftime("%m%d")

        folder_today = data_folder + folder_month + "\\" + folder_day

        # Create the data folder if not already existing
        if not os.path.exists(folder_today):
            os.mkdir(folder_today)

        self.log_file_AOD1 = Path(folder_today + "\\" + "LogAOD1.txt")
        self.log_file_AOD2 = Path(folder_today + "\\" + "LogAOD2.txt")
        self.log_file_motor1v = Path(folder_today + "\\" + "LogMotor1v.txt")
        self.log_file_motor2v = Path(folder_today + "\\" + "LogMotor2v.txt")

        # Create the log file if not existing
        self.log_file_AOD1.touch(exist_ok=True)
        self.log_file_AOD2.touch(exist_ok=True)
        self.log_file_motor1v.touch(exist_ok=True)
        self.log_file_motor2v.touch(exist_ok=True)


        # f = open(self.autocal_log, "a+")
        # # f.write("test %s\n"%time_now.strftime("%H%M%S"))
        # print(self._AODfreqlist, file=f)
        # f.write('\n')
        # f.close()

    def load_calibration(self):
        self.calibpara = loadConfig(self.calibfile)
        #calibration parameter
        self.amp_370_det = self.calibpara["amp_370_detection"]
        self.amp_370_coolingdet = self.calibpara["amp_370_coolingdet"]
        self.amp_370_symcooling = self.calibpara["amp_370_symcooling"]

        self._AODfreqlist = self.calibpara["AODfreqlist"]
        self._AODfreqlist1 = self.calibpara["AODfreqlist1"]
        self._AODfreqlist2 = self.calibpara["AODfreqlist2"]
        self._f_aom_ind1 = (self._acs_freq-np.mean(self._AODfreqlist1[0]))/2
        self._f_aom_ind2 = (self._acs_freq-np.mean(self._AODfreqlist2[0]))/2
        self._acss_pi1 = self.calibpara["acsspi1"]
        self._acss_pi2 = self.calibpara["acsspi2"]

        self._MWpitimelist0 = self.calibpara["MWpitimelist0"]
        self._MWpitimelist1 = self.calibpara["MWpitimelist1"]
        self._MWpitimelist2 = self.calibpara["MWpitimelist2"]
        self._MWpihalftimelist = self.calibpara["MWpihalftimelist"]
        self._addrpitimelist = self.calibpara["pitimelist"]
        self._Freqshift = self.calibpara["FreqShift"]
        self._MWfreq = self.calibpara["MWfreq"]
        self._MWfreq_m1 = self.calibpara["MWm1"][0]
        self._MWfreq_p1 = self.calibpara["MWp1"][0]
        self._PixelAOD = self.calibpara["PixelAOD"]
        self._timeunit = {"Microwave": np.mean(self._MWpitimelist0), "Laser411i1": self._addrpitimelist[0], "Laser411i2": self._addrpitimelist[0]}
        self._pitime3432p0 = self.calibpara["3432pitime0"]
        self._pitime3432p1 = self.calibpara["3432pitime1"]
        self._pitime3432p2 = self.calibpara["3432pitime2"]
        self._pitime3432p4 = self.calibpara["3432pitime4"]
        self._pitime3432p5 = self.calibpara["3432pitime5"]
        self._freq3432p0 = self.calibpara["3432freq0"]
        self._freq3432p1 = self.calibpara["3432freq1"]
        self._freq3432p2 = self.calibpara["3432freq2"]
        self._freq3432p3 = self.calibpara["3432freq3"]
        self._motorpos = self.calibpara["motorpos"]
        self._t_SBC_repump = self.calibpara["t_SBC_repump"]
        self.t_pumping = self.calibpara["t_pumping"]
        self.t_EITcooling = self.calibpara["t_EITcooling"]
        self.t_pumping_D32 = self.calibpara["t_pumping_D32"]
        self.t_pumping_SF1 = self.calibpara["t_pumping_SF1"]
        self._amp_370_pumping = self.calibpara["370_pumping"][1]
        self._freq_370_pumping = self.calibpara["370_pumping"][0]
        self._car_411_freqs = {"411_car_m2": self.calibpara["411_car_m2"][0],
                                "411_car_m1": self.calibpara["411_car_m1"][0],
                                "411_car_0": self.calibpara["411_car_0"][0],
                                "411_car_p1": self.calibpara["411_car_p1"][0],
                                "411_car_p2": self.calibpara["411_car_p2"][0]
                               }

        self._car_411_pitimes = {"411_car_m2": self.calibpara["411_car_m2"][1],
                                "411_car_m1": self.calibpara["411_car_m1"][1],
                                "411_car_0": self.calibpara["411_car_0"][1],
                                "411_car_p1": self.calibpara["411_car_p1"][1],
                                "411_car_p2": self.calibpara["411_car_p2"][1]
                                 }


        # The amplitudes when using the Spectrum AWG
        self._car_411_amps = {"411_car_m2": self.calibpara["411_car_m2"][2],
                                "411_car_m1": self.calibpara["411_car_m1"][2],
                                "411_car_0": self.calibpara["411_car_0"][2],
                                "411_car_p1": self.calibpara["411_car_p1"][2],
                                "411_car_p2": self.calibpara["411_car_p2"][2]
                              }

        self._car_411_relative_freqs = self.calibpara["411_relative_freq"]  # unit-MHz

        self._CEOMfreq = self.calibpara["EOMconversion"][0]
        self._CEOMpitime = self.calibpara["EOMconversion"][1]
        self._CEOMamp = self.calibpara["EOMconversion"][2]
        self._CEOMfreq_car = self.calibpara["EOMconversion"][3]

        self._MWfreq_F = self.calibpara["MWfreq_F"]
        self._MWpitimelistF = self.calibpara["MWpitimelistF"]
        self._MWpitimelistF2 = self.calibpara["MWpitimelistF2"]

        self._sb_freqlist = self.calibpara["SB_freq"]
        self._com_freq  = np.max(self._sb_freqlist)

        self._rsb_freq_main = self.calibpara["RSB_freq"]
        self._sbc_freqlist = self._rsb_freq_main


        self.PMseq_doublepass = self.calibpara["PMseq_DP"]

        self.pitime_Dexcite_addres = self.calibpara["pitime_Dexcite_addres"]
        self.car_freq_addres = self.calibpara["car_freq_addres"]
        self.car_amp_addres = self.calibpara["car_amp_addres"]

    def connect_370motor(self, idProduct = '0x4000', idVendor = '0x104d'):
        '''
        This function is used to connent the picomotor

        Parameter: The two id used to establish the serial communication

        '''
        idProduct = int(idProduct, 16)
        idVendor = int(idVendor, 16)
        if self.picomotor_all is None:
            try:
                self.picomotor_all = pmotor.Controller(idProduct=idProduct, idVendor=idVendor, slaves=2)
            except:
                self.picomotor_all = None
                print("Failed to connect to the picomotor, the com port might be occupied")
        else:
            print("picomotor has been connected by this program")


    def release_370motor(self):
        '''
        This function is used to release the interface of the picomotor
        '''
        if self.picomotor_all is not None:
            self.picomotor_all.close()
            self.picomotor_all = None
        else:
            print("picomotor was not connected!")
        

    def Config_dds(self):
        self.set_ddsfreq(self._MWfreq, channel=self._ch_MW, profile=0, ddschoice=self._dds_MW)
        self.set_ddsfreq(self._MWfreq, channel=self._ch_MW, profile=1, ddschoice=self._dds_MW)
        self.set_ddsfreq(self._MWfreq, channel=self._ch_MW, profile=2, ddschoice=self._dds_MW)
        self.set_ddsfreq(self._freq3432p0, channel=self._ch_3432, profile=0, ddschoice=self._dds_3432)
        self.set_ddsfreq(self._freq3432p1, channel=self._ch_3432, profile=2, ddschoice=self._dds_3432)
        self.set_ddsfreq(self._freq3432p2, channel=self._ch_3432, profile=3, ddschoice=self._dds_3432)
        self.set_ddsfreq(self._freq3432p0, channel=self._ch_3432, profile=4, ddschoice=self._dds_3432)
        self.set_ddsfreq(self._car_411_freqs["411_car_0"], channel=self._ch_global_411, profile=4, ddschoice=self._dds_global_411)
        self.set_ddsfreq(self._car_411_freqs["411_car_m1"], channel=self._ch_global_411, profile=5, ddschoice=self._dds_global_411)
        self.set_ddsfreq(self._car_411_freqs["411_car_p1"], channel=self._ch_global_411, profile=6, ddschoice=self._dds_global_411)
        self.set_ddsfreq(self._freq_370_pumping, channel=self._ch_370, profile=2, ddschoice=self._dds_370)
        
        self.set_ddsamp(self._amp_3432, channel=self._ch_3432, profile=0, ddschoice=self._dds_3432)
        self.set_ddsamp(self._amp_3432, channel=self._ch_3432, profile=2, ddschoice=self._dds_3432)
        self.set_ddsamp(self._amp_3432, channel=self._ch_3432, profile=3, ddschoice=self._dds_3432)
        # self.set_ddsamp(self._amp_3432_low, channel=self._ch_3432, profile=4, ddschoice=self._dds_3432)
        self.set_ddsamp(self._amp_3432, channel=self._ch_3432, profile=4, ddschoice=self._dds_3432)
        self.set_ddsamp(self._car_411_amps["411_car_0"], channel=self._ch_global_411, profile=4, ddschoice=self._dds_global_411)
        self.set_ddsamp(self._car_411_amps["411_car_m1"], channel=self._ch_global_411, profile=5, ddschoice=self._dds_global_411)
        self.set_ddsamp(self._car_411_amps["411_car_p1"], channel=self._ch_global_411, profile=6, ddschoice=self._dds_global_411)
        self.set_ddsamp(self._amp_MW, channel=self._ch_MW, profile=0, ddschoice=self._dds_MW)
        self.set_ddsamp(self._amp_MW, channel=self._ch_MW, profile=1, ddschoice=self._dds_MW)
        self.set_ddsamp(self._amp_MW, channel=self._ch_MW, profile=2, ddschoice=self._dds_MW)
        self.set_ddsamp(self._amp_370_pumping, channel=self._ch_370, profile=2, ddschoice=self._dds_370)
        self.set_ddsamp(self.amp_370_symcooling, channel=self._ch_370, profile=3, ddschoice=self._dds_370)
        self.set_ddsamp(self._amp_EITpump, channel=self._ch_EITpump, profile=7, ddschoice=self._dds_EITpump)
       

    def DDS_restart(self):
        self.seq.DDS_reconnet()
        self.ddsad.close()
        self.ddsad.open("COM9")

        self._initdds(ddschoice=1)

        self.Config_dds()
        
        print("Restart all DDS")



    def load_seqconfig(self):
        seqconfig = loadConfig(self.sequencerConfigFile)
        self.spellComb = seqconfig["spellCombo"]

    def periodic_cal(self, tcal1=5, tcal2=5, fast_mode=True):
        current_time = time.time()
        verbose = True
        old_threshold = self._detectionthr
        old_scanvalue = self.seq.scanValue
        old_repeattime = self._repeattime
        old_t_aod = self.t_aod_total
        old_linetrigger = self.get_linetrigger()
        old_370_amp = self.amp_370

        repeat_cal = 100

        if old_linetrigger:
            # Turn off line triggering if it was on
            self.change_linetrigger()


        parameter_changed = False

        low_limit = 0.6
        target = 0.8

        beam2_good = False
        beam1_good = False

        motor_half_range_init = 0.01
        motor_half_range_max = 0.03

        if current_time - self.t_ion_count > self.T_IONCOUNT_CALIB:
            self.ion_count()

        if current_time - self._AODfreqlist2[1] > self.T_INDIVIDUAL2_CALIB:
            ion_pos = self.ion_count()
            ion_disp = np.mean(ion_pos - self.old_ion_pos_beam2_cal)
            self.set_threshold(detectionthr=4000, coolingthr=4500)
            self.set_370_amp_det()
            self.set_repeattime(repeat_cal)
            self.t_aod_total = tcal2 +50
            parameter_changed = True

            if verbose:
                print("-----AOD2 freq-----")
                print(current_time - self._AODfreqlist2[1])
                print('ion displacement', ion_disp)

            if fast_mode:
                if ion_disp > 0:
                    direction_x2 = -1
                elif ion_disp == 0:
                    direction_x2 = self.direction_x2
                else:
                    direction_x2 = 1
                state0, pos_x, self.direction_x2, pos_init = self.aod_fast_cal(tcal=tcal2, diff_threshold=0.03, step_size=0.03,
                                                                               ion=[0], route=1, target=target, low_limit=0.3,
                                                                               init_direction=direction_x2, verbose=verbose)
                if state0 >= target:
                    beam2_good = True
                    self._motorpos[1][1] = (self._motorpos[1][1][0], self._AODfreqlist2[1])
                    savecalpara("motorpos", self._motorpos, self.calibfile)

            else:
                pos_init = self._AODfreqlist2[0]
                freqscanrange = np.arange(pos_init[0] - 0.2, pos_init[0] + 0.2, 0.03)
                state0, freqlist_new, calib_success = self.aodfreq_fitc(freqscanrange, route=1, tcal=tcal2,
                                                                     shelvingdet=0, ion=[0])

                pos_x = freqlist_new


            f = open(self.log_file_AOD2, "a+")
            print(pos_init, file=f)
            print(pos_x, file=f)
            print(state0, file=f)
            f.close()
            self.old_ion_pos_beam2_cal = ion_pos

        if current_time - self._motorpos[1][1][1] > self.T_INDIVIDUAL2_CALIB and not beam2_good:
            self.set_threshold(detectionthr=4000, coolingthr=4500)
            self.set_370_amp_det()
            self.set_repeattime(repeat_cal)
            self.t_aod_total = tcal2 + 50
            parameter_changed = True

            if verbose:
                print("-----AOD2 vertical motor-----")
                print(current_time - self._motorpos[1][1][1])
            # state1, pos_y, self.direction_y2 = self.motorscan_fast_cal(tcal=tcal2, diff_threshold=0.05, step_size=0.0005,
            #                                                      t_delay=0, ion=[0],
            #                                                      direction=1, route=1, target=target, low_limit=0.3,
            #                                                      init_direction=self.direction_y2, verbose=verbose)
            #
            # if state1 < low_limit:
            #     # Run the full-range calibration
            #     self.motor_getopt_fitc(tcal2, tolerance=0.17, half_range=0.004, direction=1, route=1, ion=[0])

            if fast_mode:
                half_range = motor_half_range_init
                while half_range <= motor_half_range_max:
                    t_start = time.time()
                    pos, calib_success, state, old_pos = self.motor_getopt_fitc(tcal2, target=target, low_limit=0.2,
                                                                                tolerance=0.17, half_range=half_range,
                                                                                direction=1, route=1, ion=[0], step_size=0.002, fast_mode=fast_mode)
                    t_end = time.time()
                    print("Calibration took ", t_end - t_start)
                    print("final state is ", state)
                    if calib_success:
                        break
                    half_range = 1.6 * half_range
            else:
                pos, calib_success, state, old_pos = self.motor_getopt_fitc(tcal2, target=target, low_limit=0.2,
                                                                            tolerance=0.17, half_range=0.015,
                                                                            direction=1, route=1, ion=[0],
                                                                            step_size=0.002, fast_mode=fast_mode)

            f = open(self.log_file_motor2v, "a+")
            print(old_pos, file=f)
            print(pos[1][1], file=f)
            print(state, file=f)
            f.close()

            # # After changing the vertical position, we must re-calibrate the horizontal AOD frequency
            # if verbose:
            #     print("-----AOD2 freq-----")
            #     print(current_time - self._AODfreqlist2[1])
            # state0, pos_x, self.direction_x2, pos_init = self.aod_fast_cal(tcal=tcal2, diff_threshold=0.05, step_size=0.03,
            #                                                                ion=[0], route=1, target=target, low_limit=0.3,
            #                                                                init_direction=self.direction_x2, verbose=verbose)
            # if state0 >= target:
            #     beam2_good = True
            #     self._motorpos[1][1] = (self._motorpos[1][1][0], self._AODfreqlist2[1])
            #     savecalpara("motorpos", self._motorpos, self.calibfile)
            #
            # f = open(self.log_file_AOD2, "a+")
            # print(pos_init, file=f)
            # print(pos_x, file=f)
            # f.close()

        if current_time - self._AODfreqlist1[1] > self.T_INDIVIDUAL1_CALIB:
            ion_pos = self.ion_count()
            ion_disp = np.mean(ion_pos - self.old_ion_pos_beam1_cal)
            self.set_threshold(detectionthr=4000, coolingthr=4500)
            self.set_370_amp_det()
            self.set_repeattime(repeat_cal)
            self.t_aod_total = tcal1 +50
            parameter_changed = True
            if verbose:
                print("-----AOD1 freq-----")
                print(current_time - self._AODfreqlist1[1])
                print('ion displacement', ion_disp)

            if fast_mode:
                if ion_disp > 0:
                    direction_x1 = -1
                elif ion_disp == 0:
                    direction_x1 = self.direction_x1
                else:
                    direction_x1 = 1
                state0, pos_x, self.direction_x1, pos_init = self.aod_fast_cal(tcal=tcal1, diff_threshold=0.03, step_size=0.03,
                                                                               ion=[0], route=0, target=target, low_limit=0.3,
                                                                               init_direction=direction_x1, verbose=verbose)
                if state0 >= target:
                    beam1_good = True
                    self._motorpos[0][1] = (self._motorpos[0][1][0], self._AODfreqlist1[1])
                    savecalpara("motorpos", self._motorpos, self.calibfile)
            else:
                pos_init = self._AODfreqlist1[0]
                freqscanrange = np.arange(pos_init[0]-0.2, pos_init[0]+0.2, 0.03)
                state0, freqlist_new, calib_success = self.aodfreq_fitc(freqscanrange,
                                                                     route=0,
                                                                     tcal=tcal1,
                                                                     shelvingdet=0, ion=[0])

                pos_x = freqlist_new



            f = open(self.log_file_AOD1, "a+")
            print(pos_init, file=f)
            print(pos_x, file=f)
            print(state0, file=f)
            f.close()
            self.old_ion_pos_beam1_cal = ion_pos

        # self._AODfreqlist = self._AODfreqlist2
        # if current_time - self._motorpos[0][0][1] > self.T_INDIVIDUAL1_CALIB:
        #     self.set_threshold(detectionthr=4000, coolingthr=4500)
        #     self.set_370_amp_det()
        #     self.set_repeattime(50)
        #     self.t_aod_total = tcal1 + 50
        #     parameter_changed = True
        #     if verbose:
        #         print("-----AOD1 horizontal motor-----")
        #         print(current_time - self._motorpos[0][0][1])
        #     # state0, pos_x, self.direction_x1 = self.motorscan_fast_cal(tcal=tcal1, diff_threshold=0.05, step_size=0.0003,
        #     #                                                      t_delay=0, ion=[0],
        #     #                                                      direction=0, route=0, target=target, low_limit=low_limit,
        #     #                                                      init_direction=self.direction_x1, verbose=verbose)
        #     # if state0 < low_limit:
        #     #     # Run the full-range calibration
        #     #     self.motor_getopt_fitc(tcal1, tolerance=0.17, half_range=0.004, direction=0, route=0, ion=[0])
        #     # if state0 >= target:
        #     #     beam1_good = True
        #     half_range = motor_half_range_init
        #     while half_range <= motor_half_range_max:
        #         t_start = time.time()
        #         pos, calib_success, state, old_pos = self.motor_getopt_fitc(tcal1, target=target, low_limit=0.2, tolerance=0.17, half_range=half_range, direction=0, route=0, ion=[0])
        #         t_end = time.time()
        #         print("Calibration took ", t_end - t_start)
        #         print("final state is ", state)
        #         if calib_success:
        #             break
        #         half_range = 2 * half_range
        #
        #     if state >= target:
        #         beam1_good = True
        #         self._motorpos[0][1] = (self._motorpos[0][1][0], self._motorpos[0][0][1])
        #         savecalpara("motorpos", self._motorpos, self.calibfile)

        if current_time - self._motorpos[0][1][1] > self.T_INDIVIDUAL1_CALIB and not beam1_good:
            self.set_threshold(detectionthr=4000, coolingthr=4500)
            self.set_370_amp_det()
            self.set_repeattime(repeat_cal)
            self.t_aod_total = tcal1 + 50
            parameter_changed = True
            if verbose:
                print("-----AOD1 vertical motor-----")
                print(current_time - self._motorpos[0][1][1])
            # state1, pos_y, self.direction_y1 = self.motorscan_fast_cal(tcal=tcal1, diff_threshold=0.05, step_size=0.0003,
            #                                                      t_delay=0, ion=[0],
            #                                                      direction=1, route=0, target=target, low_limit=low_limit,
            #                                                      init_direction=self.direction_y1, verbose=verbose)
            # if state1 < low_limit:
            #     self.motor_getopt_fitc(tcal1, tolerance=0.17, half_range=0.004, direction=1, route=0, ion=[0])
            if fast_mode:
                half_range = motor_half_range_init
                while half_range <= motor_half_range_max:
                    t_start = time.time()
                    pos, calib_success, state, old_pos = self.motor_getopt_fitc(tcal1, target=target, low_limit=0.2,
                                                                                tolerance=0.17, half_range=half_range,
                                                                                direction=1, route=0, ion=[0], step_size=0.002)
                    t_end = time.time()
                    print("Calibration took ", t_end - t_start)
                    print("final state is ", state)
                    if calib_success:
                        break
                    half_range = 1.6 * half_range

            else:
                pos, calib_success, state, old_pos = self.motor_getopt_fitc(tcal1, target=target, low_limit=0.2,
                                                                            tolerance=0.17, half_range=0.015,
                                                                            direction=1, route=0, ion=[0],
                                                                            step_size=0.002, fast_mode=fast_mode)


            f = open(self.log_file_motor1v, "a+")
            print(old_pos, file=f)
            print(pos[0][1], file=f)
            print(state, file=f)
            f.close()

        # Restore the parameters before entering this calibration routine
        if parameter_changed:
            self.seq.scanValue = old_scanvalue
            self.set_threshold(detectionthr=old_threshold, coolingthr=4500)
            self.set_repeattime(old_repeattime)
            self.t_aod_total = old_t_aod
            self.set_370_amp_det(old_370_amp)

        if old_linetrigger:
            # Restore the line triggering
            self.change_linetrigger()

    def detect_countall_mean(self):
        image = self._runseq(Seq=self.spellComb["CCD3432976repump"])
            
        image = image.sum(axis=1)
        count = np.zeros((self.ion_num, 1))

        for i in range(self.ion_num):
            allcount = get_allcount_1d(image, self.ion_pos, d=self._d, ion_no=i)
            count[i,0] = np.mean(allcount)

        return np.mean(count)

    def motor370_autocal(self, stepsize=200, stepback_size=-600):
        if self.picomotor_all is None:
            print("Warning: Please try to use the method connect_370motor to connect the picomotor first!")
        else:
            old_repeattime = self._repeattime
            self.set_repeattime(60)
            ion_allcount_list = []
            step_list = [stepback_size] + [stepsize]*6
            for step in step_list:
                self.picomotor_all.move(self.motor370_slave, self.motor370_axis, step)
                ion_allcount_list.append(self.detect_countall_mean())
                self.picomotor_all_step += step

            

            step_list = np.array(step_list)
            ion_allcount_list = np.array(ion_allcount_list)

            pos = np.cumsum(step_list)
            diff_ion_count = np.diff(ion_allcount_list)
            print(pos)
            print(ion_allcount_list)

            NEdge_count_diff = np.abs(np.min(diff_ion_count))
            PEdge_count_diff = np.abs(np.max(diff_ion_count))
            NEdge_count_pos = np.argmin(diff_ion_count)
            PEdge_count_pos = np.argmax(diff_ion_count)

            Edge_steep = np.argmax([NEdge_count_diff, PEdge_count_diff])
            if Edge_steep == 0:
                print(NEdge_count_diff)
                self.picomotor_all.move(self.motor370_slave, self.motor370_axis, -3*stepsize+pos[NEdge_count_pos+1]-700)
                self.picomotor_all_step = self.picomotor_all_step - 3*stepsize + pos[NEdge_count_pos+1] - 700
                
            else:
                print(PEdge_count_diff)
                self.picomotor_all.move(self.motor370_slave, self.motor370_axis, -3*stepsize+pos[PEdge_count_pos]+700)
                self.picomotor_all_step = self.picomotor_all_step - 3*stepsize + pos[PEdge_count_pos] + 700

            
            print(self.picomotor_all_step)
            pos_now = self.picomotor_all.getPos(slave=1, axis=2)


            self.set_repeattime(old_repeattime)

            return self.picomotor_all_step, pos_now
            
            
            


    def ctrl_ccd_kinetics_on(self, repeats=100, binning=(1, 1), roi=(128, 128, 256, 256)):
        # print('cmd :MEASure:KINEtics:NUM %d' % repeats)
        self.client.send(b':MEASure:KINEtics:NUM %d\n' % repeats)
        self.client.recv(1024).decode('utf-8').replace('\n', '')
        # t0 = time.time()

        while True:
            self.client.send(b':MEASure:KINEtics:NUM %d\n' % repeats)
            self.client.recv(1024).decode('utf-8').replace('\n', '')
            self.client.send(b':MEASure:KINEtics:NUM?\n')
            recv = self.client.recv(1024).decode('utf-8').replace('\n', '')
            if int(float(recv)) == repeats:
                # print('recv :MEASure:KINEtics:NUM %d' % repeats)
                break
        # print("time for setting CCD repeattime:%.2f"%(time.time()-t0)) #processing time <= 0.07s

        # print('cmd :SOURce:READ:IMAge:BINning %d,%d\n' % binning)
        # print('cmd :SOURce:READ:IMAge:ROI %d,%d,%d,%d\n' % roi)
        # t0 = time.time()

        self.client.send(b':SOURce:READ:IMAge:BINning %d,%d\n' % binning)
        self.client.recv(1024).decode('utf-8').replace('\n', '')
        while True:
            self.client.send(b':SOURce:READ:IMAge:BINning %d,%d\n' % binning)
            self.client.recv(1024).decode('utf-8').replace('\n', '')
            self.client.send(b':SOURce:READ:IMAge:BINning?\n')
            recv = self.client.recv(1024).decode('utf-8').replace('\n', '')
            # print(recv)
            if recv == str(list(binning)):
                # print('recv :SOURce:READ:IMAge:BINning %d,%d' % binning)
                break
        # print("time for setting CCD binning:%.2f"%(time.time()-t0))  #processing time = 0.00s

        # t0 = time.time()

        self.client.send(b':SOURce:READ:IMAge:ROI %d,%d,%d,%d\n' % roi)
        self.client.recv(1024).decode('utf-8').replace('\n', '')
        while True:
            self.client.send(b':SOURce:READ:IMAge:ROI %d,%d,%d,%d\n' % roi)
            self.client.recv(1024).decode('utf-8').replace('\n', '')
            self.client.send(b':SOURce:READ:IMAge:ROI?\n')
            recv = self.client.recv(1024).decode('utf-8').replace('\n', '')
            if recv == str(list(roi)):
                # print('recv :SOURce:READ:IMAge:ROI %d,%d,%d,%d' % roi)
                break
        # print("time for setting CCD roi:%.2f"%(time.time()-t0)) #processing time = 0.00s

        # print('cmd :MEASure:KINEtics:RUN ON')
        self.client.send(b':MEASure:KINEtics:RUN ON\n')
        self.client.recv(1024).decode('utf-8').replace('\n', '')

        # t0 = time.time()

        while True:
            self.client.send(b':MEASure:KINEtics:RUN ON\n')
            self.client.recv(1024).decode('utf-8').replace('\n', '')
            self.client.send(b':MEASure:KINEtics:RUN?\n')
            # print(self.client.recv(1024).decode('utf-8').replace('\n', ''))
            if self.client.recv(1024).decode('utf-8').replace('\n', '') == 'ON':

                # print('recv :MEASure:KINEtics:RUN ON')
                break
        # print("time for starting CCD:%.2f"%(time.time()-t0))  #processing time ~ 0.15s

        # t0 = time.time()

        while True:
            self.client.send(b':MEASure:KINEtics:READy?\n')
            if self.client.recv(1024).decode('utf-8').replace('\n', '') == '1':
                # print('recv :MEASure:KINEtics:READy 1')
                break
        # print("time for getting CCD status:%.2f"%(time.time()-t0))   # processing time ~ 0.1s

    def ctrl_ccd_singleloop_on(self, binning=(1, 1), roi=(128, 128, 256, 256)):
        self.client.send(b':SOURce:READ:IMAge:BINning %d,%d\n' % binning)
        self.client.recv(1024).decode('utf-8').removesuffix('\n')
        while True:
            self.client.send(b':SOURce:READ:IMAge:BINning %d,%d\n' % binning)
            self.client.recv(1024).decode('utf-8').removesuffix('\n')
            self.client.send(b':SOURce:READ:IMAge:BINning?\n')
            recv = self.client.recv(1024).decode('utf-8').replace('\n', '')
            if recv == str(list(binning)):
                print('recv :SOURce:READ:IMAge:BINning %d,%d' % binning)
                break

        self.client.send(b':SOURce:READ:IMAge:ROI %d,%d,%d,%d\n' % roi)
        self.client.recv(1024).decode('utf-8').removesuffix('\n')
        while True:
            self.client.send(b':SOURce:READ:IMAge:ROI %d,%d,%d,%d\n' % roi)
            self.client.recv(1024).decode('utf-8').removesuffix('\n')
            self.client.send(b':SOURce:READ:IMAge:ROI?\n')
            recv = self.client.recv(1024).decode('utf-8').replace('\n', '')
            if recv == str(list(roi)):
                print('recv :SOURce:READ:IMAge:ROI %d,%d,%d,%d' % roi)
                break

        print('cmd :STATus:LOOP:SINGlescan ON')

        self.client.send(b':STATus:LOOP:SINGlescan ON\n')
        self.client.recv(1024).decode('utf-8').removesuffix('\n')

        while True:
            self.client.send(b':STATus:LOOP:SINGlescan?\n')
            if self.client.recv(1024).decode('utf-8').removesuffix('\n') == 'ON':
                print('recv :STATus:LOOP:SINGlescan ON')
                break
            time.sleep(0.05)

        self.client.send(b':SOURce:IMAGe:SINGlescan:WIDTH?\n')
        width = int(self.client.recv(1024).decode('utf-8').removesuffix('\n'))
        self.client.send(b':SOURce:IMAGe:SINGlescan:HEIGHT?\n')
        height = int(self.client.recv(1024).decode('utf-8').removesuffix('\n'))

        time.sleep(1)

        return width, height


    def ctrl_ccd_singleloop_off(self):
        self.client.send(b':STATus:LOOP:SINGlescan OFF\n')
        self.client.recv(1024).decode('utf-8').removesuffix('\n')

        while True:
            self.client.send(b':STATus:LOOP:SINGlescan?\n')
            if self.client.recv(1024).decode('utf-8').removesuffix('\n') == 'OFF':
                print('recv :STATus:LOOP:SINGlescan OFF')
                break


    def get_ccd_singleloop_image(self, width, height, CVIONS=False, LoG_sigma=1.5, threshold=0.3):
        self.client.send(b':SOURce:IMAGe:SINGlescan:DATA?\n')
        recv = ''
        while True:
            # print("Videoing")
            recv += self.client.recv(100000).decode('utf-8')
            if recv.endswith('\n'):
                break
            time.sleep(0.01)
        image = np.array([int(i) for i in recv.removesuffix('\n').split(',')]).reshape(height, width)
        # print(image.shape)
        # print(np.max(image), np.min(image))
        if CVIONS:
            try:
                # print("CVION")
                para_cv = CVIONS_FAST(image[:, :], LoG_sigma=LoG_sigma, threshold=threshold)

                ion_pos = list(para_cv[:, 1].reshape(-1))
                ion_num = len(ion_pos)
                # print(ion_num)

                assert ion_num > 0

                # str_label = "Num:"+str(ion_num)

                return image, ion_pos #str_label

            except:

                return image, []
        else:

            return image


    def save_ccd_kinetics_data(self, fname='Detection', filetime=tnow(), scanvalue="1"):
        image = self.get_ccd_kinetics_data()

        year_month = time.strftime("%Y%m")
        date_now = time.strftime("%m%d")
        time_now = time.strftime("%H%M")
        folder = 'CCDData\\' + year_month + "\\" + date_now + "\\"
        if not os.path.exists(folder):
            os.makedirs(folder)

        # np.save(folder + "%s_%s.npy" % (fname, aligntime), image)
        np.save(folder + "%s_%s.npy" % (fname, scanvalue), image)
        time.sleep(0.1)

        return image


    def get_ccd_kinetics_data(self):
        # t0 = time.time()
        while True:
            self.client.send(b':MEASure:KINEtics:RUN?\n')
            if self.client.recv(1024).decode('utf-8').replace('\n', '') == 'OFF':
                break

            time.sleep(0.1)
        # print()

        self.client.send(b':SOURce:IMAGe:KINEtics:NUM?\n')
        num = int(self.client.recv(1024).decode('utf-8').replace('\n', ''))
        # print('recv :SOURce:IMAGe:KINEtics:NUM %d' % num)

        self.client.send(b':SOURce:IMAGe:KINEtics:WIDTH?\n')
        width = int(self.client.recv(1024).decode('utf-8').replace('\n', ''))
        # print('recv :SOURce:IMAGe:KINEtics:WIDTH %d' % width)

        self.client.send(b':SOURce:IMAGe:KINEtics:HEIGHT?\n')
        height = int(self.client.recv(1024).decode('utf-8').replace('\n', ''))
        # print('recv :SOURce:IMAGe:KINEtics:HEIGHT %d' % height)

        self.client.send(b':SOURce:IMAGe:KINEtics:DATA?\n')
        recv = ''

        while True:
            recv += self.client.recv(1000000).decode('utf-8')
            if recv.endswith('\n'):
                break

            time.sleep(0.01)

        image = np.array([int(i) for i in recv.replace('\n', '').split(',')]).reshape(num, height, width)

        return image


    def plot_image(image, ROI, CVIONS_TRIGGER=False):
        plt.clf()
        plt.imshow(image, cmap='gray')
        plt.title('%d' % np.max(image))
        plt.tight_layout()
        plt.axis('off')

        if CVIONS_TRIGGER:
            try:
                para_cv = CVIONS_FAST(image[:, ROI[0]:(ROI[0] + ROI[2])], LoG_sigma=1.3, threshold=0.4)
                axes = plt.gca()
                for i in range(para_cv.shape[0]):
                    circle = plt.Circle((ROI[0] + para_cv[i, 1], para_cv[i, 2]), np.sqrt(para_cv[i, 3] / np.pi),
                                        color='r',
                                        fill=False)
                    axes.add_artist(circle)
                plt.title('%d ions, len %d pxs' % (para_cv.shape[0], round(para_cv[-1, 1] - para_cv[0, 1])))
                plt.xlabel('ion pos='+str(list(para_cv[:, 1].reshape(-1))))

            except:
                pass

        plt.ion()
        plt.pause(0.05)
        plt.ioff()


    def _initdds(self, ddschoice=0):
        if ddschoice == 0:
            ddsconfig = loadConfig(".\Configuration\dds.json")
            pass

        elif ddschoice == 1:
            ddsconfig = loadConfig(".\Configuration\ddsad.json")
            for i in range(len(ddsconfig)):
                profiles = ddsconfig["channel" + str(i)]
                profilelist = list(profiles.keys())
                for j in range(len(profiles)):
                    amplitude = profiles[profilelist[j]]["amplitude"]
                    phase = profiles[profilelist[j]]["phase"]
                    frequency = profiles[profilelist[j]]["frequency"]
                    output = profiles[profilelist[j]]["output"]

                    self.ddsad.setAll(i, output, frequency, amplitude, phase, int(profilelist[j]))

        else:
            pass


    def set_ddsfreq(self, freq, channel=0, profile=0, ddschoice=0):
        if ddschoice == 0:
            self.seq.dds.setFrequency(channel=channel, profile=profile, frequency=freq)
        elif ddschoice == 1:
            self.ddsad.setFrequency(channel, freq, profile)
        elif ddschoice == 2:
            AWG.SetFreq(self.awg, channel, freq)
        elif ddschoice == 3:
            res = self.RHODE.set_frequency(freq, unit='MHZ')
            return res



    def set_ddsphase(self, phase, channel=0, profile=0, ddschoice=0):
        if ddschoice == 0:
            self.seq.dds.setPhase(channel=channel, profile=profile, phase=phase)
        elif ddschoice ==1:
            self.ddsad.setPhase(channel, phase, profile)
        else:
            pass


    def set_ddsamp(self, amp, channel=0, profile=0, ddschoice=0):
        if ddschoice == 0:
            self.seq.dds.setAmplitude(channel=channel, profile=profile, amp=amp)

        elif ddschoice == 1:
            self.ddsad.setAmplitude(channel, amp, profile)

        else:
            pass


    def set_ccdreadmode(self, binning=(1, 256), roi=(128, 128, 256, 256)):
        self._roi = roi
        self._binning = binning
        print("roi={0}, binning={1}".format(self._roi, self._binning))


    def set_repeattime(self, repeattime=100):
        self._repeattime = repeattime
        print("repeattime={}".format(self._repeattime))


    def set_cvionpara(self, LoG_sigma, thr):
        self._LoG_sigma = LoG_sigma
        self._cvthr = thr
        print("cvthreshold={0}, log_sigma={1}".format(self._cvthr, self._LoG_sigma))


    def set_threshold(self, detectionthr, coolingthr):
        self._detectionthr = detectionthr
        self._coolingthr = coolingthr
        print("threshold for detection={0}, threshold for S&D={1}".format(self._detectionthr, self._coolingthr))


    def change_linetrigger(self):
        self.seq.seq.write(b"c")
        print("change the line trigger mode")
        self.LineTrigger_Flag ^= 1

    def get_linetrigger(self):
        return self.LineTrigger_Flag



    def _runseq(self, Seq=[]):
        self.seq.loadSeq(Seq)
        self.ctrl_ccd_kinetics_on(repeats=self._repeattime, binning=self._binning, roi=self._roi)
        
        self.seq.startSeq(repeatTimes=self._repeattime)
       
        # self.seq.setIdle()
        # t0 = time.time()
        image = self.get_ccd_kinetics_data()
        # print("time for collecting CCD data:%.2f"%(time.time()-t0))  # mainly depends on the length of sequence, the time for data transferring is about 0.x s.

        return image



    def _runseq_postsel(self, Seq=[]):
        self.seq.loadSeq(Seq)
        self.ctrl_ccd_kinetics_on(repeats=self._repeattime*2, binning=self._binning, roi=self._roi)
        self.seq.startSeq(repeatTimes=self._repeattime)
        # self.seq.setIdle()
        image = self.get_ccd_kinetics_data()

        return image



    def _runseq_multi_det_inseq(self, Seq=[], det_time=1):
        self.seq.loadSeq(Seq)

        # t0 = time.time()
        self.ctrl_ccd_kinetics_on(repeats=self._repeattime * det_time, binning=self._binning, roi=self._roi)
        # print(time.time()-t0)
        self.seq.startSeq(repeatTimes=self._repeattime)

        image = self.get_ccd_kinetics_data()
        

        return image



    def runseq_video_multidet(self, Seq=[], filename='', CVIONS=False, LoG_sigma=1.5, threshold=0.3, postsel_criteria=None, folder_copy_name=None):
        self.seq.loadSeq(Seq)
        det_time = self.seq.DetTime
        assert det_time > 1
        # assert np.max(self.seq.runTime_all_InDet) > 2e7
        assert np.max(self.seq.runTime_all_InDet) >= 1e6

        # assert self._repeattime < 6
        # assert det_time > 1 and det_time < 3
        longtime_ind = np.argmax(np.array(self.seq.runTime_all_InDet))
        longtime = np.max(np.array(self.seq.runTime_all_InDet))
        assert longtime_ind==0

        year_month = time.strftime("%Y%m")
        date_now = time.strftime("%m%d")
        time_now = time.strftime("%H-%M-%S")
        folder = 'E:\\PyPrograms\\210sequencer\\data\\' + "%s\\" % year_month + "%s\\" % date_now + time_now + '_' + filename

        try:
            os.mkdir(folder)
        except FileExistsError:
            pass

        if folder_copy_name is not None:
            try:
                filepathPrefix = 'E:\\PyPrograms\\210sequencer\\data\\' + "%s\\" % year_month + "%s\\" % date_now
                folder_copy = filepathPrefix + folder_copy_name
                os.mkdir(folder_copy)
            except FileExistsError:
                pass

        def CoreFunc():
            res = self.get_ccd_singleloop_image(width, height, CVIONS=CVIONS,
                                                LoG_sigma=LoG_sigma, threshold=threshold)
            return res

        def Timerfunc(time_now):
            self.ctrl_ccd_singleloop_off()
            time.sleep(0.2)
            self.ctrl_ccd_kinetics_on(repeats=det_time-1, binning=self._binning, roi=self._roi)
            image2 = self.get_ccd_kinetics_data()
            np.save(folder + "\\MultidetFinalDet_image-%s.npy" % time_now, image2)
            if folder_copy_name is not None:
                np.save(folder_copy + "\\MultidetFinalDet_image-%s.npy" % time_now, image2)

        def Interruptfunc():
            self.seq.InterruptSeq()
            self.ctrl_ccd_singleloop_off()
            time.sleep(0.2)



        for i in range(self._repeattime):
            self.ion_count()
            pos_init = self.ion_pos

            self.seq.loadSeq(Seq)
            self.ctrl_ccd_kinetics_on(repeats=1, binning=self._binning, roi=self._roi)
            self.seq.startSeq(repeatTimes=1)
            t0 = time.time()
            image1 = self.get_ccd_kinetics_data()



            time_now = time.strftime("%H-%M-%S")

            state_postsel, thrrawdata1 = self._detectstateall(image1)
            np.save(folder + "\\MultidetPostSel_image-%s.npy" %time_now, image1)
            if folder_copy_name is not None:
                np.save(folder_copy + "\\MultidetPostSel_image-%s.npy" %time_now, image1)
            # np.save(folder + "\\MultidetPostSel_thrrawdata-%s.npy" %time_now, thrrawdata1)
            print(state_postsel)

            if np.max(self.seq.runTime_all_InDet) >= 2e7:
                if postsel_criteria is not None:
                    judge = (state_postsel == postsel_criteria)
                    if np.sum(judge) != len(judge):
                        self.seq.InterruptSeq()
                        time.sleep(0.6)
                        print("post-selection failed, restart!")

                        continue

                width, height = self.ctrl_ccd_singleloop_on(binning=(1,1), roi=self._roi)

                t_pre = time.time()-t0


                rp = rtplot.RtVideo_Timer(CoreFunc, Interruptfunc, ImageSize=(height, width),
                                            TimerTime=longtime/1e6-15-t_pre, Timerfunc=Timerfunc, Timerargs=time_now, autoRun=True)

                del rp

                print("del rp")
            else:
                time.sleep(0.1)
                self.ctrl_ccd_kinetics_on(repeats=det_time-1, binning=self._binning, roi=self._roi)
                image2 = self.get_ccd_kinetics_data()
                np.save(folder + "\\MultidetFinalDet_image-%s.npy" % time_now, image2)
                if folder_copy_name is not None:
                    np.save(folder_copy + "\\MultidetFinalDet_image-%s.npy" % time_now, image2)


            # state, thrrawdata2 = self._detectstateall(image2)


            # np.save(folder + "\\MultidetFinalDet_thrrawdata-%s.npy" % time_now, thrrawdata2)

            self.ion_count()
            pos_final = self.ion_pos
            try:
                pos_all = np.vstack((pos_init, pos_final))
                np.save(folder + "\\ion_pos_%s.npy"%time_now, pos_all)
                if folder_copy_name is not None:
                    np.save(folder_copy + "\\ion_pos_%s.npy"%time_now, pos_all)
            except:
                print("saving ion pos failed")
                print(pos_init)
                print(pos_final)

        return 0




    def _runseq_PMT(self, Seq=[]):
        self.seq.loadSeq(Seq)
        count, detailcount = self.seq.startSeq(repeatTimes=self._repeattime, returnselfreadData=True)
        # print(count)
        state = np.mean(detailcount>self.PMT_threshold)

        return state, detailcount, count


    def PMT_detection(self, eom14GHz=False):
        if eom14GHz == False:
            state, detailcount, count = self._runseq_PMT(Seq=self.spellComb["detection"])
        else:
            state, detailcount, count = self._runseq_PMT(Seq=self.spellComb["detectionCooling"])

        return state, detailcount


    def ion_count(self, ion_no=0):
        repeattime_old = self._repeattime
        self.set_repeattime(40)
        self.t_ion_count = time.time()
        image = self._runseq(Seq=self.spellComb["CCD3432976repump"])
        image = image.sum(axis=1)
        image_lb = GLcvion(image.sum(axis=0) / image.shape[0], LoG_sigma=self._LoG_sigma, threshold=self._cvthr)
        para_cv = cvion_fast_1d(image.sum(axis=0) / image.shape[0], image_lb)

        ion_pos_old = self.ion_pos
        self.ion_pos = para_cv[:, 1]

        ion_csv_file = open(self.ionfileName, "a", newline='')
        csvWriter = csv.writer(ion_csv_file)
        csvWriter.writerow([int(time.time())]+list(self.ion_pos))
        ion_csv_file.close()
        self.ion_num = self.ion_pos.shape[0]

        allcount = get_allcount_1d(image, self.ion_pos, d=2, ion_no=ion_no)
        print(np.mean(allcount))
        self.ion_allcount = np.mean(allcount)


        # self._addrpitimelist = [0]*self.ion_num
        # self._AODfreqlist = list(self._PixelAOD[0]*self.ion_pos + self._PixelAOD[1])
        # savecalpara("AODfreqlist", self._AODfreqlist, self.calibfile)

        print('ion_num = %d' % self.ion_num)

        if self.ion_num == len(ion_pos_old):
            print("Ion displacement:", self.ion_pos - ion_pos_old)


        self.set_repeattime(repeattime_old)

        # self.ion_disp = self.ion_pos - ion_pos_old

        return np.array(self.ion_pos).reshape(len(self.ion_pos), 1)



    def update_AODfreqlist(self):
        self.ion_count()
        self._AODfreqlist[0] = list(self._PixelAOD[0]*self.ion_pos + self._PixelAOD[1])
        self._AODfreqlist1[0] = list(self._PixelAOD[0]*self.ion_pos + self._PixelAOD[1])
        self._AODfreqlist2[0] = list(self._PixelAOD[0]*self.ion_pos + self._PixelAOD[1])
        savecalpara("AODfreqlist", self._AODfreqlist, self.calibfile)
        savecalpara("AODfreqlist1", self._AODfreqlist1, self.calibfile)
        savecalpara("AODfreqlist2", self._AODfreqlist2, self.calibfile)

        print("According to CCD image, AODfreqlist update successfully!")


    def update_AOD_calibration(self, freqs, route):
        t = time.time()
        freqs = [round(freq, 4) for freq in freqs]
        if route == 0:
            self._AODfreqlist1 = (freqs, t)
            savecalpara("AODfreqlist1", self._AODfreqlist1, self.calibfile)
        if route == 1:
            self._AODfreqlist2 = (freqs, t)
            savecalpara("AODfreqlist2", self._AODfreqlist2, self.calibfile)
        self._AODfreqlist = (freqs, t)
        savecalpara("AODfreqlist", self._AODfreqlist, self.calibfile)

        self._f_aom_ind1 = (self._acs_freq-np.mean(self._AODfreqlist1[0]))/2
        self._f_aom_ind2 = (self._acs_freq-np.mean(self._AODfreqlist2[0]))/2


    def calculate_ind_AOM_freq(self, f_target, route, ion=0):
        # Calculate the frequency of the (double-pass) AOM in the individual beam path,
        # so that the overall frequency is 2 * f_target.
        # f_target is the desired frequency as if driven by the global beam AOM (without the AOD).

        # In the future, to work with more than two ions, we would likely need to give the list of ions as input.
        # For now with maximally 2 ions, we subtract the average frequency of the AOD tones.
        if route == 0:
            return f_target - self._AODfreqlist1[0][ion] / 2
        if route == 1:
            return f_target - self._AODfreqlist2[0][ion] / 2

    def _detectstateall(self, image):
        if len(self.ion_pos) == 0:
            print("use ion_count firstly to get the ion position")
            return -1
        else:
            state, thrrawdata = get_state_1d(image, self.ion_pos, countthr=self._detectionthr, d=self._d, ion_no=[])

        return state, thrrawdata



    def _correlationdetect(self, image, ion=[0, 1], state_selected=[]):    

        '''
        detect the correlation between two ion.
        if the number of ions you select is 2,
        then the return "state" represents the population of all four states in z basis for two ions;
        if the number of ions is larger than 2,
        the return "state" represent odd population with the "state_selected" parameter being empty list 
        or the population of the states you select in the "state_selected" list
        '''
       
        # assert len(ion)==2

        # state, thrrawdata = get_correlation(image, self.ion_pos, countthr=self._detectionthr, d=self._d, ion_no=ion)
        state, thrrawdata = get_correlation(image, self.ion_pos, countthr=self._detectionthr, d=self._d, ion_no=ion, state_selected=state_selected)

        return state, thrrawdata


    def _detectstateall_postsel(self, image):

        pass

    def _correlationdetect_postsel(self, image, ion=[0, 1]):
        pass

    # def append_shelving_sbc(self, seq, awg_sequence, sbc=True, shelvingdet=1, PMT_det=False, awg_reload_sbc=True):
    #     #suppose that sbc is always at the start of exp. and shelvingdet at the end
    #     if sbc:
    #         sbc_seq = self.SBC_seq(self._sbc_tlist,
    #                                # self._sbc_tendlist,
    #                                self._sbc_cycle,
    #                                self._sbc_freqlist,
    #                                awg_sequence, awg_reload_sbc)
    #         seq = sbc_seq + seq
    #     else:
    #         if PMT_det == False:
    #             # Extend the F-repump time to meet the requirement of the CCD clean cycle
    #             seq = self.Doppler_cooling_seq(5000) + seq  #normal Doppler cooling
    #         else:
    #             seq = self.Doppler_cooling_seq(self.t_DopplerC_PMT) + seq  # normal Doppler cooling
    #
    #     if PMT_det == False:
    #         if shelvingdet==1:
    #             shelving_seq = self.shelvingdet_seq(awg_sequence) # shelving detection
    #             seq = seq + shelving_seq + self.CCDcoolingdet_seq()
    #
    #         elif shelvingdet == -1:
    #             # Only perform shelving, without detection. (Used for appending other pulses after shelving when debugging)
    #             shelving_seq = self.shelvingdet_seq(awg_sequence)  # shelving detection
    #             seq = seq + shelving_seq
    #
    #         elif shelvingdet==0:
    #             detseq = self.CCDdet_seq()  #normal detection
    #             seq = seq + detseq
    #         else:
    #             detseq = self.CCDcoolingdet_seq()  # cooling detection
    #             seq = seq + detseq
    #     else:
    #         if shelvingdet==2:
    #             seq = seq + self.PMTdet_seq(exposuretime=self.t_PMT_exposure, eom14GHz=True)
    #         elif shelvingdet==0:
    #             seq = seq + self.PMTdet_seq(exposuretime=self.t_PMT_exposure, eom14GHz=False)
    #
    #     return seq

    # def probe411_seq(self, awg):
    #     probeseq = ["GlobalAWG2(%f)"%cal._delay_spectrum_global]
    #     probeAWG =  SpectrumAWGSR.SingleRestartSpectrumAWG(awg)
    #     probeAWG.add_pulse_to_waveform(0, 0, 0, cal._delay_spectrum_global)
    #
    #     return probeseq, probeAWG



    def append_shelving_sbc(self, seq, sbc=True, EIT=False, shelvingdet=1, PMT_det=False, awg_reload_sbc=True, on935=True):
        #suppose that sbc is always at the start of exp. and shelvingdet at the end
        if sbc and EIT:
            sbc_seq = self.SBC_seq(self._sbc_tlist,
                                   # self._sbc_tendlist,
                                   self._sbc_cycle,
                                   self._sbc_freqlist,
                                   self.awg_spectrum1, 
                                   awg_reload_sbc=awg_reload_sbc,
                                   Frepump=False)
            seq = self.EITcooling_seq(Frepump=True) + sbc_seq + seq
        elif (not EIT) and sbc:
            sbc_seq = self.SBC_seq(self._sbc_tlist,
                                   # self._sbc_tendlist,
                                   self._sbc_cycle,
                                   self._sbc_freqlist,
                                   self.awg_spectrum1, 
                                   awg_reload_sbc=awg_reload_sbc,
                                   Frepump=True)
            seq = sbc_seq + seq
        elif EIT and (not sbc):
            seq = self.EITcooling_seq(Frepump=True) + seq
        else:
            if PMT_det == False:
                # Extend the F-repump time to meet the requirement of the CCD clean cycle
                seq = self.Doppler_cooling_seq(5000) + seq  #normal Doppler cooling
            else:
                seq = self.Doppler_cooling_seq(self.t_DopplerC_PMT) + seq  # normal Doppler cooling


        if PMT_det == False:
            if shelvingdet==1:
                shelving_seq = self.shelvingdet_seq(on935=on935) # shelving detection
                seq = seq + shelving_seq + self.CCDcoolingdet_seq()

            elif shelvingdet == -1:
                # Only perform shelving, without detection. (Used for appending other pulses after shelving when debugging)
                shelving_seq = self.shelvingdet_seq(on935=on935)  # shelving detection
                seq = seq + shelving_seq

            elif shelvingdet==0:
                detseq = self.CCDdet_seq()  #normal detection
                seq = seq + detseq
            elif shelvingdet==2:
                detseq = self.CCDcoolingdet_seq()  # cooling detection
                seq = seq + detseq
            elif shelvingdet==3:
                shelving_seq = self.F_shelving_seq()
                seq = seq + shelving_seq + self.CCDcoolingdet_seq()
        else:
            if shelvingdet==2:
                seq = seq + self.PMTdet_seq(exposuretime=self.t_PMT_exposure, eom14GHz=True)
            elif shelvingdet==0:
                seq = seq + self.PMTdet_seq(exposuretime=self.t_PMT_exposure, eom14GHz=False)

        return seq

    def Doppler_cooling_seq(self, t):
        seq = ["Frepump(%f)"%t,
                    "free(1)",
                    "Laser976(10)",
                    "pumping(%.2f)" % self.t_pumping,
                    "free(1)"]

        return seq

    def EITcooling_seq(self, Frepump=True):
        if Frepump:
            return ["Frepump(5000)", "free(1)", "Laser976(10)", "EITcooling(%.1f)"%self.t_EITcooling, "free(1)", "pumping(%.2f)"%self.t_pumping, "free(1)"]
        else:
            return ["EITcooling(%.1f)"%self.t_EITcooling, "free(1)", "pumping(%.2f)"%self.t_pumping]

    def SBC_seq(self, tlist, cycle, freqlist, awg, awg_reload_sbc=True, Frepump=True):
        N = len(freqlist)

        assert len(tlist) == N
        # assert len(tendlist) == N
        # assert len(cyclelist) == N

        awg_sequence = SpectrumAWGSR.SingleRestartSpectrumAWG(awg)

        # sbc_time = np.sum((np.array(tstartlist)+np.array(tendlist))*cycle/2.0)
        tscanrange = []
        for i in range(N):
            n_seg = len(tlist[i])
            m = cycle//n_seg
            cycle_res = cycle%n_seg
            t_nseg = []

            t_nseg = t_nseg + [tlist[i][0]] * (m + cycle_res)
            for j in range(n_seg-1):
                t_nseg = t_nseg + [tlist[i][j+1]]*m


            tscanrange.append(t_nseg)

        sbc_time = np.sum(np.array(tscanrange).reshape(-1)) + self._t_SBC_repump*N*cycle
        # SBCcycle = self.Doppler_cooling_seq(2000)
        if Frepump:
            SBCcycle = self.Doppler_cooling_seq(np.max((5000-sbc_time, 2500)))
        else:
            SBCcycle = []

        if awg_reload_sbc:
            # Reset the SBC waveform stored in awg_sequence
            awg_sequence.waveform = []

        # tscanrange = []
        #
        # for i in range(N):
        #     tscanrange.append(np.linspace(tstartlist[i], tendlist[i], cycle))

        # Prepare the waveform for SBC
        # SBCcycle.append("GlobalAWG1(%f)" % (self._delay_spectrum_global))
        SBCcycle.append("GlobalConv1(%f)" % (self._delay_spectrum_global))
        awg_sequence.add_pulse_to_waveform(0, 0, 0, self._delay_spectrum_global)
        for j in range(cycle):
            for i in range(N):
                tSBC = tscanrange[i][j]
                # AWG outputs the SBC pulse. Sequencer idles during this period.
                # SBCcycle.append("free(%f)" % (tSBC+2*self._jitter_spectrum_awg))
                SBCcycle.append("free(%f)" % (tSBC+2*self._jitter_spectrum_awg))
                if awg_reload_sbc:
                    # awg_sequence.add_pulse_to_sbc(freqlist[i], self.amp_sbc, 0, tSBC)
                    awg_sequence.add_sin_squared_pulse_to_waveform(freqlist[i], self.amp_sbc, 0, tSBC, self._t_shape_sbc)
                    awg_sequence.add_pulse_to_waveform(freqlist[i], 0, 0, 0.04+2*self._jitter_spectrum_awg)
                # Sequencer outputs the repumping pulses. AWG idles during this period.
                # SBCcycle.append("SBCrepump(%f)" % self._t_SBC_repump)
                SBCcycle.append("SBCrepump(%f)" % self._t_SBC_repump)
                if awg_reload_sbc:
                    awg_sequence.add_pulse_to_waveform(0, 0, 0, self._t_SBC_repump)
                    awg_sequence.add_pulse_to_waveform(freqlist[i], 0, 0,  0.04)
                # An extra idle time on both, to make sure the SBC pulse in next round would not overlap the repump despite jitters.
                # SBCcycle.append("free(%f)" % (2 * self._jitter_spectrum_awg))
                SBCcycle.append("free(%f)" % (2 * self._jitter_spectrum_awg))
                if awg_reload_sbc:
                    awg_sequence.add_pulse_to_waveform(0, 0, 0, 2 * self._jitter_spectrum_awg)
                    awg_sequence.add_pulse_to_waveform(freqlist[i], 0, 0, 0.04)

                # awg_waveform.append(AWG.SinCombine([freqlist[i]], [self._amp_global_411], [0], tSBC))

        # SBCcycle.append("free(%f)" % self._car_411_pitimes["411_car_0"])
        # awg_sequence.add_pulse_to_sbc(self._car_411_freqs["411_car_0"], self._amp_global_411, 0, self._car_411_pitimes["411_car_0"])
        # # An extra idle time on both
        # SBCcycle.append("free(%f)" % (2 * self._jitter_spectrum_awg))
        # awg_sequence.add_pulse_to_sbc(0, 0, 0, 2 * self._jitter_spectrum_awg)

        if awg_reload_sbc:
            # Write the new SBC pulse to the AWG
            awg_sequence.update_waveform()

        return SBCcycle



    def shelvingdet_seq(self, on935=True):

        # awg_sequence = SpectrumAWGSR.SingleRestartSpectrumAWG(awg)

        # configure the 3432 AOM amplitude and frequency

        # self.set_ddsfreq(self._freq3432p0, channel=1, profile=6, ddschoice=1)
        self.set_ddsfreq(self._freq3432p0, channel=self._ch_3432, profile=0, ddschoice=self._dds_3432)
        self.set_ddsfreq(self._car_411_freqs["411_car_0"], channel=self._ch_global_411, profile=4, ddschoice=self._dds_global_411)
        self.set_ddsfreq(self._car_411_freqs["411_car_m1"], channel=self._ch_global_411, profile=5, ddschoice=self._dds_global_411)
        self.set_ddsfreq(self._car_411_freqs["411_car_p1"], channel=self._ch_global_411, profile=6, ddschoice=self._dds_global_411)
        # self.set_ddsamp(self._amp_3432, channel=1, profile=6, ddschoice=1)
        self.set_ddsamp(self._amp_3432, channel=self._ch_3432, profile=0, ddschoice=self._dds_3432)
        self.set_ddsamp(self._car_411_amps["411_car_0"], channel=self._ch_global_411, profile=4, ddschoice=self._dds_global_411)
        self.set_ddsamp(self._car_411_amps["411_car_m1"], channel=self._ch_global_411, profile=5, ddschoice=self._dds_global_411)
        self.set_ddsamp(self._car_411_amps["411_car_p1"], channel=self._ch_global_411, profile=6, ddschoice=self._dds_global_411)


        shelving_pulses = []
        # Prepare the sequencer for shelving
        # 0 -> 0 transition

        # This looks correct on oscilloscope
        # shelving_pulses.append("GlobalAWG2(%f)" % (self._delay_spectrum_global))
        if on935:
            shelving_pulses.append("GlobalNconv2(%.2f)" % (self._car_411_pitimes["411_car_0"]))
            # shelving_pulses.append("freeNE(1)")


            # shelving_pulses.append("free(1)")
            shelving_pulses.append("freeNE(1)")
            # shelving_pulses.append("Laser3432p0(%f)" % self._pitime3432p0)
            shelving_pulses.append("LaserNE3432(%.2f)" % self._pitime3432p0)
            shelving_pulses.append("freeNEm411(1)") #time for dds profile switch
            shelving_pulses.append("GlobalNconvm2(%.2f)"%(self._car_411_pitimes["411_car_m1"]))
            shelving_pulses.append("freeNE(1)")  #To avoid the profile ttl switch error when switching two profile ttl at once
            shelving_pulses.append("freeNEp411(1)") #time for dds profile switch
            shelving_pulses.append("GlobalNconvp2(%.2f)" % (self._car_411_pitimes["411_car_p1"]))
        else:
            shelving_pulses.append("GlobalNconvN935(%.2f)" % (self._car_411_pitimes["411_car_0"]))

            # shelving_pulses.append("free(1)")
            shelving_pulses.append("freeNEn935(1)")
            # shelving_pulses.append("Laser3432p0(%f)" % self._pitime3432p0)
            shelving_pulses.append("LaserNEn9353432(%.2f)" % self._pitime3432p0)
            shelving_pulses.append("freeNEmn935(2)")  # time for dds profile switch
            shelving_pulses.append("GlobalNconvmN935(%.2f)" % (self._car_411_pitimes["411_car_m1"]))
            shelving_pulses.append("freeNEn935(1)")  # To avoid the profile ttl switch error when switching two profile ttl at once
            shelving_pulses.append("freeNEpn935(2)")  # time for dds profile switch
            shelving_pulses.append("GlobalNconvpN935(%.2f)" % (self._car_411_pitimes["411_car_p1"]))
        # shelving_pulses.append("free(%f)" % self._pitime3432p0)

        # shelving_pulses.append("free(1)")
        # shelving_pulses.append("free(%f)" % self._car_411_pitimes["411_car_p1"])
        # shelving_pulses.append("free(1)")
        # shelving_pulses.append("Laser3432p0(%f)" % self._pitime3432p0)
        # shelving_pulses.append("free(%f)" % (2 * self._jitter_spectrum_awg + 1))

        # the other transitions

        # for transition in self._car_411_freqs.keys():
        #     if  transition == "411_car_0" or transition == "411_car_p2" or transition == "411_car_m2":
        #         continue
        #     pi_time = self._car_411_pitimes[transition]
        #     # shelving_pulses.append("free(%f)" % (pi_time+2))    #2us is the margin for each free running sequence
        #     shelving_pulses.append("freeNE(%f)" % (pi_time+2))    #2us is the margin for each free running sequence
        #     # shelving_pulses.append("free(1)")
        #
        # # shelving_pulses = shelving_pulses + ["Laser976(10)"]
        #
        # # shelving_pulses = shelving_pulses + self.CCDcoolingdet_seq()
        # # shelving_pulses = shelving_pulses + self.CCDdet_seq()
        #
        # # Configure the AWG for shelving
        # # Suppose the AWG step registers have already been configures in the given awg_sequence (object of SequenceSpectrumAWG class)
        # # This function is only responsible for updating the memory of the AWG
        # awg_sequence.waveform = [] # reset the shelving waveform
        #
        # # Pi-pulse of the 0 -> 0 transition
        # awg_sequence.add_pulse_to_waveform(0, 0, 0, self._delay_spectrum_global)  # delay time matching ttl length
        # awg_sequence.add_pulse_to_waveform(self._car_411_freqs["411_car_0"],
        #                                    self._car_411_amps["411_car_0"],
        #                                    0,
        #                                    self._car_411_pitimes["411_car_0"])
        # awg_sequence.add_pulse_to_waveform(0, 0, 0, 1)  # 1 us free time matching what's written above for Sequencer
        # # Time for the 3432 pulse, during which the 411 is turned off
        # awg_sequence.add_pulse_to_waveform(0, 0, 0, self._pitime3432p0)
        # # A delay after the 3432 pulse, making sure the subsequent 411 pulse is fired after 3432 pulse finishes
        # awg_sequence.add_pulse_to_waveform(0, 0, 0, self._jitter_spectrum_awg + 1)
        #
        # # Pi-pulse of the 0 -> p1 transition
        # # awg_sequence.add_pulse_to_shelving(self._car_411_freqs["411_car_p1"],
        # #                                    self._car_411_amps["411_car_p1"],
        # #                                    0,
        # #                                    self._car_411_pitimes["411_car_p1"])
        # # awg_sequence.add_pulse_to_shelving(0, 0, 0, 1)  # 1 us free time matching what's written above for Sequencer
        # # # Time for the 3432 pulse, during which the 411 is turned off
        # # awg_sequence.add_pulse_to_shelving(0, 0, 0, self._pitime3432p0)
        # # # A delay after the 3432 pulse, making sure the subsequent 411 pulse is fired after 3432 pulse finishes
        # # awg_sequence.add_pulse_to_shelving(0, 0, 0, 2 * self._jitter_spectrum_awg + 1)
        #
        # for transition in self._car_411_freqs.keys():
        #     if transition == "411_car_0" or transition == "411_car_p2" or transition == "411_car_m2":
        #         continue
        #     car_411 = self._car_411_freqs[transition]
        #     pi_time = self._car_411_pitimes[transition]
        #     amp = self._car_411_amps[transition]
        #     awg_sequence.add_pulse_to_waveform(car_411, amp, 0, pi_time)
        #     awg_sequence.add_pulse_to_waveform(0, 0, 0, 1)
        #
        # # Write the new shelving waveform to the awg
        # awg_sequence.update_waveform()

        return shelving_pulses

    def F_shelving_seq(self, n=3, profile=0):

        if profile==0:

            # F_shelving_pulse = ["LaserNEn9353432(%.2f)"%self._pitime3432p0,
            #                     "freeNEn935(1)",
            #                     "GlobalNconvN935(%.2f)"%self._car_411_pitimes["411_car_0"],
            #                     "LaserNEn9353432(%.2f)"%self._pitime3432p0,
            #                     "coolingN935(%.2f)"%self.t_pumping_D32,
            #                     "freeNEn935(1)",
            #                     "GlobalNconvN935(%.2f)" % self._car_411_pitimes["411_car_0"],
            #                     "coolingN935(%.2f)"%self.t_pumping_D32
            #                     ]
            # F_shelving_pulse = ["freeNEn9353432p4(1)",
            #                     "LaserNEn9353432p4(%.2f)" % self._pitime3432p4,
            #                     "freeNEn935(1)",
            #                     "GlobalNconvN935(%.2f)" % self._car_411_pitimes["411_car_0"],
            #                     "freeNEn9353432p4(1)",
            #                     "LaserNEn9353432p4(%.2f)" % self._pitime3432p4,
            #                     "coolingN935(%.2f)" % self.t_pumping_D32,
            #                     "freeNEn935(1)",
            #                     "GlobalNconvN935(%.2f)" % self._car_411_pitimes["411_car_0"],
            #                     "coolingN935(%.2f)" % self.t_pumping_D32
            #                     ]
            F_shelving_pulse = [
                                "Laser3432p0(%.2f)"%self._pitime3432p5,
                                "freeNE(0.5)",
                                "GlobalNconv2(%.2f)"%self._car_411_pitimes["411_car_0"],
                                "freeNE(0.5)",
                                "cooling(%.2f)"%self.t_pumping_SF1,
                                "freeNE(0.5)",
                                "GlobalNconv2(%.2f)"%self._car_411_pitimes["411_car_0"],
                                "freeNE3432p4(0.5)",
                                "Laser3432p4(%.2f)"%self._pitime3432p5,
                                "cooling(%.2f)"%self.t_pumping_SF1,
                                "GlobalNconv2(%.2f)"%self._car_411_pitimes["411_car_0"]
                                ]

        elif profile==1:
            F_shelving_pulse = ["freeNEn9353432p1(1)",
                                "LaserNEn9353432p1(%.2f)" % self._pitime3432p1,
                                "freeNEmn935(1)",
                                "GlobalNconvmN935(%.2f)" % self._car_411_pitimes["411_car_m1"],
                                "freeNEn9353432p1(1)",
                                "LaserNEn9353432p1(%.2f)" % self._pitime3432p1,
                                "coolingN935(%.2f)" % self.t_pumping_D32,
                                "freeNEmn935(1)",
                                "GlobalNconvmN935(%.2f)" % self._car_411_pitimes["411_car_m1"],
                                "coolingN935(%.2f)" % self.t_pumping_D32
                                ]
        else:
            F_shelving_pulse = ["freeNEn9353432(1)",
                                "freeNEn9353432p2(1)",
                                "LaserNEn9353432p2(%.2f)" % self._pitime3432p2,
                                "freeNEn9353432(1)",
                                "freeNEpn935(1)",
                                "GlobalNconvpN935(%.2f)" % self._car_411_pitimes["411_car_p1"],
                                "freeNEn9353432(1)",
                                "freeNEn9353432p2(1)",
                                "LaserNEn9353432p2(%.2f)" % self._pitime3432p2,
                                "freeNEn9353432(1)",
                                "coolingN935(%.2f)" % self.t_pumping_D32,
                                "freeNEpn935(1)",
                                "GlobalNconvpN935(%.2f)" % self._car_411_pitimes["411_car_p1"],
                                "coolingN935(%.2f)" % self.t_pumping_D32
                                ]

        F_shelving_pulses = F_shelving_pulse*n


        return F_shelving_pulses


    def F_shelving_postsel_seq(self):
        self.set_ddsphase(180, channel=self._ch_3432, profile=4, ddschoice=self._dds_3432)
        self.set_ddsphase(0, channel=self._ch_3432, profile=0, ddschoice=self._dds_3432)
        self.set_ddsamp(self._amp_3432, channel=self._ch_3432, profile=4, ddschoice=self._dds_3432)
        self.set_ddsamp(self._amp_3432, channel=self._ch_3432, profile=0, ddschoice=self._dds_3432)
        self.set_ddsfreq(self._freq3432p3, channel=self._ch_3432, profile=4, ddschoice=self._dds_3432)
        self.set_ddsfreq(self._freq3432p3, channel=self._ch_3432, profile=0, ddschoice=self._dds_3432)

        shelving_pulse =  ["Laser3432p0(%.2f)" % self._pitime3432p5,
                           "freeNE(0.5)",
                           "GlobalNconv2(%.2f)" % self._car_411_pitimes["411_car_0"],
                           "freeNE(0.5)",
                           "cooling(6)",
                           "freeNE(0.5)",
                           "GlobalNconv2(%.2f)" % self._car_411_pitimes["411_car_0"],
                           "freeNE3432p4(0.5)",
                           "Laser3432p4(%.2f)" % self._pitime3432p5,
                           "cooling(6)",
                           "GlobalNconv2(%.2f)" % self._car_411_pitimes["411_car_0"]]

        shelving_pulse_F40 = self.MW_F_seq(t=1, shutter=False) + shelving_pulse*2

        postsel_seq = shelving_pulse + self.CCDcoolingdet_seq() + ["Laser976(20)", "coolingamp03432(6000)"] + self.CCDcoolingdet_seq() + ["coolingamp03432(6000)"] + shelving_pulse_F40

        return postsel_seq

    def F_shelving_postsel_seq_only30(self):
        self.set_ddsphase(0, channel=self._ch_3432, profile=4, ddschoice=self._dds_3432)
        self.set_ddsphase(0, channel=self._ch_3432, profile=0, ddschoice=self._dds_3432)
        self.set_ddsamp(self._amp_3432, channel=self._ch_3432, profile=4, ddschoice=self._dds_3432)
        self.set_ddsamp(self._amp_3432, channel=self._ch_3432, profile=0, ddschoice=self._dds_3432)
        self.set_ddsfreq(self._freq3432p0, channel=self._ch_3432, profile=4, ddschoice=self._dds_3432)
        self.set_ddsfreq(self._freq3432p0, channel=self._ch_3432, profile=0, ddschoice=self._dds_3432)

        shelving_pulse =  ["Laser3432p0(%.2f)" % self._pitime3432p0,
                           "freeNE(0.5)",
                           "GlobalNconv2(%.2f)" % self._car_411_pitimes["411_car_0"],
                           "freeNE(0.5)",
                           "cooling(6)",
                           "freeNE(0.5)",
                           "GlobalNconv2(%.2f)" % self._car_411_pitimes["411_car_0"],
                           "freeNE3432p4(0.5)",
                           "Laser3432p4(%.2f)" % self._pitime3432p0,
                           "cooling(6)",
                           "GlobalNconv2(%.2f)" % self._car_411_pitimes["411_car_0"]]

        postsel_seq = shelving_pulse

        return postsel_seq


    def PMTdet_seq(self, exposuretime=400, eom14GHz=True):
        if eom14GHz:
            return ["detectioncooling(%f)"%exposuretime]
        else:
            return ["detection(%f)"%exposuretime]

    def CCDdet_seq(self, trigger_time=155, exposuretime=1000):
        return ["CCD(%f)"%trigger_time, "ccddet(%f)"%exposuretime, "detectionfree(%f)"%1000]

    def CCDcoolingdet_seq(self, trigger_time=155, exposuretime=1000):
        return ["CCD(%f)"%trigger_time, "ccddetcooling(%f)"%exposuretime, "detectionfree(%f)"%1000]


    def MW_seq(self, profile=0, t=0.5, ion_select="mid"): 
        #t is in MWpitime unit.so 0.5 == pi/2 gate, 
        # ion_select: the pitime of the ion we use to calculate the pitime. "all"--all the ion, "mid":the ions in the middle of the ion chain. 
        # if the input is a list then select the ions with the index in the list 
        if profile == 0:
            pitime = self._MWpitimelist0
            seq_pre = []
        elif profile==1:
            pitime = self._MWpitimelist1
            seq_pre = ["freeMWp1(1)"]
        elif profile == 2:
            pitime = self._MWpitimelist2
            seq_pre = ["freeMWp2(1)"]
        if ion_select=="all":
            return seq_pre + ["Microwave"+str(profile)+"(%.2f)"%(t*np.mean(pitime))]
        elif ion_select=="mid":
            if self.ion_num < 4:
                return seq_pre + ["Microwave"+str(profile)+"(%.2f)"%(t*np.mean(pitime))]
            else:
                pitime_mean = np.mean(np.array(pitime)[1:-1])
                return seq_pre + ["Microwave"+str(profile)+"(%.2f)"%(t*pitime_mean)]
        else:
            assert np.max(ion_select) < self.ion_num
            pitime_mean = np.mean(np.array(pitime)[ion_select])
            return seq_pre + ["Microwave"+str(profile)+"(%.2f)"%(t*pitime_mean)]

    def MW_seqN935(self, profile=0, t=0.5, ion_select="mid"): 
        #t is in MWpitime unit.so 0.5 == pi/2 gate, 
        # ion_select: the pitime of the ion we use to calculate the pitime. "all"--all the ion, "mid":the ions in the middle of the ion chain. 
        # if the input is a list then select the ions with the index in the list 
        if profile == 0:
            pitime = self._MWpitimelist0
            seq_pre = []
        elif profile==1:
            pitime = self._MWpitimelist1
            seq_pre = ["freeMWp1N935(1)"]
        elif profile == 2:
            pitime = self._MWpitimelist2
            seq_pre = ["freeMWp2N935(1)"]
        if ion_select=="all":
            return seq_pre + ["Microwave"+str(profile)+"N935"+"(%.2f)"%(t*np.mean(pitime))]
        elif ion_select=="mid":
            if self.ion_num < 4:
                return seq_pre + ["Microwave"+str(profile)+"N935"+"(%.2f)"%(t*np.mean(pitime))]
            else:
                pitime_mean = np.mean(np.array(pitime)[1:-1])
                return seq_pre + ["Microwave"+str(profile)+"N935"+"(%.2f)"%(t*pitime_mean)]
        else:
            assert np.max(ion_select) < self.ion_num
            pitime_mean = np.mean(np.array(pitime)[ion_select])
            return seq_pre + ["Microwave"+str(profile)+"N935"+"(%.2f)"%(t*pitime_mean)]

    def MW_F_seq(self, t=1, shutter=False, profile=0, ion_select="mid"):  
        #t is in MWpitime unit.so 0.5 == pi/2 gate
        # ion_select: the pitime of the ion we use to calculate the pitime. "all"--all the ion, "mid":the ions in the middle of the ion chain. 
        # if the input is a list then select the ions with the index in the list 
        if profile == 0:
            pitime = self._MWpitimelistF
            seq_pre = []
            seq_name = "MicrowaveFamp03432"
        elif profile == 2:
            pitime = self._MWpitimelistF2
            seq_pre = ["freeMWFp2(1)"]
            seq_name = "MicrowaveFamp03432p2"
        else:
            print("the profile is not used, switch to profile0")
            pitime = self._MWpitimelistF
            seq_pre = []
            seq_name = "MicrowaveFamp03432"


        if shutter:
            # the shutter mode is only available in profile0
            # return ["MicrowaveFN3432(%.2f)"%(t*np.mean(self._MWpitimelistF))]
            return ["MicrowaveFN3432(%.2f)"%(t*np.mean(pitime))]
        else:
            if ion_select=="all":
                return seq_pre + [seq_name + "(%.2f)"%(t*np.mean(pitime))]
            elif ion_select=="mid":
                if self.ion_num < 4:
                    return seq_pre + [seq_name + "(%.2f)"%(t*np.mean(pitime))]
                else:
                    pitime_mean = np.mean(np.array(pitime)[1:-1])
                    return seq_pre + [seq_name + "(%.2f)"%(t*pitime_mean)]
            else:
                assert np.max(ion_select) < self.ion_num
                pitime_mean = np.mean(np.array(pitime)[ion_select])
                return seq_pre + [seq_name + "(%.2f)"%(t*pitime_mean)]

            # if profile == 0:
            #     return ["MicrowaveFamp03432(%.2f)"%(t*np.mean(self._MWpitimelistF))]
            # elif profile == 2:
            #     return ["freeMWFp2(1)", "MicrowaveFamp03432p2(%.2f)"%(t*np.mean(self._MWpitimelistF2))]
            # else:
            #     print("the profile is not used, switch to profile0")
            #     return ["MicrowaveFamp03432(%.2f)"%(t*np.mean(self._MWpitimelistF))]



    def AWG_MultiPulses_seq(self, t_off, t_off_before, t_pulse, t_margin, N_loop=1, scheme='2qgate'):
        legal_list = ['2qgate', 'simple_pulse','ZZgate', 'N-loop_ZZgate']
        assert scheme in legal_list


        if scheme == 'simple_pulse':
            seq = ["Laser411i1(%.2f)"%self.T_AWG_TRIG, "AOD1(20.5)", "free(%.2f)"%t_off_before] + ["free(%.2f)"%t_pulse, "free(%.2f)"%t_off]

        elif scheme == '2qgate':
            seq = ["Laser411i1(%.2f)" % self.T_AWG_TRIG, "AOD1(20.5)", "free(%.2f)" % t_off_before] + self.MW_seq(profile=0, t=0.5)
            seq = seq + ["free(%.2f)" % t_margin, "free(%.2f)" % t_pulse,
                         "free(%.2f)" % t_margin]  # idle during the 1st SDF pulse, with t_margin before and after it
            seq = seq + self.MW_seq(profile=0, t=1)
            seq = seq + ["free(%.2f)" % t_margin, "free(%.2f)" % t_pulse,
                         "free(%.2f)" % t_margin]  # idle during the 2nd SDF pulse, with t_margin before and after it
            seq = seq + self.MW_seq(profile=0, t=0.5) + ["free(%.2f)" % t_off]
        elif scheme == 'ZZgate':
            seq = ["Laser411i1(%.2f)" % self.T_AWG_TRIG, "AOD1(20.5)", "free(%.2f)" % t_off_before]
            seq = seq + ["free(%.2f)" % t_pulse,
                         "free(%.2f)" % t_margin]  # idle during the 1st SDF pulse, with t_margin after it
            seq = seq + self.MW_seq(profile=0, t=1)
            seq = seq + ["free(%.2f)" % t_margin, 
                         "free(%.2f)" % t_pulse]  # idle during the 2nd SDF pulse, with t_margin before it
            seq = seq + ["free(%.2f)" % t_off]
        elif scheme == 'N-loop_ZZgate':
            
            seq_prefix = ["Laser411i1(%.2f)" % self.T_AWG_TRIG, "AOD1(20.5)", "free(%.2f)" % t_off_before]
            seq_zzgate = ["free(%.2f)"%t_pulse, "free(%.2f)"%t_margin] + self.MW_seq(profile=0, t=1) + ["free(%.2f)"%t_margin, "free(%.2f)"%t_pulse]
            seq_end = ["free(%.2f)"%t_off]

            seq = seq_prefix + seq_zzgate*N_loop + seq_end

        return seq




    def Conversion_seq(self, direction="S-F"):
        self.set_ddsamp(self._car_411_amps["411_car_0"], channel=self._ch_global_411, profile=4, ddschoice=self._dds_global_411)
        self.set_ddsfreq(self._car_411_freqs["411_car_0"], channel=self._ch_global_411, profile=4, ddschoice=self._dds_global_411)
        self.set_ddsamp(self._amp_3432, channel=self._ch_3432, profile=0, ddschoice=self._dds_3432)
        self.set_ddsfreq(self._freq3432p0, channel=self._ch_3432, profile=0, ddschoice=self._dds_3432)

        if direction=="S-F":
            # return ["GlobalConv2(%.2f)"%self._CEOMpitime, "free(1)", "Laser3432p0(%.2f)"%self._pitime3432p0]
            return ["GlobalConv2(%.2f)"%self._CEOMpitime, "free(1)", "Laser3432p0(%.2f)"%((self._pitime3432p0+self._pitime3432p5)/2)]
        elif direction=="F-S":
            return ["Laser3432p0(%.2f)"%self._pitime3432p0, "free(1)", "GlobalConv2(%.2f)"%self._CEOMpitime]
        else:
            print("no such direction, return S-F")
            return ["GlobalConv2(%.2f)" % self._CEOMpitime, "free(1)", "Laser3432p0(%.2f)" % self._pitime3432p0]

    def ConversionN935_seq(self, direction="S-F"):
        self.set_ddsamp(self._car_411_amps["411_car_0"], channel=self._ch_global_411, profile=4, ddschoice=self._dds_global_411)
        self.set_ddsfreq(self._car_411_freqs["411_car_0"], channel=self._ch_global_411, profile=4, ddschoice=self._dds_global_411)
        self.set_ddsamp(self._amp_3432, channel=self._ch_3432, profile=0, ddschoice=self._dds_3432)
        self.set_ddsfreq(self._freq3432p0, channel=self._ch_3432, profile=0, ddschoice=self._dds_3432)

        if direction=="S-F":
            # return ["GlobalConv2(%.2f)"%self._CEOMpitime, "free(1)", "Laser3432p0(%.2f)"%self._pitime3432p0]
            return ["GlobalConv2N935(%.2f)"%self._CEOMpitime, "free935(1)", "Laser3432p0N935(%.2f)"%((self._pitime3432p0+self._pitime3432p5)/2)]
        elif direction=="F-S":
            return ["Laser3432p0N935(%.2f)"%self._pitime3432p0, "free935(1)", "GlobalConv2N935(%.2f)"%self._CEOMpitime]
        else:
            print("no such direction, return S-F")
            return ["GlobalConv2N935(%.2f)" % self._CEOMpitime, "free935(1)", "Laser3432p0N935(%.2f)" % self._pitime3432p0]

    def update_AOD(self, ion=[0, 1], phases1=[0, 0], phases2=[0, 0]):
        amp2 = np.sqrt(self._amp_aod_ind2 ** 2 / len(ion))
        amp1 = np.sqrt(self._amp_aod_ind1 ** 2 / len(ion))


        probe_AOD = SpectrumAWG2.ProbeSequence(self.awg_spectrum_aod)
        # Configure the idle for the AOD Spectrum
        probe_AOD.waveform_idle1 = []
        probe_AOD.waveform_idle2 = []
        # probe_AOD.add_pulse_to_idle(self.f_aod_idle, self._amp_aod_ind1, 0,
        #                             self.f_aod_idle, self._amp_aod_ind2, 0, self.t_aod_idle)

        probe_AOD.add_pulse_to_idle(self.f_aod_idle, 0, 0,
                                    self.f_aod_idle, 0, 0, self.t_aod_idle)
        probe_AOD.update_idle()

        # print(self._AODfreqlist1)
        # print(self._AODfreqlist2)

        # t_start = datetime.now()
        probe_AOD.waveform_probe1 = SpectrumAWG2.SinCombine([self._AODfreqlist1[0][i] for i in ion],
                                                            [amp1] * len(ion), phases1, self.t_aod_total,
                                                            probe_AOD._sample_rate)
        probe_AOD.waveform_probe2 = SpectrumAWG2.SinCombine([self._AODfreqlist2[0][i] for i in ion],
                                                            [amp2] * len(ion), phases2, self.t_aod_total,
                                                            probe_AOD._sample_rate)
        # print(datetime.now() - t_start)
        probe_AOD.update_probe()

    def update_AOD_ion_beam(self, ion=[0, 1]):      #one beam address one ion respectively
        probe_AOD = SpectrumAWG2.ProbeSequence(self.awg_spectrum_aod)
        # Configure the idle for the AOD Spectrum
        probe_AOD.waveform_idle1 = []
        probe_AOD.waveform_idle2 = []
        # probe_AOD.add_pulse_to_idle(self.f_aod_idle, self._amp_aod_ind1, 0,
        #                             self.f_aod_idle, self._amp_aod_ind2, 0, self.t_aod_idle)

        probe_AOD.add_pulse_to_idle(self.f_aod_idle, 0, 0,
                                    self.f_aod_idle, 0, 0, self.t_aod_idle)
        probe_AOD.update_idle()

        # print(self._AODfreqlist1)
        # print(self._AODfreqlist2)

        # t_start = datetime.now()
        probe_AOD.waveform_probe1 = SpectrumAWG2.SinCombine([self._AODfreqlist1[0][ion[0]]],
                                                            [self._amp_aod_ind1], [0], self.t_aod_total,
                                                            probe_AOD._sample_rate)
        probe_AOD.waveform_probe2 = SpectrumAWG2.SinCombine([self._AODfreqlist2[0][ion[1]]],
                                                            [self._amp_aod_ind2], [0], self.t_aod_total,
                                                            probe_AOD._sample_rate)
        # print(datetime.now() - t_start)
        probe_AOD.update_probe()


    def update_AOD_freqs(self, awg_sequence, freq_list, route, ion=[0]):
        assert len(ion)==1
        probe_AOD = awg_sequence #SpectrumAWG2.ProbeSequence(self.awg_spectrum_aod)

        if route == 0:
            # amp = np.sqrt(self._amp_aod_ind2 ** 2 / len(ion))
            amp = np.sqrt(self._amp_aod_ind1 ** 2)
            probe_AOD.waveform_probe1 = SpectrumAWG2.SinCombine([freq_list[i] for i in ion],
                                                                [amp] * len(ion), [0] * len(ion), self.t_aod_total,
                                                                probe_AOD._sample_rate)
            # probe_AOD.waveform_probe1 = SpectrumAWG2.SinCombine([freq_list[0]],
            #                                                    [amp], [0], self.t_aod_total,
            #                                                    probe_AOD._sample_rate)
            probe_AOD.waveform_probe2 = [0]
        else:
            # amp = np.sqrt(self._amp_aod_ind2 ** 2 / len(ion))
            amp = np.sqrt(self._amp_aod_ind2 ** 2)
            probe_AOD.waveform_probe1 = [0]
            probe_AOD.waveform_probe2 = SpectrumAWG2.SinCombine([freq_list[i] for i in ion],
                                                                [amp] * len(ion), [0] * len(ion), self.t_aod_total,
                                                                probe_AOD._sample_rate)
            # probe_AOD.waveform_probe2 = SpectrumAWG2.SinCombine([freq_list[0]],
            #                                                     [amp], [0], self.t_aod_total,
            #                                                     probe_AOD._sample_rate)
        probe_AOD.update_probe()

    def individual_timescanseq(self, awg_sequence_AOM, awg_sequence_AOD, route=0, ion=[1], updateAOD=True):
        dion = max(ion)-min(ion)
        assert len(ion)<3
        assert dion<3

        # Configure the idle for the AOM Spectrum
        awg_sequence_AOM.t_off_before = 20
        awg_sequence_AOM.waveform_idle1 = []
        awg_sequence_AOM.waveform_idle2 = []
        # awg_sequence_AOM.add_pulse_to_idle(self.f_aom_idle, self._awg_amp_aom_ind1, 0,
        #                                    self.f_aom_idle, self._awg_amp_aom_ind2, 0, self.t_aom_idle)
        awg_sequence_AOM.add_pulse_to_idle(self.f_aom_idle, 0, 0,
                                           self.f_aom_idle, 0, 0, self.t_aom_idle)

        awg_sequence_AOM.update_idle()

        # Configure the idle for the AOD Spectrum
        awg_sequence_AOD.waveform_idle1 = []
        awg_sequence_AOD.waveform_idle2 = []
        # awg_sequence_AOD.add_pulse_to_idle(self.f_aod_idle, self._amp_aod_ind1, 0,
        #                                    self.f_aod_idle, self._amp_aod_ind2, 0, self.t_aod_idle)
        awg_sequence_AOD.add_pulse_to_idle(self.f_aod_idle, 0, 0,
                                           self.f_aod_idle, 0, 0, self.t_aod_idle)
        if updateAOD:
            awg_sequence_AOD.update_idle()

        if route == 0:
            # use beam path 1
            amp = np.sqrt(self._amp_aod_ind1 ** 2 / len(ion))
            # amp = np.sqrt(self._amp_aod_ind1**2)
            awg_sequence_AOD.waveform_probe1 = SpectrumAWG2.SinCombine([self._AODfreqlist1[0][i] for i in ion],
                                                                       [amp]*len(ion), [0]*len(ion), self.t_aod_total,
                                                                       awg_sequence_AOD._sample_rate)

            # awg_sequence_AOD.waveform_probe1 = SpectrumAWG2.SinCombine([self._AODfreqlist1[0][0]],
            #                                                            [amp], [0],
            #                                                            self.t_aod_total,
            #                                                            awg_sequence_AOD._sample_rate)
            awg_sequence_AOD.waveform_probe2 = [0]
            if updateAOD:
                awg_sequence_AOD.update_probe()

            # print('AOD1 amp:', amp)
            # print('AOD1 time:', self.t_aod_total)
            # print('AOD1 freq:', [self._AODfreqlist[0][i] for i in ion])

            seq = ["Laser411i1(2)", "AOD1(21.5)", "free(%.2f)"%awg_sequence_AOM.t_off_before, "*free(1)"]
            # seq = ["AOD1(21.5)", "Laser411i1(21.5)"]
            # seq = ["Laser411i1(21.5)"]
            awg_sequence_AOM.a_probe1 = self._awg_amp_aom_ind1
            awg_sequence_AOM.a_probe2 = 0


        elif route == 1:
            # use beam path 2
            amp = np.sqrt(self._amp_aod_ind2 ** 2 / len(ion))
            # amp = np.sqrt(self._amp_aod_ind2 ** 2 )

            awg_sequence_AOD.waveform_probe2 = SpectrumAWG2.SinCombine([self._AODfreqlist2[0][i] for i in ion],
                                                                       [amp] * len(ion), [0] * len(ion),
                                                                       self.t_aod_total,
                                                                       awg_sequence_AOD._sample_rate)

            # awg_sequence_AOD.waveform_probe2 = SpectrumAWG2.SinCombine([self._AODfreqlist2[0][0]],
            #                                                            [amp], [0],
            #                                                            self.t_aod_total,
            #                                                            awg_sequence_AOD._sample_rate)
            awg_sequence_AOD.waveform_probe1 = [0]
            if updateAOD:
                awg_sequence_AOD.update_probe()

            seq = ["Laser411i1(2)", "AOD1(21.5)", "free(%.2f)"%awg_sequence_AOM.t_off_before, "*free(1)"]
            # seq = ["Laser411i1(21.5)"]
            awg_sequence_AOM.a_probe1 = 0
            awg_sequence_AOM.a_probe2 = self._awg_amp_aom_ind2

        # elif route == 2:
        #     # run both individual beams
        #     self.set_ddsfreq(130, 0, 0, 0)
        #     self.set_ddsfreq(130+self._car_411_freqs["411_car_0"]-np.min(self._sb_freqlist) + self._detuning_2q_gate, 3, 0, 0)
        #     amp2 = np.sqrt(self._amp_aod_ind2 ** 2 / len(ion))
        #     amp1 = np.sqrt(self._amp_aod_ind1 ** 2 / len(ion))
        #     wavelist2 = AWG.SinCombine([self._AODfreqlist[0][i] for i in ion], [amp2] * len(ion), [0] * len(ion), 500)
        #     wavelist1 = AWG.SinCombine([self._AODfreqlist[0][i] for i in ion], [amp1] * len(ion), [0] * len(ion), 500)
        #     # self._used_awg_channels.append(self._ch_aod_ind1)
        #     # self._used_awg_channels.append(self._ch_aod_ind2)
        #
        #     waveform = {str(self._ch_aod_ind1): [wavelist1], str(self._ch_aod_ind2): [wavelist2]}
        #     # seq = ["AODboth(10)", "*SDF411(0.5)"] + self.MW_seq(profile=0, t=1) + ["*SDF411(0.5)"]
        #     seq = ["AODboth(20)", "Laser411i1(21.5)"]
        #     awg_sequence.a_probe1 = self._awg_amp_aom_ind1
        #     awg_sequence.a_probe2 = self._awg_amp_aom_ind2

        # awg_sequence.update_waveform()


        return seq #, waveform

    def ind_npulse_t_scan(self, route=0, ion=[1], n_pulse=1, updateAOD=True):
        assert len(ion) == 1

        probe = SpectrumAWG2.ProbeSequence(self.awg_spectrum_aom)
        probe_AOD = SpectrumAWG2.ProbeSequence(self.awg_spectrum_aod)

        # Configure the idle for the AOM Spectrum
        probe.t_off_before = 20
        probe.waveform_idle1 = []
        probe.waveform_idle2 = []
        # awg_sequence_AOM.add_pulse_to_idle(self.f_aom_idle, self._awg_amp_aom_ind1, 0,
        #                                    self.f_aom_idle, self._awg_amp_aom_ind2, 0, self.t_aom_idle)
        probe.add_pulse_to_idle(self.f_aom_idle, 0, 0,
                                           self.f_aom_idle, 0, 0, self.t_aom_idle)

        probe.update_idle()

        # Configure the idle for the AOD Spectrum
        probe_AOD.waveform_idle1 = []
        probe_AOD.waveform_idle2 = []
        # awg_sequence_AOD.add_pulse_to_idle(self.f_aod_idle, self._amp_aod_ind1, 0,
        #                                    self.f_aod_idle, self._amp_aod_ind2, 0, self.t_aod_idle)
        probe_AOD.add_pulse_to_idle(self.f_aod_idle, 0, 0,
                                           self.f_aod_idle, 0, 0, self.t_aod_idle)
        if updateAOD:
            probe_AOD.update_idle()

        if route == 0:
            # use beam path 1
            amp = np.sqrt(self._amp_aod_ind1 ** 2 / len(ion))
            # amp = np.sqrt(self._amp_aod_ind1**2)
            probe_AOD.waveform_probe1 = SpectrumAWG2.SinCombine([self._AODfreqlist1[0][i] for i in ion],
                                                                       [amp] * len(ion), [0] * len(ion),
                                                                       self.t_aod_total,
                                                                       probe_AOD._sample_rate)

            # awg_sequence_AOD.waveform_probe1 = SpectrumAWG2.SinCombine([self._AODfreqlist1[0][0]],
            #                                                            [amp], [0],
            #                                                            self.t_aod_total,
            #                                                            awg_sequence_AOD._sample_rate)
            probe_AOD.waveform_probe2 = [0]
            if updateAOD:
                probe_AOD.update_probe()

            # print('AOD1 amp:', amp)
            # print('AOD1 time:', self.t_aod_total)
            # print('AOD1 freq:', [self._AODfreqlist[0][i] for i in ion])



        elif route == 1:
            # use beam path 2
            amp = np.sqrt(self._amp_aod_ind2 ** 2 / len(ion))
            # amp = np.sqrt(self._amp_aod_ind2 ** 2 )

            probe_AOD.waveform_probe2 = SpectrumAWG2.SinCombine([self._AODfreqlist2[0][i] for i in ion],
                                                                       [amp] * len(ion), [0] * len(ion),
                                                                       self.t_aod_total,
                                                                       probe_AOD._sample_rate)

            # awg_sequence_AOD.waveform_probe2 = SpectrumAWG2.SinCombine([self._AODfreqlist2[0][0]],
            #                                                            [amp], [0],
            #                                                            self.t_aod_total,
            #                                                            awg_sequence_AOD._sample_rate)
            probe_AOD.waveform_probe1 = [0]
            if updateAOD:
                probe_AOD.update_probe()


        def t_scan(t):
            assert (t+1)*n_pulse < self.t_aod_total

            probe.reset_probe_waveform()

            probe.add_pulse_to_probe(0, 0, 0,
                                     0, 0, 0, probe.t_off_before)

            if route==0:
                seq = ["Laser411i1(2)", "AOD1(21.5)", "free(%.2f)" % probe.t_off_before, "free(%.1f)"%((t+1)*n_pulse)]
                # seq = ["AOD1(21.5)", "Laser411i1(21.5)"]
                # seq = ["Laser411i1(21.5)"]
                probe.a_probe1 = self._awg_amp_aom_ind1
                probe.a_probe2 = 0

                AODfreq_mean = np.mean(np.array(self._AODfreqlist1[0])[np.array(ion)])



                for n in range(n_pulse):
                    probe.add_sin_squared_pulse_to_probe((self._acs_freq - AODfreq_mean) / 2, self._awg_amp_aom_ind1, 0, 0,
                                                        (self._acs_freq - AODfreq_mean) / 2, 0, 0, 0, t)
                    probe.add_sin_squared_pulse_to_probe((self._acs_freq - AODfreq_mean) / 2, 0, 0, 0,
                                                        (self._acs_freq - AODfreq_mean) / 2, 0, 0, 0, 1)

            elif route==1:
                seq = ["Laser411i1(2)", "AOD1(21.5)", "free(%.2f)" % probe.t_off_before, "free(%.1f)"%((t+1)*n_pulse)]
                # seq = ["Laser411i1(21.5)"]
                probe.a_probe1 = 0
                probe.a_probe2 = self._awg_amp_aom_ind2

                AODfreq_mean = np.mean(np.array(self._AODfreqlist2[0])[np.array(ion)])

                for n in range(n_pulse):
                    probe.add_sin_squared_pulse_to_probe((self._acs_freq - AODfreq_mean) / 2, 0, 0, 0,
                                                        (self._acs_freq - AODfreq_mean) / 2, self._awg_amp_aom_ind2, 0, 0, t)
                    probe.add_sin_squared_pulse_to_probe((self._acs_freq - AODfreq_mean) / 2, 0, 0, 0,
                                                        (self._acs_freq - AODfreq_mean) / 2, 0, 0, 0, 1)

            probe.t_off = self.t_aod_total-(t+1)*n_pulse-probe.t_off_before+20

            probe.add_sin_squared_pulse_to_probe(0, 0, 0, 0,
                                     0, 0, 0, 0, probe.t_off)

            probe.update_probe()

            MWseq0 = self.MW_seq(profile=0, t=0.5)
            MWseq1 = self.MW_seq(profile=1, t=0.5)
            gateseq = ["free(1)"] + MWseq0 + seq + ["free(1)"] + MWseq1

            seq = self.append_shelving_sbc(gateseq, sbc=False, shelvingdet=0)  # No SBC, normal detection

            image = self._runseq(Seq=seq)

            state, thrawdata = self._detectstateall(image)

            return state, thrawdata

        return t_scan


    def cal_acss_pulse(self, route=0, ion=0, n_pulse=1, updateAOD=True):

        timescan = self.ind_npulse_t_scan(route=route, ion=[ion], n_pulse=n_pulse, updateAOD=updateAOD)
        if route == 0:
            t_pi = np.array(self._acss_pi1)
            t_span = t_pi[ion]/n_pulse

        elif route == 1:
            t_pi = np.array(self._acss_pi2)
            t_span = t_pi[ion]/n_pulse

        if n_pulse == 1:
            timescanrange = list(np.linspace(0, 3*t_pi[ion], 21))
            fitfunc = Fit.rabi_fit
        else:
            timescanrange = list(np.linspace(t_pi[ion]-t_span/2, t_pi[ion]+t_span/2, 15))
            fitfunc = Fit.parabola_up_down(max_mode=(n_pulse%2))

        rp = rtplot.Rtplot_SelectIon(timescan, AutoRunStopFunc, ion=[ion], xdata=timescanrange, fitfunc=fitfunc, fileprefix="acss n pulse cal", autoRun=True)

        if rp.fit_result is not None:
            print(rp.fit_result)
            pi_time = list(rp.fit_result)[0]
        else:
            pi_time = t_pi[ion]

        t_pi[ion] = pi_time

        if route == 0:
            savecalpara("acsspi1", list(t_pi), self.calibfile)
            self._acss_pi1 = list(t_pi)
        elif route == 1:
            savecalpara("acsspi2", list(t_pi), self.calibfile)
            self._acss_pi2 = list(t_pi)

        del rp

        return t_pi



    def individual_aodscanseq(self, route=0, t=3):
        # if route==0:
        #     return ["Laser411i1(%f)"%t]
        # elif route==1:
        #     return ["Laser411i2(%f)"%t]
        # return ["AOD1(21.5)", "Laser411i1(%.2f)"%(21.5+t)]

        return ["AOD1(21.5)", "Laser411i1(21.5)", "free(%.2f)" % (t)]


    def get_detection_allcount(self):
        image = self._runseq(Seq=self.spellComb["CCDdetection"])
        data = image.sum(axis=1)
        allcount = []
        for i in range(self.ion_num):
            allcount.append(get_allcount_1d(data, self.ion_pos, d=self._d, ion_no=i))

        return allcount


    def get_pumping_allcount(self):
        image = self._runseq(Seq=self.spellComb["CCDpumping"])
        data = image.sum(axis=1)
        allcount = []
        for i in range(self.ion_num):
            allcount.append(get_allcount_1d(data, self.ion_pos, d=self._d, ion_no=i))

        return allcount


    def _fitc(self, xdata, func, fitfunc):

        fitpara = []
        ycal = np.zeros((self.ion_num, len(xdata)))
        csvFile, file, fileName, folder = genFile(func.__name__+' cal', start=min(xdata), stop=max(xdata))

        for i in range(len(xdata)):
            y = func(xdata[i])
            if y is tuple:
                state = y[0]
            else:
                state = y
            state = state.ravel()
            ycal[:, i] = state
            # print(xdata[i],state)
            csvFile.writerow([xdata[i]]+state.tolist())

        file.close()

        datafit = np.hstack((np.array(xdata).reshape((len(xdata), 1)), np.transpose(ycal)))
        # print(datafit)

        for i in range(self.ion_num):
            try:
                fitpara0, f = fitfunc(datafit[:, [0, i + 1]])
                fitpara0 = [round(para, 4) for para in fitpara0]
                fitpara.append(fitpara0)
            except:
                print("fitting did not converge at ion %d" %i)
                fitpara = None

        return fitpara

    def _selection_fitc(self, xdata, func, fitfunc, ion=None):

        if ion is None:
            fitpara = self._fitc(xdata, func, fitfunc)

        else:
            fitpara = []
            ycal = np.zeros((self.ion_num, len(xdata)))
            csvFile, file, fileName, folder = genFile(func.__name__ + ' cal', start=min(xdata), stop=max(xdata))

            for i in range(len(xdata)):
                y = func(xdata[i])
                if y is tuple:
                    state = y[0]
                else:
                    state = y
                state = state.ravel()
                ycal[:, i] = state
                # print(xdata[i],state)
                csvFile.writerow([xdata[i]] + state.tolist())

            file.close()

            datafit = np.hstack((np.array(xdata).reshape((len(xdata), 1)), np.transpose(ycal)))
            # print(datafit)

            for i in ion:
                try:
                    fitpara0, f = fitfunc(datafit[:, [0, i + 1]])
                    fitpara0 = [round(para, 4) for para in fitpara0]
                    fitpara.append(fitpara0)
                except:
                    print("fitting did not converge at ion %d" % i)
                    fitpara = None
                    break


        return fitpara


    def motor_getopt_fitc(self, tcal, target=0.8, low_limit=0.2, tolerance=0.17, half_range=0.006, direction=1, route=0,
                          ion=[0], step_size=0.001, fast_mode=True):
        if fast_mode:
            state0 = self.run_AOD(tcal, ion=ion, route=route)
        else:
            state0 = np.array([[0]])

        old_pos = self._motorpos[route][direction]

        if np.min(state0) >= target:
            calib_success = True
            best_state = np.min(state0)

            t = time.time()
            self._motorpos[route][direction] = (self._motorpos[route][direction][0], t)
            savecalpara("motorpos", self._motorpos, self.calibfile)

            return self._motorpos, calib_success, best_state, old_pos


        else:
            print(np.min(state0))

            motorscan = self.select_calmotor(tcal=tcal, direction=direction, route=route, ion=ion)

            cur_pos = old_pos[0] # self.motor_ctrl.getpos()

            scanrange = list(np.arange(cur_pos-half_range, cur_pos+half_range, step_size))

            fitpara = self._selection_fitc(scanrange, motorscan, Fit.gaussian_fit, ion=ion)

            print(fitpara)

            calib_success = False
            best_state = 0


            if fitpara is not None:

                fitpara = np.array(fitpara)

                optpos = np.mean(fitpara[:,0])
                yopt = np.mean(fitpara[:, 1]) + np.mean(fitpara[:, 3])
                # yopt = np.mean([Fit.gaussian(optpos, *list(fitpara[i,:])) for i in ion] )
                if yopt >= low_limit:
                    self.motor_ctrl.absolutemove(optpos - 0.005)
                    self.motor_ctrl.absolutemove(optpos)
                    calib_success = True

                    if route==0 and direction==0:
                        self._AODfreqlist = self._AODfreqlist2
                        self._AODfreqlist1 = self._AODfreqlist2
                        savecalpara("AODfreqlist1", self._AODfreqlist1, self.calibfile)
                        savecalpara("AODfreqlist", self._AODfreqlist, self.calibfile)

                else:
                    optpos = self._motorpos[route][direction][0]
                    self.motor_ctrl.absolutemove(optpos - 0.005)
                    self.motor_ctrl.absolutemove(optpos)  # Move to the last calibration result
                    print("Fit error, pos=", optpos)
                    calib_success = False


                # findrange = list(np.arange(optpos + np.minimum(0.003, half_range),
                #                            optpos - np.minimum(0.005, half_range), -0.0005))
                #
                # ycal = []
                # csvFile, file, fileName, folder = genFile("motorscan"+ ' cal', start=0, stop=0)
                #
                # for i in range(len(findrange)):
                #     y = motorscan(findrange[i])
                #     if y is tuple:
                #         state = y[0]
                #     else:
                #         state = y
                #     state = state.ravel().tolist()
                #     ycal.append(state)
                #     # print(xdata[i],state)
                #     csvFile.writerow([findrange[i]] + state)
                #
                #     if i>1:
                #         dy = np.abs(np.mean(np.array(ycal)[-1][ion] - np.array(ycal)[-2][ion]))
                #     else:
                #         dy = yopt
                #     avg_state = np.abs(np.mean(np.array(ycal)[-1][ion]))
                #
                #     if avg_state > best_state:
                #         # Keep track of the best state encountered when moving the motor back
                #         best_state = avg_state
                #
                #     if  avg_state > (1 - tolerance) * yopt and dy < tolerance * yopt:
                #         print("find optimal position successfully, pos=", self.motor_ctrl.getpos())
                #         calib_success = True
                #         break
                #
                #     if i == len(findrange)-1:
                #         self.motor_ctrl.absolutemove(optpos)
                #         print("failed finding optimal position, move to pos=", self.motor_ctrl.getpos())
                #
                # file.close()

            else:
                optpos = self._motorpos[route][direction][0]
                self.motor_ctrl.absolutemove(optpos - 0.005)
                self.motor_ctrl.absolutemove(optpos)    # Move to the last calibration result
                print("Fit error, pos=", optpos)


        t = time.time()
        self._motorpos[route][direction] = (self.motor_ctrl.getpos(), t)
        savecalpara("motorpos", self._motorpos, self.calibfile)

        state_final = self.run_AOD(tcal, ion=ion, route=route)

        self.motor_ctrl.close()

        return self._motorpos, calib_success, np.mean(state_final), old_pos


    def aodfreq_fitc(self, scanrange, route=1,
                    tcal=1, shelvingdet=0, ion=[0]):

        t_aod_total = tcal + 50  # 600

        # Configure the Spectrum AWG for the two AOMs
        probe_sequence = SpectrumAWG2.ProbeSequence(self.awg_spectrum_aom)


        # scanrange = list(np.arange(start, stop, step_size * np.sign(stop - start)))
            # scanrange = list(np.arange(start, stop, 0.00001 * np.sign(stop - start)))

        probe_AOD = SpectrumAWG2.ProbeSequence(self.awg_spectrum_aod)
        # shelving_AOM = SpectrumAWGSR.SingleRestartSpectrumAWG(self.awg_spectrum2)

        # Configure Sequencer
        # seq_cooling = self.Doppler_cooling_seq(5000)
        MWseq0 = self.MW_seq(profile=0, t=0.5)
        # seq411 = self.individual_aodscanseq(route=route, t=tcal)   #t--the time 411 on
        seq411 = self.individual_timescanseq(probe_sequence, probe_AOD, route=route, ion=[0])
        MWseq1 = self.MW_seq(profile=1, t=0.5)
        # seqdet = self.CCDdet_seq()

        seq = MWseq0 + seq411 + MWseq1

        seq = self.append_shelving_sbc(seq, sbc=False, shelvingdet=shelvingdet)
        # print(seq)

        # Configure the Spectrum AWG for the AODs

        # Configure the probe pulse
        probe_AOD.t_probe = t_aod_total
        probe_AOD.a_probe1 = self._amp_aod_ind1
        probe_AOD.f_probe1 = 145
        probe_AOD.a_probe2 = self._amp_aod_ind2
        probe_AOD.f_probe2 = 145
        if route == 0:
            probe_AOD.a_probe2 = 0
        elif route == 1:
            probe_AOD.a_probe1 = 0

        # probe_AOD.update_waveform()

        # Configure the output during the idle time, to send the light to the AODs
        # probe_sequence.waveform_idle1 = []
        # probe_sequence.waveform_idle2 = []
        # probe_sequence.add_pulse_to_idle(125, 1, 0, 125, 1, 0, 1)
        # probe_sequence.update_idle()
        # Configure the probe pulse
        def freqscan(freq):
            probe_sequence.t_probe = tcal
            probe_sequence.a_probe1 = self._awg_amp_aom_ind1
            probe_sequence.f_probe1 = self._f_aom_ind1
            probe_sequence.a_probe2 = self._awg_amp_aom_ind2
            probe_sequence.f_probe2 = self._f_aom_ind2
            if route == 0:
                probe_sequence.a_probe2 = 0
                probe_sequence.f_probe1 = (self._acs_freq - freq) / 2
            elif route == 1:
                probe_sequence.a_probe1 = 0
                probe_sequence.f_probe2 = (self._acs_freq - freq) / 2

            probe_sequence.t_off = t_aod_total - tcal - probe_sequence.t_off_before + 20  # 5
            probe_sequence.update_waveform()

            state, thrrawdata = self.awg_freq_scan(probe_AOD, seq, awg_channel=route)(freq)

            return state

        fitpara = self._selection_fitc(scanrange, freqscan, Fit.gaussian_fit, ion=ion)

        print(fitpara)

        # calib_success = False

        if fitpara is not None:

            fitpara = np.array(fitpara)
            optfreq = fitpara[:, 0]

            yopt = np.mean(fitpara[:, 1]) + np.mean(fitpara[:, 3])

            if route == 0:
                freqlist_old = np.array(self._AODfreqlist1[0])
            elif route == 1:
                freqlist_old = np.array(self._AODfreqlist2[0])

            freqlist_new = np.mean(optfreq[np.array(ion)].reshape(-1) - freqlist_old[np.array(ion)]) + freqlist_old
            # freqlist_new = np.array([round(freq, 4) for freq in freqlist_new])
            self.update_AOD_calibration(list(freqlist_new), route)

            calib_success = True
            print(np.diff(freqlist_old))
            print(np.diff(freqlist_new))

        else:
            if route == 0:
                freqlist_old = np.array(self._AODfreqlist1[0])
            elif route == 1:
                freqlist_old = np.array(self._AODfreqlist2[0])

            freqlist_new = freqlist_old
            yopt = 0

            calib_success = False

        return yopt, freqlist_new, calib_success



    def _singleion_fitc(self, xdata, func, fitfunc):

        fitpara = []
        statelist = []
        csvFile, file, fileName, folder = genFile(func.__name__ + ' cal', start=min(xdata), stop=max(xdata))

        for i in range(len(xdata)):
            state = func(xdata[i])
            statelist.append(state)
            csvFile.writerow([xdata[i], state])

        file.close()

        datafit = np.hstack(np.array(xdata).reshape(len(xdata), 1), np.array(statelist).reshape(len(statelist), 1))
        try:
            fitpara, f = fitfunc(datafit)

            pl.figure()
            ax = pl.axes()
            ax.plot(datafit[:,0], datafit[:,1], 'k.')
            ax.set_title("fitpara=%f" %fitpara[0])
            pl.show()
        except:
            print("single ion calibration failed!")

        return fitpara[0]


    def thrscan(self,thr):
        self.set_threshold(thr, 4000)
        imagedet = self._runseq(Seq=self.spellComb["CCDdetection"])
        statedet, rawdatadet = self._detectstateall(imagedet)
        imagepum = self._runseq(Seq=self.spellComb["CCDpumping"])
        statepum, rawdatapump = self._detectstateall(imagepum)
        fidelity = 1-(statepum+1-statedet)/2.0

        return fidelity



    def select_calddschannel(self, profile, channel, ddschoice=0, seq='', status=True):
        def setfreq(freq):
            self.set_ddsfreq(freq, channel=channel, profile=profile, ddschoice=ddschoice)

            image = self._runseq(Seq=seq)
            if status == False:
                image = image.sum(axis=1)
                count = np.zeros((self.ion_num, 1))

                for i in range(self.ion_num):
                    allcount = get_allcount_1d(image, self.ion_pos, d=self._d, ion_no=i)
                    count[i,0] = np.mean(allcount)

                return count

            else:
                state, thrrawdata = self._detectstateall(image)


                return state, thrrawdata

        return setfreq


    # Wraps the scan of the awg frequency for use in rtplot
    def awg_freq_scan(self, awg_sequence, sequencer_seq='', awg_channel=0):
        def setfreq(freq):
            # Assume the input object of AWG sequence has the method update_freq
            if awg_channel == 0:
                awg_sequence.update_freq(freq, 0)
            if awg_channel == 1:
                awg_sequence.update_freq(0, freq)
            self.seq.scanValue = awg_sequence.t_probe
            image = self._runseq(Seq=sequencer_seq)
            state, thrrawdata = self._detectstateall(image)
            return state, thrrawdata

        return setfreq

    def test_awg_freq_scan(self, awg_sequence, aom_sequence, tcal, sequencer_seq='', awg_channel=0):
        def setfreq(freq):
            # Assume the input object of AWG sequence has the method update_freq
            if awg_channel == 0:
                awg_sequence.update_freq(freq, 0)
            if awg_channel == 1:
                awg_sequence.update_freq(0, freq)
            self.seq.scanValue = awg_sequence.t_probe

            t_total = 600
            if t_total is not None:
                awg_sequence.t_off = t_total - tcal - awg_sequence.t_off_before + 5
            aom_sequence.update_time(tcal)

            image = self._runseq(Seq=sequencer_seq)
            state, thrrawdata = self._detectstateall(image)
            return state, thrrawdata

        return setfreq


    def select_phasedds(self, profile, channel, ddschoice=0, seq=''):
        def setphase(phase):
            self.set_ddsphase(phase, channel=channel, profile=profile, ddschoice=ddschoice)

            image = self._runseq(Seq=seq)
            state, thrrawdata = self._detectstateall(image)

            return state, thrrawdata

        return setphase



    def select_ampdds(self, profile, channel, ddschoice=0, seq=''):
        def setamp(amp):
            self.set_ddsamp(amp, channel=channel, profile=profile, ddschoice=ddschoice)

            image = self._runseq(Seq=seq)
            state, thrrawdata = self._detectstateall(image)

            return state, thrrawdata

        return setamp


    def selectseq(self, seq=''):
        def timescan(t):
            self.seq.scanValue = t
            image = self._runseq(Seq=seq)
            state, thrrawdata = self._detectstateall(image)

            return state, thrrawdata

        return timescan

    def seq_rt(self, t, seq=''):
        def rtfunc():
            state, thrrawdata = self.selectseq(seq)(t)

            return state
        return rtfunc

    def correlation_t_scan(self, seq='', ion=[0, 1]):
        def timescan(t):
            self.seq.scanValue = t
            image = self._runseq(Seq=seq)
            state, thrrawdata = self._correlationdetect(image, ion=ion)

            return state, thrrawdata

        return timescan

    def parity_scan(self, profile, channel, ddschoice=0, seq='', ion=[0,1]):
        def setphase(phase):
            self.set_ddsphase(phase, channel=channel, profile=profile, ddschoice=ddschoice)

            image = self._runseq(Seq=seq)
            state, thrrawdata = self._correlationdetect(image, ion=ion)

            parity = state[0, 0] + state[3, 0] - state[2, 0] - state[1, 0]

            return parity, thrrawdata

        return setphase



    def correlation_phase_scan(self, profile, channel, ddschoice=0, seq='', ion=[0,1]):
        def setphase(phase):
            self.set_ddsphase(phase, channel=channel, profile=profile, ddschoice=ddschoice)

            image = self._runseq(Seq=seq)
            state, thrrawdata = self._correlationdetect(image, ion=ion)

            return state, thrrawdata

        return setphase

    def correlation_freq_scan(self, profile, channel, ddschoice=0, seq='', ion=[0,1]):
        def setfreq(freq):
            self.set_ddsfreq(freq, channel=channel, profile=profile, ddschoice=ddschoice)

            image = self._runseq(Seq=seq)
            state, thrrawdata = self._correlationdetect(image, ion=ion)

            return state, thrrawdata

        return setfreq

    def correlation_amp_scan(self, profile, channel, ddschoice=0, seq='', ion=[0,1]):
        def setamp(amp):
            self.set_ddsamp(amp, channel=channel, profile=profile, ddschoice=ddschoice)

            image = self._runseq(Seq=seq)
            state, thrrawdata = self._correlationdetect(image, ion=ion)

            return state, thrrawdata

        return setamp

    # Wraps the scan of the awg pulse time for use in rtplot
    def awg_time_scan(self, awg_sequence, sequencer_seq='', t_total=None):
        def set_time(t):
            if t_total is not None:
                awg_sequence.t_off = t_total - t - awg_sequence.t_off_before + 20 # The 20 us extra time makes sure the idle of AOM turns on after AOD
            # Assume the input object of AWG sequence has the method update_time
            awg_sequence.update_time(t)

            # Update the scanned time in sequencer.
            # The user has to make sure the same pulse is scanned in sequencer and the awg.
            self.seq.scanValue = t

            # time.sleep(1) # Warm up the AOM after re-writing the AWG waveform

            image = self._runseq(Seq=sequencer_seq)
            state, thrrawdata = self._detectstateall(image)
            return state, thrrawdata

        return set_time


    def awg_correlation_t_scan(self, awg_sequence, sequencer_seq='', ion=[0, 1], t_total=None):
        def timescan(t):
            # awg_sequence.load_sequence()
            # Assume the input object of AWG sequence has the method update_time
            if t_total is not None:
                awg_sequence.t_off = t_total - t - awg_sequence.t_off_before + 20 # The 20 us extra time makes sure the idle of AOM turns on after AOD

            awg_sequence.update_time(t)

            self.seq.scanValue = t
            image = self._runseq(Seq=sequencer_seq)
            state, thrrawdata = self._correlationdetect(image, ion=ion)

            return state, thrrawdata

        return timescan

    def  select_calmotor(self, tcal=1, direction=1, route=0, ion=[0]):

        assert route == 0 or direction == 1
        # The sequence instance for the AOM AWG
        probe_sequence = SpectrumAWG2.ProbeSequence(self.awg_spectrum_aom)
        probe_sequence.t_probe = tcal

        # probe_sequence.a_probe1 = self._awg_amp_aom_ind1
        probe_sequence.f_probe1 = self._f_aom_ind1
        # probe_sequence.a_probe2 = self._awg_amp_aom_ind2
        probe_sequence.f_probe2 = self._f_aom_ind2

        # The sequence instance for the AOD AWG
        probe_AOD = SpectrumAWG2.ProbeSequence(self.awg_spectrum_aod)

        self.seq.scanValue = tcal

        self.motor_ctrl = Motor(com=self.motor[route][direction], velocity=2.0)

        seq411 = self.individual_timescanseq(probe_sequence, probe_AOD, route=route, ion=ion)

        if route == 0 and direction == 0:
            amp = np.sqrt(self._amp_aod_ind1 ** 2 / len(ion))
            probe_AOD.waveform_probe1 = SpectrumAWG2.SinCombine([self._AODfreqlist2[0][i] for i in ion],
                                                                [amp] * len(ion), [0] * len(ion),
                                                                self.t_aod_total,
                                                                probe_AOD._sample_rate)
            probe_AOD.waveform_probe2 = [0]
            probe_AOD.update_probe()

        probe_sequence.t_off = self.t_aod_total - tcal - probe_sequence.t_off_before + 20
        probe_sequence.update_waveform()

        seq_cooling = self.Doppler_cooling_seq(5000)
        MWseq0 = self.MW_seq(profile=0, t=0.5)
        # seq411 = self.individual_aodscanseq(route=route, t=tcal)  # t--the time 411 on
        MWseq1 = self.MW_seq(profile=1, t=0.5)
        seqdet = self.CCDdet_seq()

        seq = seq_cooling + MWseq0 + seq411 + ["free(1)"] + MWseq1 + seqdet



        def motorscan(pos):
            self.motor_ctrl.absolutemove(pos)

            image = self._runseq(Seq=seq)
            state, thrrawdata = self._detectstateall(image)

            return state

        return motorscan

    def thrcal(self):
        scanrange = list(np.arange(2000, 8500, 500))
        thrlist = self._fitc(scanrange, self.thrscan, Fit.gaussian_fit)
        self._detectionthr = np.mean([thrlist[i] for i in range(len(thrlist)) if thrlist[i]!=0])


            # print("threshold calibration failed")

        return self._detectionthr



    def detectionampscan(self, amp):
        ampscan = self.select_ampdds(1, 1, ddschoice=0, seq=self.spellComb["CCDdetection"])
        count = ampscan(amp)

        return count



    def MWfreqcal(self):
        scanrange = list(np.arange(self._MWfreq - 0.08, self._MWfreq + 0.08, 0.002))

        freqscan = self.select_calddschannel(0, self._ch_MW, ddschoice=self._dds_MW, seq=self.spellComb["CCDMW"])
        self.seq.scanValue = np.mean(self._MWpitimelist0)
        rp = rtplot.Rtplot(freqscan, AutoRunStopFunc, xdata=scanrange, fitfunc=Fit.gaussian_fit, fileprefix="MWfreqcal", autoRun=True)
        if rp.fit_resultRtplot is not None:
            freqlist = rp.fit_result
            print(rp.fit_result)
            self._MWfreq = np.mean(freqlist)
            savecalpara("MWfreq", self._MWfreq, self.calibfile)
            self.set_ddsfreq(self._MWfreq, channel=self._ch_MW, profile=1, ddschoice=self._dds_MW)
            self.set_ddsfreq(self._MWfreq, channel=self._ch_MW, profile=0, ddschoice=self._dds_MW)
        # except:
        #     print("MW frequency calibration goes wrong!")

        del rp

        return self._MWfreq


    def MW_F_freqcal(self, profile=0):
        scanrange = list(np.linspace(self._MWfreq_F - 0.0006, self._MWfreq_F + 0.0006, 30))

        seq_pre = self.Conversion_seq(direction="S-F")
        if profile==0:
            seq_MW = ["free(1)"] + ["*MicrowaveFamp03432(1000)"] + ["free(1)"]
            self.seq.scanValue = np.mean(self._MWpitimelistF)
        elif profile==2:
            seq_MW = ["freeMWFp2(1)"] + ["*MicrowaveFamp03432p2(1000)"] + ["freeMWFp2(1)"]
            self.seq.scanValue = np.mean(self._MWpitimelistF2)
        else:
            print("No such profile, switch to profile0")
            seq_MW = ["free(1)"] + ["*MicrowaveFamp03432(1000)"] + ["free(1)"]
            self.seq.scanValue = np.mean(self._MWpitimelistF)
        # seq_end = self.Conversion_seq(direction='F-S')
        seq_end = self.F_shelving_seq(n=1, profile=0)

        seq = seq_pre + seq_MW + seq_end

        seq = self.append_shelving_sbc(seq, sbc=False, shelvingdet=2)



        freqscan = self.select_calddschannel(0, 0, ddschoice=self._dds_MW_F, seq=seq)

        rp = rtplot.Rtplot(freqscan, AutoRunStopFunc, xdata=scanrange, fitfunc=Fit.inv_gaussian_fit, fileprefix="MW_F_freqcal",
                           autoRun=True)
        if rp.fit_result is not None:
            freqlist = rp.fit_result
            print(rp.fit_result)
            self._MWfreq_F = np.mean(freqlist)
            savecalpara("MWfreq_F", self._MWfreq_F, self.calibfile)
            self.set_ddsfreq(self._MWfreq_F, channel=0, profile=0, ddschoice=self._dds_MW_F)
        # except:
        #     print("MW frequency calibration goes wrong!")

        del rp

        return self._MWfreq_F


    def MWfreqfinecal(self):
        detuning_add  = 0.001
        scanrange = list(np.arange(0.02, 5000, 50))
        self.set_ddsfreq(self._MWfreq + detuning_add, channel=self._ch_MW, profile=1, ddschoice=self._dds_MW)
        self.set_ddsfreq(self._MWfreq + detuning_add, channel=self._ch_MW, profile=0, ddschoice=self._dds_MW)
        MWseq = self.MW_seq(profile=0, t=0.5)
        gateseq = MWseq + ["*free(1)"] + MWseq
        seq = self.append_shelving_sbc(gateseq, sbc=False, shelvingdet=0)
        # print(seq)

        ramsey = self.selectseq(seq=seq)
        rp = rtplot.Rtplot(ramsey, AutoRunStopFunc, xdata=scanrange, fitfunc=Fit.sine_fit, fileprefix="MWfreqcal", autoRun=True)
        if rp.fit_result is not None:
            detuning = 0.5/np.mean(np.abs(rp.fit_result))
            print(rp.fit_result)

            self._MWfreq = np.round(self._MWfreq+detuning_add-detuning, 6)
            print(self._MWfreq)
            savecalpara("MWfreq", self._MWfreq, self.calibfile)
            self.set_ddsfreq(self._MWfreq, channel=self._ch_MW, profile=1, ddschoice=self._dds_MW)
            self.set_ddsfreq(self._MWfreq, channel=self._ch_MW, profile=0, ddschoice=self._dds_MW)
            self.set_ddsfreq(self._MWfreq, channel=self._ch_MW, profile=2, ddschoice=self._dds_MW)

            print(self._MWfreq)

        del rp

        return self._MWfreq

    def update_MWpitime_calibration(self, profile, result):
        if profile == 0:
            self._MWpitimelist0 = result
            savecalpara("MWpitimelist0", self._MWpitimelist0, self.calibfile)
        elif profile==1:
            self._MWpitimelist1 = result
            savecalpara("MWpitimelist1", self._MWpitimelist1, self.calibfile)
        elif profile == 2:
            self._MWpitimelist2 = result
            savecalpara("MWpitimelist2", self._MWpitimelist2, self.calibfile)

    def MWpitimecal(self, profile=0):

        self.set_ddsfreq(self._MWfreq, channel=self._ch_MW, profile=0, ddschoice=self._dds_MW)
        self.set_ddsfreq(self._MWfreq, channel=self._ch_MW, profile=1, ddschoice=self._dds_MW)
        self.set_ddsfreq(self._MWfreq, channel=self._ch_MW, profile=2, ddschoice=self._dds_MW)

        if profile == 0:
            tscan = list(np.around(np.linspace(0.1, 3 * self._MWpitimelist0[0], 50), decimals=2))
            seq = ["*Microwave0(30)"]
        elif profile == 1:
            tscan = list(np.around(np.linspace(0.1, 3 * self._MWpitimelist1[0], 50), decimals=2))
            seq = ["freeMWp1(1)", "*Microwave1(30)"]
        elif profile == 2:
            tscan = list(np.around(np.linspace(0.1, 3 * self._MWpitimelist2[0], 50), decimals=2))
            seq = ["freeMWp2(1)", "*Microwave2(30)"]
        seq = self.append_shelving_sbc(seq, sbc=False, shelvingdet=0)

        rabi = self.selectseq(seq=seq)

        rp = rtplot.Rtplot(rabi, AutoRunStopFunc, xdata=tscan, fitfunc=Fit.rabi_fit, fileprefix="MWpitimecal", autoRun=True)
        if rp.fit_result is not None:
            result = rp.fit_result
            self.update_MWpitime_calibration(profile, result)
            print(rp.fit_result)

        del rp
        # self._timeunit["Microwave"] = np.mean(self._MWpitimelist)

        return result



    def MW_F_pitimecal(self, ion = [], profile=0):
        self.set_ddsfreq(self._MWfreq_F, channel=0, profile=0, ddschoice=self._dds_MW_F)
        seq_pre = self.Conversion_seq(direction="S-F")
        if profile==0:
            seq_MW = ["*MicrowaveFamp03432(1000)"] + ["free(1)"]
            pitime = np.mean(self._MWpitimelistF)
        elif profile==2:
            seq_MW = ["freeMWFp2(1)"] + ["*MicrowaveFamp03432p2(1000)"] + ["freeMWFp2(1)"]
            pitime = np.mean(self._MWpitimelistF2)
        else:
            print("No such profile, switch to profile0")
            seq_MW = ["*MicrowaveFamp03432(1000)"] + ["free(1)"]
            pitime = np.mean(self._MWpitimelistF)
        # seq_end = self.Conversion_seq(direction='F-S')
        seq_end = self.F_shelving_seq(n=1, profile=0)

        seq = seq_pre + seq_MW + seq_end

        seq = self.append_shelving_sbc(seq, sbc=False, shelvingdet=2)


        tscan = list(np.linspace(0.02, 3*pitime, 30))

        rabi = self.selectseq(seq=seq)
        if ion == []:
            rp = rtplot.Rtplot(rabi, AutoRunStopFunc, xdata=tscan, fitfunc=Fit.rabi_fit,
                               fileprefix="MWpitimecal", autoRun=True)
        else:
            rp = rtplot.Rtplot_SelectIon(rabi, AutoRunStopFunc, ion=ion, xdata=tscan, fitfunc=Fit.rabi_fit,
                               fileprefix="F-MWpitimecal", autoRun=True)
        if rp.fit_result is not None:
            result = rp.fit_result
            if profile==0:
                self._MWpitimelistF = result
                savecalpara("MWpitimelistF", self._MWpitimelistF, self.calibfile)
            elif profile==2:
                self._MWpitimelistF2 = result
                savecalpara("MWpitimelistF2", self._MWpitimelistF2, self.calibfile)
            else:
                self._MWpitimelistF = result
                savecalpara("MWpitimelistF", self._MWpitimelistF, self.calibfile)
            print(rp.fit_result)

        del rp

        return result



    def MW_F_pitimefinecal(self, N, ion=[], profile=0):
        n_pulse = 2 * N - 1
        self.set_ddsfreq(self._MWfreq_F, channel=0, profile=0, ddschoice=self._dds_MW_F)
        seq_pre = self.Conversion_seq(direction="S-F")
        if profile==0:
            seq_MW = ["free(25)"] + ["*MicrowaveFamp03432(1000)"] + ["free(25)"]
            time_span = self._MWpitimelistF[0] / n_pulse
            tscan = list(np.linspace(self._MWpitimelistF[0] - time_span / 2, self._MWpitimelistF[0] + time_span / 2, 15))
        elif profile==2:
            seq_MW = ["freeMWFp2(25)"] + ["*MicrowaveFamp03432p2(1000)"] + ["freeMWFp2(25)"]
            time_span = self._MWpitimelistF2[0] / n_pulse
            tscan = list(np.linspace(self._MWpitimelistF2[0] - time_span / 2, self._MWpitimelistF2[0] + time_span / 2, 15))
        else:
            print("No such prorfile, switch to profile0")
            seq_MW = ["free(25)"] + ["*MicrowaveFamp03432(1000)"] + ["free(25)"]
            time_span = self._MWpitimelistF[0] / n_pulse
            tscan = list(np.linspace(self._MWpitimelistF[0] - time_span / 2, self._MWpitimelistF[0] + time_span / 2, 15))
        # seq_end = self.Conversion_seq(direction='F-S')
        seq_end = self.F_shelving_seq(n=1, profile=0)

        seq = seq_pre + seq_MW*n_pulse + seq_end

        seq = self.append_shelving_sbc(seq, sbc=False, shelvingdet=2)




        rabi = self.selectseq(seq=seq)
        if ion==[]:
            rp = rtplot.Rtplot(rabi, AutoRunStopFunc, xdata=tscan, fitfunc=Fit.parabola_up_down(max_mode=False),
                               fileprefix="F-MWpitimecal", autoRun=True)
        else:
            rp = rtplot.Rtplot_SelectIon(rabi, AutoRunStopFunc, ion=ion, xdata=tscan, fitfunc=Fit.parabola_up_down(max_mode=False),
                               fileprefix="F-MWpitimecal", autoRun=True)
        if rp.fit_result is not None:
            result = rp.fit_result
            if profile==0:
                self._MWpitimelistF = result
                savecalpara("MWpitimelistF", self._MWpitimelistF, self.calibfile)
            elif profile ==2:
                self._MWpitimelistF2 = result
                savecalpara("MWpitimelistF2", self._MWpitimelistF2, self.calibfile)
            else:
                self._MWpitimelistF = result
                savecalpara("MWpitimelistF", self._MWpitimelistF, self.calibfile)

            print(rp.fit_result)

        del rp

        return result



    def MWpitimefinecal(self, N, profile=0):
        n_pulse = 2 * N - 1

        self.set_ddsfreq(self._MWfreq, channel=self._ch_MW, profile=0, ddschoice=self._dds_MW)
        self.set_ddsfreq(self._MWfreq, channel=self._ch_MW, profile=1, ddschoice=self._dds_MW)
        self.set_ddsfreq(self._MWfreq, channel=self._ch_MW, profile=2, ddschoice=self._dds_MW)

        if profile==0:
            time_span = self._MWpitimelist0[0]/ n_pulse
            tscan = list(np.linspace(self._MWpitimelist0[0]- time_span/2, self._MWpitimelist0[0] + time_span/2, 20))
            seq = ["free(25)", "*Microwave0(30)", "free(25)"] * n_pulse
        elif profile == 1:
            time_span = self._MWpitimelist1[0]/ n_pulse
            tscan = list(np.linspace(self._MWpitimelist1[0] - time_span / 2, self._MWpitimelist1[0] + time_span / 2, 20))
            seq = ["freeMWp1(25)", "*Microwave1(30)", "freeMWp1(25)"] * n_pulse
        elif profile == 2:
            time_span = self._MWpitimelist2[0] / n_pulse
            tscan = list(np.linspace(self._MWpitimelist2[0] - time_span / 2, self._MWpitimelist2[0] + time_span / 2, 20))
            seq = ["freeMWp2(25)", "*Microwave2(30)", "freeMWp2(25)"] * n_pulse

        seq = self.append_shelving_sbc(seq, sbc=False, shelvingdet=0)

        rabi = self.selectseq(seq=seq)
        rp = rtplot.Rtplot(rabi, AutoRunStopFunc, xdata=tscan, fitfunc=Fit.parabola_up_down(max_mode=True), fileprefix="MWpitimecal", autoRun=True)
        if rp.fit_result is not None:
            result = rp.fit_result
            self.update_MWpitime_calibration(profile, result)
            print(rp.fit_result)

        del rp
        # self._timeunit["Microwave"] = np.mean(self._MWpitimelist)

        return result

    def MWpihalftimefinecal(self, N, profile=0):
        n_pulse = 4 * N - 2
        time_span = self._MWpihalftimelist[0] / (n_pulse/2)

        self.set_ddsfreq(self._MWfreq, channel=self._ch_MW, profile=1, ddschoice=self._dds_MW)
        self.set_ddsfreq(self._MWfreq, channel=self._ch_MW, profile=0, ddschoice=self._dds_MW)
        tscan = list(np.linspace(self._MWpihalftimelist[0]- time_span/2, self._MWpihalftimelist[0] + time_span/2, 40))
        if profile==0:
            seq = ["free(25)", "*Microwave0(30)", "free(25)"] * n_pulse
        else:
            seq = ["freeMWp1(25)", "*Microwave1(30)", "freeMWp1(25)"] * n_pulse
        seq = self.append_shelving_sbc(seq, sbc=False, shelvingdet=0)

        rabi = self.selectseq(seq=seq)
        rp = rtplot.Rtplot(rabi, AutoRunStopFunc, xdata=tscan, fitfunc=Fit.parabola_up_down(max_mode=True), fileprefix="MWpihalftimecal", autoRun=True)
        if rp.fit_result is not None:
            self._MWpihalftimelist = rp.fit_result
            savecalpara("MWpihalftimelist", self._MWpihalftimelist, self.calibfile)
            print(rp.fit_result)

        del rp
        # self._timeunit["Microwave"] = np.mean(self._MWpitimelist)

        return self._MWpihalftimelist


    # def RabiRT(self, t, transition):
    #     # Run a pulse of duration t, on the given transition
    #     probe411 = SpectrumAWGSR.SingleRestartSpectrumAWG(self.awg_spectrum2)
    #     probe411.a_probe = self._amp_global_411
    #     probe411.f_probe = self._car_411_freqs[transition]
    #
    #     probe411.t_probe = t
    #
    #     probe411.update_waveform()
    #
    #     def rabi():
    #         self.seq.scanValue = t
    #         image = self._runseq(self.spellComb["CCDGlobal411Rabi"])
    #         state, thrrawdata = self._detectstateall(image)
    #         return state
    #
    #     def rabiscan(tscan):
    #         self.seq.scanValue = tscan
    #         probe411.update_time(tscan)
    #         image = self._runseq(self.spellComb["CCDGlobal411Rabi"])
    #         state, thrrawdata = self._detectstateall(image)
    #         return state
    #
    #
    #     assert transition in self._car_411_freqs.keys()
    #
    #     # rp = rtplot.Rtplot(rabiscan, AutoRunStopFunc, xdata=list(np.arange(0.1, 40, 0.4)))
    #     rp = rtplot.Rtplot(rabi, AutoRunStopFunc)



    def cal_411_transition(self, t_probe=50, amp=0.2, scanrange=0.06, transition="411_car_0"):
        # probe411 = SpectrumAWGSR.SingleRestartSpectrumAWG(self.awg_spectrum2)




        # freqscan = self.awg_freq_scan(probe411, self.spellComb["CCDGlobal411Rabi"], awg_channel=0)
        #
        # probe411.a_probe = amp
        #
        # probe411.t_probe = t_probe

        if transition == "411_car_m1":
            seq_name = "CCDGlobal411Rabim1"
            profile = 5
        elif transition == "411_car_p1":
            seq_name = "CCDGlobal411Rabip1"
            profile = 6
        else:
            seq_name = "CCDGlobal411Rabi0"
            profile = 4

        self.set_ddsamp(amp, channel=self._ch_global_411, profile=profile, ddschoice=self._dds_global_411)

        freqscan = self.select_calddschannel(profile, self._ch_global_411,
                                             ddschoice=self._dds_global_411,
                                             seq=self.spellComb[seq_name])

        self.seq.scanValue = t_probe

        car_411 = self._car_411_freqs[transition]
        freqscanrange = list(np.linspace(car_411 - scanrange/2, car_411 + scanrange/2, 40))
        rp = rtplot.Rtplot(freqscan, AutoRunStopFunc, xdata=freqscanrange, fitfunc=Fit.inv_gaussian_fit,
                           fileprefix='411globalfreqcal_' + transition, autoRun=True)
        if rp.fit_result is not None:
            savecalpara(transition, [np.mean(rp.fit_result), self._car_411_pitimes[transition], self._car_411_amps[transition]],
                        self.calibfile)
            self._car_411_freqs[transition] = np.mean(rp.fit_result)

            if transition != "411_car_m2" and transition != "411_car_p2":
                self.set_ddsfreq(np.mean(rp.fit_result), channel=self._ch_global_411, profile=profile, ddschoice=self._dds_global_411)

        del rp
        print(self._car_411_freqs[transition])



    def cal_411_fast(self, t_probe=50, amp=0.2, transition="411_car_0", n_points=30, ion=[]):
        '''
        #Need to calibrate the 0->0 carrier transition firstly,
        since the freq of the other transition is calculated from the 0->0 transition.
        scan range is fixed on [-0.01, 0.01]+car_freq
        we must be sure that we have calibrated all the three transition yesterday
        :param t_probe:
        :param amp:
        :param transition:
        :return:
        '''

        # probe411 = SpectrumAWGSR.SingleRestartSpectrumAWG(self.awg_spectrum2)
        #
        # freqscan = self.awg_freq_scan(probe411, self.spellComb["CCDGlobal411Rabi"], awg_channel=0)
        #
        #
        # probe411.a_probe = amp
        #
        # probe411.t_probe = t_probe
        if transition == "411_car_m1":
            seq_name = "CCDGlobal411Rabim1"
            profile = 5
        elif transition == "411_car_p1":
            seq_name = "CCDGlobal411Rabip1"
            profile = 6
        else:
            seq_name = "CCDGlobal411Rabi0"
            profile = 4

        self.set_ddsamp(amp, channel=self._ch_global_411, profile=profile, ddschoice=self._dds_global_411)

        freqscan = self.select_calddschannel(profile, self._ch_global_411,
                                             ddschoice=self._dds_global_411,
                                             seq=self.spellComb[seq_name])

        self.seq.scanValue = t_probe

        car_411 = self._car_411_freqs["411_car_0"]+self._car_411_relative_freqs[transition]
        freqscanrange = list(np.linspace(car_411 - 0.06, car_411 + 0.06, n_points))
        if ion==[]:
            rp = rtplot.Rtplot(freqscan, AutoRunStopFunc, xdata=freqscanrange, fitfunc=Fit.inv_gaussian_fit,
                               fileprefix='411globalfreqcal_' + transition, autoRun=True)
        else:
            rp = rtplot.Rtplot_SelectIon(freqscan, AutoRunStopFunc, ion=ion, xdata=freqscanrange, fitfunc=Fit.inv_gaussian_fit,
                               fileprefix='411globalfreqcal_' + transition, autoRun=True)

        if rp.fit_result is not None:
            self._car_411_freqs[transition] = np.mean(rp.fit_result)
            savecalpara(transition, [np.mean(rp.fit_result), self._car_411_pitimes[transition], self._car_411_amps[transition]],
                        self.calibfile)

            if transition != "411_car_m2" and transition != "411_car_p2":
                self.set_ddsfreq(np.mean(rp.fit_result), channel=self._ch_global_411, profile=profile, ddschoice=self._dds_global_411)

        del rp
        print(self._car_411_freqs[transition])




    def update_411_relative_freq(self):
        for transition in self._car_411_relative_freqs.keys():
            self._car_411_relative_freqs[transition] = self._car_411_freqs[transition]-self._car_411_freqs["411_car_0"]

        savecalpara("411_relative_freq", self._car_411_relative_freqs, self.calibfile)

        return self._car_411_relative_freqs


    def update_411_freqs(self):
        for transition in self._car_411_relative_freqs.keys():
            self._car_411_freqs[transition] = self._car_411_freqs["411_car_0"] + self._car_411_relative_freqs[transition]
            savecalpara(transition, [self._car_411_freqs[transition], self._car_411_pitimes[transition], self._car_411_amps[transition]], self.calibfile)

        return self._car_411_freqs



    def cal_411_freq(self, f_center, f_span = 0.1, t_probe=50, amp=0.2, N_points=100, autoRun=True):
        # probe411 = SpectrumAWGSR.SingleRestartSpectrumAWG(self.awg_spectrum2)
        #
        # freqscan = self.awg_freq_scan(probe411, self.spellComb["CCDGlobal411Rabi"], awg_channel=0)
        #
        # probe411.a_probe = amp
        #
        # probe411.t_probe = t_probe

        seq_name = "CCDGlobal411Rabi0"
        profile = 4

        self.set_ddsamp(amp, channel=self._ch_global_411, profile=profile, ddschoice=self._dds_global_411)

        freqscan = self.select_calddschannel(profile, self._ch_global_411,
                                             ddschoice=self._dds_global_411,
                                             seq=self.spellComb[seq_name])


        self.seq.scanValue = t_probe

        freqscanrange = list(np.linspace(f_center - f_span/2, f_center + f_span/2, N_points))
        rp = rtplot.Rtplot(freqscan, AutoRunStopFunc, xdata=freqscanrange, fitfunc=Fit.inv_gaussian_fit,
                           fileprefix='411globalfreq', autoRun=autoRun)
        if rp.fit_result is not None:
            result = np.mean(rp.fit_result)
        else:
            result = 0
        del rp

        self.set_ddsfreq(self._car_411_freqs["411_car_0"], channel=self._ch_global_411, profile=profile,
                         ddschoice=self._dds_global_411)
        self.set_ddsamp(self._car_411_amps["411_car_0"], channel=self._ch_global_411, profile=profile,
                         ddschoice=self._dds_global_411)

        return result



    def time_scan_411(self, t_list, freq, amp, fileprefix='411Rabi', autoRun=True):
        # probe411 = SpectrumAWGSR.SingleRestartSpectrumAWG(self.awg_spectrum2)
        # rabi = self.awg_time_scan(probe411, self.spellComb["CCDGlobal411Rabi"])
        #
        # probe411.f_probe = freq
        # probe411.a_probe = amp

        self.set_ddsamp(amp, channel=self._ch_global_411, profile=4,
                        ddschoice=self._dds_global_411)

        self.set_ddsfreq(freq, channel=self._ch_global_411, profile=4,
                         ddschoice=self._dds_global_411)

        rabi = self.selectseq(seq=self.spellComb["CCDGlobal411Rabi0"])


        rp = rtplot.Rtplot(rabi, AutoRunStopFunc,
                           xdata=t_list,
                           # fitfunc=Fit.rabi_fit,
                           fileprefix=fileprefix, autoRun=autoRun)
        # print(rp.fit_result)
        # result = np.mean(rp.fit_result)

        # result = rp.ydatadraw

        del rp

        self.set_ddsfreq(self._car_411_freqs["411_car_0"], channel=self._ch_global_411, profile=4,
                         ddschoice=self._dds_global_411)
        self.set_ddsamp(self._car_411_amps["411_car_0"], channel=self._ch_global_411, profile=4,
                        ddschoice=self._dds_global_411)
        # return result



    def cal_411_pitime(self, transition="411_car_0", n_pulse=1, ion=[0]):
        # probe411 = SpectrumAWGSR.SingleRestartSpectrumAWG(self.awg_spectrum2)
        # car_411 = self._car_411_freqs[transition]
        #
        # def rabi(t):
        #     # Configure the AWG waveform
        #     probe411.reset_waveform()
        #     for _ in range(n_pulse):
        #         probe411.add_pulse_to_waveform(car_411, self._car_411_amps[transition], 0, t)
        #         probe411.add_pulse_to_waveform(0, 0, 0, 1)  # 1 us gap between pulses
        #
        #     probe411.update_waveform()
        #     # Configure the sequencer
        #     seq = ["Frepump(5000)", "free(1)", "pumping(50)", "freeNE(1)"]
        #     seq += ["GlobalNconv2(%f)" % (self._delay_spectrum_global), "freeNE(%f)"%(n_pulse * (t+1))]
        #     seq += ["CCD(155)", "ccddetcooling(1000)", "detectionfree(1000)"]
        #
        #     image = self._runseq(Seq=seq)
        #     state, thrrawdata = self._detectstateall(image)
        #
        #     return state, thrrawdata



        # rabi = self.awg_time_scan(probe411, self.spellComb["CCDGlobal411Rabi"])
        #
        # probe411.a_probe = self._amp_global_411
        #
        #
        # probe411.f_probe = car_411



        time_span = self._car_411_pitimes[transition]/n_pulse
        if transition == "411_car_m1":
            seq = ["freeNEm411(1)"]
            seq = seq + ["*GlobalNconvm2(1)", "freeNEm411(2)"]*n_pulse
            profile = 5
        elif transition == "411_car_p1":
            seq = ["freeNEp411(1)"]
            seq = seq + ["*GlobalNconvp2(1)", "freeNEp411(2)"] * n_pulse
            profile = 6
        else:
            seq = ["freeNE(1)"]
            seq = seq + ["*GlobalNconv2(1)", "freeNE(2)"] * n_pulse
            profile = 4


        seq_probe = self.append_shelving_sbc(seq, sbc=False, shelvingdet=2)

        self.set_ddsfreq(self._car_411_freqs[transition], channel=self._ch_global_411, profile=profile,
                         ddschoice=self._dds_global_411)

        self.set_ddsamp(self._car_411_amps[transition], channel=self._ch_global_411, profile=profile,
                        ddschoice=self._dds_global_411)

        rabi = self.selectseq(seq=seq_probe)

        rp = rtplot.Rtplot_SelectIon(rabi, AutoRunStopFunc, ion=ion,
                           # xdata=list(np.linspace(0.1, 4 * self._car_411_pitimes[transition], 30)),
                           xdata=list(np.linspace(self._car_411_pitimes[transition]-time_span/3,
                                                  self._car_411_pitimes[transition]+time_span/3, 15)),
                           fitfunc=Fit.parabola_up_down(False),
                           fileprefix='%s_pi-time'%transition, autoRun=True)

        if rp.fit_result is not None:
            savecalpara(transition, [self._car_411_freqs[transition], np.mean(rp.fit_result), self._car_411_amps[transition]],
                        self.calibfile)
            self._car_411_pitimes[transition] = np.mean(rp.fit_result)
            print(rp.fit_result)
            print(np.std(rp.fit_result))

        del rp
        return self._car_411_pitimes[transition]


    def cal_3432_freq(self, amp=0.85, t3432=0.4, scanrange=0.3, profile=0, state=0):
        # probe411 = SpectrumAWGSR.SingleRestartSpectrumAWG(self.awg_spectrum2)
        if profile==0:
            if state==0:
                # probe411.a_probe = self._car_411_amps["411_car_0"]
                # probe411.f_probe = self._car_411_freqs["411_car_0"]
                #
                # probe411.t_probe = self._car_411_pitimes["411_car_0"]
                #
                #
                # probe411.update_probe()

                self.set_ddsfreq(self._car_411_freqs["411_car_0"], channel=self._ch_global_411, profile=4,
                                 ddschoice=self._dds_global_411)

                self.set_ddsamp(self._car_411_amps["411_car_0"], channel=self._ch_global_411, profile=4,
                                ddschoice=self._dds_global_411)

                shelving_pulses = ["freeNE(1)"]

                # 0 -> 0 transition
                # trigger the awg to play the waveform
                shelving_pulses.append("GlobalNconv2(%f)" % (self._car_411_pitimes["411_car_0"]))
                # shelving_pulses.append("freeNE(%f)" % self._car_411_pitimes["411_car_0"])  # simply a placeholder for the pi-pulse
                shelving_pulses.append("freeNE(1.5)")
                shelving_pulses.append("Laser3432p0(%.2f)"%t3432)
                shelving_pulses.append("free(1.5)")
                shelving_pulses.append("Laser976(20)")
                scanseq = self.Doppler_cooling_seq(5000) + shelving_pulses +self.CCDcoolingdet_seq()

                self.set_ddsamp(amp, channel=self._ch_3432, profile=0, ddschoice=self._dds_3432)
                freq_range = list(np.arange(self._freq3432p0-scanrange/2, self._freq3432p0+scanrange/2, 0.02))
                freqscan = self.select_calddschannel(0, self._ch_3432, ddschoice=self._dds_3432, seq=scanseq)

                rp = rtplot.Rtplot(freqscan, AutoRunStopFunc, xdata=freq_range, fitfunc=Fit.inv_gaussian_fit, fileprefix="3432freq_cal", autoRun=True)

                if rp.fit_result is not None:
                    result = np.mean(rp.fit_result)
                    print(result)
                    savecalpara("3432freq0", result, self.calibfile)
                    self._freq3432p0 = result
                    self.set_ddsfreq(self._freq3432p0, channel=self._ch_3432, profile=0, ddschoice=1)

                del rp

                self.set_ddsamp(self._amp_3432, channel=self._ch_3432, profile=0, ddschoice=1)
            else:
                # probe411.a_probe = self._car_411_amps["411_car_0"]
                # probe411.f_probe = self._car_411_freqs["411_car_0"]
                #
                # probe411.t_probe = self._car_411_pitimes["411_car_0"]
                #
                #
                # probe411.update_probe()

                self.set_ddsfreq(self._car_411_freqs["411_car_0"], channel=self._ch_global_411, profile=4,
                                 ddschoice=self._dds_global_411)

                self.set_ddsamp(self._car_411_amps["411_car_0"], channel=self._ch_global_411, profile=4,
                                ddschoice=self._dds_global_411)

                shelving_pulses = self.MW_seq(profile=0, t=1) + ["free(1)"]

                # 0 -> 0 transition
                # trigger the awg to play the waveform
                shelving_pulses.append("GlobalConv2(%f)" % (self._CEOMpitime))
                # shelving_pulses.append("freeNE(%f)" % self._car_411_pitimes["411_car_0"])  # simply a placeholder for the pi-pulse
                shelving_pulses.append("free(1.5)")
                shelving_pulses.append("Laser3432p0(%.2f)" % t3432)
                shelving_pulses.append("free(1.5)")
                shelving_pulses.append("Laser976(20)")
                scanseq = self.Doppler_cooling_seq(5000) + shelving_pulses + self.CCDcoolingdet_seq()

                self.set_ddsamp(amp, channel=self._ch_3432, profile=0, ddschoice=self._dds_3432)
                freq_range = list(np.arange(self._freq3432p0 - scanrange / 2, self._freq3432p0 + scanrange / 2, 0.02))
                freqscan = self.select_calddschannel(0, self._ch_3432, ddschoice=self._dds_3432, seq=scanseq)

                rp = rtplot.Rtplot(freqscan, AutoRunStopFunc, xdata=freq_range, fitfunc=Fit.inv_gaussian_fit,
                                   fileprefix="3432freq_cal", autoRun=True)

                if rp.fit_result is not None:
                    result = np.mean(rp.fit_result)
                    print(result)
                    savecalpara("3432freq3", result, self.calibfile)
                    self._freq3432p3 = result
                    # self.set_ddsfreq(self._freq3432p0, channel=self._ch_3432, profile=0, ddschoice=1)

                del rp

                self.set_ddsamp(self._amp_3432, channel=self._ch_3432, profile=0, ddschoice=1)


        elif profile==1:
            # print("No other profile now")
            self.set_ddsfreq(self._car_411_freqs["411_car_m1"], channel=self._ch_global_411, profile=5,
                             ddschoice=self._dds_global_411)

            self.set_ddsamp(self._car_411_amps["411_car_m1"], channel=self._ch_global_411, profile=5,
                            ddschoice=self._dds_global_411)

            shelving_pulses = ["freeNEm411(1)"]
            # shelving_pulses = ["freeNE(1)"]
            # 0 -> 0 transition
            # trigger the awg to play the waveform
            shelving_pulses.append("GlobalNconvm2(%f)" % (self._car_411_pitimes["411_car_m1"]))
            # shelving_pulses.append("GlobalNconv2(%f)" % (self._car_411_pitimes["411_car_0"]))
            # shelving_pulses.append("freeNE(%f)" % self._car_411_pitimes["411_car_0"])  # simply a placeholder for the pi-pulse
            shelving_pulses.append("free3432(1.5)")
            shelving_pulses.append("Laser3432p1(%.2f)" % t3432)
            shelving_pulses.append("free(1.5)")
            shelving_pulses.append("Laser976(20)")
            scanseq = self.Doppler_cooling_seq(5000) + shelving_pulses + self.CCDcoolingdet_seq()

            self.set_ddsamp(amp, channel=self._ch_3432, profile=2, ddschoice=self._dds_3432)
            freq_range = list(np.arange(self._freq3432p1 - scanrange / 2, self._freq3432p1 + scanrange / 2, 0.02))
            freqscan = self.select_calddschannel(2, self._ch_3432, ddschoice=self._dds_3432, seq=scanseq)

            rp = rtplot.Rtplot(freqscan, AutoRunStopFunc, xdata=freq_range, fitfunc=Fit.inv_gaussian_fit,
                               fileprefix="3432freq_cal", autoRun=True)

            if rp.fit_result is not None:
                result = np.mean(rp.fit_result)
                print(result)
                savecalpara("3432freq1", result, self.calibfile)
                self._freq3432p1 = result
                self.set_ddsfreq(self._freq3432p1, channel=self._ch_3432, profile=2, ddschoice=1)

            del rp

            self.set_ddsamp(self._amp_3432, channel=self._ch_3432, profile=2, ddschoice=1)

        else:
            self.set_ddsfreq(self._car_411_freqs["411_car_p1"], channel=self._ch_global_411, profile=6,
                             ddschoice=self._dds_global_411)

            self.set_ddsamp(self._car_411_amps["411_car_p1"], channel=self._ch_global_411, profile=6,
                            ddschoice=self._dds_global_411)

            shelving_pulses = ["freeNEp411(1)"]
            # 0 -> 0 transition
            # trigger the awg to play the waveform
            shelving_pulses.append("GlobalNconvp2(%f)" % (self._car_411_pitimes["411_car_p1"]))
            # shelving_pulses.append("freeNE(%f)" % self._car_411_pitimes["411_car_0"])  # simply a placeholder for the pi-pulse
            shelving_pulses.append("freeNE3432(1)")
            shelving_pulses.append("freeNE3432p2(1)")
            # shelving_pulses.append("free3432(1)")
            shelving_pulses.append("Laser3432p2(%.2f)" % t3432)
            shelving_pulses.append("freeNE3432p2(1.5)")
            shelving_pulses.append("Laser976(20)")
            scanseq = self.Doppler_cooling_seq(5000) + shelving_pulses + self.CCDcoolingdet_seq()

            self.set_ddsamp(amp, channel=self._ch_3432, profile=3, ddschoice=self._dds_3432)
            freq_range = list(np.arange(self._freq3432p2 - scanrange / 2, self._freq3432p2 + scanrange / 2, 0.02))
            freqscan = self.select_calddschannel(3, self._ch_3432, ddschoice=self._dds_3432, seq=scanseq)

            rp = rtplot.Rtplot(freqscan, AutoRunStopFunc, xdata=freq_range, fitfunc=Fit.inv_gaussian_fit,
                               fileprefix="3432freq_cal", autoRun=True)

            if rp.fit_result is not None:
                result = np.mean(rp.fit_result)
                print(result)
                savecalpara("3432freq2", result, self.calibfile)
                self._freq3432p2 = result
                self.set_ddsfreq(self._freq3432p2, channel=self._ch_3432, profile=3, ddschoice=1)

            del rp

            self.set_ddsamp(self._amp_3432, channel=self._ch_3432, profile=3, ddschoice=1)

        return result




    def cal_3432_pitime(self, profile=0, ion=[0], state=0):
        # probe411 = SpectrumAWGSR.SingleRestartSpectrumAWG(self.awg_spectrum2)

        if profile==0:
            if state == 0:
                self.set_ddsfreq(self._freq3432p0, channel=self._ch_3432, profile=0, ddschoice=self._dds_3432)
                self.set_ddsamp(self._amp_3432, channel=self._ch_3432, profile=0, ddschoice=self._dds_3432)


                self.set_ddsfreq(self._car_411_freqs["411_car_0"], channel=self._ch_global_411, profile=4,
                                 ddschoice=self._dds_global_411)

                self.set_ddsamp(self._car_411_amps["411_car_0"], channel=self._ch_global_411, profile=4,
                                ddschoice=self._dds_global_411)
                # probe411.a_probe = self._car_411_amps["411_car_0"]
                # probe411.f_probe = self._car_411_freqs["411_car_0"]
                #
                # probe411.t_probe = self._car_411_pitimes["411_car_0"]
                # probe411.update_probe()

                shelving_pulses = ["freeNE(1)"]

                # 0 -> 0 transition
                # trigger the awg to play the waveform
                shelving_pulses.append("GlobalNconv2(%f)" % (self._car_411_pitimes["411_car_0"]))
                # shelving_pulses.append("freeNE(%f)" %self._car_411_pitimes["411_car_0"])  # simply a placeholder for the pi-pulse
                shelving_pulses.append("freeNE(1.5)")
                shelving_pulses.append("*Laser3432p0(0.1)")
                shelving_pulses.append("free(1.5)")
                shelving_pulses.append("Laser976(20)")
                scanseq = self.Doppler_cooling_seq(5000) + shelving_pulses + self.CCDcoolingdet_seq()


                rabi3432 = self.selectseq(seq=scanseq)
                rp = rtplot.Rtplot_SelectIon(rabi3432, AutoRunStopFunc, ion=ion, xdata=list(np.linspace(0.02, 4 * self._pitime3432p0, 40)),
                                   fitfunc=Fit.rabi_fit,
                                   fileprefix='3432Rabip0', autoRun=True)
                if rp.fit_result is not None:
                    savecalpara("3432pitime0", np.mean(rp.fit_result), self.calibfile)
                    self._pitime3432p0 = np.mean(rp.fit_result)
                    print(rp.fit_result)
                    print(np.std(rp.fit_result))

                del rp
            else:
                self.set_ddsfreq(self._freq3432p3, channel=self._ch_3432, profile=0, ddschoice=self._dds_3432)
                self.set_ddsamp(self._amp_3432, channel=self._ch_3432, profile=0, ddschoice=self._dds_3432)

                self.set_ddsfreq(self._car_411_freqs["411_car_0"], channel=self._ch_global_411, profile=4,
                                 ddschoice=self._dds_global_411)

                self.set_ddsamp(self._car_411_amps["411_car_0"], channel=self._ch_global_411, profile=4,
                                ddschoice=self._dds_global_411)
                # probe411.a_probe = self._car_411_amps["411_car_0"]
                # probe411.f_probe = self._car_411_freqs["411_car_0"]
                #
                # probe411.t_probe = self._car_411_pitimes["411_car_0"]
                # probe411.update_probe()

                shelving_pulses = self.MW_seq(profile=0, t=1) + ["free(1)"]

                # 0 -> 0 transition
                # trigger the awg to play the waveform
                shelving_pulses.append("GlobalConv2(%f)" % (self._CEOMpitime))
                # shelving_pulses.append("freeNE(%f)" %self._car_411_pitimes["411_car_0"])  # simply a placeholder for the pi-pulse
                shelving_pulses.append("free(1.5)")
                shelving_pulses.append("*Laser3432p0(0.1)")
                shelving_pulses.append("free(1.5)")
                shelving_pulses.append("Laser976(20)")
                scanseq = self.Doppler_cooling_seq(5000) + shelving_pulses + self.CCDcoolingdet_seq()

                rabi3432 = self.selectseq(seq=scanseq)
                rp = rtplot.Rtplot_SelectIon(rabi3432, AutoRunStopFunc, ion=ion,
                                             xdata=list(np.linspace(0.02, 4 * self._pitime3432p5, 40)),
                                             fitfunc=Fit.rabi_fit,
                                             fileprefix='3432Rabip5', autoRun=True)
                if rp.fit_result is not None:
                    savecalpara("3432pitime5", np.mean(rp.fit_result), self.calibfile)
                    self._pitime3432p5 = np.mean(rp.fit_result)
                    print(rp.fit_result)
                    print(np.std(rp.fit_result))

                del rp
        elif profile==1:
            # print("No other profile now!")
            self.set_ddsfreq(self._freq3432p1, channel=self._ch_3432, profile=2, ddschoice=self._dds_3432)
            self.set_ddsamp(self._amp_3432, channel=self._ch_3432, profile=2, ddschoice=self._dds_3432)

            self.set_ddsfreq(self._car_411_freqs["411_car_m1"], channel=self._ch_global_411, profile=5,
                             ddschoice=self._dds_global_411)

            self.set_ddsamp(self._car_411_amps["411_car_m1"], channel=self._ch_global_411, profile=5,
                            ddschoice=self._dds_global_411)
            # probe411.a_probe = self._car_411_amps["411_car_0"]
            # probe411.f_probe = self._car_411_freqs["411_car_0"]
            #
            # probe411.t_probe = self._car_411_pitimes["411_car_0"]
            # probe411.update_probe()

            shelving_pulses = ["freeNEm411(1)"]
            # shelving_pulses = ["freeNE(1)"]
            # 0 -> 0 transition
            # trigger the awg to play the waveform
            shelving_pulses.append("GlobalNconvm2(%f)" % (self._car_411_pitimes["411_car_m1"]))
            # shelving_pulses.append("GlobalNconv2(%f)" % (self._car_411_pitimes["411_car_0"]))
            # shelving_pulses.append("freeNE(%f)" %self._car_411_pitimes["411_car_0"])  # simply a placeholder for the pi-pulse
            shelving_pulses.append("free3432(1.5)")
            shelving_pulses.append("*Laser3432p1(0.1)")
            shelving_pulses.append("free(1.5)")
            shelving_pulses.append("Laser976(20)")
            scanseq = self.Doppler_cooling_seq(5000) + shelving_pulses + self.CCDcoolingdet_seq()

            rabi3432 = self.selectseq(seq=scanseq)
            rp = rtplot.Rtplot_SelectIon(rabi3432, AutoRunStopFunc, ion=ion,
                                         xdata=list(np.linspace(0.02, 4 * self._pitime3432p1, 40)),
                                         fitfunc=Fit.rabi_fit,
                                         fileprefix='3432Rabip1', autoRun=True)
            if rp.fit_result is not None:
                savecalpara("3432pitime1", np.mean(rp.fit_result), self.calibfile)
                self._pitime3432p1 = np.mean(rp.fit_result)
                print(rp.fit_result)
                print(np.std(rp.fit_result))

            del rp

        elif profile==2:
            self.set_ddsfreq(self._freq3432p2, channel=self._ch_3432, profile=3, ddschoice=self._dds_3432)
            self.set_ddsamp(self._amp_3432, channel=self._ch_3432, profile=3, ddschoice=self._dds_3432)

            self.set_ddsfreq(self._car_411_freqs["411_car_p1"], channel=self._ch_global_411, profile=6,
                             ddschoice=self._dds_global_411)

            self.set_ddsamp(self._car_411_amps["411_car_p1"], channel=self._ch_global_411, profile=6,
                            ddschoice=self._dds_global_411)
            # probe411.a_probe = self._car_411_amps["411_car_0"]
            # probe411.f_probe = self._car_411_freqs["411_car_0"]
            #
            # probe411.t_probe = self._car_411_pitimes["411_car_0"]
            # probe411.update_probe()

            shelving_pulses = ["freeNEp411(1)"]

            # 0 -> 0 transition
            # trigger the awg to play the waveform
            shelving_pulses.append("GlobalNconvp2(%f)" % (self._car_411_pitimes["411_car_p1"]))
            # shelving_pulses.append("freeNE(%f)" %self._car_411_pitimes["411_car_0"])  # simply a placeholder for the pi-pulse
            # shelving_pulses.append("freeNE(1)")
            shelving_pulses.append("freeNE3432(1)")
            shelving_pulses.append("freeNE3432p2(1)")
            shelving_pulses.append("*Laser3432p2(0.1)")
            shelving_pulses.append("free3432(1.5)")
            shelving_pulses.append("Laser976(20)")
            scanseq = self.Doppler_cooling_seq(5000) + shelving_pulses + self.CCDcoolingdet_seq()

            rabi3432 = self.selectseq(seq=scanseq)
            rp = rtplot.Rtplot_SelectIon(rabi3432, AutoRunStopFunc, ion=ion,
                                         xdata=list(np.linspace(0.02, 4 * self._pitime3432p2, 40)),
                                         fitfunc=Fit.rabi_fit,
                                         fileprefix='3432Rabip2', autoRun=True)
            if rp.fit_result is not None:
                savecalpara("3432pitime2", np.mean(rp.fit_result), self.calibfile)
                self._pitime3432p2 = np.mean(rp.fit_result)
                print(rp.fit_result)
                print(np.std(rp.fit_result))

            del rp

        else:
            if state==0:
                self.set_ddsfreq(self._freq3432p0, channel=self._ch_3432, profile=4, ddschoice=self._dds_3432)
                self.set_ddsamp(self._amp_3432_low, channel=self._ch_3432, profile=4, ddschoice=self._dds_3432)

                self.set_ddsfreq(self._car_411_freqs["411_car_0"], channel=self._ch_global_411, profile=4,
                                 ddschoice=self._dds_global_411)

                self.set_ddsamp(self._car_411_amps["411_car_0"], channel=self._ch_global_411, profile=4,
                                ddschoice=self._dds_global_411)
                # probe411.a_probe = self._car_411_amps["411_car_0"]
                # probe411.f_probe = self._car_411_freqs["411_car_0"]
                #
                # probe411.t_probe = self._car_411_pitimes["411_car_0"]
                # probe411.update_probe()

                shelving_pulses = ["freeNE(1)"]

                # 0 -> 0 transition
                # trigger the awg to play the waveform
                shelving_pulses.append("GlobalNconv2(%f)" % (self._car_411_pitimes["411_car_0"]))
                # shelving_pulses.append("freeNE(%f)" %self._car_411_pitimes["411_car_0"])  # simply a placeholder for the pi-pulse
                shelving_pulses.append("freeNE3432p4(1.5)")
                shelving_pulses.append("*Laser3432p4(0.1)")
                shelving_pulses.append("free(1.5)")
                shelving_pulses.append("Laser976(20)")
                scanseq = self.Doppler_cooling_seq(5000) + shelving_pulses + self.CCDcoolingdet_seq()

                rabi3432 = self.selectseq(seq=scanseq)
                rp = rtplot.Rtplot_SelectIon(rabi3432, AutoRunStopFunc, ion=ion,
                                             xdata=list(np.linspace(0.02, 4 * self._pitime3432p4, 40)),
                                             fitfunc=Fit.rabi_fit,
                                             fileprefix='3432Rabip5', autoRun=True)
                if rp.fit_result is not None:
                    savecalpara("3432pitime4", np.mean(rp.fit_result), self.calibfile)
                    self._pitime3432p4 = np.mean(rp.fit_result)
                    print(rp.fit_result)
                    print(np.std(rp.fit_result))

                del rp
            else:
                self.set_ddsfreq(self._freq3432p3, channel=self._ch_3432, profile=4, ddschoice=self._dds_3432)
                self.set_ddsamp(self._amp_3432_low, channel=self._ch_3432, profile=4, ddschoice=self._dds_3432)

                self.set_ddsfreq(self._car_411_freqs["411_car_0"], channel=self._ch_global_411, profile=4,
                                 ddschoice=self._dds_global_411)

                self.set_ddsamp(self._car_411_amps["411_car_0"], channel=self._ch_global_411, profile=4,
                                ddschoice=self._dds_global_411)
                # probe411.a_probe = self._car_411_amps["411_car_0"]
                # probe411.f_probe = self._car_411_freqs["411_car_0"]
                #
                # probe411.t_probe = self._car_411_pitimes["411_car_0"]
                # probe411.update_probe()

                shelving_pulses = self.MW_seq(profile=0, t=1) + ["free(1)"]

                # 0 -> 0 transition
                # trigger the awg to play the waveform
                shelving_pulses.append("GlobalConv2(%f)" % (self._CEOMpitime))
                # shelving_pulses.append("freeNE(%f)" %self._car_411_pitimes["411_car_0"])  # simply a placeholder for the pi-pulse
                shelving_pulses.append("freeNE3432p4(1.5)")
                shelving_pulses.append("*Laser3432p4(0.1)")
                shelving_pulses.append("free(1.5)")
                shelving_pulses.append("Laser976(20)")
                scanseq = self.Doppler_cooling_seq(5000) + shelving_pulses + self.CCDcoolingdet_seq()

                rabi3432 = self.selectseq(seq=scanseq)
                rp = rtplot.Rtplot_SelectIon(rabi3432, AutoRunStopFunc, ion=ion,
                                             xdata=list(np.linspace(0.02, 4 * self._pitime3432p5, 40)),
                                             fitfunc=Fit.rabi_fit,
                                             fileprefix='3432Rabip5', autoRun=True)
                if rp.fit_result is not None:
                    savecalpara("3432pitime5", np.mean(rp.fit_result), self.calibfile)
                    self._pitime3432p5 = np.mean(rp.fit_result)
                    print(rp.fit_result)
                    print(np.std(rp.fit_result))

                del rp





    # def autocal_411_3432(self):
    #     probe411 = SpectrumAWG.ProbeSequence(self.awg_spectrum)
    #
    #     freqscan = self.awg_freq_scan(probe411, self.spellComb["CCDGlobal411Rabi"])
    #     rabi = self.awg_time_scan(probe411, self.spellComb["CCDGlobal411Rabi"])
    #     probe411.t_probe = self._tcal_global411
    #     self.seq.scanValue = self._tcal_global411
    #
    #
    #     # Calibrate the carrier frequencies
    #     for transition in self._car_411_freqs.keys():
    #         print(transition)
    #         car_411 = self._car_411_freqs[transition]
    #         amp_411 = self._car_411_amps[transition]
    #
    #         probe411.a_probe = amp_411
    #
    #         freqscanrange = list(np.arange(car_411-0.07, car_411+0.07, 0.005))
    #         rp = rtplot.Rtplot(freqscan, AutoRunStopFunc, xdata=freqscanrange, fitfunc=Fit.inv_gaussian_fit,
    #                            fileprefix='411globalfreqcal_'+transition, autoRun=True)
    #         if rp.fit_result is not None:
    #             savecalpara(transition, [np.mean(rp.fit_result), self._car_411_pitimes[transition]], self.calibfile)
    #             self._car_411_freqs[transition] = np.mean(rp.fit_result)
    #             print(rp.fit_result)
    #             print(np.std(rp.fit_result))
    #         del rp
    #
    #     # Calibrate the pi-time of each transition
    #     probe411.a_probe = self._amp_global_411
    #
    #     for transition in self._car_411_freqs.keys():
    #         car_411 = self._car_411_freqs[transition]
    #         probe411.f_probe = car_411
    #
    #         rp = rtplot.Rtplot(rabi, AutoRunStopFunc, xdata=list(np.linspace(0.1, 4 * self._car_411_pitimes[transition], 40)),
    #                            fitfunc=Fit.rabi_fit,
    #                            fileprefix='411Rabi', autoRun=True)
    #         if rp.fit_result is not None:
    #             savecalpara(transition, [self._car_411_freqs[transition], np.mean(rp.fit_result)], self.calibfile)
    #             self._car_411_pitimes[transition] = np.mean(rp.fit_result)
    #             print(rp.fit_result)
    #             print(np.std(rp.fit_result))
    #         del rp
    #
    #     # Calibrate the 3432 pi-time
    #     probe411.a_probe = self._amp_global_411
    #     probe411.f_probe = self._car_411_freqs["411_car_0"]
    #     probe411.t_probe = self._car_411_pitimes["411_car_0"]
    #     probe411.update_waveform()
    #
    #     shelving_pulses = []
    #     # 0 -> 0 transition
    #     # trigger the awg to play the waveform
    #     shelving_pulses.append("Global411(%f)" % (self._delay_spectrum_awg + self._jitter_spectrum_awg))
    #     shelving_pulses.append("free(%f)" % self._car_411_pitimes["411_car_0"]) # simply a placeholder for the pi-pulse
    #     shelving_pulses.append("free(1)")
    #     shelving_pulses.append("*Laser3432(0.1)")
    #     scanseq = ["Frepump(5000)",
    #                "free(1)",
    #                "pumping(20)",
    #                "free(1)"
    #                ] + shelving_pulses + \
    #               ["Laser976(10)",
    #                "CCD(155)",
    #                "cooling(1000)",
    #                "detectionfree(200)"]
    #
    #     rabi3432 = self.selectseq(seq=scanseq)
    #     rp = rtplot.Rtplot(rabi3432, AutoRunStopFunc, xdata=list(np.linspace(0.02, 4 * self._pitime3432p0, 40)),
    #                        fitfunc=Fit.rabi_fit,
    #                        fileprefix='3432Rabi', autoRun=True)
    #     if rp. fit_result is not None:
    #         savecalpara("3432pitime0", np.mean(rp.fit_result), self.calibfile)
    #         self._pitime3432p0 = np.mean(rp.fit_result)
    #         print(rp.fit_result)
    #         print(np.std(rp.fit_result))
    #
    #     del rp
    #
    #     return 0

    def cal_3432_pitime_fine(self, n_pulse=3, profile=0, ion=[], state=0):
        if profile==0:
            if state==0:
                self.set_ddsfreq(self._freq3432p0, channel=self._ch_3432, profile=0, ddschoice=self._dds_3432)
                self.set_ddsamp(self._amp_3432, channel=self._ch_3432, profile=0, ddschoice=self._dds_3432)


                self.set_ddsfreq(self._car_411_freqs["411_car_0"], channel=self._ch_global_411, profile=4,
                                 ddschoice=self._dds_global_411)

                self.set_ddsamp(self._car_411_amps["411_car_0"], channel=self._ch_global_411, profile=4,
                                ddschoice=self._dds_global_411)
                # probe411.a_probe = self._car_411_amps["411_car_0"]
                # probe411.f_probe = self._car_411_freqs["411_car_0"]
                #
                # probe411.t_probe = self._car_411_pitimes["411_car_0"]
                # probe411.update_probe()

                shelving_pulses = ["freeNE(1)"]

                # 0 -> 0 transition
                # trigger the awg to play the waveform
                shelving_pulses.append("GlobalNconv2(%f)" % (self._car_411_pitimes["411_car_0"]))
                # shelving_pulses.append("freeNE(%f)" %self._car_411_pitimes["411_car_0"])  # simply a placeholder for the pi-pulse
                shelving_pulses.append("freeNE(1.5)")
                for i in range(n_pulse):
                    shelving_pulses.append("*Laser3432p0(0.1)")
                    shelving_pulses.append("free(1.5)")

                shelving_pulses.append("Laser976(20)")
                scanseq = self.Doppler_cooling_seq(5000) + shelving_pulses + self.CCDcoolingdet_seq()


                rabi3432 = self.selectseq(seq=scanseq)
                half_range  = round(self._pitime3432p0/2/n_pulse, 2)
                timescanrange = list(np.linspace(self._pitime3432p0-half_range, self._pitime3432p0+half_range, 15))

                if ion == []:
                    rp = rtplot.Rtplot(rabi3432, AutoRunStopFunc, xdata=timescanrange,
                                       fitfunc=Fit.parabola_up_down(max_mode=False),
                                       fileprefix='3432Rabip0', autoRun=True)
                else:
                    rp = rtplot.Rtplot_SelectIon(rabi3432, AutoRunStopFunc, ion=ion, xdata=timescanrange,
                                       fitfunc=Fit.parabola_up_down(max_mode=False),
                                       fileprefix='3432Rabip0', autoRun=True)
                if rp.fit_result is not None:
                    savecalpara("3432pitime0", np.mean(rp.fit_result), self.calibfile)
                    self._pitime3432p0 = np.mean(rp.fit_result)
                    print(rp.fit_result)
                    print(np.std(rp.fit_result))

                del rp
            else:
                self.set_ddsfreq(self._freq3432p3, channel=self._ch_3432, profile=0, ddschoice=self._dds_3432)
                self.set_ddsamp(self._amp_3432, channel=self._ch_3432, profile=0, ddschoice=self._dds_3432)

                self.set_ddsfreq(self._car_411_freqs["411_car_0"], channel=self._ch_global_411, profile=4,
                                 ddschoice=self._dds_global_411)

                self.set_ddsamp(self._car_411_amps["411_car_0"], channel=self._ch_global_411, profile=4,
                                ddschoice=self._dds_global_411)
                # probe411.a_probe = self._car_411_amps["411_car_0"]
                # probe411.f_probe = self._car_411_freqs["411_car_0"]
                #
                # probe411.t_probe = self._car_411_pitimes["411_car_0"]
                # probe411.update_probe()

                shelving_pulses = self.MW_seq(profile=0, t=1) + ["free(1)"]

                # 0 -> 0 transition
                # trigger the awg to play the waveform
                shelving_pulses.append("GlobalConv2(%f)" % (self._CEOMpitime))
                # shelving_pulses.append("freeNE(%f)" %self._car_411_pitimes["411_car_0"])  # simply a placeholder for the pi-pulse
                shelving_pulses.append("free(1.5)")
                for i in range(n_pulse):
                    shelving_pulses.append("*Laser3432p0(0.1)")
                    shelving_pulses.append("free(1.5)")

                shelving_pulses.append("Laser976(20)")
                scanseq = self.Doppler_cooling_seq(5000) + shelving_pulses + self.CCDcoolingdet_seq()

                rabi3432 = self.selectseq(seq=scanseq)
                half_range = round(self._pitime3432p5 / 2 / n_pulse, 2)
                timescanrange = list(np.linspace(self._pitime3432p5 - half_range, self._pitime3432p5 + half_range, 15))

                if ion == []:
                    rp = rtplot.Rtplot(rabi3432, AutoRunStopFunc, xdata=timescanrange,
                                       fitfunc=Fit.parabola_up_down(max_mode=False),
                                       fileprefix='3432Rabip5', autoRun=True)
                else:
                    rp = rtplot.Rtplot_SelectIon(rabi3432, AutoRunStopFunc, ion=ion, xdata=timescanrange,
                                                 fitfunc=Fit.parabola_up_down(max_mode=False),
                                                 fileprefix='3432Rabip5', autoRun=True)
                if rp.fit_result is not None:
                    savecalpara("3432pitime5", np.mean(rp.fit_result), self.calibfile)
                    self._pitime3432p5 = np.mean(rp.fit_result)
                    print(rp.fit_result)
                    print(np.std(rp.fit_result))

                del rp
        elif profile==1:
            # print("No other profile now!")
            self.set_ddsfreq(self._freq3432p1, channel=self._ch_3432, profile=2, ddschoice=self._dds_3432)
            self.set_ddsamp(self._amp_3432, channel=self._ch_3432, profile=2, ddschoice=self._dds_3432)

            self.set_ddsfreq(self._car_411_freqs["411_car_m1"], channel=self._ch_global_411, profile=5,
                             ddschoice=self._dds_global_411)

            self.set_ddsamp(self._car_411_amps["411_car_m1"], channel=self._ch_global_411, profile=5,
                            ddschoice=self._dds_global_411)
            # probe411.a_probe = self._car_411_amps["411_car_0"]
            # probe411.f_probe = self._car_411_freqs["411_car_0"]
            #
            # probe411.t_probe = self._car_411_pitimes["411_car_0"]
            # probe411.update_probe()

            shelving_pulses = ["freeNEm411(1)"]
            # 0 -> 0 transition
            # trigger the awg to play the waveform
            shelving_pulses.append("GlobalNconvm2(%f)" % (self._car_411_pitimes["411_car_m1"]))
            # shelving_pulses.append("freeNE(%f)" %self._car_411_pitimes["411_car_0"])  # simply a placeholder for the pi-pulse
            # shelving_pulses.append("freeNE(1)")
            for i in range(n_pulse):
                shelving_pulses.append("free3432(1.5)")
                shelving_pulses.append("*Laser3432p1(0.1)")

            shelving_pulses.append("free3432(1.5)")
            shelving_pulses.append("Laser976(20)")
            scanseq = self.Doppler_cooling_seq(5000) + shelving_pulses + self.CCDcoolingdet_seq()

            rabi3432 = self.selectseq(seq=scanseq)
            half_range = round(self._pitime3432p1 / 2 / n_pulse, 2)
            timescanrange = list(np.linspace(self._pitime3432p1 - half_range, self._pitime3432p1 + half_range, 15))

            if ion == []:
                rp = rtplot.Rtplot(rabi3432, AutoRunStopFunc, xdata=timescanrange,
                                   fitfunc=Fit.parabola_up_down(max_mode=False),
                                   fileprefix='3432Rabip1', autoRun=True)
            else:
                rp = rtplot.Rtplot_SelectIon(rabi3432, AutoRunStopFunc, ion=ion, xdata=timescanrange,
                                             fitfunc=Fit.parabola_up_down(max_mode=False),
                                             fileprefix='3432Rabip1', autoRun=True)
            if rp.fit_result is not None:
                savecalpara("3432pitime1", np.mean(rp.fit_result), self.calibfile)
                self._pitime3432p1 = np.mean(rp.fit_result)
                print(rp.fit_result)
                print(np.std(rp.fit_result))

            del rp

        elif profile==2:
            self.set_ddsfreq(self._freq3432p2, channel=self._ch_3432, profile=3, ddschoice=self._dds_3432)
            self.set_ddsamp(self._amp_3432, channel=self._ch_3432, profile=3, ddschoice=self._dds_3432)

            self.set_ddsfreq(self._car_411_freqs["411_car_p1"], channel=self._ch_global_411, profile=6,
                             ddschoice=self._dds_global_411)

            self.set_ddsamp(self._car_411_amps["411_car_p1"], channel=self._ch_global_411, profile=6,
                            ddschoice=self._dds_global_411)
            # probe411.a_probe = self._car_411_amps["411_car_0"]
            # probe411.f_probe = self._car_411_freqs["411_car_0"]
            #
            # probe411.t_probe = self._car_411_pitimes["411_car_0"]
            # probe411.update_probe()

            shelving_pulses = ["freeNEp411(1)"]
            # 0 -> 0 transition
            # trigger the awg to play the waveform
            shelving_pulses.append("GlobalNconvp2(%f)" % (self._car_411_pitimes["411_car_p1"]))
            # shelving_pulses.append("freeNE(%f)" %self._car_411_pitimes["411_car_0"])  # simply a placeholder for the pi-pulse
            shelving_pulses.append("freeNE3432(1)")
            # shelving_pulses.append("free3432(1)")
            for i in range(n_pulse):
                shelving_pulses.append("freeNE3432p2(1)")
                shelving_pulses.append("*Laser3432p2(0.1)")

            shelving_pulses.append("free3432(1.5)")
            shelving_pulses.append("Laser976(20)")
            scanseq = self.Doppler_cooling_seq(5000) + shelving_pulses + self.CCDcoolingdet_seq()

            rabi3432 = self.selectseq(seq=scanseq)
            half_range = round(self._pitime3432p2 / 2 / n_pulse, 2)
            timescanrange = list(np.linspace(self._pitime3432p2 - half_range, self._pitime3432p2 + half_range, 15))

            if ion == []:
                rp = rtplot.Rtplot(rabi3432, AutoRunStopFunc, xdata=timescanrange,
                                   fitfunc=Fit.parabola_up_down(max_mode=False),
                                   fileprefix='3432Rabip2', autoRun=True)
            else:
                rp = rtplot.Rtplot_SelectIon(rabi3432, AutoRunStopFunc, ion=ion, xdata=timescanrange,
                                             fitfunc=Fit.parabola_up_down(max_mode=False),
                                             fileprefix='3432Rabip2', autoRun=True)
            if rp.fit_result is not None:
                savecalpara("3432pitime2", np.mean(rp.fit_result), self.calibfile)
                self._pitime3432p2 = np.mean(rp.fit_result)
                print(rp.fit_result)
                print(np.std(rp.fit_result))

            del rp

        else:
            if state==0:
                self.set_ddsfreq(self._freq3432p0, channel=self._ch_3432, profile=4, ddschoice=self._dds_3432)
                self.set_ddsamp(self._amp_3432_low, channel=self._ch_3432, profile=4, ddschoice=self._dds_3432)

                self.set_ddsfreq(self._car_411_freqs["411_car_0"], channel=self._ch_global_411, profile=4,
                                 ddschoice=self._dds_global_411)

                self.set_ddsamp(self._car_411_amps["411_car_0"], channel=self._ch_global_411, profile=4,
                                ddschoice=self._dds_global_411)
                # probe411.a_probe = self._car_411_amps["411_car_0"]
                # probe411.f_probe = self._car_411_freqs["411_car_0"]
                #
                # probe411.t_probe = self._car_411_pitimes["411_car_0"]
                # probe411.update_probe()

                shelving_pulses = ["freeNE(1)"]
                # 0 -> 0 transition
                # trigger the awg to play the waveform
                shelving_pulses.append("GlobalNconv2(%f)" % (self._car_411_pitimes["411_car_0"]))
                # shelving_pulses.append("freeNE(%f)" %self._car_411_pitimes["411_car_0"])  # simply a placeholder for the pi-pulse
                shelving_pulses.append("freeNE(1)")
                for i in range(n_pulse):
                    shelving_pulses.append("freeNE3432p4(1.5)")
                    shelving_pulses.append("*Laser3432p4(0.1)")

                shelving_pulses.append("freeNE3432p4(1.5)")
                shelving_pulses.append("Laser976(20)")
                scanseq = self.Doppler_cooling_seq(5000) + shelving_pulses + self.CCDcoolingdet_seq()

                rabi3432 = self.selectseq(seq=scanseq)
                half_range = round(self._pitime3432p4 / 2 / n_pulse, 2)
                timescanrange = list(np.linspace(self._pitime3432p4 - half_range, self._pitime3432p4 + half_range, 15))

                if ion == []:
                    rp = rtplot.Rtplot(rabi3432, AutoRunStopFunc, xdata=timescanrange,
                                       fitfunc=Fit.parabola_up_down(max_mode=False),
                                       fileprefix='3432Rabip4', autoRun=True)
                else:
                    rp = rtplot.Rtplot_SelectIon(rabi3432, AutoRunStopFunc, ion=ion, xdata=timescanrange,
                                                 fitfunc=Fit.parabola_up_down(max_mode=False),
                                                 fileprefix='3432Rabip4', autoRun=True)
                if rp.fit_result is not None:
                    savecalpara("3432pitime4", np.mean(rp.fit_result), self.calibfile)
                    self._pitime3432p4 = np.mean(rp.fit_result)
                    print(rp.fit_result)
                    print(np.std(rp.fit_result))

                del rp
            else:
                self.set_ddsfreq(self._freq3432p3, channel=self._ch_3432, profile=4, ddschoice=self._dds_3432)
                self.set_ddsamp(self._amp_3432_low, channel=self._ch_3432, profile=4, ddschoice=self._dds_3432)

                self.set_ddsfreq(self._car_411_freqs["411_car_0"], channel=self._ch_global_411, profile=4,
                                 ddschoice=self._dds_global_411)

                self.set_ddsamp(self._car_411_amps["411_car_0"], channel=self._ch_global_411, profile=4,
                                ddschoice=self._dds_global_411)
                # probe411.a_probe = self._car_411_amps["411_car_0"]
                # probe411.f_probe = self._car_411_freqs["411_car_0"]
                #
                # probe411.t_probe = self._car_411_pitimes["411_car_0"]
                # probe411.update_probe()

                shelving_pulses = self.MW_seq(profile=0, t=1) + ["free(1)"]
                # 0 -> 0 transition
                # trigger the awg to play the waveform
                shelving_pulses.append("GlobalConv2(%f)" % (self._CEOMpitime))
                # shelving_pulses.append("freeNE(%f)" %self._car_411_pitimes["411_car_0"])  # simply a placeholder for the pi-pulse
                shelving_pulses.append("free(1)")
                for i in range(n_pulse):
                    shelving_pulses.append("freeNE3432p4(1)")
                    shelving_pulses.append("*Laser3432p4(0.1)")

                shelving_pulses.append("freeNE3432p4(1.5)")
                shelving_pulses.append("Laser976(20)")
                scanseq = self.Doppler_cooling_seq(5000) + shelving_pulses + self.CCDcoolingdet_seq()

                rabi3432 = self.selectseq(seq=scanseq)
                half_range = round(self._pitime3432p5 / 2 / n_pulse, 2)
                timescanrange = list(np.linspace(self._pitime3432p5 - half_range, self._pitime3432p5 + half_range, 15))

                if ion == []:
                    rp = rtplot.Rtplot(rabi3432, AutoRunStopFunc, xdata=timescanrange,
                                       fitfunc=Fit.parabola_up_down(max_mode=False),
                                       fileprefix='3432Rabip5', autoRun=True)
                else:
                    rp = rtplot.Rtplot_SelectIon(rabi3432, AutoRunStopFunc, ion=ion, xdata=timescanrange,
                                                 fitfunc=Fit.parabola_up_down(max_mode=False),
                                                 fileprefix='3432Rabip5', autoRun=True)
                if rp.fit_result is not None:
                    savecalpara("3432pitime5", np.mean(rp.fit_result), self.calibfile)
                    self._pitime3432p5 = np.mean(rp.fit_result)
                    print(rp.fit_result)
                    print(np.std(rp.fit_result))

                del rp




    def Conversion_freqcal(self, n_points=20):
        '''

        Parameters
        ----------
        n_points:the number of the scan points

        Returns
        -------
        No return, the calibration result will be saved in the calibration file


        '''
        # probe411 = SpectrumAWGSR.SingleRestartSpectrumAWG(self.awg_spectrum2)
        #
        # probe411.a_probe = self._car_411_amps["411_car_0"]
        # probe411.f_probe = self._car_411_freqs["411_car_0"]
        #
        # probe411.t_probe = self._CEOMpitime #self._car_411_pitimes["411_car_0"]
        # probe411.update_probe()

        self.set_ddsfreq(self._CEOMfreq_car, channel=self._ch_global_411, profile=4,
                         ddschoice=self._dds_global_411)

        self.set_ddsamp(self._car_411_amps["411_car_0"], channel=self._ch_global_411, profile=4,
                        ddschoice=self._dds_global_411)

        # calibrate the transition frequency between the S(0,0)--D(2,0)
        seq = ["GlobalConv2(%.2f)"%self._CEOMpitime, "free(1)"]
        seq_probe = self.append_shelving_sbc(seq, sbc=False, shelvingdet=2)

        freqscanrange = list(np.linspace(self._car_411_freqs["411_car_0"]-0.02, self._car_411_freqs["411_car_0"]+0.02, n_points))
        # freqscan = self.awg_freq_scan(probe411, sequencer_seq=seq_probe, awg_channel=0)

        freqscan = self.select_calddschannel(4, self._ch_global_411,
                                             ddschoice=self._dds_global_411, seq=seq_probe)

        rp = rtplot.Rtplot(freqscan, AutoRunStopFunc, xdata=freqscanrange, fitfunc=Fit.inv_gaussian_fit,
                           fileprefix='411EOMfreqcal_0-2', autoRun=True)

        if rp.fit_result is not None:
            freq02 = np.mean(rp.fit_result)
            self._CEOMfreq_car = freq02
            self._car_411_freqs["411_car_0"] = freq02
            savecalpara("411_car_0", [self._car_411_freqs["411_car_0"], self._car_411_pitimes["411_car_0"],
                                      self._car_411_amps["411_car_0"]], self.calibfile)
        else:
            freq02 = None

        del rp

        # calibrate the transition frequency between the S(1,0)--D(3,0)
        seq = self.MW_seq(profile=0, t=1)+["GlobalConv2(%.2f)" %self._CEOMpitime, "free(1)"]
        seq_probe = self.append_shelving_sbc(seq, sbc=False, shelvingdet=2)

        freqscanrange = list(np.linspace(self._car_411_freqs["411_car_0"] - 0.02, self._car_411_freqs["411_car_0"] + 0.02, n_points))
        # freqscan = self.awg_freq_scan(probe411, sequencer_seq=seq_probe, awg_channel=0)

        freqscan = self.select_calddschannel(4, self._ch_global_411,
                                             ddschoice=self._dds_global_411, seq=seq_probe)

        rp = rtplot.Rtplot(freqscan, AutoRunStopFunc, xdata=freqscanrange, fitfunc=Fit.inv_gaussian_fit,
                           fileprefix='411EOMfreqcal_1-3', autoRun=True)
        if rp.fit_result is not None:
            freq13 = np.mean(rp.fit_result)
        else:
            freq13 = None

        del rp

        self.set_ddsfreq(self._car_411_freqs["411_car_0"], channel=self._ch_global_411,
                         profile=4, ddschoice=self._dds_global_411)

        if (freq02 is not None) and (freq13 is not None):
            dfreq = freq13-freq02
            EOMfreq = self._CEOMfreq - dfreq*1e-3
            self._CEOMfreq = round(EOMfreq, 7)
            savecalpara("EOMconversion", [self._CEOMfreq, self._CEOMpitime, self._CEOMamp, self._CEOMfreq_car], self.calibfile)
            try:
                self.PSG.set_frequency(self._CEOMfreq, unit="GHZ")
            except:
                print("PSG set freq unsuccessfully!")
        else:
            print("EOM Freq Cal not successfully!")



    def Conversion_ampcal(self, n_points=20, ion=[0]):
        '''

        Parameters
        ----------
        n_points: the number of the scan points
        ion: the index of the ions used for calibration, empty list means all the ions will be used

        Returns
        -------
        No return, the calibration result will be saved in the calibration file
        '''

        # probe411 = SpectrumAWGSR.SingleRestartSpectrumAWG(self.awg_spectrum2)
        #
        # probe411.a_probe = self._car_411_amps["411_car_0"]
        # probe411.f_probe = self._car_411_freqs["411_car_0"]
        #
        # probe411.t_probe = self._CEOMpitime  # self._car_411_pitimes["411_car_0"]
        # probe411.update_probe()

        self.set_ddsfreq(self._CEOMfreq_car, channel=self._ch_global_411, profile=4,
                         ddschoice=self._dds_global_411)

        self.set_ddsamp(self._car_411_amps["411_car_0"], channel=self._ch_global_411, profile=4,
                        ddschoice=self._dds_global_411)


        # calibrate the transition frequency between the S(0,0)--D(2,0)
        seq = ["*GlobalConv2(2)"]
        seq_probe = self.append_shelving_sbc(seq, sbc=False, shelvingdet=2)

        tscanrange = list(np.linspace(0.02, 3*self._CEOMpitime, n_points))
        # timescan = self.awg_time_scan(probe411, sequencer_seq=seq_probe)
        timescan = self.selectseq(seq=seq_probe)

        rp = rtplot.Rtplot_SelectIon(timescan, AutoRunStopFunc, ion=ion, xdata=tscanrange, fitfunc=Fit.rabi_fit,
                           fileprefix='411EOMpitimecal_0-2', autoRun=True)

        if rp.fit_result is not None:
            RabiRate02 = 0.5/np.mean(rp.fit_result)
        else:
            RabiRate02 = None

        del rp


        # calibrate the transition frequency between the S(1,0)--D(3,0)
        seq = self.MW_seq(profile=0, t=1)+["*GlobalConv2(2)"]
        seq_probe = self.append_shelving_sbc(seq, sbc=False, shelvingdet=2)

        tscanrange = list(np.linspace(0.02, 3 * self._CEOMpitime, n_points))
        # timescan = self.awg_time_scan(probe411, sequencer_seq=seq_probe)
        timescan = self.selectseq(seq=seq_probe)

        rp = rtplot.Rtplot_SelectIon(timescan, AutoRunStopFunc, ion=ion, xdata=tscanrange, fitfunc=Fit.rabi_fit,
                           fileprefix='411EOMpitimecal_1-3', autoRun=True)

        if rp.fit_result is not None:
            RabiRate13 = 0.5 / np.mean(rp.fit_result)
        else:
            RabiRate13 = None

        del rp


        if (RabiRate02 is not None) and (RabiRate13 is not None):
            RateRatio = RabiRate13/RabiRate02
            beta = self.__beta[np.argmin(np.abs(self.__Besselratio - RateRatio))]
            PowerRatio = self.__beta0**2/beta**2
            DB = round(10*np.log10(PowerRatio), 2)
            self._CEOMamp = round(self._CEOMamp + DB, 2)
            if self._CEOMamp < 4:
                savecalpara("EOMconversion", [self._CEOMfreq, self._CEOMpitime, self._CEOMamp, self._CEOMfreq_car], self.calibfile)
                try:
                    self.PSG.set_level(self._CEOMamp, unit="DBM")
                except:
                    print("PSG set level unsuccessfully!")
                    return 1
        else:
            print("EOM Amp Cal not successfully!")


    def Conversion_pitimecal(self, n_points=20, ion=[0]):
        # probe411 = SpectrumAWGSR.SingleRestartSpectrumAWG(self.awg_spectrum2)
        #
        # probe411.a_probe = self._car_411_amps["411_car_0"]
        # probe411.f_probe = self._car_411_freqs["411_car_0"]
        #
        # probe411.t_probe = self._CEOMpitime  # self._car_411_pitimes["411_car_0"]
        # probe411.update_probe()

        self.set_ddsfreq(self._CEOMfreq_car, channel=self._ch_global_411, profile=4,
                         ddschoice=self._dds_global_411)

        self.set_ddsamp(self._car_411_amps["411_car_0"], channel=self._ch_global_411, profile=4,
                        ddschoice=self._dds_global_411)

        # calibrate the transition frequency between the S(0,0)--D(2,0)
        seq = ["*GlobalConv2(1)"]
        seq_probe = self.append_shelving_sbc(seq, sbc=False, shelvingdet=2)

        tscanrange = list(np.linspace(0.02, 3 * self._CEOMpitime, n_points))
        # timescan = self.awg_time_scan(probe411, sequencer_seq=seq_probe)
        timescan = self.selectseq(seq=seq_probe)

        rp = rtplot.Rtplot_SelectIon(timescan, AutoRunStopFunc, ion=ion, xdata=tscanrange, fitfunc=Fit.rabi_fit,
                           fileprefix='411EOMpitimecal_0-2', autoRun=True)

        if rp.fit_result is not None:
            self._CEOMpitime = round(np.mean(rp.fit_result), 2)
            savecalpara("EOMconversion", [self._CEOMfreq, self._CEOMpitime, self._CEOMamp, self._CEOMfreq_car], self.calibfile)


        del rp


    def Conversion_pitimefinecal(self, n_pulse=1, ion=[]):
        # probe411 = SpectrumAWGSR.SingleRestartSpectrumAWG(self.awg_spectrum2)
        #
        # probe411.a_probe = self._car_411_amps["411_car_0"]
        # probe411.f_probe = self._car_411_freqs["411_car_0"]
        #
        # probe411.t_probe = self._CEOMpitime  # self._car_411_pitimes["411_car_0"]
        # probe411.update_probe()

        self.set_ddsfreq(self._CEOMfreq_car, channel=self._ch_global_411, profile=4,
                         ddschoice=self._dds_global_411)

        self.set_ddsamp(self._car_411_amps["411_car_0"], channel=self._ch_global_411, profile=4,
                        ddschoice=self._dds_global_411)

        # calibrate the transition frequency between the S(0,0)--D(2,0)
        seq = ["*GlobalConv2(1)", "free(5)"]*n_pulse
        seq_probe = self.append_shelving_sbc(seq, sbc=False, shelvingdet=2)

        half_range = round(self._CEOMpitime / 2 / n_pulse, 2)
        tscanrange = list(np.linspace(self._CEOMpitime - half_range, self._CEOMpitime + half_range, 15))


        # timescan = self.awg_time_scan(probe411, sequencer_seq=seq_probe)
        timescan = self.selectseq(seq=seq_probe)

        if ion == []:
            rp = rtplot.Rtplot(timescan, AutoRunStopFunc, xdata=tscanrange, fitfunc=Fit.parabola_up_down(max_mode=False),
                           fileprefix='411EOMpitimecal_0-2', autoRun=True)

        else:
            rp = rtplot.Rtplot_SelectIon(timescan, AutoRunStopFunc, ion=ion, xdata=tscanrange, fitfunc=Fit.parabola_up_down(max_mode=False),
                               fileprefix='411EOMpitimecal_0-2', autoRun=True)

        if rp.fit_result is not None:
            self._CEOMpitime = round(np.mean(rp.fit_result), 2)
            savecalpara("EOMconversion", [self._CEOMfreq, self._CEOMpitime, self._CEOMamp, self._CEOMfreq_car], self.calibfile)


        del rp



    # def trapfreq_cal(self):
    #     probe411 = SpectrumAWGSR.ProbeSequence(self.awg_spectrum2)
    #     # probe411.a_probe = self._car_411_amps["411_car_0"]
    #     probe411.a_probe = 1.0 * self._amp_global_411
    #     probe411.f_probe = np.min(self._rsb_freq_main)
    #
    #
    #     probe411.t_probe = 30
    #
    #     probe411.update_waveform()
    #     half_range = 0.01
    #
    #     freqscan = self.awg_freq_scan(probe411, self.spellComb["CCDGlobal411Rabi"], awg_channel=0)
    #
    #     central_freq = self._rsb_freq_main[0]
    #     freqscanrange = list(np.arange(central_freq - half_range, central_freq + half_range, 0.001))
    #
    #     rp = rtplot.Rtplot(freqscan, AutoRunStopFunc, xdata=freqscanrange, fitfunc=Fit.parabola_up_down(False), fileprefix="411SBC_cal", autoRun=True)
    #     if rp.fit_result != None:
    #         self._rsb_freq_main[0] = np.mean(rp.fit_result)
    #
    #     del rp
    #     print(self._rsb_freq_main[0])
    #
    #     central_freq = self._rsb_freq_main[1]
    #     freqscanrange = list(np.arange(central_freq - half_range, central_freq + half_range, 0.001))
    #
    #     rp = rtplot.Rtplot(freqscan, AutoRunStopFunc, xdata=freqscanrange, fitfunc=Fit.parabola_up_down(False),
    #                        fileprefix="411SBC_cal", autoRun=True)
    #     if rp.fit_result is not None:
    #         self._rsb_freq_main[1] = np.mean(rp.fit_result)
    #         self._sbc_freqlist = self._rsb_freq_main
    #
    #     savecalpara("RSB_freq", self._rsb_freq_main, self.calibfile)
    #
    #     del rp
    #     print(self._rsb_freq_main[1])
    #
    #     return 0


    def trapfreq_fast_cal(self):

        pass


    # def trapfreq_fine_cal(self):
    #     probe411 = SpectrumAWGSR.ProbeSequence(self.awg_spectrum2)
    #     probe411.a_probe = self._car_411_amps["411_car_0"]
    #     probe411.f_probe = np.min(self._rsb_freq_main)
    #
    #
    #     probe411.t_probe = self._tcal_global411
    #
    #     probe411.update_waveform()
    #
    #     freqscan = self.awg_freq_scan(probe411, self.spellComb["CCDGlobal411Rabi"], awg_channel=0)
    #
    #     # calibration for 0-0 carrier
    #     freq_car = self._car_411_freqs["411_car_0"]
    #     freqscanrange = list(np.arange(freq_car-0.05, freq_car+0.05, 0.005))
    #
    #     rp = rtplot.Rtplot(freqscan, AutoRunStopFunc, xdata=freqscanrange, fitfunc=Fit.inv_gaussian_fit, fileprefix="411 carrier0-0_cal", autoRun=True)
    #     if rp.fit_result is not None:
    #         self._car_411_freqs["411_car_0"] = np.mean(rp.fit_result)
    #         print(np.mean(rp.fit_result))
    #         savecalpara("411_car_0", [self._car_411_freqs["411_car_0"], self._car_411_pitimes["411_car_0"]], self.calibfile)
    #
    #     del rp
    #
    #     probe411.a_probe = self._car_411_amps["411_car_0"]
    #     probe411.f_probe = np.min(self._rsb_freq_main)
    #
    #     probe411.t_probe = self._t_fine_cal_trap_freq
    #
    #     probe411.update_waveform()
    #
    #     # freq_center_low = 2*self._car_411_freqs["411_car_0"] - self._rsb_freq_main[0]
    #     # freqscanrange = list(np.arange(freq_center_low - 0.03, freq_center_low + 0.03, 0.001))
    #     #
    #     # rp = rtplot.Rtplot(freqscan, AutoRunStopFunc, xdata=freqscanrange, fileprefix="411SB_cal", autoRun=True)
    #     # freq_low = 2 * (np.array(rp.fit_result) - self._car_411_freqs["411_car_0"])
    #     #
    #     # del rp
    #
    #
    #     freq_center_high = 2*self._car_411_freqs["411_car_0"] - self._rsb_freq_main[1]
    #     freqscanrange = list(np.arange(freq_center_high - 0.03, freq_center_high + 0.03, 0.001))
    #
    #     rp = rtplot.Rtplot(freqscan, AutoRunStopFunc, xdata=freqscanrange, fileprefix="411SB_cal", autoRun=True)
    #
    #     freq_high = 2 * (np.array(rp.fit_result) - self._car_411_freqs["411_car_0"])
    #
    #     freqlist = list(freq_high) # +list(freq_low)
    #     print(freqlist)
    #
    #     self._sb_freqlist = freqlist
    #     savecalpara("SB_freq", self._sb_freqlist, self.calibfile)
    #
    #     del rp
    #
    #     return 0



    def aodfreqcal(self, start=135, stop=155, route=0, tcal=5, autorange=False, step_size=0.02, shelvingdet=0, ion=[]):
        t_aod_total = tcal + 50 # 600

        # Configure the Spectrum AWG for the two AOMs
        probe_sequence = SpectrumAWG2.ProbeSequence(self.awg_spectrum_aom)


        if autorange and len(self._AODfreqlist[0])>1:
            scanrange = list(np.arange(np.min(self._AODfreqlist[0]), np.max(self._AODfreqlist[0]), step_size))
        else:
            scanrange = list(np.arange(start, stop, step_size * np.sign(stop - start)))
            # scanrange = list(np.arange(start, stop, 0.00001 * np.sign(stop - start)))

        probe_AOD = SpectrumAWG2.ProbeSequence(self.awg_spectrum_aod)
        # shelving_AOM = SpectrumAWGSR.SingleRestartSpectrumAWG(self.awg_spectrum2)


        # Configure Sequencer
        # seq_cooling = self.Doppler_cooling_seq(5000)
        MWseq0 = self.MW_seq(profile=0, t=0.5)
        # seq411 = self.individual_aodscanseq(route=route, t=tcal)   #t--the time 411 on
        seq411 = self.individual_timescanseq(probe_sequence, probe_AOD, route=route, ion=[0])
        MWseq1 = self.MW_seq(profile=1, t=0.5)
        # seqdet = self.CCDdet_seq()

        seq = MWseq0 + seq411 + MWseq1

        seq = self.append_shelving_sbc(seq, sbc=False, shelvingdet=shelvingdet)
        # print(seq)

        # Configure the Spectrum AWG for the AODs

            # Configure the probe pulse
        probe_AOD.t_probe = t_aod_total
        probe_AOD.a_probe1 = self._amp_aod_ind1
        probe_AOD.f_probe1 = 145
        probe_AOD.a_probe2 = self._amp_aod_ind2
        probe_AOD.f_probe2 = 145
        if route == 0:
            probe_AOD.a_probe2 = 0
        elif route == 1:
            probe_AOD.a_probe1 = 0
        # probe_AOD.update_waveform()

        # Configure the output during the idle time, to send the light to the AODs
        # probe_sequence.waveform_idle1 = []
        # probe_sequence.waveform_idle2 = []
        # probe_sequence.add_pulse_to_idle(125, 1, 0, 125, 1, 0, 1)
        # probe_sequence.update_idle()
        # Configure the probe pulse
        def freqscan(freq):
            probe_sequence.t_probe = tcal
            probe_sequence.a_probe1 = self._awg_amp_aom_ind1
            probe_sequence.f_probe1 = self._f_aom_ind1
            probe_sequence.a_probe2 = self._awg_amp_aom_ind2
            probe_sequence.f_probe2 = self._f_aom_ind2
            if route == 0:
                probe_sequence.a_probe2 = 0
                probe_sequence.f_probe1 = (self._acs_freq-freq)/2
            elif route == 1:
                probe_sequence.a_probe1 = 0
                probe_sequence.f_probe2 = (self._acs_freq-freq)/2

            probe_sequence.t_off = t_aod_total - tcal - probe_sequence.t_off_before + 20 #5
            probe_sequence.update_waveform()

            state, thrrawdata = self.awg_freq_scan(probe_AOD, seq, awg_channel=route)(freq)

            return state, thrrawdata
        # freqscan = self.test_awg_freq_scan(probe_AOD, probe_sequence, tcal, seq, awg_channel=route)

        # def freqscan(freq):
        #     probe_sequence.update_time(tcal)
        #     print("AOM updateA")
        #     state, thrrawdata = self.awg_freq_scan(probe_AOD, seq, awg_channel=route)(freq)
        #     return state, thrrawdata

        # rp = rtplot.Rtplot(freqscan, AutoRunStopFunc, xdata=scanrange, fitfunc=Fit.singaussian_fit, fileprefix='411indiviudalcal', autoRun=True)
        if ion == []:
            rp_cal = rtplot.Rtplot(freqscan, AutoRunStopFunc, xdata=scanrange, fitfunc=Fit.lorentizan_peak_fit,
                               fileprefix='411indiviudalcal', autoRun=True)

            if rp_cal.fit_result is not None:
                freqlist_new = rp_cal.fit_result
                self.update_AOD_calibration(rp_cal.fit_result, route)

                calib_success = True
            else:
                calib_success = False


        else:
            rp_cal = rtplot.Rtplot_SelectIon(freqscan, AutoRunStopFunc, ion=ion, xdata=scanrange,
                                         fitfunc=Fit.lorentizan_peak_fit, fileprefix='411individualcal', autoRun=True)

            if rp_cal.fit_result is not None:
                # print(rp.fit_result)
                if route==0:
                    freqlist_old = np.array(self._AODfreqlist1[0])
                elif route==1:
                    freqlist_old = np.array(self._AODfreqlist2[0])

                freqlist_new = np.mean(np.array(rp_cal.fit_result)[np.array(ion)].reshape(-1)-freqlist_old[np.array(ion)])+freqlist_old
                self.update_AOD_calibration(list(freqlist_new), route)

                calib_success = True
            else:
                if route==0:
                    freqlist_old = np.array(self._AODfreqlist1[0])
                elif route==1:
                    freqlist_old = np.array(self._AODfreqlist2[0])
                calib_success = False
                freqlist_new = freqlist_old

        # if len(self.ion_pos) > 1:
        #     p0 = self._PixelAOD
        #     fitp, fitcov = curve_fit(Fit.linear_fun, np.array(self.ion_pos), np.array(self._AODfreqlist[0]), p0=p0)
        #     self._PixelAOD = list(fitp)
        #     savecalpara("PixelAOD", self._PixelAOD, self.calibfile)
        #     print(self._PixelAOD)

        state0 = np.max(rp_cal.ydatadraw)

        del rp_cal

        return state0, freqlist_new, calib_success

    def test_aodfreqcal(self, freq, route=0, tcal=5):
        t_aod_total = 600 # tcal + 50

        # Configure the Spectrum AWG for the two AOMs
        probe_sequence = SpectrumAWG2.ProbeSequence(self.awg_spectrum_aom)

        probe_AOD = SpectrumAWG2.ProbeSequence(self.awg_spectrum_aod)

        # Configure Sequencer
        seq_cooling = self.Doppler_cooling_seq(5000)
        MWseq0 = self.MW_seq(profile=0, t=0.5)
        # seq411 = self.individual_aodscanseq(route=route, t=tcal)   #t--the time 411 on
        seq411 = self.individual_timescanseq(probe_sequence, probe_AOD, route=route, ion=[0])
        MWseq1 = self.MW_seq(profile=1, t=0.5)
        seqdet = self.CCDdet_seq()

        # waveform1_AOD = np.array(probe_AOD.waveform_idle1)
        # waveform1_AOM = np.array(probe_sequence.waveform_probe1)

        seq = seq_cooling+MWseq0+seq411+["free(1)"]+MWseq1+seqdet
        # print(seq)

        # Configure the Spectrum AWG for the AODs

            # Configure the probe pulse
        probe_AOD.t_probe = t_aod_total
        # probe_AOD.a_probe1 = self._amp_aod_ind1
        # probe_AOD.f_probe1 = self._AODfreqlist[0][0]
        # probe_AOD.a_probe2 = self._amp_aod_ind2
        # probe_AOD.f_probe2 = 145
        # if route == 0:
        #     probe_AOD.a_probe2 = 0
        # elif route == 1:
        #     probe_AOD.a_probe1 = 0

        # probe_AOD.update_waveform()

        # waveform2_AOD = np.array(probe_AOD.waveform_idle1)



        # Configure the probe pulse
        probe_sequence.t_probe = tcal
        probe_sequence.a_probe1 = self._awg_amp_aom_ind1
        probe_sequence.f_probe1 = self._f_aom_ind1
        probe_sequence.a_probe2 = self._awg_amp_aom_ind2
        probe_sequence.f_probe2 = self._f_aom_ind2
        if route == 0:
            probe_sequence.a_probe2 = 0
        elif route == 1:
            probe_sequence.a_probe1 = 0
        probe_sequence.t_off = t_aod_total - tcal - probe_sequence.t_off_before + 20 #5
        probe_sequence.update_waveform()

        # waveform2_AOM = np.array(probe_sequence.waveform_probe1)
        # print(np.sum(waveform2_AOM - waveform1_AOM))

        freqscan = self.awg_freq_scan(probe_AOD, seq, awg_channel=3)
        return freqscan(freq) #, probe_sequence.waveform_probe1, probe_AOD.waveform_probe1



    def motorscan_fit(self, tcal=1, ion=[0,1], half_range=0.003, direction=1, route=0):
        assert route == 0 or direction == 1
        # The sequence instance for the AOM AWG
        probe_sequence = SpectrumAWG2.ProbeSequence(self.awg_spectrum_aom)
        probe_sequence.t_probe = tcal

        # probe_sequence.a_probe1 = self._awg_amp_aom_ind1
        probe_sequence.f_probe1 = self._f_aom_ind1
        # probe_sequence.a_probe2 = self._awg_amp_aom_ind2
        probe_sequence.f_probe2 = self._f_aom_ind2

        # The sequence instance for the AOD AWG
        probe_AOD = SpectrumAWG2.ProbeSequence(self.awg_spectrum_aod)

        self.seq.scanValue = tcal

        self.motor_ctrl = Motor(com=self.motor[route][direction], velocity=2.0)
        scanrange = list(np.arange(self.motor_ctrl.getpos() - half_range, self.motor_ctrl.getpos() + half_range, 0.0005))
        seq411 = self.individual_timescanseq(probe_sequence, probe_AOD, route=route, ion=ion)

        probe_sequence.t_off = self.t_aod_total - tcal - probe_sequence.t_off_before + 5
        probe_sequence.update_waveform()

        motorscan = self.select_calmotor(seq411, tcal=tcal, direction=direction, route=route)

        rp = rtplot.Rtplot_SelectIon(motorscan, stopfunc=AutoRunStopFunc, ion=ion, xdata=scanrange, fitfunc=Fit.gaussian_fit, fileprefix="Beam%d_motorcal"%route, autoRun=True)

        if rp.fit_result is not None:
            optpos = np.mean(rp.fit_result)
        else:
            optpos = self._motorpos[route][direction][0]

        self.motor_ctrl.absolutemove(optpos)
        t = time.time()
        self._motorpos[route][direction] = (self.motor_ctrl.getpos(), t)
        savecalpara("motorpos", self._motorpos, self.calibfile)

        self.motor_ctrl.close()

        if rp.fit_result is not None:
            poslist = rp.fit_result
            del rp
            return list(self.ion_pos)+poslist
        else:
            del rp
            return 0





    def motorscancal(self, tcal=1, tolerance=0.15, ion=[0,1], half_range=0.005, direction=1, route=0, step_size=0.0005):

        # assert route==0 or direction==1
        # # The sequence instance for the AOM AWG
        # probe_sequence = SpectrumAWG2.ProbeSequence(self.awg_spectrum_aom)
        # probe_sequence.t_probe = tcal
        #
        # # probe_sequence.a_probe1 = self._awg_amp_aom_ind1
        # probe_sequence.f_probe1 = self._f_aom_ind1
        # # probe_sequence.a_probe2 = self._awg_amp_aom_ind2
        # probe_sequence.f_probe2 = self._f_aom_ind2
        #
        # # The sequence instance for the AOD AWG
        # probe_AOD = SpectrumAWG2.ProbeSequence(self.awg_spectrum_aod)
        #
        # self.seq.scanValue = tcal
        #
        # self.motor_ctrl = Motor(com=self.motor[route][direction], velocity=2.0)
        # scanrange = list(np.arange(self.motor_ctrl.getpos()-half_range, self.motor_ctrl.getpos()+half_range, 0.0005))
        # findrange = list(np.arange(self.motor_ctrl.getpos()+half_range, self.motor_ctrl.getpos()-half_range, -0.0005))
        #
        # seq411 = self.individual_timescanseq(probe_sequence, probe_AOD, route=route, ion=ion)
        #
        # if route==0 and direction==0:
        #     amp = np.sqrt(self._amp_aod_ind1 ** 2 / len(ion))
        #     probe_AOD.waveform_probe1 = SpectrumAWG2.SinCombine([self._AODfreqlist2[0][i] for i in ion],
        #                                                                [amp] * len(ion), [0] * len(ion),
        #                                                                self.t_aod_total,
        #                                                                probe_AOD._sample_rate)
        #     probe_AOD.waveform_probe2 = [0]
        #     probe_AOD.update_probe()
        #
        # probe_sequence.t_off = self.t_aod_total - tcal - probe_sequence.t_off_before+5
        # probe_sequence.update_waveform()



        motorscan = self.select_calmotor(tcal=tcal, direction=direction, route=route, ion=ion)

        cur_pos = self.motor_ctrl.getpos()

        scanrange = list(
            np.arange(cur_pos - half_range, cur_pos + half_range, step_size))

        rp_motor = rtplot.Rtplot_SelectIon(motorscan, stopfunc=AutoRunStopFunc, ion=ion, xdata=scanrange, fitfunc=Fit.gaussian_fit, fileprefix="Beam%d_motorcal"%route, autoRun=True)

        if rp_motor.fit_result is not None:
            optpos = np.mean(rp_motor.fit_result)
            findrange = list(np.arange(optpos+0.003, optpos-0.005, -0.0005))

            yopt = np.mean(rp_motor.fitpara[:, 1])
            del rp_motor
            print("Moving to the optimal position")
            # OptPos = rtplot.RtGetOptPos(motorscan, AutoRunStopFunc, yopt, tolerance=tolerance, ion=ion, xdata=findrange,
            #                             fileprefix="Beam%d_motorcal" % route, autoRun=True)
            # if OptPos.i == 0:
            self.motor_ctrl.absolutemove(optpos-0.005)

            # del OptPos
            self.motor_ctrl.absolutemove(optpos)
            print("Moved to the optimal position")

            calibsuccess = True

        else:
            del rp_motor
            print("Fit error")
            optpos = self._motorpos[route][direction][0]
            self.motor_ctrl.absolutemove(optpos-0.005)
            self.motor_ctrl.absolutemove(optpos)

            calibsuccess = False

        if route==0 and direction==0:
            self._AODfreqlist = self._AODfreqlist2
            self._AODfreqlist1 = self._AODfreqlist2
            freqs = self._AODfreqlist2[0]
            self.update_AOD_calibration(freqs, 0)


        # print(optpos)
        # if route==0:
        #     self.motor_ctrl.absolutemove(optpos-0.003)
        #
        # elif route == 1:
        #     self.motor_ctrl.absolutemove(optpos - 0.002)

        t = time.time()
        self._motorpos[route][direction] = (self.motor_ctrl.getpos(), t)
        savecalpara("motorpos", self._motorpos, self.calibfile)

        print(self._motorpos)
        self.motor_ctrl.close()
        # if route == 0:
        #     AWG.TurnOnOff(self.awg, self._ch_aod_ind1, 0, awg=True)
        # elif route == 1:
        #     AWG.TurnOnOff(self.awg, self._ch_aod_ind2, 0, awg=True)

        return yopt, cur_pos, calibsuccess, self._motorpos[route][direction]

    def motorscan_fast_cal(self, tcal=1, diff_threshold=0.1, step_size = 0.0003, t_delay=0,
                           ion=[0], direction=1, route=0, target=0.9, low_limit=0.5, init_direction=1,
                           verbose=False):
        assert route == 0 or direction == 1
        # The sequence instance for the AOM AWG
        probe_sequence = SpectrumAWG2.ProbeSequence(self.awg_spectrum_aom)
        probe_sequence.t_probe = tcal

        # probe_sequence.a_probe1 = self._awg_amp_aom_ind1
        probe_sequence.f_probe1 = self._f_aom_ind1
        # probe_sequence.a_probe2 = self._awg_amp_aom_ind2
        probe_sequence.f_probe2 = self._f_aom_ind2

        # The sequence instance for the AOD AWG
        probe_AOD = SpectrumAWG2.ProbeSequence(self.awg_spectrum_aod)

        self.seq.scanValue = tcal

        self.motor_ctrl = Motor(com=self.motor[route][direction], velocity=1.0)
        pos_init = self.motor_ctrl.getpos()

        seq411 = self.individual_timescanseq(probe_sequence, probe_AOD, route=route, ion=ion)

        seq_cooling = self.Doppler_cooling_seq(5000)
        MWseq0 = self.MW_seq(profile=0, t=0.5)
        MWseq1 = self.MW_seq(profile=1, t=0.5)
        seqdet = self.CCDdet_seq()

        seq = seq_cooling + MWseq0 + seq411 + ["free(1)"] + MWseq1 + seqdet


        probe_sequence.t_off = self.t_aod_total - tcal - probe_sequence.t_off_before + 20
        probe_sequence.update_waveform()

        image = self._runseq(Seq=seq)
        state_init, thrrawdata = self._detectstateall(image)


        diff_state = 1
        step_count = 0
        scan_direction = init_direction

        # pos = self.motor_ctrl.getpos()

        if verbose:
            print(pos_init, np.mean(state_init[ion]))
        if np.mean(state_init[ion]) >= target or np.mean(state_init[ion]) < low_limit:
            if verbose:
                print("Stop at 1st point")
            t = time.time()
            self._motorpos[route][direction] = (pos_init, t) # update the calibration time in the calibration result file
            savecalpara("motorpos", self._motorpos, self.calibfile)
            self.motor_ctrl.close()
            return np.mean(state_init[ion]), pos_init, scan_direction

        pos_new = pos_init + step_size * scan_direction
        self.motor_ctrl.absolutemove(pos_new)
        image = self._runseq(Seq=seq)
        state_new, thrrawdata = self._detectstateall(image)

        # if np.mean(state_new[ion]) < low_limit:
        #     print("Abort calibration.", pos_new, state_new)
        #     # Change the position back to the initial one
        #     self.motor_ctrl.absolutemove(pos_init)
        #     return state_new, pos_init

        diff_state = np.mean(state_new[ion] - state_init[ion])
        state_init = state_new

        if diff_state < 0 and np.abs(diff_state) > diff_threshold:
            scan_direction = -scan_direction
        if np.abs(diff_state) <= diff_threshold or np.mean(state_init[ion]) >= target:
            t = time.time()
            self._motorpos[route][direction] = (pos_new, t)
            savecalpara("motorpos", self._motorpos, self.calibfile)
            self.motor_ctrl.close()
            if verbose:
                print(pos_new, np.mean(state_init[ion]), diff_state, diff_threshold)
                print('stop at 2nd point')
            return np.mean(state_new[ion]), pos_new, scan_direction

        sign_last_time = 1
        last_pos = pos_new
        while (np.mean(state_init[ion]) < target and np.mean(state_init[ion]) > low_limit) or step_count==0:
            # pos = self.motor_ctrl.getpos()
            if verbose:
                print(last_pos, np.mean(state_init[ion]), diff_state, diff_threshold)
            scan_direction = scan_direction * sign_last_time # Flip the direction of scan, if the result is getting worse
            pos_new = last_pos + step_size * scan_direction
            self.motor_ctrl.absolutemove(pos_new)
            time.sleep(t_delay)
            image = self._runseq(Seq=seq)
            state_new, thrrawdata = self._detectstateall(image)
            diff_state = np.mean(state_new[ion]-state_init[ion])
            state_init = state_new
            step_count += 1

            last_pos = pos_new # save the current position to last_pos for the use of next round

            if sign_last_time < 0:
                if verbose:
                    print("Retrieved one step")
                scan_direction = -scan_direction  # Correct the scan direction for the return value
                break

            if np.abs(diff_state) <= diff_threshold:
                if verbose:
                    print("Insignificant difference in adjacent steps.", diff_state)
                break

            if diff_state >= 0:
                sign_last_time = 1
            else:
                sign_last_time = -1

            if step_count > 10:
                if verbose:
                    print("Caution: fast_cal maybe failed")
                self.motor_ctrl.absolutemove(pos_init) # Move back to the initial position if the calibration fails
                break

        pos_now = self.motor_ctrl.getpos()
        t = time.time()
        self._motorpos[route][direction] = (pos_now, t)
        savecalpara("motorpos", self._motorpos, self.calibfile)
        self.motor_ctrl.close()
        if verbose:
            print(pos_now, state_init)

        return np.mean(state_init[ion]), pos_now, scan_direction

    def aod_fast_cal(self, tcal=1, diff_threshold=0.1, step_size=0.02,
                     ion=[0], route=0, target=0.9, low_limit=0.5, init_direction=1, verbose=False):

        probe_sequence = SpectrumAWG2.ProbeSequence(self.awg_spectrum_aom)
        probe_sequence.t_probe = tcal

        # probe_sequence.a_probe1 = self._awg_amp_aom_ind1
        probe_sequence.f_probe1 = self._f_aom_ind1
        # probe_sequence.a_probe2 = self._awg_amp_aom_ind2
        probe_sequence.f_probe2 = self._f_aom_ind2

        # The sequence instance for the AOD AWG
        probe_AOD = SpectrumAWG2.ProbeSequence(self.awg_spectrum_aod)

        self.seq.scanValue = tcal

        seq411 = self.individual_timescanseq(probe_sequence, probe_AOD, route=route, ion=ion)

        seq_cooling = self.Doppler_cooling_seq(5000)
        MWseq0 = self.MW_seq(profile=0, t=0.5)
        MWseq1 = self.MW_seq(profile=1, t=0.5)
        seqdet = self.CCDdet_seq()

        seq = seq_cooling + MWseq0 + seq411 + ["free(1)"] + MWseq1 + seqdet

        probe_sequence.t_off = self.t_aod_total - tcal - probe_sequence.t_off_before + 20
        probe_sequence.update_waveform()

        image = self._runseq(Seq=seq)
        state_init, thrrawdata = self._detectstateall(image)

        diff_state = 1
        step_count = 0
        scan_direction = init_direction

        if route == 0:
            freqlist_init= self._AODfreqlist1[0]
            timestamp_init = self._AODfreqlist1[1]
        else:
            freqlist_init = self._AODfreqlist2[0]
            timestamp_init = self._AODfreqlist2[1]

        if verbose:
            print(freqlist_init, state_init[ion])
        if np.min(state_init[ion]) >= target or np.min(state_init[ion]) < low_limit:
            if verbose:
                print("Stop at 1st point")
            self.update_AOD_calibration(freqlist_init, route)
            return np.min(state_init[ion]), self._AODfreqlist, scan_direction, self._AODfreqlist

        # Initially change the AOD frequency by one step
        freqlist_new = list(np.array(freqlist_init) + scan_direction * step_size)
        self.update_AOD_freqs(probe_AOD, freqlist_new, route, ion)

        image = self._runseq(Seq=seq)
        state_new, thrrawdata = self._detectstateall(image)

        # if np.mean(state_new[ion]) < low_limit:
        #     print("Abort calibration.", freqlist_new, state_new)
        #     # Change the position back to the initial one
        #     self.update_AOD_freqs(probe_AOD, freqlist_init, route, ion)
        #     return state_new, freqlist_init, -1 * scan_direction

        diff_state = np.mean(np.min(state_new[ion]) - np.min(state_init[ion]))
        state_init = state_new

        if np.min(state_init[ion]) >= target:
            if verbose:
                print(freqlist_new, state_init[ion])
                print("Stop at 2nd point")
            self.update_AOD_calibration(freqlist_new, route)
            return np.min(state_init[ion]), self._AODfreqlist, scan_direction, (freqlist_init, timestamp_init)

        if diff_state < 0 and np.abs(diff_state) > diff_threshold: # Flip the direction of the sign if the result is getting worse
            scan_direction = -scan_direction

        # if np.abs(diff_state) <= diff_threshold:
        #     if verbose:
        #         print("Same results on adjacent points.")
        #     self.update_AOD_calibration(freqlist_new, route)
        #     return np.min(state_new[ion]), self._AODfreqlist, scan_direction, (freqlist_init, timestamp_init)




        sign_last_time = 1
        # while (np.min(state_init[ion]) < target and np.min(state_init[ion]) > low_limit) or step_count==0:
        while np.min(state_init[ion]) < target or step_count == 0:
            if verbose:
                print(freqlist_new, state_init[ion], diff_state, diff_threshold * np.min(state_init[ion]))
            scan_direction = scan_direction * sign_last_time # Flip the sign of scan if the result is descending
            freqlist_new = list(np.array(freqlist_new)+ scan_direction * step_size)
            self.update_AOD_freqs(probe_AOD, freqlist_new, route, ion)

            image = self._runseq(Seq=seq)
            state_new, thrrawdata = self._detectstateall(image)
            diff_state = np.mean(np.min(state_new[ion]) - np.min(state_init[ion]))
            state_init = state_new
            step_count += 1

            if sign_last_time < 0:
                if verbose:
                    print("Retrieved one step")
                scan_direction = -scan_direction # Correct the scan direction for the return value
                break
            # sign_last_time = np.sign(diff_state)
            if np.abs(diff_state) <= diff_threshold:
                if verbose:
                    print("Insignificant difference in adjacent steps.", diff_state)
                break
            if diff_state > 0:
                sign_last_time = 1
            else:
                sign_last_time = -1

            if step_count > 10:
                if verbose:
                    print("Caution: fast_cal maybe failed")
                break

        self.update_AOD_calibration(freqlist_new, route)
        # self._AODfreqlist = freqlist_new
        # savecalpara("AODfreqlist", self._AODfreqlist, self.calibfile)
        # if route==0:
        #     self._AODfreqlist1 = freqlist_new
        #     savecalpara("AODfreqlist1", self._AODfreqlist1, self.calibfile)
        # else:
        #     self._AODfreqlist2 = freqlist_new
        #     savecalpara("AODfreqlist2", self._AODfreqlist2, self.calibfile)

        if verbose:
            print(freqlist_new, state_init[ion])

        return np.min(state_init[ion]), self._AODfreqlist, scan_direction, (freqlist_init,timestamp_init)

    def run_AOD(self, tcal=1, ion=[0], route=0):
        probe_sequence = SpectrumAWG2.ProbeSequence(self.awg_spectrum_aom)
        probe_sequence.t_probe = tcal

        # probe_sequence.a_probe1 = self._awg_amp_aom_ind1
        probe_sequence.f_probe1 = self._f_aom_ind1
        # probe_sequence.a_probe2 = self._awg_amp_aom_ind2
        probe_sequence.f_probe2 = self._f_aom_ind2

        # The sequence instance for the AOD AWG
        probe_AOD = SpectrumAWG2.ProbeSequence(self.awg_spectrum_aod)

        self.seq.scanValue = tcal

        seq411 = self.individual_timescanseq(probe_sequence, probe_AOD, route=route, ion=ion)

        seq_cooling = self.Doppler_cooling_seq(5000)
        MWseq0 = self.MW_seq(profile=0, t=0.5)
        MWseq1 = self.MW_seq(profile=1, t=0.5)
        seqdet = self.CCDdet_seq()

        seq = seq_cooling + MWseq0 + seq411 + ["free(1)"] + MWseq1 + seqdet

        probe_sequence.t_off = self.t_aod_total - tcal - probe_sequence.t_off_before + 20
        probe_sequence.update_waveform()

        image = self._runseq(Seq=seq)
        state, thrrawdata = self._detectstateall(image)

        return state[ion]


    # def MWfreqrtcal(self):
    #     self.set_ddsfreq(self._MWfreq+0.005, channel=2, profile=7, ddschoice=1)
    #     self.set_ddsfreq(self._MWfreq+0.005, channel=2, profile=6, ddschoice=1)
    #     scanrange = list(np.arange(0.1, 3000, 20))
    #     func = self.selectseq(seq=self.spellComb["CCDMWramsey"])
    #     fitfunc = Fit.ramsey_fit
    #
    #     def modifycalibpara(x):
    #         self._MWfreq = self._MWfreq+0.005-x
    #         savecalpara("MWfreq", self._MWfreq, self.calibfile)
    #         self.set_ddsfreq(self._MWfreq, channel=2, profile=7, ddschoice=1)
    #         self.set_ddsfreq(self._MWfreq, channel=2, profile=6, ddschoice=1)
    #
    #     return scanrange, func, fitfunc, modifycalibpara



    # def MWpitimertcal(self):
    #     self.set_ddsfreq(self._MWfreq, channel=2, profile=7, ddschoice=1)
    #     self.set_ddsfreq(self._MWfreq, channel=2, profile=6, ddschoice=1)
    #     scanrange = list(np.around(np.linspace(0.1, 3 * self._MWpitimelist[0], 50), decimals=2))
    #     func = self.selectseq(seq=self.spellComb["CCDMW"])
    #     fitfunc = Fit.rabi_fit
    #
    #     def modifycalibpara(x):
    #         self._MWpitimelist = x
    #         savecalpara("MWpitimelist", self._MWpitimelist, self.calibfile)
    #
    #     return scanrange, func, fitfunc, modifycalibpara



    def motorscanrtcal(self, direction=1, route=0):
        scanrange = list(np.arange(self.motor[route][direction].getpos() - 0.04, self.motor[route][direction].getpos() + 0.04, 0.001))
        func = self.select_calmotor(direction=direction, route=route)
        fitfunc = Fit.cosgaussian_fit

        def modifycalibpara(x):
            self.motor[route][direction].absolutemove(x)

        return scanrange, func, fitfunc, modifycalibpara




    # def ShelvingDetection(self):
    #     seq0 = []
    #     waveform0 = {}
    #     seq, code = self.append_shelving_sbc(seq0, waveform0, sbc=False, shelvingdet=True)
    #     exp = self.selectseq(seq)
    #
    #     return exp

    def set_370_amp_det(self, amp=None):
        if amp is None:
            self.set_ddsamp(self.amp_370_det, channel=1, profile=1, ddschoice=0)
            self.amp_370 = self.amp_370_det
        else:
            self.set_ddsamp(amp, channel=1, profile=1, ddschoice=0)
            self.amp_370 = amp

    def set_370_amp_coolingdet(self):
        self.set_ddsamp(self.amp_370_coolingdet, channel=1, profile=1, ddschoice=0)
        self.amp_370 = self.amp_370_coolingdet


    def close_awg(self):
        for i in self._used_awg_channels:
            AWG.TurnOnOff(self.awg, i, 0, awg=True)
        self._used_awg_channels = []


    def closedevice(self):
        self.seq.setIdle()
        self.seq.exit()
        self.client.send(b'\n')
        self.client.close()
        for i in range(2):
            for j in range(2):
                try:
                    self.motor[i][j].close()
                except:
                    pass

        self.ddsad.close()

        # self.ionfile.close()

        # self.close_awg()
        # self.awg.close_device()
        # SpectrumAWG2.spcm_vClose(self.awg_spectrum.card)



if __name__ == '__main__':
    cal = CaliB()
    # cal.RabiRT(20, "411_car_m1")
    # cal.autocal_411_3432()

    # shelvingDet = SpectrumAWG.ShelvingDetectionSequence(cal.awg_spectrum)
    # seq0 = []
    # seq1 = cal.append_shelving_sbc(seq0, shelvingDet, sbc=False, shelvingdet=True)
    # print(seq1)
    # exp = cal.selectseq(seq1)
    # rp = rtplot.Rtplot(exp, cal.closedevice, xdata=list(np.arange(0.1, 100, 1)), fileprefix='CCDshelvingdetection')

    # Test SBC + probe
    # sbc_probe = SpectrumAWG.SbcProbeSequence(cal.awg_spectrum)
    # # Configure the 411 probe pulse
    # tstartlist = [10, 15]
    # tendlist = [60, 60]
    # cycle = 30
    # freqlist = [216.082, 216.321]
    # t_probe = 20
    #
    # seq_probe = ["Global411(40)", "*free(%f)" %t_probe]
    # seq_sbc = cal.SBC_seq(tstartlist, tendlist, cycle, freqlist, sbc_probe)
    # seq_coolingdet = cal.CCDcoolingdet_seq()
    # seq = seq_sbc+seq_probe+seq_coolingdet
    # print(seq)
    #
    # sbc_probe.add_pulse_to_probe(217.7147, 1, 0, t_probe)
    # sbc_probe.f_probe = 217.7147
    # sbc_probe.a_probe = 1
    # sbc_probe.update_probe()



    # cal._sbc_tstartlist = [10]
    # cal._sbc_tendlist = [50]
    # cal._sbc_cycle = 20
    # cal._rsb_freq_main = [216.085]

    # exp = cal.awg_time_scan(sbc_probe, seq)
    # rp = rtplot.Rtplot(exp, cal.closedevice, xdata=list(np.arange(0.1, 200, 4)), fitfunc=Fit.rabi_fit, fileprefix='SBC_probe')

    # Test SBC + probe + shelving
    # sbc_probe_shelving = SpectrumAWG.SbcProbeShelvingSequence(cal.awg_spectrum)
    # # Configure the 411 probe pulse
    # t_probe = 20
    # seq_probe = ["Global411(%f)" % t_probe, "free(1)"]
    # sbc_probe_shelving.add_pulse_to_probe(216.085, 1.0, 0, t_probe)
    # sbc_probe_shelving.update_probe()
    #
    # cal._sbc_tstartlist = [10]
    # cal._sbc_tendlist = [20]
    # cal._sbc_cycle = 2
    # cal._rsb_freq_main = [216.085]
    #
    # seq = cal.append_shelving_sbc(seq_probe, sbc_probe_shelving, sbc=True, shelvingdet=True)
    # exp = cal.selectseq(seq)
    # print(seq)
    # rp = rtplot.Rtplot(exp, cal.closedevice, xdata=list(np.arange(0.1, 100, 1)), fileprefix='SBC_probe')

    # Test 411 probe freqscan
    # probe411 = SpectrumAWG.ProbeSequence(cal.awg_spectrum)
    #
    # freqscan = cal.awg_freq_scan(probe411, cal.spellComb["CCDGlobal411Rabi"])
    # rabi = cal.awg_time_scan(probe411, cal.spellComb["CCDGlobal411Rabi"])
    #
    # freqscanrange = list(np.arange(217.6, 217.8, 0.004))
    # tscanrange = list(np.arange(0.1, 50, 1))
    # probe411.t_probe = 20
    # probe411.f_probe = 217.7147
    # cal.seq.scanValue = 20
    # probe411.a_probe = 1
    #
    # rp = rtplot.Rtplot(rabi, cal.closedevice, xdata=tscanrange, fitfunc=Fit.rabi_fit, fileprefix='411rabi')
    # rp = rtplot.Rtplot(freqscan, cal.closedevice, xdata=freqscanrange, fitfunc=Fit.inv_gaussian_fit, fileprefix='411freqscan')




    # exp = cal.ShelvingDetection()
    # # mwfreq = cal.MWfreqfinecal()
    # #
    # # print(mwfreq)
    #
    # # mwpitime = cal.MWpitimecal()
    # # print(mwpitime)
    #
    # def aodcal(freq):
    #     cal.ion_count()
    #     freqscan = cal.select_calddschannel(0, 2, ddschoice=0, seq=cal.spellComb["411i1ACS"], status=True)
    #
    #     return freqscan(freq)
    #
    # def acstimescan(t):
    #     cal.ion_count()
    #     timescan = cal.select_singleion(route=0, ion=1)
    #
    #     return timescan(t)
    #
    # def acsrt():
    #     cal.ion_count()
    #     timescan = cal.select_singleion(route=0, ion=0)
    #
    #     return timescan(50)
    #
    # def acstimescan_multi(t, ion=0):
    #     cal.ion_count()
    #     timescan = cal.select_singleion(route=0, ion=ion)
    #
    #     return timescan(t)
    #
    # def autorunstop(i):
    #     if i==cal.ion_num-1:
    #         return cal.closedevice
    #     else:
    #         def countion():
    #             print(cal.ion_num)
    #
    #         return countion
    #
    #
    # def rabirt():
    #     seq.scanValue = 10
    #     seq.loadSeq(scanSeq)
    #     allcount, detailcount = seq.startSeq(repeatTimes=100)
    #     data = np.sum(detailcount >= seq.threshold) / seq.repeatTimes
    #
    #     return 1 - data
    #
    #
    # def stop():
    #     print("next")
    #
    # # thrsetting = cal.thrcal()
    # # print(thrsetting)
    #
    #
    #
    # # aodfreq = cal.aodfreqcal(start=140, stop=150, route=1)
    # # print(aodfreq)
    # # rp = rtplot.Rtplot(aodcal, cal.closedevice, xdata=list(np.arange(144.6, 145.6, 0.03)), fitfunc=Fit.cosgaussian_fit, fileprefix='aodfreqscan')
    # # rp = rtplot.Rtplot(cal.thrscan, cal.closedevice, xdata=list(np.arange(1000, 6200, 200)), fitfunc=Fit.gaussian_fit,fileprefix='thrscan')
    # # rp = rtplot.Rtplot(acstimescan, cal.closedevice, xdata=list(np.arange(0.1, 40, 1)), fitfunc=Fit.rabi_fit,fileprefix='individualtimescan22')
    # # rp = rtplot.Rtplot(acsrt, cal.closedevice)
    # # for ion in range(cal.ion_num):
    # #     rp = rtplot.Rtplot(lambda t: acstimescan_multi(t, ion=ion), autorunstop(ion), xdata=list(np.arange(0.1, 1000, 10)), fitfunc=Fit.rabi_fit,fileprefix='individualtimescan', autoRun=True)
    #
    # # rp = rtplot.Rtplot(cal.selectseq(seq=cal.spellComb["CCDdetection"]), stop, xdata=list(np.arange(0,10,1)), fitfunc=Fit.rabi_fit, fileprefix='detection', autoRun=True)
    # # rp = rtplot.Rtplot(cal.selectseq(seq=cal.spellComb["CCDpumping"]), cal.closedevice, xdata=list(np.arange(0,10,1)), fitfunc=Fit.rabi_fit, fileprefix='pumping', autoRun=True)
    # rp = rtplot.Rtplot(exp, cal.closedevice, xdata=list(np.arange(0.1, 30, 1)),fileprefix='CCDshelvingdetection')
    #
    #
    #
    #
    #
    #
    # # for i in range(10):
    # #     cal.seq.loadSeq(cal.spellComb["CCDdetection"])
    # #     cal.ctrl_ccd_kinetics_on(repeats=100, binning=(1,256), roi=(128,128,256,256))
    # #     time.sleep(1)
    # #     cal.seq.startSeq(repeatTimes=100)
    # #     cal.seq.setIdle()
    # #     image = cal.save_ccd_kinetics_data(fname='detection', filetime=tnow(), scanvalue=('11.241-%d'%i))
    # #     pl.plot(np.mean(image, axis=0)[0])
    # #     pl.show()
    # #     print(image.shape, np.max(image))
    # #
    # cal.seq.loadSeq(cal.spellComb["CCDpumping"])
    # cal.ctrl_ccd_kinetics_on(repeats=100, binning=(1,1), roi=(128,128,256,256))
    # cal.seq.startSeq(repeatTimes=100)
    # cal.seq.setIdle()
    # image = cal.save_ccd_kinetics_data(fname='pumping', filetime=tnow(), scanvalue='11.241-100')
    # print(image.shape, np.max(image))
    # pl.imshow(np.mean(image, axis=0))
    # # pl.plot(np.mean(image, axis=0)[0])
    # pl.show()
    #
    #
    # # tscan = np.arange(25, 39.5, 0.5)
    # # for t in tscan:
    # #     cal.set_ddsfreq(145.215, channel=2, profile=0, ddschoice=0)
    # #     cal.seq.scanValue = t
    # #     cal.seq.loadSeq(cal.spellComb["411i1ACS"])
    # #     cal.ctrl_ccd_kinetics_on(repeats=100, binning=(1, 1), roi=(128, 128, 256, 256))
    # #     cal.seq.startSeq(repeatTimes=100)
    # #     cal.seq.setIdle()
    # #     image = cal.save_ccd_kinetics_data(fname='411i1', filetime=tnow(), scanvalue='%.3f'%t)
    # #
    # # pl.imshow(np.sum(image, axis=0))
    # # pl.show()