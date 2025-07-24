from RTMQ.Interface import intf
from RTMQ import Assembler as asmblr
from RTMQ.StdLib import R, ExpFlow, CfgFlow
import IonCtrl_RWG_API as rwg
import IonCtrl_Main_API as main
from oasm import *

from time import sleep
import RTMQ.StdLib as std
std.SET = std.Set

rwg_slots = [3,5,6,7]
ctr_slots = [7]
gpio_dir = [0b0000, 0b0000, 0b0000, 0b1000,
            0b00000000_00000000_00000000_11111111]
ext_pmt32 = False


def ResetUSB():
    while True:
        if intf.device.open_cnt != 0:
            intf.__exit__(0, 0, 0)
        else:
            break
    with intf:
        intf.device.dev.cycleDevicePort()
    sleep(0.8)
    with intf:
        intf.baud_reset()
    sleep(0.05)
    intf.__enter__()


def SystemInit(adr, bdr=2):
    if isinstance(adr, int):
        adr = [adr]
    f = ExpFlow(rwg.C_RWG)
    with f:
        std.StartUntimedTask()
        std.SetRTCF(upl=0, bdr=bdr, typ=0, hop=1)
        R.LED = 0
        R.DCA = 0
        R.DCD = 0
        rwg.RWG_Init()
    fM = ExpFlow(main.C_MAIN)
    with fM:
        std.StartUntimedTask()
        R.LED = 0
        R.DCA = 0
        R.DCD = 0
        std.SetRTCF(upl=0, bdr=bdr, typ=0, hop=0)
        std.RTLkSend(0)
    for a in adr:
        intf.run(a, Assemble(a, f), 0)
    intf.run(0, Assemble(0, fM), 1)


def Init():
    # SystemInit(range(1, 9), 2)
    for adr in range(len(rwg_slots)):
        f = ExpFlow(rwg.C_RWG)
        with f:
            std.StartUntimedTask()
            R.LED = 0
            R.DCA = 0
            R.DCD = 0
            rwg.Cfg_GPIO(dir=gpio_dir[adr], inv=0,
                         pos=gpio_dir[adr], neg=0, trg=0)
            for c in range(4):
                if c+4*adr < len(DDS.List):
                    car = DDS.List[c+4*adr]
                    rwg.Set_Carrier(
                        c, car.f[0](), car.a[0]() or 0, car.p[0]() or 0, upd=True)
            rwg.RWG_Sync()
            std.RTLkSend(0)
        intf.run(rwg_slots[adr], Assemble(rwg_slots[adr], f), 1)
    f = CfgFlow(main.C_MAIN)
    with f:
        main.Cfg_GPIO(dir=gpio_dir[-1], inv=0,
                      pos=gpio_dir[-1], neg=0, trg=0)
        R.LED = 0
        R.DCA = 0
        R.DCD = 0
        std.RTLkSend(0, wait=False)
    intf.run(0, Assemble(0, f), 1)
    Run(Seq(Wave).Idle(10))


def DumpCache(adr):
    seg_len = 400
    if type(adr) == int:
        adr = [adr]
    ret = []
    for a in adr:
        core = main.C_MAIN if a == 0 else rwg.C_RWG
        f = CfgFlow(core, True, False)
        with f:
            R.DCA = 0
            std.RTLkSend(R.DCD, wait=False)
        cnt = intf.run(a, Assemble(a, f), 1)[0]
        sgs = 0
        tmp = []
        while cnt > sgs:
            seg = min(cnt - sgs, seg_len)
            f = ExpFlow(core)
            with f:
                std.StartUntimedTask()
                with std.Scan(R.DCA, sgs+1, sgs+seg+1, 1):
                    std.Wait(10)
                    std.RTLkSend(R.DCD)
            res = intf.run(a, Assemble(a, f), seg)
            sgs += seg
            tmp += res
        ret += [tmp]
    return ret


