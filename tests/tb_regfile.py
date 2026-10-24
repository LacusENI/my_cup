"""
regfile（寄存器堆）的单元测试。

regfile 的行为：
  - 读：组合读；读 $0 永远得到 0
  - 写：时钟上升沿，如果 reg_write=1 且目标不是 $0，就写入

注意：
  - 写是“时钟上升沿”发生的，所以要先设置好 reg_dst/wb_data，再等上升沿；
  - 读是组合逻辑，等一会儿就能读到。
"""

import cocotb
from cocotb.triggers import ReadOnly, RisingEdge

from cocotb_utils import start_clock


@cocotb.test()
async def write_read_test(dut):
    """写 R5，再从读端口 1 读回来。"""
    await start_clock(dut)

    # 写：R5 = 0xDEADBEEF
    dut.reg_write.value = 1
    dut.reg_dst.value = 5
    dut.wb_data.value = 0xDEAD_BEEF
    await RisingEdge(dut.clk)   # 上升沿真正写入

    # 关闭写，改读端口，读 R5
    dut.reg_write.value = 0
    dut.reg_src1.value = 5
    await ReadOnly()

    assert int(dut.rs1_data.value) == 0xDEAD_BEEF, "R5 应该读回刚写入的值"


@cocotb.test()
async def zero_register_test(dut):
    """$0 永远读 0，即使尝试写它也不会改变。"""
    await start_clock(dut)

    # 尝试写 $0
    dut.reg_write.value = 1
    dut.reg_dst.value = 0
    dut.wb_data.value = 0xFFFF_FFFF
    await RisingEdge(dut.clk)

    # 读 $0
    dut.reg_write.value = 0
    dut.reg_src1.value = 0
    dut.reg_src2.value = 0
    await ReadOnly()

    assert int(dut.rs1_data.value) == 0, "$0 读出来必须是 0"
    assert int(dut.rs2_data.value) == 0, "第二个读端口读 $0 也必须是 0"


@cocotb.test()
async def two_read_ports_test(dut):
    """两个读端口可以同时读出不同的寄存器。"""
    await start_clock(dut)

    # 写 R3 = 0x11111111
    dut.reg_write.value = 1
    dut.reg_dst.value = 3
    dut.wb_data.value = 0x1111_1111
    await RisingEdge(dut.clk)

    # 写 R7 = 0x22222222
    dut.reg_dst.value = 7
    dut.wb_data.value = 0x2222_2222
    await RisingEdge(dut.clk)

    # 同时读 R3 和 R7
    dut.reg_write.value = 0
    dut.reg_src1.value = 3
    dut.reg_src2.value = 7
    await ReadOnly()

    assert int(dut.rs1_data.value) == 0x1111_1111, "读端口 1 应该读到 R3"
    assert int(dut.rs2_data.value) == 0x2222_2222, "读端口 2 应该读到 R7"


@cocotb.test()
async def write_disable_test(dut):
    """reg_write=0 时，不能改写寄存器。"""
    await start_clock(dut)

    # 先写 R6 = 0xAAAAAAAA
    dut.reg_write.value = 1
    dut.reg_dst.value = 6
    dut.wb_data.value = 0xAAAA_AAAA
    await RisingEdge(dut.clk)

    # 关闭写使能，再给一个新值；这个新值不应该被写进去
    dut.reg_write.value = 0
    dut.wb_data.value = 0xBBBB_BBBB
    await RisingEdge(dut.clk)

    # 读回：应该还是旧值
    dut.reg_src1.value = 6
    await ReadOnly()
    assert int(dut.rs1_data.value) == 0xAAAA_AAAA, "写使能关闭时寄存器不应改变"
