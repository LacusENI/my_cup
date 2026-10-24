`default_nettype none

module npc
    import cpu_pkg::*;
(
    input  word_t curr_pc,
    input  npc_op_t     npc_op,
    input  logic        cond_jmp,
    input  logic [25:0] jmp_target,
    input  logic [15:0] jmp_offset,
    input  word_t jmp_reg,
    output word_t pc_plus4,
    output word_t next_pc
);

    word_t pc_target;
    word_t pc_offset;
    assign pc_target = {curr_pc[XLEN-1:28], jmp_target, 2'b00};
    assign pc_offset = {{14{jmp_offset[15]}}, jmp_offset, 2'b00};
    assign pc_plus4 = curr_pc + 32'd4;

    always_comb begin
        unique case (npc_op)
            NPC_OP_DIRECT: next_pc = pc_target;
            NPC_OP_BRANCH: next_pc = cond_jmp ? (curr_pc + pc_offset) : pc_plus4;
            NPC_OP_RA:     next_pc = jmp_reg;
            default:       next_pc = pc_plus4;
        endcase
    end
endmodule

`default_nettype wire
