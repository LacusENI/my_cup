"""
ISA 级测试：每个用例只执行一条 RV32I 指令。

只断言架构状态：
  - PC（下一条指令地址）
  - 通用寄存器
  - 数据内存
  - inst_illegal

不读内部数据通路信号，也不依赖实现细节。
分支/跳转只断言 PC，不执行目标指令。
"""

from typing import Protocol

import cocotb

from utils.cocotb_utils import (
    CpuAccess,
    Signal,
    assert_fields,
    read_mem,
    read_pc,
    read_reg,
    read_reg_raw,
    run_one_instruction,
)
from utils.riscv_asm import add, addi, beq, jal, jalr, lw, sw


class CpuTop(CpuAccess, Protocol):
    """cpu_top 供 ISA 测试使用的字段。"""

    inst_illegal: Signal


CPU_TOP_FIELDS = (
    "clk",
    "rst",
    "inst_illegal",
    "u_pc.curr_pc",
    "u_pc.next_pc",
    "u_regfile.regs",
    "u_instrm.mem",
    "u_datam.mem",
)


@cocotb.test()
async def contract_test(dut: CpuTop):
    """契约：cpu_top 暴露测试依赖的架构状态和 inst_illegal。"""
    assert_fields(dut, CPU_TOP_FIELDS, "cpu_top")


# --------------------------------------------------------------------------- #
# 算术
# --------------------------------------------------------------------------- #
@cocotb.test()
async def add_test(dut: CpuTop):
    """add x3, x1, x2：5 + 3 = 8，PC 前进到 4。"""
    await run_one_instruction(
        dut,
        add(rd=3, rs1=1, rs2=2),
        registers={1: 5, 2: 3},
    )

    assert read_reg(dut, 3) == 8
    assert read_pc(dut) == 4


@cocotb.test()
async def add_wrap_test(dut: CpuTop):
    """add 是 32 位回绕：0xFFFFFFFF + 1 = 0。"""
    await run_one_instruction(
        dut,
        add(rd=3, rs1=1, rs2=2),
        registers={1: 0xFFFF_FFFF, 2: 1},
    )

    assert read_reg(dut, 3) == 0
    assert read_pc(dut) == 4


@cocotb.test()
async def addi_positive_test(dut: CpuTop):
    """addi x1, x0, 8：正数立即数。"""
    await run_one_instruction(dut, addi(rd=1, rs1=0, imm=8))

    assert read_reg(dut, 1) == 8
    assert read_pc(dut) == 4


@cocotb.test()
async def addi_negative_test(dut: CpuTop):
    """addi x2, x0, -1：验证 12 位立即数符号扩展。"""
    await run_one_instruction(dut, addi(rd=2, rs1=0, imm=-1))

    assert read_reg(dut, 2) == 0xFFFF_FFFF
    assert read_pc(dut) == 4


@cocotb.test()
async def addi_x0_test(dut: CpuTop):
    """写 x0 必须被丢弃。"""
    await run_one_instruction(dut, addi(rd=0, rs1=0, imm=8), registers={0: 0})

    assert read_reg_raw(dut, 0) == 0
    assert read_pc(dut) == 4


# --------------------------------------------------------------------------- #
# 分支
# --------------------------------------------------------------------------- #
@cocotb.test()
async def beq_taken_test(dut: CpuTop):
    """beq 成立：PC = 0 + 8 = 8。"""
    await run_one_instruction(
        dut,
        beq(rs1=1, rs2=2, offset=8),
        registers={1: 8, 2: 8},
    )

    assert read_pc(dut) == 8


@cocotb.test()
async def beq_not_taken_test(dut: CpuTop):
    """beq 不成立：PC = 4。"""
    await run_one_instruction(
        dut,
        beq(rs1=1, rs2=2, offset=8),
        registers={1: 8, 2: 9},
    )

    assert read_pc(dut) == 4


# --------------------------------------------------------------------------- #
# 跳转
# --------------------------------------------------------------------------- #
@cocotb.test()
async def jal_test(dut: CpuTop):
    """jal x1, 8：PC=8，x1=PC+4=4。"""
    await run_one_instruction(dut, jal(rd=1, offset=8))

    assert read_pc(dut) == 8
    assert read_reg(dut, 1) == 4


