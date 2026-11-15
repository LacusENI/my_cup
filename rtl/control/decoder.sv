`default_nettype none

module decoder
    import cpu_pkg::*;
(
    input  word_t inst,
    output inst_t decoded,
    output word_t imm,
    output logic  opcode_err
);

    // ----------------------------------------------------------------------- //
    // 字段切分
    // ----------------------------------------------------------------------- //
    assign decoded.funct12 = inst[31:20];
    assign decoded.funct7  = inst[31:25];
    assign decoded.rs2     = inst[24:20];
    assign decoded.rs1     = inst[19:15];
    assign decoded.funct3  = inst[14:12];
    assign decoded.rd      = inst[11:7];
    assign decoded.opcode  = inst[6:0];

    // ----------------------------------------------------------------------- //
    // 立即数生成：纯组合函数
    //
    // B/J 型的立即数在指令中不是连续排列，在这里统一拼成“字节偏移”，
    // NPC 不再左移。U 型立即数直接取指令高 20 位。
    // ----------------------------------------------------------------------- //
    function automatic word_t imm_i(input logic [11:0] i);
        return {{20{i[11]}}, i};
    endfunction

    function automatic word_t imm_s(input logic [11:0] i);
        return {{20{i[11]}}, i};
    endfunction

    function automatic word_t imm_b(input logic [12:0] i);
        return {{19{i[12]}}, i};
    endfunction

    function automatic word_t imm_j(input logic [20:0] i);
        return {{11{i[20]}}, i};
    endfunction

    function automatic word_t imm_gen(input word_t i);
        case (i[6:0])
            OP_IMM, OP_LOAD, OP_JALR: return imm_i(i[31:20]);
            OP_STORE: return imm_s({i[31:25], i[11:7]});
            OP_BRANCH: return imm_b({i[31], i[7], i[30:25], i[11:8], 1'b0});
            OP_JAL: return imm_j({i[31], i[19:12], i[20], i[30:21], 1'b0});
            OP_LUI, OP_AUIPC: return {i[31:12], {12{1'b0}}};
            OP_SYSTEM: return imm_i(i[31:20]);
            default: return '0;
        endcase
    endfunction

    assign imm = imm_gen(inst);

    // ----------------------------------------------------------------------- //
    // opcode 合法性
    //
    // decoder 只判断“是否认识这个 opcode”，用于说明 imm 是否可信。
    // funct3/funct7/rd/rs1/funct12 的完整合法性由 ctrl 统一检查。
    // ----------------------------------------------------------------------- //
    always_comb begin
        unique case (decoded.opcode)
            OP_R, OP_IMM, OP_LOAD, OP_STORE, OP_BRANCH,
            OP_JALR, OP_JAL, OP_LUI, OP_AUIPC,
            OP_MISC_MEM, OP_SYSTEM:
            opcode_err = 1'b0;
            default: opcode_err = 1'b1;
        endcase
    end

endmodule

`default_nettype wire
