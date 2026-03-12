version: v0.1

date: 2026/03/12

## 描述
计算下一指令开始时的PC值。
分为正常递增、直接跳转（直接跳转到目标）、根据条件跳转指定的偏移量（条件跳转）

## 端口
input
- jmp : 是否使用直接跳转
- cond_jmp : 是否使用条件跳转
- jmp_target : 若使用直接跳转，跳转的目标地址
- jmp_offset : 若使用条件跳转，跳转的地址偏移量
- curr_pc : 当前的PC值

output
- next_pc : 下次的PC值