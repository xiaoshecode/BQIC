import numpy as np
import scipy.optimize as optimize
from scipy.signal import find_peaks,peak_widths,peak_prominences
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.pyplot import MultipleLocator 


#from thefuzz import process, fuzz
#from Drivers.fitModels import models
#_models = models._models
class models:
    fitRes = None
import matplotlib.pyplot as plt
from typing import List, Tuple

import time
from datetime import datetime
import os



try:
    NB = get_ipython().__class__.__name__ == 'ZMQInteractiveShell'
except:
    NB = False
if NB:
    import plotly.express as px
    import plotly.graph_objects as go
else:
    import matplotlib.pyplot as plt

def _rabi(x, k, a0, a1, a2, a3):
    return np.exp(-1*k*x) * a0 * np.sin(a1 * x + a2) + a3
        
def rabi(X,Y,name_file):
    now = datetime.now()
    time_now = now.strftime("%Y-%m-%d")
    time_month = now.strftime("%Y%m")
    time_year = now.strftime("%Y")
    path_file = 'D:\\Data'+ '\\' + time_year + '\\' + time_month +'\\'+ time_now
    if not os.path.exists(path_file):
        os.makedirs(path_file)
    localtime = time.asctime( time.localtime(time.time()) )
    path_fig = path_file + '\\'+localtime[-13:-11]+'-'+localtime[-10:-8]+'-'+localtime[-7:-5]+ name_file +'.jpg'
    fs = np.fft.fftfreq(len(X), X[1]-X[0])
    Y1 = abs(np.fft.fft(Y))
    freq = abs(fs[np.argmax(Y1[1:]) + 1])
    a0 = max(Y) - min(Y)
    a1 = 2*np.pi*freq
    a2 = 0
    a3 = np.mean(Y)        
    p0 = [0, a0, a1, a2, a3]
    para, _ = optimize.curve_fit(_rabi,X,Y,p0=p0)
    y_fit = [_rabi(a, *para) for a in X]
    if NB:
        fig = px.line(x=X,y=y_fit)
        fig.add_trace(go.Scatter(x=X,y=Y,mode='markers',name='',showlegend=False))
        fig.show()
        fig.write_image(path_fig)
    else:
        plt.plot(X,Y,'b--')
        plt.plot(X, y_fit, 'g')
        plt.savefig(path_fig,dpi=300)
        plt.show()
    delay = [(np.ceil(para[3]*2/np.pi)*np.pi/2-para[3])/para[2], (np.floor(para[3]*2/np.pi)*np.pi/2-para[3])/para[2]]
    if delay[0] > -delay[1]:
        delay = delay[1]
    else:
        delay = delay[0]
    return [[2*np.pi/para[2], delay], para]

def _multi_gaussian_with_offset(x, *params):
    """
    带垂直偏移的多个高斯函数叠加
    参数顺序：A1, mu1, sigma1, A2, mu2, sigma2, ..., offset
    """
    n_peaks = (len(params)-1) // 3  # 计算高斯峰数量
    offset = params[-1]  # 最后一个参数是偏移量
    y = np.zeros_like(x) + offset
    
    for i in range(n_peaks):
        A = params[3*i]
        mu = params[3*i+1]
        sigma = params[3*i+2]
        y += A * np.exp(-(x - mu)**2 / (2 * sigma**2))
    return y

