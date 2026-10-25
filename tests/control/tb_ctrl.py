"""
ctrl（控制器）的单元测试。

ctrl 是“纯组合逻辑”：
  你给它 op/funct，它马上输出一个打包好的 ctrl_t 结构体。

Icarus 的 VPI 不会把 packed struct 的字段暴露成子对象。
为了不手写字段位偏移，测试使用 `tests/hdl/ctrl_probe.sv`：
它把 ctrl_t 的每个字段摊平成普通端口，测试直接读 `dut.<field>.value`。
"""

from typing import Protocol

import cocotb

from utils.cocotb_utils import Signal, assert_fields, settle

# --------------------------------------------------------------------------- #
# 常量（来自 cpu_pkg.sv，是对外契约）
#
# 已发布的数值不要修改；需要扩展时只新增，保持向后兼容。
# --------------------------------------------------------------------------- #
OP_R       = 0b000000
OP_ADDIU   = 0b001001
OP_BEQ     = 0b000100
OP_LW      = 0b100011
OP_SW      = 0b101011
OP_J       = 0b000010
OP_JAL     = 0b000011

FUNCT_ADDU = 0b100001
FUNCT_JR   = 0b001000

NPC_OP_PLUS4  = 0b00
NPC_OP_BRANCH = 0b01
NPC_OP_DIRECT = 0b10
NPC_OP_RA     = 0b11

RD_SEL_RT     = 0b00
RD_SEL_RD     = 0b01
RD_SEL_REG_RA = 0b10

WB_SEL_ALU_OUT = 0b00
WB_SEL_R_DATA  = 0b01
WB_SEL_PC_P4   = 0b10

SRC2_SEL_RS2 = 0
SRC2_SEL_IMM = 1

EXT_TYPE_SIGN_EXT = 1

ALU_OP_ADD = 0b0001
ALU_OP_SUB = 0b0010

COND_TYPE_EQ = 0b00


# ctrl 的公开字段：由 tests/hdl/ctrl_probe.sv 摊平后暴露给 cocotb。
# 这里不需要知道 struct 的位偏移，只需要字段名。
class CtrlDut(Protocol):
    op: Signal
    funct: Signal
    npc_op: Signal
    reg_write: Signal
    alu_op: Signal
    mem_write: Signal
    mem_read: Signal
    cond_type: Signal
    ext_type: Signal
    rd_sel: Signal
    wb_sel: Signal
    src2_sel: Signal


REQUIRED_FIELDS = (
    "op",
    "funct",
    "npc_op",
    "reg_write",
    "alu_op",
    "mem_write",
    "mem_read",
    "cond_type",
    "ext_type",
    "rd_sel",
    "wb_sel",
    "src2_sel",
)


# --------------------------------------------------------------------------- #
# 测试
# --------------------------------------------------------------------------- #
@cocotb.test()
async def contract_test(dut: CtrlDut):
    """契约：ctrl_probe 仍然暴露 op / funct 和扁平化后的控制字段。"""
    assert_fields(dut, REQUIRED_FIELDS, "ctrl_probe")


@cocotb.test()
async def addu_control_test(dut: CtrlDut):
    """addu $rd, $rs, $rt：两个寄存器相加，结果写回 rd。"""
    dut.op.value = OP_R
    dut.funct.value = FUNCT_ADDU
    await settle()

    assert int(dut.reg_write.value) == 1, "addu 应该写寄存器"
    assert int(dut.rd_sel.value) == RD_SEL_RD, "addu 的目标寄存器是 rd"
    assert int(dut.wb_sel.value) == WB_SEL_ALU_OUT, "addu 写回 ALU 结果"
    assert int(dut.src2_sel.value) == SRC2_SEL_RS2, "addu 的第二个操作数来自 rs2"
    assert int(dut.alu_op.value) == ALU_OP_ADD, "addu 做加法"
    assert int(dut.npc_op.value) == NPC_OP_PLUS4, "addu 不跳转，PC+4"
    assert int(dut.mem_read.value) == 0, "addu 不读内存"
    assert int(dut.mem_write.value) == 0, "addu 不写内存"


@cocotb.test()
async def addiu_control_test(dut: CtrlDut):
    """addiu $rt, $rs, imm：rs 加立即数，结果写回 rt。"""
    dut.op.value = OP_ADDIU
    dut.funct.value = 0
    await settle()

    assert int(dut.reg_write.value) == 1, "addiu 应该写寄存器"
    assert int(dut.rd_sel.value) == RD_SEL_RT, "addiu 的目标寄存器是 rt"
    assert int(dut.wb_sel.value) == WB_SEL_ALU_OUT, "addiu 写回 ALU 结果"
    assert int(dut.src2_sel.value) == SRC2_SEL_IMM, "addiu 的第二个操作数是立即数"
    assert int(dut.ext_type.value) == EXT_TYPE_SIGN_EXT, "立即数需要符号扩展"
    assert int(dut.alu_op.value) == ALU_OP_ADD, "addiu 做加法"
    assert int(dut.npc_op.value) == NPC_OP_PLUS4, "addiu 不跳转，PC+4"
    assert int(dut.mem_read.value) == 0
    assert int(dut.mem_write.value) == 0