@cocotb.test()
async def jal_x0_test(dut: CpuTop):
    """jal x0, 8：不写 x0。"""
    await run_one_instruction(dut, jal(rd=0, offset=8), registers={0: 0})

    assert read_pc(dut) == 8
    assert read_reg_raw(dut, 0) == 0


@cocotb.test()
async def jalr_test(dut: CpuTop):
    """jalr x1, 0(x2)：PC=x2=8，x1=4。"""
    await run_one_instruction(
        dut,
        jalr(rd=1, offset=0, rs1=2),
        registers={2: 8},
    )

    assert read_pc(dut) == 8
    assert read_reg(dut, 1) == 4


@cocotb.test()
async def jalr_rd_equals_rs1_test(dut: CpuTop):
    """jalr x1, 4(x1)：目标必须用旧的 x1 计算。"""
    await run_one_instruction(
        dut,
        jalr(rd=1, offset=4, rs1=1),
        registers={1: 8},
    )

    assert read_pc(dut) == 12
    assert read_reg(dut, 1) == 4


@cocotb.test()
async def jalr_x0_test(dut: CpuTop):
    """jalr x0, 0(x2)：不写 x0。"""
    await run_one_instruction(
        dut,
        jalr(rd=0, offset=0, rs1=2),
        registers={0: 0, 2: 8},
    )

    assert read_pc(dut) == 8
    assert read_reg_raw(dut, 0) == 0


# --------------------------------------------------------------------------- #
# 访存
# --------------------------------------------------------------------------- #
@cocotb.test()
async def lw_test(dut: CpuTop):
    """lw x2, 0(x1)：从地址 8 读一个字到 x2。"""
    await run_one_instruction(
        dut,
        lw(rd=2, offset=0, rs1=1),
        registers={1: 8},
        memory={2: 0x1122_3344},
    )

    assert read_reg(dut, 2) == 0x1122_3344
    assert read_pc(dut) == 4


@cocotb.test()
async def lw_negative_offset_test(dut: CpuTop):
    """lw x2, -4(x1)：负偏移地址计算。"""
    await run_one_instruction(
        dut,
        lw(rd=2, offset=-4, rs1=1),
        registers={1: 8},
        memory={1: 0xAABB_CCDD},
    )

    assert read_reg(dut, 2) == 0xAABB_CCDD
    assert read_pc(dut) == 4


@cocotb.test()
async def sw_test(dut: CpuTop):
    """sw x3, 0(x1)：把 x3 写到地址 8，不写寄存器。"""
    await run_one_instruction(
        dut,
        sw(rs2=3, offset=0, rs1=1),
        registers={1: 8, 3: 0x1122_3344},
        memory={2: 0},
    )

    assert read_mem(dut, 2) == 0x1122_3344
    assert read_reg(dut, 3) == 0x1122_3344
    assert read_pc(dut) == 4


@cocotb.test()
async def sw_negative_offset_test(dut: CpuTop):
    """sw x3, -4(x1)：负偏移地址计算。"""
    await run_one_instruction(
        dut,
        sw(rs2=3, offset=-4, rs1=1),
        registers={1: 8, 3: 0x5566_7788},
        memory={1: 0},
    )

    assert read_mem(dut, 1) == 0x5566_7788
    assert read_pc(dut) == 4


# --------------------------------------------------------------------------- #
# 非法指令
# --------------------------------------------------------------------------- #
@cocotb.test()
async def illegal_stop_test(dut: CpuTop):
    """非法编码：PC 保持，寄存器/内存都不改变。"""
    # sub x3, x1, x2 的 funct7=0x20；本批只实现 add。
    illegal = 0x4020_81B3
    await run_one_instruction(
        dut,
        illegal,
        registers={1: 5, 2: 3, 3: 0x1234_5678},
        memory={0: 0xDEAD_BEEF},
    )

    assert int(dut.inst_illegal.value) == 1
    assert read_pc(dut) == 0
    assert read_reg(dut, 3) == 0x1234_5678
    assert read_mem(dut, 0) == 0xDEAD_BEEF
