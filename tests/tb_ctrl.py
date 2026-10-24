"""
ctrl（控制器）的单元测试。

ctrl 是“纯组合逻辑”：
  你给它 op/funct，它马上输出一个打包好的 ctrl_t 结构体。

由于 Icarus 的 VPI 不会把 packed struct 的字段暴露成子对象，
这里用一个 field() 小工具，从 dut.ctrl 的整数值里取出字段。

字段布局不再手写：rtl_consts.struct_layout() 会从 cpu_pkg.sv 里
解析 ctrl_t 的字段顺序和位宽，RTL 改了布局，测试会自动跟着变。
"""

from typing import Protocol

import cocotb

from cocotb_utils import Signal, assert_fields, settle
from rtl_consts import (
    ALU_OP_ADD,
    ALU_OP_SUB,
    COND_TYPE_EQ,
    EXT_TYPE_SIGN_EXT,
    FUNCT_ADDU,
    FUNCT_JR,
    NPC_OP_BRANCH,
    NPC_OP_DIRECT,
    NPC_OP_PLUS4,
    NPC_OP_RA,
    OP_ADDIU,
    OP_BEQ,
    OP_J,
    OP_JAL,
    OP_LW,
    OP_R,
    OP_SW,
    RD_SEL_RD,
    RD_SEL_REG_RA,
    RD_SEL_RT,
    SRC2_SEL_IMM,
    SRC2_SEL_RS2,
    WB_SEL_ALU_OUT,
    WB_SEL_PC_P4,
    WB_SEL_R_DATA,
    struct_layout,
)

# ctrl_t 的字段布局：(最高位, 位宽)
CTRL_LAYOUT = struct_layout("ctrl_t")


# ctrl 的公开字段：测试依赖哪些，就列哪些。
class CtrlDut(Protocol):
    op: Signal
    funct: Signal
    ctrl: Signal


REQUIRED_FIELDS = ("op", "funct", "ctrl")


def field(dut: CtrlDut, name: str) -> int:
    """从打包的 ctrl_t 里取出一个字段的整数值。"""
    msb, width = CTRL_LAYOUT[name]
    shift = msb - width + 1
    mask = (1 << width) - 1
    return (int(dut.ctrl.value) >> shift) & mask


# --------------------------------------------------------------------------- #
# 测试
# --------------------------------------------------------------------------- #
@cocotb.test()
async def contract_test(dut: CtrlDut):
    """契约：ctrl 仍然暴露 op / funct / ctrl。"""
    assert_fields(dut, REQUIRED_FIELDS, "ctrl")


@cocotb.test()
async def addu_control_test(dut: CtrlDut):
    """addu $rd, $rs, $rt：两个寄存器相加，结果写回 rd。"""
    dut.op.value = OP_R
    dut.funct.value = FUNCT_ADDU
    await settle()

    assert field(dut, "reg_write") == 1, "addu 应该写寄存器"
    assert field(dut, "rd_sel") == RD_SEL_RD, "addu 的目标寄存器是 rd"
    assert field(dut, "wb_sel") == WB_SEL_ALU_OUT, "addu 写回 ALU 结果"
    assert field(dut, "src2_sel") == SRC2_SEL_RS2, "addu 的第二个操作数来自 rs2"
    assert field(dut, "alu_op") == ALU_OP_ADD, "addu 做加法"
    assert field(dut, "npc_op") == NPC_OP_PLUS4, "addu 不跳转，PC+4"
    assert field(dut, "mem_read") == 0, "addu 不读内存"
    assert field(dut, "mem_write") == 0, "addu 不写内存"


@cocotb.test()
async def addiu_control_test(dut: CtrlDut):
    """addiu $rt, $rs, imm：rs 加立即数，结果写回 rt。"""
    dut.op.value = OP_ADDIU
    dut.funct.value = 0
    await settle()

    assert field(dut, "reg_write") == 1, "addiu 应该写寄存器"
    assert field(dut, "rd_sel") == RD_SEL_RT, "addiu 的目标寄存器是 rt"
    assert field(dut, "wb_sel") == WB_SEL_ALU_OUT, "addiu 写回 ALU 结果"
    assert field(dut, "src2_sel") == SRC2_SEL_IMM, "addiu 的第二个操作数是立即数"
    assert field(dut, "ext_type") == EXT_TYPE_SIGN_EXT, "立即数需要符号扩展"
    assert field(dut, "alu_op") == ALU_OP_ADD, "addiu 做加法"
    assert field(dut, "npc_op") == NPC_OP_PLUS4, "addiu 不跳转，PC+4"
    assert field(dut, "mem_read") == 0
    assert field(dut, "mem_write") == 0