class Compiler:
    def reset(self):
        self.ttl = 0
        self.last_ttl = 0
        self.sbg = [{}, {}, {}, {}]

    def body(self, seq):
        for i in range(len(seq)):
            w = seq[i]
            if type(w) is str:
                std.ASM(w)
            elif type(w) is Expr:
                Eval(w, Env+[std.__dict__], this=self)
            elif type(w) in (tuple, list, Seq):
                self.body(w)
            elif type(w) is Obj and w['...'] is Wave:
                for j in range(w.num()):
                    self.wave(w, j)
            elif callable(w):
                w(self)


def RTCall(core, func, *args, **kwargs):
    def run():
        flow = ExpFlow(core)
        with flow:
            func(*Eval(args), **Eval(kwargs))
        return flow.assem[2:-3]
    std.ASM([run])


class RWGCompiler(Compiler):
    def __init__(self, adr):
        self.adr = adr
        self.stat = []

    def compile(self, prog, repeats=100):
        self.now = 0
        self.flow = ExpFlow(rwg.C_RWG)
        with self.flow:
            std.StartUntimedTask()
            R.DCA = 0
            R.DCD = 0
            std.RTLkSend(0)
            rwg.Wait_Master()
            with std.LoopForever() if repeats is True else std.Repeat(R.R0, repeats):
                rwg.RWG_Sync()
                self.origin = ((1, 1, 1, 1), [1, 1, 1, 1])  # True
                self.reset()
                self.body(prog)

    def wave(self, w, idx):
        dur = w[idx]()
        # print(dur)
        self.last_ttl = self.ttl
        self.ttl = 0
        for ttl in (w.ttl[idx]() or []):
            if ttl // 4 != self.adr:
                continue
            self.ttl |= 1 << (ttl % 4)
        # print(w,w.ttl[idx](),self.ttl,w.dds[idx]())
        for chn in range(4):
            name = DDS.Name[4*self.adr+chn]
            off = DDS.List[4*self.adr+chn].off
            dds = (-(w.dds[idx]() or Arg()))[name] or off
            num = [int(i.split('.')[-1]) for i in dds[:].keys()]
            num = max(num) if len(num) > 0 else 0
            state = {}
            for i in range(1, num+1):
                sbg = i - 1
                frq = dds.f[i]() or 0
                am_p = dds.a[i]() or 0
                am_n = dds.a[-i]() or 0
                pha = dds.p[i]() or 0
                fsi, ar_p, ar_n = None, None, None
                if type(frq) in (tuple, list):
                    frq, fsi = frq[0], (frq[1]-frq[0])/dur
                else:
                    fsi = None
                if type(am_p) in (tuple, list):
                    # print(name,am_p)
                    am_p, ar_p = am_p[0], (am_p[1]-am_p[0])/dur
                else:
                    ar_p = None
                if type(am_n) in (tuple, list):
                    am_n, ar_n = am_n[0], (am_n[1]-am_n[0])/dur
                else:
                    ar_n = None if ar_p is None else 0
                state[sbg] = (frq, am_p, am_n, pha, fsi, ar_p, ar_n)
            # if name in ('LAOM411','LAOD','LSAOM411','RAOD','RAOM411','RSAOM411'):
            #    print('Conf: ',name, chn, sbg, (frq, am_p, am_n, pha, fsi, ar_p, ar_n))
            # print(chn,self.sbg[chn].get(sbg,None),state,self.sbg[chn].get(sbg,None) != state)
            last_state = self.sbg[chn].get('cfg', None)
            if not Equal(last_state, state):
                now = self.sbg[chn].get('now', 0)
                if last_state is None:
                    self.origin[1][chn] = 1
                    now = self.now
                else:
                    for sbg, val in state.items():
                        conf = last_state.get(sbg, None)
                        if conf is None or not Equal(conf[0], val[0]):
                            self.origin[1][chn] = 1
                            now = self.now
                            break
                for sbg, val in state.items():
                    if self.origin[1][chn] == 0 and Equal(last_state.get(sbg, None), val):
                        continue
                    frq, am_p, am_n, pha, fsi, ar_p, ar_n = val
                    if fsi is None and ar_p is None and ar_n is None:
                        self.stat.append(('set_sbg',chn,sbg,frq,am_p,pha))
                        # if name in ('MW',):
                        #    print(name, (chn, sbg, frq, am_p, am_n, pha, True, self.now))
                        if Expr in (type(frq), type(am_p), type(am_n), type(pha), type(now)):
                            RTCall(rwg.C_RWG, rwg.Set_SBG, chn, sbg,
                                   frq, am_p, am_n, pha, True, now)
                        else:
                            rwg.Set_SBG(chn, sbg, frq, am_p,
                                        am_n, pha, True, now)
                        # self.origin[1][chn] = 1
                        # print(f'{name} adr {self.adr}-ch {chn} SBG[{sbg}]({frq},{am_p},{am_n},{pha})')
                    else:
                        if Expr in (type(fsi), type(ar_p), type(ar_n)):
                            RTCall(rwg.C_RWG, rwg.Set_Ramp,
                                   chn, sbg, fsi, ar_p, ar_n)
                        else:
                            rwg.Set_Ramp(chn, sbg, fsi, ar_p, ar_n)
                self.sbg[chn]['cfg'] = state
                self.sbg[chn]['now'] = now
                # if name in ('MW',):
                #     print(name, chn, sbg, val, self.origin[1][chn], now, self.now)
                # self.origin[1][chn] = 0
                # print(f'{name} adr {self.adr}-ch {chn} Ramp[{sbg}]({fsi},{ar_p},{ar_n})')
        mrk = (self.ttl & 1, self.ttl >> 1 & 1,
               self.ttl >> 2 & 1, self.ttl >> 3 & 1)
        self.stat.append(('play_wave',dur,self.origin))
        if type(dur) is Expr:
            dur = sym.round(dur * 300)
            RTCall(rwg.C_RWG, rwg.RWG_PlayWave, dur, self.origin,
                   sfq=(1, 1, 1, 1), sam=(1, 1, 1, 1), mrk=mrk)
        else:
            dur = round(dur * 300)
            rwg.RWG_PlayWave(dur, self.origin, sfq=(
                1, 1, 1, 1), sam=(1, 1, 1, 1), mrk=mrk)
        self.now += dur & -2
        self.origin = ((0, 0, 0, 0), [0, 0, 0, 0])
        last_ctr = self.last_ttl & gpio_dir[self.adr]
        ctr = self.ttl & gpio_dir[self.adr]
        if last_ctr > 0 and ctr == 0:
            rwg.Save_Count(last_ctr, ext_pmt32)


