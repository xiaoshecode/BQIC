import math
import base64
import io

import numpy as np
from matplotlib import cm
import cv2
from PIL import Image
from scipy.ndimage import gaussian_filter, gaussian_laplace
from skimage.measure import label
from Fit import *


def background(image):
    sgm_est = 30
    hist, bin_edges = np.histogram(image.ravel(), bins=int(np.ptp(image) / (sgm_est / 10)))
    bin_mid = (bin_edges[:-1] + bin_edges[1:]) / 2

    [x, y] = [bin_mid, hist]

    amp_t = np.max(y)
    x0_t = bin_edges[np.argmax(y)]
    sgm_t = FWHM(x, y) / (2 * np.sqrt(2 * np.log(2)))
    bg_t = np.min(y)
    p0_t = [amp_t, x0_t, sgm_t, bg_t]

    p0, _ = curve_fit(gaussian, x, y, p0_t)
    [amp, x0, sgm, bg] = p0

    idx = np.where(abs(x - x0) < sgm * 2)
    y1 = y[idx]
    x1 = x[idx]

    p1_t = p0
    p1, _ = curve_fit(gaussian, x1, y1, p1_t)
    [amp, x0, sgm, bg] = p0

    return x0


def CVIONS(image, gf_sigma=1, threshold=0.3):

    def fit_one_ion(image):
        zm = np.max(image)
        [ym, xm] = divmod(np.argmax(image), image.shape[1])
        rm = 1
        while image[ym + rm, xm] > zm * threshold:
            rm += 1
        pm = [zm, xm, ym, rm]
        x = np.arange(xm - rm, xm + rm + 1)
        y = np.arange(ym - rm, ym + rm + 1)
        x, y = np.meshgrid(x, y)
        z = image[y, x]

        amp_t = np.max(z)
        x0_t = xm
        y0_t = ym
        sgmx_t = rm
        sgmy_t = rm
        p0_t = [amp_t, x0_t, y0_t, sgmx_t, sgmy_t]
        p0, _ = curve_fit(lambda var, amp, x0, y0, sgmx, sgmy:
                          gaussian_2d(var, amp, x0, y0, sgmx, sgmy, 0).ravel(),
                          (x, y),
                          z.ravel(),
                          p0_t)

        return pm, p0

    def cut_the_ion(image, p0):
        [xc, yc, sgmx, sgmy] = p0[1:5]
        x = np.arange(int(xc - sgmx * 4), math.ceil(xc + sgmx * 4))
        y = np.arange(int(yc - sgmy * 4), math.ceil(yc + sgmy * 4))
        x, y = np.meshgrid(x, y)

        image[y, x] -= gaussian_2d((x, y), *p0, 0)

    def fit_all_ions(image, para_fit0):
        para_fit1 = np.zeros((para_fit0.shape[0], para_fit0.shape[1] + 1))

        if para_fit0.shape[0] > 1:
            x0_mid = [round(i) for i in (para_fit0[:-1, 1] + para_fit0[1:, 1]) / 2]

        for i in range(para_fit0.shape[0]):
            p0_t = para_fit0[i, :]
            [x0_t, y0_t, sgmx_t, sgmy_t] = p0_t[1:]

            if para_fit0.shape[0] > 1:
                x1 = np.max([round(2 * x0_t - x0_mid[i]) if i == 0 else x0_mid[i-1],
                             int(x0_t - sgmx_t * 2)])
                x2 = np.min([round(2 * x0_t - x0_mid[i - 1]) if i == para_fit0.shape[0] - 1 else x0_mid[i],
                             math.ceil(x0_t + sgmx_t * 2)])
            else:
                x1 = int(x0_t - sgmx_t * 2)
                x2 = math.ceil(x0_t + sgmx_t * 2)

            x = np.arange(x1, x2 + 1)
            y = np.arange(int(y0_t - sgmy_t * 2), math.ceil(y0_t + sgmy_t * 2) + 1)

            x, y = np.meshgrid(x, y)
            z = image[y, x]

            bg_t = 0
            p0, _ = curve_fit(lambda var, amp, x0, y0, sgmx, sgmy, bg:
                              gaussian_2d(var, amp, x0, y0, sgmx, sgmy, bg).ravel(),
                              (x, y),
                              z.ravel(),
                              [*p0_t, bg_t])
            para_fit1[i, :] = p0

        return para_fit1

    bg = background(image)
    image = image - bg

    image_gf = gaussian_filter(image, sigma=gf_sigma)

    para_max = np.array([[]])
    para_fit0 = np.array([[]])

    while True:
        # fit one ion
        pm, p0 = fit_one_ion(image_gf)

        if para_fit0.size == 0:
            para_max = np.array([pm])
            para_fit0 = np.array([p0])
        else:
            i = np.searchsorted(para_fit0[:, 1], p0[1])
            para_max = np.insert(para_max, i, pm, axis=0)
            para_fit0 = np.insert(para_fit0, i, p0, axis=0)

        # cut the ion
        cut_the_ion(image_gf, p0)

        # check ions left
        zm = np.max(image_gf)
        [ym, xm] = divmod(np.argmax(image_gf), image.shape[1])
        if para_fit0.shape[0] == 1:
            ratio = zm / para_fit0[0, 0]
        else:
            i = np.searchsorted((para_fit0[:-1, 1] + para_fit0[1:, 1]) / 2, xm)
            ratio = zm / para_fit0[i, 0]

        if ratio < 0.5:
            break

    # fit again with raw data
    para_fit1 = fit_all_ions(image, para_fit0)

    # figure, axes = plt.subplots()
    # for p0 in para_fit1:
    #     e = Ellipse(xy=(p0[1], p0[2]), width=p0[3] * 3, height=p0[4] * 3, color='r', fill=False)
    #     axes.add_artist(e)
    # plt.title('Circle')
    # plt.imshow(image)
    # plt.show()
    return para_fit1


