`include "rtl/core/defines.v"

module Cond (
    input zero_f,
    input neg_f,
    input overflow_f,
    input carry_f,
    input [1:0] cond_type,
    output reg cond_jmp
);

    always @(*) begin
        case (cond_type)
            `COND_TYPE_EQ: 
                cond_jmp = zero_f;
            default: 
                cond_jmp = 1'b0;
        endcase
    end
endmodule