`default_nettype none

// MEM/WB 流水线寄存器
module mem_wb_reg
    import cpu_pkg::*;
(
    input  logic   clk,
    input  logic   rst,
    input  logic   flush,
    input  logic   stall,
    input  mem_wb_t mem_wb_in,
    output mem_wb_t mem_wb_out
);
    always_ff @(posedge clk) begin
        if (rst || flush)
            mem_wb_out <= '0;
        else if (!stall)
            mem_wb_out <= mem_wb_in;
    end
endmodule

`default_nettype wire
