"""
decoder（指令译码 + 立即数生成）的单元测试。

decoder 是纯组合逻辑。测试通过 test-only probe 观察：
  - RV32I 字段：opcode / rd / rs1 / rs2 / funct3 / funct7
  - imm：I/S/B/J 四种立即数
  - valid_encoding：是否属于本批 7 条指令

立即数生成虽然写在 decoder 内部，但这里单独覆盖每种格式，
避免只靠指令级测试才能发现 B/J 型拼位错误。
"""

from typing import Protocol

import cocotb

from utils.cocotb_utils import Signal, assert_fields, settle
from utils.riscv_asm import (
    BRANCH,
    JALR,
    LOAD,
    OP,
    STORE,
    add,
    addi,
    b_type,
    beq,
    i_type,
    jal,
    jalr,
    lw,
    r_type,
    s_type,
    sw,
)


class DecoderDut(Protocol):
    inst: Signal
    opcode: Signal
    rd: Signal
    funct3: Signal
    rs1: Signal
    rs2: Signal
    funct7: Signal
    imm: Signal
    valid_encoding: Signal


REQUIRED_FIELDS = (
    "inst",
    "opcode",
    "rd",
    "funct3",
    "rs1",
    "rs2",
    "funct7",
    "imm",
    "valid_encoding",
)


@cocotb.test()
async def contract_test(dut: DecoderDut):
    """契约：decoder_probe 暴露字段、立即数和合法编码。"""
    assert_fields(dut, REQUIRED_FIELDS, "decoder_probe")


@cocotb.test()
async def fields_test(dut: DecoderDut):
    """R 型字段切分：add x3, x1, x2。"""
    dut.inst.value = add(rd=3, rs1=1, rs2=2)
    await settle()

    assert int(dut.opcode.value) == OP
    assert int(dut.rd.value) == 3
    assert int(dut.rs1.value) == 1
    assert int(dut.rs2.value) == 2
    assert int(dut.funct3.value) == 0
    assert int(dut.funct7.value) == 0
    assert int(dut.imm.value) == 0
    assert int(dut.valid_encoding.value) == 1


@cocotb.test()
async def imm_i_test(dut: DecoderDut):
    """I 型立即数：正数、负数和边界。"""
    cases = [
        (addi(rd=1, rs1=0, imm=8), 8),
        (addi(rd=1, rs1=0, imm=-1), 0xFFFF_FFFF),
        (lw(rd=2, offset=-4, rs1=1), 0xFFFF_FFFC),
        (jalr(rd=1, offset=-4, rs1=2), 0xFFFF_FFFC),
    ]
    for instruction, expected in cases:
        dut.inst.value = instruction
        await settle()
        assert int(dut.imm.value) == expected, f"I 型立即数错误: {instruction:#010x}"


@cocotb.test()
async def imm_s_test(dut: DecoderDut):
    """S 型立即数：imm[11:5] 与 imm[4:0] 的拼接和符号扩展。"""
    cases = [
        (sw(rs2=3, offset=0, rs1=1), 0),
        (sw(rs2=3, offset=2047, rs1=1), 2047),
        (sw(rs2=3, offset=-4, rs1=1), 0xFFFF_FFFC),
        (sw(rs2=3, offset=-2048, rs1=1), 0xFFFF_F800),
    ]
    for instruction, expected in cases:
        dut.inst.value = instruction
        await settle()
        assert int(dut.imm.value) == expected, f"S 型立即数错误: {instruction:#010x}"


@cocotb.test()
async def imm_b_test(dut: DecoderDut):
    """B 型立即数：乱序位拼接、符号扩展、bit0 为 0。"""
    cases = [
        (beq(rs1=1, rs2=2, offset=0), 0),
        (beq(rs1=1, rs2=2, offset=8), 8),
        (beq(rs1=1, rs2=2, offset=-8), 0xFFFF_FFF8),
        (beq(rs1=1, rs2=2, offset=4094), 4094),
        (beq(rs1=1, rs2=2, offset=-4096), 0xFFFF_F000),
    ]
    for instruction, expected in cases:
        dut.inst.value = instruction
        await settle()
        assert int(dut.imm.value) == expected, f"B 型立即数错误: {instruction:#010x}"


@cocotb.test()
async def imm_j_test(dut: DecoderDut):
    """J 型立即数：乱序位拼接、符号扩展、bit0 为 0。"""
    cases = [
        (jal(rd=1, offset=0), 0),
        (jal(rd=1, offset=8), 8),
        (jal(rd=1, offset=-8), 0xFFFF_FFF8),
        (jal(rd=1, offset=1048574), 1048574),
        (jal(rd=1, offset=-1048576), 0xFFF0_0000),
    ]
    for instruction, expected in cases:
        dut.inst.value = instruction
        await settle()
        assert int(dut.imm.value) == expected, f"J 型立即数错误: {instruction:#010x}"


@cocotb.test()
async def invalid_r_type_test(dut: DecoderDut):
    """未实现的 R 型 funct7/funct3 不应被接受。"""
    # sub 的 funct7=0x20；本批只实现 add。
    dut.inst.value = r_type(opcode=OP, rd=1, funct3=0, rs1=1, rs2=2, funct7=0x20)
    await settle()
    assert int(dut.valid_encoding.value) == 0


@cocotb.test()
async def invalid_opcode_test(dut: DecoderDut):
    """未知 opcode 应该输出 illegal，imm 保持 0。"""
    dut.inst.value = 0xFFFF_FFFF
    await settle()
    assert int(dut.valid_encoding.value) == 0
    assert int(dut.imm.value) == 0


@cocotb.test()
async def invalid_funct3_test(dut: DecoderDut):
    """addi 只接受 funct3=000。"""
    dut.inst.value = i_type(opcode=0x13, rd=1, funct3=1, rs1=0, imm=8)
    await settle()
    assert int(dut.valid_encoding.value) == 0


@cocotb.test()
async def invalid_funct3_matrix_test(dut: DecoderDut):
    """LOAD/STORE/BRANCH/JALR 的非法 funct3 都必须拒绝。"""
    cases = [
        i_type(opcode=LOAD, rd=1, funct3=1, rs1=0, imm=0),       # lh
        s_type(opcode=STORE, funct3=1, rs1=0, rs2=1, imm=0),     # sh
        b_type(opcode=BRANCH, funct3=1, rs1=0, rs2=1, offset=0), # bne
        i_type(opcode=JALR, rd=1, funct3=1, rs1=0, imm=0),       # 非法 jalr
        r_type(opcode=OP, rd=1, funct3=1, rs1=0, rs2=1, funct7=0),
    ]
    for instruction in cases:
        dut.inst.value = instruction
        await settle()
        assert int(dut.valid_encoding.value) == 0, f"不应接受 {instruction:#010x}"
