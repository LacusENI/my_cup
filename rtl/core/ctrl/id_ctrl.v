`include "rtl/core/defines.v"

module id_ctrl (
    input [5:0] op,
    input [5:0] funct,
    output rd_sel,
    output ext_type,
    output reg_write
);
    wire addu, addiu, beq, lw, sw, j;
    assign addu = (op == `OP_R_INSTR) && (funct == `FUNCT_ADDU);
    assign addiu = (op == `OP_ADDIU);
    assign beq = (op == `OP_BEQ);
    assign lw = (op == `OP_LW);
    assign sw = (op == `OP_SW);
    assign j = (op == `OP_J);

    assign rd_sel = lw ? `RD_SEL_RT :
                    addiu ? `RD_SEL_RT :
                    addu ? `RD_SEL_RD : 
                    1'bx;
    assign ext_type = addiu ? `EXT_TYPE_SIGN_EXT :
                      lw ? `EXT_TYPE_SIGN_EXT :
                      sw ? `EXT_TYPE_SIGN_EXT :
                      1'bx;
    assign reg_write = (addu | addiu | lw);
endmodule