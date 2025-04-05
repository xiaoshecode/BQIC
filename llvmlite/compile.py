from __future__ import print_function
from ctypes import CFUNCTYPE, c_double
# import llvmlite.binding as llvm
import llvmlite.binding as binding
from llvmlite import ir

binding.initialize()
binding.initialize_all_targets()
binding.initialize_native_target()
binding.initialize_native_asmprinter()
binding.initialize_all_asmprinters()

#  # Create some types
double = ir.DoubleType()
int32 = ir.IntType(32)
fnty = ir.FunctionType(int32, (int32, int32))

# Create a new module as add
# module = ir.Module("test")
# module.triple = "riscv32-unknown-linux"
# # declare a function

# func = ir.Function(module, fnty, name="add")

# # Now implement the function
# block = func.append_basic_block(name="entry")
# builder = ir.IRBuilder(block)
# a, b = func.args
# result = builder.add(a, b, name="res")
# builder.ret(result)

# Create a new module as jump
module = ir.Module(name="example")
func_type = ir.FunctionType(ir.VoidType(), [])
func = ir.Function(module, func_type, name="test_func")
entry_block = func.append_basic_block(name="entry")
true_block = func.append_basic_block(name="true_block")
false_block = func.append_basic_block(name="false_block")
exit_block = func.append_basic_block(name="exit")

builder = ir.IRBuilder(entry_block)

# 创建条件变量
cond = ir.Constant(ir.IntType(1), 1)  # 条件为真
builder.cbranch(cond, true_block, false_block)

# 在 true_block 中插入跳转到 exit_block
builder.position_at_end(true_block)
builder.branch(exit_block)

# 在 false_block 中插入跳转到 exit_block
builder.position_at_end(false_block)
builder.branch(exit_block)

# 在 exit_block 中插入返回指令
builder.position_at_end(exit_block)
builder.ret_void()

# Create a new module as load
# # 创建模块和函数
# module = ir.Module(name="example")
# func_type = ir.FunctionType(ir.VoidType(), [])
# func = ir.Function(module, func_type, name="test_func")
# entry_block = func.append_basic_block(name="entry")

# builder = ir.IRBuilder(entry_block)

# # 分配一个整数变量
# int32 = ir.IntType(32)
# ptr = builder.alloca(int32, name="my_var")  # 分配内存
# builder.store(ir.Constant(int32, 42), ptr)  # 将值 42 存储到内存中

# # 从内存中读取值
# loaded_value = builder.load(ptr, name="loaded_value")

# # 打印读取的值（LLVM IR 中没有直接打印功能，这里仅生成 IR）
# builder.ret_void()

# 输出生成的 LLVM IR
print(module)
# # print(module)

def create_target_machine():
    riscv_target = binding.Target.from_triple("riscv32-unknown-linux")
    riscv_machine = riscv_target.create_target_machine(
        cpu="generic-rv32",
        # features="+m", #基础整数指令集
        opt=0,
        reloc="default",
        codemodel="small",
        abiname="ilp32" # 整数ABI(Application Binary Interface)，不支持硬件浮点运算
    )
    return riscv_target,riscv_machine 

def create_execution_engine():
    # Create a target machine representing the host
    # target = llvm.Target.from_triple("riscv32-unknown-linux")
    # print("target is:", target)
    target,target_machine = create_target_machine()
    # And an execution engine with an empty backing module
    backing_mod = binding.parse_assembly("")
    engine = binding.create_mcjit_compiler(backing_mod, target_machine)
    return engine


def compile_ir(engine, llvm_ir):
    # Create a LLVM IR string with the given engine

    # Create a LLVM module object from the IR
    mod = binding.parse_assembly(llvm_ir)
    mod.verify()
    # add the module and make sure it is ready for execution
    engine.add_module(mod)
    engine.finalize_object()
    engine.run_static_constructors()
    return mod

if __name__ == '__main__':
    # engine = create_execution_engine()
    # mod = compile_ir(engine, module.__repr__())  # transfer to string

    riscv_target, riscv_machine = create_target_machine()
    print("riscv_target:", riscv_target)
    print("riscv_machine:", riscv_machine)

    llvm_module = binding.parse_assembly(module.__repr__())
    
    # 输出汇编代码
    print("\nRISCV32 Assembly code:")
    print(riscv_machine.emit_assembly(llvm_module))
    save_path = "test.s"
    with open(save_path, "w") as f:
        f.write(riscv_machine.emit_assembly(llvm_module))
    print("Save assembly code to", save_path)
    # 输出机器码
    # print("\nRISCV32 Machine code:")
    machine_code = riscv_machine.emit_object(llvm_module)

    save_path = "test.o"
    with open(save_path, "wb") as f:
        f.write(machine_code)
    print("Save machine code to", save_path)

    # from elftools.elf.elffile import ELFFile
