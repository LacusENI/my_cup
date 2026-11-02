"""
程序装载测试：验证 `$readmemh` + plusarg 机制。

这个测试不是“单指令 ISA 测试”，而是 program 级冒烟测试：
程序在仿真开始前由 `instm` 的 `initial` + `$readmemh` 装入，
然后跑几个周期，检查 demo.hex 的最终结果。
"""

import os

import cocotb

from utils.cocotb_utils import CpuAccess, read_reg, run_program

# 程序跑完后等待的周期数；mycup prog 可以通过环境变量覆盖
PROGRAM_CYCLES = int(os.environ.get("MYCUP_PROG_CYCLES", "8"))


@cocotb.test()
async def prog_demo_test(dut: CpuAccess):
    """装载 programs/demo.hex，检查算术、访存和 beq 跳过程序流。

    这个测试需要 pytest 包装层传入 +inst=<绝对路径>；
    程序本身在仿真开始前由 instm 的 $readmemh 装入。
    """
    # instuctions 传空：不要覆盖 $readmemh 已经装好的程序。
    # x5 预置为 0，用来验证 beq 确实跳过了 addi x5,x0,99。
    await run_program(
        dut,
        instuctions=[],
        registers={5: 0},
        extra_cycles=PROGRAM_CYCLES,
    )

    # demo.hex 覆盖 addi/add/sw/lw/beq；x5 所在指令应被 beq 跳过。
    assert read_reg(dut, 1) == 8
    assert read_reg(dut, 2) == 5
    assert read_reg(dut, 3) == 13
    assert read_reg(dut, 4) == 13
    assert read_reg(dut, 5) == 0
