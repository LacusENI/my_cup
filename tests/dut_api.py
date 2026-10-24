"""
DUT 的公开接口：类型注解 + 访问器 + 契约字段表。

cocotb 的 `dut` 是运行时动态对象：字段要到仿真开始后才存在，
所以普通的 Python 类型注解没法直接约束它。这里做三件事：

  1. 用 `Protocol` 声明测试依赖的字段；
     IDE / 类型检查器能看到字段名，写错时更早发现。
  2. 用 `read_*` / `write_*` 收口常见访问；
     以后 RTL 里改名，只改这个文件，不用满测试找。
  3. 用 `PUBLIC_FIELDS` + `assert_public_fields` 在仿真里验证
     “RTL 确实还暴露这些字段”。

注意：
  - Protocol 只在静态检查时起作用，运行时不会自动检查；
  - 真正保证字段存在的是 `tb_contract.py` 里的契约测试；
  - `Signal.value` 故意写成 Any，因为 cocotb 可能返回 int / LogicArray，
    测试里统一用 `int(...)` 转成 Python 整数。
"""

from __future__ import annotations

from typing import Any, Protocol, Sequence


# --------------------------------------------------------------------------- #
# 1. 基础协议
# --------------------------------------------------------------------------- #
class Signal(Protocol):
    """cocotb 信号：测试只关心 `.value`。"""

    value: Any


class HasClock(Protocol):
    """任何带 `clk` 的 DUT 都可以传给 start_clock / wait_cycles。"""

    clk: Signal


class Pc(Protocol):
    curr_pc: Signal
    next_pc: Signal


class RegFile(Protocol):
    # cocotb 的数组句柄可以按下标访问，行为上类似 Sequence
    regs: Sequence[Signal]


class Memory(Protocol):
    mem: Sequence[Signal]


# --------------------------------------------------------------------------- #
# 2. 各个 DUT 的公开字段
# --------------------------------------------------------------------------- #
class CpuTop(Protocol):
    clk: Signal
    rst: Signal
    u_pc: Pc
    u_regfile: RegFile
    u_instrm: Memory
    u_datam: Memory


class AluDut(Protocol):
    alu_op: Signal
    alu_src1: Signal
    alu_src2: Signal
    alu_out: Signal
    zero_f: Signal
    neg_f: Signal
    overflow_f: Signal
    carry_f: Signal


class CtrlDut(Protocol):
    op: Signal
    funct: Signal
    ctrl: Signal


class DatamDut(Protocol):
    clk: Signal
    mem_read: Signal
    mem_write: Signal
    addr: Signal
    w_data: Signal
    r_data: Signal
    mem: Sequence[Signal]


class NpcDut(Protocol):
    curr_pc: Signal
    npc_op: Signal
    cond_jmp: Signal
    jmp_target: Signal
    jmp_offset: Signal
    jmp_reg: Signal
    pc_plus4: Signal
    next_pc: Signal


class RegfileDut(Protocol):
    clk: Signal
    reg_src1: Signal
    reg_src2: Signal
    reg_dst: Signal
    wb_data: Signal
    reg_write: Signal
    rs1_data: Signal
    rs2_data: Signal
    regs: Sequence[Signal]


class PipeRegisterDut(Protocol):
    """四个流水线寄存器共用这套控制信号；输入/输出字段名按实例不同。"""

    clk: Signal
    rst: Signal
    flush: Signal
    stall: Signal


# --------------------------------------------------------------------------- #
# 3. 常见访问器：把内部路径收口到一处
# --------------------------------------------------------------------------- #
def read_pc(dut: CpuTop) -> int:
    """当前 PC。"""
    return int(dut.u_pc.curr_pc.value)


def read_reg(dut: CpuTop, index: int) -> int:
    """读通用寄存器。"""
    return int(dut.u_regfile.regs[index].value)


def write_reg(dut: CpuTop, index: int, value: int) -> None:
    """预置通用寄存器（测试用）。"""
    dut.u_regfile.regs[index].value = value


def read_mem(dut: CpuTop, word_index: int) -> int:
    """读数据内存的一个字（按字索引，不是字节地址）。"""
    return int(dut.u_datam.mem[word_index].value)


def write_mem(dut: CpuTop, word_index: int, value: int) -> None:
    """预置数据内存的一个字（测试用）。"""
    dut.u_datam.mem[word_index].value = value


def write_instr(dut: CpuTop, word_index: int, instruction: int) -> None:
    """把机器码写进指令存储器。"""
    dut.u_instrm.mem[word_index].value = instruction


# --------------------------------------------------------------------------- #
# 4. 契约字段表：测试真正依赖的字段
#
# 只列“测试会碰”的字段，不追求把 RTL 所有信号都列出来。
# 如果这些字段被改名/删除，契约测试会失败，并提示同步修改本文件。
# --------------------------------------------------------------------------- #
PUBLIC_FIELDS: dict[str, tuple[str, ...]] = {
    "cpu_top": (
        "clk",
        "rst",
        "u_pc.curr_pc",
        "u_pc.next_pc",
        "u_regfile.regs",
        "u_instrm.mem",
        "u_datam.mem",
    ),
    "alu": (
        "alu_op",
        "alu_src1",
        "alu_src2",
        "alu_out",
        "zero_f",
        "neg_f",
        "overflow_f",
        "carry_f",
    ),
    "ctrl": (
        "op",
        "funct",
        "ctrl",
    ),
    "datam": (
        "clk",
        "mem_read",
        "mem_write",
        "addr",
        "w_data",
        "r_data",
        "mem",
    ),
    "npc": (
        "curr_pc",
        "npc_op",
        "cond_jmp",
        "jmp_target",
        "jmp_offset",
        "jmp_reg",
        "pc_plus4",
        "next_pc",
    ),
    "regfile": (
        "clk",
        "reg_src1",
        "reg_src2",
        "reg_dst",
        "wb_data",
        "reg_write",
        "rs1_data",
        "rs2_data",
        "regs",
    ),
    "if_id_reg": (
        "clk",
        "rst",
        "flush",
        "stall",
        "if_id_in",
        "if_id_out",
    ),
    "id_ex_reg": (
        "clk",
        "rst",
        "flush",
        "stall",
        "id_ex_in",
        "id_ex_out",
    ),
    "ex_mem_reg": (
        "clk",
        "rst",
        "flush",
        "stall",
        "ex_mem_in",
        "ex_mem_out",
    ),
    "mem_wb_reg": (
        "clk",
        "rst",
        "flush",
        "stall",
        "mem_wb_in",
        "mem_wb_out",
    ),
}


def missing_fields(dut: Any, contract: str) -> list[str]:
    """返回契约里缺失的字段路径。"""
    try:
        paths = PUBLIC_FIELDS[contract]
    except KeyError:
        raise KeyError(f"没有为 {contract!r} 定义 PUBLIC_FIELDS") from None

    missing: list[str] = []

    for path in paths:
        obj = dut
        for part in path.split("."):
            try:
                obj = obj[part]
            except (KeyError, AttributeError):
                missing.append(path)
                break

    return missing


def assert_public_fields(dut: Any, contract: str) -> None:
    """确认真实 RTL 仍然暴露契约里承诺的字段。"""
    missing = missing_fields(dut, contract)
    assert not missing, (
        f"{contract} 缺少测试依赖的字段: {', '.join(missing)}。\n"
        "如果只是改名，请同步更新 tests/dut_api.py 里的 PUBLIC_FIELDS 和访问器。"
    )
