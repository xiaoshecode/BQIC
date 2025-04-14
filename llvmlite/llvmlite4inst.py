import llvmlite.binding as binding
import llvmlite.ir as ir

binding.initialize()
binding.initialize_all_targets()
binding.initialize_all_asmprinters()
binding.initialize_native_target()
binding.initialize_native_asmprinter()


def create_target_machine():
    riscv_target = binding.Target.from_triple("riscv32-unknown-linux")
    riscv_machine = riscv_target.create_target_machine(
        cpu="generic-rv32",
        # features="+m", #基础整数指令集
        opt=0,
        reloc="default",
        codemodel="small",
        abiname="ilp32",  # 整数ABI(Application Binary Interface)，不支持硬件浮点运算
    )
    return riscv_target, riscv_machine


riscv_target, riscv_machine = create_target_machine()
module = ir.Module(name="loadmemory")
module.triple = riscv_target.triple
func_type = ir.FunctionType(ir.VoidType(), [])
func = ir.Function(module, func_type, name="main")
block = func.append_basic_block(name="entry")
builder = ir.IRBuilder(block)

# custom_asm_code = ".word 0xABCDEF01"  # 使用直接的十六进制表示自定义指令
# 或者如果有助记符: "custom.acc x10, x11, x12"
# 插入一条riscv的csr指令，CSRRC rd, csr, rs1
# custom_asm_code = ".word 0x3005B073"  # 假设 x10 是一个寄存器
# asm_func_type = ir.FunctionType(ir.VoidType(), [])  # 定义函数类型
# custom_inline_asm = ir.InlineAsm(asm_func_type, custom_asm_code, "", True)
# builder.call(custom_inline_asm, [])  # 调用内联汇编函数
# builder.load_reg(ir.IntType(32), "x1")  #
# builder.store_reg(ir.Constant(ir.IntType(32), 1999), ir.IntType(32),"x10")  # 假设 x10 是一个寄存器
# builder.store_reg(ir.Constant(ir.IntType(32), 1999), ir.IntType(32),"x11")  # 假设 x11 是一个寄存器
builder.ret_void()

# 输出生成的 LLVM IR
print("Generated LLVM IR:")
print(module)

llvm_module = binding.parse_assembly(module.__repr__())
print("Assembly code:")
print(riscv_machine.emit_assembly(llvm_module))
# print("\nRISCV32 Machine code:")
# machine_code = riscv_machine.emit_object(llvm_module)