class MainCompiler(Compiler):
    def __init__(self):
        self.adr = len(rwg_slots)

    def compile(self, prog, repeats=100):
        self.now = 0
        self.flow = ExpFlow(main.C_MAIN)
        with self.flow:
            std.StartUntimedTask()
            R.DCA = 0
            R.DCD = 0
            main.Trig_Slave(rwg_slots, 175)
            with std.LoopForever() if repeats is True else std.Repeat(R.R0, repeats):
                std.StartTimedTask(300)
                self.reset()
                self.body(prog)
            std.RTLkSend(0)

    def wave(self, w, i):
        dur = w[i]()
        self.last_ttl = self.ttl
        self.ttl = 0
        for ttl in (w.ttl[i]() or []):
            if ttl < 4*len(rwg_slots):
                continue
            self.ttl |= 1 << (ttl-4*len(rwg_slots))
        if type(dur) is Expr:
            dur = sym.round(dur * 300)
            RTCall(main.C_MAIN, main.TTL_Stage, dur, self.ttl)
        else:
            dur = round(dur * 300)
            main.TTL_Stage(dur, self.ttl)
        self.now += dur & -2
        last_ctr = self.last_ttl & gpio_dir[-1]
        ctr = self.ttl & gpio_dir[-1]
        if last_ctr > 0 and ctr == 0:
            main.Save_Count(last_ctr)


