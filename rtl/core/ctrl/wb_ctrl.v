`include "rtl/core/defines.v"

module wb_ctrl (
    input [5:0] op,
    input [5:0] funct,
    output wb_sel
);
    wire addu, addiu, lw;
    assign addu = (op == `OP_R_INSTR) && (funct == `FUNCT_ADDU);
    assign addiu = (op == `OP_ADDIU);
    assign lw = (op == `OP_LW);

    assign wb_sel = addu ? `WB_SEL_ALU_OUT :
                    addiu ? `WB_SEL_ALU_OUT :
                    lw ? `WB_SEL_R_DATA :
                    1'bx;
endmodule