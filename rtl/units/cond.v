`define COND_TYPE_EQ  2'b00
`define COND_TYPE_NEQ 2'b01
`define COND_TYPE_LT  2'b10
`define COND_TYPE_LTU 2'b11

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