"""lw/sw 的 pytest 包装。"""


def test_lw_sw(cpu_sim, run_cocotb_case):
    """先用 sw 写内存，再用 lw 读回来，验证整条访存链路。"""
    run_cocotb_case(cpu_sim, "tb_lw_sw", "lw_sw_test")
