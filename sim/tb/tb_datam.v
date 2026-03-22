`timescale 1ns/1ps

module tb_datam ();
    reg clk;
    reg mem_read, mem_write;
    reg [31:0] addr, w_data;
    wire [31:0] r_data;

    datam dut (.*);

    always #5 clk = ~clk;

    initial begin
        $dumpfile("waves/tb_datam.vcd");
        $dumpvars(0, tb_datam);

        clk = 0;

        mem_write = 1;
        addr = 32'b1000_1000;
        w_data = 32'b0010_0001;
        #10;
        $display("write(enabled)  %b %b", addr, w_data);

        mem_write = 0;
        mem_read = 1;
        #10;
        $display("read(enable)    %b %b", addr, r_data);

        mem_write = 0;
        w_data = 32'b1111_0111;
        #10;
        $display("write(disabled) %b %b", addr, w_data);

        mem_read = 1;
        #10;
        $display("read(enable)    %b %b", addr, r_data);

        $display("tb_datam 测试完毕");
        $finish;
    end
endmodule