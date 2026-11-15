# 控制信号真值表（当前实现）

当前控制表由 `rtl/control/ctrl.sv` 产生。decoder 只负责字段切分和立即数格式，
并输出 `opcode_err`；ctrl 在 `opcode_err=1` 时直接判为非法，不再检查其他字段。
对于已知 opcode，完整编码合法性（funct3/funct7/rd/rs1/funct12）由 ctrl 检查。
`ctrl` 只输出 `inst_illegal` 和 `sys_op`，最终 `halt` / `halt_cause` 由 `halt_unit` 生成。

| inst | opcode | funct3 | funct7 | npc_op | src2_sel | reg_write | wb_sel | alu_op | mem_read | mem_write |
| :---: | :----: | :----: | :----: | :----: | :------: | :-------: | :----: | :----: | :------: | :-------: |
| add   | 0110011 | 000 | 0000000 | plus4  | rs2 | 1 | alu_out | add | 0 | 0 |
| addi  | 0010011 | 000 | x | plus4  | imm | 1 | alu_out  | add | 0 | 0 |
| beq   | 1100011 | 000 | x | branch | rs2 | 0 | x        | eq | 0 | 0 |
| lw    | 0000011 | 010 | x | plus4  | imm | 1 | r_data   | add | 1 | 0 |
| sw    | 0100011 | 010 | x | plus4  | imm | 0 | x        | add | 0 | 1 |
| jal   | 1101111 |  x  | x | jal    | rs2 | 1 | pc_plus4 | nop | 0 | 0 |
| jalr  | 1100111 | 000 | x | jalr   | imm | 1 | pc_plus4 | add | 0 | 0 |
| lui   | 0110111 |  x  | x | plus4  | imm | 1 | imm      | nop | 0 | 0 |
| auipc | 0010111 |  x  | x | plus4  | imm | 1 | pc_plus_imm | nop | 0 | 0 |
| illegal | 其他 | 其他 | 其他 | plus4 | rs2 | 0 | alu_out | nop | 0 | 0 |

## FENCE / SYSTEM

| inst | opcode | funct3 | funct12 | inst_illegal | sys_op | 行为 |
| :---: | :----: | :----: | :----: | :--: | :-- | :-- |
| fence | 0001111 | 000 | x | 0 | `SYS_NONE` | NOP，PC+4 |
| ecall | 1110011 | 000 | 000 | 0 | `SYS_ECALL` | halt_unit 产生 `HALT_ECALL` |
| ebreak | 1110011 | 000 | 001 | 0 | `SYS_EBREAK` | halt_unit 产生 `HALT_EBREAK` |
| 非法 SYSTEM | 1110011 | 000 | 其他 | 1 | `SYS_NONE` | halt_unit 产生 `HALT_ILLEGAL_INST` |

`fence` 要求 `rd=0`、`rs1=0`；`fence.i`（funct3=001）当前不实现。
`PAUSE` 是 `fence w, 0` 的 FENCE hint，按 NOP 处理。

非法指令：

```text
inst_illegal = 1
sys_op       = SYS_NONE
reg_write    = 0
mem_read     = 0
mem_write    = 0
alu_op       = ALU_NOP
npc_op       = NPC_PLUS4   // 停机时由 pc.stall 保持 PC
```

`inst_illegal` 表示完整编码非法；`sys_op` 表示合法的系统指令语义。
两者由 `halt_unit` 映射成最终 `halt_cause`。

## 地址故障与最终 halt

`halt_unit` 汇总所有来源，优先级为：

```text
inst_addr_err
  > inst_illegal
  > sys_op
  > load_addr_err
  > store_addr_err
  > target_addr_err
```

| 来源 | halt_cause |
| :-- | :-- |
| 取指地址未对齐 / 跳转目标未对齐 | `HALT_INST_ADDR_ERR` (0) |
| 非法指令 / `ecall` / `ebreak` | `HALT_ILLEGAL_INST` / `HALT_ECALL` / `HALT_EBREAK` |
| load 地址未对齐 | `HALT_LOAD_ADDR_ERR` (4) |
| store 地址未对齐 | `HALT_STORE_ADDR_ERR` (6) |

> MIPS 版本的控制表已随 `v0.3-mips` 归档；当前实现契约见
> [`docs/units/`](../units/) 与本文。
