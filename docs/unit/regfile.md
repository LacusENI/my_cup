version: 0.1

date: 2026/03/12

## 端口
input
- clk : 时钟信号
- reg_src1(5) : 读取寄存器名1
- reg_src2(5) : 读取寄存器名2
- reg_dst(5) : 写入寄存器名
- reg_write : 写使能信号
- wb_data : 写入数据

output
- rs1_data(32) : 读取数据1
- rs2_data(32) : 读取数据2
