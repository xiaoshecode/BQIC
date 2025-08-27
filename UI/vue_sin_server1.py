import asyncio, websockets, json, math, time, socket

HOST = "0.0.0.0"
PORT = 8765
INTERVAL = 0.1          # 0.1 s 一个点

config = {"freq": 1.0, "amp": 50.0}
start_t = time.perf_counter()

def now():
    return time.perf_counter() - start_t

def generate(t):
    w = 2 * math.pi * config["freq"]
    return config["amp"] * math.sin(w * t)

async def handler(ws):               # ← 只有这一个参数
    sock = ws.transport.get_extra_info("socket")
    if sock:
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    async def sender():
        while True:
            y = generate(now())
            await ws.send(json.dumps({"t": round(now(), 3), "v": round(y, 2)}))
            await asyncio.sleep(INTERVAL)

    async def receiver():
        async for msg in ws:
            try:
                config.update(json.loads(msg))
            except Exception as e:
                print("Bad config:", e)

    await asyncio.gather(receiver(), sender())

async def main():
    async with websockets.serve(handler, HOST, PORT):
        print(f"Sine server ready ws://{HOST}:{PORT}")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())