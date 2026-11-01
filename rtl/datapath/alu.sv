`default_nettype none

module alu
    import cpu_pkg::*;
(
    input  word_t   alu_src1,
    input  word_t   alu_src2,
    input  alu_op_t alu_op,
    output word_t   alu_out,
    output logic    cmp_result
);

    always_comb begin
        alu_out    = '0;
        cmp_result = 1'b0;

        unique case (alu_op)
            ALU_ADD: alu_out = alu_src1 + alu_src2;
            ALU_EQ:  cmp_result = (alu_src1 == alu_src2);
            ALU_NOP: ;
            default: ;
        endcase
    end

endmodule

`default_nettype wire
