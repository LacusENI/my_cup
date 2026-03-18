module COND (
    input zero_f,
    input neg_f,
    input overflow_f,
    input carry_f,
    input [2:0] cond_type,
    output reg cond_jmp
);

    localparam CMP_EQ = 3'b001;
    localparam CMP_NEQ = 3'b010;

    always @(*) begin
        case (cond_type)
            CMP_EQ: cond_jmp = zero_f;
            default: cond_jmp = 1'b0;
        endcase
    end
endmodule