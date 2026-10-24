`include "defines.vh"

module datam (
    input clk,
    input mem_read,
    input mem_write,
    input [31:0] addr,
    input [31:0] w_data,
    output reg [31:0] r_data
);
    reg [31:0] mem [0:2047];

    wire [10:0] mem_addr = addr[12:2];

    // 当前仅整字访问：addr[12:2] 有效；高 19 位与低 2 位暂不参与译码
    // （未来接总线 / 字节掩码时再使用）。名字含 unused，Verilator 不会告警。
    wire unused_addr = &{1'b0, addr[31:13], addr[1:0]};

    // 仿真期数据装载 (仅仿真有效, 综合时忽略)
    // 用法: vvp <target> +data=<path/to/data.hex>
    reg [1023:0] init_file;
    initial begin
        if ($value$plusargs("data=%s", init_file))
            $readmemh(init_file, mem);
    end

    // 读操作：当前仅支持整字访问
    always @(*) begin
        if (mem_read)
            r_data = mem[mem_addr];
        else
            r_data = 32'b0;
    end

    // 写操作：当前仅支持整字访问
    always @(posedge clk) begin
        if (mem_write)
            mem[mem_addr] <= w_data;
    end
endmodule
