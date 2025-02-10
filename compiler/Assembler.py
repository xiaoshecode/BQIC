import utils4assemble as utils4assemble


def riscv_assemble_insts(insts, riscv_config_path):
    riscv_config = utils4assemble.riscv_load_config(riscv_config_path)
    parts = insts.split()
    inst = parts[0]
    r_type = ["add", "sub", "sll", "slt", "sltu", "xor", "srl", "sra", "or", "and"]
    if inst in r_type:
        machine_code = utils4assemble.riscv_assemble_rtype(
            riscv_config, inst, parts[1], parts[2], parts[3]
        )
    elif inst in ["lw"]:
        rd = parts[1]
        offset, rs1 = parts[2].split("(")
        rs1 = rs1.strip(")")
        machine_code = utils4assemble.risv_assemble_itype(
            riscv_config, inst, rd, rs1, offset
        )
    elif inst in ["addi", "slti", "sltiu", "xori", "ori", "andi"]:
        rd = parts[1]
        rs1 = parts[2]
        imm = parts[3]
        machine_code = utils4assemble.risv_assemble_itype(
            riscv_config, inst, rd, rs1, imm
        )
    elif inst in ["slli", "srli", "srai"]:
        rd = parts[1]
        rs1 = parts[2]
        imm = parts[3]
        machine_code = utils4assemble.risv_assemble_itype(
            riscv_config, inst, rd, rs1, imm
        )
    elif inst in ["sw"]:
        rs2 = parts[1]
        offset, rs1 = parts[2].split("(")
        rs1 = rs1.strip(")")
        machine_code = utils4assemble.riscv_assemble_stype(
            riscv_config, inst, rs1, rs2, offset
        )
    elif inst in ["beq", "bne", "blt", "bge", "bltu", "bgeu"]:
        rs1 = parts[1]
        rs2 = parts[2]
        imm = parts[3]
        machine_code = utils4assemble.riscv_assemble_btype(
            riscv_config, inst, rs1, rs2, imm
        )
    elif inst in ["lui"]:
        rd = parts[1]
        imm = parts[2]
        machine_code = utils4assemble.riscv_assemble_lui(riscv_config, inst, rd, imm)
    elif inst in ["auipc"]:
        rd = parts[1]
        imm = parts[2]
        machine_code = utils4assemble.riscv_assemble_auipc(riscv_config, inst, rd, imm)
    elif inst in ["jal"]:
        rd = parts[1]
        imm = parts[2]
        machine_code = utils4assemble.riscv_assemble_jal(riscv_config, inst, rd, imm)
    elif inst in ["jalr"]:
        rd = parts[1]
        rs1 = parts[2]
        imm = parts[3]
        machine_code = utils4assemble.riscv_assemble_jalr(
            riscv_config, inst, rd, rs1, imm
        )
    elif inst in ["lujr"]:
        rd = parts[1]
        rs1 = parts[2]
        machine_code = utils4assemble.riscv_assemble_lujr(riscv_config, inst, rd, rs1)
    elif inst in ["luw"]:
        rd = parts[1]
        urs = parts[2]
        machine_code = utils4assemble.riscv_assemble_luw(riscv_config, inst, rd, urs)
    elif inst in ["setur"]:
        urd = parts[1]
        rs1 = parts[2]
        imm = parts[3]
        machine_code = utils4assemble.riscv_assemble_setur(
            riscv_config, inst, urd, rs1, imm
        )
    elif inst in ["setui"]:
        urd = parts[1]
        imm = parts[2]
        machine_code = utils4assemble.assemble_setui(riscv_config, inst, urd, imm)
    else:
        raise ValueError("Invalid instruction: {}".format(inst))
    mechine_code_hex = utils4assemble.bin2hex(machine_code)
    return mechine_code_hex

def read_assembly_file(filename):
    # 读取汇编指令文件
    with open(filename, "r") as f:
        instructions = f.readlines()
    return [inst.strip() for inst in instructions if inst.strip() != ""]


def write_machinecode(filename, machine_codes):
    # 将机器码字符串写入文件
    with open(filename, "w") as f:
        i = 0
        for code in machine_codes:
            if i % 4 == 3:
                f.write(code + "\n")
            else:
                f.write(code)
            i += 1
        f.write("ffffffff\n")
        for i in range(0, 15):
            if i % 4 == 3:
                f.write("00000000\n")
            else:
                f.write("00000000")
        f.write("ffffffff\n")


def write_machinecode2hex(filename, machine_codes):
    # 将机器码字符串转换为字节,然后写入文件
    with open(filename, "wb") as f:
        for code in machine_codes:
            f.write(bytes.fromhex(code))


def generate_assemble(input_filename, output_filename, output_hex_filename, riscv_config_path):
    instructions = read_assembly_file(input_filename)
    machine_codes = [riscv_assemble_insts(inst, riscv_config_path) for inst in instructions]
    write_machinecode(output_filename, machine_codes)
    write_machinecode2hex(output_hex_filename, machine_codes)
    print("Assembly code assembled successfully!")

# testbench
if __name__ == "__main__":
    # Example usage
    instructions = [
        "add x1 x2 x3",
        "sub x4 x5 x6",
        "lw x7 0(x8)",
        "sw x9 4(x10)",
        "beq x11 x12 -16",
        "slli x11 x12 3",
        "lui x2 786432",
        "jal x0 20",
        "auipc x1 20",
        "lujr x1 x2",
        "luw x1 z1",
        "setur y1 x1 20",
        "setui y1 20",
    ]
    #TODO: more test cases
    riscv_config_path = "riscv_config.json"
    for inst in instructions:
        machine_code_hex = riscv_assemble_insts(inst, riscv_config_path)
        print(f"{inst} -> {machine_code_hex}")
    generate_assemble("assembly_ttl.s", "test.mem", "test.hex", riscv_config_path)