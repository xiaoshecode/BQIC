import json

def load_json(file):
    with open(file) as f:
        return json.load(f)

filename = "riscv_config.json"
data = load_json(filename)

print(data)