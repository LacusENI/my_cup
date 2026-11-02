version: 0.3-rv32i

date: 2026/11/02

## 描述

算术逻辑单元。v0.3-rv32i 只实现加法、相等比较和空操作。

## 端口

input
- `alu_src1(32)`：操作数 1
- `alu_src2(32)`：操作数 2
- `alu_op(alu_op_t)`：操作码

output
- `alu_out(32)`：运算结果
- `cmp_result`：比较结果（1 位）

## 操作码

| 操作 | 编码 | 行为 |
| :-- | :-- | :-- |
| `ALU_NOP` | `2'b00` | `alu_out=0`，`cmp_result=0` |
| `ALU_ADD` | `2'b01` | `alu_out = alu_src1 + alu_src2` |
| `ALU_EQ` | `2'b10` | `cmp_result = (alu_src1 == alu_src2)`，`alu_out=0` |

## 行为

- `always_comb` + `unique case`；未定义操作输出 0；
- 不产生 `zero_f/neg_f/overflow_f/carry_f` 等标志；
- 分支条件在顶层组合：`branch_taken = cmp_result && (npc_op == NPC_BRANCH)`；
- `cmp_result` 仅在 `ALU_EQ` 时可能为 1，`ALU_ADD` / `ALU_NOP` 时为 0。
