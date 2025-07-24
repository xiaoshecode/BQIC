import re
from CompilerDev.Interpreter.DDS_Seq import DDS, Seq
def extract_number(string):
    # 使用正则表达式匹配所有数字
    numbers = re.findall(r'\d+', string)
    # 如果找到数字，返回第一个数字
    # print("numbers:", numbers)
    if numbers:
        return int(numbers[0])
    # 如果没有找到数字，返回None
    return None

def compile2Bell(seqs): # RTMQv1.0 transfer to Bell
    """
    将序列转换为Bell硬件执行的IR   
    每个dds通道有4个参数[f,a,p,t]
    每个ttl通道有3个参数[mode,address]，暂时用来计数input , [mode, delay]
    """
    seq4Bell = []
    for seq in seqs:
        # 逆序遍历
        Flag_TTL = False
        Flag_Delay = False
        delay = 0
        DDSList = []
        for item in seq[::-1]:
            if type(item)==type(DDS("dds")):
                # print("dds")
                DeviceID = extract_number(item.name[0])
                Freq = item[0]
                Amp = item[1]
                Phase = item[2]
                DDSList.append(["dds",DeviceID, Freq, Amp, Phase,delay])
            if Flag_Delay == False:
                delay = item # 读取延时
                Flag_Delay = True
                # print("delay:", delay)
            if Flag_TTL==False: # 读取TTL
                # TTL = item
                mode = 1 #1: input,0:output
                # if mode == #TTL mode 在硬件中不能导入
                Flag_TTL = True
                # print("TTL channel:", TTL)
        DDSList.reverse() # 反转顺序
        DDSList.append(["TTL", mode, delay])
        # print("DDSList:", DDSList)
        seq4Bell.append(DDSList)
    # print("Bell序列:", seq4Bell)
    return seq4Bell

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