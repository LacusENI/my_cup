version: 0.3-rv32i

date: 2026/11/02

## 描述

计算下一条指令的 PC。根据 `npc_op` 选择四种来源：

| `npc_op`     | 含义     | `next_pc`             |
| :----------- | :------- | :-------------------- |
| `NPC_PLUS4`  | 顺序执行 | `inst_pc + 4`         |
| `NPC_BRANCH` | 条件分支 | `branch_taken ? inst_pc + pc_offset : inst_pc + 4` |
| `NPC_JAL`    | `jal`    | `inst_pc + pc_offset` |
| `NPC_JALR`   | `jalr`   | `jalr_target & 32'hFFFF_FFFE` |

## 端口

input
- `inst_pc(32)`：当前指令的 PC
- `npc_op`
- `branch_taken`：branch 分支是否跳转
- `jalr_target(32)`：jalr 指令的寄存器目标（ALU 的 `rs1 + imm`）
- `pc_offset(32)`：跳转偏移（branch 或 jal 使用，字节偏移）
- `inst_illegal`：指令非法；为 1 时保持 PC

output
- `pc_plus4(32)`：`inst_pc + 4`
- `next_pc(32)`：下一条指令地址

## 说明

- `pc_offset` 已在 decoder 中完成符号扩展，bit0=0；NPC 不再左移。
- `jalr_target` 由 ALU 计算，NPC 清除 bit0。
- `inst_illegal` 优先级最高：非法指令时 `next_pc = inst_pc`。
- 仿真断言：`jalr_target[1]`、branch/jal 目标 bit1 必须为 0。
