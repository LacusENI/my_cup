"""ctrl（控制器）的单元测试。

cocotb 用例和 pytest 入口在同一个文件里，由 ``@cocotb_test`` 连接。
详细机制见 ``tests/utils/cocotb_utils.py`` 的 ``cocotb_test``。

ctrl 是纯组合逻辑：输入 opcode/funct3/funct7 和 valid_encoding，
输出打包好的 ctrl_t。测试通过 test-only probe 观察扁平化字段。
"""

from typing import Protocol

from utils.assembler import assemble
from utils.cocotb_utils import Signal, assert_fields, cocotb_test, settle
from utils.cpu_pkg import (
    ALU_ADD,
    ALU_EQ,
    ALU_NOP,
    NPC_BRANCH,
    NPC_JAL,
    NPC_JALR,
    NPC_PLUS4,
    SRC2_SEL_IMM,
    SRC2_SEL_RS2,
    WB_SEL_ALU_OUT,
    WB_SEL_IMM,
    WB_SEL_PC_PLUS4,
    WB_SEL_PC_PLUS_IMM,
    WB_SEL_R_DATA,
)


# conftest.py 里的 session fixture 名。
SIM = "ctrl_sim"


class CtrlDut(Protocol):
    opcode: Signal
    funct3: Signal
    funct7: Signal
    valid_encoding: Signal
    npc_op: Signal
    reg_write: Signal
    alu_op: Signal
    mem_read: Signal
    mem_write: Signal
    wb_sel: Signal
    src2_sel: Signal
    inst_illegal: Signal


REQUIRED_FIELDS = (
    "opcode",
    "funct3",
    "funct7",
    "valid_encoding",
    "npc_op",
    "reg_write",
    "alu_op",
    "mem_read",
    "mem_write",
    "wb_sel",
    "src2_sel",
    "inst_illegal",
)


async def drive(
    dut: CtrlDut, *, opcode: int, funct3: int, funct7: int = 0, valid: int = 1
) -> None:
    dut.opcode.value = opcode
    dut.funct3.value = funct3
    dut.funct7.value = funct7
    dut.valid_encoding.value = valid
    await settle()


async def drive_asm(dut: CtrlDut, text: str) -> None:
    """用真实指令编码驱动 ctrl，避免在测试里手写 opcode/funct3。"""
    word = assemble(text)
    await drive(
        dut,
        opcode=word & 0x7F,
        funct3=(word >> 12) & 0x7,
        funct7=(word >> 25) & 0x7F,
    )


@cocotb_test(dut=SIM)
async def test_contract(dut: CtrlDut):
    """契约：ctrl_probe 暴露所有控制字段。"""
    assert_fields(dut, REQUIRED_FIELDS, "ctrl_probe")


@cocotb_test(dut=SIM)
async def test_add_control(dut: CtrlDut):
    """add：ALU 加法，写回 rd，PC+4。"""
    await drive_asm(dut, "add x1, x2, x3")

    assert int(dut.reg_write.value) == 1
    assert int(dut.alu_op.value) == ALU_ADD
    assert int(dut.src2_sel.value) == SRC2_SEL_RS2
    assert int(dut.wb_sel.value) == WB_SEL_ALU_OUT
    assert int(dut.npc_op.value) == NPC_PLUS4
    assert int(dut.mem_read.value) == 0
    assert int(dut.mem_write.value) == 0
    assert int(dut.inst_illegal.value) == 0


@cocotb_test(dut=SIM)
async def test_addi_control(dut: CtrlDut):
    """addi：ALU 加法，第二操作数是立即数，写回 rd。"""
    await drive_asm(dut, "addi x1, x0, 8")

    assert int(dut.reg_write.value) == 1
    assert int(dut.alu_op.value) == ALU_ADD
    assert int(dut.src2_sel.value) == SRC2_SEL_IMM
    assert int(dut.wb_sel.value) == WB_SEL_ALU_OUT
    assert int(dut.npc_op.value) == NPC_PLUS4
    assert int(dut.inst_illegal.value) == 0


@cocotb_test(dut=SIM)
async def test_beq_control(dut: CtrlDut):
    """beq：ALU 相等比较，分支 NPC，不写寄存器/内存。"""
    await drive_asm(dut, "beq x1, x2, 8")

    assert int(dut.npc_op.value) == NPC_BRANCH
    assert int(dut.alu_op.value) == ALU_EQ
    assert int(dut.src2_sel.value) == SRC2_SEL_RS2
    assert int(dut.reg_write.value) == 0
    assert int(dut.mem_read.value) == 0
    assert int(dut.mem_write.value) == 0
    assert int(dut.inst_illegal.value) == 0


