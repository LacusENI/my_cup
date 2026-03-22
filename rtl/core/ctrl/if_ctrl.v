`include "rtl/core/defines.v"

module if_ctrl (
    input [5:0] op,
    input [5:0] funct,
    output [1:0] npc_op
);
    wire beq, j;

    assign beq = (op == `OP_BEQ);
    assign j = (op == `OP_J);

    assign npc_op = beq ? `NPC_OP_BRANCH :
                    j ? `NPC_OP_DIRECT :
                    `NPC_OP_PLUS4;
endmodule