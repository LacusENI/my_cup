"""
MIPS 子集指令编码器（assembler helper）。

测试里不再手写 `0x24010008` 这种机器码，而是写：

    addiu(rt=1, rs=0, imm=8)
    beq(rs=1, rt=2, offset=2)

这样可读性更好，字段改错也更容易发现。

当前只覆盖项目冻结的 8 条指令：
    addu, addiu, lw, sw, beq, j, jal, jr

> 切 RV32I 时，这个模块可以整体替换成 `riscv_asm.py`。
"""

# --------------------------------------------------------------------------- #
# 编码常量
#
# 这些数值是 CPU 的对外契约：RTL 和测试都依赖它们。
# 已发布的数值不要修改；需要扩展时只新增指令，保持向后兼容。
# 如果确实要改，测试会失败——这是故意的，提醒你这是一次破坏性变更。
# --------------------------------------------------------------------------- #
OP_R     = 0b000000
OP_J     = 0b000010
OP_JAL   = 0b000011
OP_BEQ   = 0b000100
OP_ADDIU = 0b001001
OP_LW    = 0b100011
OP_SW    = 0b101011

FUNCT_ADDU = 0b100001
FUNCT_JR   = 0b001000

MASK32 = 0xFFFF_FFFF


# --------------------------------------------------------------------------- #
# 基础编码函数
# --------------------------------------------------------------------------- #
def _check_range(value: int, bits: int, name: str) -> None:
    """检查无符号字段是否在 bits 位范围内。"""
    if not 0 <= value < (1 << bits):
        raise ValueError(f"{name}={value} 超出 {bits} 位无符号范围")


def _imm16(value: int, name: str = "imm") -> int:
    """把有符号/无符号的 16 位立即数转成补码位模式。"""
    if not -0x8000 <= value <= 0xFFFF:
        raise ValueError(f"{name}={value} 超出 16 位范围")
    return value & 0xFFFF


def r_type(rs: int, rt: int, rd: int, funct: int, shamt: int = 0) -> int:
    """R 型指令：

        opcode(6) rs(5) rt(5) rd(5) shamt(5) funct(6)
    """
    _check_range(rs, 5, "rs")
    _check_range(rt, 5, "rt")
    _check_range(rd, 5, "rd")
    _check_range(shamt, 5, "shamt")
    _check_range(funct, 6, "funct")
    value = (OP_R << 26) | (rs << 21) | (rt << 16) | (rd << 11) | (shamt << 6) | funct
    return value & MASK32


def i_type(opcode: int, rs: int, rt: int, imm: int) -> int:
    """I 型指令：

        opcode(6) rs(5) rt(5) imm(16)
    """
    _check_range(opcode, 6, "opcode")
    _check_range(rs, 5, "rs")
    _check_range(rt, 5, "rt")
    value = (opcode << 26) | (rs << 21) | (rt << 16) | _imm16(imm)
    return value & MASK32


def j_type(opcode: int, target: int) -> int:
    """J 型指令：

        opcode(6) instr_index(26)
    """
    _check_range(opcode, 6, "opcode")
    _check_range(target, 26, "target")
    value = (opcode << 26) | target
    return value & MASK32


# --------------------------------------------------------------------------- #
# 指令级 helper（参数顺序尽量贴近汇编写法）
# --------------------------------------------------------------------------- #
def addu(*, rd: int, rs: int, rt: int) -> int:
    """addu rd, rs, rt"""
    return r_type(rs=rs, rt=rt, rd=rd, funct=FUNCT_ADDU)


def addiu(*, rt: int, rs: int, imm: int) -> int:
    """addiu rt, rs, imm"""
    return i_type(OP_ADDIU, rs=rs, rt=rt, imm=imm)


def lw(*, rt: int, offset: int, base: int) -> int:
    """lw rt, offset(base)"""
    return i_type(OP_LW, rs=base, rt=rt, imm=offset)


def sw(*, rt: int, offset: int, base: int) -> int:
    """sw rt, offset(base)"""
    return i_type(OP_SW, rs=base, rt=rt, imm=offset)


def beq(*, rs: int, rt: int, offset: int) -> int:
    """beq rs, rt, offset（offset 单位是指令字）"""
    return i_type(OP_BEQ, rs=rs, rt=rt, imm=offset)


def j(*, target: int) -> int:
    """j target（target 是 26 位 instr_index）"""
    return j_type(OP_J, target=target)


def jal(*, target: int) -> int:
    """jal target（target 是 26 位 instr_index）"""
    return j_type(OP_JAL, target=target)


def jr(*, rs: int) -> int:
    """jr rs"""
    return r_type(rs=rs, rt=0, rd=0, funct=FUNCT_JR)


__all__ = [
    "OP_R",
    "OP_J",
    "OP_JAL",
    "OP_BEQ",
    "OP_ADDIU",
    "OP_LW",
    "OP_SW",
    "FUNCT_ADDU",
    "FUNCT_JR",
    "r_type",
    "i_type",
    "j_type",
    "addu",
    "addiu",
    "lw",
    "sw",
    "beq",
    "j",
    "jal",
    "jr",
]
