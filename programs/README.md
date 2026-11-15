# programs

存放 RV32I 汇编程序。`.S` 是程序接口；`.o` / `.bin` / `.hex` 是
`build/programs/` 下的中间产物，不提交到仓库。

## 构建

```bash
# 汇编 programs/**/*.S，并生成 build/programs/programs.json
uv run mycup build-programs

# 汇编单个文件
uv run mycup asm programs/demo.S
```

单个程序的产物：

```text
programs/demo.S
  -> build/programs/demo.o
  -> build/programs/demo.bin
  -> build/programs/demo.hex
```

也可以使用：

```bash
make programs
make asm FILE=programs/demo.S
```

## 运行

```bash
# 直接给 .S，mycup 会先汇编
uv run mycup prog programs/demo.S

# 也可以直接给已经生成的 hex
uv run mycup prog build/programs/demo.hex

# 同时装载数据存储器
uv run mycup prog programs/demo.S --data programs/data.hex
```

`mycup prog` 会把最终 hex 路径写入 `MYCUP_PROG`，然后运行
`tests/cpu/test_prog.py::test_prog_demo`。

## 外部 hex

已有外部程序时，可以绕过表直接注入：

```bash
MYCUP_PROG=/tmp/foo.hex uv run pytest tests/cpu/test_prog.py
```

`test_prog.py` 默认声明 `programs/demo.S`，构建后通过
`build/programs/programs.json` 查表得到对应 hex。

## demo.S

```asm
_start:
    addi x1, x0, 8
    addi x2, x0, 5
    add  x3, x1, x2
    sw   x3, 0(x0)
    lw   x4, 0(x0)

    beq  x4, x3, after_skip
    addi x5, x0, 99
after_skip:
    lui  x6, 0x12345
    auipc x7, 0
    fence iorw, iorw
    ecall
```

程序必须以 `ecall` 或 `ebreak` 结束；`run_program` 会等待 `halt=1`。

## 当前限制

当前构建流程只处理单个 `.text` 段，不依赖 linker：

```text
llvm-mc -> .o -> llvm-objcopy -> .bin -> .hex
```

如果以后需要 `.data`、多文件链接或外部符号，再引入 `lld` 和 linker script。
