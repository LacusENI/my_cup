"""
npc（下一 PC）的单元测试。

npc 是纯组合逻辑：
  根据“当前 PC + 跳转类型 + 条件 + 目标/偏移”，算出下一条指令的地址。
  没有时钟，也不需要复位。

四种情况：
  NPC_OP_PLUS4  : 正常顺序执行，PC = PC + 4
  NPC_OP_BRANCH : 条件分支，PC = PC + (offset << 2)
  NPC_OP_DIRECT : j / jal，目标地址 = {PC[31:28], instr_index, 2'b00}
  NPC_OP_RA     : jr，PC = 寄存器里的地址
"""

import cocotb

from cocotb_utils import settle

# 与 cpu_pkg.sv 保持一致
NPC_OP_PLUS4  = 0b00
NPC_OP_BRANCH = 0b01
NPC_OP_DIRECT = 0b10
NPC_OP_RA     = 0b11


@cocotb.test()
async def plus4_test(dut):
    """普通情况：下一条指令在旁边，PC = PC + 4。"""
    dut.curr_pc.value = 0x0000_0010
    dut.npc_op.value = NPC_OP_PLUS4
    dut.cond_jmp.value = 0
    await settle()

    assert int(dut.pc_plus4.value) == 0x0000_0014, "PC+4 应该是 0x14"
    assert int(dut.next_pc.value) == 0x0000_0014, "默认下一条就是 PC+4"


@cocotb.test()
async def branch_taken_test(dut):
    """beq 成立：PC = PC + (offset << 2)。"""
    dut.curr_pc.value = 0x0000_0100
    dut.npc_op.value = NPC_OP_BRANCH
    dut.cond_jmp.value = 1          # 条件成立
    dut.jmp_offset.value = 0x0004   # 偏移 4 条指令 = 16 字节
    await settle()

    # 0x100 + (0x0004 << 2) = 0x100 + 0x10 = 0x110
    assert int(dut.next_pc.value) == 0x0000_0110, "分支成立应该跳到 0x110"


@cocotb.test()
async def branch_not_taken_test(dut):
    """beq 不成立：即使给了偏移，也还是 PC + 4。"""
    dut.curr_pc.value = 0x0000_0100
    dut.npc_op.value = NPC_OP_BRANCH
    dut.cond_jmp.value = 0          # 条件不成立
    dut.jmp_offset.value = 0x0004
    await settle()

    assert int(dut.next_pc.value) == 0x0000_0104, "分支不成立就顺序执行"


@cocotb.test()
async def branch_backward_test(dut):
    """向后跳：offset 是负数时，要正确做符号扩展。"""
    dut.curr_pc.value = 0x0000_0100
    dut.npc_op.value = NPC_OP_BRANCH
    dut.cond_jmp.value = 1
    dut.jmp_offset.value = 0xFFFC   # 16 位补码，等于 -4 条指令
    await settle()

    # -4 条指令 = -16 字节；0x100 - 0x10 = 0x0F0
    assert int(dut.next_pc.value) == 0x0000_00F0, "负偏移应该向回跳"


@cocotb.test()
async def direct_jump_test(dut):
    """j / jal：目标地址由 PC 高 4 位和 26 位 instr_index 拼出来。"""
    dut.curr_pc.value = 0x8000_0000
    dut.npc_op.value = NPC_OP_DIRECT
    dut.jmp_target.value = 0x000010  # 26 位目标
    await settle()

    # {0x8, 0x000010, 2'b00} = 0x8000_0040
    assert int(dut.next_pc.value) == 0x8000_0040, "直接跳转地址拼接错误"


@cocotb.test()
async def jump_register_test(dut):
    """jr：直接跳到寄存器里的地址。"""
    dut.npc_op.value = NPC_OP_RA
    dut.ra.value = 0x1234_5678
    await settle()

    assert int(dut.next_pc.value) == 0x1234_5678, "jr 应该使用寄存器地址"
