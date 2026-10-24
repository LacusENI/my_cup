"""
ctrl（控制器）的单元测试。

ctrl 是“纯组合逻辑”：
  你给它 op/funct，它马上输出一个打包好的 ctrl_t 结构体。

由于 Icarus 的 VPI 不会把 packed struct 的字段暴露成子对象，
这里用一个 field() 小工具，从 dut.ctrl 的整数值里取出字段。

ctrl_t 的字段布局（与 cpu_pkg.sv 保持一致，packed struct 从 MSB 开始）：
  npc_op[16:15]
  reg_write[14]
  alu_op[13:10]
  mem_write[9]
  mem_read[8]
  cond_type[7:6]
  ext_type[5]
  rd_sel[4:3]
  wb_sel[2:1]
  src2_sel[0]
"""

import cocotb

from cocotb_utils import settle

# 每个字段：(最高位, 位宽)
CTRL_FIELDS = {
    "npc_op":    (16, 2),
    "reg_write": (14, 1),
    "alu_op":    (13, 4),
    "mem_write": (9, 1),
    "mem_read":  (8, 1),
    "cond_type": (7, 2),
    "ext_type":  (5, 1),
    "rd_sel":    (4, 2),
    "wb_sel":    (2, 2),
    "src2_sel":  (0, 1),
}


def field(dut, name: str) -> int:
    """从打包的 ctrl_t 里取出一个字段的整数值。"""
    msb, width = CTRL_FIELDS[name]
    shift = msb - width + 1
    mask = (1 << width) - 1
    return (int(dut.ctrl.value) >> shift) & mask


# --------------------------------------------------------------------------- #
# 指令编码（与 cpu_pkg.sv 保持一致）
# --------------------------------------------------------------------------- #
OP_R_INSTR = 0b000000
OP_ADDIU   = 0b001001
OP_BEQ     = 0b000100
OP_LW      = 0b100011
OP_SW      = 0b101011
OP_J       = 0b000010
OP_JAL     = 0b000011

FUNCT_ADDU = 0b100001
FUNCT_JR   = 0b001000

# --------------------------------------------------------------------------- #
# 控制信号取值（同样来自 cpu_pkg.sv）
# --------------------------------------------------------------------------- #
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


# --------------------------------------------------------------------------- #
# 测试
# --------------------------------------------------------------------------- #
@cocotb.test()
async def addu_control_test(dut):
    """addu $rd, $rs, $rt：两个寄存器相加，结果写回 rd。"""
    dut.op.value = OP_R_INSTR
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
async def addiu_control_test(dut):
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
async def beq_control_test(dut):
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
async def lw_control_test(dut):
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
async def sw_control_test(dut):
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
async def j_control_test(dut):
    """j target：无条件直接跳转。"""
    dut.op.value = OP_J
    dut.funct.value = 0
    await settle()

    assert field(dut, "npc_op") == NPC_OP_DIRECT, "j 是直接跳转"
    assert field(dut, "reg_write") == 0, "j 不写寄存器"
    assert field(dut, "mem_read") == 0
    assert field(dut, "mem_write") == 0


@cocotb.test()
async def jal_control_test(dut):
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
async def jr_control_test(dut):
    """jr $rs：跳到寄存器里的地址。"""
    dut.op.value = OP_R_INSTR
    dut.funct.value = FUNCT_JR
    await settle()

    assert field(dut, "npc_op") == NPC_OP_RA, "jr 跳到寄存器地址"
    assert field(dut, "reg_write") == 0, "jr 不写寄存器"
    assert field(dut, "mem_read") == 0
    assert field(dut, "mem_write") == 0
