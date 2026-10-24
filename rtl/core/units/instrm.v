`default_nettype none

module instrm
    import cpu_pkg::*;
(
    /* verilator lint_off UNUSED */
    input  word_t instr_addr,
    /* verilator lint_on UNUSED */
    output word_t instr
);
    word_t mem [0:IMEM_WORDS-1];

    logic [IMEM_ADDR_W-1:0] mem_addr;
    assign mem_addr = instr_addr[IMEM_ADDR_W+1:2];
    assign instr = mem[mem_addr];

    // 仿真期程序装载 (仅仿真有效, 综合时忽略)
    // 用法: vvp <target> +instr=<path/to/program.hex>
    logic [1023:0] init_file;
    initial begin
        if ($value$plusargs("instr=%s", init_file))
            $readmemh(init_file, mem);
    end
endmodule

`default_nettype wire
