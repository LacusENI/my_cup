"""cocotb 测试模块：ALU（由 test_alu.py 通过 simulator 调起，pytest 不直接收集）"""

from typing import Protocol

import cocotb
from cocotb.triggers import Timer

from cocotb_utils import Signal, assert_fields


# ALU 操作码是对外契约：数值不要随意改。
ALU_OP_ADD = 0b0001
ALU_OP_SUB = 0b0010


# ALU 的公开字段：测试依赖哪些，就列哪些。
class AluDut(Protocol):
    alu_op: Signal
    alu_src1: Signal
    alu_src2: Signal
    alu_out: Signal
    zero_f: Signal


REQUIRED_FIELDS = (
    "alu_op",
    "alu_src1",
    "alu_src2",
    "alu_out",
    "zero_f",
)


@cocotb.test()
async def contract_test(dut: AluDut):
    """契约：ALU 仍然暴露测试依赖的端口。"""
    assert_fields(dut, REQUIRED_FIELDS, "alu")


@cocotb.test()
async def alu_add_test(dut: AluDut):
    dut.alu_op.value = ALU_OP_ADD
    dut.alu_src1.value = 5
    dut.alu_src2.value = 3
    await Timer(1, unit="ns")
    assert int(dut.alu_out.value) == 8
    assert int(dut.zero_f.value) == 0


@cocotb.test()
async def alu_sub_test(dut: AluDut):
    dut.alu_op.value = ALU_OP_SUB
    dut.alu_src1.value = 8
    dut.alu_src2.value = 8
    await Timer(1, unit="ns")
    assert int(dut.alu_out.value) == 0
    assert int(dut.zero_f.value) == 1
