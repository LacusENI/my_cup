# 控制信号真值表（当前实现）

当前控制表由 `rtl/control/ctrl.sv` 产生；`valid_encoding` 来自 decoder。

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

非法指令：

```text
halt       = 1
halt_cause = HALT_ILLEGAL_INST (2)
reg_write  = 0
mem_read   = 0
mem_write  = 0
alu_op     = ALU_NOP
npc_op     = NPC_PLUS4   // 停机时由 pc.stall 保持 PC
```

`halt` 是译码级有效位；`halt_cause` 只在 `halt=1` 时解释。
后续地址错误等非译码来源会在 `cpu_top` 中汇总并覆盖最终 `halt_cause`。

> MIPS 版本的控制表已随 `v0.3-mips` 归档；当前实现契约见
> [`docs/units/`](../units/) 与本文。
