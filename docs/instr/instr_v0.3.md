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

## 3. lb rt, offset(base)
编码
|  lb(6)  | base(5) |  rt(5)  | offset(16) |
| :-----: | :-----: | :-----: | :--------: |
| [31:26] | [25:21] | [20:16] |   [15:0]   |
| 10 0000 |    -    |    -    |     -      |

- IF : reg_src1 = base, reg_dst = rt, imm = offset
- ID : src1 = R[reg_src1], src2 = imm
- EX : alu_out = src1 + src2
- MEM: r_data = sign_ext(M[alu_out]_byte)
- WB : R[reg_dst] = r_data

## 4. lbu rt, offset(base)
编码
|  lbu(6) | base(5) |  rt(5)  | offset(16) |
| :-----: | :-----: | :-----: | :--------: |
| [31:26] | [25:21] | [20:16] |   [15:0]   |
| 10 0100 |    -    |    -    |     -      |

- IF : reg_src1 = base, reg_dst = rt, imm = offset
- ID : src1 = R[reg_src1], src2 = imm
- EX : alu_out = src1 + src2
- MEM: r_data = zero_ext(M[alu_out]_byte)
- WB : R[reg_dst] = r_data

## 5. lh rt, offset(base)
编码
|  lh(6)  | base(5) |  rt(5)  | offset(16) |
| :-----: | :-----: | :-----: | :--------: |
| [31:26] | [25:21] | [20:16] |   [15:0]   |
| 10 0001 |    -    |    -    |     -      |

- IF : reg_src1 = base, reg_dst = rt, imm = offset
- ID : src1 = R[reg_src1], src2 = imm
- EX : alu_out = src1 + src2
- MEM: r_data = sign_ext(M[alu_out]_halfword)
- WB : R[reg_dst] = r_data

## 6. lhu rt, offset(base)
编码
|  lhu(6) | base(5) |  rt(5)  | offset(16) |
| :-----: | :-----: | :-----: | :--------: |
| [31:26] | [25:21] | [20:16] |   [15:0]   |
| 10 0101 |    -    |    -    |     -      |

- IF : reg_src1 = base, reg_dst = rt, imm = offset
- ID : src1 = R[reg_src1], src2 = imm
- EX : alu_out = src1 + src2
- MEM: r_data = zero_ext(M[alu_out]_halfword)
- WB : R[reg_dst] = r_data
