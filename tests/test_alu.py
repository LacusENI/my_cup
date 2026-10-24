"""alu 的 pytest 包装：每个函数对应 tb_alu.py 里的一个用例。"""


def test_contract(alu_sim, run_cocotb_case):
    """alu 的公开字段契约。"""
    run_cocotb_case(alu_sim, "tb_alu", "contract_test")


def test_alu_add(alu_sim, run_cocotb_case):
    """加法：5 + 3 = 8。"""
    run_cocotb_case(alu_sim, "tb_alu", "alu_add_test")


def test_alu_sub(alu_sim, run_cocotb_case):
    """减法：8 - 8 = 0，同时 zero 标志应该为 1。"""
    run_cocotb_case(alu_sim, "tb_alu", "alu_sub_test")
