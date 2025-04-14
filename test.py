import llvmlite.binding as binding
import llvmlite.ir as ir
binding.initialize()
binding.initialize_all_targets()
binding.initialize_all_asmprinters()
binding.initialize_native_target()
binding.initialize_native_asmprinter()
module = ir.Module(name="addmyinst")
func_type = ir.FunctionType(ir.VoidType(),[])
func = ir.Function(module, func_type, name="main")
block = func.append_basic_block(name="entry")
builder = ir.IRBuilder(block)
# builder.asm(
#     asm="addi x1, x0, 0\n"
#         "addi x2, x0, 3\n"
#         "setur y0, x1, 0\n"
#         "setur y1, x1, 0\n"
#         "setur y2, x1, 0\n"
#         "addi x1, x1, 1\n"
#         "bne x1, x2, -52\n"
#         "jal x0, 0\n",
#     ftype=ir.FunctionType(ir.VoidType(), []),
#     constraint="~{x1},~{x2},~{y0},~{y1},~{y2}",
#     args=[],
#     side_effect=True
# )
builder.ret_void()
# 输出生成的 LLVM IR
print("Generated LLVM IR:")
print(module)

# 解析并验证 IR
llvm_ir = str(module)
binding_module = binding.parse_assembly(llvm_ir)
binding_module.verify()

# 创建目标机
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
target, target_machine = create_target_machine()

# 生成汇编代码
asm = target_machine.emit_assembly(binding_module)
print("\nGenerated Assembly:")
print(asm)