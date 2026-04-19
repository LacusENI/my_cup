version: v0.2

data: 2026/04/19

# 添加的指令
- jal
- jr

# 1. jal target
编码
| special(6) | instr_index(26) |
| :--------: | :-------------: |
|  [31:26]   |      [25:0]     |
|   00 0011  |       -         |

- IF : PC = jmp_target, jmp_target[27:0] = instr_index << 2
- ID : reg_dst = $ra
- EX :
- MEM:
- WB : R[reg_dst] = PC + 4

# 2. jr rs
编码
| special(6) |  rs(5)  |  rt(5)  |  rd(5)  | shamt(5) | funct(6) |
| :--------: | :-----: | :-----: | :-----: | :------: | :------: |
|  [31:26]   | [25:21] | [20:16] | [15:11] |  [10:6]  |   [5:0]  |
|   00 0000  |    -    |    -    |    -    |  0 0000  | 00 1000  |

- IF : PC = jmp_target
- ID : reg_src1 = rs, jmp_target = R[reg_src1]
- EX :
- MEM:
- WB :