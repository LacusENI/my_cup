`timescale 1ns/1ps
`include "defines.vh"
`include "vtest.vh"

module tb_datam ();
    reg clk;
    reg mem_read, mem_write, read_signed;
    reg [1:0] mem_size; // 00: Word, 01: Half, 10: Byte
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

        // 测试1: 读写全字
        `TEST(write_read_word_test)
            // 写入字
            addr = 32'h0000_0080;
            w_data = 32'hAABB_CCDD;
            mem_size = `MEM_SIZE_WORD; 
            mem_write = 1; mem_read = 0;
            #10;
            // 读取字
            addr = 32'h0000_0080;
            mem_size = `MEM_SIZE_WORD; 
            mem_write = 0; mem_read = 1;
            #10;
            `EXPECT("M_word[+0]", r_data, 32'hAABB_CCDD);
        `TEST_END

        // 测试2: 测试写入字节
        `TEST(write_byte_test)
            // 写入初始数据
            addr = 32'h0000_0080;
            w_data = 32'h0000_0000;
            mem_size = `MEM_SIZE_WORD; 
            mem_write = 1; mem_read = 0;
            #10;
            // 写入最高位字节(偏移: 0)
            addr = 32'h0000_0080;
            w_data = 32'h0000_0011; // byte[0] = 8'h11
            mem_size = `MEM_SIZE_BYTE; 
            mem_write = 1; mem_read = 0;
            #10;
            // 写入最低位字节(偏移: 3)
            addr = 32'h0000_0083;
            w_data = 32'h0000_00FF; // byte[3] = 8'hFF
            mem_size = `MEM_SIZE_BYTE; 
            mem_write = 1; mem_read = 0;
            #10;
            // 检验: 读取整个字
            addr = 32'h0000_0080;
            mem_size = `MEM_SIZE_WORD;
            mem_write = 0; mem_read = 1;
            #10;
            `EXPECT("M_word[+0]", r_data, 32'h1100_00FF);
        `TEST_END

        // 测试3: 测试读取字节
        `TEST(read_byte_test)
            // 写入字
            addr = 32'h0000_0080;
            w_data = 32'hAABB_CCDD;
            mem_size = `MEM_SIZE_WORD; 
            mem_write = 1; mem_read = 0;
            #10;
            // 读取字节(无符号, 偏移: 1)
            addr = 32'h0000_0081;
            mem_size = `MEM_SIZE_BYTE;
            mem_write = 0; mem_read = 1;
            read_signed = 0;
            #10;
            `EXPECT("M_unsigned_byte[+1]", r_data, 32'h0000_00BB);
            // 读取字节(有符号, 偏移: 2)
            addr = 32'h0000_0082;
            mem_size = `MEM_SIZE_BYTE;
            mem_write = 0; mem_read = 1;
            read_signed = 1;
            #10;
            `EXPECT("M_signed_byte[+2]", r_data, 32'hFFFF_FFCC);
        `TEST_END

        // 测试4: 测试写入半字:
        `TEST(write_half_word_test)
            // 写入高位半字(偏移: 0)
            addr = 32'h0000_0080;
            w_data = 32'h0000_AABB; // halfword[0] = 16'hAABB
            mem_size = `MEM_SIZE_HALF; 
            mem_write = 1; mem_read = 0;
            #10;
            // 写入低位半字(偏移: 2)
            addr = 32'h0000_0082;
            w_data = 32'h0000_5566; // halfword[1] = 16'5566
            mem_size = `MEM_SIZE_HALF; 
            mem_write = 1; mem_read = 0;
            #10;
            // 读取数据
            addr = 32'h0000_0080;
            mem_size = `MEM_SIZE_WORD;
            mem_write = 0; mem_read = 1;
            #10;
            `EXPECT("M_word[+0]", r_data, 32'hAABB5566);
        `TEST_END

        // 测试5: 测试读取半字
        `TEST(read_half_word_test)
            // 写入数据
            addr = 32'h0000_0080;
            w_data = 32'hAABB_CCDD;
            mem_size = `MEM_SIZE_WORD; 
            mem_write = 1; mem_read = 0;
            #10;
            // 读取半字(无符号, 偏移: 0)
            addr = 32'h0000_0080;
            mem_size = `MEM_SIZE_HALF;
            mem_write = 0; mem_read = 1;
            read_signed = 0;
            #10;
            `EXPECT("M_unsigned_halfword[+0]", r_data, 32'h0000_AABB);
            // 读取半字(有符号, 偏移: 2)
            addr = 32'h0000_0082;
            mem_size = `MEM_SIZE_HALF;
            mem_write = 0; mem_read = 1;
            read_signed = 1;
            #10;
            `EXPECT("M_signed_halfword[+2]", r_data, 32'hFFFF_CCDD);
        `TEST_END

        // 测试6: 测试写入禁用
        `TEST(write_disable_test)
            // 写入数据
            addr = 32'h0000_0080;
            w_data = 32'hAABBCCDD;
            mem_size = `MEM_SIZE_WORD;
            mem_write = 0; mem_read = 0;
            #10;
            // 修改 w_data, 但写使能信号置零
            addr = 32'h0000_0080;
            w_data = 32'hFFFFFFFF;
            mem_size = `MEM_SIZE_WORD;
            mem_write = 0; mem_read = 0;
            #10;
            // 读取数据(数据应当不被修改)
            addr = 32'h0000_0080;
            mem_size = `MEM_SIZE_WORD;
            mem_write = 0; mem_read = 1;
            #10;
            `EXPECT("r_data", r_data, 32'hAABBCCDD);
        `TEST_END

        `VTEST_FINISH
    end
endmodule
