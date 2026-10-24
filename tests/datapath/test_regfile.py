"""regfile 的 pytest 包装：每个函数对应 tb_regfile.py 里的一个用例。"""


def test_contract(regfile_sim, run_cocotb_case):
    """regfile 的公开字段契约。"""
    run_cocotb_case(regfile_sim, "tb_regfile", "contract_test")


def test_regfile_write_read(regfile_sim, run_cocotb_case):
    """写入后能正确读回。"""
    run_cocotb_case(regfile_sim, "tb_regfile", "write_read_test")


def test_regfile_zero_register(regfile_sim, run_cocotb_case):
    """$0 恒为零。"""
    run_cocotb_case(regfile_sim, "tb_regfile", "zero_register_test")


def test_regfile_two_read_ports(regfile_sim, run_cocotb_case):
    """两个读端口互不影响。"""
    run_cocotb_case(regfile_sim, "tb_regfile", "two_read_ports_test")


def test_regfile_write_disable(regfile_sim, run_cocotb_case):
    """写使能关闭时寄存器不变。"""
    run_cocotb_case(regfile_sim, "tb_regfile", "write_disable_test")
