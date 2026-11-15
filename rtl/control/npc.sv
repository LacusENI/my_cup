`default_nettype none

module npc
    import cpu_pkg::*;
(
    input  word_t   inst_pc,
    input  npc_op_t npc_op,
    input  logic    branch_taken,
    input  word_t   pc_offset,
    input  word_t   jalr_target,
    output word_t   pc_plus4,
    output word_t   pc_plus_imm,
    output word_t   next_pc
);

    assign pc_plus4 = inst_pc + 32'd4;
    assign pc_plus_imm = inst_pc + pc_offset;

    // 仿真断言：RV32I 没有 C 扩展，所有跳转目标必须 4 字节对齐。
    // jalr 的 bit0 由 NPC 清除，bit1 必须为 0；
    // branch/jal 的目标同样要求 bit1 为 0。
    always_comb begin
        if ((npc_op == NPC_JALR) && jalr_target[1])
            $fatal(1, "npc: unaligned jalr target %0h", jalr_target);
        if (((npc_op == NPC_JAL) ||
             ((npc_op == NPC_BRANCH) && branch_taken)) &&
            pc_plus_imm[1])
            $fatal(1, "npc: unaligned branch/jal target %0h", pc_plus_imm);
    end

    always_comb begin
        unique case (npc_op)
            NPC_PLUS4: next_pc = pc_plus4;
            NPC_BRANCH: next_pc = branch_taken ? pc_plus_imm : pc_plus4;
            NPC_JAL: next_pc = pc_plus_imm;
            NPC_JALR: next_pc = jalr_target & 32'hFFFF_FFFE;
            default: next_pc = pc_plus4;
        endcase
    end

endmodule

`default_nettype wire
