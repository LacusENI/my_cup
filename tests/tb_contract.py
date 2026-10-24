"""
契约测试：检查真实 RTL 是否仍然暴露测试依赖的字段。

这些测试不验证功能，只验证“接口还在”：
  - 如果某个信号/子模块被改名或删除，这里会直接失败；
  - 失败信息会提示同步更新 tests/dut_api.py。

这样测试代码可以放心用 `dut_api` 里的访问器，
而不用靠“跑起来才发现字段没了”。
"""

import cocotb

from dut_api import assert_public_fields


@cocotb.test()
async def cpu_top_contract_test(dut):
    """cpu_top：ISA 测试依赖的 PC / 寄存器堆 / 指令内存 / 数据内存。"""
    assert_public_fields(dut, "cpu_top")


@cocotb.test()
async def alu_contract_test(dut):
    """alu：操作码、两个源操作数、结果和标志位。"""
    assert_public_fields(dut, "alu")


@cocotb.test()
async def ctrl_contract_test(dut):
    """ctrl：op / funct 输入和打包后的 ctrl 输出。"""
    assert_public_fields(dut, "ctrl")


@cocotb.test()
async def datam_contract_test(dut):
    """datam：读写控制、地址、数据端口和内部 mem 数组。"""
    assert_public_fields(dut, "datam")


@cocotb.test()
async def npc_contract_test(dut):
    """npc：当前 PC、跳转控制和下一 PC。"""
    assert_public_fields(dut, "npc")


@cocotb.test()
async def regfile_contract_test(dut):
    """regfile：读写端口和内部 regs 数组。"""
    assert_public_fields(dut, "regfile")


@cocotb.test()
async def if_id_reg_contract_test(dut):
    """IF/ID 流水线寄存器。"""
    assert_public_fields(dut, "if_id_reg")


@cocotb.test()
async def id_ex_reg_contract_test(dut):
    """ID/EX 流水线寄存器。"""
    assert_public_fields(dut, "id_ex_reg")


@cocotb.test()
async def ex_mem_reg_contract_test(dut):
    """EX/MEM 流水线寄存器。"""
    assert_public_fields(dut, "ex_mem_reg")


@cocotb.test()
async def mem_wb_reg_contract_test(dut):
    """MEM/WB 流水线寄存器。"""
    assert_public_fields(dut, "mem_wb_reg")