def CVIONS_FAST(image, LoG_sigma=1.5, threshold=0.3):
    # bg = background(image)
    # image = image - bg

    image_log = gaussian_laplace(image, LoG_sigma)

    image_log = 1 - (image_log - np.min(image_log)) / (np.max(image_log) - np.min(image_log))

    image_bn = np.where(image_log > threshold, 1, 0)

    image_lb = label(image_bn)

    lb_num = np.max(image_lb)

    para_num = 4
    para_cv = np.zeros((lb_num, para_num))

    for lb in range(1, lb_num + 1):
        count = image[image_lb == lb]
        wgt = count / np.sum(count)
        y, x = np.where(image_lb == lb)

        max_count = np.max(count)
        x0 = np.average(x, weights=wgt)
        y0 = np.average(y, weights=wgt)
        s = np.count_nonzero(image_lb == lb)

        para_cv[lb - 1, :] = [max_count, x0, y0, s]

    order = np.argsort(para_cv[:, 1])

    for i in range(para_num):
        para_cv[:, i] = para_cv[order, i]

    # figure, axes = plt.subplots()
    # for i in range(para_cv.shape[0]):
    #     circle = plt.Circle((para_cv[i, 1], para_cv[i, 2]), np.sqrt(para_cv[i, 3] / np.pi), color='r', fill=False)
    #     axes.add_artist(circle)
    # plt.title('Circle')
    # plt.imshow(image)
    # plt.pause(1)
    # plt.close()
    return para_cv

def Hopping_detect(x1, x2, threshold_diff=6):
    if len(x2) != len(x1):
        return 1
    else:
        diff_x = np.abs(np.array(x2) - np.array(x1))
        max_difference = np.max(diff_x)
        if max_difference > threshold_diff:
            return 1
        else:
            return 0