def multi_gaussian_with_offset(data,p0=[]):
    x=data[0]
    y=data[1][:,0]
    n_peaks = (len(p0)-1) // 3

    lower = [0, -np.inf, 0]*n_peaks + [-np.inf]  # offset下界
    upper = [np.inf]*3*n_peaks + [np.inf]        # offset上界
    bounds = (lower, upper)

    # 执行拟合
    popt, pcov = optimize.curve_fit(_multi_gaussian_with_offset, x, y, p0=p0)

    # 解析拟合结果
    n_peaks_fit = (len(popt)-1) // 3
    params_fit = popt[:-1]
    offset_fit = popt[-1]
    perr = np.sqrt(np.diag(pcov))  # 参数误差

    # 打印结果
    print("拟合参数 ± 标准误差:")
    for i in range(n_peaks_fit):
        print(f"峰 {i+1}:")
        print(f"  振幅 = {popt[3*i]:.2f} ± {perr[3*i]:.2f}")
        print(f"  中心 = {popt[3*i+1]:.2f} ± {perr[3*i+1]:.2f}")
        print(f"  半高宽 = {2.355*popt[3*i+2]:.2f} ± {2.355*perr[3*i+2]:.2f}\n")  # FWHM=2.355σ
    print(f"基线偏移 = {offset_fit:.2f} ± {perr[-1]:.2f}")

    # 可视化
    plt.figure(figsize=(12, 6))

    # 绘制原始数据
    plt.scatter(x, y, s=2, color='grey', alpha=0.6, label='带噪声数据')

    # 总拟合曲线
    total_fit = _multi_gaussian_with_offset(x, *popt)
    plt.plot(x, total_fit, 'r-', lw=2, label='总拟合')
    plt.show()
    return popt

def _lorentz(x,x0,w,a,b,c):
    return a*np.sin(c*np.sqrt(1+((x-x0)/w)**2))/np.sqrt(1+((x-x0)/w)**2)**2+b
    
def drive(X,Y,name_file):
    now = datetime.now()
    time_now = now.strftime("%Y-%m-%d")
    time_month = now.strftime("%Y%m")
    time_year = now.strftime("%Y")
    path_file = 'D:\\Data'+ '\\' + time_year + '\\' + time_month +'\\'+ time_now
    if not os.path.exists(path_file):
        os.makedirs(path_file)
    localtime = time.asctime( time.localtime(time.time()) )
    path_fig = path_file + '\\'+localtime[-13:-11]+'-'+localtime[-10:-8]+'-'+localtime[-7:-5]+ name_file +'.jpg'
    peak = Y.argmax()
    base = Y.min()
    height = Y[peak]-base
    width = X[np.abs(Y[peak:]-height/2-base).argmin()+peak] - X[np.abs(Y[:peak]-height/2-base).argmin()]
    p0=[X[peak],width/2,height,base,np.arcsin(np.sqrt(Y[peak]/100))]
    para,_=optimize.curve_fit(_lorentz,X,Y,p0=p0,maxfev=10000)
    y_fit=np.array([_lorentz(x,*para) for x in X])
    if NB:
        fig = px.line(x=X,y=y_fit)
        fig.add_trace(go.Scatter(x=X,y=Y,mode='markers',name='',showlegend=False))
        fig.show()
        fig.write_image(path_fig)
    else:
        plt.plot(X, Y, 'b--')
        plt.plot(X, y_fit, 'g')
        plt.savefig(path_fig,dpi=300)
        plt.show()
    return para

def peaks(X,Y,name_file,n=None,height=None,threshold=None,distance=None,prominence=None,width=None,sort=None):
    now = datetime.now()
    time_now = now.strftime("%Y-%m-%d")
    time_month = now.strftime("%Y%m")
    time_year = now.strftime("%Y")
    path_file = 'D:\\Data'+ '\\' + time_year + '\\' + time_month +'\\'+ time_now
    if not os.path.exists(path_file):
        os.makedirs(path_file)
    localtime = time.asctime( time.localtime(time.time()) )
    path_fig = path_file + '\\'+localtime[-13:-11]+'-'+localtime[-10:-8]+'-'+localtime[-7:-5]+ name_file +'.jpg'
    if height == None:
        height = Y.min()
    ind,props=find_peaks(Y,height=height,threshold=threshold,distance=distance,prominence=prominence,width=width,rel_height=0.5)
    if sort == None:
        if prominence == None and width == None:
            sort = 'peak_heights'
        elif width == None:
            sort = 'prominences'
        else:
            sort = 'widths'
    heights=props[sort]
    
    if X is None:
        X = np.arange(len(Y))
    if n == None or n > len(ind):
        n = len(ind)
    ind=ind[np.argsort(heights)[::-1][:n]]
    widths=peak_widths(Y,ind,rel_height=0.5)
    prominences=peak_prominences(Y,ind)[0]
    if NB:
        fig = px.line(x=X,y=Y)
        fig.add_trace(go.Scatter(x=X[ind],y=Y[ind],mode='markers',name='',showlegend=False))
        for i in range(len(ind)):
            fig.add_shape(type='line',x0=X[round(widths[2][i])],y0=widths[1][i],x1=X[round(widths[3][i])],y1=widths[1][i])
            fig.add_shape(type='line',x0=X[ind[i]],y0=Y[ind[i]]-prominences[i],x1=X[ind[i]],y1=Y[ind[i]],line={'dash':'dot'})
        fig.show()
        fig.write_image(path_fig)
    else:
        plt.plot(X,Y)
        plt.plot(X[ind],Y[ind],'x')
        plt.hlines(widths[1],X[widths[2].round().astype(int)],X[widths[3].round().astype(int)],color='C1')
        plt.vlines(x=X[ind],ymin=Y[ind]-prominences,ymax=Y[ind],color='C1',linestyles='dashed')
        plt.savefig(path_fig,dpi=300)
        plt.show()
    return ind.astype(int),widths[0].round().astype(int),prominences


