import numpy as np
from scipy.optimize import curve_fit


def FWHM(x, y):
    i = np.argmax(y)
    y = abs(y - np.max(y) / 2)
    x1 = x[np.argmin(y[:i])]
    x2 = x[i + np.argmin(y[i:])]
    return x2 - x1


def cal_frequency(x, y):
    N = len(y)
    bw = 1 / ((x[-1] - x[0]) / (len(x) - 1))
    fft_y = np.abs(np.fft.fft(y - np.mean(y))) / N
    fft_y[1:] = fft_y[1:] + fft_y[:0:-1]
    fft_y = fft_y[:int(N / 2) + 1]
    f = np.linspace(0, 1, N, endpoint=False)[:int(N / 2) + 1] * bw
    return f[np.argmax(fft_y)]


def gaussian(x, amp, x0, sgmx, bg):
    res = amp * np.exp(- (x - x0) ** 2 / (2 * sgmx ** 2)) + bg
    return res


def gaussian_2d(var, amp, x0, y0, sgmx, sgmy, bg):
    x = var[0]
    y = var[1]
    res = amp * np.exp(- (x - x0) ** 2 / (2 * sgmx ** 2)
                       - (y - y0) ** 2 / (2 * sgmy ** 2)) + bg
    return res


def rabi_osc(omg, f, f0, t, phi):
    dlt = f - f0
    res = omg ** 2 / (dlt ** 2 + omg ** 2) * np.sin(np.sqrt(dlt ** 2 + omg ** 2) * t + phi) ** 2
    return res


def drive_frequency_fit(data):
    x = data[:, 0]
    y = data[:, 1]

    omg_t = FWHM(x, y) / np.sqrt(2)
    f0_t = x[np.argmax(y)]
    t_t = np.pi / 2 / omg_t
    p0_t = [omg_t, f0_t, t_t]
    p0, _ = curve_fit(lambda f, omg, f0, t: rabi_osc(omg, f, f0, t, 0), x, y, p0_t)
    # [omg, f0, t] = p0

    return p0


def rabi_frequency_fit(data):
    x = data[:, 0]
    y = data[:, 1]

    omg_t = cal_frequency(x, y) / 2 * 2 * np.pi
    p0_t = [omg_t]
    p0, _ = curve_fit(lambda t, omg: rabi_osc(omg, 0, 0, t, 0), x, y, p0_t)
    # [omg, f0, t] = p0

    return p0


def gauss_coherence_fit(data, tau_t=100e3):
    x = data[:, 0]
    y = data[:, 1]

    omg_t = cal_frequency(x, y) / 2 * 2 * np.pi
    # tau_t = 100e3
    p0_t = [omg_t, tau_t]
    p0, _ = curve_fit(lambda t, omg, tau: 0.5 + (rabi_osc(omg, 0, 0, t, np.pi/2) - 0.5) * np.exp(- (t / tau) ** 2), x, y, p0_t)

    return p0


def gauss_decay_fit(data, tau_t=100e3):
    x = data[:, 0]
    y = data[:, 1]

    # tau_t = 100e3
    p0_t = [tau_t]
    p0, _ = curve_fit(lambda t, tau: 0.5 + 0.5 * np.exp(- (t / tau) ** 2), x, y, p0_t)

    return p0


def exp_decay_fit(data, tau_t=100e3):
    x = data[:, 0]
    y = data[:, 1]

    # tau_t = 100e3
    p0_t = [tau_t]
    p0, _ = curve_fit(lambda t, tau: 0.5 + 0.5 * np.exp(- (t / tau)), x, y, p0_t)

    return p0
