"""
cocotb 常用小工具（带详细注释，方便第一次接触的同学阅读）。

这些函数都很短，目的只有一个：
把“等待/时钟/复位”这类重复动作收起来，让测试本身更像自然语言。

这里只放**多个测试共用**的 CPU 顶层接口和通用工具。
各单元 DUT（alu / ctrl / ...）的 Protocol 和契约字段，
放在各自的 `test_*.py` 里，方便就近阅读和修改。
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol, Sequence

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ReadOnly, RisingEdge, Timer

# tests/ 的绝对路径。cocotb 的 runner.test(test_dir=TESTS) 会把它放进
# 仿真器进程的 sys.path，因此模块名要写成 "datapath.test_alu" 这种形式。
TESTS_ROOT = Path(__file__).resolve().parents[1]


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

    cpu_top 的完整公开字段在 tests/cpu/test_inst.py 的 CpuTop 协议里声明；
    这里只是让 run_program / read_reg 等工具函数有个类型可写。
    """

    clk: Signal
    rst: Signal
    halt: Signal
    halt_cause: Signal
    u_pc: Pc
    u_regfile: RegFile
    u_instm: Memory
    u_datam: Memory


# --------------------------------------------------------------------------- #
# CPU 顶层常见访问器：把内部路径收口到一处
# --------------------------------------------------------------------------- #
def read_pc(dut: CpuAccess) -> int:
    """当前 PC。"""
    return int(dut.u_pc.curr_pc.value)


def read_reg(dut: CpuAccess, index: int) -> int:
    """读通用寄存器；x0 按架构语义恒为 0。"""
    if index == 0:
        return 0
    return int(dut.u_regfile.regs[index].value)


def read_reg_raw(dut: CpuAccess, index: int) -> int:
    """直接读内部寄存器数组，用于验证 x0 写保护。

    正常测试请使用 read_reg；这个函数会暴露未初始化寄存器的 X，
    所以调用前应先把目标寄存器预置成已知值。
    """
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


def write_inst(dut: CpuAccess, word_index: int, instruction: int) -> None:
    """把机器码写进指令存储器。"""
    dut.u_instm.mem[word_index].value = instruction


# --------------------------------------------------------------------------- #
# 契约检查：每个测试文件自己提供字段列表
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
        f"如果只是改名，请同步更新对应测试文件里的契约测试。"
    )


# --------------------------------------------------------------------------- #
# 把 cocotb test 同时变成 pytest 用例
# --------------------------------------------------------------------------- #
def _cocotb_module_name(fn) -> str:
    """返回 cocotb runner 能 import 的模块名，例如 ``datapath.test_alu``。

    为什么不直接用 ``fn.__module__``：
    pytest 和仿真器是两个进程，它们不保证用同一个模块名导入测试文件
    （可能是 ``test_alu``，也可能是 ``datapath.test_alu``）。
    这里根据源文件路径计算，两个进程得到的结果一致。
    """
    path = Path(fn.__code__.co_filename).resolve()
    try:
        relative = path.relative_to(TESTS_ROOT)
    except ValueError:
        # 测试文件不在 tests/ 下时退回到 Python 自己的模块名。
        return fn.__module__
    return relative.with_suffix("").as_posix().replace("/", ".")


