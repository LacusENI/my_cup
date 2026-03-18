module NPC (
    input [31:0] curr_pc,
    input jmp,
    input cond_jmp,
    input [31:0] jmp_target,
    input [31:0] jmp_offset,
    output reg [31:0] next_pc
);
    always @(*) begin
        if (jmp)
            next_pc = jmp_target;
        else if (cond_jmp)
            next_pc = curr_pc + jmp_offset;
        else
            next_pc = curr_pc + 4;
    end
endmodule