"""流水线寄存器的 pytest 入口。"""


def test_if_id_register(if_id_sim, run_cocotb_case):
    """IF/ID：复位 / 装载 / 停顿 / 冲刷。"""
    run_cocotb_case(if_id_sim, "tb_pipe_regs", "if_id_register_test")


def test_id_ex_register(id_ex_sim, run_cocotb_case):
    """ID/EX：复位 / 装载 / 停顿 / 冲刷。"""
    run_cocotb_case(id_ex_sim, "tb_pipe_regs", "id_ex_register_test")


def test_ex_mem_register(ex_mem_sim, run_cocotb_case):
    """EX/MEM：复位 / 装载 / 停顿 / 冲刷。"""
    run_cocotb_case(ex_mem_sim, "tb_pipe_regs", "ex_mem_register_test")


def test_mem_wb_register(mem_wb_sim, run_cocotb_case):
    """MEM/WB：复位 / 装载 / 停顿 / 冲刷。"""
    run_cocotb_case(mem_wb_sim, "tb_pipe_regs", "mem_wb_register_test")
