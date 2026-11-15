"""pc（程序计数器）的单元测试。

cocotb 用例和 pytest 入口在同一个文件里，由 ``@cocotb_test`` 连接。
详细机制见 ``tests/utils/cocotb_utils.py`` 的 ``cocotb_test``。

pc 是时序状态：
  - rst=1 时清零；
  - rst=0 且 stall=0 时，下一个上升沿写入 next_pc；
  - rst=0 且 stall=1 时保持当前值。
"""

from typing import Protocol

from cocotb.triggers import RisingEdge

from utils.cocotb_utils import (
    Signal,
    assert_fields,
    cocotb_test,
    settle,
    start_clock,
)


# conftest.py 里的 session fixture 名。
SIM = "pc_sim"


class PcDut(Protocol):
    clk: Signal
    rst: Signal
    stall: Signal
    next_pc: Signal
    curr_pc: Signal


REQUIRED_FIELDS = ("clk", "rst", "stall", "next_pc", "curr_pc")


@cocotb_test(dut=SIM)
async def test_contract(dut: PcDut):
    """契约：pc 暴露复位、stall 和下一 PC 接口。"""
    assert_fields(dut, REQUIRED_FIELDS, "pc")


@cocotb_test(dut=SIM)
async def test_pc_update_and_reset(dut: PcDut):
    """正常更新后，复位优先于 stall 和 next_pc。"""
    await start_clock(dut)

    dut.rst.value = 0
    dut.stall.value = 0
    dut.next_pc.value = 0x0000_0010
    await RisingEdge(dut.clk)
    await settle()
    assert int(dut.curr_pc.value) == 0x0000_0010

    dut.rst.value = 1
    dut.stall.value = 1
    dut.next_pc.value = 0x0000_0020
    await RisingEdge(dut.clk)
    await settle()
    assert int(dut.curr_pc.value) == 0

    dut.rst.value = 0
    dut.stall.value = 0
    dut.next_pc.value = 0x0000_0024
    await RisingEdge(dut.clk)
    await settle()
    assert int(dut.curr_pc.value) == 0x0000_0024


@cocotb_test(dut=SIM)
async def test_pc_stall(dut: PcDut):
    """stall=1 时 PC 保持；释放后恢复更新。"""
    await start_clock(dut)

    dut.rst.value = 0
    dut.stall.value = 0
    dut.next_pc.value = 0x0000_0010
    await RisingEdge(dut.clk)
    await settle()
    assert int(dut.curr_pc.value) == 0x0000_0010

    dut.stall.value = 1
    dut.next_pc.value = 0x0000_0020
    await RisingEdge(dut.clk)
    await settle()
    assert int(dut.curr_pc.value) == 0x0000_0010

    dut.stall.value = 0
    dut.next_pc.value = 0x0000_0024
    await RisingEdge(dut.clk)
    await settle()
    assert int(dut.curr_pc.value) == 0x0000_0024
