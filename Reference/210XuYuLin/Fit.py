import numpy as np
from scipy.optimize import curve_fit
from scipy.special import gamma



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

def lorentizan(x, x0, amp, fwhm, bg):
    y = amp/(1+4*(x-x0)**2/fwhm**2) + bg

    return y

def gaussian(x, x0, amp, sgmx, bg):
    res = amp * np.exp(- (x - x0) ** 2 / (2 * sgmx ** 2)) + bg
    return res

def multi_gaussian(x, n, x0, amp, sgmx, bg):
    res = 0
    for i in range(n):
        res += gaussian(x, x0[i], amp[i], sgmx[i], bg)


def cosgaussian(x, x0, t0, sigfreq):
    res = np.cos(np.exp(-(x-x0)**2/(sigfreq**2))*t0*np.pi/2.0)**2
    return res

def singaussian(x,  x0, t0, sigfreq):
    res = np.sin(np.exp(-(x - x0) ** 2 / (sigfreq ** 2)) * t0 * np.pi / 2.0) ** 2
    return res

def possion(x, mean):
    res = (mean)**(x)/gamma(x+1)*np.exp(-mean)
    return res

def gaussian_2d(var, amp, x0, y0, sgmx, sgmy, bg):
    x = var[0]
    y = var[1]
    res = amp * np.exp(- (x - x0) ** 2 / (2 * sgmx ** 2)
                       - (y - y0) ** 2 / (2 * sgmy ** 2)) + bg
    return res

def parity_sine(x, amp, offset):

    # return amp*np.sin(2*np.pi/180*x)+offset
    return amp * np.sin(4 * np.pi * x) + offset

def rabi_osc(t, pitime, phi, tau):
    res = (1 - np.exp(-t/tau) * np.cos(np.pi/pitime * t + phi))/2.0
    return res

def gaussian_decay_sin(t, pitime, phi, tau):
    res = (1-np.exp(-t**2/tau**2) * np.cos(np.pi/pitime * t + phi))/2.0
    return res

def linear_fun(x, k, b):
    res = k*x + b
    return res

def parabola(x, x0, a, b):
    return a * (x - x0)**2 + b

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


def rabi_fit(data):
    x = data[:, 0]
    y = data[:, 1]

    omg_t = cal_frequency(x, y)
    if y[0] == 0:
        phi0 = 0
    else:
        phi0 = np.pi
    p0_t = [1.0/2.0/omg_t, y[0]*np.pi, 1.0/2.0/omg_t*4]
    print(p0_t)
    p0, _ = curve_fit(rabi_osc, x, y, p0_t, bounds=([0, -np.pi/2, 0], [np.inf, np.pi/2*3, np.inf]))
    # [omg, f0, t] = p0
    if np.abs(p0[1])<np.abs(p0[1]-np.pi):
        p0[0] = (np.pi-p0[1])*p0[0]/np.pi
    else:
        p0[0] = (np.pi - (p0[1]-np.pi)) * p0[0] / np.pi

    func = rabi_osc

    return p0, func

def gaussian_decay_sin_fit(data):
    x = data[:, 0]
    y = data[:, 1]

    omg_t = cal_frequency(x, y)
    if y[0] == 0:
        phi0 = 0
    else:
        phi0 = np.pi
    p0_t = [1.0 / 2.0 / omg_t, y[0] * np.pi, 100000]
    print(p0_t)
    p0, _ = curve_fit(gaussian_decay_sin, x, y, p0_t, bounds=([0, -np.pi / 2, 0], [np.inf, np.pi / 2 * 3, np.inf]))
    # [omg, f0, t] = p0
    if np.abs(p0[1]) < np.abs(p0[1] - np.pi):
        p0[0] = (np.pi - p0[1]) * p0[0] / np.pi
    else:
        p0[0] = (np.pi - (p0[1] - np.pi)) * p0[0] / np.pi

    func = gaussian_decay_sin

    return p0, func

def parity_sine_fit(data):
    x = data[:, 0]
    y = data[:, 1]

    # omg_t = cal_frequency(x, y)

    p0_t = [1, 0]
    p0, _ = curve_fit(parity_sine, x, y, p0_t)
    # [omg, f0, t] = p0

    func = parity_sine

    return p0, func

