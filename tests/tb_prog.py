"""
程序装载测试：验证 `$readmemh` + plusarg 机制。

这个测试不是“单指令 ISA 测试”，而是 program 级冒烟测试：
程序在仿真开始前由 `instrm` 的 `initial` + `$readmemh` 装入，
然后跑几个周期，检查 demo.hex 的最终结果。
"""

import os

import cocotb

from cocotb_utils import run_program

# 程序跑完后等待的周期数；mycup prog 可以通过环境变量覆盖
PROGRAM_CYCLES = int(os.environ.get("MYCUP_PROG_CYCLES", "4"))


@cocotb.test()
async def prog_demo_test(dut):
    """装载 programs/demo.hex，检查 R1=8、R2=5、R3=13。

    这个测试需要 pytest 包装层传入 +instr=<绝对路径>；
    程序本身在仿真开始前由 instrm 的 $readmemh 装入。
    """
    # instructions 传空：不要覆盖 $readmemh 已经装好的程序
    await run_program(dut, instructions=[], extra_cycles=PROGRAM_CYCLES)

    # demo.hex: addiu $1,8; addiu $2,5; addu $3,$1,$2
    assert int(dut.u_regfile.regs[1].value) == 8
    assert int(dut.u_regfile.regs[2].value) == 5
    assert int(dut.u_regfile.regs[3].value) == 13
