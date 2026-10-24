# Python 验证 PoC（cocotb + pytest）

这是与现有 HDL testbench **并存**的 Python 验证入口，不影响 `sim/tb` 下任何旧用例。
目标是先跑通「uv + cocotb + pytest + Icarus」这条链，验证可行后再逐步迁移。

## 快速开始

```bash
uv sync            # 创建 .venv 并安装 cocotb / pytest（首次）
uv run pytest -v   # 运行全部 Python 用例
uv run mycup test  # 等价的统一入口
```

依赖只追踪 Python 侧；`iverilog` / `verilator` 仍是系统依赖。

## 目录结构

```
tests/
├── conftest.py        # session 级 build fixture（每个 DUT 只编译一次）
├── tb_alu.py          # cocotb 用例（HDL 激励，由仿真器加载）
├── test_alu.py        # pytest 包装（调用 runner.test）
├── tb_lw_sw.py        # 指令级：sw/lw 往返
└── test_lw_sw.py
```

命名约定（很重要）：

- `tb_*.py`：**cocotb 测试模块**，由仿真器在 Python 进程中加载，pytest **不会**直接收集；
- `test_*.py`：**pytest 用例**，负责 `build` 后调用 `runner.test()`。

## 与旧 testbench 的对应关系

| Python | 旧 HDL TB |
| :-- | :-- |
| `test_alu.py` / `tb_alu.py` | `sim/tb/unit/tb_alu.v` |
| `test_lw_sw.py` / `tb_lw_sw.py` | `sim/tb/instr/tb_lw.v` + `tb_sw.v`（lw/sw 往返） |

## 常用命令

```bash
uv run pytest -v tests/test_alu.py                 # 单个文件
uv run pytest -v tests/test_alu.py::test_alu_add   # 单个用例
MYCUP_WAVES=1 uv run pytest -v tests/test_lw_sw.py   # 导出波形
```

波形由 cocotb/仿真器生成（Icarus 下为 `build/cocotb/<toplevel>_wave/<toplevel>.fst`），可用 GTKWave 打开。

## 已验证的坑

1. **必须设 timescale**：`build(timescale=("1ns", "1ps"))`，否则 Icarus 精度是 1 秒，
   `Timer(1, "ns")` 会抛 `Unable to accurately represent`。
2. **cocotb 2.x 用 `cocotb_tools.runner`**，没有 `cocotb.runner`。
3. **内部信号可直接读写**：`dut.u_regfile.regs[1].value = ...`（Icarus VPI 实测可用）。
4. **`ReadOnly` 阶段不能赋值**：先 `await Timer(...)` 或等到下一个 `RisingEdge`。
5. **Icarus 不支持 `'{...}` 结构体赋值模式**（仿真侧用逐字段赋值）。
6. `build()` 默认会复用已有构建；RTL 改动后如需强制重编，可传 `always=True`。

## 下一步（待你确认）

- 把剩余指令级 TB 逐个迁移过来（可用 pytest 参数化减少重复）；
- 写一个 Python 参考模型 `tests/model/iss.py`，做**整程序差分对比**（这是 cocotb 最大的价值）；
- 需要更快的仿真时，把后端从 Icarus 换成 Verilator（内部信号访问需加相应编译选项）；
- 全部迁移完成、CI 稳定后，再考虑下线 `sim/tb`。
