"""
从 `rtl/cpu_pkg.sv` 读取常量与 packed struct 布局。

为什么不直接在测试里写 `ALU_OP_ADD = 0b0001`？
  - 那样 RTL 一改，测试就可能悄悄对不上；
  - 这里让 `cpu_pkg.sv` 成为唯一事实来源；
  - 测试里只写名字，值在 import 时从 RTL 解析出来。

这个模块只解析项目里用到的“简单写法”，不是完整的 SystemVerilog 解析器：
  - enum / localparam 的数字常量；
  - packed struct 的字段顺序和位宽。

如果以后 `cpu_pkg.sv` 用了更复杂的表达式，解析器会直接报错，
而不是悄悄给出一个错误的值。
"""

from __future__ import annotations

import re
from pathlib import Path

PKG_PATH = Path(__file__).resolve().parents[1] / "rtl" / "cpu_pkg.sv"


# --------------------------------------------------------------------------- #
# 1. 去掉注释，避免把注释里的数字误当成常量
# --------------------------------------------------------------------------- #
def _strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"//[^\n]*", "", text)
    return text


# --------------------------------------------------------------------------- #
# 2. 解析数字常量
#
# 支持：
#   ALU_OP_ADD = 4'b0001,
#   OP_ADDIU   = 6'b001001;
#   XLEN       = 32;
# --------------------------------------------------------------------------- #
_CONST_RE = re.compile(
    r"\b(?P<name>[A-Z][A-Z0-9_]*)\s*=\s*"
    r"(?:(?:\d+)?'(?P<base>[bBhHdD])(?P<digits>[0-9a-fA-F_]+)|(?P<dec>\d+))"
    # 枚举最后一个成员后面是 `}`，localparam 后面是 `;`，中间成员是 `,`。
    r"\s*[,;}]"
)


def _parse_int_literal(match: re.Match[str]) -> int:
    """把 `4'b0001` / `6'h3F` / `32` 这样的字面量转成 Python int。"""
    if match.group("dec") is not None:
        return int(match.group("dec"), 10)

    base = {"b": 2, "h": 16, "d": 10}[match.group("base").lower()]
    digits = match.group("digits").replace("_", "")
    return int(digits, base)


def _load_constants(text: str) -> dict[str, int]:
    constants: dict[str, int] = {}
    for match in _CONST_RE.finditer(text):
        constants[match.group("name")] = _parse_int_literal(match)

    if not constants:
        raise ValueError(f"没有从 {PKG_PATH} 解析到任何常量")

    return constants


# --------------------------------------------------------------------------- #
# 3. 解析 enum 的位宽
#
# 例如：
#   typedef enum logic [3:0] { ... } alu_op_t;   -> 4
#   typedef enum logic       { ... } ext_type_t; -> 1
# --------------------------------------------------------------------------- #
_ENUM_RE = re.compile(
    r"typedef\s+enum\s+logic\s*"
    r"(?:\[\s*(?P<msb>\d+)\s*:\s*(?P<lsb>\d+)\s*\])?\s*"
    r"\{[^}]*\}\s*(?P<name>[A-Za-z_]\w*)\s*;",
    re.DOTALL,
)


def _load_enum_widths(text: str) -> dict[str, int]:
    widths: dict[str, int] = {}
    for match in _ENUM_RE.finditer(text):
        if match.group("msb") is None:
            widths[match.group("name")] = 1
        else:
            widths[match.group("name")] = (
                int(match.group("msb")) - int(match.group("lsb")) + 1
            )
    return widths


# --------------------------------------------------------------------------- #
# 4. 解析 packed struct 的字段
#
# 例如 ctrl_t：
#   typedef struct packed {
#       npc_op_t npc_op;
#       logic    reg_write;
#       ...
#   } ctrl_t;
#
# 解析结果保存“字段声明顺序”，位偏移稍后统一计算。
# --------------------------------------------------------------------------- #
_STRUCT_RE = re.compile(
    r"typedef\s+struct\s+packed\s*\{(?P<body>.*?)\}\s*(?P<name>[A-Za-z_]\w*)\s*;",
    re.DOTALL,
)

_FIELD_RE = re.compile(
    r"^(?P<type>[A-Za-z_]\w*)\s*"
    r"(?:\[\s*(?P<msb>\d+)\s*:\s*(?P<lsb>\d+)\s*\])?\s+"
    r"(?P<name>[A-Za-z_]\w*)$"
)


def _load_struct_fields(
    text: str,
) -> dict[str, list[tuple[str, int | None, int | None, str]]]:
    structs: dict[str, list[tuple[str, int | None, int | None, str]]] = {}

    for match in _STRUCT_RE.finditer(text):
        struct_name = match.group("name")
        fields: list[tuple[str, int | None, int | None, str]] = []

        for raw_field in match.group("body").split(";"):
            raw_field = " ".join(raw_field.split())
            if not raw_field:
                continue

            field_match = _FIELD_RE.match(raw_field)
            if field_match is None:
                raise ValueError(
                    f"无法解析 {struct_name} 的字段: {raw_field!r}"
                )

            msb_text = field_match.group("msb")
            lsb_text = field_match.group("lsb")
            fields.append(
                (
                    field_match.group("type"),
                    int(msb_text) if msb_text is not None else None,
                    int(lsb_text) if lsb_text is not None else None,
                    field_match.group("name"),
                )
            )

        structs[struct_name] = fields

    return structs


# --------------------------------------------------------------------------- #
# 5. 计算类型宽度 / struct 布局
# --------------------------------------------------------------------------- #
_STRUCT_WIDTH_CACHE: dict[str, int] = {}


