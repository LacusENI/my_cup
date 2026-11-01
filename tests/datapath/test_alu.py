"""alu 的 pytest 包装：每个函数对应 tb_alu.py 里的一个用例。"""


def test_contract(alu_sim, run_cocotb_case):
    """alu 的公开字段契约。"""
    run_cocotb_case(alu_sim, "tb_alu", "contract_test")


def test_alu_add(alu_sim, run_cocotb_case):
    """加法：5 + 3 = 8。"""
    run_cocotb_case(alu_sim, "tb_alu", "alu_add_test")


def test_alu_add_wrap(alu_sim, run_cocotb_case):
    """加法回绕。"""
    run_cocotb_case(alu_sim, "tb_alu", "alu_add_wrap_test")


def test_alu_eq_true(alu_sim, run_cocotb_case):
    """相等比较：相等。"""
    run_cocotb_case(alu_sim, "tb_alu", "alu_eq_true_test")


def test_alu_eq_false(alu_sim, run_cocotb_case):
    """相等比较：不相等。"""
    run_cocotb_case(alu_sim, "tb_alu", "alu_eq_false_test")


def test_alu_nop(alu_sim, run_cocotb_case):
    """空操作。"""
    run_cocotb_case(alu_sim, "tb_alu", "alu_nop_test")