def sine_fit(data):
    x = data[:, 0]
    y = data[:, 1]

    omg_t = cal_frequency(x, y)

    p0_t = [1.0/2.0/omg_t, y[0]*np.pi, 200]
    # print(p0_t)
    p0, _ = curve_fit(rabi_osc, x, y, p0_t)
    # [omg, f0, t] = p0

    func = rabi_osc

    return p0, func


def ramsey_fit(data):
    p0, func = rabi_fit(data)
    p0[0] = 0.5/p0[0]

    return p0, func

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


def exp_decay_fit(data, tau_t=1e3):
    x = data[:, 0]
    y = data[:, 1]

    # tau_t = 100e3
    p0_t = [tau_t]
    p0, _ = curve_fit(lambda t, tau: 0.5 + 0.5 * np.exp(- (t / tau)), x, y, p0_t)

    return p0

def cosgaussian_fit(data, sigma=0.4):
    x = list(data[:, 0])
    y = list(data[:, 1])
    
    para0 = [x[y.index(min(y))], np.arccos(2*min(y)-1)/np.pi, sigma]
    fitpara, fitcov = curve_fit(cosgaussian, x, y, p0=para0)
    func = cosgaussian
    
    return fitpara, func

def singaussian_fit(data, sigma=0.3):
    x = list(data[:, 0])
    y = list(data[:, 1])

    para0 = [x[y.index(max(y))], np.arccos(1-2 * max(y)) / np.pi, sigma]
    fitpara, fitcov = curve_fit(singaussian, x, y, p0=para0)
    func = singaussian

    return fitpara, func

def possion_fit(data, mean=5000):
    x = data[:,0]
    y = data[:,1]
    fitpara, fitcov = curve_fit(possion, x, y, p0=[mean])
    func = possion
    return fitpara, func

def gaussian_fit(data):
    x = data[:,0]
    y = data[:,1]
    fitpara, fitcov = curve_fit(gaussian, x, y, p0=[x[list(y).index(max(y))], max(y)-min(y), FWHM(x, y), min(y)], bounds=([np.min(x), 0, 0, 0], [np.max(x), 1, np.inf, 1]))
    func = gaussian

    return fitpara, func

def inv_gaussian_fit(data):
    x = data[:, 0]
    y = data[:, 1]
    fitpara, fitcov = curve_fit(gaussian, x, y, p0=[x[list(y).index(min(y))], min(y) - max(y), FWHM(x, np.max(y)-y), max(y)], bounds=([np.min(x), -1, 0, 0], [np.max(x), 0, np.inf, 1]))
    func = gaussian

    return fitpara, func

def lorentizan_fit(data):
    x = data[:, 0]
    y = data[:, 1]
    # fwhm  = FWHM(x,np.max(y)-y)
    fitpara, fitcov = curve_fit(lorentizan, x, y, p0=[x[np.argmin(y)], min(y) - max(y), 0.2, max(y)])
    func = lorentizan

    return fitpara, func

def lorentizan_peak_fit(data):
    x = data[:, 0]
    y = data[:, 1]
    # fwhm  = FWHM(x,np.max(y)-y)
    fitpara, fitcov = curve_fit(lorentizan, x, y, p0=[x[np.argmax(y)], max(y) - min(y), 0.2, min(y)])
    func = lorentizan

    return fitpara, func

def min_fit(data):
    x = data[:,0]
    y = data[:,1]
    ymin = np.min(y)

    return [ymin], np.min

def max_fit(data):
    x = data[:,0]
    y = data[:,1]

    ymax = np.max(y)

    return [ymax], np.max

def parabola_up_down(max_mode=True):
    def parabola_fit(data):
        x = data[:, 0]
        y = data[:, 1]
        if max_mode:
            x0 = x[np.argmax(y)]
            a = (y[0]-np.max(y))/(x[0]-x0)**2
            b = np.max(y)
        else:
            x0 = x[np.argmin(y)]
            a = (y[0] - np.min(y)) / (x[0] - x0) ** 2
            b = np.min(y)
        fitpara, fitcov = curve_fit(parabola, x, y, p0=[x0, a, b], maxfev=50000)
        func = parabola

        return fitpara, func

    return parabola_fit