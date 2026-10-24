"""cocotb 测试模块：指令级 sb/sh/lw（对应旧 sim/tb/instr/tb_load_save.v）"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ReadOnly, RisingEdge

# 大端 MIPS 机器码
SB_3_0_1 = 0xA0230000  # sb $3, 0($1)
SB_3_1_1 = 0xA0230001  # sb $3, 1($1)
SH_4_2_1 = 0xA4240002  # sh $4, 2($1)
LW_2_0_1 = 0x8C220000  # lw $2, 0($1)


@cocotb.test()
async def load_save_test(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    # 初始化寄存器与内存（等价于旧 TB 直接改 regs/mem）
    dut.u_regfile.regs[1].value = 8
    dut.u_regfile.regs[3].value = 0x0000_00AA
    dut.u_regfile.regs[4].value = 0x0000_BBCC
    dut.u_regfile.regs[5].value = 0x1122_3344
    dut.u_datam.mem[2].value = 0

    # 装载指令
    dut.u_instrm.mem[0].value = SB_3_0_1
    dut.u_instrm.mem[1].value = SB_3_1_1
    dut.u_instrm.mem[2].value = SH_4_2_1
    dut.u_instrm.mem[3].value = LW_2_0_1

    # 复位
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    dut.rst.value = 0

    # 执行 4 条指令（多等一拍保证写回完成）
    for _ in range(5):
        await RisingEdge(dut.clk)

    await ReadOnly()
    assert int(dut.u_datam.mem[2].value) == 0xAAAA_BBCC
    assert int(dut.u_regfile.regs[2].value) == 0xAAAA_BBCC
