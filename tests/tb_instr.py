"""
指令级测试：把一段机器码装进 CPU，跑几个周期，然后检查结果。

覆盖当前冻结 ISA：
  addu / addiu / lw / sw / beq / j / jal / jr

每个测试的写法都很像：
  1. 准备机器码（必要时预置寄存器/内存）
  2. 调用 run_program(...) 装载、复位、运行
  3. 用 assert 检查寄存器/内存

机器码含义写在注释里，方便对照 MIPS 编码。
"""

import os

import cocotb

from cocotb_utils import run_program

# 程序装载测试的等待周期数；mycup prog 可以通过环境变量覆盖
PROGRAM_CYCLES = int(os.environ.get("MYCUP_PROG_CYCLES", "4"))

# --------------------------------------------------------------------------- #
# 机器码（大端 MIPS）
# --------------------------------------------------------------------------- #
ADDIU_R1_R0_8   = 0x24010008  # addiu $1, $0, 8
ADDIU_R2_R0_8   = 0x24020008  # addiu $2, $0, 8
ADDIU_R2_R0_5   = 0x24020005  # addiu $2, $0, 5
ADDIU_R2_R0_9   = 0x24020009  # addiu $2, $0, 9
ADDIU_R2_R0_NEG = 0x2402FFFF  # addiu $2, $0, -1
ADDIU_R3_R0_99  = 0x24030063  # addiu $3, $0, 99
ADDIU_R4_R0_7   = 0x24040007  # addiu $4, $0, 7
ADDIU_R4_R0_99  = 0x24040063  # addiu $4, $0, 99
ADDIU_R5_R0_7   = 0x24050007  # addiu $5, $0, 7
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
    """addu $3, $1, $2：5 + 3 = 8。"""
    await run_program(
        dut,
        instructions=[ADDU_R3_R1_R2],
        registers={1: 5, 2: 3},
    )

    assert int(dut.u_regfile.regs[3].value) == 8


@cocotb.test()
async def addiu_test(dut):
    """addiu：正数立即数 + 负数立即数（验证符号扩展）。"""
    await run_program(
        dut,
        instructions=[ADDIU_R1_R0_8, ADDIU_R2_R0_NEG],
    )

    assert int(dut.u_regfile.regs[1].value) == 8
    assert int(dut.u_regfile.regs[2].value) == 0xFFFF_FFFF


# --------------------------------------------------------------------------- #
# 分支 / 跳转
# --------------------------------------------------------------------------- #
@cocotb.test()
async def beq_taken_test(dut):
    """beq 成立：跳过紧接着的一条指令。"""
    await run_program(
        dut,
        instructions=[
            ADDIU_R1_R0_8,    # R1 = 8
            ADDIU_R2_R0_8,    # R2 = 8
            BEQ_R1_R2_2,      # 相等 -> 跳到 PC+8（跳过下一条）
            ADDIU_R3_R0_99,   # 这条应该被跳过
            ADDIU_R4_R0_7,    # 跳到这里
        ],
        registers={3: 0, 4: 0},  # 先清零，才能判断“是否被跳过”
    )

    assert int(dut.u_regfile.regs[3].value) == 0, "被跳过的指令不应执行"
    assert int(dut.u_regfile.regs[4].value) == 7, "跳转目标应该执行"


@cocotb.test()
async def beq_not_taken_test(dut):
    """beq 不成立：顺序执行下一条指令。"""
    await run_program(
        dut,
        instructions=[
            ADDIU_R1_R0_8,    # R1 = 8
            ADDIU_R2_R0_9,    # R2 = 9（不相等）
            BEQ_R1_R2_2,
            ADDIU_R3_R0_99,   # 这条应该执行
            ADDIU_R4_R0_7,
        ],
    )

    assert int(dut.u_regfile.regs[3].value) == 99, "分支不成立时应该顺序执行"
    assert int(dut.u_regfile.regs[4].value) == 7


@cocotb.test()
async def j_test(dut):
    """j 2：直接跳到地址 8（跳过 mem[1]）。"""
    await run_program(
        dut,
        instructions=[
            J_2,              # 跳到地址 8
            ADDIU_R3_R0_99,   # 被跳过
            ADDIU_R4_R0_7,    # 目标
        ],
        registers={3: 0, 4: 0},  # 先清零，才能判断“是否被跳过”
    )

    assert int(dut.u_regfile.regs[3].value) == 0
    assert int(dut.u_regfile.regs[4].value) == 7


@cocotb.test()
async def jal_test(dut):
    """jal 3：跳到地址 12，同时把返回地址（4）写进 $31。"""
    await run_program(
        dut,
        instructions=[
            JAL_3,            # 跳转并链接
            ADDIU_R3_R0_99,   # 被跳过
            ADDIU_R4_R0_99,   # 被跳过
            ADDIU_R5_R0_7,    # 目标
        ],
        registers={3: 0, 4: 0, 5: 0},  # 先清零，才能判断“是否被跳过”
    )

    assert int(dut.u_regfile.regs[31].value) == 4, "$31 应该保存返回地址"
    assert int(dut.u_regfile.regs[3].value) == 0
    assert int(dut.u_regfile.regs[4].value) == 0
    assert int(dut.u_regfile.regs[5].value) == 7


@cocotb.test()
async def jr_test(dut):
    """jr $1：跳到 R1 里的地址（8，即 mem[2]）。"""
    await run_program(
        dut,
        instructions=[
            JR_R1,            # 跳到 R1
            ADDIU_R3_R0_99,   # 被跳过
            ADDIU_R4_R0_7,    # 目标
        ],
        registers={1: 8, 3: 0, 4: 0},  # R1 = 8；R3/R4 先清零用于判断跳过
    )

    assert int(dut.u_regfile.regs[3].value) == 0
    assert int(dut.u_regfile.regs[4].value) == 7


# --------------------------------------------------------------------------- #
# 访存
# --------------------------------------------------------------------------- #
@cocotb.test()
async def lw_sw_test(dut):
    """sw 写内存，lw 再读回来。"""
    await run_program(
        dut,
        instructions=[SW_R3_0_R1, LW_R2_0_R1],
        registers={1: 8, 3: 0x1122_3344},  # R1 = 地址 8；R3 = 要写的数据
        memory={2: 0},                     # mem[2] 对应地址 8
    )

    assert int(dut.u_datam.mem[2].value) == 0x1122_3344, "内存应该被写入"
    assert int(dut.u_regfile.regs[2].value) == 0x1122_3344, "lw 应该读回同一个值"


# --------------------------------------------------------------------------- #
# 程序装载（+instr= plusarg）
# --------------------------------------------------------------------------- #
@cocotb.test()
async def prog_demo_test(dut):
    """用 programs/demo.hex 验证 $readmemh 程序装载。

    这个测试需要 pytest 包装层传入 +instr=<绝对路径>；
    程序本身在仿真开始前由 instrm 的 $readmemh 装入。
    """
    # instructions 传空：不要覆盖 $readmemh 已经装好的程序
    await run_program(dut, instructions=[], extra_cycles=PROGRAM_CYCLES)

    # demo.hex: addiu $1,8; addiu $2,5; addu $3,$1,$2
    assert int(dut.u_regfile.regs[1].value) == 8
    assert int(dut.u_regfile.regs[2].value) == 5
    assert int(dut.u_regfile.regs[3].value) == 13
