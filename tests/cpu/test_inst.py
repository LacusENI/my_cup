"""ISA 级测试：每个用例只执行一条 RV32I 指令。

cocotb 用例和 pytest 入口在同一个文件里，由 ``@cocotb_test`` 连接。
详细机制见 ``tests/utils/cocotb_utils.py`` 的 ``cocotb_test``。

只断言架构状态：
  - PC（下一条指令地址）
  - 通用寄存器
  - 数据内存
  - inst_illegal

不读内部数据通路信号，也不依赖实现细节。
分支/跳转只断言 PC，不执行目标指令。
"""

from typing import Protocol

from utils.assembler import assemble
from utils.cocotb_utils import (
    CpuAccess,
    Signal,
    assert_fields,
    cocotb_test,
    read_mem,
    read_pc,
    read_reg,
    read_reg_raw,
    reset_and_wait,
    run_one_instruction,
    settle,
    start_clock,
    wait_cycles,
    write_inst,
    write_mem,
    write_reg,
)


# conftest.py 里的 session fixture 名。
SIM = "cpu_sim"


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
    "u_instm.mem",
    "u_datam.mem",
)


@cocotb_test(dut=SIM)
async def test_contract(dut: CpuTop):
    """契约：cpu_top 暴露测试依赖的架构状态和 inst_illegal。"""
    assert_fields(dut, CPU_TOP_FIELDS, "cpu_top")


# --------------------------------------------------------------------------- #
# 算术
# --------------------------------------------------------------------------- #
@cocotb_test(dut=SIM)
async def test_add(dut: CpuTop):
    """add x3, x1, x2：5 + 3 = 8，PC 前进到 4。"""
    await run_one_instruction(
        dut,
        assemble("add x3, x1, x2"),
        registers={1: 5, 2: 3},
    )

    assert read_reg(dut, 3) == 8
    assert read_pc(dut) == 4


@cocotb_test(dut=SIM)
async def test_add_wrap(dut: CpuTop):
    """add 是 32 位回绕：0xFFFFFFFF + 1 = 0。"""
    await run_one_instruction(
        dut,
        assemble("add x3, x1, x2"),
        registers={1: 0xFFFF_FFFF, 2: 1},
    )

    assert read_reg(dut, 3) == 0
    assert read_pc(dut) == 4


@cocotb_test(dut=SIM)
async def test_addi_positive(dut: CpuTop):
    """addi x1, x0, 8：正数立即数。"""
    await run_one_instruction(dut, assemble("addi x1, x0, 8"))

    assert read_reg(dut, 1) == 8
    assert read_pc(dut) == 4


@cocotb_test(dut=SIM)
async def test_addi_negative(dut: CpuTop):
    """addi x2, x0, -1：验证 12 位立即数符号扩展。"""
    await run_one_instruction(dut, assemble("addi x2, x0, -1"))

    assert read_reg(dut, 2) == 0xFFFF_FFFF
    assert read_pc(dut) == 4


@cocotb_test(dut=SIM)
async def test_addi_x0(dut: CpuTop):
    """写 x0 必须被丢弃。"""
    await run_one_instruction(dut, assemble("addi x0, x0, 8"), registers={0: 0})

    assert read_reg_raw(dut, 0) == 0
    assert read_pc(dut) == 4


# --------------------------------------------------------------------------- #
# 分支
# --------------------------------------------------------------------------- #
@cocotb_test(dut=SIM)
async def test_beq_taken(dut: CpuTop):
    """beq 成立：PC = 0 + 8 = 8。"""
    await run_one_instruction(
        dut,
        assemble("beq x1, x2, 8"),
        registers={1: 8, 2: 8},
    )

    assert read_pc(dut) == 8


@cocotb_test(dut=SIM)
async def test_beq_not_taken(dut: CpuTop):
    """beq 不成立：PC = 4。"""
    await run_one_instruction(
        dut,
        assemble("beq x1, x2, 8"),
        registers={1: 8, 2: 9},
    )

    assert read_pc(dut) == 4


# --------------------------------------------------------------------------- #
# 跳转
# --------------------------------------------------------------------------- #
@cocotb_test(dut=SIM)
async def test_jal(dut: CpuTop):
    """jal x1, 8：PC=8，x1=PC+4=4。"""
    await run_one_instruction(dut, assemble("jal x1, 8"))

    assert read_pc(dut) == 8
    assert read_reg(dut, 1) == 4


@cocotb_test(dut=SIM)
async def test_jal_x0(dut: CpuTop):
    """jal x0, 8：不写 x0。"""
    await run_one_instruction(dut, assemble("jal x0, 8"), registers={0: 0})

    assert read_pc(dut) == 8
    assert read_reg_raw(dut, 0) == 0


@cocotb_test(dut=SIM)
async def test_jalr(dut: CpuTop):
    """jalr x1, 0(x2)：PC=x2=8，x1=4。"""
    await run_one_instruction(
        dut,
        assemble("jalr x1, 0(x2)"),
        registers={2: 8},
    )

    assert read_pc(dut) == 8
    assert read_reg(dut, 1) == 4


