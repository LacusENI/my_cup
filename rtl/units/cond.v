module Cond (
    input zero_f,
    input neg_f,
    input overflow_f,
    input carry_f,
    input [1:0] cond_type,
    output reg cond_jmp
);

    localparam CMP_EQ = 2'b00;
    localparam CMP_NEQ = 2'b01;
    localparam CMP_LT = 2'b10;
    localparam CMP_LTU = 2'b11;

    always @(*) begin
        case (cond_type)
            CMP_EQ: cond_jmp = zero_f;
            default: cond_jmp = 1'b0;
        endcase
    end
endmodule