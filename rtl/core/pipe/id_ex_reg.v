`default_nettype none

// ID/EX 流水线寄存器
module id_ex_reg
    import cpu_pkg::*;
(
    input  logic   clk,
    input  logic   rst,
    input  logic   flush,
    input  logic   stall,
    input  id_ex_t id_ex_in,
    output id_ex_t id_ex_out
);
    always_ff @(posedge clk) begin
        if (rst || flush)
            id_ex_out <= '0;
        else if (!stall)
            id_ex_out <= id_ex_in;
    end
endmodule

`default_nettype wire
