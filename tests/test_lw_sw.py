"""把 tb_lw_sw.py 的 sw/lw 指令级用例包装成 pytest 用例。"""

import os
from pathlib import Path

TESTS = Path(__file__).resolve().parent
WAVES = os.environ.get("MYCUP_WAVES") == "1"


def test_lw_sw(cpu_sim):
    cpu_sim.runner.test(
        hdl_toplevel=cpu_sim.toplevel,
        test_module="tb_lw_sw",
        testcase="lw_sw_test",
        test_dir=TESTS,
        build_dir=cpu_sim.build_dir,
        waves=WAVES,
    )
