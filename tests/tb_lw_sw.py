"""cocotb 测试模块：指令级 sw/lw 往返"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ReadOnly, RisingEdge

# 大端 MIPS 机器码
SW_3_0_1 = 0xAC230000  # sw $3, 0($1)
LW_2_0_1 = 0x8C220000  # lw $2, 0($1)


@cocotb.test()
async def lw_sw_test(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    # 初始化寄存器与内存（等价于旧 TB 直接改 regs/mem）
    dut.u_regfile.regs[1].value = 8
    dut.u_regfile.regs[3].value = 0x1122_3344
    dut.u_datam.mem[2].value = 0

    # 装载指令
    dut.u_instrm.mem[0].value = SW_3_0_1
    dut.u_instrm.mem[1].value = LW_2_0_1

    # 复位
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    dut.rst.value = 0

    # 执行 2 条指令（多等一拍保证写回完成）
    for _ in range(4):
        await RisingEdge(dut.clk)

    await ReadOnly()
    assert int(dut.u_datam.mem[2].value) == 0x1122_3344
    assert int(dut.u_regfile.regs[2].value) == 0x1122_3344
