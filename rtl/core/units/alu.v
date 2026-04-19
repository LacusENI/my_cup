`include "rtl/core/defines.v"

module alu (
    input [31:0] alu_src1,
    input [31:0] alu_src2,
    input [3:0] alu_op,
    output reg [31:0] alu_out,
    output zero_f,
    output neg_f,
    output overflow_f,
    output carry_f
);
    
    always @(*) begin
        case (alu_op)
            `ALU_OP_ADD: alu_out = alu_src1 + alu_src2;
            `ALU_OP_SUB: alu_out = alu_src1 - alu_src2;
            default: alu_out = 32'b0;
        endcase
    end

    assign zero_f = (alu_out == 32'b0);
    assign neg_f = 1'b0; //TODO: 待实现
    assign overflow_f = 1'b0; //TODO: 待实现
    assign carry_f = 1'b0; //TODO: 待实现

endmodule
