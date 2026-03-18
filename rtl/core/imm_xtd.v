module ImmXtd (
    input [15:0] imm16,
    input extend_type,
    output [31:0] imm32
);
    wire [31:0] zero_xtd = {16'b0, imm16};
    wire [31:0] sign_xtd = {{16{imm16[15]}}, imm16};

    assign imm32 = extend_type ? sign_xtd : zero_xtd;
endmodule