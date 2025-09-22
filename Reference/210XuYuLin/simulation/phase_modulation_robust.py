# -*- coding: utf-8 -*-
"""
This code designs a phase-modulated MS gate
by dividing into equal segments with adjustable phases on each segment
"""
import numpy as np
from scipy.optimize import minimize
from scipy.sparse.linalg import eigsh
from scipy.special import jv
import matplotlib.pyplot as plt
import TrapFreqCAL

def alpha_seg(t1, t2, mu, omega_k, tau=0, ramp='linear'):
    # tau: ramp time before and after segment
    # ramp: waveform, e.g., linear or sin
    # t2 - t1 should be larger than 2tau
    t1 = np.reshape(t1, (-1, 1))
    t2 = np.reshape(t2, (-1, 1))
    omega_k = np.reshape(omega_k, (1, -1))
    if ramp == 'linear':
        res = np.exp(-0.5j * (t1 + t2) * (mu - omega_k)) \
            * np.sinc(0.5 * (mu - omega_k) * tau / np.pi) \
            * np.sinc(0.5 * (mu - omega_k) * (t2 - t1 - tau) / np.pi) \
            * 0.5 * (t2 - t1 - tau)
    if ramp == 'sin':
        # sin^2 [pi/2*t/tau] ramping function
        res = np.pi**2 * np.exp(-0.5j * (t1 + t2) * (mu - omega_k)) \
            * np.sinc((np.pi - np.abs((mu - omega_k) * tau)) / 2 / np.pi) \
            / 2 / (np.pi + np.abs((mu - omega_k) * tau)) \
            * np.sinc(0.5 * (mu - omega_k) * (t2 - t1 - tau) / np.pi) \
            * 0.5 * (t2 - t1 - tau)
    return(res)
def phi_seg_diag(t1, t2, mu, omega_k, tau=0, ramp='linear'):
    t1 = np.reshape(t1, (-1, 1))
    t2 = np.reshape(t2, (-1, 1))
    omega_k = np.reshape(omega_k, (1, -1))
    if ramp == 'linear':
        # Evaluation of this function requires high numerical accuracy
        # We divide it into several steps
        # First, evaluate intermediate functions of (mu-omega_k)*tau
        x = (mu - omega_k) * tau
        f1 = (1 - np.exp(-1j * x))**2 / x**2
        f2 = (1 + 1j * x - np.exp(1j * x)) / x**2
        # The term we want has accuracy of x^4 from direct evaluation
        # The Taylor series expansion has accuracy of x^2 after truncation
        # For balance we set 1e-16/x^4 ~ x^2
        ind = np.abs(x) < 2e-3
        f1[ind] = (-1 + 1j * x + 7 / 12 * x**2 - 1j / 4 * x**3)[ind]
        f2[ind] = (0.5 + 1j / 6 * x - 1 / 24 * x**2 - 1j / 120 * x**3)[ind]
        res = (3 * np.exp(1j * (mu - omega_k) * (t2 - t1)) * f1 + 6 * f2 
               + 1j * (mu - omega_k) * (3 * (t2 - t1) - 4 * tau)) \
            / 12 / (mu - omega_k)**2
        ind = np.abs((mu - omega_k) * (t2 - t1)) < 1e-6
        res[ind] = (1 / 8 * (t2 - t1 - tau)**2 * np.ones(omega_k.shape))[ind]
    if ramp == 'sin':
        res = (1j * (mu - omega_k)**5 * tau**4 * (4 * (t2 - t1) - 5 * tau)
               - 1j * np.pi**2 * (mu - omega_k)**3 * tau**2 
                               * (8 * (t2 - t1) - 11 * tau)
               - np.pi**4 * (np.exp(1j * (mu - omega_k) * (t2 - t1))
                             * (1 + np.exp(-1j * (mu - omega_k) * tau))**2
                             - 2 * np.exp(1j * (mu - omega_k) * tau) - 2
                             - 2j * (mu - omega_k) 
                                     * (2 * (t2 - t1) - 3 * tau))) \
            / 16 / (mu - omega_k)**2 / (np.pi**2 
                                        - (mu - omega_k)**2 * tau**2)**2
        ind = np.abs((mu - omega_k) * (t2 - t1)) < 1e-6
        res[ind] = (1 / 8 * (t2 - t1 - tau)**2 * np.ones(omega_k.shape))[ind]
        ind = np.abs((mu - omega_k) * tau * np.ones((t2 - t1).shape) 
                     - np.pi) < 1e-6
        res[ind] = ((-17j * np.pi 
                     + (1 + np.exp(1j * (mu - omega_k) * (t2 - t1))) * np.pi**2
                     + 16j * (mu - omega_k) * (t2 - t1))
                    / 64 / (mu - omega_k)**2)[ind]
        ind = np.abs((mu - omega_k) * tau * np.ones((t2 - t1).shape) 
                     + np.pi) < 1e-6
        res[ind] = ((17j * np.pi 
                     + (1 + np.exp(1j * (mu - omega_k) * (t2 - t1))) * np.pi**2
                     + 16j * (mu - omega_k) * (t2 - t1))
                    / 64 / (mu - omega_k)**2)[ind]
    return(res)

