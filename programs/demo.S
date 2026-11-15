# demo.S —— my_cup RV32I 示例程序
#
# 程序以 ecall 结束；run_program 会等待 halt=1 后停止。
# 构建：
#   mycup build-programs
# 运行：
#   mycup prog programs/demo.S

    .section .text
    .globl _start

_start:
    addi x1, x0, 8
    addi x2, x0, 5
    add  x3, x1, x2          # x3 = 13
    sw   x3, 0(x0)           # data[0] = 13
    lw   x4, 0(x0)           # x4 = 13

    beq  x4, x3, after_skip
    addi x5, x0, 99          # 应被跳过

after_skip:
    lui  x6, 0x12345         # x6 = 0x12345000
    auipc x7, 0              # x7 = 当前 PC = 0x20
    fence iorw, iorw         # NOP
    ecall                    # halt，cause=11
