"""halt_unit（停机仲裁）的单元测试。

halt_unit 是纯组合逻辑，负责汇总译码级 halt 与各类地址故障。
优先级：

    inst_addr_err
      > inst_illegal
      > sys_op
      > load_addr_err
      > store_addr_err
      > target_addr_err
"""

from typing import Protocol

from utils.cocotb_utils import Signal, assert_fields, cocotb_test, settle
from utils.cpu_pkg import (
    HALT_EBREAK,
    HALT_ECALL,
    HALT_ILLEGAL_INST,
    HALT_INST_ADDR_ERR,
    HALT_LOAD_ADDR_ERR,
    HALT_STORE_ADDR_ERR,
    SYS_EBREAK,
    SYS_ECALL,
    SYS_NONE,
)


# conftest.py 里的 session fixture 名。
SIM = "halt_unit_sim"


class HaltUnitDut(Protocol):
    inst_illegal: Signal
    sys_op: Signal
    inst_addr_err: Signal
    load_addr_err: Signal
    store_addr_err: Signal
    target_addr_err: Signal
    halt: Signal
    halt_cause: Signal


REQUIRED_FIELDS = (
    "inst_illegal",
    "sys_op",
    "inst_addr_err",
    "load_addr_err",
    "store_addr_err",
    "target_addr_err",
    "halt",
    "halt_cause",
)


async def drive(
    dut: HaltUnitDut,
    *,
    inst_illegal: int = 0,
    sys_op: int = SYS_NONE,
    inst_addr_err: int = 0,
    load_addr_err: int = 0,
    store_addr_err: int = 0,
    target_addr_err: int = 0,
) -> None:
    dut.inst_illegal.value = inst_illegal
    dut.sys_op.value = sys_op
    dut.inst_addr_err.value = inst_addr_err
    dut.load_addr_err.value = load_addr_err
    dut.store_addr_err.value = store_addr_err
    dut.target_addr_err.value = target_addr_err
    await settle()


@cocotb_test(dut=SIM)
async def test_contract(dut: HaltUnitDut):
    """契约：halt_unit 暴露所有仲裁输入和输出。"""
    assert_fields(dut, REQUIRED_FIELDS, "halt_unit")


@cocotb_test(dut=SIM)
async def test_no_fault(dut: HaltUnitDut):
    """没有故障时不停机。"""
    await drive(dut)

    assert int(dut.halt.value) == 0


@cocotb_test(dut=SIM)
async def test_inst_illegal(dut: HaltUnitDut):
    """非法指令映射为 cause 2。"""
    await drive(dut, inst_illegal=1)

    assert int(dut.halt.value) == 1
    assert int(dut.halt_cause.value) == HALT_ILLEGAL_INST


@cocotb_test(dut=SIM)
async def test_sys_ecall(dut: HaltUnitDut):
    """ECALL 映射为 cause 11。"""
    await drive(dut, sys_op=SYS_ECALL)

    assert int(dut.halt.value) == 1
    assert int(dut.halt_cause.value) == HALT_ECALL


@cocotb_test(dut=SIM)
async def test_sys_ebreak(dut: HaltUnitDut):
    """EBREAK 映射为 cause 3。"""
    await drive(dut, sys_op=SYS_EBREAK)

    assert int(dut.halt.value) == 1
    assert int(dut.halt_cause.value) == HALT_EBREAK


@cocotb_test(dut=SIM)
async def test_inst_addr_err_priority(dut: HaltUnitDut):
    """取指地址错误优先级最高。"""
    await drive(
        dut,
        inst_illegal=1,
        sys_op=SYS_ECALL,
        inst_addr_err=1,
        load_addr_err=1,
        store_addr_err=1,
        target_addr_err=1,
    )

    assert int(dut.halt.value) == 1
    assert int(dut.halt_cause.value) == HALT_INST_ADDR_ERR


@cocotb_test(dut=SIM)
async def test_load_addr_err(dut: HaltUnitDut):
    """load 地址错误映射为 cause 4。"""
    await drive(dut, load_addr_err=1)

    assert int(dut.halt.value) == 1
    assert int(dut.halt_cause.value) == HALT_LOAD_ADDR_ERR


@cocotb_test(dut=SIM)
async def test_store_addr_err(dut: HaltUnitDut):
    """store 地址错误映射为 cause 6。"""
    await drive(dut, store_addr_err=1)

    assert int(dut.halt.value) == 1
    assert int(dut.halt_cause.value) == HALT_STORE_ADDR_ERR


@cocotb_test(dut=SIM)
async def test_target_addr_err(dut: HaltUnitDut):
    """跳转目标错误映射为取指地址错误 cause 0。"""
    await drive(dut, target_addr_err=1)

    assert int(dut.halt.value) == 1
    assert int(dut.halt_cause.value) == HALT_INST_ADDR_ERR


@cocotb_test(dut=SIM)
async def test_priority_order(dut: HaltUnitDut):
    """inst_illegal > sys_op > load > store > target。"""
    await drive(
        dut,
        inst_illegal=1,
        sys_op=SYS_ECALL,
        load_addr_err=1,
        store_addr_err=1,
        target_addr_err=1,
    )
    assert int(dut.halt_cause.value) == HALT_ILLEGAL_INST

    await drive(
        dut,
        sys_op=SYS_ECALL,
        load_addr_err=1,
        store_addr_err=1,
        target_addr_err=1,
    )
    assert int(dut.halt_cause.value) == HALT_ECALL

    await drive(dut, load_addr_err=1, store_addr_err=1, target_addr_err=1)
    assert int(dut.halt_cause.value) == HALT_LOAD_ADDR_ERR

    await drive(dut, store_addr_err=1, target_addr_err=1)
    assert int(dut.halt_cause.value) == HALT_STORE_ADDR_ERR

    await drive(dut, target_addr_err=1)
    assert int(dut.halt_cause.value) == HALT_INST_ADDR_ERR
