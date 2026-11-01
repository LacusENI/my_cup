"""编码器自检：用标准已知机器码验证 riscv_asm 的字段拼接。"""

import pytest

from utils.riscv_asm import (
    BRANCH,
    JAL,
    OP,
    OP_IMM,
    STORE,
    add,
    addi,
    b_type,
    beq,
    i_type,
    j,
    jal,
    jalr,
    jr,
    j_type,
    lw,
    nop,
    r_type,
    ret,
    s_type,
    sw,
)


# --------------------------------------------------------------------------- #
# 7 条指令的标准机器码
# --------------------------------------------------------------------------- #
def test_add():
    assert add(rd=3, rs1=1, rs2=2) == 0x002081B3
    assert add(rd=0, rs1=0, rs2=0) == 0x00000033


def test_addi():
    assert addi(rd=1, rs1=0, imm=8) == 0x00800093
    # 负立即数使用 12 位补码
    assert addi(rd=2, rs1=1, imm=-1) == 0xFFF08113
    assert addi(rd=3, rs1=1, imm=-2048) == 0x80008193


def test_beq():
    assert beq(rs1=1, rs2=2, offset=8) == 0x00208463
    # 负分支偏移（向后跳 4 字节）
    assert beq(rs1=1, rs2=1, offset=-4) == 0xFE108EE3


def test_lw():
    assert lw(rd=2, offset=0, rs1=1) == 0x0000A103
    # 负的 load 偏移
    assert lw(rd=2, offset=-4, rs1=1) == 0xFFC0A103


def test_sw():
    assert sw(rs2=3, offset=0, rs1=1) == 0x0030A023
    # 负的 store 偏移
    assert sw(rs2=3, offset=-4, rs1=1) == 0xFE30AE23


def test_jal():
    assert jal(rd=1, offset=8) == 0x008000EF
    # 负跳转偏移
    assert jal(rd=0, offset=-4) == 0xFFDFF06F


def test_jalr():
    assert jalr(rd=1, offset=0, rs1=2) == 0x000100E7
    assert jalr(rd=0, offset=-4, rs1=1) == 0xFFC08067


# --------------------------------------------------------------------------- #
# 伪指令展开
# --------------------------------------------------------------------------- #
def test_pseudo_instructions():
    # j offset -> jal x0, offset
    assert j(offset=8) == 0x0080006F
    # jr rs1 -> jalr x0, 0(rs1)
    assert jr(rs1=5) == 0x00028067
    # ret -> jalr x0, 0(ra)
    assert ret() == 0x00008067
    # nop -> addi x0, x0, 0
    assert nop() == 0x00000013


# --------------------------------------------------------------------------- #
# 底层编码函数
# --------------------------------------------------------------------------- #
def test_primitive_encoders():
    assert (
        r_type(opcode=OP, rd=3, funct3=0, rs1=1, rs2=2, funct7=0)
        == 0x002081B3
    )
    assert (
        i_type(opcode=OP_IMM, rd=1, funct3=0, rs1=0, imm=8)
        == 0x00800093
    )
    assert (
        s_type(opcode=STORE, funct3=2, rs1=1, rs2=3, imm=0)
        == 0x0030A023
    )
    assert (
        b_type(opcode=BRANCH, funct3=0, rs1=1, rs2=2, offset=8)
        == 0x00208463
    )
    assert j_type(opcode=JAL, rd=1, offset=8) == 0x008000EF


# --------------------------------------------------------------------------- #
# 范围检查
# --------------------------------------------------------------------------- #
def test_immediate_boundaries_accepted():
    assert addi(rd=1, rs1=0, imm=-2048) == 0x80000093
    assert addi(rd=1, rs1=0, imm=2047) == 0x7FF00093
    assert lw(rd=1, offset=-2048, rs1=0) == 0x80002083
    assert sw(rs2=1, offset=2047, rs1=0) == 0x7E102FA3
    assert beq(rs1=1, rs2=2, offset=-4096) == 0x80208063
    assert jal(rd=1, offset=1048574) == 0x7FFFF0EF


@pytest.mark.parametrize("imm", [-2049, 2048])
def test_addi_immediate_out_of_range(imm):
    with pytest.raises(ValueError):
        addi(rd=1, rs1=0, imm=imm)


@pytest.mark.parametrize("offset", [-2049, 2048])
def test_memory_offset_out_of_range(offset):
    with pytest.raises(ValueError):
        lw(rd=1, offset=offset, rs1=0)
    with pytest.raises(ValueError):
        sw(rs2=1, offset=offset, rs1=0)


@pytest.mark.parametrize("offset", [-4097, 4096, -3, 3])
def test_beq_offset_out_of_range_or_odd(offset):
    with pytest.raises(ValueError):
        beq(rs1=1, rs2=2, offset=offset)


@pytest.mark.parametrize("offset", [-1048578, 1048576, -3, 3])
def test_jal_offset_out_of_range_or_odd(offset):
    with pytest.raises(ValueError):
        jal(rd=1, offset=offset)


@pytest.mark.parametrize("reg", [-1, 32])
def test_register_out_of_range(reg):
    with pytest.raises(ValueError):
        add(rd=reg, rs1=0, rs2=0)
    with pytest.raises(ValueError):
        addi(rd=0, rs1=reg, imm=0)
    with pytest.raises(ValueError):
        jalr(rd=0, offset=0, rs1=reg)


def test_results_are_uint32():
    values = [
        add(rd=3, rs1=1, rs2=2),
        addi(rd=1, rs1=0, imm=-1),
        beq(rs1=1, rs2=2, offset=-4),
        lw(rd=2, offset=-4, rs1=1),
        sw(rs2=3, offset=-4, rs1=1),
        jal(rd=1, offset=-4),
        jalr(rd=1, offset=-4, rs1=1),
    ]
    for value in values:
        assert isinstance(value, int)
        assert 0 <= value <= 0xFFFF_FFFF
