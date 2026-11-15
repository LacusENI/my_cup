`default_nettype none

module datam
    import cpu_pkg::*;
(
    input  logic  clk,
    input  logic  mem_read_en,
    input  logic  mem_write_en,
    input  word_t addr,
    input  word_t w_data,
    output word_t r_data,
    output logic  addr_err
);
    word_t mem[0:DMEM_WORDS-1];

    logic [DMEM_ADDR_W-1:0] mem_addr;
    assign mem_addr = addr[DMEM_ADDR_W+1:2];

    // 当前仅整字访问：addr[DMEM_ADDR_W+1:2] 有效；高 19 位与低 2 位暂不参与译码
    // （未来接总线 / 字节掩码时再使用）。名字含 unused，Verilator 不会告警。
    logic unused_addr;
    assign unused_addr = &{1'b0, addr[XLEN-1:DMEM_ADDR_W+2], addr[1:0]};

    // 仿真期数据装载 (仅仿真有效, 综合时忽略)
    // 用法: vvp <target> +data=<path/to/data.hex>
    logic [1023:0] init_file;
    initial begin
        if ($value$plusargs("data=%s", init_file)) $readmemh(init_file, mem);
    end

    // 地址未对齐只上报；是否真的触发访问故障由 cpu_top 结合读/写意图判断。
    assign addr_err = (addr[1:0] != 2'b00);

    // 读操作：当前仅支持整字访问
    always_comb begin
        if (mem_read_en) r_data = mem[mem_addr];
        else r_data = '0;
    end

    // 写操作：当前仅支持整字访问
    always_ff @(posedge clk) begin
        if (mem_write_en) mem[mem_addr] <= w_data;
    end
endmodule

`default_nettype wire
