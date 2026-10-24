"""ctrl 的 pytest 包装。

每个函数只做一件事：
  告诉 pytest “去跑 tb_ctrl.py 里的哪个 cocotb 用例”。

真正的测试步骤在 tb_ctrl.py 里，这样职责很清晰：
  - test_ctrl.py：pytest 的入口（收集、报告）
  - tb_ctrl.py  ：cocotb 的测试内容（激励、断言）
"""


def test_contract(ctrl_sim, run_cocotb_case):
    """ctrl 的公开字段契约。"""
    run_cocotb_case(ctrl_sim, "tb_ctrl", "contract_test")


def test_addu_control(ctrl_sim, run_cocotb_case):
    """addu 的控制信号。"""
    run_cocotb_case(ctrl_sim, "tb_ctrl", "addu_control_test")


def test_addiu_control(ctrl_sim, run_cocotb_case):
    """addiu 的控制信号。"""
    run_cocotb_case(ctrl_sim, "tb_ctrl", "addiu_control_test")


def test_beq_control(ctrl_sim, run_cocotb_case):
    """beq 的控制信号。"""
    run_cocotb_case(ctrl_sim, "tb_ctrl", "beq_control_test")


def test_lw_control(ctrl_sim, run_cocotb_case):
    """lw 的控制信号。"""
    run_cocotb_case(ctrl_sim, "tb_ctrl", "lw_control_test")


def test_sw_control(ctrl_sim, run_cocotb_case):
    """sw 的控制信号。"""
    run_cocotb_case(ctrl_sim, "tb_ctrl", "sw_control_test")


def test_j_control(ctrl_sim, run_cocotb_case):
    """j 的控制信号。"""
    run_cocotb_case(ctrl_sim, "tb_ctrl", "j_control_test")


def test_jal_control(ctrl_sim, run_cocotb_case):
    """jal 的控制信号。"""
    run_cocotb_case(ctrl_sim, "tb_ctrl", "jal_control_test")


def test_jr_control(ctrl_sim, run_cocotb_case):
    """jr 的控制信号。"""
    run_cocotb_case(ctrl_sim, "tb_ctrl", "jr_control_test")
