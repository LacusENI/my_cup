"""npc 的 pytest 包装：每个函数对应 tb_npc.py 里的一个用例。"""


def test_npc_plus4(npc_sim, run_cocotb_case):
    """顺序执行：PC + 4。"""
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


def test_npc_direct_jump(npc_sim, run_cocotb_case):
    """j / jal 的直接跳转。"""
    run_cocotb_case(npc_sim, "tb_npc", "direct_jump_test")


def test_npc_jump_register(npc_sim, run_cocotb_case):
    """jr 的寄存器跳转。"""
    run_cocotb_case(npc_sim, "tb_npc", "jump_register_test")
