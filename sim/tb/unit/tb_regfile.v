`timescale 1ns/1ps
`include "vtest.vh"

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

    always #5 clk <= ~clk;

    `VTEST_INIT

    initial begin
        $dumpfile("waves/tb_regfile.vcd");
        $dumpvars(0, tb_regfile);
        
        `VTEST_BOOT
        clk = 0;

        `TEST(regfile_r0_test)
            reg_write = 1;
            reg_dst = 0;
            wb_data = 32'b1001;
            #10;
            reg_write = 0;
            reg_src1 = 0;
            #10;
            `EXPECT("R[0]", rs1_data, 0)
        `TEST_END
        
        `TEST(regfile_src2_test)
            reg_write = 1;
            reg_dst = 2;
            wb_data = 32'b1100;
            #10;
            reg_write = 0;
            reg_src2 = 2;
            #10
            `EXPECT("R[2]", rs2_data, 32'b1100)
        `TEST_END

        `VTEST_FINISH
    end
endmodule
