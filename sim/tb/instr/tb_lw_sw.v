`timescale 1ns/1ps

module tb_lw_sw();

    reg clk, rst;

    cpu_top cpu (
        .clk(clk),
        .rst(rst)
    );

    always #5 clk <= ~clk;

    initial begin
        $dumpfile("waves/tb_lw_sw.vcd");
        $dumpvars(0, tb_lw_sw);

        clk = 0;
        rst = 1;

        // 初始化寄存器和数据存储器
        cpu.u_regfile.regs[1] = 32'd4;   // 基址
        cpu.u_regfile.regs[2] = 32'd0;   // lw 的目标寄存器
        cpu.u_regfile.regs[3] = 32'd123; // 要存储的值
        cpu.u_datam.mem[1]      = 32'd0; // 初始化存储器位置

        // 指令序列：
        // sw $3, 4($1)
        // lw $2, 4($1)
        cpu.u_pc.curr_pc       = 32'd0;
        cpu.u_instrm.mem[0]    = 32'hAC230004; // sw $3,4($1)
        cpu.u_instrm.mem[1]    = 32'h8C220004; // lw $2,4($1)

        #10;
        rst = 0;

        // 让 CPU 执行两条指令
        #40;

        $display("lw/sw 测试结果：");
        $display("R[1] = %d", cpu.u_regfile.regs[1]);
        $display("R[3] = %d", cpu.u_regfile.regs[3]);
        $display("Mem[1] = %d", cpu.u_datam.mem[1]);
        $display("R[2] = %d", cpu.u_regfile.regs[2]);

        if (cpu.u_datam.mem[2] == 32'd123 && cpu.u_regfile.regs[2] == 32'd123)
            $display("TEST PASSED");
        else
            $display("TEST FAILED");

        $finish;
    end

endmodule