def encode_pic(image, para_cv=None):
    image = (image - np.min(image)) / (np.max(image) - np.min(image))
    pic = np.delete(np.uint8(cm.gray(image) * 255), 3, 2)

    if para_cv is not None:
        for i in range(para_cv.shape[0]):
            x = round(para_cv[i, 1])
            y = round(para_cv[i, 2])
            pic[y-1:y+2, x-1:x+2, 0] = 0
            pic[y-1:y+2, x-1:x+2, 1] = 0
            pic[y-1:y+2, x-1:x+2, 2] = 255

    ret, buf = cv2.imencode('.jpg', pic)
    return base64.b64encode(Image.fromarray(np.uint8(buf)).tobytes()).decode('utf-8')


def decode_pic(image_str):
    img = Image.open(io.BytesIO(base64.b64decode(image_str.encode('utf-8'))))
    image = np.array(img.getdata()).reshape(img.size[1], img.size[0], 3)
    img.show()
    return image

def GLcvion(image, LoG_sigma=1.5, threshold=0.3):
    image = image-np.min(image)

    image_log = gaussian_laplace(image, LoG_sigma)

    image_log = 1 - (image_log - np.min(image_log)) / (np.max(image_log) - np.min(image_log))

    image_bn = np.where(image_log > threshold, 1, 0)

    image_lb = label(image_bn)

    return image_lb

def GL_abs_cv(image, LoG_sigma=1.5, threshold=0.5):
    image = image - np.min(image)
    image_log = abs(gaussian_laplace(image, LoG_sigma))
    image_log = (image_log - np.min(image_log)) / (np.max(image_log) - np.min(image_log))
    image_bn = np.where(image_log > threshold, 1, 0)
    image_lb = label(image_bn)

    return image_lb

def cvion_fast_1d(image, image_lb):
    ion_num = np.max(image_lb)
    para_num = 3
    para_cv = np.zeros((ion_num, para_num))
    for lb in range(1, ion_num+1):
        count = image[image_lb==lb]
        wgt = count / np.sum(count)
        pixel= np.where(image_lb==lb)
        print(pixel[0])
        pixel0 = int(np.average(pixel[0], weights=wgt))

        maxcount = np.max(count)
        s = np.count_nonzero(image_lb == lb)

        para_cv[lb-1,:]=np.array([maxcount, pixel0, s])

    return para_cv

def get_allcount_1d(data, ion_pos, d=2, ion_no=0, mode='SUM'):    #mode——简单求和|高斯加权求和
    data = data-np.min(data)
    pixel0 = int(ion_pos[ion_no])
    if mode == 'SUM':
        count = data[:, pixel0 - d:pixel0 + d + 1]
        allcount = count.sum(axis=1)

    elif mode == 'GAUSS':
        roi = np.arange(pixel0-2*d, pixel0+2*d+1, 1)    #高斯加权平均的区域
        mask = np.exp(-(roi-pixel0)**2/2.0/d**2)
        allcount = np.dot(data[:, pixel0-2*d:pixel0+2*d+1], mask)

    return allcount

def get_state_1d(data, ion_pos, countthr=4500, d=2, ion_no=[], mode='SUM'):
    data = data.sum(axis=1)

    if len(ion_no)==1:

        allcount = get_allcount_1d(data, ion_pos, d=d, ion_no=ion_no[0], mode=mode)
        state = np.zeros((1,1))
        state[0,0] = np.sum(allcount>countthr)/len(allcount)

    elif len(ion_no)==0:
        thrrawdata = np.zeros((ion_pos.shape[0], data.shape[0]))
        state = np.zeros((ion_pos.shape[0], 1))
        for i in range(ion_pos.shape[0]):
            allcount = get_allcount_1d(data, ion_pos, d=d, ion_no=i, mode=mode)
            thrrawdata[i, :] = allcount
            state[i,0] = np.sum(allcount>countthr)/len(allcount)
    else:
        state = np.zeros((len(ion_no), 1))
        j = 0
        for i in ion_no:
            allcount = get_allcount_1d(data, ion_pos, d=d, ion_no=i, mode=mode)
            state[j, 0] = np.sum(allcount > countthr) / len(allcount)
            j+=1

    return state, thrrawdata

