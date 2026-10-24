`default_nettype none

module ext (
    input  logic [15:0] imm16,
    input  logic        ext_type,
    output logic [31:0] imm32
);
    import cpu_pkg::*;

    logic [31:0] zero_ext;
    logic [31:0] sign_ext;
    assign zero_ext = z_ext_16_32(imm16);
    assign sign_ext = s_ext_16_32(imm16);

    assign imm32 = ext_type ? sign_ext : zero_ext;
endmodule

`default_nettype wire
