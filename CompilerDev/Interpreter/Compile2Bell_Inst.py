# 自己动手，丰衣足食
def addi(rd, rs, imm):
    """
    立即数加法指令
    :param rs: 源寄存器
    :param rd: 目标寄存器
    :param imm: 立即数
    :return: 汇编指令字符串
    """
    return f"addi {rd} {rs} {imm}"


def setur(rd, rs, imm):
    """
    立即数赋值指令
    :param rs: 源寄存器
    :param rd: 目标寄存器
    :param imm: 立即数
    :return: 汇编指令字符串
    """
    return f"setur {rd} {rs} {imm}"


def bne(rd, rs, opaddress):
    """
    分支指令
    :param rs: 源寄存器
    :param rd: 目标寄存器
    :param opaddress: 相对偏移地址,可正可负
    :return: 汇编指令字符串
    """
    return f"bne {rd} {rs} {opaddress}"


def jal(rd, opaddress):
    """
    跳转指令
    :param rd: 目标寄存器
    :param opaddress: 相对偏移地址,可正可负
    :return: 汇编指令字符串
    """
    return f"jal {rd} {opaddress}"


def add(rd, rs1, rs2):
    """
    加法指令
    :param rd: 目标寄存器
    :param rs1: 源寄存器1
    :param rs2: 源寄存器2
    :return: 汇编指令字符串
    """
    return f"add {rd} {rs1} {rs2}"


def setui(rd, imm):
    """
    立即数赋值指令
    :param rd: 目标寄存器
    :param imm: 立即数
    :return: 汇编指令字符串
    """
    return f"setui {rd} {imm}"


def lujr(rd, rs):
    """
    跳转指令
    :param rd: 目标寄存器
    :param rs: 源寄存器
    :return: 汇编指令字符串
    """
    return f"lujr {rd} {rs}"


def luw(rd, rs):
    """
    加载寄存器指令
    :param rd: 目标寄存器
    :param rs: 源寄存器
    :return: 汇编指令字符串
    """
    return f"luw {rd} {rs}"


def jump(rd, label):  # 跳转的伪指令，便于进行地址操作和寻址，jump到某个lable的地址
    """
    跳转指令
    :param rd: 目标寄存器
    :param label: 标签地址
    :return: 汇编指令字符串
    """
    return f"jump {rd} {label}"


def EndSeq():
    """
    结束指令
    :return: 汇编指令字符串
    """
    return jal("x0", 0)


def StopCPU():
    """
    停止CPU指令
    :return: 汇编指令字符串
    """
    return setui("halt", 1)


# no branch
def LoadDDS(x2: int, x3: int = 0):
    # TODO : need to be optimized
    """
    加载DDS指令
    :param x2: 循环截至变量
    :param x3: 程序运行数据存储的基地址
    :return: 汇编指令字符串
    返回生成的汇编指令列表和汇编指令的长度
    """
    # 设置初始循环变量x1, 循环截至变量x2, 同步触发写入y40
    Asmembly = []
    Asmembly.append(addi("x1", "x0", 0))
    Asmembly.append(addi("x2", "x0", x2))
    # for i in range(24):
    Asmembly.append(setur("y40", "x3", 0))  # 设置寄存器y40为当前频率
    Asmembly.append(addi("x3", "x3", 1))
    Asmembly.append(addi("x1", "x1", 1))
    Asmembly.append(bne("x1", "x2", -4 * (3)))  # 循环结束条件
    return Asmembly, len(Asmembly)


# dds_module, len_dds = LoadDDS(2)
# print(dds_module,len_dds)


def LoadTTL(x2: int):
    """
    加载TTL指令
    :param x1: 循环变量 == 序列长度 
    :param x2: 循环截至变量
    :return: 汇编指令字符串
    返回生成的汇编指令列表和汇编指令的长度
    """
    # 设置初始循环变量x1, 循环截至变量x2
    Asmembly = []
    Asmembly.append(addi("x1", "x0", 0))
    Asmembly.append(addi("x2", "x0", x2))
    for i in range(32):
        Asmembly.append(setur("y{}".format(i), "x1", 0))  # 设置寄存器y0为当前频率
    Asmembly.append(addi("x1", "x1", 1))
    Asmembly.append(bne("x1", "x2", -4 * (1 + 32)))  # 循环结束条件
    return Asmembly, len(Asmembly)


def LoadwithBranch_TTL(BranchLen: list, BranchBlock:list):  # Two Branch
    # 第一段branch的长度为BranchLen[0]，相对跳转地址为4*(BranchLen[0])
    # 第二段branch的长度为BranchLen[1]，
    # JumpReg = "x31" # ttl计数结果放在x31寄存器中
    # Branch1Reg = "x30"  # 跳转寄存器1
    # Branch2Reg = "x29"  # 跳转寄存器2
    # BranchBlock  存放Branch1和Branch2的具体指令
    # BranchLen    存放Branch1和Branch2的指令长度
    Asmembly = []
    Asmembly.append(StopCPU())
    Asmembly.append(luw("x31", "z1"))
    Asmembly.append(
        bne("x31", "x0", 4 * (BranchLen[0]))
    )  # TODO: 增加其他判断类型,增加更多跳转分支，增加条件约束
    Asmembly.append(BranchBlock[0])  # 跳转分发，暂停CPU
    
    Asmembly.append(BranchBlock[1]) 
    return Asmembly, len(Asmembly)
# def LoadwithBranch_DDS(BranchLen:list):

def TCMSendJump():
    """
    TTL接受跳转指令后，所有板卡同步进行跳转,two branch
    """
    BranchBlock0 = []
    BranchBlock1 = []
    BranchBlock0.append(setui("jump", 1)) # 跳转到第一个分支
    BranchBlock0.append(StopCPU()) # 停止CPU

    BranchBlock1.append(setui("jump", 2)) # 跳转到第二个分支
    BranchBlock1.append(StopCPU()) # 停止CPU
    
    BranchBlock = [BranchBlock0, BranchBlock1]
    BranchLen = [len(BranchBlock0),len(BranchBlock1)] # 分支长度

    Asm,AsmLen = LoadwithBranch_TTL(BranchLen, BranchBlock) # 生成跳转指令

    return Asm, AsmLen # 返回生成的汇编指令和长度

def TCMReceiveJump():
    """
    所有板卡接受跳转指令进行同步跳转
    """
    # 板卡上需要跳转的基地址


if __name__ == "__main__":
    # LoadDDS(2)
    # print(LoadDDS(2))
    SeqLen = 3
    Inst = LoadDDS(3)
    # 将列表逐行写入文件
    # for item in Inst:
    #     print(item)
    with open("../Output/LoadDDS.txt", "w") as f:
        for item in Inst[0]:
            f.write(item + "\n")
