# Python 验证（cocotb + pytest）

项目的验证链路：**cocotb 负责在仿真器里执行测试，pytest 负责收集、筛选和报告。**
两者通过 `tests/utils/cocotb_utils.py` 里的 `@cocotb_test` 装饰器连接。

旧的 HDL TB 与 `sim/tb`、`lib/vtest.vh` 已经全部移除。

## 快速开始

```bash
uv sync            # 首次：创建 .venv，安装 cocotb / pytest
make programs      # 汇编 programs/**/*.S
uv run mycup test  # 自动汇编程序并跑全部用例
uv run pytest -v   # 直接调 pytest（需要先 make programs）
```

依赖只追踪 Python 侧；`iverilog` / `verilator` / `llvm-mc` / `llvm-objcopy`
仍是系统依赖。

## 目录结构

```text
tests/
├── conftest.py        # fixture：编译 DUT + run_cocotb_case
├── utils/
│   ├── cocotb_utils.py  # 时钟 / 复位 / 等待 + @cocotb_test + CPU 共享访问器
│   ├── assembler.py     # llvm-mc 封装：汇编文本 -> 32 位机器码
│   └── test_asm.py      # assembler.py 的 golden / 错误用例
├── hdl/
│   ├── ctrl_probe.sv    # test-only：把 ctrl_t 摊平给 cocotb
│   └── decoder_probe.sv # test-only：把 inst_t 摊平给 cocotb
├── control/
│   ├── test_decoder.py  # decoder 字段 / 立即数 / opcode_err
│   ├── test_ctrl.py     # ctrl 合法编码 / 控制表 / halt
│   ├── test_npc.py      # npc 分支 / 跳转
│   ├── test_pc.py       # pc 更新 / 复位 / stall
│   └── test_halt_unit.py # halt 仲裁优先级
├── datapath/
│   ├── test_alu.py      # ADD / EQ / NOP
│   └── test_regfile.py  # 32x32 寄存器堆
├── memory/
│   ├── test_datam.py    # 整字数据存储器
│   └── test_instm.py    # 指令存储器 / inst_addr_err
└── cpu/
    ├── test_inst.py     # RV32I 单指令 ISA + cpu_top 契约
    └── test_prog.py     # program 级：$readmemh 程序装载
```

目录按 RTL 职责划分：

- `control/`：`decoder`、`ctrl`、`npc`
- `datapath/`：`alu`、`regfile`
- `memory/`：`datam`
- `cpu/`：`cpu_top` 级测试（ISA / program）
- `utils/`：测试工具，不是 DUT 测试

## 一个文件里同时写 cocotb 和 pytest

每个模块级测试文件都自带：

- 本模块的 `Protocol`（例如 `AluDut`）；
- `REQUIRED_FIELDS`（测试依赖的字段列表）；
- 一个 `test_contract`，在仿真里确认这些字段还在。

测试函数长这样：

```python
from utils.cocotb_utils import cocotb_test, settle

SIM = "alu_sim"   # conftest.py 里的 fixture 名


@cocotb_test(dut=SIM)
async def test_alu_add(dut):
    """ADD：5 + 3 = 8。"""
    dut.alu_op.value = 1
    dut.alu_src1.value = 5
    dut.alu_src2.value = 3
    await settle()

    assert int(dut.alu_out.value) == 8
```

`@cocotb_test` 同时做两件事：

1. 用 `cocotb.test()` 把 async 函数注册成 cocotb test；
2. 返回一个普通同步 wrapper，让 pytest 把它当成普通 `test_*` 用例收集。

pytest 执行 wrapper 时，会调用 `run_cocotb_case` 启动一次仿真；仿真器里的
cocotb 再执行原来的 async 函数。详细注释见
[`tests/utils/cocotb_utils.py`](utils/cocotb_utils.py) 的 `cocotb_test`。

> **为什么不能只写 `@cocotb.test()`？**
> 它返回的是 `TestGenerator` 对象，pytest 默认不会收集；而且断言发生在
> 仿真器进程里，pytest 进程拿不到原始 `AssertionError`。
> `@cocotb_test` 负责把这两层接起来。

命名约定：

- 测试文件统一用 `test_*.py`；
- 测试函数统一用 `test_` 前缀；
- 单 DUT 文件在顶部写 `SIM = "<fixture 名>"`，每个测试用 `@cocotb_test(dut=SIM)`；
- 一个文件里有多个 DUT 时，每个测试单独写 `@cocotb_test(dut="...")`；
- 需要 plusargs 的测试给 `@cocotb_test(..., plusargs=...)`，传列表或返回列表的函数。

## 覆盖范围

