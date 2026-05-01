`include "defines.vh"

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

    wire [10:0] mem_addr = addr[12:2];

    // 读操作
    always @(*) begin
        if (mem_read)
            r_data = mem[mem_addr];
        else
            r_data = 32'b0;
    end
 
    // 写操作
    always @(posedge clk) begin
        if (mem_write) begin
            case (mem_size)
                `MEM_SIZE_WORD: begin // 字
                    mem[mem_addr] <= w_data;
                end
                `MEM_SIZE_HALF: begin // 半字
                    if (addr[1] == 1'b0)
                        mem[mem_addr][31:16] <= w_data[15:0];
                    else
                        mem[mem_addr][15:0] <= w_data[15:0];
                end
                `MEM_SIZE_BYTE: begin // 字节
                    case (addr[1:0])
                        2'b00: mem[mem_addr][31:24] <= w_data[7:0];
                        2'b01: mem[mem_addr][23:16] <= w_data[7:0];
                        2'b10: mem[mem_addr][15:8] <= w_data[7:0];
                        2'b11: mem[mem_addr][7:0] <= w_data[7:0];
                    endcase
                end
                default: begin
                    // 不应发生
                end
            endcase
        end
    end
endmodule
