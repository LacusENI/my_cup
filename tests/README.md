# Python 验证（cocotb + pytest）

项目的验证现在**只有这一条链路**：cocotb 写测试内容，pytest 负责收集和报告。
旧的 HDL TB 与 `sim/tb`、`lib/vtest.vh` 已经全部移除。

## 快速开始

```bash
uv sync            # 首次：创建 .venv，安装 cocotb / pytest
uv run mycup test  # 跑全部 50 个用例
uv run pytest -v   # 同上（直接调 pytest）
```

依赖只追踪 Python 侧；`iverilog` / `verilator` 仍是系统依赖。

## 目录结构

```
tests/
├── conftest.py        # fixture：编译 DUT + run_cocotb_case
├── cocotb_utils.py    # 时钟 / 复位 / 等待 + CPU 顶层共享访问器
├── rtl_consts.py      # 从 cpu_pkg.sv 解析常量 / struct 布局
├── mips_asm.py        # MIPS 子集指令编码器（不再手写机器码）
├── test_rtl_consts.py # 常量 / struct 布局解析器自检
├── test_asm.py        # 编码器自检
├── tb_alu.py          # cocotb 用例 + AluDut 契约
├── test_alu.py        # pytest 入口
├── tb_ctrl.py         # cocotb 用例 + CtrlDut 契约
├── test_ctrl.py
├── tb_datam.py        # cocotb 用例 + DatamDut 契约
├── test_datam.py
├── tb_npc.py          # cocotb 用例 + NpcDut 契约
├── test_npc.py
├── tb_regfile.py      # cocotb 用例 + RegfileDut 契约
├── test_regfile.py
├── tb_pipe_regs.py    # cocotb 用例 + 四个流水线寄存器的契约
├── test_pipe_regs.py
├── tb_instr.py        # ISA 级：单指令 + cpu_top 契约
├── test_instr.py
├── tb_prog.py         # program 级：$readmemh 程序装载
└── test_prog.py
```

每个**模块级** `tb_*.py`（`tb_alu` / `tb_ctrl` / ... / `tb_instr`）里都自带：

- 本模块的 `Protocol`（例如 `AluDut`）；
- `REQUIRED_FIELDS`（测试依赖的字段列表）；
- 一个 `contract_test`，在仿真里确认这些字段还在。

`tb_prog.py` 是 program 级冒烟测试，不是模块 tb，所以复用 `cocotb_utils` 里的 CPU 访问器。

命名约定：

- `tb_*.py`：**cocotb 测试内容**，由仿真器在 Python 进程里加载，pytest 不会直接收集；
- `test_*.py`：**pytest 入口**，负责调用 `runner.test()`，只做“选择和报告”。

## 覆盖范围

| 测试文件 | 覆盖内容 | 用例数 |
| :-- | :-- | :-- |
| `test_alu.py` | 加法、减法、zero 标志、alu 契约 | 3 |
| `test_ctrl.py` | 8 条指令的控制信号、ctrl 契约 | 9 |
| `test_datam.py` | 整字读写、写禁用、读禁用、datam 契约 | 4 |
| `test_npc.py` | plus4 / 分支 / 回跳 / 直接跳 / jr、npc 契约 | 7 |
| `test_regfile.py` | 读写、`$0`、双读端口、写禁用、regfile 契约 | 5 |
| `test_pipe_regs.py` | IF/ID、ID/EX、EX/MEM、MEM/WB 的行为 + 契约 | 8 |
| `test_asm.py` | MIPS 指令编码器自检（已知机器码） | 1 |
| `test_instr.py` | 单指令 ISA + cpu_top 契约 | 11 |
| `test_prog.py` | 程序装载（`$readmemh`） | 1 |
| `test_rtl_consts.py` | `cpu_pkg.sv` 常量 / struct 布局解析自检 | 1 |

合计 **50 个用例**。

