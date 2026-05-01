`timescale 1ns/1ps
`include "vtest.vh"
`include "instr.vh"

module tb_beq ();
    reg clk, rst;

    cpu_top cpu (
        .clk(clk),
        .rst(rst)
    );

    always #5 clk <= ~clk;

    // addu rd, rs, rt
    function [31:0] addu_code(input [4:0] rd, input [4:0] rs, input [4:0] rt);
        addu_code = {`OP_R, rs, rt, rd, 5'b0, `FUNCT_ADDU};
    endfunction

    // beq, rs, rt, offset
    function [31:0] beq_code(input [4:0] rs, input[4:0] rt, input [15:0] offset);
        beq_code = {`OP_BEQ, rs, rt, offset};
    endfunction

    `VTEST_INIT

    initial begin
        $dumpfile("waves/tb_beq.vcd");
        $dumpvars(0, tb_beq);

        `VTEST_BOOT

        `TEST(beq_jmp_test)
            clk = 0;
            rst = 1;

            cpu.u_pc.curr_pc = 32'd0;
            cpu.u_regfile.regs[1] = 32'd7;
            cpu.u_regfile.regs[2] = 32'd7;
            cpu.u_regfile.regs[3] = 32'd0;
            cpu.u_regfile.regs[4] = 32'd0;

            cpu.u_instrm.mem[0] = beq_code(1, 2, 2);  // beq $1, $2, 2 -> target PC = 8
            cpu.u_instrm.mem[1] = addu_code(3, 1, 3); // addu $3, $1, $3 (跳过，如果分支成功)
            cpu.u_instrm.mem[2] = addu_code(4, 1, 2); // addu $4, $1, $2
            
            #10;
            rst = 0;

            // 经过三个时钟周期
            @(posedge clk); #1;
            @(posedge clk); #1;
            @(posedge clk); #1;
            
            // 如果分支跳转成功，R[3] = 0, R[4] = 14
            `EXPECT("R[3]", cpu.u_regfile.regs[3], 32'd0);
            `EXPECT("R[4]", cpu.u_regfile.regs[4], 32'd14);
        `TEST_END

        `TEST(beq_not_jmp_test)
            clk = 0;
            rst = 1;

            cpu.u_pc.curr_pc = 32'd0;
            cpu.u_regfile.regs[1] = 32'd7;
            cpu.u_regfile.regs[2] = 32'd7;
            cpu.u_regfile.regs[3] = 32'd0;
            cpu.u_regfile.regs[4] = 32'd0;

            cpu.u_instrm.mem[0] = beq_code(1, 0, 2);  // beq $1, $0, 2
            cpu.u_instrm.mem[1] = addu_code(3, 1, 3); // addu $3, $1, $3 (不会跳过)
            cpu.u_instrm.mem[2] = addu_code(4, 1, 2); // addu $4, $1, $2

            #10;
            rst = 0;

            // 经过三个时钟周期
            @(posedge clk); #1;
            @(posedge clk); #1;
            @(posedge clk); #1;

            // 如果没有跳转, R[3] = 7, R[4] = 14
            `EXPECT("R[3]", cpu.u_regfile.regs[3], 32'd7);
            `EXPECT("R[4]", cpu.u_regfile.regs[4], 32'd14);
        `TEST_END

        `VTEST_FINISH
    end
endmodule
