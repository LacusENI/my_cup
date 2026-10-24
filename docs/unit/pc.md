version: 0.2

date: 2026/10/24

## 描述

程序计数器（同步复位）。

## 端口

input
- `clk`：时钟信号
- `rst`：复位信号
- `next_pc(32)`：下一条指令地址

output
- `curr_pc(32)`：当前 PC

## 行为

```systemverilog
always_ff @(posedge clk)
    if (rst) curr_pc <= '0;
    else     curr_pc <= next_pc;
```
