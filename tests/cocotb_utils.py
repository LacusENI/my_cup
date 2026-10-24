"""
cocotb 常用小工具（带详细注释，方便第一次接触的同学阅读）。

这些函数都很短，目的只有一个：
把“等待/时钟/复位”这类重复动作收起来，让测试本身更像自然语言。
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


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
