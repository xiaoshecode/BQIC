import json


def load_json(file):
    with open(file) as f:
        return json.load(f)


# class RISCV4bqic():#TODO
# def __init__(self):

def riscv_load_config(filename="riscv_config.json"):
    # Load the RISC-V configuration file
    riscv_config = load_json(filename)
    # Instruction_Set = riscv_config["INSTRUCTION_SET"]
    # Register_Map = riscv_config["REGISTER_MAP"]
    # User_Register_Map = riscv_config["USER_REGISTER_MAP"]
    # User_Read_Register_Map = riscv_config["USER_READ_REGISTER_MAP"]
    return riscv_config


def riscv_assemble_rtype(riscv_config, instr, rd, rs1, rs2):
    opcode = riscv_config["INSTRUCTION_SET"][instr]["opcode"]
    funct3 = riscv_config["INSTRUCTION_SET"][instr]["funct3"]
    funct7 = riscv_config["INSTRUCTION_SET"][instr]["funct7"]
    rd_bin = riscv_config["REGISTER_MAP"][rd]
    rs1_bin = riscv_config["REGISTER_MAP"][rs1]
    rs2_bin = riscv_config["REGISTER_MAP"][rs2]
    assemblebin_rtype = funct7 + rs2_bin + rs1_bin + funct3 + rd_bin + opcode
    return assemblebin_rtype


def risv_assemble_itype(riscv_config, instr, rd, rs1, imm):
    opcode = riscv_config["INSTRUCTION_SET"][instr]["opcode"]
    funct3 = riscv_config["INSTRUCTION_SET"][instr]["funct3"]
    rd_bin = riscv_config["REGISTER_MAP"][rd]
    rs1_bin = riscv_config["REGISTER_MAP"][rs1]
    imm_bin = number2bin(imm, 12)
    assemblebin_itype = imm_bin + rs1_bin + funct3 + rd_bin + opcode
    return assemblebin_itype


def riscv_assemble_stype(riscv_config, instr, rs1, rs2, imm):
    opcode = riscv_config["INSTRUCTION_SET"][instr]["opcode"]
    funct3 = riscv_config["INSTRUCTION_SET"][instr]["funct3"]
    rs1_bin = riscv_config["REGISTER_MAP"][rs1]
    rs2_bin = riscv_config["REGISTER_MAP"][rs2]
    imm_bin = number2bin(imm, 12)
    imm_bin1 = imm_bin[:7]
    imm_bin2 = imm_bin[7:]
    assemblebin_stype = imm_bin1 + rs2_bin + rs1_bin + funct3 + imm_bin2 + opcode
    return assemblebin_stype


def riscv_assemble_btype(riscv_config, instr, rs1, rs2, imm):
    opcode = riscv_config["INSTRUCTION_SET"][instr]["opcode"]
    funct3 = riscv_config["INSTRUCTION_SET"][instr]["funct3"]
    rs1_bin = riscv_config["REGISTER_MAP"][rs1]
    rs2_bin = riscv_config["REGISTER_MAP"][rs2]
    imm_bin = number2bin_trans(imm, 13)
    imm_bin1 = imm_bin[0]
    imm_bin2 = imm_bin[2:8]
    imm_bin3 = imm_bin[8:12]
    imm_bin4 = imm_bin[1]
    assemblebin_btype = (
        imm_bin1 + imm_bin2 + rs2_bin + rs1_bin + funct3 + imm_bin3 + imm_bin4 + opcode
    )
    return assemblebin_btype


def riscv_assemble_lui(riscv_config, instr, rd, imm):
    opcode = riscv_config["INSTRUCTION_SET"][instr]["opcode"]
    rd_bin = riscv_config["REGISTER_MAP"][rd]
    imm_bin = number2bin_trans(imm, 20)
    assemblebin_lui = imm_bin + rd_bin + opcode
    return assemblebin_lui


def riscv_assemble_auipc(riscv_config, instr, rd, imm):
    opcode = riscv_config["INSTRUCTION_SET"][instr]["opcode"]
    rd_bin = riscv_config["REGISTER_MAP"][rd]
    imm_bin = number2bin_trans(imm, 20)
    assemblebin_auipc = imm_bin + rd_bin + opcode
    return assemblebin_auipc


