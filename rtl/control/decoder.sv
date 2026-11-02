`default_nettype none

module decoder
    import cpu_pkg::*;
(
    input  word_t inst,
    output inst_t decoded,
    output word_t imm,
    output logic  valid_encoding
);

    // ----------------------------------------------------------------------- //
    // 字段切分
    // ----------------------------------------------------------------------- //
    assign decoded.funct7 = inst[31:25];
    assign decoded.rs2    = inst[24:20];
    assign decoded.rs1    = inst[19:15];
    assign decoded.funct3 = inst[14:12];
    assign decoded.rd     = inst[11:7];
    assign decoded.opcode = inst[6:0];

    // ----------------------------------------------------------------------- //
    // 立即数生成：纯组合函数
    //
    // 只在本批 7 条指令范围内使用。B/J 型的立即数在指令中不是连续排列，
    // 在这里统一拼成“字节偏移”，NPC 不再左移。
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
            default: return '0;
        endcase
    endfunction

    assign imm = imm_gen(inst);

    // ----------------------------------------------------------------------- //
    // 合法编码判断
    //
    // 当前只接受 7 条指令。任何未实现/非法 opcode、funct3、funct7 都输出 0，
    // 后续由 ctrl 统一转成 inst_illegal 并停止执行。
    // ----------------------------------------------------------------------- //
    always_comb begin
        valid_encoding = 1'b1;
        unique case (decoded.opcode)
            OP_R:      valid_encoding = (decoded.funct3 == F3_ADD) && (decoded.funct7 == F7_ADD);
            OP_IMM:    valid_encoding = (decoded.funct3 == F3_ADD);
            OP_LOAD:   valid_encoding = (decoded.funct3 == F3_LW);
            OP_STORE:  valid_encoding = (decoded.funct3 == F3_SW);
            OP_BRANCH: valid_encoding = (decoded.funct3 == F3_BEQ);
            OP_JALR:   valid_encoding = (decoded.funct3 == F3_JALR);
            OP_JAL:    valid_encoding = 1'b1;
            default:   valid_encoding = 1'b0;
        endcase
    end

endmodule

`default_nettype wire
