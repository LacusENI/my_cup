version: 0.2

date: 2026/10/24

## 描述

根据 ALU 标志和 `cond_type` 产生分支条件 `cond_jmp`。

## 端口

input
- `zero_f`：结果为零
- `neg_f`：结果为负（当前未使用）
- `overflow_f`：结果溢出（当前未使用）
- `carry_f`：进位为 1（当前未使用）
- `cond_type(cond_type_t)`：比较类型

output
- `cond_jmp`：是否满足条件

## 比较类型

| 类型 | 编码 | 当前状态 |
| :-- | :-- | :-- |
| `COND_TYPE_EQ` | `2'b00` | ✅ 已实现 |
| NE / LT / LTU | `2'b01` / `2'b10` / `2'b11` | 延后 |

## 说明

- 当前只实现相等比较；
- `neg_f/overflow_f/carry_f` 预留给未来的有符号/无符号比较。
