`default_nettype none

// EX/MEM 流水线寄存器
module ex_mem_reg
    import cpu_pkg::*;
(
    input  logic   clk,
    input  logic   rst,
    input  logic   flush,
    input  logic   stall,
    input  ex_mem_t ex_mem_in,
    output ex_mem_t ex_mem_out
);
    always_ff @(posedge clk) begin
        if (rst || flush)
            ex_mem_out <= '0;
        else if (!stall)
            ex_mem_out <= ex_mem_in;
    end
endmodule

`default_nettype wire
