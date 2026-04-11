`timescale 1ns/1ps

module tb_regfile ();
    reg clk;
    reg [4:0] reg_src1;
    reg [4:0] reg_src2;
    reg [4:0] reg_dst;
    reg [31:0] wb_data;
    reg reg_write;
    wire [31:0] rs1_data;
    wire [31:0] rs2_data;

    regfile dut (.*);

    always #5 clk = ~clk;

    initial begin
        $dumpfile("waves/tb_regfile.vcd");
        $dumpvars(0, tb_regfile);

        clk = 0;

        reg_write = 1;
        reg_dst = 0;
        wb_data = 32'b1001;
        #10;
        $display("write $0 %b", wb_data);

        reg_write = 0;
        reg_src1 = 0;
        #10;
        $display("read $0 %b", rs1_data);

        reg_write = 1;
        reg_dst = 2;
        wb_data = 32'b1100;
        #10;
        $display("write $2 %b", wb_data);

        reg_write = 0;
        reg_src2 = 2;
        #10
        $display("read $2 %b", rs2_data);
        $display("tb_regfile 测试完毕");
        $finish;
    end
endmodule