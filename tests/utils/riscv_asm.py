"""
RV32I 最小子集指令编码器（assembler helper）。

测试里不再手写 `0x00800093` 这种机器码，而是写：

    addi(rd=1, rs1=0, imm=8)
    beq(rs1=1, rs2=2, offset=8)

这样可读性更好，字段改错也更容易发现。

当前只覆盖本批 7 条指令：

    add, addi, beq, lw, sw, jal, jalr

以及伪指令展开：

    j offset        -> jal x0, offset
    jr rs1          -> jalr x0, 0(rs1)
    ret             -> jalr x0, 0(ra)
    nop             -> addi x0, x0, 0

注意：所有 offset 都是“字节偏移”，且分支/跳转偏移必须是偶数。
"""

# --------------------------------------------------------------------------- #
# 编码常量
#
# 这些数值是 RISC-V 标准编码，RTL 和测试都依赖它们。
# --------------------------------------------------------------------------- #
OP = 0x33        # R 型：add
OP_IMM = 0x13    # I 型：addi
LOAD = 0x03      # I 型：lw
STORE = 0x23     # S 型：sw
BRANCH = 0x63    # B 型：beq
JALR = 0x67      # I 型：jalr
JAL = 0x6F       # J 型：jal

F3_ADD = 0
F3_ADDI = 0
F3_BEQ = 0
F3_LW = 2
F3_SW = 2
F3_JALR = 0

F7_ADD = 0

# 寄存器编号
ZERO = 0
RA = 1

MASK32 = 0xFFFF_FFFF


# --------------------------------------------------------------------------- #
# 基础检查与编码函数
# --------------------------------------------------------------------------- #
def _check_unsigned(value: int, bits: int, name: str) -> None:
    """检查无符号字段是否在 bits 位范围内。"""
    if not 0 <= value < (1 << bits):
        raise ValueError(f"{name}={value} 超出 {bits} 位无符号范围")


def _check_signed(value: int, bits: int, name: str) -> None:
    """检查有符号立即数是否在 bits 位补码范围内。"""
    low = -(1 << (bits - 1))
    high = (1 << (bits - 1)) - 1
    if not low <= value <= high:
        raise ValueError(f"{name}={value} 超出 {bits} 位有符号范围 [{low}, {high}]")


def _check_even(value: int, name: str) -> None:
    """分支/跳转偏移以 2 字节为单位，必须为偶数。"""
    if value % 2 != 0:
        raise ValueError(f"{name}={value} 必须是偶数（单位：字节）")


def _encode_signed(value: int, bits: int, name: str) -> int:
    """检查有符号范围并返回 bits 位补码位模式。"""
    _check_signed(value, bits, name)
    return value & ((1 << bits) - 1)


def r_type(*, opcode: int, rd: int, funct3: int, rs1: int, rs2: int,
           funct7: int = 0) -> int:
    """R 型指令：

        funct7(7) rs2(5) rs1(5) funct3(3) rd(5) opcode(7)
    """
    _check_unsigned(opcode, 7, "opcode")
    _check_unsigned(rd, 5, "rd")
    _check_unsigned(funct3, 3, "funct3")
    _check_unsigned(rs1, 5, "rs1")
    _check_unsigned(rs2, 5, "rs2")
    _check_unsigned(funct7, 7, "funct7")
    value = (
        (funct7 << 25)
        | (rs2 << 20)
        | (rs1 << 15)
        | (funct3 << 12)
        | (rd << 7)
        | opcode
    )
    return value & MASK32