| 测试文件 | 覆盖内容 | 用例数 |
| :-- | :-- | :-- |
| `control/test_decoder.py` | RV32I 字段切分、I/S/B/J/U 立即数、opcode_err | 8 |
| `control/test_ctrl.py` | 12 条指令控制表、合法编码、fence/ecall/ebreak | 18 |
| `control/test_npc.py` | PLUS4 / BRANCH / JAL / JALR / target_addr_err | 8 |
| `control/test_pc.py` | PC 更新、复位、stall 保持 | 3 |
| `control/test_halt_unit.py` | halt 来源与优先级仲裁 | 10 |
| `datapath/test_alu.py` | ADD / EQ / NOP、32 位回绕 | 6 |
| `datapath/test_regfile.py` | 读写、x0、双读端口、写禁用 | 5 |
| `memory/test_datam.py` | 整字读写、写/读禁用、addr_err | 5 |
| `memory/test_instm.py` | 取指与 inst_addr_err | 2 |
| `utils/test_asm.py` | llvm-mc 封装、golden 和错误输入检查 | 20 |
| `cpu/test_inst.py` | 12 条单指令 ISA + SYSTEM/地址故障 + 契约 | 32 |
| `cpu/test_prog.py` | 程序装载（`$readmemh`） | 1 |

合计 **118 个用例**。

## 怎么写一个新测试

以 `npc` 为例。

### 1. 在 `conftest.py` 加一个 fixture

```python
@pytest.fixture(scope="session")
def npc_sim():
    """单元级：npc（纯组合逻辑）。"""
    return _build("npc", [PKG, RTL / "control" / "npc.sv"], "npc", "control")
```

`_build` 会调用 `iverilog` 编译，并记录 build 目录；`session` 表示整个测试会话只编译一次。
最后一个参数是 `module_prefix`，表示测试模块所在的子目录（这里是 `tests/control/`）。

> 如果模块用到 `cpu_pkg.sv` 里的常量，记得把 `PKG` 放在源文件列表第一位。

### 2. 直接在 `tests/control/test_npc.py` 写用例

```python
from typing import Protocol

from utils.cocotb_utils import Signal, cocotb_test, settle

SIM = "npc_sim"


class NpcDut(Protocol):
    inst_pc: Signal
    npc_op: Signal
    branch_taken: Signal
    pc_offset: Signal
    jalr_target: Signal
    pc_plus4: Signal
    pc_plus_imm: Signal
    next_pc: Signal


@cocotb_test(dut=SIM)
async def test_npc_plus4(dut: NpcDut):
    """普通情况：PC + 4。"""
    dut.inst_pc.value = 0x10
    dut.npc_op.value = 0
    dut.branch_taken.value = 0
    dut.pc_offset.value = 0
    dut.jalr_target.value = 0
    await settle()
    assert int(dut.next_pc.value) == 0x14
```

不需要再建 `tb_npc.py`，也不需要在另一个文件里写 pytest wrapper。

### 3. 运行

```bash
uv run pytest -v tests/control/test_npc.py::test_npc_plus4
```

## 指令级测试怎么写

`cpu/test_inst.py` 是 **ISA 级单指令测试**：每个用例只执行一条指令，只断言架构状态（PC / 寄存器 / 内存）：

```python
from utils.assembler import assemble
from utils.cocotb_utils import cocotb_test, read_pc, read_reg, run_one_instruction

SIM = "cpu_sim"


@cocotb_test(dut=SIM)
async def test_add(dut):
    """add x3, x1, x2：5 + 3 = 8。"""
    await run_one_instruction(
        dut,
        assemble("add x3, x1, x2"),   # llvm-mc 汇编成机器码
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

程序装载（`$readmemh`）是另一层，放在 `tests/cpu/test_prog.py`。
它用 `@cocotb_test(dut="cpu_sim", plusargs=_plusargs)` 把 `+inst=` / `+data=`
传给仿真器命令行。

## DUT 的类型注解与公开字段

cocotb 的 `dut` 是**运行时动态对象**：字段要到仿真开始后才存在，
所以不能像普通类那样加 `@dataclass` 或直接写属性类型。

项目里的做法是**把接口声明放在各自的测试文件里**，不在一个公共文件里堆所有模块的字段。

例如 `test_alu.py` 顶部：

```python
class AluDut(Protocol):
    alu_op: Signal
    alu_src1: Signal
    alu_src2: Signal
    alu_out: Signal
    cmp_result: Signal


REQUIRED_FIELDS = ("alu_op", "alu_src1", "alu_src2", "alu_out", "cmp_result")


@cocotb_test(dut=SIM)
async def test_contract(dut: AluDut):
    assert_fields(dut, REQUIRED_FIELDS, "alu")
