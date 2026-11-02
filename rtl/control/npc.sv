`default_nettype none

module npc
    import cpu_pkg::*;
(
    input  word_t   inst_pc,
    input  npc_op_t npc_op,
    input  logic    branch_taken,
    input  word_t   pc_offset,
    input  word_t   jalr_target,
    input  logic    inst_illegal,
    output word_t   pc_plus4,
    output word_t   next_pc
);

    assign pc_plus4 = inst_pc + 32'd4;

    // 仿真断言：RV32I 没有 C 扩展，jalr 目标必须 4 字节对齐。
    // bit0 由 NPC 清除；bit1 必须为 0。
    always_comb begin
        if (!inst_illegal && (npc_op == NPC_JALR) && jalr_target[1])
            $fatal(1, "npc: unaligned jalr target %0h", jalr_target);
    end

    always_comb begin
        if (inst_illegal) begin
            // 非法指令停止取指：PC 保持，后续不会再执行新指令。
            next_pc = inst_pc;
        end else begin
            unique case (npc_op)
                NPC_PLUS4: next_pc = pc_plus4;
                NPC_BRANCH: next_pc = branch_taken ? (inst_pc + pc_offset) : pc_plus4;
                NPC_JAL: next_pc = inst_pc + pc_offset;
                NPC_JALR: next_pc = jalr_target & 32'hFFFF_FFFE;
                default: next_pc = pc_plus4;
            endcase
        end
    end

endmodule

`default_nettype wire
