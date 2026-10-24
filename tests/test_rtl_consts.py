"""rtl_consts 自检：确认解析器真的从 cpu_pkg.sv 读到了常量和布局。"""

from rtl_consts import CONSTS, struct_layout, struct_width


def test_constants_and_layout():
    # 常量：只检查“解析成功且彼此有区分”，不把具体值再抄一遍
    assert CONSTS["ALU_OP_ADD"] != CONSTS["ALU_OP_SUB"]
    assert CONSTS["OP_ADDIU"] != CONSTS["OP_R"]

    # ctrl_t 的布局：这是 tb_ctrl 取字段时依赖的“金标准”
    assert struct_width("ctrl_t") == 17
    layout = struct_layout("ctrl_t")
    assert layout["npc_op"] == (16, 2)
    assert layout["alu_op"] == (13, 4)
    assert layout["src2_sel"] == (0, 1)
