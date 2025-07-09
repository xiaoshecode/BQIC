import utils4assemble


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
    # print("汇编指令:", instructions)
    machine_codes = [riscv_assemble_insts(inst, riscv_config_path) for inst in instructions]
    write_machinecode(output_filename, machine_codes)
    write_machinecode2hex(output_hex_filename, machine_codes)
    print("Assembly code assembled successfully!")


def merge_param_files_with_header(file1, output_file):
    with open(file1, 'r') as f1:
        lines1 = f1.readlines()
    total_lines = len(lines1)
    total_lines_hex = format(total_lines, '04x')
    header = f"eb9c55aa0002000000000000{total_lines_hex}0000\n"
    merged_content = [header] + lines1
    with open(output_file, 'w') as output:
        output.writelines(merged_content)
    print(f"添加header成功，文件已保存到: {output_file}")
    print(f"header: {header.strip()}")
# testbench
if __name__ == "__main__":
    # Example usage
    # instructions = [
    #     "addi x1 x0 0",
    #     "addi x2 x0 1",
    #     "setur y0 x1 0",
    #     "setur y1 x1 0",
    #     "setur y2 x1 0",
    #     "setur y3 x1 0",
    #     "setur y4 x1 0",
    #     "setur y5 x1 0",
    #     "setur y6 x1 0",
    #     "setur y7 x1 0",
    #     "setur y8 x1 0",
    #     "setur y9 x1 0",
    #     "setur y10 x1 0",
    #     "setur y11 x1 0",
    #     "setur y12 x1 0",
    #     "setur y13 x1 0",
    #     "setur y14 x1 0",
    #     "setur y15 x1 0",
    #     "setur y16 x1 0",
    #     "setur y17 x1 0",
    #     "setur y18 x1 0",
    #     "setur y19 x1 0",
    #     "setur y20 x1 0",
    #     "setur y21 x1 0",
    #     "setur y22 x1 0",
    #     "setur y23 x1 0",
    #     "addi x1 x1 1",
    #     "bne x1 x2 -100",
    # ]
    #TODO: more test cases
    riscv_config_path = "riscv_config.json"
    # for inst in instructions:
    #     machine_code_hex = riscv_assemble_insts(inst, riscv_config_path)
    #     print(f"{inst} -> {machine_code_hex}")
    generate_assemble("assembly_ttl.s", "test.txt", "test.hex", riscv_config_path)
    merge_param_files_with_header("test.txt", "test_header.txt")