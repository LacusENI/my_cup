`default_nettype none

module cond (
    input  logic       zero_f,
    /* verilator lint_off UNUSED */
    input  logic       neg_f,
    input  logic       overflow_f,
    input  logic       carry_f,
    /* verilator lint_on UNUSED */
    input  logic [1:0] cond_type,
    output logic       cond_jmp
);
    import cpu_pkg::*;

    always_comb begin
        unique case (cond_type)
            COND_TYPE_EQ: cond_jmp = zero_f;
            default:      cond_jmp = 1'b0;
        endcase
    end
endmodule

`default_nettype wire
