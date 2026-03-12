version: v0.1 

date: 2026/03/12

## 支持的指令
- addu
- addiu
- lw
- sw
- beq
- j

## 1. addu rd, rs, rt
编码
| special(6) |  rs(5)  |  rt(5)  |  rd(5)  |  0(5)  | addu(6) |
| :--------: | :-----: | :-----: | :-----: | :----: | :-----: |
|  [31:26]   | [25:21] | [20:16] | [15:11] | [10:6] |  [5:0]  |
|  00 0000   |    -    |    -    |    -    | 0 0000 | 10 0001 |

- IF : reg_src1 = rs, reg_src2 = rt, reg_dst = rd
- ID : src1 = R[reg_src1], src2 = R[reg_src2]
- EX : alu_out = src1 + src2
- MEM: 
- WB : R[reg_dst] = alu_out

## 2. addiu rt, rs, imm
编码
| addi(6) |  rs(5)  |  rt(5)  | imm(16) |
| :-----: | :-----: | :-----: | :-----: |
| [31:26] | [25:21] | [20:16] | [15:0]  |
| 00 1001 |    -    |    -    |    -    |

- IF : reg_src1 = rs, reg_dst = rt, imm = imm
- ID : src1 = R[reg_src1], src = imm
- EX : alu_out = src1 + src2
- MEM: 
- WB : R[reg_dst] = alu_out

## 3. lw rt, offset(base)
编码
|  lw(6)  | base(5) |  rt(5)  | offset(16) |
| :-----: | :-----: | :-----: | :--------: |
| [31:26] | [25:21] | [20:16] |   [15:0]   |
| 10 0011 |    -    |    -    |     -      |

- IF : reg_src1 = base, reg_dst = rt, imm = offset
- ID : src1 = R[reg_src1], src2 = imm
- EX : alu_out = src1 + src2
- MEM: r_data = M[alu_out]
- WB : R[reg_dst] = r_data

## 4. sw rt, offset(base)
编码
|  sw(6)  | base(5) |  rt(5)  | offset(16) |
| :-----: | :-----: | :-----: | :--------: |
| [31:26] | [25:21] | [20:16] |   [15:0]   |
| 00 0100 |    -    |    -    |     -      |

- IF : reg_src1 = base, reg_src2 = rt, imm = offset
- ID : src1 = R[reg_src1], src2 = imm, rs2_data = R[reg_src2]
- EX : alu_out = src1 + src2
- MEM: M[alu_out] = rs2_data
- WB : 

## 5. beq rs, rt, offset
编码
| beq(6)  |  bs(5)  |  rt(5)  | offset(16) |
| :-----: | :-----: | :-----: | :--------: |
| [31:26] | [25:21] | [20:16] |   [15:0]   |
| 00 0100 |    -    |    -    |     -      |

- IF : reg_src1 = rs, reg_src2 = rt, jmp_offset = offset
- ID : src1 = R[reg_src1], src2 = R[reg_src2]
- EX : zero_f = (src1 - src2 == 0)
- if (cond_jmp): PC = PC + jmp_offset
- else:          PC = PC + 4

## 6. j target
编码
|  j(6)   | instr_index(26) |
| :-----: | :-------------: |
| [31:26] |     [25:0]      |
| 00 0010 |        -        |

- jmp_target = instr_index
- PC = jmp_target