def ion_photn_fitted(data,scale):
    now = datetime.now()
    time_now = now.strftime("%Y-%m-%d")
    time_month = now.strftime("%Y%m")
    time_year = now.strftime("%Y")
    path_file = 'D:\\Data'+ '\\' + time_year + '\\' + time_month +'\\'+ time_now
    if not os.path.exists(path_file):
        os.makedirs(path_file)
    N = len(data)
    pmt_number = np.zeros(N)
    photon_time = np.zeros(N)
    ion_count = np.zeros(N)
    count1b = 0       
    count1d = 0       
    totalcount1 = 0   
    count2b = 0       
    count2d = 0
    totalcount2 = 0
    for i in range(len(data)):
        pmt_number[i] = data[i][0]
        photon_time[i] = data[i][1]
        ion_count[i] = data[i][2]
    for i in range(len(data)):
        if(photon_time[i] in scale):
            if(pmt_number[i] == 0):            
                totalcount1 = totalcount1 + 1
                if(ion_count[i] >= 2):
                    count1b = count1b + 1
                if(ion_count[i] < 2):
                    count1d = count1d + 1
            if(pmt_number[i] == 1):
                totalcount2 = totalcount2 + 1
                if(ion_count[i] >= 2):
                    count2b = count2b + 1
                if(ion_count[i] < 2):
                    count2d = count2d + 1
    P1b = count1b/totalcount1
    P1d = count1d/totalcount1
    P2b = count2b/totalcount2
    P2d = count2d/totalcount2
    print("in pmt 1, the number of the bright state is %s"%count1b)
    print("in pmt 1, the number of the dark state is %s"%count1d)
    print("in pmt 2, the number of the bright state is %s"%count2b)
    print("in pmt 2, the number of the dark state is %s"%count2d)
    print("in pmt 1, the probability of the bright state is %f" %P1b)
    print("in pmt 1, the probability of the dark state is %f" %P1d)
    print("in pmt 2, the probability of the bright state is %f" %P2b)
    print("in pmt 2, the probability of the dark state is %f" %P2d) 
    fig = plt.figure(dpi=100)
    ax = fig.add_axes(Axes3D(fig))
    X = [1,2]
    Y = [0,1]  
    Z = [P1d,P2d,P1b,P2b]
    xx,yy = np.meshgrid(X,Y)
    X,Y = xx.ravel(),yy.ravel()
    height = np.zeros_like(Z)
    width = depth = 0.25
    c = ['dodgerblue']*len(Z) 
    x_major_locator = MultipleLocator(1)   
    y_major_locator = MultipleLocator(1)
    z_major_locator = MultipleLocator(0.2)
    ax.xaxis.set_major_locator(x_major_locator)
    ax.yaxis.set_major_locator(y_major_locator)
    ax.zaxis.set_major_locator(z_major_locator)
    ax.set_zlim(0,1.01)
    ax.bar3d(X,Y,height,width,depth,Z,color=c,shade=True)   
    ax.set_ylabel('S')
    ax.set_xlabel(r'$\Pi$')
    ax.set_zlabel(r'$Conditional\ probability\ P(S|\Pi)$')
    scale_ls = range(2)
    scale_ls_x = [1,2]
    index_ls = [r'$|\downarrow\rightangle$',r'$|\uparrow\rightangle$']
    index_ls_x = [r'$|H\rightangle$',r'$|V\rightangle$']
    plt.yticks(scale_ls,index_ls)  
    plt.xticks(scale_ls_x,index_ls_x) 

    XX = [1,2,1,2]
    YY = [1,1,2,2]
    for x,y,z in zip(XX,YY,Z):
        ax.text(x-0.37,y,z-0.3,'%.3f' %z,ha='center',va='bottom')
    localtime = time.asctime( time.localtime(time.time()) )
    path_fig = 'D:\\Data'+ '\\' + time_year + '\\' + time_month +'\\'+ time_now +'\\'+localtime[-13:-11]+'-'+localtime[-10:-8]+'-'+localtime[-7:-5]+'ion-photon.jpg'
    plt.savefig(path_fig,dpi=300)
    plt.show()


