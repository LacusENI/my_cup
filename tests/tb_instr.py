"""
ISA 级测试：**每个用例只执行一条指令**。

只断言架构状态：
  - PC（下一条指令地址）
  - 通用寄存器
  - 数据内存

不读内部流水线信号，也不依赖“跑几个周期”。
分支/跳转只断言 PC，不执行目标指令——目标指令属于 program 测试。

机器码由 `mips_asm` 里的编码器生成，不再手写十六进制。
"""

import cocotb

from cocotb_utils import run_one_instruction
from dut_api import CpuTop, read_mem, read_pc, read_reg
from mips_asm import addu, addiu, beq, j, jal, jr, lw, sw


# --------------------------------------------------------------------------- #
# 算术 / 逻辑
# --------------------------------------------------------------------------- #
@cocotb.test()
async def addu_test(dut: CpuTop):
    """addu $3, $1, $2：5 + 3 = 8；PC 应该前进到 4。"""
    await run_one_instruction(
        dut,
        addu(rd=3, rs=1, rt=2),
        registers={1: 5, 2: 3},
    )

    assert read_reg(dut, 3) == 8
    assert read_pc(dut) == 4


@cocotb.test()
async def addiu_positive_test(dut: CpuTop):
    """addiu $1, $0, 8：正数立即数。"""
    await run_one_instruction(dut, addiu(rt=1, rs=0, imm=8))

    assert read_reg(dut, 1) == 8
    assert read_pc(dut) == 4


@cocotb.test()
async def addiu_negative_test(dut: CpuTop):
    """addiu $2, $0, -1：验证符号扩展。"""
    await run_one_instruction(dut, addiu(rt=2, rs=0, imm=-1))

    assert read_reg(dut, 2) == 0xFFFF_FFFF
    assert read_pc(dut) == 4


# --------------------------------------------------------------------------- #
# 分支 / 跳转：只断言 PC
# --------------------------------------------------------------------------- #
@cocotb.test()
async def beq_taken_test(dut: CpuTop):
    """beq 成立：PC = 0 + (2 << 2) = 8。"""
    await run_one_instruction(
        dut,
        beq(rs=1, rt=2, offset=2),
        registers={1: 8, 2: 8},   # 相等
    )

    assert read_pc(dut) == 8


@cocotb.test()
async def beq_not_taken_test(dut: CpuTop):
    """beq 不成立：PC = 4。"""
    await run_one_instruction(
        dut,
        beq(rs=1, rt=2, offset=2),
        registers={1: 8, 2: 9},   # 不相等
    )

    assert read_pc(dut) == 4


@cocotb.test()
async def j_test(dut: CpuTop):
    """j 2：PC = 2 << 2 = 8。"""
    await run_one_instruction(dut, j(target=2))

    assert read_pc(dut) == 8


@cocotb.test()
async def jal_test(dut: CpuTop):
    """jal 3：PC = 12，同时 $31 = PC+4 = 4。"""
    await run_one_instruction(dut, jal(target=3))

    assert read_pc(dut) == 12
    assert read_reg(dut, 31) == 4


@cocotb.test()
async def jr_test(dut: CpuTop):
    """jr $1：PC = R1 = 8。"""
    await run_one_instruction(dut, jr(rs=1), registers={1: 8})

    assert read_pc(dut) == 8


# --------------------------------------------------------------------------- #
# 访存：只断言寄存器 / 内存 / PC
# --------------------------------------------------------------------------- #
@cocotb.test()
async def lw_test(dut: CpuTop):
    """lw $2, 0($1)：从地址 8 读一个字到 R2。"""
    await run_one_instruction(
        dut,
        lw(rt=2, offset=0, base=1),
        registers={1: 8},              # 地址 8 -> mem[2]
        memory={2: 0x1122_3344},       # 预置内存
    )

    assert read_reg(dut, 2) == 0x1122_3344
    assert read_pc(dut) == 4


@cocotb.test()
async def sw_test(dut: CpuTop):
    """sw $3, 0($1)：把 R3 写到地址 8。"""
    await run_one_instruction(
        dut,
        sw(rt=3, offset=0, base=1),
        registers={1: 8, 3: 0x1122_3344},  # R1 = 地址 8，R3 = 数据
        memory={2: 0},                     # 地址 8 -> mem[2]
    )

    assert read_mem(dut, 2) == 0x1122_3344
    assert read_pc(dut) == 4
