version: 0.3-rv32i

date: 2026/11/02

## 描述

指令存储器（IMEM），默认 2048 字，组合读。

## 端口

input
- `inst_addr(32)`：读取指令的字节地址

output
- `inst(32)`：读出的指令
- `inst_addr_err`：取指地址未对齐标志

## 行为

- `mem_addr = inst_addr[IMEM_ADDR_W+1:2]`；
- `inst = mem[mem_addr]`；
- 容量由 `IMEM_WORDS` 决定（默认 2048 字 / 8 KiB）；
- 当前没有压缩指令，取指固定 32 位。

## 地址错误

- `inst_addr[1:0] != 0` 时置 `inst_addr_err`；
- 模块内部不 `$fatal`，停机由 `cpu_top` 统一处理。

## 仿真期装载

`instm` 内含 `initial` + `$readmemh`，可通过 vvp 的 plusarg 装载程序：

```bash
uv run mycup prog programs/demo.S
```
