"""
pytest fixtures：每个 DUT 只编译一次（session 级），多个测试复用。

这里有两个概念：
  1. *_sim fixture：负责“编译 HDL”，并保存后续运行测试需要的信息；
  2. run_cocotb_case：负责“启动一次仿真，跑一个 cocotb 测试用例”。

单独的 test_*.py 只负责挑选要跑哪个用例，具体仿真细节都在这里。
"""

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace

import pytest
from cocotb_tools.runner import get_runner

ROOT = Path(__file__).resolve().parents[1]
RTL = ROOT / "rtl"
PKG = RTL / "cpu_pkg.sv"
TESTS = Path(__file__).resolve().parent
# 让 pytest 进程也能 `from utils.xxx import ...`。
# cocotb 子进程里，runner.test(test_dir=TESTS) 会把 tests/ 放进 sys.path。
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))

# 现在没有需要 `include 的头文件了；cpu_pkg.sv 作为普通源文件编译。
INCLUDES: list[Path] = []
BUILD = ROOT / "build" / "cocotb"
WAVES = os.environ.get("MYCUP_WAVES") == "1"


def _rtl_sources() -> list[Path]:
    """全部 RTL 源文件，且 cpu_pkg.sv 必须排在最前面。"""
    files = sorted(p for p in RTL.rglob("*") if p.suffix == ".sv")
    package = [p for p in files if p.name == "cpu_pkg.sv"]
    return package + [p for p in files if p.name != "cpu_pkg.sv"]


def _build(toplevel: str, sources, build_name: str, module_prefix: str):
    """编译一个 DUT，返回后续 runner.test 需要的对象。

    参数说明：
      toplevel      : HDL 顶层模块名（例如 "ctrl"）
      sources       : 参与编译的 .sv 文件列表
      build_name    : build 目录名（不同 DUT 分开，互不覆盖）
      module_prefix : 测试模块所在目录，例如 "control" -> "control.test_ctrl"
    """
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
    return SimpleNamespace(
        runner=runner,
        build_dir=build_dir,
        toplevel=toplevel,
        module_prefix=module_prefix,
    )


# --------------------------------------------------------------------------- #
# 每个 DUT 一个 fixture
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session")
def cpu_sim():
    """整个 cpu_top（全部 RTL）。指令级测试用这个。"""
    return _build("cpu_top", _rtl_sources(), "cpu_top", "cpu")


@pytest.fixture(scope="session")
def alu_sim():
    """单元级：alu。"""
    return _build("alu", [PKG, RTL / "datapath" / "alu.sv"], "alu", "datapath")


@pytest.fixture(scope="session")
def ctrl_sim():
    """单元级：ctrl（纯组合逻辑），通过 test-only probe 观察 struct 字段。"""
    return _build(
        "ctrl_probe",
        [
            PKG,
            RTL / "control" / "ctrl.sv",
            TESTS / "hdl" / "ctrl_probe.sv",
        ],
        "ctrl_probe",
        "control",
    )


@pytest.fixture(scope="session")
def decoder_sim():
    """单元级：decoder（纯组合逻辑），通过 test-only probe 观察字段和立即数。"""
    return _build(
        "decoder_probe",
        [
            PKG,
            RTL / "control" / "decoder.sv",
            TESTS / "hdl" / "decoder_probe.sv",
        ],
        "decoder_probe",
        "control",
    )


@pytest.fixture(scope="session")
def datam_sim():
    """单元级：datam（数据存储器）。"""
    return _build("datam", [PKG, RTL / "memory" / "datam.sv"], "datam", "memory")


@pytest.fixture(scope="session")
def npc_sim():
    """单元级：npc（下一 PC，纯组合逻辑）。"""
    return _build("npc", [PKG, RTL / "control" / "npc.sv"], "npc", "control")


@pytest.fixture(scope="session")
def regfile_sim():
    """单元级：regfile（寄存器堆）。"""
    return _build(
        "regfile",
        [PKG, RTL / "datapath" / "regfile.sv"],
        "regfile",
        "datapath",
    )


# --------------------------------------------------------------------------- #
# 把一次 pytest 用例变成一次 cocotb 仿真
# --------------------------------------------------------------------------- #
def _format_cocotb_failure(results_xml: Path) -> str | None:
    """从 cocotb 的 xUnit XML 里提取失败信息。

    为什么要读 XML：
    - 断言发生在仿真器进程里，pytest 进程拿不到原始的 AssertionError；
    - cocotb 会把每个 testcase 的结果写进 results_xml；
    - runner.test() 在失败时只是 sys.exit(1)，pytest 默认只能看到
      “SystemExit: 1”，看不到具体断言。
    这里把 XML 里的 <failure>/<error> 拼成一段文本，再交给 pytest.fail()。
    """
    if not results_xml.is_file():
        return None

    try:
        root = ET.parse(results_xml).getroot()
    except ET.ParseError:
        return None

    parts: list[str] = []
    for testcase in root.iter("testcase"):
        for node in testcase:
            if node.tag not in ("failure", "error"):
                continue
            name = testcase.get("name", "<unknown>")
            message = (node.get("message") or "").strip()
            detail = (node.text or "").strip()
            text = f"{name}: {message}".strip()
            if detail:
                text += f"\n{detail}"
            parts.append(text)

    return "\n\n".join(parts) or None


@pytest.fixture
def run_cocotb_case():
    """返回一个函数：运行指定 cocotb 模块里的一个测试用例。

    这是 pytest 进程和仿真器进程之间的桥：

    - pytest 用例调用本 fixture 返回的 ``_run``；
    - ``_run`` 调用 ``runner.test()``，启动一次 ``vvp``；
    - ``vvp`` 里的 cocotb 执行 ``@cocotb_test`` 注册的 async 函数；
    - 结果写进 ``results_xml``，由这里翻译成 pytest 的 pass/fail。

    目前主要由 ``tests/utils/cocotb_utils.py`` 的 ``cocotb_test`` 装饰器调用，
    一般不需要在测试文件里手写 ``run_cocotb_case(...)``。
    """

    def _run(sim, test_module: str, testcase: str, plusargs=None):
        # 新写法传的是完整模块名（例如 "datapath.test_alu"）；
        # 旧的 "tb_alu" 写法仍然兼容，会自动补上 sim.module_prefix。
        if "." not in test_module:
            test_module = f"{sim.module_prefix}.{test_module}"

        # cocotb 默认会把 pytest 结果写成 tests/<testcase>.result.xml；
        # 这里显式指到 build/ 下，避免污染源码目录。
        results_xml = sim.build_dir / f"{testcase}.result.xml"
        try:
            sim.runner.test(
                hdl_toplevel=sim.toplevel,
                test_module=test_module,
                testcase=testcase,
                test_dir=TESTS,
                build_dir=sim.build_dir,
                results_xml=str(results_xml),
                waves=WAVES,
                plusargs=plusargs or [],
            )
        except SystemExit:
            # runner.test() 在 cocotb 测试失败时会 sys.exit(1)。
            # 直接把 SystemExit 交给 pytest 只会显示“SystemExit: 1”，
            # 所以这里从 results.xml 里取出真正的断言信息，再让 pytest 报错。
            failure = _format_cocotb_failure(results_xml)
            if failure:
                # from None：不要在 pytest 输出里再显示 “During handling of
                # the above exception...”，因为 SystemExit 只是 runner 的
                # 内部信号，真正的失败信息已经在 failure 里了。
                raise pytest.fail.Exception(failure, pytrace=False) from None
            raise

    return _run