@cocotb_test(dut=SIM)
async def test_jalr_rd_equals_rs1(dut: CpuTop):
    """jalr x1, 4(x1)：目标必须用旧的 x1 计算。"""
    await run_one_instruction(
        dut,
        assemble("jalr x1, 4(x1)"),
        registers={1: 8},
    )

    assert read_pc(dut) == 12
    assert read_reg(dut, 1) == 4


@cocotb_test(dut=SIM)
async def test_jalr_x0(dut: CpuTop):
    """jalr x0, 0(x2)：不写 x0。"""
    await run_one_instruction(
        dut,
        assemble("jalr x0, 0(x2)"),
        registers={0: 0, 2: 8},
    )

    assert read_pc(dut) == 8
    assert read_reg_raw(dut, 0) == 0


# --------------------------------------------------------------------------- #
# 访存
# --------------------------------------------------------------------------- #
@cocotb_test(dut=SIM)
async def test_lw(dut: CpuTop):
    """lw x2, 0(x1)：从地址 8 读一个字到 x2。"""
    await run_one_instruction(
        dut,
        assemble("lw x2, 0(x1)"),
        registers={1: 8},
        memory={2: 0x1122_3344},
    )

    assert read_reg(dut, 2) == 0x1122_3344
    assert read_pc(dut) == 4


@cocotb_test(dut=SIM)
async def test_lw_negative_offset(dut: CpuTop):
    """lw x2, -4(x1)：负偏移地址计算。"""
    await run_one_instruction(
        dut,
        assemble("lw x2, -4(x1)"),
        registers={1: 8},
        memory={1: 0xAABB_CCDD},
    )

    assert read_reg(dut, 2) == 0xAABB_CCDD
    assert read_pc(dut) == 4


@cocotb_test(dut=SIM)
async def test_sw(dut: CpuTop):
    """sw x3, 0(x1)：把 x3 写到地址 8，不写寄存器。"""
    await run_one_instruction(
        dut,
        assemble("sw x3, 0(x1)"),
        registers={1: 8, 3: 0x1122_3344},
        memory={2: 0},
    )

    assert read_mem(dut, 2) == 0x1122_3344
    assert read_reg(dut, 3) == 0x1122_3344
    assert read_pc(dut) == 4


@cocotb_test(dut=SIM)
async def test_sw_negative_offset(dut: CpuTop):
    """sw x3, -4(x1)：负偏移地址计算。"""
    await run_one_instruction(
        dut,
        assemble("sw x3, -4(x1)"),
        registers={1: 8, 3: 0x5566_7788},
        memory={1: 0},
    )

    assert read_mem(dut, 1) == 0x5566_7788
    assert read_pc(dut) == 4


# --------------------------------------------------------------------------- #
# 复位
# --------------------------------------------------------------------------- #
@cocotb_test(dut=SIM)
async def test_reset_write_suppression(dut: CpuTop):
    """复位沿不能提交寄存器写或存储写。

    程序：
      0: addi x1, x1, 1
      4: sw   x1, 0(x0)
      8: jal  x0, -8        # 回到 0

    先在 PC=0 拉复位，检查 x1 不变；再在 PC=4 拉复位，检查内存不变。
    """
    await start_clock(dut)
    write_reg(dut, 1, 0)
    write_mem(dut, 0, 0)
    write_inst(dut, 0, assemble("addi x1, x1, 1"))
    write_inst(dut, 1, assemble("sw x1, 0(x0)"))
    write_inst(dut, 2, assemble("jal x0, -8"))

    await reset_and_wait(dut)

    # 跑完一圈，回到 PC=0；此时 x1=1，mem[0]=1
    await wait_cycles(dut, 3)
    await settle()
    assert read_pc(dut) == 0
    assert read_reg(dut, 1) == 1
    assert read_mem(dut, 0) == 1

    # PC=0 时复位：不应再执行 addi
    dut.rst.value = 1
    await wait_cycles(dut, 1)
    await settle()
    assert read_pc(dut) == 0
    assert read_reg(dut, 1) == 1
    assert read_mem(dut, 0) == 1

    # 释放复位，执行 addi 到 PC=4；此时 x1=2，mem[0] 仍为 1
    dut.rst.value = 0
    await wait_cycles(dut, 1)
    await settle()
    assert read_pc(dut) == 4
    assert read_reg(dut, 1) == 2
    assert read_mem(dut, 0) == 1

    # PC=4 时复位：不应执行 sw
    dut.rst.value = 1
    await wait_cycles(dut, 1)
    await settle()
    assert read_pc(dut) == 0
    assert read_reg(dut, 1) == 2
    assert read_mem(dut, 0) == 1

    dut.rst.value = 0


# --------------------------------------------------------------------------- #
# 非法指令
# --------------------------------------------------------------------------- #
@cocotb_test(dut=SIM)
async def test_illegal_stop(dut: CpuTop):
    """非法编码：PC 保持，寄存器/内存都不改变。"""
    # sub x3, x1, x2 的 funct7=0x20；当前只实现 add。
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
