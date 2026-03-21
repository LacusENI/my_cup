`include "rtl/core/defines.v"

module ctrl (
    input [5:0] op,
    input [5:0] funct,
    output reg npc_op,
    output reg reg_write,
    output reg alu_op,
    output reg mem_write,
    output reg mem_read,
    output reg cond_type,
    output reg ext_type,
    output reg rd_sel,
    output reg wb_sel,
    output reg src2_sel
);
    localparam OP_R_INSTR = 6'b00_0000;
    localparam OP_ADDIU   = 6'b00_1001;
    localparam OP_BEQ     = 6'b00_0100;
    localparam OP_LW      = 6'b10_0011;
    localparam OP_SW      = 6'b10_1011;
    localparam OP_J       = 6'b00_0010;

    localparam FUNCT_ADDU  = 6'b10_0001;
endmodule