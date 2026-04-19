`include "rtl/core/defines.v"

module decoder (
    input [31:0] instr,
    output [5:0] op,
    output [5:0] funct,
    output [4:0] shamt,
    output [4:0] rs, rt, rd,
    output [15:0] imm16,
    output [25:0] instr_index
);
    assign op = instr[31:26];

    assign instr_index = instr[25:0];

    assign rs = instr[25:21];
    assign rt = instr[20:16];
    assign rd = instr[15:11];

    assign imm16 = instr[15:0];
    
    assign shamt = instr[10:6];
    assign funct = instr[5:0];
endmodule
