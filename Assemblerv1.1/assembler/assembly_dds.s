addi x1 x0 0
addi x2 x0 3
setur y0 x1 0 #x1循环变量，x2
setur y1 x1 0
setur y2 x1 0
setur y3 x1 0
setur y4 x1 0
setur y5 x1 0
setur y6 x1 0
setur y7 x1 0
setur y8 x1 0
setur y9 x1 0
setur y10 x1 0
setur y11 x1 0
setur y12 x1 0
setur y13 x1 0
setur y14 x1 0
setur y15 x1 0
setur y16 x1 0
setur y17 x1 0
setur y18 x1 0
setur y19 x1 0
setur y20 x1 0
setur y21 x1 0
setur y22 x1 0
setur y23 x1 0 #数组长度是无限
addi x1 x1 1
bne x1 x2 -100 #一行是4，跳转到第三行
jal x0 0 #结束语句
jal x0 0