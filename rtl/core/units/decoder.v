`default_nettype none

module decoder (
    input  logic [31:0] instr,
    output logic [5:0]  op,
    output logic [5:0]  funct,
    output logic [4:0]  shamt,
    output logic [4:0]  rs,
    output logic [4:0]  rt,
    output logic [4:0]  rd,
    output logic [15:0] imm16,
    output logic [25:0] instr_index
);
    assign op = instr[31:26];
    assign funct = instr[5:0];
    assign shamt = instr[10:6];
    assign rs = instr[25:21];
    assign rt = instr[20:16];
    assign rd = instr[15:11];
    assign imm16 = instr[15:0];
    assign instr_index = instr[25:0];
endmodule

`default_nettype wire
