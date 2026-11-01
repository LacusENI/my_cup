"""decoder 的 pytest 包装：每个函数对应 tb_decoder.py 里的一个用例。"""


def test_contract(decoder_sim, run_cocotb_case):
    """decoder 的公开字段契约。"""
    run_cocotb_case(decoder_sim, "tb_decoder", "contract_test")


def test_fields(decoder_sim, run_cocotb_case):
    """R 型字段切分。"""
    run_cocotb_case(decoder_sim, "tb_decoder", "fields_test")


def test_imm_i(decoder_sim, run_cocotb_case):
    """I 型立即数。"""
    run_cocotb_case(decoder_sim, "tb_decoder", "imm_i_test")


def test_imm_s(decoder_sim, run_cocotb_case):
    """S 型立即数。"""
    run_cocotb_case(decoder_sim, "tb_decoder", "imm_s_test")


def test_imm_b(decoder_sim, run_cocotb_case):
    """B 型立即数。"""
    run_cocotb_case(decoder_sim, "tb_decoder", "imm_b_test")


def test_imm_j(decoder_sim, run_cocotb_case):
    """J 型立即数。"""
    run_cocotb_case(decoder_sim, "tb_decoder", "imm_j_test")


def test_invalid_r_type(decoder_sim, run_cocotb_case):
    """未实现的 R 型指令。"""
    run_cocotb_case(decoder_sim, "tb_decoder", "invalid_r_type_test")


def test_invalid_opcode(decoder_sim, run_cocotb_case):
    """未知 opcode。"""
    run_cocotb_case(decoder_sim, "tb_decoder", "invalid_opcode_test")


def test_invalid_funct3(decoder_sim, run_cocotb_case):
    """非法 funct3。"""
    run_cocotb_case(decoder_sim, "tb_decoder", "invalid_funct3_test")


def test_invalid_funct3_matrix(decoder_sim, run_cocotb_case):
    """所有指令格式的非法 funct3。"""
    run_cocotb_case(decoder_sim, "tb_decoder", "invalid_funct3_matrix_test")
