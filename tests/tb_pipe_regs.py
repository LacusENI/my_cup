"""
流水线级间寄存器的单元测试。

四个寄存器（IF/ID、ID/EX、EX/MEM、MEM/WB）行为完全一样：
  - rst / flush：输出清 0（插入气泡）
  - stall      ：输出保持不变（暂停流水线）
  - 正常        ：上升沿把输入打一拍

每个寄存器都用一个 struct packed（if_id_t、id_ex_t、ex_mem_t、mem_wb_t）承载数据。
由于 Icarus 的 VPI 不暴露 struct 字段，这里直接把 struct 当成一个整数来读写，
验证“复位 / 装载 / 保持 / 冲刷”四种行为。
"""

import cocotb
from cocotb.triggers import ReadOnly, RisingEdge

from cocotb_utils import settle, start_clock

# 两个有辨识度的位模式
PATTERN = 0x1234_5678_9ABC_DEF0
NEW_PATTERN = 0x0FED_CBA9_8765_4321


async def check_pipe_register(dut, input_name: str, output_name: str):
    """通用的流水线寄存器测试。

    参数：
      input_name  : 输入 struct 的信号名（例如 "if_id_in"）
      output_name : 输出 struct 的信号名（例如 "if_id_out"）
    """
    input_signal = getattr(dut, input_name)
    output_signal = getattr(dut, output_name)

    await start_clock(dut)

    # 1. 复位：无论输入是什么，输出都应该是 0
    dut.rst.value = 1
    dut.flush.value = 0
    dut.stall.value = 0
    input_signal.value = PATTERN
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(output_signal.value) == 0, "复位后输出应该全 0"
    await settle()

    # 2. 正常装载：上升沿后，输出应该等于输入
    dut.rst.value = 0
    input_signal.value = PATTERN
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(output_signal.value) == PATTERN, "正常时钟沿应该把输入打一拍"
    await settle()

    # 3. 停顿：stall=1 时，输出应该保持旧值
    dut.stall.value = 1
    input_signal.value = NEW_PATTERN
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(output_signal.value) == PATTERN, "stall=1 时输出应该保持不变"
    await settle()

    # 4. 冲刷：flush=1 时，输出应该清 0
    dut.stall.value = 0
    dut.flush.value = 1
    input_signal.value = NEW_PATTERN
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(output_signal.value) == 0, "flush=1 时输出应该清 0"


@cocotb.test()
async def if_id_register_test(dut):
    """IF/ID：复位 / 装载 / 停顿 / 冲刷。"""
    await check_pipe_register(dut, "if_id_in", "if_id_out")


@cocotb.test()
async def id_ex_register_test(dut):
    """ID/EX：复位 / 装载 / 停顿 / 冲刷。"""
    await check_pipe_register(dut, "id_ex_in", "id_ex_out")


@cocotb.test()
async def ex_mem_register_test(dut):
    """EX/MEM：复位 / 装载 / 停顿 / 冲刷。"""
    await check_pipe_register(dut, "ex_mem_in", "ex_mem_out")


@cocotb.test()
async def mem_wb_register_test(dut):
    """MEM/WB：复位 / 装载 / 停顿 / 冲刷。"""
    await check_pipe_register(dut, "mem_wb_in", "mem_wb_out")
