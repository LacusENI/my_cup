`timescale 1ns/1ps

module tb_addu ();
    reg clk, rst;

    cpu_top cpu(
        .clk(clk),
        .rst(rst)
    );

    always #5 clk = ~clk;

    initial begin
        $dumpfile("waves/tb_addu.vcd");
        $dumpvars(0, tb_addu);

        clk = 0;
        rst = 1;

        cpu.u_pc.curr_pc = 32'd0;
        cpu.u_regfile.regs[1] = 32'd5;
        cpu.u_regfile.regs[2] = 32'd3;
        cpu.u_regfile.regs[3] = 32'd0;
        cpu.u_instrm.mem[0] = 32'h00221821; // addu $3, $1, $2

        #10;
        rst = 0;

        // 等待 CPU 执行一条指令
        #20;

        $display("addu $3, $1, $2");
        $display("R[1] = %d", cpu.u_regfile.regs[1]);
        $display("R[2] = %d", cpu.u_regfile.regs[2]);
        $display("R[3] = %d", cpu.u_regfile.regs[3]);
        $display("instr_addr = %d", cpu.instr_addr);

        if (cpu.u_regfile.regs[3] == 8) // 计算结果：5 + 3 = 8
            $display("TEST PASSED");
        else
            $display("TEST FAILED");

        $finish;
    end
endmodule