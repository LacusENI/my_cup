`include "rtl/core/defines.v"

module ctrl (
    input [5:0] op,
    input [5:0] funct,
    output [1:0] npc_op,
    output       reg_write,
    output [3:0] alu_op,
    output       mem_write,
    output       mem_read,
    output [1:0] cond_type,
    output       ext_type,
    output       rd_sel,
    output       wb_sel,
    output       src2_sel
);
    if_ctrl u_if_ctrl(.*);
    id_ctrl u_id_ctrl(.*);
    ex_ctrl u_ex_ctrl(.*);
    mem_ctrl u_mem_ctrl(.*);
    wb_ctrl u_wb_ctrl(.*);
endmodule