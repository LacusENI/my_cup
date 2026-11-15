`default_nettype none

// ***************************************************************
// test-only probe：把 ctrl_t 摊平成 cocotb 可以直接访问的端口
//
// 这个模块只用于仿真，不参与综合，也不在 rtl/ 下。
// 它不做任何逻辑，只是把 ctrl 输出的 struct 字段逐一接出来，
// 这样测试就不用手写字段位偏移。
// ***************************************************************
module ctrl_probe
    import cpu_pkg::*;
(
    input  opcode_t opcode,
    input  funct3_t funct3,
    input  funct7_t funct7,
    input  reg_t    rd,
    input  reg_t    rs1,
    input  funct12_t funct12,
    input  logic    opcode_err,

    output npc_op_t    npc_op,
    output logic       reg_write,
    output alu_op_t    alu_op,
    output logic       mem_read,
    output logic       mem_write,
    output wb_sel_t     wb_sel,
    output src2_sel_t   src2_sel,
    output logic        halt,
    output halt_cause_t halt_cause
);

    ctrl_t c;

    ctrl u_ctrl (
        .opcode(opcode),
        .funct3(funct3),
        .funct7(funct7),
        .rd(rd),
        .rs1(rs1),
        .funct12(funct12),
        .opcode_err(opcode_err),
        .ctrl(c)
    );

    // 一对一摊平，不在这里加任何逻辑。
    assign npc_op       = c.npc_op;
    assign reg_write    = c.reg_write;
    assign alu_op       = c.alu_op;
    assign mem_read     = c.mem_read;
    assign mem_write    = c.mem_write;
    assign wb_sel       = c.wb_sel;
    assign src2_sel     = c.src2_sel;
    assign halt         = c.halt;
    assign halt_cause   = c.halt_cause;

endmodule

`default_nettype wire
