version: 0.3-rv32i

date: 2026/11/02

## 描述

指令存储器（IMEM），默认 2048 字，组合读。

## 端口

input
- `inst_addr(32)`：读取指令的字节地址

output
- `inst(32)`：读出的指令

## 行为

- `mem_addr = inst_addr[IMEM_ADDR_W+1:2]`；
- `inst = mem[mem_addr]`；
- 容量由 `IMEM_WORDS` 决定（默认 2048 字 / 8 KiB）；
- 当前没有压缩指令，取指固定 32 位。

## 断言

- `inst_addr[1:0]` 必须为 0（仿真断言）。

## 仿真期装载

`instm` 内含 `initial` + `$readmemh`，可通过 vvp 的 plusarg 装载程序：

```bash
uv run mycup prog programs/demo.hex
```
