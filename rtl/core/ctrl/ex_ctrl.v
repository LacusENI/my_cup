`include "rtl/core/defines.v"

module ex_ctrl (
    input [5:0] op,
    input [5:0] funct,
    output       src2_sel,
    output [3:0] alu_op,
    output [1:0] cond_type
);
    wire addu, addiu, beq, lw, sw, j;
    assign addu = (op == `OP_R_INSTR) && (funct == `FUNCT_ADDU);
    assign addiu = (op == `OP_ADDIU);
    assign beq = (op == `OP_BEQ);
    assign lw = (op == `OP_LW);
    assign sw = (op == `OP_SW);
    assign j = (op == `OP_J);

    assign src2_sel = addu ? `SRC2_SEL_RS2 :
                      beq ? `SRC2_SEL_RS2 :
                      addiu ? `SRC2_SEL_IMM :
                      lw ? `SRC2_SEL_IMM :
                      sw ? `SRC2_SEL_IMM :
                      1'bx;
    assign alu_op = beq ? `ALU_OP_SUB :
                    `ALU_OP_ADD;
    assign cond_type = beq ? `COND_TYPE_EQ :
                       1'bx;
endmodule