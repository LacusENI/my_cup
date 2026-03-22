`ifndef DEFINES_V
`define DEFINES_V

`define ALU_OP_ADD 4'b0001
`define ALU_OP_SUB 4'b0010

`define COND_TYPE_EQ  2'b00
`define COND_TYPE_NEQ 2'b01
`define COND_TYPE_LT  2'b10
`define COND_TYPE_LTU 2'b11

`define NPC_OP_PLUS4  2'b00
`define NPC_OP_BRANCH 2'b01
`define NPC_OP_DIRECT 2'b10

`define RD_SEL_RT      1'b0
`define RD_SEL_RD      1'b1
`define WB_SEL_ALU_OUT 1'b0
`define WB_SEL_R_DATA  1'b1
`define SRC2_SEL_RS2   1'b0
`define SRC2_SEL_IMM   1'b1

`endif // DEFINES_V