def phi_seg(t1, t2, mu, omega_k, tau=0, ramp='linear'):
    alpha = alpha_seg(t1, t2, mu, omega_k, tau, ramp)
    theta = alpha[:, np.newaxis, :].conj() * alpha[np.newaxis, :, :]
    n = alpha.shape[0]
    ind = np.arange(n).reshape((-1, 1, 1)) <= np.arange(n).reshape((1, -1, 1))
    theta[np.repeat(ind, alpha.shape[1], axis=2)] = 0
    theta[range(n), range(n), :] = phi_seg_diag(t1, t2, mu, omega_k, tau, ramp)
    return(theta * 2)

def robust_sequence(nseg, tau, mu, omega_k, g_ik, nk, x0='search',
                    display=False, regularization=0, 
                    ramp_tau=0, ramp='linear'):
    # g_ik = b_ik * eta_k for two target ions
    # n_k thermal phonon number for each mode
    t_list = np.linspace(0, tau, nseg + 1)
    alpha = alpha_seg(t_list[:-1], t_list[1:], mu, omega_k, ramp_tau, ramp)
    alpha1_nk = g_ik[0, :].reshape((1, -1)) * alpha
    alpha2_nk = g_ik[1, :].reshape((1, -1)) * alpha
    beta_k = 2 * (2 * nk.reshape((1, -1)) + 1)
    M_ij = (alpha1_nk.conj() * beta_k) @ alpha1_nk.T \
            + (alpha2_nk.conj() * beta_k) @ alpha2_nk.T
    M_ij = (M_ij + M_ij.T.conj()) / 2
    
    theta = phi_seg(t_list[:-1], t_list[1:], mu, omega_k, ramp_tau, ramp)
    gamma_ij = np.sum((g_ik[0, :] * g_ik[1, :]).reshape((1, 1, -1)) * theta,
                      axis=2)
    
    # For robust solution, consider time integral, 
    # i.e. cumsum of discrete segments
    alpha1_global = alpha1_nk * np.arange(nseg, 0, -1).reshape((-1, 1))
    alpha2_global = alpha2_nk * np.arange(nseg, 0, -1).reshape((-1, 1))
    M_ij_global = (alpha1_global.conj() * beta_k) @ alpha1_global.T \
                   + (alpha2_global.conj() * beta_k) @ alpha2_global.T
    M_ij_global = (M_ij_global + M_ij_global.T.conj()) / 2
    G_ij_global = gamma_ij * np.arange(nseg, 0, -1).reshape((-1, 1))
    G_ij_global = (G_ij_global + G_ij_global.T.conj()) / 2
    gamma_ij = (gamma_ij - gamma_ij.T.conj()) / 2j
    
    # Consider symmetric pulses phi(i) = -phi(nseg-i-1)
    # Set middle phase to zero
    nsub = nseg // 2
    if nseg % 2 == 0:
        phase_full = lambda x : np.concatenate((x, -x[::-1]))
    else:
        phase_full = lambda x : np.concatenate((x, [0], -x[::-1]))
    # optimize pulse sequence
    fun = lambda x : obj_fun(phase_full(x), M_ij_global, G_ij_global, 
                             gamma_ij, regularization)
    symmetric_grad = lambda x : np.real(x[:nsub] - x[-1:-nsub-1:-1])
    grad = lambda x : symmetric_grad(obj_grad(phase_full(x), 
                                              M_ij_global, G_ij_global, 
                                              gamma_ij, regularization))
    if type(x0) == str and x0 == 'search':
        x0 = np.arange(nseg) * optimize_symmetric(nseg, M_ij, gamma_ij,
                                                  display)
        x0 = (x0 - np.mean(x0))[:nsub]
    elif type(x0) != str and len(x0) == nsub:
        x0 = np.copy(x0)
    else:
        x0 = 2 * np.pi * np.random.rand(nsub)
    sol = minimize(fun, x0, method='BFGS', jac=grad)
    rabi = getRabi(phase_full(sol.x), gamma_ij)
    return(infid(phase_full(sol.x), M_ij * rabi**2, gamma_ij * rabi**2), 
           rabi, phase_full(sol.x),sol.x)
    