def ion_photnccd_fitted(data,scale,x,threshold):
    x = int(x)
    now = datetime.now()
    time_now = now.strftime("%Y-%m-%d")
    time_month = now.strftime("%Y%m")
    time_year = now.strftime("%Y")
    path_file = 'D:\\Data'+ '\\' + time_year + '\\' + time_month +'\\'+ time_now
    if not os.path.exists(path_file):
        os.makedirs(path_file)
    N = len(data)
    pmt_number = np.zeros(N)
    photon_time = np.zeros(N)
    ion_count = np.zeros(N)
    count1b = 0       
    count1d = 0       
    totalcount1 = 0   
    count2b = 0       
    count2d = 0
    totalcount2 = 0
    for i in range(len(data)):
        pmt_number[i] = data[i][1][0]
        photon_time[i] = data[i][1][1]
        ion_count[i] = data[i][2][0][x]
    for i in range(len(data)):
        if(photon_time[i] in scale):
            if(pmt_number[i] == 0):            
                totalcount1 = totalcount1 + 1
                if(ion_count[i] >= threshold):
                    count1b = count1b + 1
                if(ion_count[i] < threshold):
                    count1d = count1d + 1
            if(pmt_number[i] == 1):
                totalcount2 = totalcount2 + 1
                if(ion_count[i] >= threshold):
                    count2b = count2b + 1
                if(ion_count[i] < threshold):
                    count2d = count2d + 1
    P1b = count1b/totalcount1
    P1d = count1d/totalcount1
    P2b = count2b/totalcount2
    P2d = count2d/totalcount2
    print("in pmt 1, the number of the bright state is %s"%count1b)
    print("in pmt 1, the number of the dark state is %s"%count1d)
    print("in pmt 2, the number of the bright state is %s"%count2b)
    print("in pmt 2, the number of the dark state is %s"%count2d)
    print("in pmt 1, the probability of the bright state is %f" %P1b)
    print("in pmt 1, the probability of the dark state is %f" %P1d)
    print("in pmt 2, the probability of the bright state is %f" %P2b)
    print("in pmt 2, the probability of the dark state is %f" %P2d) 
    fig = plt.figure(dpi=100)
    ax = fig.add_axes(Axes3D(fig))
    X = [1,2]
    Y = [0,1]  
    Z = [P1d,P2d,P1b,P2b]
    xx,yy = np.meshgrid(X,Y)
    X,Y = xx.ravel(),yy.ravel()
    height = np.zeros_like(Z)
    width = depth = 0.25
    c = ['dodgerblue']*len(Z) 
    x_major_locator = MultipleLocator(1)   
    y_major_locator = MultipleLocator(1)
    z_major_locator = MultipleLocator(0.2)
    ax.xaxis.set_major_locator(x_major_locator)
    ax.yaxis.set_major_locator(y_major_locator)
    ax.zaxis.set_major_locator(z_major_locator)
    ax.set_zlim(0,1.01)
    ax.bar3d(X,Y,height,width,depth,Z,color=c,shade=True)   
    ax.set_ylabel('S')
    ax.set_xlabel(r'$\Pi$')
    ax.set_zlabel(r'$Conditional\ probability\ P(S|\Pi)$')
    scale_ls = range(2)
    scale_ls_x = [1,2]
    index_ls = [r'$|\downarrow\rightangle$',r'$|\uparrow\rightangle$']
    index_ls_x = [r'$|H\rightangle$',r'$|V\rightangle$']
    plt.yticks(scale_ls,index_ls)  
    plt.xticks(scale_ls_x,index_ls_x) 

    XX = [1,2,1,2]
    YY = [1,1,2,2]
    for x,y,z in zip(XX,YY,Z):
        ax.text(x-0.37,y,z-0.3,'%.3f' %z,ha='center',va='bottom')
    localtime = time.asctime( time.localtime(time.time()) )
    path_fig = 'D:\\Data'+ '\\' + time_year + '\\' + time_month +'\\'+ time_now +'\\'+localtime[-13:-11]+'-'+localtime[-10:-8]+'-'+localtime[-7:-5]+'ion-photon.jpg'
    plt.savefig(path_fig,dpi=300)
    plt.show()


