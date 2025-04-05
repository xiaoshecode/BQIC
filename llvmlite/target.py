from __future__ import print_function
from ctypes import CFUNCTYPE, c_double
# import llvmlite
import llvmlite.binding as binding
from llvmlite import ir

# 初始化LLVM
binding.initialize()
binding.initialize_all_targets()
binding.initialize_native_target()
binding.initialize_native_asmprinter()

target = binding.Target.from_default_triple()
target_machine = target.create_target_machine()
print("target:", target)
print("target_machine:",target_machine)
print(binding.llvm_version_info)

riscv_target = binding.Target.from_triple("riscv32-unknown-linux")
riscv_machine = riscv_target.create_target_machine(
    cpu="generic-rv32",
    features="+m", #基础整数指令集
    opt=0,
    reloc="default",
    codemodel="small",
    abiname="ilp32" # 整数ABI(Application Binary Interface)，不支持硬件浮点运算
)
