# programs

存放用于仿真的机器码程序（十六进制文本，供 `$readmemh` 装载）。

格式：每行一个 32 位十六进制数（大端），第 n 行对应指令存储器下标 `n`，
即地址 `n*4`。支持 `@地址` 语法指定起始位置，详见 Verilog `$readmemh`。

## 用法

```bash
# 装载指令存储器 (+instr=)
make run-tb_prog PROG=programs/demo.hex

# 装载数据存储器 (+data=)
make run-tb_prog PROG=programs/demo.hex DATA=programs/data.hex
```

- 程序通过 vvp 的 **plusarg** 传入，**只在仿真期有效**，不参与综合。
- 若未传 `+instr=`，`tb_prog` 会打印 `[ SKIP ]` 并正常退出，因此 `make all` 不受影响。
- 程序比存储器（2048 字）短时，`$readmemh` 会给出 "Not enough words" 警告，**属于正常现象**。

## demo.hex

```
addiu $1, $0, 8
addiu $2, $0, 5
addu  $3, $1, $2    # $3 = 13
```