def ion_photnfinal_fitted(data,scale,threshold1,threshold2):
    results = {'00':[0,0,0],'01':[0,0,0],'10':[0,0,0],'11':[0,0,0]} 
    now = datetime.now()
    time_now = now.strftime("%Y-%m-%d")
    time_month = now.strftime("%Y%m")
    time_year = now.strftime("%Y")
    path_file = 'D:\\Data'+ '\\' + time_year + '\\' + time_month +'\\'+ time_now
    if not os.path.exists(path_file):
        os.makedirs(path_file)
    N = len(data)
    pmt_number = np.zeros(N)
    photon_time = np.zeros(N)
    ion_count1 = np.zeros(N)     
    ion_count2 = np.zeros(N) 
    parity = 0
    total_count = 0
    for i in range(len(data)):
        pmt_number[i] = data[i][1][0]
        photon_time[i] = data[i][1][1]
        ion_count1[i] = data[i][2][0][0]
        ion_count2[i] = data[i][2][0][1]
    for i in range(len(data)):
        if(photon_time[i] in scale):
            if(ion_count1[i]<=threshold1 and ion_count2[i]<=threshold2):
                results['00'][0] = results['00'][0] + 1
                if(pmt_number[i] == 0):
                    results['00'][1] = results['00'][1] + 1
                if(pmt_number[i] == 1):
                    results['00'][2] = results['00'][2] + 1
            if(ion_count1[i]<=threshold1 and ion_count2[i]>threshold2):
                results['01'][0] = results['01'][0] + 1
                if(pmt_number[i] == 0):
                    results['01'][1] = results['01'][1] + 1
                if(pmt_number[i] == 1):
                    results['01'][2] = results['01'][2] + 1
            if(ion_count1[i]>threshold1 and ion_count2[i]<=threshold2):
                results['10'][0] = results['10'][0] + 1
                if(pmt_number[i] == 0):
                    results['10'][1] = results['10'][1] + 1
                if(pmt_number[i] == 1):
                    results['10'][2] = results['10'][2] + 1
            if(ion_count1[i]>threshold1 and ion_count2[i]>threshold2):
                results['11'][0] = results['11'][0] + 1
                if(pmt_number[i] == 0):
                    results['11'][1] = results['11'][1] + 1
                if(pmt_number[i] == 1):
                    results['11'][2] = results['11'][2] + 1
    keys = [key for key in results]
    localtime = time.asctime( time.localtime(time.time()) )
    lsc = len(scale)-1
    total_count = results['00'][0]+results['01'][0]+results['10'][0]+results['11'][0]
    parity = (-results['00'][1]+results['00'][2]+results['01'][1]-results['01'][2]+results['10'][1]-results['10'][2]-results['11'][1]+results['11'][2])/total_count
    with open(path_file+'\\'+localtime[-13:-11]+'-'+localtime[-10:-8]+'-'+localtime[-7:-5]+'finalexp'+'.txt', 'w') as f:
        for i in range(3):
            f.write(str(keys[i]))
            f.write('\t')
            f.write(str(results[keys[i]][0]))
            f.write('\t')
            f.write(str(results[keys[i]][1]))
            f.write('\t')
            f.write(str(results[keys[i]][2]))
            f.write('\n') 
        f.write(str(keys[3]))
        f.write('\t')
        f.write(str(results[keys[3]][0]))
        f.write('\t')
        f.write(str(results[keys[3]][1]))
        f.write('\t')
        f.write(str(results[keys[3]][2]))
        f.write('\t')
        f.write(str(parity))
        f.write('\n') 
        f.write('scale:'+str(scale[0])+'-'+str(scale[lsc]))
        f.write('\n')
        f.write('threshold1:'+str(threshold1))
        f.write('\n')
        f.write('threshold2:'+str(threshold2))
        f.write('\n')
    return results, parity





