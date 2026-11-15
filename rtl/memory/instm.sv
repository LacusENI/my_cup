`default_nettype none

module instm
    import cpu_pkg::*;
(
    input  word_t inst_addr,
    output word_t inst,
    output logic  inst_addr_err
);
    word_t mem[0:IMEM_WORDS-1];

    logic [IMEM_ADDR_W-1:0] mem_addr;
    assign mem_addr = inst_addr[IMEM_ADDR_W+1:2];
    assign inst = mem[mem_addr];

    // 高地址位暂不参与译码；名字含 unused，Verilator 不会告警。
    logic unused_addr;
    assign unused_addr = &{1'b0, inst_addr[XLEN-1:IMEM_ADDR_W+2]};

    // 地址错误只上报，不在存储器内部停机；由 cpu_top 统一仲裁。
    assign inst_addr_err = (inst_addr[1:0] != 2'b00);

    // 仿真期程序装载 (仅仿真有效, 综合时忽略)
    // 用法: vvp <target> +inst=<path/to/program.hex>
    logic [1023:0] init_file;
    initial begin
        if ($value$plusargs("inst=%s", init_file)) $readmemh(init_file, mem);
    end
endmodule

`default_nettype wire
