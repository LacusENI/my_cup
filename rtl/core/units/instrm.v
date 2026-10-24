`default_nettype none

module instrm (
    /* verilator lint_off UNUSED */
    input  logic [31:0] instr_addr,
    /* verilator lint_on UNUSED */
    output logic [31:0] instr
);
    logic [31:0] mem [0:2047];

    logic [10:0] mem_addr;
    assign mem_addr = instr_addr[12:2];
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
