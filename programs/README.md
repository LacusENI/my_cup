# programs

存放用于仿真的机器码程序（十六进制文本，供 `$readmemh` 装载）。

格式：每行一个 32 位十六进制数（大端），第 n 行对应指令存储器下标 `n`，
即地址 `n*4`。支持 `@地址` 语法指定起始位置，详见 Verilog `$readmemh`。

## 用法

```bash
# 只装载指令存储器 (+instr=)
uv run mycup prog programs/demo.hex

# 同时装载数据存储器 (+data=)
uv run mycup prog programs/demo.hex --data programs/data.hex

# 指定程序跑完后等待的周期数（默认 4）
uv run mycup prog programs/demo.hex --cycles 8
```

`mycup prog` 会运行 `tests/cpu/test_prog.py::test_prog_demo`：
程序路径通过 `+instr=` / `+data=` 传给 vvp，`instrm` / `datam` 中的 `initial` 据此调用 `$readmemh`。

说明：

- 程序通过 vvp 的 **plusarg** 传入，**只在仿真期有效**，不参与综合；
- 程序比存储器（2048 字）短时，`$readmemh` 会给出 "Not enough words" 警告，**属于正常现象**；
- 当前 `prog_demo_test` 的断言是针对 `demo.hex` 的（`R1=8, R2=5, R3=13`）。
  如果要跑别的程序，建议在 `tests/cpu/tb_instr.py` 里新增一个对应的 cocotb 用例，
  或者先把它当作“装载是否成功”的冒烟测试。

## demo.hex

```
addiu $1, $0, 8
addiu $2, $0, 5
addu  $3, $1, $2    # $3 = 13
```