def obj_fun(x, M, G, gamma, regularization=0):
    phi_ij = x.reshape((-1, 1)) - x.reshape((1, -1))
    cos_ij = np.cos(phi_ij)
    sin_ij = np.sin(phi_ij)
    theta = np.sum(np.real(gamma) * cos_ij - np.imag(gamma) * sin_ij)
    scale = np.pi / 4 / np.abs(theta)
    M = M * scale
    G = G * scale
    res = 0.5 * np.sum(np.real(M) * cos_ij - np.imag(M) * sin_ij) \
            + np.sum(np.real(G) * cos_ij - np.imag(G) * sin_ij)**2 \
            + regularization * scale # minimizing Omega^2
    # print(res)
    return(res)
def obj_grad(x, M, G, gamma, regularization=0):
    phi_ij = x.reshape((-1, 1)) - x.reshape((1, -1))
    cos_ij = np.cos(phi_ij)
    sin_ij = np.sin(phi_ij)
    theta = np.sum(np.real(gamma) * cos_ij - np.imag(gamma) * sin_ij)
    scale = np.pi / 4 / np.abs(theta)
    M = M * scale
    G = G * scale
    res = np.sum(-np.real(M) * sin_ij - np.imag(M) * cos_ij, axis=1) \
            + 4 * np.sum(np.real(G) * cos_ij - np.imag(G) * sin_ij) \
                * np.sum(-np.real(G) * sin_ij - np.imag(G) * cos_ij, axis=1)
    res += - (0.5 * np.sum(np.real(M) * cos_ij - np.imag(M) * sin_ij)
              # note the additional factor 2 here for G
              + 2 * np.sum(np.real(G) * cos_ij - np.imag(G) * sin_ij)**2) \
            / theta * 2 * np.sum(-np.real(gamma) * sin_ij
                                 - np.imag(gamma) * cos_ij, axis=1)
    res += regularization * 2 * scale / theta \
            * np.sum(np.real(gamma) * sin_ij + np.imag(gamma) * cos_ij, 
                     axis=1)
    return(res)
def getRabi(x, gamma):
    phi_ij = x.reshape((-1, 1)) - x.reshape((1, -1))
    cos_ij = np.cos(phi_ij)
    sin_ij = np.sin(phi_ij)
    theta = np.sum(np.real(gamma) * cos_ij - np.imag(gamma) * sin_ij)
    scale = np.pi / 4 / np.abs(theta)
    return(np.sqrt(scale))

def infid(x, M, gamma):
    # for this part, use the original M and gamma
    phi_ij = x.reshape((-1, 1)) - x.reshape((1, -1))
    cos_ij = np.cos(phi_ij)
    sin_ij = np.sin(phi_ij)
    theta = np.sum(np.real(gamma) * cos_ij - np.imag(gamma) * sin_ij)
    if theta > 0:
        res = (theta - np.pi / 4)**2
    else:
        res = (theta + np.pi / 4)**2
    res += np.sum(np.real(M) * cos_ij - np.imag(M) * sin_ij)
    return(res)
def optimize_symmetric(nseg, M, gamma, display=True):
    lam = eigsh(M, k=1, M=gamma, sigma=0)[0][0]
    A = M - lam * gamma
    def real_part(x):
        v = np.exp(-1j * np.arange(nseg) * x)
        return(np.abs(v.conj() @ (A @ v)))
    def imag_part(x):
        v = np.exp(-1j * np.arange(nseg) * x)
        return(np.sum(np.abs(np.imag((A @ v) * v.conj()))))
    m = 1000
    theta = np.linspace(0, 2 * np.pi, m)
    data = np.zeros(m)
    for i in range(m):
        data[i] = real_part(theta[i]) + imag_part(theta[i])
    if display:
        plt.figure()
        plt.plot(theta / 2 / np.pi, data)
    return(theta[np.argmin(data)])
