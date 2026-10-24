"""指令级测试的 pytest 包装：每个函数对应 tb_instr.py 里的一个用例。"""

import os
from pathlib import Path

# 默认用 demo.hex；也可以通过 MYCUP_PROG 环境变量指定别的程序（mycup prog 会设置）
DEMO_PROGRAM = Path(__file__).resolve().parents[1] / "programs" / "demo.hex"
PROGRAM = Path(os.environ.get("MYCUP_PROG", str(DEMO_PROGRAM)))
DATA_FILE = os.environ.get("MYCUP_DATA")


def test_addu(cpu_sim, run_cocotb_case):
    """addu：5 + 3 = 8。"""
    run_cocotb_case(cpu_sim, "tb_instr", "addu_test")


def test_addiu(cpu_sim, run_cocotb_case):
    """addiu：正数立即数 + 负数立即数（符号扩展）。"""
    run_cocotb_case(cpu_sim, "tb_instr", "addiu_test")


def test_beq_taken(cpu_sim, run_cocotb_case):
    """beq 成立：跳过下一条。"""
    run_cocotb_case(cpu_sim, "tb_instr", "beq_taken_test")


def test_beq_not_taken(cpu_sim, run_cocotb_case):
    """beq 不成立：顺序执行。"""
    run_cocotb_case(cpu_sim, "tb_instr", "beq_not_taken_test")


def test_j(cpu_sim, run_cocotb_case):
    """j：直接跳转。"""
    run_cocotb_case(cpu_sim, "tb_instr", "j_test")


def test_jal(cpu_sim, run_cocotb_case):
    """jal：跳转并写 $ra。"""
    run_cocotb_case(cpu_sim, "tb_instr", "jal_test")


def test_jr(cpu_sim, run_cocotb_case):
    """jr：跳到寄存器地址。"""
    run_cocotb_case(cpu_sim, "tb_instr", "jr_test")


def test_lw_sw(cpu_sim, run_cocotb_case):
    """sw 写内存，lw 读回。"""
    run_cocotb_case(cpu_sim, "tb_instr", "lw_sw_test")


def test_prog_demo(cpu_sim, run_cocotb_case):
    """用 hex 程序验证 $readmemh 程序装载（默认 programs/demo.hex）。"""
    plusargs = [f"+instr={PROGRAM}"]
    if DATA_FILE:
        plusargs.append(f"+data={DATA_FILE}")
    run_cocotb_case(
        cpu_sim,
        "tb_instr",
        "prog_demo_test",
        plusargs=plusargs,
    )
