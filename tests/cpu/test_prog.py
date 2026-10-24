"""程序装载测试的 pytest 入口。"""

import os
from pathlib import Path

# 默认用 demo.hex；也可以通过 MYCUP_PROG 环境变量指定别的程序（mycup prog 会设置）
# tests/cpu/test_prog.py -> 项目根目录
DEMO_PROGRAM = Path(__file__).resolve().parents[2] / "programs" / "demo.hex"
PROGRAM = Path(os.environ.get("MYCUP_PROG", str(DEMO_PROGRAM)))
DATA_FILE = os.environ.get("MYCUP_DATA")


def test_prog_demo(cpu_sim, run_cocotb_case):
    """用 hex 程序验证 $readmemh 程序装载（默认 programs/demo.hex）。"""
    plusargs = [f"+instr={PROGRAM}"]
    if DATA_FILE:
        plusargs.append(f"+data={DATA_FILE}")
    run_cocotb_case(
        cpu_sim,
        "tb_prog",
        "prog_demo_test",
        plusargs=plusargs,
    )
