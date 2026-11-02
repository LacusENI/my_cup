`default_nettype none

module instm
    import cpu_pkg::*;
(
    input  word_t inst_addr,
    output word_t inst
);
    word_t mem[0:IMEM_WORDS-1];

    logic [IMEM_ADDR_W-1:0] mem_addr;
    assign mem_addr = inst_addr[IMEM_ADDR_W+1:2];
    assign inst = mem[mem_addr];

    // 仿真断言：取指地址必须 4 字节对齐。
    // PC 只按 4 递增，正常情况下不会触发；这里用于捕获未来 jalr 等路径的错误。
    always_comb begin
        if (inst_addr[1:0] != 2'b00)
            $fatal(1, "instm: unaligned instruction address %0h", inst_addr);
    end

    // 仿真期程序装载 (仅仿真有效, 综合时忽略)
    // 用法: vvp <target> +inst=<path/to/program.hex>
    logic [1023:0] init_file;
    initial begin
        if ($value$plusargs("inst=%s", init_file)) $readmemh(init_file, mem);
    end
endmodule

`default_nettype wire
