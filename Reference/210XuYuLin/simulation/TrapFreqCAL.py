# -*- coding: utf-8 -*-
"""
Created on Tue Dec 27 10:05:01 2022

@author: pc
"""

#计算离子单链的radial简正模式
#所需输入参数为离子位置以及质心模频率，输出各个简正模式的频率以及每个模式本征向量

import matplotlib.pyplot as pl
import numpy as np

M = 171 * 1.66054e-27  #mass-kg
ELE_CHARGE = 1.60218e-19  #charge-coulomb
EPSILON0 = 8.85419e-12

def F_int(z):
    z = np.abs(z)
    y = np.piecewise(z, [z==0, z>0], [0, lambda z: ELE_CHARGE**2/4/np.pi/EPSILON0/z**3])
    return y


class trapfreqcalc():
    def __init__(self, f_com, pos):  #pos-um, f_com-MHz
        self.N = len(pos)   #ion num
        self.pos = np.array(pos)*10**(-6) #pos-m
        self.omega = 2*np.pi*f_com*10**6  #trap frequency-Hz



    def calc_normal_mode(self):
        
        Z, Z0 = np.meshgrid(self.pos, self.pos)
        dZ = Z-Z0
        
        alpha = F_int(dZ)/M
        alpha_diag = np.diag(np.sum(alpha, axis=1))
        # print(np.sqrt(alpha))
        
        # alpha_mid = alpha[:-1]+alpha[1:]
        # alpha_all = [alpha[0]]+list(alpha_mid)+[alpha[-1]]
        omega_all = np.array([self.omega**2]*self.N)
        
        # fmatrix = np.diag([(omega**2-alpha)]+[(omega**2-2*alpha)]*(N-2)+[(omega**2-alpha)])
        fmatrix = np.diag(omega_all)-alpha_diag
        fmatrix = fmatrix + alpha
        
        # for i in range(N-1):
        #     fmatrix[i, i+1] = alpha[i]
        #     fmatrix[i+1, i] = alpha[i]
            
        E, V = np.linalg.eigh(fmatrix)
        
        freq_norm = np.sqrt(E)/10**6/2/np.pi   #trap freq--MHz
        
        return V, freq_norm
# print(V)

if __name__ == "__main__":
    pos = np.array([220, 237, 252, 266, 281, 298])*0.384  #ion position--um
    f_com = 1.440525 #trap freq of common mode--MHz
    
    calc_TF = trapfreqcalc(f_com, pos)
    V, freq = calc_TF.calc_normal_mode()
    
    pl.figure()
    ax = pl.axes()
    for i in range(len(freq)):
        ax.axvline(x = freq[i])
    
    ax.set_xlabel("freq/MHz")
    print(freq)
    print(V)
    
    
    #mode vector plot
    pl.figure()
    
    pl.imshow(V)
    pl.xlabel("mode")
    pl.ylabel("ion index")
    pl.colorbar()   
    # pl.show()
    
    #inverse inference
    # trap_freq = np.array([1.4685, 1.5249, 1.5694, 1.6004])
    # fmatrix_exp = V@np.diag((trap_freq*2*np.pi*10**6)**2)@V.T
