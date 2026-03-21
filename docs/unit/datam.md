version: 0.1

date: 2026/03/12

## 描述
数据存储器（目前支持字读写）

## 端口
input
- clk : 时钟信号
- mem_read : 读使能信号
- mem_write : 写使能信号
- addr(32) : 目标内存地址
- w_data(32) : 写入数据

output
- r_data(32) : 读取数据
