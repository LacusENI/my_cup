"""程序装载测试（program 级冒烟测试）。

cocotb 用例和 pytest 入口在同一个文件里，由 ``@cocotb_test`` 连接。
详细机制见 ``tests/utils/cocotb_utils.py`` 的 ``cocotb_test``。

这个测试不是“单指令 ISA 测试”，而是 program 级检查：
程序先在测试流程前由 ``mycup build-programs`` 汇编，
再由 ``instm`` 的 ``initial`` + ``$readmemh`` 装入，
然后运行到 ``halt``，检查 demo.S 的最终结果。

plusargs 必须在启动仿真器之前确定，所以这里通过 ``_plusargs()``
在 wrapper 运行时求值，再交给 ``runner.test(plusargs=...)``。
"""

import os

from mycup.programs import resolve_program
from utils.cocotb_utils import CpuAccess, cocotb_test, read_reg, run_program
from utils.cpu_pkg import HALT_ECALL


# conftest.py 里的 session fixture 名。
SIM = "cpu_sim"


# 默认用 demo.S；也可以通过 MYCUP_PROG 指定 .S 或 .hex。
# .S 会先由 mycup build-programs / mycup test 汇编。
PROGRAM = os.environ.get("MYCUP_PROG", "programs/demo.S")
DATA_FILE = os.environ.get("MYCUP_DATA")

# 程序跑完后等待的周期数；mycup prog 可以通过环境变量覆盖
PROGRAM_CYCLES = int(os.environ.get("MYCUP_PROG_CYCLES", "8"))


def _plusargs() -> list[str]:
    """构造 runner.test 需要的 +inst / +data 参数。

    这个函数在 pytest 进程里执行，结果会传给仿真器命令行；
    所以不能在 cocotb 测试函数内部临时加 plusargs。
    """
    args = [f"+inst={resolve_program(PROGRAM)}"]
    if DATA_FILE:
        args.append(f"+data={DATA_FILE}")
    return args


@cocotb_test(dut=SIM, plusargs=_plusargs)
async def test_prog_demo(dut: CpuAccess):
    """装载 programs/demo.S，运行到 ecall halt 后检查程序结果。"""
    # instructions 传空：不要覆盖 $readmemh 已经装好的程序。
    # x5 预置为 0，用来验证 beq 确实跳过了 addi x5,x0,99。
    await run_program(
        dut,
        instructions=[],
        registers={5: 0},
        extra_cycles=PROGRAM_CYCLES,
    )

    # demo.S 覆盖 addi/add/sw/lw/beq/lui/auipc/fence/ecall。
    # x5 所在指令应被 beq 跳过；程序最后停在 ecall。
    assert read_reg(dut, 1) == 8
    assert read_reg(dut, 2) == 5
    assert read_reg(dut, 3) == 13
    assert read_reg(dut, 4) == 13
    assert read_reg(dut, 5) == 0
    assert read_reg(dut, 6) == 0x12345_000
    assert read_reg(dut, 7) == 0x0000_0020
    assert int(dut.halt.value) == 1
    assert int(dut.halt_cause.value) == HALT_ECALL