def riscv_assemble_jal(riscv_config, instr, rd, imm):
    opcode = riscv_config["INSTRUCTION_SET"][instr]["opcode"]
    rd_bin = riscv_config["REGISTER_MAP"][rd]
    imm_bin = number2bin_trans(imm, 21)
    imm_bin1 = imm_bin[0]
    imm_bin2 = imm_bin[10:20]
    imm_bin3 = imm_bin[9]
    imm_bin4 = imm_bin[1:9]
    assemblebin_jal = imm_bin1 + imm_bin2 + imm_bin3 + imm_bin4 + rd_bin + opcode
    return assemblebin_jal


def riscv_assemble_jalr(riscv_config, instr, rd, rs1, imm):
    opcode = riscv_config["INSTRUCTION_SET"][instr]["opcode"]
    funct3 = riscv_config["INSTRUCTION_SET"][instr]["funct3"]
    rd_bin = riscv_config["REGISTER_MAP"][rd]
    rs1_bin = riscv_config["REGISTER_MAP"][rs1]
    imm_bin = number2bin_trans(imm, 12)
    assemblebin_jalr = imm_bin + rs1_bin + funct3 + rd_bin + opcode
    return assemblebin_jalr


def riscv_assemble_lujr(riscv_config, instr, rd, rs1):
    opcode = riscv_config["INSTRUCTION_SET"][instr]["opcode"]
    funct3 = riscv_config["INSTRUCTION_SET"][instr]["funct3"]
    rd_bin = riscv_config["REGISTER_MAP"][rd]
    rs1_bin = riscv_config["REGISTER_MAP"][rs1]
    imm_bin = "000000000000"
    assemblebin_lujr = imm_bin + rs1_bin + funct3 + rd_bin + opcode
    return assemblebin_lujr


def riscv_assemble_luw(riscv_config, instr, rd, urs):
    opcode = riscv_config["INSTRUCTION_SET"][instr]["opcode"]
    funct3 = riscv_config["INSTRUCTION_SET"][instr]["funct3"]
    rd_bin = riscv_config["REGISTER_MAP"][rd]
    urs_bin = riscv_config["USER_READ_REGISTER_MAP"][urs]
    assemblebin_luw = "0" + urs_bin + "0000000000000" + funct3 + rd_bin + opcode
    return assemblebin_luw


def riscv_assemble_setur(riscv_config, instr, urd, rs1, imm):
    opcode = riscv_config["INSTRUCTION_SET"][instr]["opcode"]
    urd_bin = riscv_config["USER_REGISTER_MAP"][urd]
    rs1_bin = riscv_config["REGISTER_MAP"][rs1]
    imm_bin = number2bin(imm, 12)
    imm_bin1 = imm_bin[0:4]
    imm_bin2 = imm_bin[4:12]
    assemblebin_setur = imm_bin1 + urd_bin + rs1_bin + imm_bin2 + opcode
    return assemblebin_setur


def assemble_setui(riscv_config, instr, urd, imm):
    opcode = riscv_config["INSTRUCTION_SET"][instr]["opcode"]
    urd_bin = riscv_config["USER_REGISTER_MAP"][urd]
    imm_bin = number2bin(imm, 16)
    imm_bin1 = imm_bin[0:3]
    imm_bin2 = imm_bin[3:16]
    assemblebin_setui = imm_bin1 + urd_bin + imm_bin2 + opcode
    return assemblebin_setui


def number2bin_trans(val, bits):
    # 计算一个二进制补码表示
    # val:字符串类型的整数
    # bits: 位数
    # 返回值: 二进制补码表示，字符串类型
    val = int(val)
    if val < 0:
        val = (1 << bits) + val
    return format(val, f"0{bits}b")


def number2bin(val: int, bits: int):
    # 将一个整数转换为二进制表示
    # val: 整数
    # bits: 位数
    # 返回值: 二进制表示，字符串类型
    return format(int(val), f"0{bits}b")


def bin2hex(binstr: str):
    # 将一个二进制字符串转换为十六进制字符串
    # binstr: 二进制字符串
    # 返回值: 十六进制字符串
    return format(int(binstr, 2), "08x")
