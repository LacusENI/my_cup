`timescale 1ns/1ps

module tb_datam ();
    reg clk;
    reg mem_read, mem_write;
    reg [1:0] mem_size; // 00: Word, 01: Half, 10: Byte
    reg [31:0] addr, w_data;
    wire [31:0] r_data;

    integer errors = 0;

    datam dut (.*);

    always #5 clk <= ~clk;

    task check_result(input [31:0] expected);
        begin
            mem_write = 0;
            mem_read = 1;
            #10;
            if (r_data !== expected) begin
                $display("  [ERROR] Addr: %h | Get: %h | Expected: %h", addr, r_data, expected);
                errors = errors + 1;
            end else begin
                $display("  [PASS]  Addr: %h | Data: %h", addr, r_data);
            end
            mem_read = 0;
        end
    endtask

    initial begin
        $dumpfile("waves/tb_datam.vcd");
        $dumpvars(0, tb_datam);

        clk = 0;
        mem_read = 0;
        mem_write = 0;
        errors = 0;

        $display("tb_datam");

        // 1. 测试 sw: 写入全字
        $display("TEST[1]: sw (Word) at 0x80");
        addr = 32'h0000_0080; 
        w_data = 32'hAABBCCDD;
        mem_size = 2'b00; mem_write = 1; #10;
        check_result(32'hAABBCCDD);

        // 2. 测试 sb: 修改大端的第 0 字节 (最高位字节)
        $display("TEST[2]: sb (Byte) at 0x80 (addr[1:0]=00)");
        addr = 32'h0000_0080;
        w_data = 32'h0000_0011; // 尝试把 AA 改成 11
        mem_size = 2'b10; mem_write = 1; #10;
        check_result(32'h11BBCCDD);

        // 3. 测试 sb: 修改大端的第 3 字节 (最低位字节)
        $display("TEST[3]: sb (Byte) at 0x83 (addr[1:0]=11)");
        addr = 32'h0000_0083;
        w_data = 32'h0000_00FF; // 尝试把 DD 改成 FF
        mem_size = 2'b10; mem_write = 1; #10;
        check_result(32'h11BBCCFF);

        // 4. 测试 sh): 修改大端的低半字
        $display("TEST[4]: sh (Halfword) at 0x82 (addr[1]=1)");
        addr = 32'h0000_0082;
        w_data = 32'h0000_5566; // 尝试把 CCFF 改成 5566
        mem_size = 2'b01; mem_write = 1; #10;
        check_result(32'h11BB5566);

        // 5. 测试写入禁用
        $display("TEST[5]: Write Disabled check");
        addr = 32'h0000_0080;
        w_data = 32'hFFFFFFFF;
        mem_write = 0; #10;
        check_result(32'h11BB5566); // 数据不应改变

        if (errors == 0)
            $display("\nTEST PASSED");
        else
            $display("\nTEST FAILED with %d errors", errors);

        $finish;
    end
endmodule
