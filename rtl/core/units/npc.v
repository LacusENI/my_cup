`include "defines.vh"

module npc (
    input [31:0] curr_pc,
    input [1:0]  npc_op,
    input        cond_jmp,
    input [25:0] jmp_target,
    input [15:0] jmp_offset,
    input [31:0] ra,
    output [31:0] pc_plus4,
    output reg [31:0] next_pc
);
    wire [31:0] pc_target = {curr_pc[31:28], jmp_target, 2'b00};
    wire [31:0] pc_offset = {{14{jmp_offset[15]}}, jmp_offset, 2'b00};
    assign pc_plus4 = curr_pc + 4;

    always @(*) begin
        if (npc_op == `NPC_OP_DIRECT)
            next_pc = pc_target;
        else if ((npc_op == `NPC_OP_BRANCH) && cond_jmp)
            next_pc = curr_pc + pc_offset;
        else if (npc_op == `NPC_OP_RA)
            next_pc = ra;
        else
            next_pc = pc_plus4;
    end
endmodule
