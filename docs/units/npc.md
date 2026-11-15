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
- `pc_offset(32)`：PC 相对偏移（branch / jal / auipc 使用，字节偏移）

output
- `pc_plus4(32)`：`inst_pc + 4`
- `pc_plus_imm(32)`：`inst_pc + pc_offset`，同时供 `auipc` 写回使用
- `target_addr_err`：branch/jal/jalr 目标未对齐标志
- `next_pc(32)`：下一条指令地址

## 说明

- `pc_offset` 已在 decoder 中完成符号扩展，bit0=0；NPC 不再左移。
- `jalr_target` 由 ALU 计算，NPC 清除 bit0。
- NPC 不处理停机；停机时由 `pc.stall` 保持 `curr_pc`。
- `jalr_target[1]` 或 branch/jal 目标 bit1 非零时置 `target_addr_err`，由 `cpu_top` 统一仲裁。
