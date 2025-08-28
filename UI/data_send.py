import socket, json, time, random
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
while True:
    data = [random.randint(0, 100) for _ in range(20)]  # 任意长度
    sock.sendto(json.dumps(data).encode(), ('127.0.0.1', 9999))
    time.sleep(0.1)