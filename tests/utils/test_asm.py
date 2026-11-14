"""LLVM MC 汇编封装的自检。"""

import pytest

from utils.assembler import assemble


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("add x3, x1, x2", 0x002081B3),
        ("add ra, sp, gp", 0x003100B3),
        ("addi x1, x0, -1", 0xFFF00093),
        ("lw x2, -4(x1)", 0xFFC0A103),
        ("sw x3, -4(x1)", 0xFE30AE23),
        ("beq x1, x2, 8", 0x00208463),
        ("beq x1, x2, -8", 0xFE208CE3),
        ("jal x1, 8", 0x008000EF),
        ("jal x1, -8", 0xFF9FF0EF),
        ("jalr x1, 0(x2)", 0x000100E7),
        ("lui x5, 0xABCDE", 0xABCDE2B7),
        ("srai x7, x8, 31", 0x41F45393),
        ("nop", 0x00000013),
    ],
)
def test_golden_vectors(text, expected):
    assert assemble(text) == expected


def test_inline_comment():
    assert assemble("add x3, x1, x2 # x3 = x1 + x2") == 0x002081B3


def test_rejects_empty_text():
    with pytest.raises(ValueError, match="不能为空"):
        assemble("   ")


def test_rejects_multiple_instructions():
    with pytest.raises(ValueError, match="不是单条"):
        assemble("add x1, x0, x0\nadd x2, x0, x0")


def test_rejects_pseudo_expansion():
    with pytest.raises(ValueError, match="不是单条"):
        assemble("li x1, 0x12345678")


def test_rejects_unknown_instruction():
    with pytest.raises(ValueError, match="无法汇编"):
        assemble("frobnicate x1, x2, x3")


def test_rejects_out_of_range_immediate():
    with pytest.raises(ValueError, match="无法汇编"):
        assemble("addi x1, x0, 2048")


def test_rejects_unaligned_branch():
    with pytest.raises(ValueError, match="无法汇编"):
        assemble("beq x1, x2, 3")
