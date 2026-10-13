`timescale 1ns/1ps
`include "vtest.vh"

// 程序装载验证: 依赖 RTL 中的 $readmemh + plusarg 机制
//   make run-tb_prog PROG=programs/demo.hex
// 未提供 PROG 时自动跳过, 不影响 make all。
module tb_prog ();
    reg clk, rst;

    cpu_top cpu (
        .clk(clk),
        .rst(rst)
    );

    always #5 clk <= ~clk;

    `VTEST_INIT

    initial begin
        $dumpfile("waves/tb_prog.vcd");
        $dumpvars(0, tb_prog);

        if (!$test$plusargs("instr")) begin
            $display("[ SKIP ] tb_prog: 未提供 +instr=<file>, 已跳过");
            $display("         运行示例: make run-tb_prog PROG=programs/demo.hex");
            $finish;
        end

        `VTEST_BOOT

        clk = 0;
        rst = 1;
        #10;
        rst = 0;
        #60; // 足够执行 demo.hex 的 3 条指令

        `TEST(prog_demo)
            // addiu $1,$0,8 ; addiu $2,$0,5 ; addu $3,$1,$2  => $3 = 13
            `EXPECT("R[1]", cpu.u_regfile.regs[1], 32'd8);
            `EXPECT("R[2]", cpu.u_regfile.regs[2], 32'd5);
            `EXPECT("R[3]", cpu.u_regfile.regs[3], 32'd13);
        `TEST_END

        `VTEST_FINISH
    end
endmodule
