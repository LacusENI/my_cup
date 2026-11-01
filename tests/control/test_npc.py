"""npc 的 pytest 包装：每个函数对应 tb_npc.py 里的一个用例。"""


def test_contract(npc_sim, run_cocotb_case):
    """npc 的公开字段契约。"""
    run_cocotb_case(npc_sim, "tb_npc", "contract_test")


def test_npc_plus4(npc_sim, run_cocotb_case):
    """顺序执行：PC+4。"""
    run_cocotb_case(npc_sim, "tb_npc", "plus4_test")


def test_npc_branch_taken(npc_sim, run_cocotb_case):
    """条件分支成立。"""
    run_cocotb_case(npc_sim, "tb_npc", "branch_taken_test")


def test_npc_branch_not_taken(npc_sim, run_cocotb_case):
    """条件分支不成立。"""
    run_cocotb_case(npc_sim, "tb_npc", "branch_not_taken_test")


def test_npc_branch_backward(npc_sim, run_cocotb_case):
    """负偏移（向后跳）。"""
    run_cocotb_case(npc_sim, "tb_npc", "branch_backward_test")


def test_npc_jal(npc_sim, run_cocotb_case):
    """jal 的 PC 目标。"""
    run_cocotb_case(npc_sim, "tb_npc", "jal_test")


def test_npc_jalr(npc_sim, run_cocotb_case):
    """jalr 的寄存器目标。"""
    run_cocotb_case(npc_sim, "tb_npc", "jalr_test")


def test_npc_illegal_hold(npc_sim, run_cocotb_case):
    """非法指令保持 PC。"""
    run_cocotb_case(npc_sim, "tb_npc", "illegal_hold_test")
