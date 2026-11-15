`default_nettype none

module halt_unit
    import cpu_pkg::*;
(
    input  logic        inst_illegal,
    input  sys_op_t     sys_op,
    input  logic        inst_addr_err,
    input  logic        load_addr_err,
    input  logic        store_addr_err,
    input  logic        target_addr_err,
    output logic        halt,
    output halt_cause_t halt_cause
);

    // 统一仲裁所有停机来源。
    // halt_cause 只在 halt=1 时有意义；halt=0 时输出值不参与架构判断。
    always_comb begin
        halt       = 1'b1;
        halt_cause = HALT_ILLEGAL_INST;

        if (inst_addr_err)
            halt_cause = HALT_INST_ADDR_ERR;
        else if (inst_illegal)
            halt_cause = HALT_ILLEGAL_INST;
        else if (sys_op == SYS_ECALL)
            halt_cause = HALT_ECALL;
        else if (sys_op == SYS_EBREAK)
            halt_cause = HALT_EBREAK;
        else if (load_addr_err)
            halt_cause = HALT_LOAD_ADDR_ERR;
        else if (store_addr_err)
            halt_cause = HALT_STORE_ADDR_ERR;
        else if (target_addr_err)
            halt_cause = HALT_INST_ADDR_ERR;
        else
            halt = 1'b0;
    end

endmodule

`default_nettype wire
