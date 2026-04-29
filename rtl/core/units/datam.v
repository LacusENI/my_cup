`include "rtl/core/defines.v"

module datam (
    input clk,
    input mem_read,
    input mem_write,
    /* verilator lint_off UNUSED */
    input [31:0] addr,
    input [1:0] mem_size,
    input [31:0] w_data,
    output reg [31:0] r_data
);
    reg [31:0] mem [0:2047];

    // 读操作
    always @(*) begin
        if (mem_read)
            r_data = mem[addr[31:2]];
        else
            r_data = 32'b0;
    end

    // 写操作
    always @(posedge clk) begin
        if (mem_write)
            mem[addr[31:2]] <= w_data;
    end

endmodule
