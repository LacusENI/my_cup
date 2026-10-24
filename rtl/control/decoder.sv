`default_nettype none

module decoder
    import cpu_pkg::*;
(
    input  word_t instr,
    output instr_t      decoded,
    output logic [15:0] imm16,
    output logic [25:0] instr_index
);

    // 指令字段（op/rs/rt/rd/shamt/funct）
    assign decoded.op = instr[31:26];
    assign decoded.rs = instr[25:21];
    assign decoded.rt = instr[20:16];
    assign decoded.rd = instr[15:11];
    assign decoded.shamt = instr[10:6];
    assign decoded.funct = instr[5:0];

    // 立即数与跳转索引
    assign imm16 = instr[15:0];
    assign instr_index = instr[25:0];
endmodule

`default_nettype wire
