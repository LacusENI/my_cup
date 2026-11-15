"""npc（下一 PC）的单元测试。

cocotb 用例和 pytest 入口在同一个文件里，由 ``@cocotb_test`` 连接。
详细机制见 ``tests/utils/cocotb_utils.py`` 的 ``cocotb_test``。

npc 是纯组合逻辑：
  根据当前 PC、NPC 类型、分支条件和偏移，算出 PC+4 与 next_pc。

当前语义：
  PC+4    : next_pc = inst_pc + 4
  BRANCH  : taken ? inst_pc + pc_offset : inst_pc + 4
  JAL     : inst_pc + pc_offset
  JALR    : jalr_target & ~1

停机时 PC 由 ``pc.stall`` 保持，NPC 不参与停机判断。
"""

from typing import Protocol

from utils.cocotb_utils import Signal, assert_fields, cocotb_test, settle
from utils.cpu_pkg import NPC_BRANCH, NPC_JAL, NPC_JALR, NPC_PLUS4


# conftest.py 里的 session fixture 名。
SIM = "npc_sim"


class NpcDut(Protocol):
    inst_pc: Signal
    npc_op: Signal
    branch_taken: Signal
    pc_offset: Signal
    jalr_target: Signal
    pc_plus4: Signal
    pc_plus_imm: Signal
    target_addr_err: Signal
    next_pc: Signal


REQUIRED_FIELDS = (
    "inst_pc",
    "npc_op",
    "branch_taken",
    "pc_offset",
    "jalr_target",
    "pc_plus4",
    "pc_plus_imm",
    "target_addr_err",
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
) -> None:
    dut.inst_pc.value = inst_pc
    dut.npc_op.value = npc_op
    dut.branch_taken.value = branch_taken
    dut.pc_offset.value = pc_offset
    dut.jalr_target.value = jalr_target
    await settle()


@cocotb_test(dut=SIM)
async def test_contract(dut: NpcDut):
    """契约：npc 暴露新接口的所有字段。"""
    assert_fields(dut, REQUIRED_FIELDS, "npc")


@cocotb_test(dut=SIM)
async def test_npc_plus4(dut: NpcDut):
    """普通顺序执行：PC+4。"""
    await drive(dut, inst_pc=0x0000_0010, npc_op=NPC_PLUS4)

    assert int(dut.pc_plus4.value) == 0x0000_0014
    assert int(dut.next_pc.value) == 0x0000_0014


@cocotb_test(dut=SIM)
async def test_npc_branch_taken(dut: NpcDut):
    """beq 成立：PC = PC + 字节偏移。"""
    await drive(
        dut,
        inst_pc=0x0000_0100,
        npc_op=NPC_BRANCH,
        branch_taken=1,
        pc_offset=0x10,
    )

    assert int(dut.next_pc.value) == 0x0000_0110


@cocotb_test(dut=SIM)
async def test_npc_branch_not_taken(dut: NpcDut):
    """beq 不成立：仍然 PC+4。"""
    await drive(
        dut,
        inst_pc=0x0000_0100,
        npc_op=NPC_BRANCH,
        branch_taken=0,
        pc_offset=0x10,
    )

    assert int(dut.next_pc.value) == 0x0000_0104


@cocotb_test(dut=SIM)
async def test_npc_branch_backward(dut: NpcDut):
    """负偏移：向后跳。"""
    await drive(
        dut,
        inst_pc=0x0000_0100,
        npc_op=NPC_BRANCH,
        branch_taken=1,
        pc_offset=0xFFFF_FFF0,  # -16
    )

    assert int(dut.next_pc.value) == 0x0000_00F0


@cocotb_test(dut=SIM)
async def test_npc_jal(dut: NpcDut):
    """jal：PC = PC + 字节偏移；同时 pc_plus4 用于 link。"""
    await drive(dut, inst_pc=0x0000_0100, npc_op=NPC_JAL, pc_offset=0x20)

    assert int(dut.pc_plus4.value) == 0x0000_0104
    assert int(dut.pc_plus_imm.value) == 0x0000_0120
    assert int(dut.next_pc.value) == 0x0000_0120


@cocotb_test(dut=SIM)
async def test_npc_jalr(dut: NpcDut):
    """jalr：目标 = (rs1 + imm) & ~1。"""
    await drive(
        dut,
        inst_pc=0x0000_0100,
        npc_op=NPC_JALR,
        jalr_target=0x1234_5679,
    )

    assert int(dut.pc_plus4.value) == 0x0000_0104
    assert int(dut.next_pc.value) == 0x1234_5678


@cocotb_test(dut=SIM)
async def test_npc_target_addr_err(dut: NpcDut):
    """branch/jal/jalr 目标 bit1 非零时置 target_addr_err。"""
    cases = [
        (NPC_JAL, 0, 2, 0),
        (NPC_BRANCH, 1, 2, 0),
        (NPC_BRANCH, 0, 2, 0),
        (NPC_JALR, 0, 0, 2),
    ]
    expected = [1, 1, 0, 1]
    for (op, taken, offset, target), want in zip(cases, expected):
        await drive(
            dut,
            inst_pc=0x0000_0100,
            npc_op=op,
            branch_taken=taken,
            pc_offset=offset,
            jalr_target=target,
        )
        assert int(dut.target_addr_err.value) == want, (
            f"target_addr_err 错误: op={op} taken={taken} "
            f"offset={offset} target={target}"
        )
