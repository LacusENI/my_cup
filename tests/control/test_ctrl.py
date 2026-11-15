"""ctrl（控制器）的单元测试。

cocotb 用例和 pytest 入口在同一个文件里，由 ``@cocotb_test`` 连接。
详细机制见 ``tests/utils/cocotb_utils.py`` 的 ``cocotb_test``。

ctrl 是纯组合逻辑：输入 opcode/funct3/funct7/rd/rs1/funct12，
输出打包好的 ctrl_t。测试通过 test-only probe 观察扁平化字段。

decoder 只负责字段和立即数格式；完整编码合法性在这里验证。
"""

from typing import Protocol

from utils.assembler import assemble
from utils.cocotb_utils import Signal, assert_fields, cocotb_test, settle
from utils.cpu_pkg import (
    ALU_ADD,
    ALU_EQ,
    ALU_NOP,
    HALT_EBREAK,
    HALT_ECALL,
    HALT_ILLEGAL_INST,
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
    rd: Signal
    rs1: Signal
    funct12: Signal
    opcode_err: Signal
    npc_op: Signal
    reg_write: Signal
    alu_op: Signal
    mem_read: Signal
    mem_write: Signal
    wb_sel: Signal
    src2_sel: Signal
    halt: Signal
    halt_cause: Signal


REQUIRED_FIELDS = (
    "opcode",
    "funct3",
    "funct7",
    "rd",
    "rs1",
    "funct12",
    "opcode_err",
    "npc_op",
    "reg_write",
    "alu_op",
    "mem_read",
    "mem_write",
    "wb_sel",
    "src2_sel",
    "halt",
    "halt_cause",
)


def _with_field(word: int, msb: int, lsb: int, value: int) -> int:
    """只修改测试激励中的字段，不参与正式编码。"""
    width = msb - lsb + 1
    mask = (1 << width) - 1
    return (word & ~(mask << lsb)) | ((value & mask) << lsb)


async def drive(
    dut: CtrlDut,
    *,
    opcode: int,
    funct3: int,
    funct7: int = 0,
    rd: int = 0,
    rs1: int = 0,
    funct12: int = 0,
    opcode_err: int = 0,
) -> None:
    dut.opcode.value = opcode
    dut.funct3.value = funct3
    dut.funct7.value = funct7
    dut.rd.value = rd
    dut.rs1.value = rs1
    dut.funct12.value = funct12
    dut.opcode_err.value = opcode_err
    await settle()


async def drive_word(dut: CtrlDut, word: int, *, opcode_err: int = 0) -> None:
    """用完整机器码驱动 ctrl，避免手写字段。"""
    await drive(
        dut,
        opcode=word & 0x7F,
        funct3=(word >> 12) & 0x7,
        funct7=(word >> 25) & 0x7F,
        rd=(word >> 7) & 0x1F,
        rs1=(word >> 15) & 0x1F,
        funct12=(word >> 20) & 0xFFF,
        opcode_err=opcode_err,
    )


async def drive_asm(dut: CtrlDut, text: str) -> None:
    await drive_word(dut, assemble(text))


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
    assert int(dut.halt.value) == 0


@cocotb_test(dut=SIM)
async def test_addi_control(dut: CtrlDut):
    """addi：ALU 加法，第二操作数是立即数，写回 rd。"""
    await drive_asm(dut, "addi x1, x0, 8")

    assert int(dut.reg_write.value) == 1
    assert int(dut.alu_op.value) == ALU_ADD
    assert int(dut.src2_sel.value) == SRC2_SEL_IMM
    assert int(dut.wb_sel.value) == WB_SEL_ALU_OUT
    assert int(dut.npc_op.value) == NPC_PLUS4
    assert int(dut.halt.value) == 0


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
    assert int(dut.halt.value) == 0


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
    assert int(dut.halt.value) == 0


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
    assert int(dut.halt.value) == 0


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
    assert int(dut.halt.value) == 0


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
    assert int(dut.halt.value) == 0


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
    assert int(dut.halt.value) == 0


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
    assert int(dut.halt.value) == 0


@cocotb_test(dut=SIM)
async def test_fence_control(dut: CtrlDut):
    """fence / PAUSE：按 NOP 处理，不写寄存器/内存。"""
    await drive_asm(dut, "fence iorw, iorw")

    assert int(dut.npc_op.value) == NPC_PLUS4
    assert int(dut.reg_write.value) == 0
    assert int(dut.mem_read.value) == 0
    assert int(dut.mem_write.value) == 0
    assert int(dut.halt.value) == 0


@cocotb_test(dut=SIM)
async def test_ecall_control(dut: CtrlDut):
    """ecall：停机，cause=HALT_ECALL。"""
    await drive_asm(dut, "ecall")

    assert int(dut.halt.value) == 1
    assert int(dut.halt_cause.value) == HALT_ECALL
    assert int(dut.reg_write.value) == 0
    assert int(dut.mem_read.value) == 0
    assert int(dut.mem_write.value) == 0
    assert int(dut.npc_op.value) == NPC_PLUS4


@cocotb_test(dut=SIM)
async def test_ebreak_control(dut: CtrlDut):
    """ebreak：停机，cause=HALT_EBREAK。"""
    await drive_asm(dut, "ebreak")

    assert int(dut.halt.value) == 1
    assert int(dut.halt_cause.value) == HALT_EBREAK
    assert int(dut.reg_write.value) == 0
    assert int(dut.mem_read.value) == 0
    assert int(dut.mem_write.value) == 0
    assert int(dut.npc_op.value) == NPC_PLUS4


@cocotb_test(dut=SIM)
async def test_illegal_control(dut: CtrlDut):
    """未知 opcode：halt=1、cause=2，不写寄存器/内存。"""
    await drive(dut, opcode=0, funct3=0, opcode_err=1)

    assert int(dut.halt.value) == 1
    assert int(dut.halt_cause.value) == HALT_ILLEGAL_INST
    assert int(dut.reg_write.value) == 0
    assert int(dut.mem_read.value) == 0
    assert int(dut.mem_write.value) == 0
    assert int(dut.alu_op.value) == ALU_NOP
    assert int(dut.npc_op.value) == NPC_PLUS4


@cocotb_test(dut=SIM)
async def test_opcode_err_forces_illegal(dut: CtrlDut):
    """decoder 标记 opcode_err 时，即使字段看似合法也必须停机。"""
    await drive(
        dut,
        opcode=assemble("add x1, x2, x3") & 0x7F,
        funct3=0,
        funct7=0,
        rd=1,
        rs1=2,
        opcode_err=1,
    )

    assert int(dut.halt.value) == 1
    assert int(dut.halt_cause.value) == HALT_ILLEGAL_INST
    assert int(dut.reg_write.value) == 0


@cocotb_test(dut=SIM)
async def test_invalid_r_type(dut: CtrlDut):
    """未实现的 R 型 funct7/funct3 不应被接受。"""
    word = _with_field(assemble("add x1, x1, x2"), 31, 25, 0x20)
    await drive_word(dut, word)

    assert int(dut.halt.value) == 1
    assert int(dut.halt_cause.value) == HALT_ILLEGAL_INST
    assert int(dut.reg_write.value) == 0


@cocotb_test(dut=SIM)
async def test_invalid_funct3_matrix(dut: CtrlDut):
    """LOAD/STORE/BRANCH/JALR/OP-IMM 的非法 funct3 都必须拒绝。"""
    cases = [
        _with_field(assemble("lw x1, 0(x0)"), 14, 12, 1),  # lh
        _with_field(assemble("sw x1, 0(x0)"), 14, 12, 1),  # sh
        _with_field(assemble("beq x0, x1, 0"), 14, 12, 1),  # bne
        _with_field(assemble("jalr x1, 0(x0)"), 14, 12, 1),  # 非法 jalr
        _with_field(assemble("add x1, x0, x1"), 14, 12, 1),
    ]
    for instruction in cases:
        await drive_word(dut, instruction)
        assert int(dut.halt.value) == 1, f"不应接受 {instruction:#010x}"
        assert int(dut.halt_cause.value) == HALT_ILLEGAL_INST


@cocotb_test(dut=SIM)
async def test_invalid_system(dut: CtrlDut):
    """SYSTEM 组内其他 funct12/非零 rd/rs1 都应非法。"""
    ecall = assemble("ecall")
    cases = [
        _with_field(ecall, 11, 7, 1),      # rd != 0
        _with_field(ecall, 19, 15, 1),     # rs1 != 0
        _with_field(ecall, 31, 20, 0x102),  # sret，当前不支持
    ]
    for instruction in cases:
        await drive_word(dut, instruction)
        assert int(dut.halt.value) == 1
        assert int(dut.halt_cause.value) == HALT_ILLEGAL_INST
