"""instm（指令存储器）的单元测试。

instm 是纯组合存储器：
  - 按字索引读取指令；
  - inst_addr[1:0] != 0 时只置 inst_addr_err，不在模块内部停机。

停机语义由 cpu_top 统一处理。
"""

from typing import Protocol

from utils.cocotb_utils import Signal, assert_fields, cocotb_test, settle


# conftest.py 里的 session fixture 名。
SIM = "instm_sim"


class InstmDut(Protocol):
    inst_addr: Signal
    inst: Signal
    inst_addr_err: Signal


REQUIRED_FIELDS = ("inst_addr", "inst", "inst_addr_err")


@cocotb_test(dut=SIM)
async def test_contract(dut: InstmDut):
    """契约：instm 暴露取指地址、指令和地址错误。"""
    assert_fields(dut, REQUIRED_FIELDS, "instm")


@cocotb_test(dut=SIM)
async def test_instm_addr_err(dut: InstmDut):
    """取指地址未对齐时置 inst_addr_err，对齐时为 0。"""
    dut.inst_addr.value = 0x0000_0000
    await settle()
    assert int(dut.inst_addr_err.value) == 0

    dut.inst_addr.value = 0x0000_0002
    await settle()
    assert int(dut.inst_addr_err.value) == 1
