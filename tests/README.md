# Python 验证（cocotb + pytest）

项目的验证链路：cocotb 写测试内容，pytest 负责收集和报告。
旧的 HDL TB 与 `sim/tb`、`lib/vtest.vh` 已经全部移除。

## 快速开始

```bash
uv sync            # 首次：创建 .venv，安装 cocotb / pytest
uv run mycup test  # 跑全部用例
uv run pytest -v   # 同上（直接调 pytest）
```

依赖只追踪 Python 侧；`iverilog` / `verilator` 仍是系统依赖。

## 覆盖率

```bash
make install-verilator  # 一次性：项目本地 Verilator 5.054
make cov                # Verilator line coverage
uv run mycup cov --toggle
```

`mycup cov` 会设置 `MYCUP_SIM=verilator` / `MYCUP_COVERAGE=1`，跑完所有 cocotb 用例后
把每个测试的 `coverage.dat` 汇总到 `logs/coverage/`。未覆盖行位于
`logs/coverage/annotated/`，以 `%000000` 开头。

> 覆盖率需要 Verilator >= 5.054；默认的 Icarus 测试流程不受影响。
> `mycup cov` 会优先使用 `.tools/verilator-conda/` 下的本地工具。

## 目录结构

```
tests/
├── conftest.py        # fixture：编译 DUT + run_cocotb_case
├── utils/
│   ├── cocotb_utils.py  # 时钟 / 复位 / 等待 + CPU 顶层共享访问器
│   ├── riscv_asm.py     # RV32I 7 条指令编码器
│   ├── mips_asm.py      # MIPS 历史编码器（保留参考）
│   └── test_asm.py      # RV32I 编码器自检
├── hdl/
│   ├── ctrl_probe.sv    # test-only：把 ctrl_t 摊平给 cocotb
│   └── decoder_probe.sv # test-only：把 inst_t 摊平给 cocotb
├── control/
│   ├── tb_decoder.py    # decoder 字段 / 立即数 / 合法编码
│   ├── tb_ctrl.py       # ctrl 控制表 / 非法指令
│   ├── tb_npc.py        # npc 分支 / 跳转 / illegal hold
│   └── test_*.py
├── datapath/
│   ├── tb_alu.py        # ADD / EQ / NOP
│   ├── tb_regfile.py    # 32x32 寄存器堆
│   └── test_*.py
├── memory/
│   ├── tb_datam.py      # 整字数据存储器
│   └── test_datam.py
├── pipe/
│   ├── tb_pipe_regs.py  # 四个流水线寄存器（尚未接入 top）
│   └── test_pipe_regs.py
└── cpu/
    ├── tb_inst.py      # RV32I 单指令 ISA + cpu_top 契约
    ├── test_inst.py
    ├── tb_prog.py       # program 级：$readmemh 程序装载
    └── test_prog.py
```

目录按 RTL 职责划分：

- `control/`：`decoder`、`ctrl`、`npc`
- `datapath/`：`alu`、`regfile`
- `memory/`：`datam`
- `pipe/`：流水线级间寄存器
- `cpu/`：`cpu_top` 级测试（ISA / program）
- `utils/`：测试工具，不是 DUT 测试

每个**模块级** `tb_*.py`（`tb_alu` / `tb_ctrl` / ... / `tb_inst`）里都自带：

- 本模块的 `Protocol`（例如 `AluDut`）；
- `REQUIRED_FIELDS`（测试依赖的字段列表）；
- 一个 `contract_test`，在仿真里确认这些字段还在。

命名约定：

- `tb_*.py`：**cocotb 测试内容**，由仿真器在 Python 进程里加载，pytest 不会直接收集；
- `test_*.py`：**pytest 入口**，负责调用 `runner.test()`，只做“选择和报告”。

> `tests/hdl/ctrl_probe.sv` 和 `decoder_probe.sv` 是 **test-only probe**：
> 它们实例化 RTL，把 packed struct 字段摊平成普通端口，避免 Python 里手写位偏移。
> 它们不参与综合，也不在 `.verilator/verilator.f` 的 lint 清单里。

## 覆盖范围

| 测试文件 | 覆盖内容 | 用例数 |
| :-- | :-- | :-- |
| `control/test_decoder.py` | RV32I 字段切分、I/S/B/J 立即数、非法编码 | 10 |
| `control/test_ctrl.py` | 7 条指令控制表、非法指令安全控制 | 9 |
| `control/test_npc.py` | PLUS4 / BRANCH / JAL / JALR / illegal hold | 8 |
| `datapath/test_alu.py` | ADD / EQ / NOP、32 位回绕 | 6 |
| `datapath/test_regfile.py` | 读写、x0、双读端口、写禁用 | 5 |
| `memory/test_datam.py` | 整字读写、写禁用、读禁用 | 4 |
| `pipe/test_pipe_regs.py` | 四个流水线寄存器的行为 + 契约 | 8 |
| `utils/test_asm.py` | RV32I 编码器、范围和伪指令检查 | 25 |
| `cpu/test_inst.py` | 7 条单指令 ISA + 复位写抑制 + 非法停止 + 契约 | 19 |
| `cpu/test_prog.py` | 程序装载（`$readmemh`） | 1 |

