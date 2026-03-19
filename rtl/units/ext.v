module Ext (
    input [15:0] imm16,
    input ext_type,
    output [31:0] imm32
);
    wire [31:0] zero_ext = {16'b0, imm16};
    wire [31:0] sign_ext = {{16{imm16[15]}}, imm16};

    assign imm32 = ext_type ? sign_ext : zero_ext;
endmodule