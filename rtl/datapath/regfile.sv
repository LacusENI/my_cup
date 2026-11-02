`default_nettype none

module regfile
    import cpu_pkg::*;
(
    input  logic  clk,
    input  reg_t  rs1,
    input  reg_t  rs2,
    input  reg_t  rd,
    input  word_t wb_data,
    input  logic  reg_write,
    output word_t rs1_data,
    output word_t rs2_data
);
    word_t regs[0:31];

    // 读操作：x0 恒为 0
    assign rs1_data = (rs1 == '0) ? '0 : regs[rs1];
    assign rs2_data = (rs2 == '0) ? '0 : regs[rs2];

    // 写操作：上升沿写入，且不写 x0
    always_ff @(posedge clk) begin
        if (reg_write && rd != '0) regs[rd] <= wb_data;
    end
endmodule

`default_nettype wire
