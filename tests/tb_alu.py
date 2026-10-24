"""cocotb 测试模块：ALU（由 test_alu.py 通过 simulator 调起，pytest 不直接收集）"""

import cocotb
from cocotb.triggers import Timer

from dut_api import AluDut
from rtl_consts import ALU_OP_ADD, ALU_OP_SUB


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