def optimize_symmetric2(nseg, M, gamma, display=True):
    count = np.arange(nseg, 0, -1)
    count[1:] = count[1:] * 2
    def evaluate(A, x):
        cosx = np.cos(np.arange(nseg) * x)
        sinx = np.sin(np.arange(nseg) * x)
        res = np.sum(np.real(A[0, :]) * cosx * count) \
                + np.sum(np.imag(A[0, :]) * sinx * count)
        return(res)
    m = 1000
    theta = np.linspace(0, 2 * np.pi, m)
    data = np.zeros(m)
    for i in range(m):
        data[i] = np.abs(evaluate(M, theta[i]) / evaluate(gamma, theta[i]))
    if display:
        plt.figure()
        plt.plot(theta / 2 / np.pi, data)
    return(theta[np.argmin(data)])
def smoothing(phi):
    y = (phi / 2 / np.pi) % 1
    dif = (y[1:] - y[:-1]) % 1
    dif[dif > 0.5] -= 1
    y = np.insert(np.cumsum(dif), 0, 0)
    return(y * 2 * np.pi)
def single_frequency_oscillation(omega_k, g_ik, nu, dphi, cut=1):
    # We can model the effect of a single-freq oscillation
    # dphi*cos(nu*t+varphi)
    # as Bessel modulation up to certain cutoff to the collective phonon modes
    # Output is the modulated mode frequency and mode vector
    omega_new = omega_k
    g_new = g_ik * jv(0, dphi)
    for i in range(cut):
        omega_new = np.concatenate((omega_new, 
                                    omega_k + (i + 1) * nu,
                                    omega_k - (i + 1) * nu))
        g_new = np.concatenate((g_new,
                                g_ik * jv(i + 1, dphi),
                                g_ik * jv(i + 1, dphi)), axis=1)
    return(omega_new, g_new)

if __name__ == "__main__":
    
    f_com = 1.6023
    pos = [0, 5.8, 11.2, 17]
    
    TFcalc = TrapFreqCAL.trapfreqcalc(f_com, pos)
    V, freq = TFcalc.calc_normal_mode()
    print(freq)
    
    
    nseg = 15
    tau = 150
    ramp_tau = 2
    mu = 2 * np.pi * 1.6223
    # omega_k = 2 * np.pi * np.array([1.5693,1.6004])
    # omega_k = 2 * np.pi * np.array([1.4671, 1.5238, 1.5685, 1.5997])
    omega_k = 2 * np.pi * np.array([1.4696, 1.5268, 1.5715, 1.6023])
    eta_k = 2 * 2 * np.pi / 411e-9 * np.sqrt(6.62607e-34 / 2 / np.pi / 2 / 171 / 1.66054e-27 / omega_k / 1e6)
    # b_ik = np.array([[0.5, 0, -0.5, 0.70710678],
    #                      [0.5, 0, 0.5, -0.70710678]])
    # b_ik = np.array([[0.6767, 0.5, 0.214, 0.5], 
    #                  [-0.6767, 0.5, -0.214, 0.5]])
    # b_ik = np.array([[0.70710678], [0.70710678]])
    b_ik = V[[0, 3], :]
    g_ik = eta_k.reshape((1, -1)) * b_ik
    nk = np.ones(4) * 0.0
    
    # t1 = np.array([0, 10, 20, 30])
    # # t2 = np.array([10, 20, 30, 40])
    x0 = 2*np.pi*np.array([0.683, 0.0048,  0.305,  0.391, 0.202, 1.3, 1.04, 0, 
                            -1.04, -1.3, -0.202, -0.391, -0.305, -0.0048, -0.683])
    # print(phi_seg_diag(t1, t2, mu, omega_k, tau=0, ramp='sin'))
    # print(alpha_seg(t1, t2, mu, omega_k, tau=0, ramp='sin'))
    infd, rabi, phaseseq, x = robust_sequence(nseg, tau, mu, omega_k, g_ik, nk, x0='random',
                                              display=False, regularization=10, 
                                              ramp_tau=ramp_tau, ramp='sin')
    
    print(infd, rabi)
