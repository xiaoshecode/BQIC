from __future__ import print_function
from ctypes import CFUNCTYPE, c_double
import llvmlite.binding as llvm

llvm.initialize()
llvm.initialize_native_target()
llvm.initialize_native_asmprinter()

# LLVM IR
from llvmlite import ir

#  # Create some types
double = ir.DoubleType()
int32 = ir.IntType(32)
fnty = ir.FunctionType(double, (double, double))

# Create a new module
module = ir.Module("test")
module.triple = "Bell-RISCV"
# declare a function
func = ir.Function(module, fnty, name="fpadd")

# Now implement the function
block = func.append_basic_block(name="entry")
builder = ir.IRBuilder(block)
a, b = func.args
result = builder.fadd(a, b, name="res")
builder.ret(result)

# print(module)


def create_execution_engine():
    # Create a target machine representing the host
    target = llvm.Target.from_default_triple()
    print("target is:", target)
    target_machine = target.create_target_machine()
    # And an execution engine with an empty backing module
    backing_mod = llvm.parse_assembly("")
    engine = llvm.create_mcjit_compiler(backing_mod, target_machine)
    return engine


def compile_ir(engine, llvm_ir):
    # Create a LLVM IR string with the given engine

    # Create a LLVM module object from the IR
    mod = llvm.parse_assembly(llvm_ir)
    mod.verify()
    # add the module and make sure it is ready for execution
    engine.add_module(mod)
    engine.finalize_object()
    engine.run_static_constructors()
    return mod


engine = create_execution_engine()
mod = compile_ir(engine, module.__repr__())  # transfer to string

# Look up the function pointer (a Python int)
func_ptr = engine.get_function_address("fpadd")

# Run the function via ctypes
cfunc = CFUNCTYPE(c_double, c_double, c_double)(func_ptr)
res = cfunc(1.0, 3.5)
print("fpadd(1.0, 3.5) =", res)
