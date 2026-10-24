`timescale 1ns/1ps
`include "vtest.vh"

module tb_datam ();
    reg clk;
    reg mem_read, mem_write;
    reg [31:0] addr, w_data;
    wire [31:0] r_data;

    datam dut (.*);

    always #5 clk <= ~clk;

    `VTEST_INIT

    initial begin
        $dumpfile("waves/tb_datam.vcd");
        $dumpvars(0, tb_datam);
        `VTEST_BOOT

        clk = 0;
        mem_read = 0;
        mem_write = 0;

        // 测试1: 整字读写
        `TEST(write_read_word_test)
            addr = 32'h0000_0080;
            w_data = 32'hAABB_CCDD;
            mem_write = 1; mem_read = 0;
            #10;

            addr = 32'h0000_0080;
            mem_write = 0; mem_read = 1;
            #10;
            `EXPECT("M_word", r_data, 32'hAABB_CCDD);
        `TEST_END

        // 测试2: 写使能关闭时数据不变
        `TEST(write_disable_test)
            addr = 32'h0000_0080;
            w_data = 32'hAABB_CCDD;
            mem_write = 1; mem_read = 0;
            #10;

            addr = 32'h0000_0080;
            w_data = 32'hFFFF_FFFF;
            mem_write = 0; mem_read = 0;
            #10;

            addr = 32'h0000_0080;
            mem_write = 0; mem_read = 1;
            #10;
            `EXPECT("M_word", r_data, 32'hAABB_CCDD);
        `TEST_END

        // 测试3: 读使能关闭时输出为 0
        `TEST(read_disable_test)
            addr = 32'h0000_0080;
            mem_write = 0; mem_read = 0;
            #10;
            `EXPECT("r_data", r_data, 32'h0000_0000);
        `TEST_END

        `VTEST_FINISH
    end
endmodule