def i_type(*, opcode: int, rd: int, funct3: int, rs1: int, imm: int) -> int:
    """I 型指令：

        imm[11:0](12) rs1(5) funct3(3) rd(5) opcode(7)
    """
    _check_unsigned(opcode, 7, "opcode")
    _check_unsigned(rd, 5, "rd")
    _check_unsigned(funct3, 3, "funct3")
    _check_unsigned(rs1, 5, "rs1")
    imm12 = _encode_signed(imm, 12, "imm")
    value = (imm12 << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode
    return value & MASK32


def s_type(*, opcode: int, funct3: int, rs1: int, rs2: int, imm: int) -> int:
    """S 型指令（store）：

        imm[11:5](7) rs2(5) rs1(5) funct3(3) imm[4:0](5) opcode(7)
    """
    _check_unsigned(opcode, 7, "opcode")
    _check_unsigned(funct3, 3, "funct3")
    _check_unsigned(rs1, 5, "rs1")
    _check_unsigned(rs2, 5, "rs2")
    imm12 = _encode_signed(imm, 12, "imm")
    value = (
        (((imm12 >> 5) & 0x7F) << 25)
        | (rs2 << 20)
        | (rs1 << 15)
        | (funct3 << 12)
        | ((imm12 & 0x1F) << 7)
        | opcode
    )
    return value & MASK32


def b_type(*, opcode: int, funct3: int, rs1: int, rs2: int, offset: int) -> int:
    """B 型指令（branch）：

        imm[12] imm[10:5](6) rs2(5) rs1(5) funct3(3)
        imm[4:1](4) imm[11] opcode(7)

    offset 为 13 位有符号字节偏移，且必须为偶数。
    """
    _check_unsigned(opcode, 7, "opcode")
    _check_unsigned(funct3, 3, "funct3")
    _check_unsigned(rs1, 5, "rs1")
    _check_unsigned(rs2, 5, "rs2")
    _check_even(offset, "offset")
    imm13 = _encode_signed(offset, 13, "offset")
    value = (
        (((imm13 >> 12) & 0x1) << 31)
        | (((imm13 >> 5) & 0x3F) << 25)
        | (rs2 << 20)
        | (rs1 << 15)
        | (funct3 << 12)
        | (((imm13 >> 1) & 0xF) << 8)
        | (((imm13 >> 11) & 0x1) << 7)
        | opcode
    )
    return value & MASK32


def j_type(*, opcode: int, rd: int, offset: int) -> int:
    """J 型指令：

        imm[20] imm[10:1](10) imm[11] imm[19:12](8) rd(5) opcode(7)

    offset 为 21 位有符号字节偏移，且必须为偶数。
    """
    _check_unsigned(opcode, 7, "opcode")
    _check_unsigned(rd, 5, "rd")
    _check_even(offset, "offset")
    imm21 = _encode_signed(offset, 21, "offset")
    value = (
        (((imm21 >> 20) & 0x1) << 31)
        | (((imm21 >> 1) & 0x3FF) << 21)
        | (((imm21 >> 11) & 0x1) << 20)
        | (((imm21 >> 12) & 0xFF) << 12)
        | (rd << 7)
        | opcode
    )
    return value & MASK32


# --------------------------------------------------------------------------- #
# 指令级 helper（参数顺序尽量贴近汇编写法）
# --------------------------------------------------------------------------- #
def add(*, rd: int, rs1: int, rs2: int) -> int:
    """add rd, rs1, rs2"""
    return r_type(
        opcode=OP, rd=rd, funct3=F3_ADD, rs1=rs1, rs2=rs2, funct7=F7_ADD
    )


def addi(*, rd: int, rs1: int, imm: int) -> int:
    """addi rd, rs1, imm"""
    return i_type(opcode=OP_IMM, rd=rd, funct3=F3_ADDI, rs1=rs1, imm=imm)


def beq(*, rs1: int, rs2: int, offset: int) -> int:
    """beq rs1, rs2, offset（offset 单位是字节）"""
    return b_type(
        opcode=BRANCH, funct3=F3_BEQ, rs1=rs1, rs2=rs2, offset=offset
    )


def lw(*, rd: int, offset: int, rs1: int) -> int:
    """lw rd, offset(rs1)"""
    return i_type(opcode=LOAD, rd=rd, funct3=F3_LW, rs1=rs1, imm=offset)


def sw(*, rs2: int, offset: int, rs1: int) -> int:
    """sw rs2, offset(rs1)"""
    return s_type(opcode=STORE, funct3=F3_SW, rs1=rs1, rs2=rs2, imm=offset)


def jal(*, rd: int, offset: int) -> int:
    """jal rd, offset（offset 单位是字节）"""
    return j_type(opcode=JAL, rd=rd, offset=offset)


def jalr(*, rd: int, offset: int, rs1: int) -> int:
    """jalr rd, offset(rs1)"""
    return i_type(opcode=JALR, rd=rd, funct3=F3_JALR, rs1=rs1, imm=offset)


# --------------------------------------------------------------------------- #
# 伪指令展开
# --------------------------------------------------------------------------- #
def j(*, offset: int) -> int:
    """j offset -> jal x0, offset"""
    return jal(rd=ZERO, offset=offset)


def jr(*, rs1: int) -> int:
    """jr rs1 -> jalr x0, 0(rs1)"""
    return jalr(rd=ZERO, offset=0, rs1=rs1)


def ret() -> int:
    """ret -> jalr x0, 0(ra)"""
    return jalr(rd=ZERO, offset=0, rs1=RA)


def nop() -> int:
    """nop -> addi x0, x0, 0"""
    return addi(rd=ZERO, rs1=ZERO, imm=0)


__all__ = [
    "OP",
    "OP_IMM",
    "LOAD",
    "STORE",
    "BRANCH",
    "JALR",
    "JAL",
    "F3_ADD",
    "F3_ADDI",
    "F3_BEQ",
    "F3_LW",
    "F3_SW",
    "F3_JALR",
    "F7_ADD",
    "ZERO",
    "RA",
    "r_type",
    "i_type",
    "s_type",
    "b_type",
    "j_type",
    "add",
    "addi",
    "beq",
    "lw",
    "sw",
    "jal",
    "jalr",
    "j",
    "jr",
    "ret",
    "nop",
]
