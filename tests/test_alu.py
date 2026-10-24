"""把 tb_alu.py 里的 cocotb 用例包装成 pytest 用例。"""

import os
from pathlib import Path

TESTS = Path(__file__).resolve().parent
WAVES = os.environ.get("MYCUP_WAVES") == "1"


def _run(sim, testcase: str) -> None:
    sim.runner.test(
        hdl_toplevel=sim.toplevel,
        test_module="tb_alu",
        testcase=testcase,
        test_dir=TESTS,
        build_dir=sim.build_dir,
        waves=WAVES,
    )


def test_alu_add(alu_sim):
    _run(alu_sim, "alu_add_test")


def test_alu_sub(alu_sim):
    _run(alu_sim, "alu_sub_test")