@cocotb.test()
async def beq_control_test(dut: CtrlDut):
    """beq $rs, $rt, offset：相等则跳转。"""
    dut.op.value = OP_BEQ
    dut.funct.value = 0
    await settle()

    assert int(dut.npc_op.value) == NPC_OP_BRANCH, "beq 是条件分支"
    assert int(dut.alu_op.value) == ALU_OP_SUB, "beq 用减法判断是否相等"
    assert int(dut.cond_type.value) == COND_TYPE_EQ, "beq 的条件是相等"
    assert int(dut.src2_sel.value) == SRC2_SEL_RS2, "beq 比较两个寄存器"
    assert int(dut.reg_write.value) == 0, "beq 不写寄存器"
    assert int(dut.mem_read.value) == 0
    assert int(dut.mem_write.value) == 0


@cocotb.test()
async def lw_control_test(dut: CtrlDut):
    """lw $rt, offset($rs)：从内存读一个字，写回 rt。"""
    dut.op.value = OP_LW
    dut.funct.value = 0
    await settle()

    assert int(dut.reg_write.value) == 1, "lw 应该写寄存器"
    assert int(dut.rd_sel.value) == RD_SEL_RT, "lw 的目标寄存器是 rt"
    assert int(dut.wb_sel.value) == WB_SEL_R_DATA, "lw 写回内存读出的数据"
    assert int(dut.src2_sel.value) == SRC2_SEL_IMM, "lw 的地址 = rs + 立即数"
    assert int(dut.ext_type.value) == EXT_TYPE_SIGN_EXT, "偏移量需要符号扩展"
    assert int(dut.mem_read.value) == 1, "lw 要读内存"
    assert int(dut.mem_write.value) == 0
    assert int(dut.npc_op.value) == NPC_OP_PLUS4


@cocotb.test()
async def sw_control_test(dut: CtrlDut):
    """sw $rt, offset($rs)：把 rt 写进内存。"""
    dut.op.value = OP_SW
    dut.funct.value = 0
    await settle()

    assert int(dut.reg_write.value) == 0, "sw 不写寄存器"
    assert int(dut.src2_sel.value) == SRC2_SEL_IMM, "sw 的地址 = rs + 立即数"
    assert int(dut.ext_type.value) == EXT_TYPE_SIGN_EXT, "偏移量需要符号扩展"
    assert int(dut.mem_read.value) == 0
    assert int(dut.mem_write.value) == 1, "sw 要写内存"
    assert int(dut.npc_op.value) == NPC_OP_PLUS4


@cocotb.test()
async def j_control_test(dut: CtrlDut):
    """j target：无条件直接跳转。"""
    dut.op.value = OP_J
    dut.funct.value = 0
    await settle()

    assert int(dut.npc_op.value) == NPC_OP_DIRECT, "j 是直接跳转"
    assert int(dut.reg_write.value) == 0, "j 不写寄存器"
    assert int(dut.mem_read.value) == 0
    assert int(dut.mem_write.value) == 0


@cocotb.test()
async def jal_control_test(dut: CtrlDut):
    """jal target：跳转，同时把返回地址写进 $ra。"""
    dut.op.value = OP_JAL
    dut.funct.value = 0
    await settle()

    assert int(dut.npc_op.value) == NPC_OP_DIRECT, "jal 是直接跳转"
    assert int(dut.reg_write.value) == 1, "jal 要写 $ra"
    assert int(dut.rd_sel.value) == RD_SEL_REG_RA, "jal 的目标寄存器是 $ra"
    assert int(dut.wb_sel.value) == WB_SEL_PC_P4, "jal 写回 PC+4"
    assert int(dut.mem_read.value) == 0
    assert int(dut.mem_write.value) == 0


@cocotb.test()
async def jr_control_test(dut: CtrlDut):
    """jr $rs：跳到寄存器里的地址。"""
    dut.op.value = OP_R
    dut.funct.value = FUNCT_JR
    await settle()

    assert int(dut.npc_op.value) == NPC_OP_RA, "jr 跳到寄存器地址"
    assert int(dut.reg_write.value) == 0, "jr 不写寄存器"
    assert int(dut.mem_read.value) == 0
    assert int(dut.mem_write.value) == 0