合计 **95 个用例**。

> 流水线寄存器用 `struct packed`（`if_id_t` / `id_ex_t` / `ex_mem_t` / `mem_wb_t`）承载数据；
> 由于 Icarus VPI 不暴露 struct 字段，测试里把 struct 当成一个整数来读写。

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

### 2. 写 `tests/control/tb_npc.py`（cocotb 用例）

```python
from typing import Protocol

import cocotb
from utils.cocotb_utils import Signal, assert_fields, settle

NPC_PLUS4 = 0

class NpcDut(Protocol):
    inst_pc: Signal
    npc_op: Signal
    branch_taken: Signal
    pc_offset: Signal
    jalr_target: Signal
    inst_illegal: Signal
    pc_plus4: Signal
    next_pc: Signal

@cocotb.test()
async def plus4_test(dut: NpcDut):
    """普通情况：PC + 4。"""
    dut.inst_pc.value = 0x10
    dut.npc_op.value = NPC_PLUS4
    dut.branch_taken.value = 0
    dut.pc_offset.value = 0
    dut.jalr_target.value = 0
    dut.inst_illegal.value = 0
    await settle()
    assert int(dut.next_pc.value) == 0x14
```

### 3. 写 `tests/control/test_npc.py`（pytest 入口）

```python
def test_npc_plus4(npc_sim, run_cocotb_case):
    """顺序执行：PC + 4。"""
    run_cocotb_case(npc_sim, "tb_npc", "plus4_test")
```

`run_cocotb_case` 是 `conftest.py` 里的 fixture，负责启动一次仿真。
它会根据 fixture 的 `module_prefix` 自动补全模块路径：

```
"tb_npc" + "control" -> "control.tb_npc"
```

## 指令级测试怎么写

`tb_inst.py` 是 **ISA 级单指令测试**：每个用例只执行一条指令，只断言架构状态（PC / 寄存器 / 内存）：

```python
from utils.cocotb_utils import read_pc, read_reg
from utils.riscv_asm import add

@cocotb.test()
async def add_test(dut: CpuTop):
    """add x3, x1, x2：5 + 3 = 8。"""
    await run_one_instuction(
        dut,
        add(rd=3, rs1=1, rs2=2),   # 编码器生成机器码
        registers={1: 5, 2: 3},
    )
    assert read_reg(dut, 3) == 8
    assert read_pc(dut) == 4
```

`run_one_instuction` 会：

1. 启动时钟；
2. 预置寄存器和数据内存；
3. 把机器码写入 `mem[0]`；
4. 复位，执行一条指令；
5. 进入只读阶段，之后断言 PC / 寄存器 / 内存。

> 单周期下“一条指令 = 一个上升沿”。接流水线后，这里应改为等待 `retire/commit` 信号，
> 而不是依赖固定周期数。

程序装载（`$readmemh`）是另一层，放在 `tests/cpu/tb_prog.py` / `tests/cpu/test_prog.py`。

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
    cmp_result: Signal

REQUIRED_FIELDS = ("alu_op", "alu_src1", "alu_src2", "alu_out", "cmp_result")

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

> `tests/utils/cocotb_utils.py` 里只保留**多个测试共享**的 CPU 访问器
> （`CpuAccess` / `read_pc` / `read_reg` / `read_mem`），因为
> `tb_inst`、`tb_prog` 和 `run_program` 都要用。
> `cpu_top` 自己的 `CpuTop` 协议仍然在 `tests/cpu/tb_inst.py` 顶部声明。

常见架构状态不直接写 `dut.u_regfile.regs[3]`，而是走访问器：

```python
assert read_reg(dut, 3) == 8
assert read_pc(dut) == 4
assert read_mem(dut, 2) == 0x1122_3344
```

这样 CPU 顶层的内部路径只出现在 `tests/utils/cocotb_utils.py` 一处，改名时不用满测试找。

## 常量是对外契约

测试里直接写死控制值，例如：

```python
ALU_ADD = 1
ALU_EQ = 2
NPC_BRANCH = 1
```

`tests/utils/riscv_asm.py` 里也直接写死 RV32I opcode / funct3。

`tb_ctrl.py` 不手写 `ctrl_t` 的字段位偏移，而是通过
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
uv run mycup prog programs/demo.hex                    # 跑 hex 程序
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
