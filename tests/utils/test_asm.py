"""编码器自检：用已知机器码验证 mips_asm 的字段拼接。"""

from utils.mips_asm import addu, addiu, beq, j, jal, jr, lw, sw


def test_known_encodings():
    assert addu(rd=3, rs=1, rt=2) == 0x00221821
    assert addiu(rt=1, rs=0, imm=8) == 0x24010008
    assert addiu(rt=2, rs=0, imm=-1) == 0x2402FFFF
    assert beq(rs=1, rt=2, offset=2) == 0x10220002
    assert j(target=2) == 0x08000002
    assert jal(target=3) == 0x0C000003
    assert jr(rs=1) == 0x00200008
    assert lw(rt=2, offset=0, base=1) == 0x8C220000
    assert sw(rt=3, offset=0, base=1) == 0xAC230000
