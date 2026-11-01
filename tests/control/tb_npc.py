"""
npc（下一 PC）的单元测试。

npc 是纯组合逻辑：
  根据当前 PC、NPC 类型、分支条件和偏移，算出 PC+4 与 next_pc。

本批语义：
  PC+4    : next_pc = inst_pc + 4
  BRANCH  : taken ? inst_pc + pc_offset : inst_pc + 4
  JAL     : inst_pc + pc_offset
  JALR    : jalr_target & ~1
  illegal : next_pc = inst_pc（停止）
"""

from typing import Protocol

import cocotb

from utils.cocotb_utils import Signal, assert_fields, settle


NPC_PLUS4 = 0
NPC_BRANCH = 1
NPC_JAL = 2
NPC_JALR = 3


class NpcDut(Protocol):
    inst_pc: Signal
    npc_op: Signal
    branch_taken: Signal
    pc_offset: Signal
    jalr_target: Signal
    inst_illegal: Signal
    pc_plus4: Signal
    next_pc: Signal


REQUIRED_FIELDS = (
    "inst_pc",
    "npc_op",
    "branch_taken",
    "pc_offset",
    "jalr_target",
    "inst_illegal",
    "pc_plus4",
    "next_pc",
)


async def drive(
    dut: NpcDut,
    *,
    inst_pc: int,
    npc_op: int,
    branch_taken: int = 0,
    pc_offset: int = 0,
    jalr_target: int = 0,
    inst_illegal: int = 0,
) -> None:
    dut.inst_pc.value = inst_pc
    dut.npc_op.value = npc_op
    dut.branch_taken.value = branch_taken
    dut.pc_offset.value = pc_offset
    dut.jalr_target.value = jalr_target
    dut.inst_illegal.value = inst_illegal
    await settle()


@cocotb.test()
async def contract_test(dut: NpcDut):
    """契约：npc 暴露新接口的所有字段。"""
    assert_fields(dut, REQUIRED_FIELDS, "npc")


@cocotb.test()
async def plus4_test(dut: NpcDut):
    """普通顺序执行：PC+4。"""
    await drive(dut, inst_pc=0x0000_0010, npc_op=NPC_PLUS4)

    assert int(dut.pc_plus4.value) == 0x0000_0014
    assert int(dut.next_pc.value) == 0x0000_0014


@cocotb.test()
async def branch_taken_test(dut: NpcDut):
    """beq 成立：PC = PC + 字节偏移。"""
    await drive(
        dut,
        inst_pc=0x0000_0100,
        npc_op=NPC_BRANCH,
        branch_taken=1,
        pc_offset=0x10,
    )

    assert int(dut.next_pc.value) == 0x0000_0110


@cocotb.test()
async def branch_not_taken_test(dut: NpcDut):
    """beq 不成立：仍然 PC+4。"""
    await drive(
        dut,
        inst_pc=0x0000_0100,
        npc_op=NPC_BRANCH,
        branch_taken=0,
        pc_offset=0x10,
    )

    assert int(dut.next_pc.value) == 0x0000_0104


@cocotb.test()
async def branch_backward_test(dut: NpcDut):
    """负偏移：向后跳。"""
    await drive(
        dut,
        inst_pc=0x0000_0100,
        npc_op=NPC_BRANCH,
        branch_taken=1,
        pc_offset=0xFFFF_FFF0,  # -16
    )

    assert int(dut.next_pc.value) == 0x0000_00F0


@cocotb.test()
async def jal_test(dut: NpcDut):
    """jal：PC = PC + 字节偏移；同时 pc_plus4 用于 link。"""
    await drive(dut, inst_pc=0x0000_0100, npc_op=NPC_JAL, pc_offset=0x20)

    assert int(dut.pc_plus4.value) == 0x0000_0104
    assert int(dut.next_pc.value) == 0x0000_0120


@cocotb.test()
async def jalr_test(dut: NpcDut):
    """jalr：目标 = (rs1 + imm) & ~1。"""
    await drive(
        dut,
        inst_pc=0x0000_0100,
        npc_op=NPC_JALR,
        jalr_target=0x1234_5679,
    )

    assert int(dut.pc_plus4.value) == 0x0000_0104
    assert int(dut.next_pc.value) == 0x1234_5678


@cocotb.test()
async def illegal_hold_test(dut: NpcDut):
    """非法指令优先级最高：PC 保持，不执行 JAL/BRANCH/JALR。"""
    for op in (NPC_BRANCH, NPC_JAL, NPC_JALR):
        await drive(
            dut,
            inst_pc=0x0000_0200,
            npc_op=op,
            branch_taken=1,
            pc_offset=0x40,
            jalr_target=0x0000_0300,
            inst_illegal=1,
        )
        assert int(dut.next_pc.value) == 0x0000_0200, f"npc_op={op} 时不应跳转"
