`default_nettype none

module pc (
    input  logic        clk,
    input  logic        rst,
    input  logic [31:0] next_pc,
    output logic [31:0] curr_pc
);
    always_ff @(posedge clk) begin
        if (rst)
            curr_pc <= '0;
        else
            curr_pc <= next_pc;
    end
endmodule

`default_nettype wire
