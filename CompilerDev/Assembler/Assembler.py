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
        #格式要求： 1 补 2个，2补1个，3补0个，0补3个 
        switch = i % 4
        if switch == 1:
            f.write("0000006f")
            f.write("0000006f")
            f.write("ffffffff\n")
        elif switch == 2:
            f.write("0000006f")
            f.write("ffffffff")
        elif switch == 3:
            f.write("ffffffff")
        elif switch == 0:
            f.write("0000006f")
            f.write("0000006f")
            f.write("0000006f")
            f.write("ffffffff")
    
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
    # write_machinecode2hex(output_hex_filename, machine_codes) # 暂时先不需要
    print("Assembly code assembled successfully!")

def merge_inst_files_with_header(file1, output_file):
    #生成指令需要的包头
    full_output_merge = output_file
    with open(file1, 'r') as f1:  # 建议添加encoding='utf-8'避免编码错误
        lines1 = f1.readlines()
    total_lines = len(lines1)
    total_lines_hex = format(total_lines, '04x')
    header = f"eb9c55aa0001000000000000{total_lines_hex}0000\n"
    merged_content = [header] + lines1
    
    with open(full_output_merge, 'w', encoding='utf-8') as output:  # 同样添加encoding
        output.writelines(merged_content)
    
    print(f"添加header成功，文件已保存到: {full_output_merge}")
    print(f"header: {header.strip()}")

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
    #TODO: more test cases
    riscv_config_path = "riscv_config.json"
    # for inst in instructions:
    #     machine_code_hex = riscv_assemble_insts(inst, riscv_config_path)
    #     print(f"{inst} -> {machine_code_hex}")
    generate_assemble("assembly_ttl.s", "test.txt", "test.hex", riscv_config_path)
    merge_inst_files_with_header("test.txt", "test_header.txt")