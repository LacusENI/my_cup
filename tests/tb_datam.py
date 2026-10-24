"""
datam（数据存储器）的单元测试。

datam 的行为很简单：
  - 写：时钟上升沿，如果 mem_write=1，就把 w_data 写进 mem[addr]
  - 读：组合读，如果 mem_read=1，r_data 就等于 mem[addr]

注意：
  - 写是“时钟上升沿”发生的，所以要先设置好 addr/w_data，再等上升沿；
  - 读是组合逻辑，等一会儿就能读到；
  - mem_read=0 时，r_data 固定为 0。
"""

from typing import Protocol, Sequence

import cocotb
from cocotb.triggers import ReadOnly, RisingEdge

from cocotb_utils import Signal, assert_fields, settle, start_clock

# 地址 0x80 是 4 的倍数，对应 mem[0x80 / 4] = mem[32]
ADDR = 0x0000_0080


# datam 的公开字段：测试依赖哪些，就列哪些。
class DatamDut(Protocol):
    clk: Signal
    mem_read: Signal
    mem_write: Signal
    addr: Signal
    w_data: Signal
    r_data: Signal
    mem: Sequence[Signal]


REQUIRED_FIELDS = (
    "clk",
    "mem_read",
    "mem_write",
    "addr",
    "w_data",
    "r_data",
    "mem",
)


@cocotb.test()
async def contract_test(dut: DatamDut):
    """契约：datam 仍然暴露读写端口和内部 mem。"""
    assert_fields(dut, REQUIRED_FIELDS, "datam")


@cocotb.test()
async def write_read_word_test(dut: DatamDut):
    """写一个整字，再读回来，应该得到同样的值。"""
    await start_clock(dut)

    # 第一步：写入 0xAABBCCDD
    dut.addr.value = ADDR
    dut.w_data.value = 0xAABB_CCDD
    dut.mem_write.value = 1
    dut.mem_read.value = 0
    await RisingEdge(dut.clk)   # 上升沿真正把数据写进内存

    # 第二步：切换成读模式
    dut.mem_write.value = 0
    dut.mem_read.value = 1
    await ReadOnly()            # 等组合逻辑稳定，再读取

    assert int(dut.r_data.value) == 0xAABB_CCDD, "读回来的字应该和写入一致"


@cocotb.test()
async def write_disable_test(dut: DatamDut):
    """mem_write=0 时，即使改 w_data，也不应该改写内存。"""
    await start_clock(dut)

    # 先写入一个已知值
    dut.addr.value = ADDR
    dut.w_data.value = 0x1122_3344
    dut.mem_write.value = 1
    dut.mem_read.value = 0
    await RisingEdge(dut.clk)

    # 关闭写使能，再给一个新值；这个新值不应该被写进去
    dut.mem_write.value = 0
    dut.w_data.value = 0xFFFF_FFFF
    await RisingEdge(dut.clk)

    # 读回：应该还是旧值
    dut.mem_read.value = 1
    await ReadOnly()
    assert int(dut.r_data.value) == 0x1122_3344, "写使能关闭时内存不应改变"


@cocotb.test()
async def read_disable_test(dut: DatamDut):
    """mem_read=0 时，r_data 固定输出 0。"""
    dut.addr.value = ADDR
    dut.mem_read.value = 0
    dut.mem_write.value = 0
    await settle()

    assert int(dut.r_data.value) == 0, "不读内存时 r_data 应该是 0"
