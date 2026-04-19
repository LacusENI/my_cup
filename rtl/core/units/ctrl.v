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
    output [1:0] rd_sel,
    output       wb_sel,
    output       src2_sel
);
    wire addu, addiu, beq, lw, sw, j;
    assign addu = (op == `OP_R_INSTR) && (funct == `FUNCT_ADDU);
    assign addiu = (op == `OP_ADDIU);
    assign beq = (op == `OP_BEQ);
    assign lw = (op == `OP_LW);
    assign sw = (op == `OP_SW);
    assign j = (op == `OP_J);

    // IF
    assign npc_op = beq ? `NPC_OP_BRANCH :
                    j ? `NPC_OP_DIRECT :
                    `NPC_OP_PLUS4;

    // ID
    assign rd_sel = lw ? `RD_SEL_RT :
                    addiu ? `RD_SEL_RT :
                    addu ? `RD_SEL_RD : 
                    2'bx;
    assign ext_type = addiu ? `EXT_TYPE_SIGN_EXT :
                      lw ? `EXT_TYPE_SIGN_EXT :
                      sw ? `EXT_TYPE_SIGN_EXT :
                      1'bx;
    assign reg_write = (addu | addiu | lw);

    // EX
    assign src2_sel = addu ? `SRC2_SEL_RS2 :
                      beq ? `SRC2_SEL_RS2 :
                      addiu ? `SRC2_SEL_IMM :
                      lw ? `SRC2_SEL_IMM :
                      sw ? `SRC2_SEL_IMM :
                      1'bx;
    assign alu_op = beq ? `ALU_OP_SUB :
                    `ALU_OP_ADD;
    assign cond_type = beq ? `COND_TYPE_EQ :
                       2'bx;

    // MEM
    assign mem_read = lw;
    assign mem_write = sw;

    assign wb_sel = addu ? `WB_SEL_ALU_OUT :
                    addiu ? `WB_SEL_ALU_OUT :
                    lw ? `WB_SEL_R_DATA :
                    1'bx;
endmodule