def Assemble(*args):
    if len(args) == 2:
        addr, flow = args
        buf = asmblr.reach_node(addr)
        if flow.typ == "cfg":
            if flow.ssp:
                buf += asmblr.suspend_node(addr)
            buf += asmblr.node_exec(addr, flow.assem, flow.core)
            if flow.rsm:
                buf += asmblr.resume_node(addr)
        else:
            prg = asmblr.asm_program(flow.assem, flow.core)
            buf += asmblr.reset_node(addr) + \
                asmblr.download_to(addr, prg, flow.core) + \
                asmblr.resume_node(addr)
        return buf
    else:
        assem = args[0]
        code = []
        for adr in range(len(rwg_slots)+1):
            addr = 0 if adr == len(rwg_slots) else rwg_slots[adr]
            flow = assem[adr].flow
            code.append((Assemble(addr, flow), Eval(assem[adr].now)))
        return code


def Compile(prog, repeats=100, save=None):
    import time
    if save is not None:
        save = open(save, 'w')
    assem = []
    for adr in range(len(rwg_slots)):
        comp = RWGCompiler(adr)
        tic = time.time()
        comp.compile(prog, repeats)
        # print(f'RWG Compiler-{adr}:', time.time()-tic)
        if save is not None:
            save.write(f'% RWG{adr}' + ('-'*20) + '\n')
            save.write('\n'.join(comp.flow.assem))
        assem.append(comp)
    comp = MainCompiler()
    tic = time.time()
    comp.compile(prog, repeats)
    # print(f'Main Compiler:', time.time()-tic)
    if save is not None:
        save.write(f'% Main' + ('-'*20) + '\n')
        save.write('\n'.join(comp.flow.assem))
        save.close()
    assem.append(comp)
    return assem


def Run(prog, repeats=100):
    if not (type(prog[0]) is tuple and type(prog[0][0]) is bytearray):
        if not isinstance(prog[0], Compiler):
            prog = Compile(prog, repeats)
        prog = Assemble(prog)
    tot = [0]*(len(rwg_slots)+1)
    for adr in range(len(rwg_slots)):
        buf, tot[adr] = prog[adr]
        intf.run(None, buf, 1, 1)
    # sleep(0.09)
    buf, tot[-1] = prog[-1]
    intf.run(None, buf, 1, (1e-6*max(tot)/300+1e-2)*repeats+5)
    if repeats is not True:
        res = DumpCache(ctr_slots)
        return res[0]


if __name__ == '__main__':
    # from config import *

    #SystemInit(range(1, 9), 2)
    #import sys;sys.exit(0)
    while intf.device.open_cnt > 0:
        intf.__exit__(0,0,0)
    intf.__enter__()
    
    import numpy as np
    import time
    Env[0] = globals()
    Load()

    Init()
    print('='*20)
    seq = Seq(Wave).Cooling(2000).Detection(1000, 1).Wait(1)

    def feedback(self):
        if self.adr == 0:
            std.SEL(R.CTRX, "C3")
        elif self.adr == 1:
            std.SEL(R.CTRX, "C1")
        with std.If(R.CTRX <= 2):
            self.body(Seq(Wave).Wait(11).Detection(1000, 1))
        with std.Else():
            self.body(Seq(Wave).Pumping(10, 1).Detection(1000, 1))
    # seq(feedback)
    # seq(lambda self: std.SEL(R.CTRX,"C3" if self.adr == 0 else "C1"))
    # seq.If(sym.R.CTRX<=2,Seq(Wave).Wait(11).Detection(1000,1)).Else(Seq(Wave).Pumping(10,1).Detection(1000,1))
    # seq.Pumping(10,1).Wait(1).Detection(1000,1)
    seq.Protect(10)
    print(seq)
    counts = Run(seq, 100)
    print(counts)
    print(sum(Run(Seq(Wave).Detection(1000, 1).Wait(1),100)))
    # print((np.array(counts)>1).reshape((100,2)).mean(0),counts[-2:])

   # Run([sym.SET(R.LED,this.adr+1)])
    # Run([sym.StartTimedTask(1000000.),sym.SET(R.LED,0),sym.StartTimedTask(1000000.),sym.SET(R.LED,this.adr+1)])

    # seq = Seq(Wave)(Wave(100).dds[0](LSEOM=DDS.LSEOM.ramp).ttl[0]([8])).Protect(10)
    # print(seq)
    # cseq = Compile(seq)
    # print(cseq)
    # Init()
    # for i in range(1000):
    #    Run(cseq)
