"""datam 的 pytest 包装：每个函数对应 tb_datam.py 里的一个用例。"""


def test_datam_write_read_word(datam_sim, run_cocotb_case):
    """整字写入再读出。"""
    run_cocotb_case(datam_sim, "tb_datam", "write_read_word_test")


def test_datam_write_disable(datam_sim, run_cocotb_case):
    """写使能关闭时数据不变。"""
    run_cocotb_case(datam_sim, "tb_datam", "write_disable_test")


def test_datam_read_disable(datam_sim, run_cocotb_case):
    """读使能关闭时输出 0。"""
    run_cocotb_case(datam_sim, "tb_datam", "read_disable_test")