def _type_width(
    type_name: str,
    msb: int | None,
    lsb: int | None,
    stack: tuple[str, ...],
) -> int:
    """返回一个字段类型的位宽。"""
    if msb is not None and lsb is not None:
        return msb - lsb + 1

    if type_name == "logic":
        return 1

    if type_name == "word_t":
        return CONSTS["XLEN"]

    if type_name in ENUM_WIDTHS:
        return ENUM_WIDTHS[type_name]

    if type_name in _STRUCT_FIELDS:
        return struct_width(type_name, stack)

    raise ValueError(f"不知道如何计算类型 {type_name!r} 的位宽")


def struct_width(name: str, stack: tuple[str, ...] = ()) -> int:
    """返回一个 packed struct 的总位宽。"""
    if name in _STRUCT_WIDTH_CACHE:
        return _STRUCT_WIDTH_CACHE[name]

    if name not in _STRUCT_FIELDS:
        raise KeyError(f"cpu_pkg.sv 里没有 struct {name!r}")

    if name in stack:
        raise ValueError(f"struct {name!r} 出现循环引用: {' -> '.join(stack + (name,))}")

    total = 0
    for type_name, msb, lsb, _field_name in _STRUCT_FIELDS[name]:
        total += _type_width(type_name, msb, lsb, stack + (name,))

    _STRUCT_WIDTH_CACHE[name] = total
    return total


def struct_layout(name: str) -> dict[str, tuple[int, int]]:
    """返回 packed struct 的字段布局：{字段名: (最高位, 位宽)}。

    例如 ctrl_t 的 npc_op 在最高位，布局是：
        {"npc_op": (16, 2), "reg_write": (14, 1), ...}
    """
    total = struct_width(name)
    remaining = total
    layout: dict[str, tuple[int, int]] = {}

    for type_name, msb, lsb, field_name in _STRUCT_FIELDS[name]:
        width = _type_width(type_name, msb, lsb, (name,))
        remaining -= width
        layout[field_name] = (remaining + width - 1, width)

    return layout


# --------------------------------------------------------------------------- #
# 6. 模块级常量
# --------------------------------------------------------------------------- #
_TEXT = _strip_comments(PKG_PATH.read_text(encoding="utf-8"))

CONSTS: dict[str, int] = _load_constants(_TEXT)
ENUM_WIDTHS: dict[str, int] = _load_enum_widths(_TEXT)
_STRUCT_FIELDS = _load_struct_fields(_TEXT)

# 下面这些名字只是“给 IDE / 类型检查器看的声明”。
# 值仍然来自上面的 CONSTS（也就是 cpu_pkg.sv），没有第二份数值。
# 如果 RTL 删掉某个名字，import 阶段就会直接 KeyError。
XLEN: int = CONSTS["XLEN"]
IMEM_WORDS: int = CONSTS["IMEM_WORDS"]
DMEM_WORDS: int = CONSTS["DMEM_WORDS"]

ALU_OP_ADD: int = CONSTS["ALU_OP_ADD"]
ALU_OP_SUB: int = CONSTS["ALU_OP_SUB"]

COND_TYPE_EQ: int = CONSTS["COND_TYPE_EQ"]

EXT_TYPE_ZERO_EXT: int = CONSTS["EXT_TYPE_ZERO_EXT"]
EXT_TYPE_SIGN_EXT: int = CONSTS["EXT_TYPE_SIGN_EXT"]

NPC_OP_PLUS4: int = CONSTS["NPC_OP_PLUS4"]
NPC_OP_BRANCH: int = CONSTS["NPC_OP_BRANCH"]
NPC_OP_DIRECT: int = CONSTS["NPC_OP_DIRECT"]
NPC_OP_RA: int = CONSTS["NPC_OP_RA"]

RD_SEL_RT: int = CONSTS["RD_SEL_RT"]
RD_SEL_RD: int = CONSTS["RD_SEL_RD"]
RD_SEL_REG_RA: int = CONSTS["RD_SEL_REG_RA"]

WB_SEL_ALU_OUT: int = CONSTS["WB_SEL_ALU_OUT"]
WB_SEL_R_DATA: int = CONSTS["WB_SEL_R_DATA"]
WB_SEL_PC_P4: int = CONSTS["WB_SEL_PC_P4"]

SRC2_SEL_RS2: int = CONSTS["SRC2_SEL_RS2"]
SRC2_SEL_IMM: int = CONSTS["SRC2_SEL_IMM"]

OP_R: int = CONSTS["OP_R"]
OP_ADDIU: int = CONSTS["OP_ADDIU"]
OP_BEQ: int = CONSTS["OP_BEQ"]
OP_LW: int = CONSTS["OP_LW"]
OP_SW: int = CONSTS["OP_SW"]
OP_J: int = CONSTS["OP_J"]
OP_JAL: int = CONSTS["OP_JAL"]

FUNCT_ADDU: int = CONSTS["FUNCT_ADDU"]
FUNCT_JR: int = CONSTS["FUNCT_JR"]


def const(name: str) -> int:
    """按名字取常量（适合需要动态拼名字的场合）。"""
    try:
        return CONSTS[name]
    except KeyError:
        raise KeyError(f"cpu_pkg.sv 里没有常量 {name!r}") from None


def __getattr__(name: str) -> int:
    """让 `from rtl_consts import ALU_OP_ADD` 直接可用。"""
    if name in CONSTS:
        return CONSTS[name]
    raise AttributeError(f"cpu_pkg.sv 里没有常量 {name!r}")


def __dir__() -> list[str]:
    """让 IDE / dir() 能看到所有从 RTL 解析出来的常量。"""
    return sorted(set(globals()) | set(CONSTS))


__all__ = sorted(CONSTS)
