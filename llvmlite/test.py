from llvmlite import ir

# Create some types
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

# Print the module IR
print(module)
