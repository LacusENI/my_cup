`include "defines.vh"
`include "ext.vh"

module ext (
    input [15:0] imm16,
    input ext_type,
    output [31:0] imm32
);
    
    wire [31:0] zero_ext = z_ext_16_32(imm16);
    wire [31:0] sign_ext = s_ext_16_32(imm16);

    assign imm32 = ext_type ? sign_ext : zero_ext;
endmodule
