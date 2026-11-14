"""程序装载测试（program 级冒烟测试）。

cocotb 用例和 pytest 入口在同一个文件里，由 ``@cocotb_test`` 连接。
详细机制见 ``tests/utils/cocotb_utils.py`` 的 ``cocotb_test``。

这个测试不是“单指令 ISA 测试”，而是 program 级检查：
程序在仿真开始前由 ``instm`` 的 ``initial`` + ``$readmemh`` 装入，
然后跑几个周期，检查 demo.hex 的最终结果。

plusargs 必须在启动仿真器之前确定，所以这里通过 ``_plusargs()``
在 wrapper 运行时求值，再交给 ``runner.test(plusargs=...)``。
"""

import os
from pathlib import Path

from utils.cocotb_utils import CpuAccess, cocotb_test, read_reg, run_program


# conftest.py 里的 session fixture 名。
SIM = "cpu_sim"


# 默认用 demo.hex；也可以通过 MYCUP_PROG 环境变量指定别的程序（mycup prog 会设置）
# tests/cpu/test_prog.py -> 项目根目录
DEMO_PROGRAM = Path(__file__).resolve().parents[2] / "programs" / "demo.hex"
PROGRAM = Path(os.environ.get("MYCUP_PROG", str(DEMO_PROGRAM)))
DATA_FILE = os.environ.get("MYCUP_DATA")

# 程序跑完后等待的周期数；mycup prog 可以通过环境变量覆盖
PROGRAM_CYCLES = int(os.environ.get("MYCUP_PROG_CYCLES", "8"))


def _plusargs() -> list[str]:
    """构造 runner.test 需要的 +inst / +data 参数。

    这个函数在 pytest 进程里执行，结果会传给仿真器命令行；
    所以不能在 cocotb 测试函数内部临时加 plusargs。
    """
    args = [f"+inst={PROGRAM}"]
    if DATA_FILE:
        args.append(f"+data={DATA_FILE}")
    return args


@cocotb_test(dut=SIM, plusargs=_plusargs)
async def test_prog_demo(dut: CpuAccess):
    """装载 programs/demo.hex，检查算术、访存和 beq 跳过程序流。"""
    # instructions 传空：不要覆盖 $readmemh 已经装好的程序。
    # x5 预置为 0，用来验证 beq 确实跳过了 addi x5,x0,99。
    await run_program(
        dut,
        instructions=[],
        registers={5: 0},
        extra_cycles=PROGRAM_CYCLES,
    )

    # demo.hex 覆盖 addi/add/sw/lw/beq；x5 所在指令应被 beq 跳过。
    assert read_reg(dut, 1) == 8
    assert read_reg(dut, 2) == 5
    assert read_reg(dut, 3) == 13
    assert read_reg(dut, 4) == 13
    assert read_reg(dut, 5) == 0