@cocotb_test(dut=SIM)
async def test_lw_control(dut: CtrlDut):
    """lw：地址 = rs1 + imm，读内存，写回 rd。"""
    await drive_asm(dut, "lw x1, 0(x2)")

    assert int(dut.reg_write.value) == 1
    assert int(dut.alu_op.value) == ALU_ADD
    assert int(dut.src2_sel.value) == SRC2_SEL_IMM
    assert int(dut.mem_read.value) == 1
    assert int(dut.mem_write.value) == 0
    assert int(dut.wb_sel.value) == WB_SEL_R_DATA
    assert int(dut.npc_op.value) == NPC_PLUS4


@cocotb_test(dut=SIM)
async def test_sw_control(dut: CtrlDut):
    """sw：地址 = rs1 + imm，写内存，不写寄存器。"""
    await drive_asm(dut, "sw x1, 0(x2)")

    assert int(dut.reg_write.value) == 0
    assert int(dut.alu_op.value) == ALU_ADD
    assert int(dut.src2_sel.value) == SRC2_SEL_IMM
    assert int(dut.mem_read.value) == 0
    assert int(dut.mem_write.value) == 1
    assert int(dut.npc_op.value) == NPC_PLUS4


@cocotb_test(dut=SIM)
async def test_jal_control(dut: CtrlDut):
    """jal：PC+4 写回 rd，跳到 PC+offset。"""
    await drive_asm(dut, "jal x1, 8")

    assert int(dut.npc_op.value) == NPC_JAL
    assert int(dut.reg_write.value) == 1
    assert int(dut.alu_op.value) == ALU_NOP
    assert int(dut.wb_sel.value) == WB_SEL_PC_PLUS4
    assert int(dut.mem_read.value) == 0
    assert int(dut.mem_write.value) == 0


@cocotb_test(dut=SIM)
async def test_jalr_control(dut: CtrlDut):
    """jalr：ALU 计算 rs1+imm，PC+4 写回 rd，跳到寄存器目标。"""
    await drive_asm(dut, "jalr x1, 0(x2)")

    assert int(dut.npc_op.value) == NPC_JALR
    assert int(dut.reg_write.value) == 1
    assert int(dut.alu_op.value) == ALU_ADD
    assert int(dut.src2_sel.value) == SRC2_SEL_IMM
    assert int(dut.wb_sel.value) == WB_SEL_PC_PLUS4
    assert int(dut.mem_read.value) == 0
    assert int(dut.mem_write.value) == 0


@cocotb_test(dut=SIM)
async def test_lui_control(dut: CtrlDut):
    """lui：U 型立即数直接写回 rd，PC+4。"""
    await drive_asm(dut, "lui x1, 0x12345")

    assert int(dut.reg_write.value) == 1
    assert int(dut.alu_op.value) == ALU_NOP
    assert int(dut.src2_sel.value) == SRC2_SEL_IMM
    assert int(dut.wb_sel.value) == WB_SEL_IMM
    assert int(dut.npc_op.value) == NPC_PLUS4
    assert int(dut.mem_read.value) == 0
    assert int(dut.mem_write.value) == 0
    assert int(dut.inst_illegal.value) == 0


@cocotb_test(dut=SIM)
async def test_auipc_control(dut: CtrlDut):
    """auipc：PC + U 型立即数写回 rd，PC+4。"""
    await drive_asm(dut, "auipc x1, 0x12345")

    assert int(dut.reg_write.value) == 1
    assert int(dut.alu_op.value) == ALU_NOP
    assert int(dut.src2_sel.value) == SRC2_SEL_IMM
    assert int(dut.wb_sel.value) == WB_SEL_PC_PLUS_IMM
    assert int(dut.npc_op.value) == NPC_PLUS4
    assert int(dut.mem_read.value) == 0
    assert int(dut.mem_write.value) == 0
    assert int(dut.inst_illegal.value) == 0


@cocotb_test(dut=SIM)
async def test_illegal_control(dut: CtrlDut):
    """非法编码：inst_illegal=1，不写寄存器/内存，ALU/NPC 安全默认。"""
    await drive(dut, opcode=0, funct3=0, valid=0)

    assert int(dut.inst_illegal.value) == 1
    assert int(dut.reg_write.value) == 0
    assert int(dut.mem_read.value) == 0
    assert int(dut.mem_write.value) == 0
    assert int(dut.alu_op.value) == ALU_NOP
    assert int(dut.npc_op.value) == NPC_PLUS4
    assert int(dut.wb_sel.value) == WB_SEL_ALU_OUT
    assert int(dut.src2_sel.value) == SRC2_SEL_RS2
