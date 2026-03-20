version: v0.1

date: 2026/03/12

## 描述
接受要进行比较类型和ALU计算结果的条件码，给出比较的结果。

## 端口
input
- cond_type(2) : 比较条件的类型
- zero_f : 条件码 - 结果为零
- negative_f : 条件码 - 结果为负
- overflow_f : 条件码 - 结果溢出
- carry_f : 条件码 - 进位为1

output
- cond_jmp : 是否满足条件

## 比较类型
- 相等 : 00
- 不相等 : 01
- 小于(有符号): 10
- 大于(无符号): 11