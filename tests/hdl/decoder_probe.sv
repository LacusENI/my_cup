`default_nettype none

// ***************************************************************
// test-only probe：把 decoder 的 inst_t 输出摊平成普通端口
//
// Icarus 的 VPI 不会把 packed struct 的字段暴露成子对象，
// 所以单元测试通过这个 probe 读取 opcode/rd/rs1/rs2/funct3/funct7。
// ***************************************************************
module decoder_probe
    import cpu_pkg::*;
(
    input  word_t inst,

    output opcode_t opcode,
    output reg_t    rd,
    output funct3_t funct3,
    output reg_t    rs1,
    output reg_t    rs2,
    output funct7_t funct7,
    output word_t   imm,
    output logic    valid_encoding
);

    inst_t decoded;

    decoder u_decoder (
        .inst(inst),
        .decoded(decoded),
        .imm(imm),
        .valid_encoding(valid_encoding)
    );

    assign opcode = decoded.opcode;
    assign rd     = decoded.rd;
    assign funct3 = decoded.funct3;
    assign rs1    = decoded.rs1;
    assign rs2    = decoded.rs2;
    assign funct7 = decoded.funct7;

endmodule

`default_nettype wire