@cocotb.test()
async def beq_control_test(dut: CtrlDut):
    """beq $rs, $rt, offset：相等则跳转。"""
    dut.op.value = OP_BEQ
    dut.funct.value = 0
    await settle()

    assert field(dut, "npc_op") == NPC_OP_BRANCH, "beq 是条件分支"
    assert field(dut, "alu_op") == ALU_OP_SUB, "beq 用减法判断是否相等"
    assert field(dut, "cond_type") == COND_TYPE_EQ, "beq 的条件是相等"
    assert field(dut, "src2_sel") == SRC2_SEL_RS2, "beq 比较两个寄存器"
    assert field(dut, "reg_write") == 0, "beq 不写寄存器"
    assert field(dut, "mem_read") == 0
    assert field(dut, "mem_write") == 0


@cocotb.test()
async def lw_control_test(dut: CtrlDut):
    """lw $rt, offset($rs)：从内存读一个字，写回 rt。"""
    dut.op.value = OP_LW
    dut.funct.value = 0
    await settle()

    assert field(dut, "reg_write") == 1, "lw 应该写寄存器"
    assert field(dut, "rd_sel") == RD_SEL_RT, "lw 的目标寄存器是 rt"
    assert field(dut, "wb_sel") == WB_SEL_R_DATA, "lw 写回内存读出的数据"
    assert field(dut, "src2_sel") == SRC2_SEL_IMM, "lw 的地址 = rs + 立即数"
    assert field(dut, "ext_type") == EXT_TYPE_SIGN_EXT, "偏移量需要符号扩展"
    assert field(dut, "mem_read") == 1, "lw 要读内存"
    assert field(dut, "mem_write") == 0
    assert field(dut, "npc_op") == NPC_OP_PLUS4


@cocotb.test()
async def sw_control_test(dut: CtrlDut):
    """sw $rt, offset($rs)：把 rt 写进内存。"""
    dut.op.value = OP_SW
    dut.funct.value = 0
    await settle()

    assert field(dut, "reg_write") == 0, "sw 不写寄存器"
    assert field(dut, "src2_sel") == SRC2_SEL_IMM, "sw 的地址 = rs + 立即数"
    assert field(dut, "ext_type") == EXT_TYPE_SIGN_EXT, "偏移量需要符号扩展"
    assert field(dut, "mem_read") == 0
    assert field(dut, "mem_write") == 1, "sw 要写内存"
    assert field(dut, "npc_op") == NPC_OP_PLUS4


@cocotb.test()
async def j_control_test(dut: CtrlDut):
    """j target：无条件直接跳转。"""
    dut.op.value = OP_J
    dut.funct.value = 0
    await settle()

    assert field(dut, "npc_op") == NPC_OP_DIRECT, "j 是直接跳转"
    assert field(dut, "reg_write") == 0, "j 不写寄存器"
    assert field(dut, "mem_read") == 0
    assert field(dut, "mem_write") == 0


@cocotb.test()
async def jal_control_test(dut: CtrlDut):
    """jal target：跳转，同时把返回地址写进 $ra。"""
    dut.op.value = OP_JAL
    dut.funct.value = 0
    await settle()

    assert field(dut, "npc_op") == NPC_OP_DIRECT, "jal 是直接跳转"
    assert field(dut, "reg_write") == 1, "jal 要写 $ra"
    assert field(dut, "rd_sel") == RD_SEL_REG_RA, "jal 的目标寄存器是 $ra"
    assert field(dut, "wb_sel") == WB_SEL_PC_P4, "jal 写回 PC+4"
    assert field(dut, "mem_read") == 0
    assert field(dut, "mem_write") == 0


@cocotb.test()
async def jr_control_test(dut: CtrlDut):
    """jr $rs：跳到寄存器里的地址。"""
    dut.op.value = OP_R
    dut.funct.value = FUNCT_JR
    await settle()

    assert field(dut, "npc_op") == NPC_OP_RA, "jr 跳到寄存器地址"
    assert field(dut, "reg_write") == 0, "jr 不写寄存器"
    assert field(dut, "mem_read") == 0
    assert field(dut, "mem_write") == 0
