version: v0.1

date: 2026/03/12

## 描述
算术逻辑单元

## 端口
input
- alu_src1(32): 操作数1
- alu_src2(32): 操作数2
- alu_op(4): 操作码

output
- alu_out(32) : 运算结果
- zero_f : 结果为零
- negative_f : 结果为负
- overflow_f : 结果溢出
- carry_f : 进位为1

## 操作码定义

- ADD : 0001
- SUB : 0010
- MUL : 0011
- DIV : 0100
- AND : 0101
- OR  : 0110
- XOR : 0111
- NOR : 1000
- SRA : 1001
- SRL : 1010
- SLL : 1011