# 控制信号真值表（v0.3-rv32i）

当前控制表由 `rtl/control/ctrl.sv` 产生；`valid_encoding` 来自 decoder。

| instr | opcode | funct3 | funct7 | npc_op | src2_sel | reg_write | wb_sel | alu_op | mem_read | mem_write |
| :---: | :----: | :----: | :----: | :----: | :------: | :-------: | :----: | :----: | :------: | :-------: |
| add   | 0110011 | 000 | 0000000 | plus4  | rs2 | 1 | alu_out | add | 0 | 0 |
| addi  | 0010011 | 000 | x | plus4 | imm | 1 | alu_out | add | 0 | 0 |
| beq   | 1100011 | 000 | x | branch | rs2 | 0 | x | eq | 0 | 0 |
| lw    | 0000011 | 010 | x | plus4 | imm | 1 | r_data | add | 1 | 0 |
| sw    | 0100011 | 010 | x | plus4 | imm | 0 | x | add | 0 | 1 |
| jal   | 1101111 | x | x | jal | x | 1 | pc_plus4 | nop | 0 | 0 |
| jalr  | 1100111 | 000 | x | jalr | imm | 1 | pc_plus4 | add | 0 | 0 |
| illegal | 其他 | 其他 | 其他 | plus4 | rs2 | 0 | alu_out | nop | 0 | 0 |

非法指令：

```text
inst_illegal = 1
reg_write    = 0
mem_read     = 0
mem_write    = 0
alu_op       = ALU_NOP
npc_op       = NPC_PLUS4   // NPC 内部用 inst_illegal 覆盖为 hold
```

> MIPS 版本的控制表已随 `v0.3-mips` 归档；当前实现契约见
> [`docs/v0.3-rv32i/units.md`](../v0.3-rv32i/units.md)。
