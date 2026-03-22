`include "rtl/core/defines.v"

module mem_ctrl (
    input [5:0] op,
    input [5:0] funct,
    output mem_read,
    output mem_write
);
    wire lw, sw;
    assign lw = (op == `OP_LW);
    assign sw = (op == `OP_SW);

    assign mem_read = lw;
    assign mem_write = sw;
endmodule