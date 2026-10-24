"""
cocotb 常用小工具（带详细注释，方便第一次接触的同学阅读）。

这些函数都很短，目的只有一个：
把“等待/时钟/复位”这类重复动作收起来，让测试本身更像自然语言。
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ReadOnly, RisingEdge, Timer


async def settle():
    """等待 1ns，让组合逻辑完成计算。

    在 cocotb 里给 dut.xxx 赋值后，信号不会“瞬间”全部更新；
    组合逻辑需要一点仿真时间。等 1ns 足够让它稳定。
    """
    await Timer(1, unit="ns")


async def start_clock(dut, period_ns=10):
    """启动一个周期为 period_ns 的时钟。

    Clock(...).start() 是一个协程（可以理解成“一直运行的时钟任务”）。
    start_soon 让它在后台跑，这样下面的测试步骤还能继续执行。
    """
    cocotb.start_soon(Clock(dut.clk, period_ns, unit="ns").start())


async def reset_and_wait(dut):
    """给 DUT 一个复位脉冲，然后释放复位。

    步骤：
      1. 拉高 rst
      2. 等一个上升沿（让复位生效）
      3. 拉低 rst（开始正常工作）
    """
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    dut.rst.value = 0


async def wait_cycles(dut, count):
    """等待 count 个时钟上升沿。"""
    for _ in range(count):
        await RisingEdge(dut.clk)


async def run_program(dut, instructions, registers=None, memory=None, extra_cycles=2):
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

    # 预置寄存器和数据内存（相当于旧 TB 里直接改 regs/mem）
    for reg_index, value in (registers or {}).items():
        dut.u_regfile.regs[reg_index].value = value
    for word_index, value in (memory or {}).items():
        dut.u_datam.mem[word_index].value = value

    # 装载指令
    for index, instruction in enumerate(instructions):
        dut.u_instrm.mem[index].value = instruction

    # 复位，然后跑 len(instructions) + extra_cycles 个周期
    await reset_and_wait(dut)
    await wait_cycles(dut, len(instructions) + extra_cycles)

    # 等到只读阶段再断言，确保所有信号都已经稳定
    await ReadOnly()
