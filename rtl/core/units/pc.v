`default_nettype none

module pc
    import cpu_pkg::*;
(
    input  logic        clk,
    input  logic        rst,
    input  word_t next_pc,
    output word_t curr_pc
);
    always_ff @(posedge clk) begin
        if (rst)
            curr_pc <= '0;
        else
            curr_pc <= next_pc;
    end
endmodule

`default_nettype wire
