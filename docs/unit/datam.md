version: 0.2

date: 2026/10/24

## 描述

数据存储器（DMEM），当前**仅支持整字（32 位）读写**。

> 子字访问（`sb/sh/lb/lbu/lh/lhu`）已整体延后：它涉及端序策略、字节掩码
> (`wstrb`) 与 DM 控制器设计，等内存子系统定型后再统一实现。

## 端口

input
- `clk` : 时钟
- `mem_read` : 读使能
- `mem_write` : 写使能
- `addr(32)` : 目标地址
- `w_data(32)` : 写入数据

output
- `r_data(32)` : 读出数据（`mem_read=0` 时为 0）

## 行为

- **读**：组合读；`mem_addr = addr[12:2]`，容量 2048 字（8 KiB）。
- **写**：时钟上升沿写入一个整字。
- `addr[31:13]` 当前未参与译码（地址空间回绕），后续接入总线/控制器时会重新定义。

## 仿真期装载

`datam` 内含 `initial` + `$readmemh`，可通过 vvp 的 plusarg 装载初始数据：

```bash
uv run mycup run tb_prog --prog programs/demo.hex --data programs/data.hex
```