def cocotb_test(
    *,
    dut: str,
    plusargs: Sequence[str] | Callable[[], Sequence[str]] | None = None,
    **cocotb_kwargs: Any,
):
    """把 ``async def test_xxx(dut)`` 同时注册成 cocotb test 和 pytest 用例。

    背景（这层装饰器到底在解决什么）：

    1. pytest 进程只负责“启动仿真器”。真正执行测试的是仿真器里内嵌的
       Python 进程；两个进程之间没有共享对象。
    2. ``@cocotb.test()`` 返回的是 ``TestGenerator`` 对象，pytest 默认
       不会收集它（它只收集普通函数/类）。
    3. 所以这里做两件事：
       - 把原始 async 函数注册成 cocotb test；
       - 返回一个普通同步函数 wrapper，让 pytest 把它当成普通 test_* 用例。
    4. 仿真器里的 cocotb 通过扫描模块属性找 ``TestGenerator``。
       原始 async 函数已经被 wrapper 替换掉了，因此这里额外把
       ``TestGenerator`` 挂到模块的私有属性上，供 cocotb 发现。

    参数：
      dut:
        conftest.py 里的 fixture 名，例如 ``"alu_sim"``。
        wrapper 运行时通过 ``request.getfixturevalue(dut)`` 拿到它。
      plusargs:
        传给 ``runner.test()`` 的 plusargs；也可以传一个函数，运行时再求值。
        例如 program 级测试需要 ``+inst=...``。
      **cocotb_kwargs:
        原样传给 ``cocotb.test()``，例如 ``timeout_time`` / ``skip`` / ``expect_fail``。

    注意：
      - **不要**在 wrapper 上用 ``functools.wraps``。它会设置 ``__wrapped__``，
        pytest 通过 ``inspect.signature`` 会看到原函数的 ``dut`` 参数，
        于是误以为需要注入 ``dut`` fixture，而不是这里的 ``request``。
      - pytest 的 marker 建议写在 ``@cocotb_test(...)`` 外层，例如
        ``@pytest.mark.xfail``；这里也会复制内层的 ``pytestmark``，两种顺序
        都能工作，但外层最直观。
      - 测试函数请用 ``test_`` 前缀，这样 pytest 和 cocotb 两边名字一致。
    """

    def decorate(fn):
        # 第一步：注册成 cocotb test。cocotb_kwargs 原样透传，
        # 所以以后要用 timeout / expect_fail 时不需要改这个装饰器。
        test = cocotb.test(**cocotb_kwargs)(fn)

        # 第二步：把 TestGenerator 藏到模块属性里。
        # cocotb/regression.py 的 discover_tests() 会遍历 vars(module)，
        # 找到所有 TestGenerator 并执行；属性名本身不重要，只要不覆盖
        # wrapper 即可。这里用 __cocotb_ 前缀避免和普通名字冲突。
        module = sys.modules.get(fn.__module__)
        if module is not None:
            attr_name = f"__cocotb_{fn.__qualname__.replace('.', '_')}"
            setattr(module, attr_name, test)

        # 第三步：pytest 真正收集和执行的是这个普通同步函数。
        # 它通过 request 拿 DUT fixture 和 run_cocotb_case，再启动一次仿真。
        def wrapper(request):
            sim = request.getfixturevalue(dut)
            run_case = request.getfixturevalue("run_cocotb_case")
            actual_plusargs = plusargs() if callable(plusargs) else plusargs
            run_case(sim, _cocotb_module_name(fn), test.name, actual_plusargs)

        # 让 pytest / IDE 看到的名字和原测试一致。
        # 注意这里只复制必要的属性，不使用 functools.wraps（原因见 docstring）。
        wrapper.__name__ = fn.__name__
        wrapper.__qualname__ = fn.__qualname__
        wrapper.__module__ = fn.__module__
        wrapper.__doc__ = fn.__doc__
        # 如果 marker 写在 @cocotb_test 内层（先作用于原函数），
        # 这里把 pytestmark 复制到 wrapper 上，xfail/skip 才会生效。
        wrapper.pytestmark = list(getattr(fn, "pytestmark", []))
        # 方便调试：可以从 wrapper 反查原始的 cocotb TestGenerator。
        wrapper.__cocotb_test__ = test

        return wrapper

    return decorate


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
    wait_for_halt=True,
    max_cycles=2048,
):
    """装载一个“小程序”，复位，然后运行到 halt。

    参数：
      instructions : 机器码列表，从 mem[0] 开始依次写入
      registers    : 预置寄存器，例如 {1: 8} 表示 R1 = 8
      memory       : 预置数据内存，例如 {2: 0} 表示 mem[2] = 0（按字索引）
      extra_cycles : halt 后额外等待的周期数（默认 2）
      wait_for_halt: 是否等待 dut.halt 置 1；单指令测试设为 False
      max_cycles   : wait_for_halt=True 时的安全上限，防止程序不返回

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
        write_inst(dut, index, instruction)

    await reset_and_wait(dut)

    if wait_for_halt:
        for _ in range(max_cycles):
            await RisingEdge(dut.clk)
            await settle()
            if int(dut.halt.value) == 1:
                break
        else:
            raise AssertionError(
                f"程序在 {max_cycles} 个周期内没有进入 halt"
            )
        await wait_cycles(dut, extra_cycles)
    else:
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
        wait_for_halt=False,
    )
