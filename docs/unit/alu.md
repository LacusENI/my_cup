version: 0.2

date: 2026/10/24

## 描述

算术逻辑单元。当前只实现加法与减法；逻辑、移位、比较等操作随 ISA 演进再补。

## 端口

input
- `alu_src1(32)`：操作数 1
- `alu_src2(32)`：操作数 2
- `alu_op(alu_op_t)`：操作码

output
- `alu_out(32)`：运算结果
- `zero_f`：结果为零
- `neg_f`：结果为负（当前恒 0，TODO）
- `overflow_f`：结果溢出（当前恒 0，TODO）
- `carry_f`：进位为 1（当前恒 0，TODO）

## 操作码

| 操作 | 编码 |
| :-- | :-- |
| `ALU_OP_ADD` | `4'b0001` |
| `ALU_OP_SUB` | `4'b0010` |

> 其余操作（AND/OR/XOR/SLL/SRL/SRA/SLT/SLTU 等）待实现。

## 行为

- `always_comb` + `unique case`；未定义操作输出 0；
- `zero_f = (alu_out == 0)`。
