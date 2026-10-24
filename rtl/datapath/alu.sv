`default_nettype none

module alu
    import cpu_pkg::*;
(
    input  word_t alu_src1,
    input  word_t alu_src2,
    input  alu_op_t     alu_op,
    output word_t alu_out,
    output logic        zero_f,
    output logic        neg_f,
    output logic        overflow_f,
    output logic        carry_f
);

    always_comb begin
        unique case (alu_op)
            ALU_OP_ADD: alu_out = alu_src1 + alu_src2;
            ALU_OP_SUB: alu_out = alu_src1 - alu_src2;
            default:    alu_out = '0;
        endcase
    end

    assign zero_f = (alu_out == '0);
    assign neg_f = 1'b0;  // TODO: 待实现
    assign overflow_f = 1'b0;  // TODO: 待实现
    assign carry_f = 1'b0;  // TODO: 待实现

endmodule

`default_nettype wire
