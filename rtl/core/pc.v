`include "rtl/core/defines.v"

module pc (
    input clk,
    input rst,
    input [31:0] next_pc,
    output reg [31:0] curr_pc
);
    always @(posedge clk) begin
        if (rst)
            curr_pc <= 32'b0;
        else
            curr_pc <= next_pc;
    end
endmodule