> 流水线寄存器用 `struct packed`（`if_id_t` / `id_ex_t` / `ex_mem_t` / `mem_wb_t`）承载数据；
> 由于 Icarus VPI 不暴露 struct 字段，测试里把 struct 当成一个整数来读写。

## 怎么写一个新测试（3 步）

以 `npc` 为例：

### 1. 在 `conftest.py` 加一个 fixture

```python
@pytest.fixture(scope="session")
def npc_sim():
    """单元级：npc（纯组合逻辑）。"""
    return _build("npc", [PKG, RTL / "control" / "npc.sv"], "npc")
```

`_build` 会调用 `iverilog` 编译，并记录 build 目录；`session` 表示整个测试会话只编译一次。

> 如果模块用到 `cpu_pkg.sv` 里的常量，记得把 `PKG` 放在源文件列表第一位。

### 2. 写 `tb_npc.py`（cocotb 用例）

```python
from typing import Protocol

import cocotb
from cocotb_utils import Signal, assert_fields, settle
from rtl_consts import NPC_OP_PLUS4

# NpcDut 就在本文件顶部声明
class NpcDut(Protocol):
    curr_pc: Signal
    npc_op: Signal
    ...

@cocotb.test()
async def plus4_test(dut: NpcDut):
    """普通情况：PC = PC + 4。"""
    dut.curr_pc.value = 0x10
    dut.npc_op.value = NPC_OP_PLUS4   # 不手写 0b00，值来自 cpu_pkg.sv
    dut.cond_jmp.value = 0
    await settle()
    assert int(dut.next_pc.value) == 0x14
```

- `@cocotb.test()` 注册用例；
- `dut` 是 HDL 顶层句柄；
- `dut: NpcDut` 只是给 IDE / 类型检查器看的，运行时不会检查；
- `await settle()` 等组合逻辑稳定。

### 3. 写 `test_npc.py`（pytest 入口）

```python
def test_npc_plus4(npc_sim, run_cocotb_case):
    """顺序执行：PC + 4。"""
    run_cocotb_case(npc_sim, "tb_npc", "plus4_test")
```

`run_cocotb_case` 是 `conftest.py` 里的 fixture，负责启动一次仿真。

## 指令级测试怎么写

`tb_instr.py` 是 **ISA 级单指令测试**：每个用例只执行一条指令，只断言架构状态（PC / 寄存器 / 内存）：

```python
from cocotb_utils import read_pc, read_reg
from mips_asm import addu

# CpuTop 在 tb_instr.py 顶部声明（class CpuTop(CpuAccess, Protocol)）


@cocotb.test()
async def addu_test(dut: CpuTop):
    """addu $3, $1, $2：5 + 3 = 8。"""
    await run_one_instruction(
        dut,
        addu(rd=3, rs=1, rt=2),   # 编码器生成机器码，不手写 0x00221821
        registers={1: 5, 2: 3},
    )
    assert read_reg(dut, 3) == 8
    assert read_pc(dut) == 4
```

`run_one_instruction` 会：

1. 启动时钟；
2. 预置寄存器和数据内存；
3. 把机器码写入 `mem[0]`；
4. 复位，执行一条指令；
5. 进入只读阶段，之后断言 PC / 寄存器 / 内存。

> 单周期下“一条指令 = 一个上升沿”。接流水线后，这里应改为等待 `retire/commit` 信号，
> 而不是依赖固定周期数。

程序装载（`$readmemh`）是另一层，放在 `tb_prog.py` / `test_prog.py`。

## DUT 的类型注解与公开字段

cocotb 的 `dut` 是**运行时动态对象**：字段要到仿真开始后才存在，
所以不能像普通类那样加 `@dataclass` 或直接写属性类型。

项目里的做法是**把接口声明放在各自的 `tb_*.py` 里**，不在一个公共
文件里堆所有模块的字段。

例如 `tb_alu.py` 顶部：

