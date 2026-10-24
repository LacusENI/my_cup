`default_nettype none

module ext
    import cpu_pkg::*;
(
    input  logic [15:0] imm16,
    input  ext_type_t   ext_type,
    output word_t imm32
);

    word_t zero_ext;
    word_t sign_ext;
    assign zero_ext = z_ext_16_32(imm16);
    assign sign_ext = s_ext_16_32(imm16);

    always_comb begin
        unique case (ext_type)
            EXT_TYPE_ZERO_EXT: imm32 = zero_ext;
            EXT_TYPE_SIGN_EXT: imm32 = sign_ext;
            default:           imm32 = '0;
        endcase
    end
endmodule

`default_nettype wire
