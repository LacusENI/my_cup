"""ctrl 的 pytest 包装：每个函数对应 tb_ctrl.py 里的一个用例。"""


def test_contract(ctrl_sim, run_cocotb_case):
    """ctrl 的公开字段契约。"""
    run_cocotb_case(ctrl_sim, "tb_ctrl", "contract_test")


def test_add_control(ctrl_sim, run_cocotb_case):
    """add 的控制信号。"""
    run_cocotb_case(ctrl_sim, "tb_ctrl", "add_control_test")


def test_addi_control(ctrl_sim, run_cocotb_case):
    """addi 的控制信号。"""
    run_cocotb_case(ctrl_sim, "tb_ctrl", "addi_control_test")


def test_beq_control(ctrl_sim, run_cocotb_case):
    """beq 的控制信号。"""
    run_cocotb_case(ctrl_sim, "tb_ctrl", "beq_control_test")


def test_lw_control(ctrl_sim, run_cocotb_case):
    """lw 的控制信号。"""
    run_cocotb_case(ctrl_sim, "tb_ctrl", "lw_control_test")


def test_sw_control(ctrl_sim, run_cocotb_case):
    """sw 的控制信号。"""
    run_cocotb_case(ctrl_sim, "tb_ctrl", "sw_control_test")


def test_jal_control(ctrl_sim, run_cocotb_case):
    """jal 的控制信号。"""
    run_cocotb_case(ctrl_sim, "tb_ctrl", "jal_control_test")


def test_jalr_control(ctrl_sim, run_cocotb_case):
    """jalr 的控制信号。"""
    run_cocotb_case(ctrl_sim, "tb_ctrl", "jalr_control_test")


def test_illegal_control(ctrl_sim, run_cocotb_case):
    """非法指令的控制信号。"""
    run_cocotb_case(ctrl_sim, "tb_ctrl", "illegal_control_test")
