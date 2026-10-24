`default_nettype none

module regfile (
    input  logic        clk,
    input  logic [4:0]  reg_src1,
    input  logic [4:0]  reg_src2,
    input  logic [4:0]  reg_dst,
    input  logic [31:0] wb_data,
    input  logic        reg_write,
    output logic [31:0] rs1_data,
    output logic [31:0] rs2_data
);
    logic [31:0] regs [0:31];

    localparam logic [4:0] ZERO_REG = '0;

    // 读操作：$0 恒为 0
    assign rs1_data = (reg_src1 == ZERO_REG) ? '0 : regs[reg_src1];
    assign rs2_data = (reg_src2 == ZERO_REG) ? '0 : regs[reg_src2];

    // 写操作：上升沿写入，且不写 $0
    always_ff @(posedge clk) begin
        if (reg_write && reg_dst != ZERO_REG)
            regs[reg_dst] <= wb_data;
    end
endmodule

`default_nettype wire
