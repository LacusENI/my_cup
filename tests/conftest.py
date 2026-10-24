"""
pytest fixtures: 每个 DUT 只 build 一次（session 级），测试用例复用。
"""

import os
from pathlib import Path
from types import SimpleNamespace

import pytest
from cocotb_tools.runner import get_runner

ROOT = Path(__file__).resolve().parents[1]
RTL = ROOT / "rtl"
INCLUDES = [ROOT / "rtl" / "core" / "include", ROOT / "lib"]
BUILD = ROOT / "build" / "cocotb"
WAVES = os.environ.get("MYCUP_WAVES") == "1"


def _build(toplevel: str, sources, build_name: str):
    runner = get_runner("icarus")
    # Icarus 要求 build 阶段就开启 waves，否则 test 阶段传 waves 无效
    build_dir = BUILD / (build_name + ("_wave" if WAVES else ""))
    runner.build(
        sources=sources,
        hdl_toplevel=toplevel,
        includes=INCLUDES,
        build_args=["-g2012"],
        timescale=("1ns", "1ps"),  # Icarus 不设这个，Timer(ns) 会报精度错误
        waves=WAVES,
        build_dir=build_dir,
    )
    return SimpleNamespace(runner=runner, build_dir=build_dir, toplevel=toplevel)


@pytest.fixture(scope="session")
def cpu_sim():
    """整个 cpu_top（全部 RTL）"""
    return _build("cpu_top", sorted(RTL.rglob("*.v")), "cpu_top")


@pytest.fixture(scope="session")
def alu_sim():
    """单元级：alu"""
    return _build("alu", [RTL / "core" / "units" / "alu.v"], "alu")
