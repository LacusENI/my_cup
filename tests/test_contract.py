"""契约测试的 pytest 入口：每个 DUT 跑一次 tb_contract 里对应的用例。"""

import pytest

from dut_api import PUBLIC_FIELDS

# (契约名, 对应的 session fixture)
CONTRACT_CASES = [
    ("cpu_top", "cpu_sim"),
    ("alu", "alu_sim"),
    ("ctrl", "ctrl_sim"),
    ("datam", "datam_sim"),
    ("npc", "npc_sim"),
    ("regfile", "regfile_sim"),
    ("if_id_reg", "if_id_sim"),
    ("id_ex_reg", "id_ex_sim"),
    ("ex_mem_reg", "ex_mem_sim"),
    ("mem_wb_reg", "mem_wb_sim"),
]


@pytest.mark.parametrize("contract, sim_fixture", CONTRACT_CASES)
def test_contract(contract, sim_fixture, request, run_cocotb_case):
    """确认该 DUT 仍然有 PUBLIC_FIELDS 里承诺的字段。"""
    sim = request.getfixturevalue(sim_fixture)
    run_cocotb_case(sim, "tb_contract", f"{contract}_contract_test")


def test_contract_cases_match_manifest():
    """防止新增了 PUBLIC_FIELDS，却忘了在 CONTRACT_CASES 里加测试。"""
    assert {contract for contract, _ in CONTRACT_CASES} == set(PUBLIC_FIELDS)