def fit(x = None, y = None, model:str = None, **kwargs):

    # check values
    if model is None:
        raise ValueError('model is not specified')
    
    if x is None or y is None:
        raise ValueError('x or y is not specified')
    
    x = np.asarray(x)
    y = np.asarray(y)
    if len(x) != len(y):
        raise ValueError('x and y must have the same length')
    
    # fuzzy search to match model
    if any(item in model for item in '+-*/' ) and 'x' in model:
        model =  models.expressionModel(model)
    else:
        res, ratio = process.extractOne(model, _models, scorer = fuzz.QRatio)
        if ratio < 70:
            print(f'Can not find mode {model}, do you mean {res} ?\nAvailiable models are {_models}')
            return
        
        model = eval(f"models.{res}Model()")

    # fit and return
    return model.Fit(x, y, **kwargs)
  
def medianFilter(data, window_size = 4):
    """
    Applies a median filter to 1-D data.
    data: 1-D numpy array of data.
    window_size: size of the median filter window.
    """
    padded_data = np.pad(data, window_size // 2, mode='reflect')
    filtered_data = np.empty_like(data)
    for i in range(len(data)):
        filtered_data[i] = np.median(padded_data[i:i+window_size])
    return filtered_data

def aodScanFit(x, y, data_window = 30, debug = False, **kwargs):
    """
    the sharp of input y is in the peak format
    """
    model = models.expressionModel('amp*(cos(theta*exp(-2*(x - cen)**2/sigma**2) + offset) + 1)')
    pad_size = kwargs.get('pad_size', 2)
    height = kwargs.get('height', 0.2)
    distance = kwargs.get('distance', len(x)*2//3)
    
    # find the mean peak location
    y_all = np.pad(medianFilter(y), pad_size, mode = 'constant', constant_values = 0)
    peak_all, h_all = find_peaks(y_all, height = height, distance = distance)
    peak_x = peak_all - pad_size

    peakNum = len(peak_all)
    dataNum = len(x)
    
    # find the fine peak and choose data
    dx = x[1] - x[0]
    extend_x = np.hstack((x, x + x[-1] -x[0] + dx))
    extend_y = np.hstack((y, y))

    if peakNum > 0:
        loc = peak_x[-1]
        choice = np.arange(max(loc - data_window, 0), min(loc + data_window +1, peakNum*dataNum-1))
        y_cropped = extend_y[choice]
        y_cropped = np.pad(medianFilter(y_cropped, 3), pad_size, mode = 'constant', constant_values = 0)
         
        # find local peak and update choice
        local_peak_num = 0
        height = 1.5*height
        while local_peak_num == 0:
            height *= 0.9
            local_peak_loc, local_peak_h = find_peaks(y_cropped, height = height, distance = 5)
            local_peak_num = len(local_peak_loc)
            
            # check if the peak is valid
            for i in range(local_peak_num - 1):
                idx1, idx2 = local_peak_loc[i:i+2]
                loc = round((idx1 + idx2)/2)
                if y_cropped[loc] > (y_cropped[idx1] + y_cropped[idx2])/4:
                    local_peak_num -= 1		

        peak_x = local_peak_loc - pad_size + choice[0]
        loc = round(np.mean(peak_x))
        choice = np.arange(max(loc - data_window, 0), min(loc + data_window +1, peakNum*dataNum-1))
        xdata = extend_x[choice]
        ydata = extend_y[choice]

        cen_x = np.mean(extend_x[peak_x])
        cen_y = extend_y[loc]

    else:
        xdata = x
        ydata = y
        cen_x = np.mean(x)
        cen_y = y.max()
        peak_all = np.array([len(x)//2])
        local_peak_num = 1

    cen = (cen_x, xdata.min(), xdata.max())
    theta0 = np.arccos(1-2*cen_y)
    theta = np.array([theta0, 0, 1.5*np.pi]) + np.pi*(local_peak_num -1)
    # theta = theta0
    # theta = tuple(theta.tolist())

    ret = [False, False]
    ydata = 1 - ydata
    try:
        res =  model.Fit(xdata, ydata, cen = cen, sigma=(0.45, 0.3, 0.7), offset=(0, -0.1, 0.1), amp=[0.5, 0, 0.55], theta=theta.tolist())
        ret = [res, peak_all]
    except Exception as e:
        print('fit failed', e)
    
    # the information used for debug
    if debug:
        fig, ax = plt.subplots(2, 2, figsize = (12, 8))
        fig.set_tight_layout(True)
        ax = ax.flatten()

        ax[0].plot(x, y)
        ax[1].plot(xdata, ydata)
        ax[1].plot(xdata, res.best_fit)

        # peak choice
        if len(peak_all) > 0:
            ax[2].plot(y_all)
            ax[2].plot(peak_all, h_all['peak_heights'], 'x')

            ax[3].plot(y_cropped)
            ax[3].plot(local_peak_loc, local_peak_h['peak_heights'], 'x')
        titles = ['all','cropped', 'all peak', 'cropped peak']
        for i in range(len(ax)):
            ax[i].set_title(titles[i])
        
        try:
            get_ipython()
        except:
            fig.show()
        # fig.savefig(f"{time.strftime('%y%m%d')}_debug_{rnk}.pdf")
    return ret

def aodScanSort(res, num, span, isDesc = None, rg=0.5):
    """
    Sort the data by the peak position.
    """
    span = span/num
    diff = np.diff(res)
    isDesc = diff[diff > 0].size < diff.size/2 if isDesc is None else isDesc

    for i in range(diff.size):
        while (res[i + (not isDesc)] - res[i + isDesc]) <= rg:
            res[i+1] += span*(1 - 2*isDesc)

        # if isDesc:
        # 	while res[i] - res[i+1] <= rg:
        # 		res[i+1] -= span
        # else:
        # 	while res[i+1]- res[i] <= rg:
        # 		res[i+1] += span
    return res
    

    # return res2

def aodScanFits(xdata, ydata, num = 20, span = 44, shift = 0, isDesc = None, rg = 0.5, **kwargs):
    """
    Fit and Sort the data by the peak position.
    xdata: the scaned data, 1-d array
    ydata: data of ion m*n where n is the number of ions
    num: number of sbg splits
    span: the total scan span
    shift: the shift of the final result
    isDesc: the direction of result
    rg: the min diff of neighbor fit result
    """
    ionNum = ydata.shape[1]
    res = np.nan*np.zeros(ionNum)
    faults = []
    norm = np.any(ydata>1)
    for i in range(ionNum):
        amp = 1
        # if norm:
        # 	amp = np.max(ydata[:,i])
        fitRes, pks = aodScanFit(xdata, ydata[:, i]/amp, **kwargs)
        if fitRes:
            res[i] = fitRes.params['cen'].value
            if fitRes.rsquared < 0.8 or len(pks) > 1:
                faults.append([i, res[i], fitRes])
    res2 = aodScanSort(res, num, span, isDesc, rg) + shift

    # plot the final result
    if NB:
        fig = go.Figure(data = go.Scatter(x = np.arange(ionNum), y = res2))
        fig.update_layout(title = 'Scan result', xaxis_title = 'Ion index', yaxis_title = 'Frequency')
        if len(faults):
            picked = [item[0] for item in faults]
            line = go.Scatter(x = picked, y = res2[picked], mode = 'markers', marker = dict(color = 'red'), name = 'uncertain')
            fig.add_trace(line)
        fig.show()
    return res2, faults, res

def carrier(x, y, **kwargs)-> Tuple[float, models.fitRes]:
    """
    Possible kwargs: amp, cen, omega, k, c

    The intial/restriction of the fitting params,
    when assigned in list format, the first one is the initial value, the second one is the lower bound, the third one is the upper bound
    ----
    amp: float or [float, float, float], amplitude
    cen: float or [float, float, float], center
    omega: float or [float, float, float], rabi omega
    k: float or [float, float, float], eta
    c: float or [float, float, float], consnat
    """

    expr = "amp*sin(k*sqrt(omega**2 + (x-cen)**2))**2*omega**2/(omega**2 + (x-cen)**2) + c"
    model = models.expressionModel(expr)

    # guess the intial value
    x, y = np.array(x).flatten(), np.array(y).flatten()
    res =  peaks(x, y, height = y.max()/2,n=1)

    cen = x[res[0]].mean()
    width = np.diff(x).mean()*res[1][0]
    amp = res[2].mean()
    k = np.pi/2/(0.7*width)

    cen = kwargs.get('cen', (cen, cen - width, cen + width))
    amp = kwargs.get('amp', (amp, y.mean(), 1.5*y.max()))
    omega = kwargs.get('omgea', (width*0.7, 0.3*width, 1.5*width))
    c = kwargs.get('c', (y.min(), 0, y.max()))
    k = kwargs.get('k', (k, 0,  np.inf))

    # fit the result
    res = model.Fit(x, y, amp = amp, cen = cen, k = k, omega = omega, c = c)
    return res.values['cen'], res


def mode(x, y, **kwargs)-> Tuple[List[float], models.fitRes]:
    """
    Possible kwargs
    ---
    height: float, the min height used when find peaks

    distance: float, the min distance used when find peaks

    num: the number of peaks to find, if not assigned, it will be set according to the number of peaks found

    Returns:
    ----
    cen: the fitted center
    res: the fitting result
    """
    
    def expr(i):
        return f"amp_{i}*sin(k_{i}*sqrt(omega_{i}**2 + (x-cen_{i})**2))**2*omega_{i}**2/(omega_{i}**2 + (x-cen_{i})**2)"

    height = kwargs.get('height', 30)
    distance = kwargs.get('distance', 5)

    x, y = np.array(x).flatten(), np.array(y).flatten()
    num = kwargs.get('num', None)
    res = peaks(x, y, n=num, height = height, distance = distance)
    

    model = "+".join([expr(i) for i in range(num)]) + " + c"
    model = models.expressionModel(model)

    rank = np.argsort(res[0])
    cens = x[res[0][rank]]
    width =res[1][rank]
    widths = width*np.diff(x).mean() 
    heights = res[2][rank]

    # gen the initial params and fit the model
    params = {"c": 0}
    for i in range(num):
        params[f"amp_{i}"] =  (heights[i], heights[i]-10, heights[i] + 10)
        params[f"cen_{i}"] =  (cens[i], cens[i] - widths[i], cens[i] + widths[i])
        params[f"omega_{i}"] =  (widths[i]*0.7, 0.3*widths[i], 1.5*widths[i])
        params[f"k_{i}"] = (np.pi/2/(0.7*widths[i]), 0, np.inf)

    # crop the data to shorten the fitting time
    start, stop = max(res[0].min() - 3*width[0], 0) , min(res[0].max() + 3*width[-1], len(x))
    res = model.Fit(x[start: stop], y[start: stop], **params)
    return [res.values[f"cen_{i}"] for i in range(num)], res


if __name__ == '__main__':
    import Data
    # rabi(*Data.avg('Time[805]-20230323190119.json'))
    # rabi(*Data.avg('Time[5]-20230323195241.json'))
    # X,Y = Data.avg('DDS[AOM1, 1]-20230323191050.json')
    # drive(X,1-Y)
    xdata = np.load("./AODScanX.npy")
    ydata = np.load("./AODScanY.npy")
    res = aodScanFits(xdata, ydata, 5, 25)

    fig, ax = plt.subplots()
    ax.plot(res[0], marker = 'o')
    plt.show()
    MODELS = {
    'rabi':   rabi,
    'drive':  drive,
    'multi_gaussian': multi_gaussian_with_offset,
    'carrier': carrier,
    'peaks':   peaks,
}