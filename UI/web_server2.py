import asyncio, json, websockets, socket, threading

UDP_PORT = 9999
WS_PORT  = 8765
latest_avg = 0          # 只存平均值

# ---------- UDP ----------
def udp_listener():
    global latest_avg
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('127.0.0.1', UDP_PORT))
    while True:
        data, _ = sock.recvfrom(4096)
        try:
            arr = json.loads(data.decode())
            latest_avg = sum(arr) / len(arr)   # 计算平均
        except Exception:
            pass

# ---------- WebSocket ----------
async def handler(websocket):
    while True:
        await websocket.send(json.dumps({"value": latest_avg}))
        await asyncio.sleep(0.1)

async def main():
    threading.Thread(target=udp_listener, daemon=True).start()
    async with websockets.serve(handler, "localhost", WS_PORT):
        print("UDP: 9999   WS: 8765")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())