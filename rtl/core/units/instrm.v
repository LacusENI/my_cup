`include "rtl/core/defines.v"

module instrm (
    input [31:0] instr_addr,
    output [31:0] instr
);
    reg [31:0] mem [0:2047];

    assign instr = mem[instr_addr[31:2]];
endmodule