```

这样：

- 读 `test_alu.py` 就知道 alu 测试依赖哪些字段；
- 改 alu 的端口时，只改这个文件；
- `test_contract` 会在仿真里确认字段真的存在；
- 如果字段改名/删除，失败信息会提示同步更新当前测试文件。

每个模块级测试文件都遵循同样的结构：`Protocol` + `REQUIRED_FIELDS` + `test_contract`。

> `tests/utils/cocotb_utils.py` 里保留**多个测试共享**的 CPU 访问器
> （`CpuAccess` / `read_pc` / `read_reg` / `read_mem`），因为
> `test_inst`、`test_prog` 和 `run_program` 都要用。
> `cpu_top` 自己的 `CpuTop` 协议仍然在 `tests/cpu/test_inst.py` 顶部声明。

常见架构状态不直接写 `dut.u_regfile.regs[3]`，而是走访问器：

```python
assert read_reg(dut, 3) == 8
assert read_pc(dut) == 4
assert read_mem(dut, 2) == 0x1122_3344
```

这样 CPU 顶层的内部路径只出现在 `tests/utils/cocotb_utils.py` 一处，改名时不用满测试找。

## 常量与 ISA 编码

控制枚举仍然来自 RTL：

| 常量 | 来源 | 生成文件 |
| :-- | :-- | :-- |
| 控制枚举（`ALU_*` / `NPC_*` / `WB_SEL_*` / `SRC2_SEL_*`） | `rtl/cpu_pkg.sv` | `tests/utils/cpu_pkg.py` |

测试里直接 import：

```python
from utils.cpu_pkg import ALU_ADD, ALU_EQ, NPC_BRANCH
```

不要手写 `ALU_ADD = 1` 这类数值。RTL 改了枚举顺序或值以后，运行：

```bash
make code-gen
```

CI 会执行 `make code-gen-check`，如果生成文件不是最新就会失败。

ISA 编码不再由 Python 生成。单指令测试统一写汇编文本：

```python
from utils.assembler import assemble

word = assemble("add x3, x1, x2")
```

`tests/utils/assembler.py` 调用 `llvm-mc -triple=riscv32`，只接受一条
32 位指令。因此 `llvm-mc` 是系统依赖，`make doctor` 会检查它。

`test_ctrl.py` 不手写 `ctrl_t` 的字段位偏移，而是通过
`tests/hdl/ctrl_probe.sv` 把字段摊平后直接读取：

```python
assert int(dut.alu_op.value) == ALU_ADD
```

这样常量数值仍然是测试契约，但 struct 布局由 SV wrapper 在编译期检查。

## 常用命令

```bash
uv run mycup test                                      # 全部
uv run pytest -v tests/cpu/test_inst.py               # 单指令 ISA 测试
uv run pytest -v tests/cpu/test_inst.py::test_add     # 单个用例
uv run pytest -v tests/cpu/test_prog.py                # 程序装载测试
make programs                                         # 汇编 programs/**/*.S
uv run mycup prog programs/demo.S                     # 汇编并运行程序
MYCUP_WAVES=1 uv run pytest -v tests/cpu/test_inst.py # 导出波形
```

波形路径：`build/cocotb/<toplevel>_wave/<toplevel>.fst`，可用 GTKWave 打开。

## 已验证的坑

1. **必须设 timescale**：`build(timescale=("1ns", "1ps"))`，否则 `Timer(1, "ns")` 会报精度错误。
2. **cocotb 2.x 用 `cocotb_tools.runner`**，没有 `cocotb.runner`。
3. **内部信号可直接读写**：`dut.u_regfile.regs[1].value = ...`（Icarus VPI 实测可用）；
   但项目里优先用 `tests/utils/cocotb_utils.py` 的访问器，避免路径散落在测试中。
4. **`ReadOnly` 阶段不能赋值**：先 `await Timer(...)` 或等到下一个 `RisingEdge`。
5. **Icarus 不支持 `'{...}` 结构体赋值模式**（仿真侧用逐字段赋值）。
6. `build()` 默认会复用已有构建；RTL 改动后如需强制重编，可传 `always=True`。
7. **组合逻辑测试用 `await settle()`**（等 1ns）；时序逻辑测试用 `await RisingEdge(clk)` + `await ReadOnly()`。
8. **未写过的寄存器是 `X`**：`read_reg` 对 x0 直接返回 0，但其他寄存器测试前应先预置。
9. **`@cocotb_test` 的 wrapper 不要用 `functools.wraps`**：它会设置 `__wrapped__`，
   pytest 会看到原函数的 `dut` 参数，而不是 wrapper 的 `request`。
10. **pytest marker 建议写在 `@cocotb_test` 外层**：例如 `@pytest.mark.xfail`。
    装饰器也会复制内层 `pytestmark`，两种顺序都能工作，但外层最直观。
11. **cocotb 失败时 pytest 看到的是 XML 里的断言信息**：
    `tests/conftest.py` 会读取 `results.xml`，把真正的 `AssertionError` 文本交给
    `pytest.fail()`；如果 XML 不存在，才会退回 `SystemExit`。
