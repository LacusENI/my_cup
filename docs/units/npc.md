version: 0.3-rv32i

date: 2026/10/24

## 描述

计算下一条指令的 PC。根据 `npc_op` 选择四种来源：

| `npc_op`     | 含义     | `next_pc`             |
| :----------- | :------- | :-------------------- |
| `NPC_PLUS4`  | 顺序执行 | `inst_pc + 4`         |
| `NPC_BRANCH` | 条件分支 | `branch_taken ? inst_pc + pc_offset : inst_pc +4` |
| `NPC_JALR`   | `jalr`   | `jalr_target`         |
| `NPC_JAL`    | `jal`    | `inst_pc + pc_offset` |

## 端口

input
- `inst_pc(32)`    ：当前指令的 PC
- `npc_op`
- `branch_taken`   ：branch 分支是否跳转
- `jalr_target(32)`：jalr 指令直接跳转目标
- `pc_offset(32)`  ：跳转偏移（branch 或 jal 使用）
- `inst_illegal`   : 指令有效（无效时保持 PC）

output
- `pc_plus4(32)`：`inst_pc + 4`
- `next_pc(32)`：下一条指令地址
