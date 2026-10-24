"""
ISA 级测试：**每个用例只执行一条指令**。

只断言架构状态：
  - PC（下一条指令地址）
  - 通用寄存器
  - 数据内存

不读内部流水线信号，也不依赖“跑几个周期”。
分支/跳转只断言 PC，不执行目标指令——目标指令属于 program 测试。

机器码含义写在注释里，方便对照 MIPS 编码。
"""

import cocotb

from cocotb_utils import run_one_instruction

# --------------------------------------------------------------------------- #
# 机器码（大端 MIPS）
# --------------------------------------------------------------------------- #
ADDIU_R1_R0_8   = 0x24010008  # addiu $1, $0, 8
ADDIU_R2_R0_NEG = 0x2402FFFF  # addiu $2, $0, -1
ADDU_R3_R1_R2   = 0x00221821  # addu  $3, $1, $2
BEQ_R1_R2_2     = 0x10220002  # beq   $1, $2, 2
J_2             = 0x08000002  # j     2
JAL_3           = 0x0C000003  # jal   3
JR_R1           = 0x00200008  # jr    $1
SW_R3_0_R1      = 0xAC230000  # sw    $3, 0($1)
LW_R2_0_R1      = 0x8C220000  # lw    $2, 0($1)


# --------------------------------------------------------------------------- #
# 算术 / 逻辑
# --------------------------------------------------------------------------- #
@cocotb.test()
async def addu_test(dut):
    """addu $3, $1, $2：5 + 3 = 8；PC 应该前进到 4。"""
    await run_one_instruction(
        dut,
        ADDU_R3_R1_R2,
        registers={1: 5, 2: 3},
    )

    assert int(dut.u_regfile.regs[3].value) == 8
    assert int(dut.u_pc.curr_pc.value) == 4


@cocotb.test()
async def addiu_positive_test(dut):
    """addiu $1, $0, 8：正数立即数。"""
    await run_one_instruction(dut, ADDIU_R1_R0_8)

    assert int(dut.u_regfile.regs[1].value) == 8
    assert int(dut.u_pc.curr_pc.value) == 4


@cocotb.test()
async def addiu_negative_test(dut):
    """addiu $2, $0, -1：验证符号扩展。"""
    await run_one_instruction(dut, ADDIU_R2_R0_NEG)

    assert int(dut.u_regfile.regs[2].value) == 0xFFFF_FFFF
    assert int(dut.u_pc.curr_pc.value) == 4


# --------------------------------------------------------------------------- #
# 分支 / 跳转：只断言 PC
# --------------------------------------------------------------------------- #
@cocotb.test()
async def beq_taken_test(dut):
    """beq 成立：PC = 0 + (2 << 2) = 8。"""
    await run_one_instruction(
        dut,
        BEQ_R1_R2_2,
        registers={1: 8, 2: 8},   # 相等
    )

    assert int(dut.u_pc.curr_pc.value) == 8


@cocotb.test()
async def beq_not_taken_test(dut):
    """beq 不成立：PC = 4。"""
    await run_one_instruction(
        dut,
        BEQ_R1_R2_2,
        registers={1: 8, 2: 9},   # 不相等
    )

    assert int(dut.u_pc.curr_pc.value) == 4


@cocotb.test()
async def j_test(dut):
    """j 2：PC = 2 << 2 = 8。"""
    await run_one_instruction(dut, J_2)

    assert int(dut.u_pc.curr_pc.value) == 8


@cocotb.test()
async def jal_test(dut):
    """jal 3：PC = 12，同时 $31 = PC+4 = 4。"""
    await run_one_instruction(dut, JAL_3)

    assert int(dut.u_pc.curr_pc.value) == 12
    assert int(dut.u_regfile.regs[31].value) == 4


@cocotb.test()
async def jr_test(dut):
    """jr $1：PC = R1 = 8。"""
    await run_one_instruction(dut, JR_R1, registers={1: 8})

    assert int(dut.u_pc.curr_pc.value) == 8


# --------------------------------------------------------------------------- #
# 访存：只断言寄存器 / 内存 / PC
# --------------------------------------------------------------------------- #
@cocotb.test()
async def lw_test(dut):
    """lw $2, 0($1)：从地址 8 读一个字到 R2。"""
    await run_one_instruction(
        dut,
        LW_R2_0_R1,
        registers={1: 8},              # 地址 8 -> mem[2]
        memory={2: 0x1122_3344},       # 预置内存
    )

    assert int(dut.u_regfile.regs[2].value) == 0x1122_3344
    assert int(dut.u_pc.curr_pc.value) == 4


@cocotb.test()
async def sw_test(dut):
    """sw $3, 0($1)：把 R3 写到地址 8。"""
    await run_one_instruction(
        dut,
        SW_R3_0_R1,
        registers={1: 8, 3: 0x1122_3344},  # R1 = 地址 8，R3 = 数据
        memory={2: 0},                     # 地址 8 -> mem[2]
    )

    assert int(dut.u_datam.mem[2].value) == 0x1122_3344
    assert int(dut.u_pc.curr_pc.value) == 4
