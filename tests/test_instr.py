"""ISA 级测试的 pytest 入口：每个函数对应 tb_instr.py 里的一个单指令用例。"""


def test_contract(cpu_sim, run_cocotb_case):
    """cpu_top 的公开字段契约。"""
    run_cocotb_case(cpu_sim, "tb_instr", "contract_test")


def test_addu(cpu_sim, run_cocotb_case):
    """addu：5 + 3 = 8。"""
    run_cocotb_case(cpu_sim, "tb_instr", "addu_test")


def test_addiu_positive(cpu_sim, run_cocotb_case):
    """addiu 正数立即数。"""
    run_cocotb_case(cpu_sim, "tb_instr", "addiu_positive_test")


def test_addiu_negative(cpu_sim, run_cocotb_case):
    """addiu 负数立即数（符号扩展）。"""
    run_cocotb_case(cpu_sim, "tb_instr", "addiu_negative_test")


def test_beq_taken(cpu_sim, run_cocotb_case):
    """beq 成立：只断言 PC。"""
    run_cocotb_case(cpu_sim, "tb_instr", "beq_taken_test")


def test_beq_not_taken(cpu_sim, run_cocotb_case):
    """beq 不成立：只断言 PC。"""
    run_cocotb_case(cpu_sim, "tb_instr", "beq_not_taken_test")


def test_j(cpu_sim, run_cocotb_case):
    """j：只断言 PC。"""
    run_cocotb_case(cpu_sim, "tb_instr", "j_test")


def test_jal(cpu_sim, run_cocotb_case):
    """jal：断言 PC 和 $31。"""
    run_cocotb_case(cpu_sim, "tb_instr", "jal_test")


def test_jr(cpu_sim, run_cocotb_case):
    """jr：只断言 PC。"""
    run_cocotb_case(cpu_sim, "tb_instr", "jr_test")


def test_lw(cpu_sim, run_cocotb_case):
    """lw：断言寄存器。"""
    run_cocotb_case(cpu_sim, "tb_instr", "lw_test")


def test_sw(cpu_sim, run_cocotb_case):
    """sw：断言内存。"""
    run_cocotb_case(cpu_sim, "tb_instr", "sw_test")
