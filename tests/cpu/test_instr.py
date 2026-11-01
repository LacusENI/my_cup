"""ISA 级测试的 pytest 入口：每个函数对应 tb_instr.py 里的一个单指令用例。"""


def test_contract(cpu_sim, run_cocotb_case):
    """cpu_top 的公开字段契约。"""
    run_cocotb_case(cpu_sim, "tb_instr", "contract_test")


def test_add(cpu_sim, run_cocotb_case):
    """add：5 + 3 = 8。"""
    run_cocotb_case(cpu_sim, "tb_instr", "add_test")


def test_add_wrap(cpu_sim, run_cocotb_case):
    """add 的 32 位回绕。"""
    run_cocotb_case(cpu_sim, "tb_instr", "add_wrap_test")


def test_addi_positive(cpu_sim, run_cocotb_case):
    """addi 正数立即数。"""
    run_cocotb_case(cpu_sim, "tb_instr", "addi_positive_test")


def test_addi_negative(cpu_sim, run_cocotb_case):
    """addi 负数立即数。"""
    run_cocotb_case(cpu_sim, "tb_instr", "addi_negative_test")


def test_addi_x0(cpu_sim, run_cocotb_case):
    """写 x0 被丢弃。"""
    run_cocotb_case(cpu_sim, "tb_instr", "addi_x0_test")


def test_beq_taken(cpu_sim, run_cocotb_case):
    """beq 成立。"""
    run_cocotb_case(cpu_sim, "tb_instr", "beq_taken_test")


def test_beq_not_taken(cpu_sim, run_cocotb_case):
    """beq 不成立。"""
    run_cocotb_case(cpu_sim, "tb_instr", "beq_not_taken_test")


def test_jal(cpu_sim, run_cocotb_case):
    """jal 的 link 和目标。"""
    run_cocotb_case(cpu_sim, "tb_instr", "jal_test")


def test_jal_x0(cpu_sim, run_cocotb_case):
    """jal x0 不写 x0。"""
    run_cocotb_case(cpu_sim, "tb_instr", "jal_x0_test")


def test_jalr(cpu_sim, run_cocotb_case):
    """jalr 的寄存器目标。"""
    run_cocotb_case(cpu_sim, "tb_instr", "jalr_test")


def test_jalr_rd_equals_rs1(cpu_sim, run_cocotb_case):
    """jalr rd==rs1 使用旧值。"""
    run_cocotb_case(cpu_sim, "tb_instr", "jalr_rd_equals_rs1_test")


def test_jalr_x0(cpu_sim, run_cocotb_case):
    """jalr x0 不写 x0。"""
    run_cocotb_case(cpu_sim, "tb_instr", "jalr_x0_test")


def test_lw(cpu_sim, run_cocotb_case):
    """lw 整字读取。"""
    run_cocotb_case(cpu_sim, "tb_instr", "lw_test")


def test_lw_negative_offset(cpu_sim, run_cocotb_case):
    """lw 负偏移。"""
    run_cocotb_case(cpu_sim, "tb_instr", "lw_negative_offset_test")


def test_sw(cpu_sim, run_cocotb_case):
    """sw 整字写入。"""
    run_cocotb_case(cpu_sim, "tb_instr", "sw_test")


def test_sw_negative_offset(cpu_sim, run_cocotb_case):
    """sw 负偏移。"""
    run_cocotb_case(cpu_sim, "tb_instr", "sw_negative_offset_test")


def test_illegal_stop(cpu_sim, run_cocotb_case):
    """非法指令停止。"""
    run_cocotb_case(cpu_sim, "tb_instr", "illegal_stop_test")
