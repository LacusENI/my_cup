version: 0.4.0

date: 2026/11/15

## 描述

停机仲裁单元。汇总译码级非法/SYSTEM 语义和地址故障，输出最终 `halt` / `halt_cause`。

## 端口

input
- `inst_illegal`：ctrl 判定的非法编码
- `sys_op`：`SYS_NONE` / `SYS_ECALL` / `SYS_EBREAK`
- `inst_addr_err`：取指地址未对齐
- `load_addr_err`：load 地址未对齐
- `store_addr_err`：store 地址未对齐
- `target_addr_err`：branch/jal/jalr 目标未对齐

output
- `halt`：最终停机有效位
- `halt_cause`：停机原因，仅 `halt=1` 时有效

## 优先级

```text
inst_addr_err
  > inst_illegal
  > sys_op
  > load_addr_err
  > store_addr_err
  > target_addr_err
```

没有故障时 `halt=0`，`halt_cause` 不参与架构判断。
