version: 0.2

date: 2026/10/24

## 描述

计算下一条指令的 PC。根据 `npc_op` 选择四种来源：

| `npc_op` | 含义 | `next_pc` |
| :-- | :-- | :-- |
| `NPC_OP_PLUS4` | 顺序执行 | `curr_pc + 4` |
| `NPC_OP_BRANCH` | 条件分支 | `cond_jmp ? curr_pc + (sign_ext(jmp_offset) << 2) : curr_pc + 4` |
| `NPC_OP_DIRECT` | `j` / `jal` | `{curr_pc[31:28], jmp_target, 2'b00}` |
| `NPC_OP_RA` | `jr` | `jmp_reg` |

## 端口

input
- `curr_pc(32)`：当前 PC
- `npc_op(npc_op_t)`：下一 PC 来源
- `cond_jmp`：分支条件是否成立
- `jmp_target(26)`：直接跳转的 26 位目标
- `jmp_offset(16)`：分支偏移（单位：指令字）
- `jmp_reg(32)`：寄存器跳转目标（`jr` 的 `rs1`）

output
- `pc_plus4(32)`：`curr_pc + 4`
- `next_pc(32)`：下一条指令地址

## 说明

- 分支偏移在内部左移 2 位，变成字节偏移；
- 当前实现的分支基址是 **当前 PC**（不是 MIPS 的 PC+4）；
- `jmp_reg` 旧名 `ra`，容易和 `jal` 的 `$ra` 混淆，已改名。
