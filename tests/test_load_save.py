"""把 tb_load_save.py 的指令级用例包装成 pytest 用例。"""

import os
from pathlib import Path

TESTS = Path(__file__).resolve().parent
WAVES = os.environ.get("MYCUP_WAVES") == "1"


def test_load_save(cpu_sim):
    cpu_sim.runner.test(
        hdl_toplevel=cpu_sim.toplevel,
        test_module="tb_load_save",
        testcase="load_save_test",
        test_dir=TESTS,
        build_dir=cpu_sim.build_dir,
        waves=WAVES,
    )
