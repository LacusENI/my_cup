"""
cocotb 常用小工具（带详细注释，方便第一次接触的同学阅读）。

这些函数都很短，目的只有一个：
把“等待/时钟/复位”这类重复动作收起来，让测试本身更像自然语言。

这里只放**多个测试共用**的 CPU 顶层接口和通用工具。
各单元 DUT（alu / ctrl / ...）的 Protocol 和契约字段，
放在各自的 `tb_*.py` 里，方便就近阅读和修改。
"""

from __future__ import annotations

from typing import Any, Protocol, Sequence

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ReadOnly, RisingEdge, Timer


# --------------------------------------------------------------------------- #
# 共享类型
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


class CpuAccess(Protocol):
    """共享访问器需要的最小 CPU 顶层接口。

    cpu_top 的完整公开字段在 tb_instr.py 里声明；
    这里只是让 run_program / read_reg 等工具函数有个类型可写。
    """

    clk: Signal
    rst: Signal
    u_pc: Pc
    u_regfile: RegFile
    u_instrm: Memory
    u_datam: Memory


# --------------------------------------------------------------------------- #
# CPU 顶层常见访问器：把内部路径收口到一处
# --------------------------------------------------------------------------- #
def read_pc(dut: CpuAccess) -> int:
    """当前 PC。"""
    return int(dut.u_pc.curr_pc.value)


def read_reg(dut: CpuAccess, index: int) -> int:
    """读通用寄存器。"""
    return int(dut.u_regfile.regs[index].value)


def write_reg(dut: CpuAccess, index: int, value: int) -> None:
    """预置通用寄存器（测试用）。"""
    dut.u_regfile.regs[index].value = value


def read_mem(dut: CpuAccess, word_index: int) -> int:
    """读数据内存的一个字（按字索引，不是字节地址）。"""
    return int(dut.u_datam.mem[word_index].value)


def write_mem(dut: CpuAccess, word_index: int, value: int) -> None:
    """预置数据内存的一个字（测试用）。"""
    dut.u_datam.mem[word_index].value = value


def write_instr(dut: CpuAccess, word_index: int, instruction: int) -> None:
    """把机器码写进指令存储器。"""
    dut.u_instrm.mem[word_index].value = instruction


# --------------------------------------------------------------------------- #
# 契约检查：每个 tb_*.py 自己提供字段列表
# --------------------------------------------------------------------------- #
def assert_fields(dut: Any, fields: tuple[str, ...], owner: str) -> None:
    """检查 DUT 是否暴露 `fields` 里列出的字段路径。

    参数：
      dut    : cocotb 顶层句柄
      fields : 例如 ("u_pc.curr_pc", "u_regfile.regs")
      owner  : 出错的模块名，用于提示信息
    """
    missing: list[str] = []

    for path in fields:
        obj = dut
        for part in path.split("."):
            try:
                obj = obj[part]
            except (KeyError, AttributeError):
                missing.append(path)
                break

    assert not missing, (
        f"{owner} 缺少测试依赖的字段: {', '.join(missing)}。\n"
        f"如果只是改名，请同步更新对应的 tb_*.py 契约测试。"
    )


# --------------------------------------------------------------------------- #
# 等待 / 时钟 / 复位
# --------------------------------------------------------------------------- #
async def settle():
    """等待 1ns，让组合逻辑完成计算。

    在 cocotb 里给 dut.xxx 赋值后，信号不会“瞬间”全部更新；
    组合逻辑需要一点仿真时间。等 1ns 足够让它稳定。
    """
    await Timer(1, unit="ns")


async def start_clock(dut: HasClock, period_ns=10):
    """启动一个周期为 period_ns 的时钟。

    Clock(...).start() 是一个协程（可以理解成“一直运行的时钟任务”）。
    start_soon 让它在后台跑，这样下面的测试步骤还能继续执行。
    """
    cocotb.start_soon(Clock(dut.clk, period_ns, unit="ns").start())


async def reset_and_wait(dut: CpuAccess):
    """给 DUT 一个复位脉冲，然后释放复位。

    步骤：
      1. 拉高 rst
      2. 等一个上升沿（让复位生效）
      3. 拉低 rst（开始正常工作）
    """
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    dut.rst.value = 0


async def wait_cycles(dut: HasClock, count: int):
    """等待 count 个时钟上升沿。"""
    for _ in range(count):
        await RisingEdge(dut.clk)


# --------------------------------------------------------------------------- #
# 程序装载 / 单指令执行
# --------------------------------------------------------------------------- #
async def run_program(
    dut: CpuAccess,
    instructions,
    registers=None,
    memory=None,
    extra_cycles=2,
):
    """装载一个“小程序”，复位，然后跑若干周期。

    参数：
      instructions : 机器码列表，从 mem[0] 开始依次写入
      registers    : 预置寄存器，例如 {1: 8} 表示 R1 = 8
      memory       : 预置数据内存，例如 {2: 0} 表示 mem[2] = 0（按字索引）
      extra_cycles : 指令跑完后额外多等几拍，保证写回完成

    注意：
      - 指令存储器是“按字索引”的，mem[0] 对应地址 0；
      - 数据内存也是“按字索引”的。
    """
    await start_clock(dut)

    # 预置寄存器和数据内存（具体路径收口在访问器里）
    for reg_index, value in (registers or {}).items():
        write_reg(dut, reg_index, value)
    for word_index, value in (memory or {}).items():
        write_mem(dut, word_index, value)

    # 装载指令
    for index, instruction in enumerate(instructions):
        write_instr(dut, index, instruction)

    # 复位，然后跑 len(instructions) + extra_cycles 个周期
    await reset_and_wait(dut)
    await wait_cycles(dut, len(instructions) + extra_cycles)

    # 等到只读阶段再断言，确保所有信号都已经稳定
    await ReadOnly()


async def run_one_instruction(
    dut: CpuAccess, instruction, registers=None, memory=None
):
    """执行“一条”指令，然后停在只读阶段。

    这是 ISA 级测试的基础：
      - 只关心架构状态（PC / 寄存器 / 数据内存）；
      - 不关心流水线级数、停顿、前递等微架构细节。

    目前是单周期 CPU：复位后一个上升沿就执行完一条指令。
    以后接流水线时，这里应该改成“等到 retire/commit 信号”，
    而不是依赖固定周期数。
    """
    await run_program(
        dut,
        instructions=[instruction],
        registers=registers,
        memory=memory,
        extra_cycles=0,
    )
