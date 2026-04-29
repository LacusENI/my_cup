version: 0.3

data: 2026/06/15

# 添加的指令
- sb
- sh

# 1. sb rt, offset(rs)
编码
| opcode(6) | rs(5)  | rt(5)  | offset(16) |
| :-------: | :----: | :----: | :------:: |
| 00 1010   |    -   |    -   |     -     |
- IF : reg_src1 = base, reg_src2 = rt, imm = offset
- ID : src1 = R[reg_src1], src2 = imm, rs2_data = R[reg_src2]
- EX : alu_out = src1 + src2
- MEM: M[alu_out] = R[reg_src2][7:0]
- WB : 

# 2. sh rt, offset(rs)
编码
| opcode(6) | rs(5)  | rt(5)  | offset(16) |
| :-------: | :----: | :----: | :------:: |
| 00 1011   |    -   |    -   |     -     |
- IF : reg_src1 = base, reg_src2 = rt, imm = offset
- ID : src1 = R[reg_src1], src2 = imm, rs2_data = R[reg_src2]
- EX : alu_out = src1 + src2
- MEM: M[alu_out] = R[reg_src2][15:0]
- WB : 