# def get_state_1d_postsel(data, ion_pos, countthr=4000, d=2, ion_no=[], mode='SUM'):
#     data = data.sum(axis=1)
#
#     if len(ion_no)==1:
#
#         allcount = get_allcount_1d(data, ion_pos, d=d, ion_no=ion_no[0], mode=mode)
#         state = np.zeros((1,1))
#         state[0,0] = np.sum(allcount>countthr)/len(allcount)
#
#     elif len(ion_no)==0:
#         thrrawdata = np.zeros((ion_pos.shape[0], data.shape[0]))
#         state = np.zeros((ion_pos.shape[0], 1))
#         for i in range(ion_pos.shape[0]):
#             allcount = get_allcount_1d(data, ion_pos, d=d, ion_no=i, mode=mode)
#             thrrawdata[i, :] = allcount
#             state[i,0] = np.sum(allcount>countthr)/len(allcount)
#     else:
#         state = np.zeros((len(ion_no), 1))
#         j = 0
#         for i in ion_no:
#             allcount = get_allcount_1d(data, ion_pos, d=d, ion_no=i, mode=mode)
#             state[j, 0] = np.sum(allcount > countthr) / len(allcount)
#             j+=1
#
#     return state, thrrawdata


def get_correlation(data, ion_pos, countthr=4500, d=2, ion_no=[0,1], mode='SUM', state_selected=[]):  #state_selected: the population of which you measure, format="0000"
    data = data.sum(axis=1)
    thrrawdata = np.zeros((ion_pos.shape[0], data.shape[0]))
    
    for i in range(ion_pos.shape[0]):
        allcount = get_allcount_1d(data, ion_pos, d=d, ion_no=i, mode=mode)
        thrrawdata[i, :] = allcount

    if len(ion_no) == 2:   #all states of two ion 
        state = np.zeros((4, 1))
        state[0, 0] = np.mean(((thrrawdata[ion_no[0], :]<countthr)&(thrrawdata[ion_no[1], :]<countthr)))
        state[1, 0] = np.mean(((thrrawdata[ion_no[0], :]>countthr)&(thrrawdata[ion_no[1], :]<countthr)))
        state[2, 0] = np.mean(((thrrawdata[ion_no[0], :]<countthr)&(thrrawdata[ion_no[1], :]>countthr)))
        state[3, 0] = np.mean(((thrrawdata[ion_no[0], :]>countthr)&(thrrawdata[ion_no[1], :]>countthr)))

        return state, thrrawdata
    else:   # only calculate the odd population of all selected ions 
        if len(state_selected) == 0:
            odd_pop = np.mean(np.sum(thrrawdata[ion_no, :]>countthr, axis=0)%2)

            return odd_pop, thrrawdata
        else:
            assert len(ion_no)==len(state_selected[0])
            state1_each_repeat = thrrawdata[ion_no, :] > countthr
            
            state = np.zeros((len(state_selected), 1))
            for state_index in range(len(state_selected)):
                truth_value = True
                state_str = state_selected[state_index]
                state_array = np.array([int(x) for x in state_str]).reshape(len(state_str),1)
                state[state_index, 0] = np.mean(np.prod(((1-state_array)-(-1)**state_array*state1_each_repeat), axis=0))
                # for ion_index in range(len(state_str)):
                #    truth_value = np.logical_and(truth_value, (1-int(state_str[ion_index]))-(-1)**int(state_str[ion_index])*state1_each_repeat[ion_index, :])
                   
                # state[state_index, 0] = np.mean(truth_value)
            
            return state, thrrawdata
        

        





        

    






def threshold_debug(data, ion_pos, d = 2, ion_no=[]):
    data = data.sum(axis=1)












