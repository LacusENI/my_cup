"""decoder（指令译码 + 立即数生成）的单元测试。

cocotb 用例和 pytest 入口在同一个文件里，由 ``@cocotb_test`` 连接。
pytest 收集的是装饰器生成的同步 wrapper；仿真器里的 cocotb 执行原来的
async 函数。详细机制见 ``tests/utils/cocotb_utils.py`` 的 ``cocotb_test``。

decoder 是纯组合逻辑。测试通过 test-only probe 观察：
  - RV32I 字段：opcode / rd / rs1 / rs2 / funct3 / funct7
  - imm：I/S/B/J 四种立即数
  - valid_encoding：是否属于当前实现子集

立即数生成虽然写在 decoder 内部，但这里单独覆盖每种格式，
避免只靠指令级测试才能发现 B/J 型拼位错误。
"""

from typing import Protocol

from utils.assembler import assemble
from utils.cocotb_utils import Signal, assert_fields, cocotb_test, settle


# conftest.py 里的 session fixture 名：负责编译 decoder_probe 并复用 build 目录。
SIM = "decoder_sim"


class DecoderDut(Protocol):
    inst: Signal
    opcode: Signal
    rd: Signal
    funct3: Signal
    rs1: Signal
    rs2: Signal
    funct7: Signal
    imm: Signal
    valid_encoding: Signal


REQUIRED_FIELDS = (
    "inst",
    "opcode",
    "rd",
    "funct3",
    "rs1",
    "rs2",
    "funct7",
    "imm",
    "valid_encoding",
)


@cocotb_test(dut=SIM)
async def test_contract(dut: DecoderDut):
    """契约：decoder_probe 暴露字段、立即数和合法编码。"""
    assert_fields(dut, REQUIRED_FIELDS, "decoder_probe")


@cocotb_test(dut=SIM)
async def test_fields(dut: DecoderDut):
    """R 型字段切分：add x3, x1, x2。"""
    word = assemble("add x3, x1, x2")
    dut.inst.value = word
    await settle()

    assert int(dut.opcode.value) == (word & 0x7F)
    assert int(dut.rd.value) == 3
    assert int(dut.rs1.value) == 1
    assert int(dut.rs2.value) == 2
    assert int(dut.funct3.value) == 0
    assert int(dut.funct7.value) == 0
    assert int(dut.imm.value) == 0
    assert int(dut.valid_encoding.value) == 1


@cocotb_test(dut=SIM)
async def test_imm_i(dut: DecoderDut):
    """I 型立即数：正数、负数和边界。"""
    cases = [
        (assemble("addi x1, x0, 8"), 8),
        (assemble("addi x1, x0, -1"), 0xFFFF_FFFF),
        (assemble("lw x2, -4(x1)"), 0xFFFF_FFFC),
        (assemble("jalr x1, -4(x2)"), 0xFFFF_FFFC),
    ]
    for instruction, expected in cases:
        dut.inst.value = instruction
        await settle()
        assert int(dut.imm.value) == expected, f"I 型立即数错误: {instruction:#010x}"


@cocotb_test(dut=SIM)
async def test_imm_s(dut: DecoderDut):
    """S 型立即数：imm[11:5] 与 imm[4:0] 的拼接和符号扩展。"""
    cases = [
        (assemble("sw x3, 0(x1)"), 0),
        (assemble("sw x3, 2047(x1)"), 2047),
        (assemble("sw x3, -4(x1)"), 0xFFFF_FFFC),
        (assemble("sw x3, -2048(x1)"), 0xFFFF_F800),
    ]
    for instruction, expected in cases:
        dut.inst.value = instruction
        await settle()
        assert int(dut.imm.value) == expected, f"S 型立即数错误: {instruction:#010x}"


@cocotb_test(dut=SIM)
async def test_imm_b(dut: DecoderDut):
    """B 型立即数：乱序位拼接、符号扩展、bit0 为 0。"""
    cases = [
        (assemble("beq x1, x2, 0"), 0),
        (assemble("beq x1, x2, 8"), 8),
        (assemble("beq x1, x2, -8"), 0xFFFF_FFF8),
        (assemble("beq x1, x2, 4094"), 4094),
        (assemble("beq x1, x2, -4096"), 0xFFFF_F000),
    ]
    for instruction, expected in cases:
        dut.inst.value = instruction
        await settle()
        assert int(dut.imm.value) == expected, f"B 型立即数错误: {instruction:#010x}"


@cocotb_test(dut=SIM)
async def test_imm_j(dut: DecoderDut):
    """J 型立即数：乱序位拼接、符号扩展、bit0 为 0。"""
    cases = [
        (assemble("jal x1, 0"), 0),
        (assemble("jal x1, 8"), 8),
        (assemble("jal x1, -8"), 0xFFFF_FFF8),
        (assemble("jal x1, 1048574"), 1048574),
        (assemble("jal x1, -1048576"), 0xFFF0_0000),
    ]
    for instruction, expected in cases:
        dut.inst.value = instruction
        await settle()
        assert int(dut.imm.value) == expected, f"J 型立即数错误: {instruction:#010x}"


def _with_field(word: int, msb: int, lsb: int, value: int) -> int:
    """只修改测试激励中的字段，不参与正式编码。"""
    width = msb - lsb + 1
    mask = (1 << width) - 1
    return (word & ~(mask << lsb)) | ((value & mask) << lsb)


@cocotb_test(dut=SIM)
async def test_invalid_r_type(dut: DecoderDut):
    """未实现的 R 型 funct7/funct3 不应被接受。"""
    # sub 的 funct7=0x20；当前只实现 add。
    dut.inst.value = _with_field(assemble("add x1, x1, x2"), 31, 25, 0x20)
    await settle()
    assert int(dut.valid_encoding.value) == 0


@cocotb_test(dut=SIM)
async def test_invalid_opcode(dut: DecoderDut):
    """未知 opcode 应该输出 illegal，imm 保持 0。"""
    dut.inst.value = 0xFFFF_FFFF
    await settle()
    assert int(dut.valid_encoding.value) == 0
    assert int(dut.imm.value) == 0


@cocotb_test(dut=SIM)
async def test_invalid_funct3(dut: DecoderDut):
    """addi 只接受 funct3=000。"""
    dut.inst.value = _with_field(assemble("addi x1, x0, 8"), 14, 12, 1)
    await settle()
    assert int(dut.valid_encoding.value) == 0


@cocotb_test(dut=SIM)
async def test_invalid_funct3_matrix(dut: DecoderDut):
    """LOAD/STORE/BRANCH/JALR 的非法 funct3 都必须拒绝。"""
    cases = [
        _with_field(assemble("lw x1, 0(x0)"), 14, 12, 1),  # lh
        _with_field(assemble("sw x1, 0(x0)"), 14, 12, 1),  # sh
        _with_field(assemble("beq x0, x1, 0"), 14, 12, 1),  # bne
        _with_field(assemble("jalr x1, 0(x0)"), 14, 12, 1),  # 非法 jalr
        _with_field(assemble("add x1, x0, x1"), 14, 12, 1),
    ]
    for instruction in cases:
        dut.inst.value = instruction
        await settle()
        assert int(dut.valid_encoding.value) == 0, f"不应接受 {instruction:#010x}"
