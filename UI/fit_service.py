
import asyncio, json, base64, io
import numpy as np
from aiohttp import web
from scipy.optimize import curve_fit
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import aiohttp_cors  # 新增

# ---------------- 模型 ----------------
def _rabi(x, k, a0, a1, a2, a3):
    return np.exp(-k * x) * a0 * np.sin(a1 * x + a2) + a3

def _lorentz(x, x0, w, a, b, c):
    return a * np.sinc(np.sqrt(1 + ((x - x0) / w) ** 2)) ** 2 + b

def _gaussian(x, A, mu, sigma, offset):
    return A * np.exp(-((x - mu) ** 2) / (2 * sigma ** 2)) + offset

# ---------------- 拟合包装 ----------------
def fit_rabi(x, y):
    fs = np.fft.fftfreq(len(x), x[1] - x[0])
    a1 = 2 * np.pi * abs(fs[np.argmax(np.abs(np.fft.fft(y))[1:]) + 1])
    p0 = [0.01, np.ptp(y), a1, 0, np.mean(y)]
    popt, _ = curve_fit(_rabi, x, y, p0=p0, maxfev=5000)
    pred = _rabi(x, *popt)
    r2 = 1 - np.sum((y - pred) ** 2) / np.sum((y - np.mean(y)) ** 2)
    return dict(params=popt.tolist(), r2=float(r2)), pred

def fit_lorentz(x, y):
    peak = np.argmax(y)
    p0 = [x[peak], (x[-1] - x[0]) / 4, y[peak] - y.min(), y.min(), 1.0]
    popt, _ = curve_fit(_lorentz, x, y, p0=p0, maxfev=5000)
    pred = _lorentz(x, *popt)
    r2 = 1 - np.sum((y - pred) ** 2) / np.sum((y - np.mean(y)) ** 2)
    return dict(params=popt.tolist(), r2=float(r2)), pred

def fit_gaussian(x, y, p0=None):
    if p0 is None:
        p0 = [np.ptp(y), x[np.argmax(y)], (x[-1] - x[0]) / 4, np.min(y)]
    popt, _ = curve_fit(_gaussian, x, y, p0=p0, maxfev=5000)
    pred = _gaussian(x, *popt)
    r2 = 1 - np.sum((y - pred) ** 2) / np.sum((y - np.mean(y)) ** 2)
    return dict(params=popt.tolist(), r2=float(r2)), pred

MODELS = {'rabi': fit_rabi, 'lorentz': fit_lorentz, 'gaussian': fit_gaussian}

# ---------------- 绘图 ----------------
def plot_to_base64(x, y, pred, title=""):
    fig = Figure(figsize=(6, 3), dpi=120)
    FigureCanvas(fig)
    ax = fig.add_subplot(111)
    ax.plot(x, y, 'o', label='data', markersize=3)
    ax.plot(x, pred, 'r-', label='fit')
    ax.set_title(title)
    ax.legend()
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    return "data:image/png;base64," + base64.b64encode(buf.read()).decode()

# ---------------- 路由 ----------------
routes = web.RouteTableDef()

@routes.get('/models')
async def list_models(request):
    return web.json_response(list(MODELS.keys()))

@routes.post('/fit')
async def fit_handler(request):
    body = await request.json()
    x = np.asarray(body['x'], dtype=float)
    y = np.asarray(body['y'], dtype=float)
    model = body.get('model', 'rabi')
    if model not in MODELS:
        return web.json_response({'error': 'unknown model'}, status=400)
    func = MODELS[model]
    try:
        if model == 'gaussian':
            info, pred = func(x, y, body.get('p0'))
        else:
            info, pred = func(x, y)
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)
    info['img'] = plot_to_base64(x, y, pred, model)
    return web.json_response(info)

# ---------------- 启动 ----------------
app = web.Application()
cors = aiohttp_cors.setup(app, defaults={
    "*": aiohttp_cors.ResourceOptions(
        allow_credentials=True,
        expose_headers="*",
        allow_headers="*",
    )
})
app.add_routes(routes)
for route in list(app.router.routes()):
    cors.add(route)

if __name__ == '__main__':
    web.run_app(app, host='localhost', port=8766)