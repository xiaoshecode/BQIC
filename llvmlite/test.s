	.text
	.attribute	4, 16
	.attribute	5, "rv32i2p0"
	.file	"<string>"
	.globl	test_func
	.p2align	2
	.type	test_func,@function
test_func:
	.cfi_startproc
	li	a0, 0
	bne	a0, a0, .LBB0_2
	j	.LBB0_1
.LBB0_1:
	j	.LBB0_3
.LBB0_2:
	j	.LBB0_3
.LBB0_3:
	ret
.Lfunc_end0:
	.size	test_func, .Lfunc_end0-test_func
	.cfi_endproc

	.section	".note.GNU-stack","",@progbits