```python
class AluDut(Protocol):
    alu_op: Signal
    alu_src1: Signal
    alu_src2: Signal
    alu_out: Signal
    zero_f: Signal

REQUIRED_FIELDS = ("alu_op", "alu_src1", "alu_src2", "alu_out", "zero_f")

@cocotb.test()
async def contract_test(dut: AluDut):
    assert_fields(dut, REQUIRED_FIELDS, "alu")
```

这样：

- 读 `tb_alu.py` 就知道 alu 测试依赖哪些字段；
- 改 alu 的端口时，只改这个文件；
- `contract_test` 会在仿真里确认字段真的存在；
- 如果字段改名/删除，失败信息会提示同步更新当前 `tb_*.py`。

每个 `tb_*.py` 都遵循同样的结构：`Protocol` + `REQUIRED_FIELDS` + `contract_test`。

> `cocotb_utils.py` 里只保留**多个测试共享**的 CPU 访问器
> （`CpuAccess` / `read_pc` / `read_reg` / `read_mem`），因为
> `tb_instr`、`tb_prog` 和 `run_program` 都要用。
> `cpu_top` 自己的 `CpuTop` 协议仍然在 `tb_instr.py` 顶部声明。

常见架构状态不直接写 `dut.u_regfile.regs[3]`，而是走访问器：

```python
assert read_reg(dut, 3) == 8
assert read_pc(dut) == 4
assert read_mem(dut, 2) == 0x1122_3344
```

这样 CPU 顶层的内部路径只出现在 `cocotb_utils.py` 一处，改名时不用满测试找。

## 常量单一来源

测试里不写 `ALU_OP_ADD = 0b0001`，而是从 `rtl/cpu_pkg.sv` 解析：

```python
from rtl_consts import ALU_OP_ADD, NPC_OP_PLUS4

dut.alu_op.value = ALU_OP_ADD
```

`rtl_consts.py` 在 import 时读取 `cpu_pkg.sv`，解析：

- enum / localparam 的数字常量；
- packed struct 的字段顺序和位宽（`struct_layout("ctrl_t")`）。

因此 `tb_ctrl.py` 不再手写 `ctrl_t` 的 `[16:15]` 这类偏移，
`mips_asm.py` 也不再手写 opcode / funct。

> 解析器只支持项目用到的简单写法；遇到不认识的表达式会直接报错，
> 不会悄悄给出错误值。

## 常用命令

```bash
uv run mycup test                                      # 全部
uv run pytest -v tests/test_instr.py                   # 单指令 ISA 测试
uv run pytest -v tests/test_instr.py::test_addu        # 单个用例
uv run pytest -v tests/test_prog.py                    # 程序装载测试
uv run mycup prog programs/demo.hex                    # 跑 hex 程序
MYCUP_WAVES=1 uv run pytest -v tests/test_instr.py     # 导出波形
```

波形路径：`build/cocotb/<toplevel>_wave/<toplevel>.fst`，可用 GTKWave 打开。

## 已验证的坑

1. **必须设 timescale**：`build(timescale=("1ns", "1ps"))`，否则 `Timer(1, "ns")` 会报精度错误。
2. **cocotb 2.x 用 `cocotb_tools.runner`**，没有 `cocotb.runner`。
3. **内部信号可直接读写**：`dut.u_regfile.regs[1].value = ...`（Icarus VPI 实测可用）；
   但项目里优先用 `cocotb_utils.py` 的访问器，避免路径散落在测试中。
4. **`ReadOnly` 阶段不能赋值**：先 `await Timer(...)` 或等到下一个 `RisingEdge`。
5. **Icarus 不支持 `'{...}` 结构体赋值模式**（仿真侧用逐字段赋值）。
6. `build()` 默认会复用已有构建；RTL 改动后如需强制重编，可传 `always=True`。
7. **组合逻辑测试用 `await settle()`**（等 1ns）；时序逻辑测试用 `await RisingEdge(clk)` + `await ReadOnly()`。
8. **未写过的寄存器是 `X`**：分支/跳转测试里，如果要断言“某条指令被跳过”，先把目标寄存器预置成 0，否则 `int(X)` 会报错。
