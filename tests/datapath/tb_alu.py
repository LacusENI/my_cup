"""cocotb 测试模块：ALU（由 test_alu.py 通过 simulator 调起，pytest 不直接收集）。"""

from typing import Protocol

import cocotb

from utils.cocotb_utils import Signal, assert_fields, settle


ALU_NOP = 0
ALU_ADD = 1
ALU_EQ = 2


class AluDut(Protocol):
    alu_op: Signal
    alu_src1: Signal
    alu_src2: Signal
    alu_out: Signal
    cmp_result: Signal


REQUIRED_FIELDS = (
    "alu_op",
    "alu_src1",
    "alu_src2",
    "alu_out",
    "cmp_result",
)


@cocotb.test()
async def contract_test(dut: AluDut):
    """契约：ALU 暴露输入、结果和比较位。"""
    assert_fields(dut, REQUIRED_FIELDS, "alu")


@cocotb.test()
async def alu_add_test(dut: AluDut):
    """ADD：5 + 3 = 8，cmp_result 必须为 0。"""
    dut.alu_op.value = ALU_ADD
    dut.alu_src1.value = 5
    dut.alu_src2.value = 3
    await settle()

    assert int(dut.alu_out.value) == 8
    assert int(dut.cmp_result.value) == 0


@cocotb.test()
async def alu_add_wrap_test(dut: AluDut):
    """ADD 是 32 位回绕，不产生溢出异常。"""
    dut.alu_op.value = ALU_ADD
    dut.alu_src1.value = 0xFFFF_FFFF
    dut.alu_src2.value = 1
    await settle()

    assert int(dut.alu_out.value) == 0
    assert int(dut.cmp_result.value) == 0


@cocotb.test()
async def alu_eq_true_test(dut: AluDut):
    """EQ：相等时 cmp_result=1，alu_out=0。"""
    dut.alu_op.value = ALU_EQ
    dut.alu_src1.value = 244
    dut.alu_src2.value = 244
    await settle()

    assert int(dut.alu_out.value) == 0
    assert int(dut.cmp_result.value) == 1


@cocotb.test()
async def alu_eq_false_test(dut: AluDut):
    """EQ：不相等时 cmp_result=0。"""
    dut.alu_op.value = ALU_EQ
    dut.alu_src1.value = 244
    dut.alu_src2.value = 245
    await settle()

    assert int(dut.alu_out.value) == 0
    assert int(dut.cmp_result.value) == 0


@cocotb.test()
async def alu_nop_test(dut: AluDut):
    """NOP：输出和比较位都为 0。"""
    dut.alu_op.value = ALU_NOP
    dut.alu_src1.value = 0x1234_5678
    dut.alu_src2.value = 0x1234_5678
    await settle()

    assert int(dut.alu_out.value) == 0
    assert int(dut.cmp_result.value) == 0
