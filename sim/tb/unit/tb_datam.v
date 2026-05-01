`timescale 1ns/1ps
`include "defines.vh"
`include "vtest.vh"

module tb_datam ();
    reg clk;
    reg mem_read, mem_write;
    reg [1:0] mem_size; // 00: Word, 01: Half, 10: Byte
    reg [31:0] addr, w_data;
    wire [31:0] r_data;

    datam dut (.*);

    always #5 clk <= ~clk;

    task check_result(input [31:0] expected);
        begin
            mem_write = 0;
            mem_read = 1;
            #10;
            `EXPECT("r_data", r_data, expected)
            mem_read = 0;
        end
    endtask

    `VTEST_INIT

    initial begin
        $dumpfile("waves/tb_datam.vcd");
        $dumpvars(0, tb_datam);
        `VTEST_BOOT

        clk = 0;
        mem_read = 0;
        mem_write = 0;

        // 测试1: 读写全字
        `TEST(write_read_test)
            addr = 32'h0000_0080;
            w_data = 32'hAABBCCDD;
            mem_size = 2'b00; mem_write = 1; 
            #10;
            check_result(32'hAABBCCDD);
        `TEST_END

        // 测试2: 修改第 0 字节 (最高位字节)
        `TEST(write_byte0_test)
            addr = 32'h0000_0080;
            w_data = 32'h0000_0011; // 尝试把 AA 改成 11
            mem_size = 2'b10; mem_write = 1; 
            #10;
            check_result(32'h11BBCCDD);
        `TEST_END

        // 测试3: 修改第 3 字节 (最低位字节)
        `TEST(write_byte3_test)
            addr = 32'h0000_0083;
            w_data = 32'h0000_00FF; // 尝试把 DD 改成 FF
            mem_size = 2'b10; mem_write = 1; 
            #10;
            check_result(32'h11BBCCFF);
        `TEST_END

        // 测试4: 测试 sh: 修改大端的低半字
        `TEST(write_half_word_test)
            addr = 32'h0000_0082;
            w_data = 32'h0000_5566; // 尝试把 CCFF 改成 5566
            mem_size = 2'b01; mem_write = 1; #10;
            check_result(32'h11BB5566);
        `TEST_END

        // 测试5: 测试写入禁用
        `TEST(write_disable_test)
            addr = 32'h0000_0080;
            w_data = 32'hFFFFFFFF;
            mem_write = 0; #10;
            check_result(32'h11BB5566); // 数据不应改变
        `TEST_END

        `VTEST_FINISH
    end
endmodule
