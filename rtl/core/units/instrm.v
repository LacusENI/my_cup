`include "rtl/core/defines.v"

module instrm (
    /* verilator lint_off UNUSED */
    input [31:0] instr_addr,
    output [31:0] instr
);
    reg [31:0] mem [0:2047];

    wire [10:0] mem_addr = instr_addr[12:2];

    assign instr = mem[mem_addr];
endmodule
