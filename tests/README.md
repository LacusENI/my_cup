# Python 验证（cocotb + pytest）

用 Python 写 testbench：**编译一次、pytest 收集、仿真器执行**。
目标是逐步替换 `sim/tb` 下的 HDL TB，让验证只有一条链路。

## 快速开始

```bash
uv sync            # 首次：创建 .venv，安装 cocotb / pytest
uv run mycup test  # 跑全部 Python 用例
uv run pytest -v   # 同上（直接调 pytest）
```

依赖只追踪 Python 侧；`iverilog` / `verilator` 仍是系统依赖。

## 目录结构

```
tests/
├── conftest.py        # fixture：编译 DUT + run_cocotb_case
├── cocotb_utils.py    # 时钟 / 复位 / 等待的小工具
├── tb_alu.py          # cocotb 用例：alu
├── test_alu.py        # pytest 包装
├── tb_ctrl.py         # cocotb 用例：控制器
├── test_ctrl.py
├── tb_datam.py        # cocotb 用例：数据存储器
├── test_datam.py
├── tb_npc.py          # cocotb 用例：下一 PC
├── test_npc.py
├── tb_regfile.py      # cocotb 用例：寄存器堆
├── test_regfile.py
├── tb_lw_sw.py        # 指令级：sw → lw 往返
└── test_lw_sw.py
```

命名约定（很重要）：

- `tb_*.py`：**cocotb 测试模块**，由仿真器在 Python 进程里加载，pytest **不会**直接收集；
- `test_*.py`：**pytest 用例**，负责调用 `runner.test()`，只做“入口”和“报告”。

## 与 HDL TB 的对应关系

| Python | HDL TB | 状态 |
| :-- | :-- | :-- |
| `test_alu.py` / `tb_alu.py` | `sim/tb/unit/tb_alu.v` | ✅ |
| `test_ctrl.py` / `tb_ctrl.py` | `sim/tb/unit/tb_ctrl.v` | ✅ |
| `test_datam.py` / `tb_datam.py` | `sim/tb/unit/tb_datam.v` | ✅ |
| `test_npc.py` / `tb_npc.py` | `sim/tb/unit/tb_npc.v` | ✅ |
| `test_regfile.py` / `tb_regfile.py` | `sim/tb/unit/tb_regfile.v` | ✅ |
| `test_lw_sw.py` / `tb_lw_sw.py` | `sim/tb/instr/tb_lw.v`、`tb_sw.v` | ✅（往返覆盖） |
| — | `tb_addiu/addu/beq/j/jal/jr.v` | ⏳ 待迁移 |
| — | `tb_prog.v` | ⏳ 待迁移 |

## 怎么写一个新测试（3 步）

以 `npc` 为例：

### 1. 在 `conftest.py` 加一个 fixture

```python
@pytest.fixture(scope="session")
def npc_sim():
    """单元级：npc（纯组合逻辑）。"""
    return _build("npc", [RTL / "core" / "units" / "npc.v"], "npc")
```

`_build` 会调用 `iverilog` 编译，并记录 build 目录；`session` 表示整个测试会话只编译一次。

### 2. 写 `tb_npc.py`（cocotb 用例）

```python
import cocotb
from cocotb_utils import settle

@cocotb.test()
async def plus4_test(dut):
    """普通情况：PC = PC + 4。"""
    dut.curr_pc.value = 0x10
    dut.npc_op.value = 0b00
    dut.cond_jmp.value = 0
    await settle()
    assert int(dut.next_pc.value) == 0x14
```

- `@cocotb.test()` 注册用例；
- `dut` 是 HDL 顶层句柄；
- `await settle()` 等组合逻辑稳定。

### 3. 写 `test_npc.py`（pytest 包装）

```python
def test_npc_plus4(npc_sim, run_cocotb_case):
    """顺序执行：PC + 4。"""
    run_cocotb_case(npc_sim, "tb_npc", "plus4_test")
```

`run_cocotb_case` 是 `conftest.py` 里的 fixture，负责启动一次仿真。

## 常用命令

```bash
uv run mycup test                                  # 全部
uv run pytest -v tests/test_ctrl.py                # 单个文件
uv run pytest -v tests/test_ctrl.py::test_addu_control   # 单个用例
MYCUP_WAVES=1 uv run pytest -v tests/test_npc.py   # 导出波形
```

波形路径：`build/cocotb/<toplevel>_wave/<toplevel>.fst`，可用 GTKWave 打开。

## 已验证的坑

1. **必须设 timescale**：`build(timescale=("1ns", "1ps"))`，否则 `Timer(1, "ns")` 会报精度错误。
2. **cocotb 2.x 用 `cocotb_tools.runner`**，没有 `cocotb.runner`。
3. **内部信号可直接读写**：`dut.u_regfile.regs[1].value = ...`（Icarus VPI 实测可用）。
4. **`ReadOnly` 阶段不能赋值**：先 `await Timer(...)` 或等到下一个 `RisingEdge`。
5. **Icarus 不支持 `'{...}` 结构体赋值模式**（仿真侧用逐字段赋值）。
6. `build()` 默认会复用已有构建；RTL 改动后如需强制重编，可传 `always=True`。
7. **组合逻辑测试用 `await settle()`**（等 1ns）；时序逻辑测试用 `await RisingEdge(clk)` + `await ReadOnly()`。

## 迁移进度

- [x] `alu`
- [x] `ctrl`
- [x] `datam`
- [x] `npc`
- [x] `regfile`
- [x] `lw/sw` 往返
- [ ] `addiu` / `addu` / `beq` / `j` / `jal` / `jr`
- [ ] `tb_prog`（用 `runner.test(plusargs=[...])`）
- [ ] 删除 `sim/tb/**` 与 `lib/vtest.vh`
- [ ] 简化 `mycup`（去掉 build / run / all / wave）
