version: 0.2

date: 2026/10/24

## 描述

指令存储器（IMEM），默认 2048 字，组合读。

## 端口

input
- `instr_addr(32)`：读取指令的字节地址

output
- `instr(32)`：读出的指令

## 行为

- `mem_addr = instr_addr[IMEM_ADDR_W+1:2]`；
- `instr = mem[mem_addr]`；
- 容量由 `IMEM_WORDS` 决定（默认 2048 字 / 8 KiB）。

## 仿真期装载

`instrm` 内含 `initial` + `$readmemh`，可通过 vvp 的 plusarg 装载程序：

```bash
uv run mycup prog programs/demo.hex
```
