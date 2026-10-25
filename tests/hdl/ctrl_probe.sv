`default_nettype none

// ***************************************************************
// test-only probe：把 ctrl_t 摊平成 cocotb 可以直接访问的端口
//
// 这个模块只用于仿真，不参与综合，也不在 rtl/ 下。
// 它不做任何逻辑，只是把 ctrl 输出的 struct 字段逐一接出来，
// 这样测试就不用手写字段位偏移了。
// ***************************************************************
module ctrl_probe
    import cpu_pkg::*;
(
    input  logic [5:0] op,
    input  logic [5:0] funct,

    output npc_op_t    npc_op,
    output logic       reg_write,
    output alu_op_t    alu_op,
    output logic       mem_write,
    output logic       mem_read,
    output cond_type_t cond_type,
    output ext_type_t  ext_type,
    output rd_sel_t    rd_sel,
    output wb_sel_t    wb_sel,
    output src2_sel_t  src2_sel
);

    ctrl_t c;

    ctrl u_ctrl (
        .op(op),
        .funct(funct),
        .ctrl(c)
    );

    // 一对一摊平，不在这里加任何逻辑。
    assign npc_op    = c.npc_op;
    assign reg_write = c.reg_write;
    assign alu_op    = c.alu_op;
    assign mem_write = c.mem_write;
    assign mem_read  = c.mem_read;
    assign cond_type = c.cond_type;
    assign ext_type  = c.ext_type;
    assign rd_sel    = c.rd_sel;
    assign wb_sel    = c.wb_sel;
    assign src2_sel  = c.src2_sel;

endmodule

`default_nettype wire
