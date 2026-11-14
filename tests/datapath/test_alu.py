"""ALU 单元测试。

这个文件是新写法的试点：**cocotb 用例和 pytest 入口放在同一个文件里**，
不再需要单独的 ``tb_alu.py``。

原来的写法是：
    tb_alu.py   : 放 @cocotb.test() 的 async 函数，由仿真器里的 cocotb 执行
    test_alu.py : 放一个 pytest 函数，调用 run_cocotb_case() 启动仿真

现在的写法是：
    @cocotb_test(dut="alu_sim")
    async def test_add(dut): ...

``@cocotb_test`` 会同时做两件事：
  1. 把这个 async 函数注册成 cocotb test；
  2. 返回一个普通同步函数给 pytest 收集，由它负责启动仿真。

更底层的解释见 ``tests/utils/cocotb_utils.py`` 里 ``cocotb_test`` 的注释。
"""

from typing import Protocol

from utils.cocotb_utils import Signal, assert_fields, cocotb_test, settle
from utils.cpu_pkg import ALU_ADD, ALU_EQ, ALU_NOP


# conftest.py 里 session 级 fixture 的名字。
# 它负责编译 alu（整个测试会话只编译一次），并复用 build/cocotb/alu/。
SIM = "alu_sim"


class AluDut(Protocol):
    alu_op: Signal
    alu_src1: Signal
    alu_src2: Signal
    alu_out: Signal
    cmp_result: Signal


REQUIRED_FIELDS = (
    "alu_op",
    "alu_src1",
    "alu_src2",
    "alu_out",
    "cmp_result",
)


@cocotb_test(dut=SIM)
async def test_contract(dut: AluDut):
    """契约：ALU 暴露输入、结果和比较位。"""
    assert_fields(dut, REQUIRED_FIELDS, "alu")


@cocotb_test(dut=SIM)
async def test_alu_add(dut: AluDut):
    """ADD：5 + 3 = 8，cmp_result 必须为 0。"""
    dut.alu_op.value = ALU_ADD
    dut.alu_src1.value = 5
    dut.alu_src2.value = 3
    await settle()

    assert int(dut.alu_out.value) == 8
    assert int(dut.cmp_result.value) == 0


@cocotb_test(dut=SIM)
async def test_alu_add_wrap(dut: AluDut):
    """ADD 是 32 位回绕，不产生溢出异常。"""
    dut.alu_op.value = ALU_ADD
    dut.alu_src1.value = 0xFFFF_FFFF
    dut.alu_src2.value = 1
    await settle()

    assert int(dut.alu_out.value) == 0
    assert int(dut.cmp_result.value) == 0


@cocotb_test(dut=SIM)
async def test_alu_eq_true(dut: AluDut):
    """EQ：相等时 cmp_result=1，alu_out=0。"""
    dut.alu_op.value = ALU_EQ
    dut.alu_src1.value = 244
    dut.alu_src2.value = 244
    await settle()

    assert int(dut.alu_out.value) == 0
    assert int(dut.cmp_result.value) == 1


@cocotb_test(dut=SIM)
async def test_alu_eq_false(dut: AluDut):
    """EQ：不相等时 cmp_result=0。"""
    dut.alu_op.value = ALU_EQ
    dut.alu_src1.value = 244
    dut.alu_src2.value = 245
    await settle()

    assert int(dut.alu_out.value) == 0
    assert int(dut.cmp_result.value) == 0


@cocotb_test(dut=SIM)
async def test_alu_nop(dut: AluDut):
    """NOP：输出和比较位都为 0。"""
    dut.alu_op.value = ALU_NOP
    dut.alu_src1.value = 0x1234_5678
    dut.alu_src2.value = 0x1234_5678
    await settle()

    assert int(dut.alu_out.value) == 0
    assert int(dut.cmp_result.value) == 0
