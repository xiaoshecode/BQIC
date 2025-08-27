import asyncio
import websockets
import json
import random
import time

START_TIME = time.perf_counter()
TOTAL_POINTS = 500
INTERVAL = 0.05        # 每条间隔 0.1 s

connected_clients = set()

async def handler(websocket):
    """一个客户端一条连接"""
    connected_clients.add(websocket)
    try:
        # 等待前端发送 "start"
        async for msg in websocket:
            if msg.strip() == "start":
                await send_2000(websocket)
                break
    finally:
        connected_clients.discard(websocket)
        await websocket.close()

async def send_2000(ws):
    """只给当前 ws 发 2000 条"""
    for idx in range(TOTAL_POINTS):
        elapsed_ms = int((time.perf_counter() - START_TIME) * 1000)
        data = {"timestamp": elapsed_ms, "value": random.randint(0, 100)}
        await ws.send(json.dumps(data))
        await asyncio.sleep(INTERVAL)
    await ws.close()     # 发完自动断开

async def main():
    async with websockets.serve(handler, "localhost", 8765):
        print("WebSocket server started at ws://localhost:8765")
        print("等待前端发送 'start' 后再推送 2000 条数据…")
        await asyncio.Future()   # 一直运行

if __name__ == "__main__":
    asyncio.run(main())