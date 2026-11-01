"""
ctrl（控制器）的单元测试。

ctrl 是纯组合逻辑：输入 opcode/funct3/funct7 和 valid_encoding，
输出打包好的 ctrl_t。测试通过 test-only probe 观察扁平化字段。

本批 7 条指令的控制表见 docs/v0.3-rv32i/units.md。
"""

from typing import Protocol

import cocotb

from utils.cocotb_utils import Signal, assert_fields, settle
from utils.riscv_asm import (
    BRANCH,
    F3_ADD,
    F3_BEQ,
    F3_JALR,
    F3_LW,
    F3_SW,
    JAL,
    JALR,
    LOAD,
    OP,
    OP_IMM,
    STORE,
)


# 控制枚举的数值是对外契约，与 cpu_pkg.sv 保持一致。
NPC_PLUS4 = 0
NPC_BRANCH = 1
NPC_JAL = 2
NPC_JALR = 3

ALU_NOP = 0
ALU_ADD = 1
ALU_EQ = 2

WB_ALU_OUT = 0
WB_R_DATA = 1
WB_PC_PLUS4 = 2

SRC2_RS2 = 0
SRC2_IMM = 1


class CtrlDut(Protocol):
    opcode: Signal
    funct3: Signal
    funct7: Signal
    valid_encoding: Signal
    npc_op: Signal
    reg_write: Signal
    alu_op: Signal
    mem_read: Signal
    mem_write: Signal
    wb_sel: Signal
    src2_sel: Signal
    inst_illegal: Signal


REQUIRED_FIELDS = (
    "opcode",
    "funct3",
    "funct7",
    "valid_encoding",
    "npc_op",
    "reg_write",
    "alu_op",
    "mem_read",
    "mem_write",
    "wb_sel",
    "src2_sel",
    "inst_illegal",
)


async def drive(
    dut: CtrlDut, *, opcode: int, funct3: int, funct7: int = 0, valid: int = 1
) -> None:
    dut.opcode.value = opcode
    dut.funct3.value = funct3
    dut.funct7.value = funct7
    dut.valid_encoding.value = valid
    await settle()


@cocotb.test()
async def contract_test(dut: CtrlDut):
    """契约：ctrl_probe 暴露所有控制字段。"""
    assert_fields(dut, REQUIRED_FIELDS, "ctrl_probe")


@cocotb.test()
async def add_control_test(dut: CtrlDut):
    """add：ALU 加法，写回 rd，PC+4。"""
    await drive(dut, opcode=OP, funct3=F3_ADD, funct7=0)

    assert int(dut.reg_write.value) == 1
    assert int(dut.alu_op.value) == ALU_ADD
    assert int(dut.src2_sel.value) == SRC2_RS2
    assert int(dut.wb_sel.value) == WB_ALU_OUT
    assert int(dut.npc_op.value) == NPC_PLUS4
    assert int(dut.mem_read.value) == 0
    assert int(dut.mem_write.value) == 0
    assert int(dut.inst_illegal.value) == 0


@cocotb.test()
async def addi_control_test(dut: CtrlDut):
    """addi：ALU 加法，第二操作数是立即数，写回 rd。"""
    await drive(dut, opcode=OP_IMM, funct3=F3_ADD)

    assert int(dut.reg_write.value) == 1
    assert int(dut.alu_op.value) == ALU_ADD
    assert int(dut.src2_sel.value) == SRC2_IMM
    assert int(dut.wb_sel.value) == WB_ALU_OUT
    assert int(dut.npc_op.value) == NPC_PLUS4
    assert int(dut.inst_illegal.value) == 0


@cocotb.test()
async def beq_control_test(dut: CtrlDut):
    """beq：ALU 相等比较，分支 NPC，不写寄存器/内存。"""
    await drive(dut, opcode=BRANCH, funct3=F3_BEQ)

    assert int(dut.npc_op.value) == NPC_BRANCH
    assert int(dut.alu_op.value) == ALU_EQ
    assert int(dut.src2_sel.value) == SRC2_RS2
    assert int(dut.reg_write.value) == 0
    assert int(dut.mem_read.value) == 0
    assert int(dut.mem_write.value) == 0
    assert int(dut.inst_illegal.value) == 0


@cocotb.test()
async def lw_control_test(dut: CtrlDut):
    """lw：地址 = rs1 + imm，读内存，写回 rd。"""
    await drive(dut, opcode=LOAD, funct3=F3_LW)

    assert int(dut.reg_write.value) == 1
    assert int(dut.alu_op.value) == ALU_ADD
    assert int(dut.src2_sel.value) == SRC2_IMM
    assert int(dut.mem_read.value) == 1
    assert int(dut.mem_write.value) == 0
    assert int(dut.wb_sel.value) == WB_R_DATA
    assert int(dut.npc_op.value) == NPC_PLUS4


@cocotb.test()
async def sw_control_test(dut: CtrlDut):
    """sw：地址 = rs1 + imm，写内存，不写寄存器。"""
    await drive(dut, opcode=STORE, funct3=F3_SW)

    assert int(dut.reg_write.value) == 0
    assert int(dut.alu_op.value) == ALU_ADD
    assert int(dut.src2_sel.value) == SRC2_IMM
    assert int(dut.mem_read.value) == 0
    assert int(dut.mem_write.value) == 1
    assert int(dut.npc_op.value) == NPC_PLUS4


@cocotb.test()
async def jal_control_test(dut: CtrlDut):
    """jal：PC+4 写回 rd，跳到 PC+offset。"""
    await drive(dut, opcode=JAL, funct3=0)

    assert int(dut.npc_op.value) == NPC_JAL
    assert int(dut.reg_write.value) == 1
    assert int(dut.alu_op.value) == ALU_NOP
    assert int(dut.wb_sel.value) == WB_PC_PLUS4
    assert int(dut.mem_read.value) == 0
    assert int(dut.mem_write.value) == 0


@cocotb.test()
async def jalr_control_test(dut: CtrlDut):
    """jalr：ALU 计算 rs1+imm，PC+4 写回 rd，跳到寄存器目标。"""
    await drive(dut, opcode=JALR, funct3=F3_JALR)

    assert int(dut.npc_op.value) == NPC_JALR
    assert int(dut.reg_write.value) == 1
    assert int(dut.alu_op.value) == ALU_ADD
    assert int(dut.src2_sel.value) == SRC2_IMM
    assert int(dut.wb_sel.value) == WB_PC_PLUS4
    assert int(dut.mem_read.value) == 0
    assert int(dut.mem_write.value) == 0


@cocotb.test()
async def illegal_control_test(dut: CtrlDut):
    """非法编码：inst_illegal=1，不写寄存器/内存，ALU/NPC 安全默认。"""
    await drive(dut, opcode=0, funct3=0, valid=0)

    assert int(dut.inst_illegal.value) == 1
    assert int(dut.reg_write.value) == 0
    assert int(dut.mem_read.value) == 0
    assert int(dut.mem_write.value) == 0
    assert int(dut.alu_op.value) == ALU_NOP
    assert int(dut.npc_op.value) == NPC_PLUS4
    assert int(dut.wb_sel.value) == WB_ALU_OUT
    assert int(dut.src2_sel.value) == SRC2_RS2
