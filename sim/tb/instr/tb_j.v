`timescale 1ns/1ps

module tb_j ();
    reg clk, rst;

    cpu_top cpu (
        .clk(clk),
        .rst(rst)
    );

    always #5 clk <= ~clk;

    initial begin
        $dumpfile("waves/tb_j.vcd");
        $dumpvars(0, tb_j);

        clk = 0;
        rst = 1;

        cpu.u_pc.curr_pc = 32'd0;
        cpu.u_regfile.regs[1] = 32'd5;
        cpu.u_regfile.regs[2] = 32'd3;
        cpu.u_regfile.regs[3] = 32'd0;
        cpu.u_regfile.regs[4] = 32'd0;

        cpu.u_instrm.mem[0] = 32'h08000002; // j 2 -> target PC = 8
        cpu.u_instrm.mem[1] = 32'h00221821; // addu $3, $1, $2 (跳过，如果跳转成功)
        cpu.u_instrm.mem[2] = 32'h00222021; // addu $4, $1, $2

        #10;
        rst = 0;

        // 等待第一个时钟周期（跳转发生）
        @(posedge clk);
        #1;
        $display("rst=0 后 instr_addr = %d", cpu.instr_addr);

        // 等待第二个时钟周期（执行跳转目标）
        @(posedge clk);
        #1;
        $display("跳转执行后 instr_addr = %d", cpu.instr_addr);
        $display("R[4] = %d", cpu.u_regfile.regs[4]);
        $display("R[3] = %d", cpu.u_regfile.regs[3]);

        if (cpu.instr_addr == 32'd12 && cpu.u_regfile.regs[4] == 32'd8 && cpu.u_regfile.regs[3] == 32'd0)
            $display("TEST PASSED");
        else
            $display("TEST FAILED");

        $finish;
    end
endmodule
