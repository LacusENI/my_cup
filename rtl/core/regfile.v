module RF (
    input clk,
    input [4:0] reg_src1,
    input [4:0] reg_src2,
    input [4:0] reg_dst,
    input [31:0] wb_data,
    input reg_write,
    output [31:0] rs1_data,
    output [31:0] rs2_data
);
    reg [31:0] regs [0:31];

    localparam ZERO_REG = 5'b0;

    // 读操作
    assign rs1_data = (reg_src1 == 5'b0) ? 32'b0 : regs[reg_src1];
    assign rs2_data = (reg_src2 == 5'b0) ? 32'b0 : regs[reg_src2];

    // 写操作
    always @(posedge clk) begin
        if (reg_write && reg_dst != ZERO_REG)
            regs[reg_dst] <= wb_data;
    end
endmodule